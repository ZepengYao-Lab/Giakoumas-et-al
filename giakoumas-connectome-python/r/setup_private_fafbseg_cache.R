args <- commandArgs(trailingOnly = TRUE)

annotation_url <- paste0(
  "https://raw.githubusercontent.com/flyconnectome/flywire_annotations/",
  "v2.1.0/supplemental_files/Supplemental_file1_neuron_annotations.tsv"
)
connectome_url <- paste0(
  "https://flyem.mrc-lmb.cam.ac.uk/flyconnectome/flywire_connectivity/",
  "syn_proof_analysis_filtered_consolidated_783.feather"
)

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

default_source_cache <- function() {
  if (!requireNamespace("rappdirs", quietly = TRUE)) {
    return("")
  }
  path.expand(rappdirs::user_data_dir(file.path("R", "fafbseg"), appauthor = NULL))
}

copy_one <- function(source_path, target_path, label) {
  if (!file.exists(source_path)) {
    stop(
      paste0(
        "Missing required source file for ", label, ": ", source_path,
        "\nProvide an explicit source cache path as the first argument if your fafbseg cache lives elsewhere."
      ),
      call. = FALSE
    )
  }

  dir.create(dirname(target_path), recursive = TRUE, showWarnings = FALSE)
  success <- file.copy(
    from = source_path,
    to = target_path,
    overwrite = TRUE,
    copy.mode = TRUE,
    copy.date = TRUE
  )

  if (!isTRUE(success)) {
    stop(paste0("Failed to copy ", label, " to ", target_path), call. = FALSE)
  }

  cat("Copied ", label, " -> ", target_path, "\n", sep = "")
}

download_one <- function(url, target_path, label) {
  dir.create(dirname(target_path), recursive = TRUE, showWarnings = FALSE)
  previous_timeout <- getOption("timeout")
  on.exit(options(timeout = previous_timeout), add = TRUE)
  options(timeout = max(600, previous_timeout))
  if (file.exists(target_path)) {
    file.remove(target_path)
  }
  utils::download.file(url, target_path, mode = "wb", quiet = FALSE)
  if (!file.exists(target_path) || file.size(target_path) == 0) {
    stop(paste0("Failed to download ", label, " from ", url), call. = FALSE)
  }
  cat("Downloaded ", label, " -> ", target_path, "\n", sep = "")
}

write_manifest <- function(target_cache, source_mode, source_cache = NA_character_) {
  manifest_path <- file.path(target_cache, "SOURCE_MANIFEST.txt")
  writeLines(
    c(
      paste("created_at:", format(Sys.time(), tz = "UTC", usetz = TRUE)),
      paste("source_mode:", source_mode),
      paste("source_cache:", source_cache),
      paste("annotation_url:", annotation_url),
      paste("connectome_url:", connectome_url),
      "local_annotation_path: flywire_annotations/supplemental_files/Supplemental_file1_neuron_annotations.tsv",
      "local_connectome_path: flywire_connectome_analysis_data/783/syn_proof_analysis_filtered_783.feather"
    ),
    manifest_path
  )
  cat("Wrote manifest -> ", manifest_path, "\n", sep = "")
}

PROJECT_ROOT <- find_project_root()
download_mode <- "--download" %in% args
source_args <- args[args != "--download"]

source_cache <- if (length(source_args) >= 1) {
  normalizePath(source_args[[1]], winslash = "/", mustWork = TRUE)
} else {
  normalizePath(default_source_cache(), winslash = "/", mustWork = FALSE)
}

target_cache <- file.path(PROJECT_ROOT, ".local_data", "fafbseg")

annotation_target <- file.path(
  target_cache,
  "flywire_annotations",
  "supplemental_files",
  "Supplemental_file1_neuron_annotations.tsv"
)
connectome_target <- file.path(
  target_cache,
  "flywire_connectome_analysis_data",
  "783",
  "syn_proof_analysis_filtered_783.feather"
)

if (download_mode) {
  download_one(annotation_url, annotation_target, "FlyWire neuron annotations")
  download_one(connectome_url, connectome_target, "FlyWire connectome synapse table")
  write_manifest(target_cache, source_mode = "download", source_cache = NA_character_)
} else if (dir.exists(source_cache)) {
  copy_one(
    file.path(
      source_cache,
      "flywire_annotations",
      "supplemental_files",
      "Supplemental_file1_neuron_annotations.tsv"
    ),
    annotation_target,
    "FlyWire neuron annotations"
  )

  copy_one(
    file.path(
      source_cache,
      "flywire_connectome_analysis_data",
      "783",
      "syn_proof_analysis_filtered_783.feather"
    ),
    connectome_target,
    "FlyWire connectome synapse table"
  )
  write_manifest(target_cache, source_mode = "copy", source_cache = source_cache)
} else {
  cat(
    "No local fafbseg cache was found at:\n",
    source_cache,
    "\n\nFalling back to direct download.\n\n",
    sep = ""
  )
  download_one(annotation_url, annotation_target, "FlyWire neuron annotations")
  download_one(connectome_url, connectome_target, "FlyWire connectome synapse table")
  write_manifest(target_cache, source_mode = "download", source_cache = NA_character_)
}

cat(
  "\nPrivate fafbseg cache is ready at:\n",
  target_cache,
  "\n\nThis directory is gitignored and will not be published with the repository.\n",
  "Use `--download` to force online retrieval for reviewer-facing reproducibility.\n",
  sep = ""
)
