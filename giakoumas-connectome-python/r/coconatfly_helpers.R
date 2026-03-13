gc_find_project_root <- function(start = getwd()) {
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

gc_ensure_dir <- function(path) {
  dir.create(path, recursive = TRUE, showWarnings = FALSE)
  invisible(path)
}

gc_load_selected_population <- function(project_root, config) {
  selected_path <- file.path(project_root, config$selected_csv)
  readr::read_csv(
    selected_path,
    show_col_types = FALSE,
    col_types = readr::cols(root_id = readr::col_character())
  ) |>
    dplyr::rename(id = root_id)
}

gc_prepare_population <- function(selected_population, config) {
  ids_string <- paste(selected_population$id, collapse = " ")
  metadata <- coconatfly::cf_meta(coconatfly::cf_ids(ids_string, datasets = "flywire"))
  population <- dplyr::left_join(metadata, selected_population, by = "id")
  display_name <- if ("name.x" %in% names(population)) {
    population$name.x
  } else if ("name" %in% names(population)) {
    population$name
  } else {
    population$id
  }
  population$side_name_id <- paste(population$side, display_name, population$id, sep = "")

  partners <- population |>
    coconatfly::cf_partners(
      threshold = config$min_partner_weight,
      partners = config$partner_mode
    )

  output_counts <- partners |>
    dplyr::group_by(pre_id) |>
    dplyr::summarise(output_count = sum(weight), .groups = "drop") |>
    dplyr::mutate(pre_id = as.character(pre_id))

  filtered <- population |>
    dplyr::left_join(output_counts, by = c("id" = "pre_id")) |>
    dplyr::mutate(output_count = dplyr::coalesce(output_count, 0)) |>
    dplyr::filter(output_count >= config$min_total_output)

  list(
    selected_population = selected_population,
    metadata = metadata,
    partners = partners,
    filtered_population = filtered
  )
}

gc_build_dendrogram <- function(prepared, config) {
  hc <- coconatfly::cf_cosine_plot(
    prepared$filtered_population$key,
    threshold = config$clustering_threshold,
    partners = config$partner_mode,
    method = config$clustering_method,
    heatmap = FALSE
  )

  dendrogram_meta <- coconatfly::cf_meta(hc) |>
    dplyr::left_join(
      prepared$selected_population |>
        dplyr::select(id, nerve),
      by = "id"
    )

  labels <- paste(dendrogram_meta$id, dendrogram_meta$nerve, sep = config$label_separator %||% ": ")

  list(
    hc = hc,
    dendrogram_meta = dendrogram_meta,
    labels = labels
  )
}

gc_plot_dendrogram <- function(result) {
  config <- result$config
  old_par <- graphics::par(no.readonly = TRUE)
  on.exit(graphics::par(old_par), add = TRUE)

  graphics::par(mar = config$mar, xpd = TRUE)
  graphics::plot(
    result$dendrogram$hc,
    labels = result$dendrogram$labels,
    hang = config$hang,
    cex = config$cex,
    main = config$plot_title
  )
}

gc_plot_heatmap <- function(result) {
  config <- result$config
  old_par <- graphics::par(no.readonly = TRUE)
  on.exit(graphics::par(old_par), add = TRUE)

  graphics::par(mar = config$mar)
  if (!is.null(config$oma)) {
    graphics::par(oma = config$oma)
  }

  with(
    result$prepared$filtered_population,
    coconatfly::cf_cosine_plot(
      key,
      threshold = config$clustering_threshold,
      labRow = id,
      interactive = FALSE,
      partners = config$partner_mode,
      method = config$clustering_method,
      cexRow = config$cex_row,
      cexCol = config$cex_col
    )
  )
}

gc_save_base_plot <- function(path, width, height, plot_fun) {
  ext <- tolower(tools::file_ext(path))
  if (ext == "pdf") {
    grDevices::pdf(path, width = width, height = height)
  } else if (ext == "svg") {
    grDevices::svg(path, width = width, height = height)
  } else {
    stop(glue::glue("Unsupported output extension '{ext}'."), call. = FALSE)
  }
  on.exit(grDevices::dev.off(), add = TRUE)
  plot_fun()
}

gc_save_analysis_outputs <- function(result, formats = c("pdf", "svg")) {
  figure_dir <- file.path(result$output_dir, "figures")
  gc_ensure_dir(figure_dir)

  output_paths <- lapply(formats, function(ext) {
    file.path(figure_dir, paste0(result$config$figure_stem, ".", ext))
  })
  names(output_paths) <- formats

  plot_fun <- if (identical(result$config$plot_type, "dendrogram")) {
    function() gc_plot_dendrogram(result)
  } else {
    function() gc_plot_heatmap(result)
  }

  for (ext in formats) {
    gc_save_base_plot(
      path = output_paths[[ext]],
      width = result$config$plot_width,
      height = result$config$plot_height,
      plot_fun = plot_fun
    )
  }

  summary_path <- file.path(result$output_dir, "analysis_summary.csv")
  readr::write_csv(result$summary, summary_path)

  filtered_path <- file.path(result$output_dir, "filtered_population.csv")
  readr::write_csv(result$prepared$filtered_population, filtered_path)

  partners_path <- file.path(result$output_dir, "partners.csv")
  readr::write_csv(result$prepared$partners, partners_path)

  if (!is.null(result$dendrogram)) {
    dendrogram_meta_path <- file.path(result$output_dir, "dendrogram_metadata.csv")
    readr::write_csv(result$dendrogram$dendrogram_meta, dendrogram_meta_path)
  }

  c(output_paths, summary = summary_path, filtered_population = filtered_path, partners = partners_path)
}

gc_build_summary <- function(result) {
  data.frame(
    analysis_key = result$config$key,
    plot_type = result$config$plot_type,
    selected_neurons = nrow(result$prepared$selected_population),
    filtered_neurons = nrow(result$prepared$filtered_population),
    partner_rows = nrow(result$prepared$partners),
    output_dir = result$output_dir,
    stringsAsFactors = FALSE
  )
}

gc_run_coconatfly_analysis <- function(key, project_root = gc_find_project_root()) {
  config <- gc_get_coconatfly_config(key)
  selected_population <- gc_load_selected_population(project_root, config)
  prepared <- gc_prepare_population(selected_population, config)
  dendrogram <- if (identical(config$plot_type, "dendrogram")) {
    gc_build_dendrogram(prepared, config)
  } else {
    NULL
  }

  output_dir <- file.path(project_root, config$output_dir)
  gc_ensure_dir(output_dir)

  result <- list(
    config = config,
    project_root = project_root,
    output_dir = output_dir,
    prepared = prepared,
    dendrogram = dendrogram
  )
  result$summary <- gc_build_summary(result)
  class(result) <- c("gc_coconatfly_result", class(result))
  result
}

`%||%` <- function(x, y) {
  if (is.null(x) || (length(x) == 1 && is.na(x))) {
    y
  } else {
    x
  }
}
