# Data Flow

1. Load external case files from `cases/external/...`.
2. Parse raw input files through external adapters.
3. Map raw inputs into canonical domain models.
4. Validate canonical data and assumptions.
5. Normalize identifiers and derived fields.
6. Execute simulation and/or analysis pipelines.
7. Compare outputs when both result sets exist.
8. Persist raw and derived artifacts under `outputs/runs/...`.
