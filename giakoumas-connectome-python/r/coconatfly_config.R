gc_coconatfly_configs <- list(
  aphn_phn = list(
    key = "aphn_phn",
    selected_csv = "data/input/input_coconatfly/selected/aPhN_PhN_cosine.csv",
    output_dir = "output/r_coconatfly/aphn_phn_cosine",
    figure_stem = "aPhN_PhN_dendrogram_wardd2",
    plot_type = "dendrogram",
    plot_title = "PanPharyngeal Sensory Axons Dendrogram",
    min_partner_weight = 5,
    min_total_output = 5,
    partner_mode = "outputs",
    clustering_threshold = 1,
    clustering_method = "ward.D2",
    plot_width = 10,
    plot_height = 4,
    cex = 0.2,
    hang = -0.01,
    mar = c(6, 5, 4, 5),
    label_separator = ": "
  ),
  phn = list(
    key = "phn",
    selected_csv = "data/input/input_coconatfly/selected/PhN_cosine.csv",
    output_dir = "output/r_coconatfly/phn_cosine",
    figure_stem = "PhN_clustermap_wardd2",
    plot_type = "heatmap",
    plot_title = "PhN Cosine Similarity",
    min_partner_weight = 5,
    min_total_output = 4,
    partner_mode = "outputs",
    clustering_threshold = 1,
    clustering_method = "ward.D2",
    plot_width = 15,
    plot_height = 10,
    cex_row = 0.2,
    cex_col = 0.2,
    mar = c(15, 20, 4, 2) + 0.1,
    oma = c(5, 5, 5, 5)
  ),
  aphn = list(
    key = "aphn",
    selected_csv = "data/input/input_coconatfly/selected/aPhN_cosine.csv",
    output_dir = "output/r_coconatfly/aphn_cosine/aphn",
    figure_stem = "aPhN_clustermap_wardd2",
    plot_type = "heatmap",
    plot_title = "aPhN Cosine Similarity",
    min_partner_weight = 5,
    min_total_output = 5,
    partner_mode = "outputs",
    clustering_threshold = 1,
    clustering_method = "ward.D2",
    plot_width = 15,
    plot_height = 10,
    cex_row = 0.3,
    cex_col = 0.3,
    mar = c(10, 10, 4, 2) + 0.1,
    oma = NULL
  ),
  aphn1 = list(
    key = "aphn1",
    selected_csv = "data/input/input_coconatfly/selected/aPhN1_cosine.csv",
    output_dir = "output/r_coconatfly/aphn_cosine/aphn1",
    figure_stem = "aPhN1_clustermap_wardd2",
    plot_type = "heatmap",
    plot_title = "aPhN1 Cosine Similarity",
    min_partner_weight = 5,
    min_total_output = 5,
    partner_mode = "outputs",
    clustering_threshold = 1,
    clustering_method = "ward.D2",
    plot_width = 10,
    plot_height = 4,
    cex_row = 0.4,
    cex_col = 0.4,
    mar = c(15, 15, 4, 15) + 0.1,
    oma = NULL
  ),
  aphn2 = list(
    key = "aphn2",
    selected_csv = "data/input/input_coconatfly/selected/aPhN2_cosine.csv",
    output_dir = "output/r_coconatfly/aphn_cosine/aphn2",
    figure_stem = "aPhN2_clustermap_wardd2",
    plot_type = "heatmap",
    plot_title = "aPhN2 Cosine Similarity",
    min_partner_weight = 5,
    min_total_output = 5,
    partner_mode = "outputs",
    clustering_threshold = 1,
    clustering_method = "ward.D2",
    plot_width = 10,
    plot_height = 4,
    cex_row = 0.3,
    cex_col = 0.3,
    mar = c(15, 15, 4, 15) + 0.1,
    oma = NULL
  )
)

gc_get_coconatfly_config <- function(key) {
  if (!key %in% names(gc_coconatfly_configs)) {
    stop(glue::glue("Unknown Coconatfly config '{key}'."), call. = FALSE)
  }
  gc_coconatfly_configs[[key]]
}
