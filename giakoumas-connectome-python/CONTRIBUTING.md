# Contributing

## Scope

This repository is organized around thin notebooks plus shared Python and R workflow code.

- Keep reusable Python logic in `src/giakoumas_connectome/`.
- Keep reusable R workflow logic in `r/`.
- Keep notebooks thin, readable, and runnable from top to bottom.

## Development Basics

From the project root:

```bash
python -m pip install -e .
pytest
```

For the refactored R cosine workflows:

```bash
Rscript r/setup_private_fafbseg_cache.R
Rscript r/run_coconatfly_analysis.R phn aphn_phn aphn aphn1 aphn2
```

## Notebook Changes

- Prefer targeted edits over large notebook rewrites.
- Do not commit notebook outputs unless there is a specific reason to preserve them.
- Keep notebook filenames stable and descriptive.

## Data Policy

- Do not commit private caches, generated outputs, or third-party annotation/connectome cache files.
- Put local third-party R reference data in `.local_data/`, which is gitignored.
- Before adding any external data to the repository, confirm that redistribution is permitted.

## Pull Requests

- Summarize the scientific or workflow motivation for the change.
- Note any changed outputs, assumptions, or expected reviewer-facing impact.
- Mention what you validated locally.
