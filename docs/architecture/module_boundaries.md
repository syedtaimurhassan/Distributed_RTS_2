# Module Boundaries

- `domain`: canonical models only, no simulation or analysis dependencies
- `adapters`: external input parsing and export adapters
- `validation`: reusable checks and error aggregation
- `normalization`: canonicalization and derived-field pipeline
- `simulation`: discrete-event simulator scaffold
- `analysis`: analytical WCRT scaffold
- `comparison`: side-by-side result alignment and diagnostics
- `orchestration`: end-to-end workflows
- `output`: artifact layout and writers
