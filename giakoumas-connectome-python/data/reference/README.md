This directory is reserved for reference-data notes only.

The public repository intentionally does not bundle third-party FlyWire annotation or connectome cache files.

If you need the R cosine workflows, stage those files into a private local cache with:

```bash
Rscript r/setup_private_fafbseg_cache.R
Rscript r/setup_private_fafbseg_cache.R --download
```

That command copies the minimum required files into `.local_data/fafbseg/`, which is gitignored and meant for private local use only.
