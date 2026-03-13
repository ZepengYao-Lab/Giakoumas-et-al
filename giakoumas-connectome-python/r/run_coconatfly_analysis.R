args <- commandArgs(trailingOnly = TRUE)

find_project_root <- function(start = getwd()) {
  current <- normalizePath(start, winslash = "/", mustWork = TRUE)
  repeat {
    if (dir.exists(file.path(current, "r")) && dir.exists(file.path(current, "data"))) {
      return(current)
    }
    parent <- dirname(current)
    if (identical(parent, current)) {
      stop("Could not locate the standalone project root.", call. = FALSE)
    }
    current <- parent
  }
}

PROJECT_ROOT <- find_project_root()
source(file.path(PROJECT_ROOT, "r", "bootstrap.R"))
gc_bootstrap()

if (length(args) == 0) {
  cat("Usage: Rscript r/run_coconatfly_analysis.R <analysis-key> [<analysis-key> ...]\n")
  cat("Available analysis keys:\n")
  for (key in names(gc_coconatfly_configs)) {
    cat(" - ", key, "\n", sep = "")
  }
  quit(status = 1)
}

for (key in args) {
  result <- gc_run_coconatfly_analysis(key, project_root = PROJECT_ROOT)
  paths <- gc_save_analysis_outputs(result)
  print(result$summary)
  print(unlist(paths))
}
