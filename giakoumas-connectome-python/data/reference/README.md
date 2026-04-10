# Reference Data Notes

This directory is reserved for documentation about reference datasets and local data dependencies.

The public repository does not bundle third-party FlyWire annotation or connectome cache files that should remain in a private local cache.

For the R cosine-similarity workflows, prepare the expected local cache with:

```bash
Rscript r/setup_private_fafbseg_cache.R
```

On a clean machine, the minimum required files can be downloaded with:

```bash
Rscript r/setup_private_fafbseg_cache.R --download
```

Those files are staged into `.local_data/fafbseg/`, which is gitignored and intended for local use rather than redistribution.
