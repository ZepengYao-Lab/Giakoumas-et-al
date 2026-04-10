# Giakoumas Connectome Python Workflows

This directory contains a structured analysis workspace for rerunning and extending the Python- and R-based workflows used in the Giakoumas et al. connectome project. It combines shared code, thin notebooks, and workflow-specific output directories in a form that is easier to rerun on a clean machine than the original notebook-only layout.

## Layout

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

## Installation

From this directory:

```bash
python -m pip install -e .
```

This installs the `giakoumas-connectome` command-line entry point.

## Python Command-Line Workflows

List available workflow families:

```bash
giakoumas-connectome list
```

Run a workflow:

```bash
giakoumas-connectome run phn
```

Outputs are written under:

```text
output/<workflow-name>/
```

For example:

```text
output/phn/
```

Each workflow export includes tables, figures, and a manifest describing the generated outputs.

## Notebook Entry Points

The notebooks in [`notebooks/`](./notebooks) are intentionally lightweight. They import the shared package code, execute a workflow or report-building step, and render the resulting tables and figures.

Current notebook entry points are:

- `1-coconatfly-aphn-phn-cosine.ipynb`
- `2-coconatfly-phn-cosine.ipynb`
- `3-coconatfly-aphn-cosine.ipynb`
- `4-phn-connectome-analysis.ipynb`
- `5-pso-sa-connectome-analysis.ipynb`
- `5.1-pso-sa-input-connectome-analysis.ipynb`
- `6-aphn1-sa-connectome-analysis.ipynb`
- `7-aphn2-sa-connectome-analysis.ipynb`
- `8-hops-visualization.ipynb`
- `9-full-hops-figure.ipynb`

## Standard Output Structure

Workflow outputs typically include:

- summary and manifest files
- per-set second-order and third-order tables
- workflow-level connectivity matrices
- figure suites under `figures/`

Notebook-specific exports also populate dedicated output directories for:

- direct-input analyses
- hop-based sensory-to-motor visualizations
- portrait Sankey figure assembly
- refactored R cosine-similarity workflows

## R Cosine Workflows

The cosine-similarity notebooks depend on locally available R packages, including:

- `readr`
- `dplyr`
- `coconatfly`
- `coconat`
- `fafbseg`
- `bit64`
- `glue`
- `IRkernel` for notebook execution

Run the R workflows with:

```bash
Rscript r/run_coconatfly_analysis.R aphn_phn
Rscript r/run_coconatfly_analysis.R phn
Rscript r/run_coconatfly_analysis.R aphn aphn1 aphn2
```

R outputs are written under:

```text
output/r_coconatfly/
```

## Data And Cache Handling

This repository does not bundle third-party FlyWire annotation or connectome cache files that should remain local.

For the R cosine workflows, the expected private cache location is:

```text
.local_data/fafbseg/
```

To populate that cache, run:

```bash
Rscript r/setup_private_fafbseg_cache.R
```

If a clean machine needs the minimum required files downloaded directly:

```bash
Rscript r/setup_private_fafbseg_cache.R --download
```

See [`data/reference/README.md`](./data/reference/README.md) and [`THIRD_PARTY_DATA.md`](./THIRD_PARTY_DATA.md) for the corresponding data-handling notes.

## License And Citation

- Code in this directory is released under the MIT license. See [`LICENSE`](./LICENSE).
- Repository citation information is provided in [`CITATION.cff`](./CITATION.cff).
- Contribution guidance is summarized in [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Tests

Run:

```bash
pytest
```
