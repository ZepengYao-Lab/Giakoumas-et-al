# Third-Party Data Policy

This repository intentionally does not redistribute third-party FlyWire annotation or connectome cache files.

## Why

Some upstream resources used by the R workflows are distributed through external projects and publications. Public availability does not automatically mean this repository has permission to redistribute those files.

## What This Repository Does Instead

- ships code, notebooks, and your project-specific workflow inputs
- keeps external reference caches out of version control
- supports a private local cache under `.local_data/`, which is gitignored

## Local Setup

If you need the refactored R cosine workflows, stage the required local cache files with:

```bash
Rscript r/setup_private_fafbseg_cache.R
```

Or force a fresh download from the upstream online sources with:

```bash
Rscript r/setup_private_fafbseg_cache.R --download
```

You can also point the workflows to an existing local cache with:

```bash
export GIAKOUMAS_FAFBSEG_CACHE="/path/to/fafbseg"
```

## Before Publishing Data

Before committing or redistributing any third-party data, verify:

- the upstream license
- redistribution permissions
- citation requirements
- any terms attached to the original dataset or repository
