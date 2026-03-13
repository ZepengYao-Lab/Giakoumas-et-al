# Giakoumas Connectome Workflow

This directory is a standalone, notebook-centered refactor of analyses from the original `Giakoumas-et-al` repository.

The goal is to keep the original project untouched while providing a cleaner structure that is closer to a professional analysis repository:

- copied workflow data under `data/`
- reference-data notes under `data/reference/`
- reusable Python package code under `src/giakoumas_connectome/`
- reusable R workflow code under `r/`
- thin notebooks under `notebooks/`
- generated tables and figures under `output/`

## Project Layout

```text
giakoumas-connectome-python/
├── data/
│   ├── flywire_data/
│   ├── input/
│   └── reference/
├── notebooks/
├── output/
├── r/
├── src/giakoumas_connectome/
└── tests/
```

## Install

From this directory:

```bash
python -m pip install -e .
```

## Run From The Terminal

List Python workflows:

```bash
giakoumas-connectome list
```

Run a Python workflow and export tables plus figures:

```bash
giakoumas-connectome run phn
```

Outputs are written to:

```text
output/phn/
```

Run the refactored R cosine workflows:

```bash
Rscript r/setup_private_fafbseg_cache.R
Rscript r/setup_private_fafbseg_cache.R --download
Rscript r/run_coconatfly_analysis.R aphn_phn
Rscript r/run_coconatfly_analysis.R phn
Rscript r/run_coconatfly_analysis.R aphn aphn1 aphn2
```

R outputs are written under:

```text
output/r_coconatfly/
```

## Public Release Notes

- This repository does not bundle third-party FlyWire annotation/connectome cache files.
- Private local reference data belong in `.local_data/`, which is gitignored.
- Before redistributing third-party data yourself, verify the upstream license, terms, and citation requirements.

## Run From A Notebook

The notebooks in `notebooks/` are intentionally thin. They import the shared package code, build a report object, display key tables, and call common plotting functions.

Current notebook entry points:

- `4-phn-connectome-analysis.ipynb`
- `5-pso-sa-connectome-analysis.ipynb`
- `6-aphn1-sa-connectome-analysis.ipynb`
- `7-aphn2-sa-connectome-analysis.ipynb`
- `pso-sa-input-connectome-analysis.ipynb`
- `8-hops-visualization.ipynb`
- `9-full-hops-figure.ipynb`
- `1-coconatfly-aphn-phn-cosine.ipynb`
- `2-coconatfly-phn-cosine.ipynb`
- `3-coconatfly-aphn-cosine.ipynb`

This is the intended pattern for adding or maintaining analyses:

1. Keep biological configuration and interpretation in the notebook.
2. Keep reusable Python logic in `src/giakoumas_connectome/`.
3. Keep reusable R workflow logic in `r/`.
4. Reuse the same plotting/report code across notebook families.

## Standard Outputs

Each workflow export includes:

- `tables/workflow_summary.csv`
- `tables/first_order_set_to_set_matrix.csv`
- `tables/second_order_set_to_set_matrix.csv`
- `tables/set_to_second_order_matrix.csv`
- `tables/second_to_third_order_matrix.csv`
- per-set input synapse count tables
- per-set second-order and third-order tables
- a figure suite under `figures/`, including the restored UpSet plots, 2N-to-2N heatmap, set-to-2N heatmap, 2N-to-3N heatmap, and input/output synapse-count scatter plot
- `report_manifest.json`

Notebook-specific exports also include:

- `output/pso_sa_input_analysis/` for the direct-input tables and figures derived from `_aPhN_DCSO_input_connectome_analysis_v1.ipynb`
- `output/hops_visualization/` for the hop-count grid and annotated motor-path CSVs derived from `hops_visualization.ipynb`
- `output/full_hops_figure/` for the portrait Sankey SVG/HTML derived from `Full_hops_figure.ipynb`
- `output/r_coconatfly/aphn_phn_cosine/` for the refactored `1_Coconatfly_aPhN_PhN_Cosine.ipynb`
- `output/r_coconatfly/phn_cosine/` for the refactored `2_Coconatfly_PhN_Cosine.ipynb`
- `output/r_coconatfly/aphn_cosine/` for the refactored `3_Coconatfly_aPhN_Cosine.ipynb`

## R Workflow Notes

The R cosine notebooks depend on locally available R packages, including:

- `readr`
- `dplyr`
- `coconatfly`
- `coconat`
- `fafbseg`
- `bit64`
- `glue`
- `IRkernel` for notebook execution

For legal and ethical repo hygiene, this public repository does not bundle third-party FlyWire annotation/connectome cache files. Instead, the R workflows look for those files in one of these places:

- a private gitignored cache at `.local_data/fafbseg/`
- or a path supplied through `GIAKOUMAS_FAFBSEG_CACHE`
- or your existing local `fafbseg` user cache

The easiest setup is:

```bash
Rscript r/setup_private_fafbseg_cache.R
```

For a reviewer or any clean machine without a pre-existing local cache, use:

```bash
Rscript r/setup_private_fafbseg_cache.R --download
```

That script either copies from an existing local `fafbseg` cache or downloads the minimum required files directly into `.local_data/fafbseg/`, which is ignored by git and therefore not published with the repository.

Before redistributing any third-party data yourself, verify the upstream license/terms and citation requirements.

## License And Citation

- Code in this repository is released under the MIT license. See `LICENSE`.
- If you use this workflow in research output, add a repository citation alongside the underlying scientific data/resource citations. See `CITATION.cff`.
- Contribution expectations are summarized in `CONTRIBUTING.md`.
- Third-party data handling notes are in `THIRD_PARTY_DATA.md`.

## Tests

Run:

```bash
pytest
```

The R cosine workflows were validated by running:

```bash
Rscript r/run_coconatfly_analysis.R phn aphn_phn aphn aphn1 aphn2
```
