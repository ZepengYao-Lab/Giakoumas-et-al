# Output Directory

This directory stores generated analysis products, including tables, figures, and workflow manifests created by the notebooks and command-line workflows in this repository.

Contents under `output/` should be treated as derived results rather than hand-edited source material.

When regenerating analyses:

- keep source logic in `analyses/`, `src/`, or `giakoumas-connectome-python/`
- write derived products into workflow-specific subdirectories under `output/`
- avoid editing exported figures or tables in place unless the change is part of a documented figure-assembly step
