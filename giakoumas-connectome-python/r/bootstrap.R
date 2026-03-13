options(scipen = 999)
options(rgl.useNULL = TRUE)

gc_r_dir <- if (exists("PROJECT_ROOT", inherits = TRUE)) {
  file.path(get("PROJECT_ROOT", inherits = TRUE), "r")
} else {
  dirname(normalizePath(sys.frame(1)$ofile, winslash = "/", mustWork = TRUE))
}

gc_project_root <- dirname(gc_r_dir)

gc_private_data_root <- function(project_root = gc_project_root) {
  file.path(project_root, ".local_data")
}

gc_private_fafbseg_cache <- function(project_root = gc_project_root) {
  file.path(gc_private_data_root(project_root), "fafbseg")
}

gc_configure_runtime_cache <- function(project_root = gc_project_root) {
  xdg_cache_root <- file.path(project_root, ".cache")
  dir.create(xdg_cache_root, recursive = TRUE, showWarnings = FALSE)
  Sys.setenv(XDG_CACHE_HOME = xdg_cache_root)
  invisible(xdg_cache_root)
}

gc_resolve_fafbseg_cache <- function(project_root = gc_project_root) {
  env_cache <- Sys.getenv("GIAKOUMAS_FAFBSEG_CACHE", "")
  if (nzchar(env_cache)) {
    return(normalizePath(env_cache, winslash = "/", mustWork = FALSE))
  }

  private_cache <- gc_private_fafbseg_cache(project_root)
  if (dir.exists(private_cache)) {
    return(private_cache)
  }

  getFromNamespace("fafbseg_userdir", "fafbseg")()
}

gc_required_fafbseg_paths <- function(cache_root) {
  list(
    annotations = file.path(
      cache_root,
      "flywire_annotations",
      "supplemental_files",
      "Supplemental_file1_neuron_annotations.tsv"
    ),
    connectome = file.path(
      cache_root,
      "flywire_connectome_analysis_data",
      "783",
      "syn_proof_analysis_filtered_783.feather"
    )
  )
}

gc_assert_fafbseg_reference_data <- function(cache_root) {
  required_paths <- gc_required_fafbseg_paths(cache_root)
  missing_paths <- required_paths[!vapply(required_paths, file.exists, logical(1))]

  if (length(missing_paths) == 0) {
    return(invisible(cache_root))
  }

  formatted_missing <- paste(
    paste0(" - ", names(missing_paths), ": ", unlist(missing_paths)),
    collapse = "\n"
  )

  stop(
    paste(
      "Required FlyWire reference files were not found.",
      "This public repository intentionally does not bundle third-party annotation/connectome data.",
      "Provide a local cache in one of these ways:",
      paste0("1. Run `Rscript r/setup_private_fafbseg_cache.R` to stage a private gitignored cache at ", gc_private_fafbseg_cache(gc_project_root)),
      "2. Or set `GIAKOUMAS_FAFBSEG_CACHE` to an existing local fafbseg cache directory.",
      "Missing paths:",
      formatted_missing,
      sep = "\n"
    ),
    call. = FALSE
  )
}

gc_configure_fafbseg_runtime <- function(project_root = gc_project_root) {
  gc_configure_runtime_cache(project_root)
  cache_root <- gc_resolve_fafbseg_cache(project_root)

  options(
    fafbseg.cachedir = cache_root,
    fafbseg.flywire_connectome_dir = file.path(cache_root, "flywire_connectome_analysis_data"),
    fafbseg.use_static_celltypes = TRUE
  )

  local_userdir <- function(..., os = NULL) {
    args <- list(...)
    if (length(args) > 0) {
      file.path(cache_root, ...)
    } else {
      cache_root
    }
  }

  assignInNamespace("fafbseg_userdir", local_userdir, ns = "fafbseg")
  assignInNamespace(
    "flywire_sirepo_update",
    function(x, branch = "main") invisible(x),
    ns = "fafbseg"
  )
  assignInNamespace(
    "flywire_sirepo_download",
    function(repo = "flyconnectome/flywire_annotations", version = c(783L, 630L), ref = NULL, ...) {
      localdir <- getFromNamespace("flywire_sirepo_dir", "fafbseg")(
        repo = repo,
        create_basedir = TRUE
      )
      if (!file.exists(localdir)) {
        stop(
          paste0(
            "Local FlyWire annotation data was not found at ",
            localdir,
            ". Run `Rscript r/setup_private_fafbseg_cache.R` or set `GIAKOUMAS_FAFBSEG_CACHE`."
          ),
          call. = FALSE
        )
      }
      invisible(localdir)
    },
    ns = "fafbseg"
  )

  gc_assert_fafbseg_reference_data(cache_root)
  invisible(cache_root)
}

gc_bootstrap <- function() {
  suppressPackageStartupMessages({
    library(readr)
    library(dplyr)
    library(coconatfly)
    library(coconat)
    library(fafbseg)
    library(bit64)
    library(glue)
  })
  gc_configure_fafbseg_runtime(gc_project_root)
  invisible(TRUE)
}

source(file.path(gc_r_dir, "coconatfly_config.R"), local = globalenv())
source(file.path(gc_r_dir, "coconatfly_helpers.R"), local = globalenv())
