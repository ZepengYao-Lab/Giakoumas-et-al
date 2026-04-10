# Giakoumas et al.

Code, notebooks, and workflow scaffolding for the connectomic analyses in:

**Connectomic mapping of pharyngeal and gut sensory circuits in adult _Drosophila_**  
Dimitrios S. Giakoumas, Julia M. Zhu, Alaina Jamal, Zepeng Yao  
DOI: [10.64898/2025.12.14.694216](https://doi.org/10.64898/2025.12.14.694216)

## Overview

This repository contains the analysis environment used to generate and inspect the study's connectomic results. It includes:

- the original analysis notebooks in [`analyses/`](./analyses)
- curated input tables in [`input/`](./input)
- project data tables in [`flywire_data/`](./flywire_data)
- a root-level Python workflow package in [`src/giakoumas_workflow/`](./src/giakoumas_workflow)
- a more structured standalone workflow workspace in [`giakoumas-connectome-python/`](./giakoumas-connectome-python)

The notebook files preserve the analysis logic and figure-generation steps, while the packaged workflows provide a cleaner command-line surface for repeated Python analyses.

## Repository Layout

```text
.
├── analyses/                     Original notebooks used for analysis and figure generation
├── flywire_data/                 Project data tables used by the notebooks
├── input/                        Curated neuron-set inputs
├── output/                       Generated outputs
├── src/giakoumas_workflow/       Root-level Python workflow package
├── tests/                        Tests for the root-level Python workflow package
└── giakoumas-connectome-python/  Standalone refactored workflow workspace
```

## Root-Level Python Workflows

The root package provides a small command-line interface for rerunning the main Python workflows without editing notebook state.

### Installation

```bash
python -m pip install -e .
```

### List available workflows

```bash
giakoumas-workflow list
```

Current workflow families correspond to these input locations:

- `phn` -> `input/PhN/`
- `pso-sa` -> `input/PSO_SA/`
- `aphn1` -> `input/aPhN/aPhN1/`
- `aphn2` -> `input/aPhN/aPhN2/`

### Run a workflow

```bash
giakoumas-workflow run phn
```

By default, outputs are written under:

```text
output/python_workflows/<workflow-name>/
```

Example:

```bash
giakoumas-workflow run aphn1 --output-dir output/python_workflows/aphn1
```

If third-order outputs should exclude first-order sensory identifiers explicitly:

```bash
giakoumas-workflow run phn --exclude-first-order-from-third-order
```

Each workflow writes per-set second-order and third-order tables together with:

- `workflow_summary.csv`
- `workflow_manifest.json`

## Standalone Refactored Workspace

The [`giakoumas-connectome-python/`](./giakoumas-connectome-python) subdirectory contains a more structured, notebook-fronted workflow package with shared Python and R code. See its own [README](./giakoumas-connectome-python/README.md) for installation, notebook entry points, and data-cache requirements.

## Notes On Reproducibility

- Generated outputs are written under [`output/`](./output) or the package-specific output directories.
- Some workflows rely on local data tables or caches that are not appropriate to redistribute directly.
- The original notebooks are retained because they document the analysis process and figure assembly used in the project.

## Testing

Run the root Python tests with:

```bash
pytest
```
