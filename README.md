# DRTS Mini Project 2

Scaffold for a university mini-project on Time-Sensitive Networking (TSN) worst-case response-time (WCRT) analysis, discrete-event simulation, and result comparison.

The repository is intentionally scaffold-first. It provides package boundaries, CLI entrypoints, configuration files, output contracts, reusable adapters, validation and normalization layers, and baseline subsystem engines. Milestone 2 adds the analytical AVB WCRT path on top of the normalized case pipeline.

## Current Scope

- Python `src/` layout package
- One CLI with subcommands
- External case loading and canonical normalization
- Explicit validation and normalization layers
- Baseline AVB analytical WCRT engine for normalized cases
- Separate top-level simulation, analysis, and comparison subsystems
- Output helpers for JSON, CSV, and run-directory creation
- Initial tests and documentation skeleton

## Baseline Assumptions

- Simplified TSN baseline only
- Line topology in the assignment baseline
- One traffic direction in the simplified baseline
- Three output queues per port:
  - AVB Class A
  - AVB Class B
  - Best Effort
- AVB Class A and B use CBS
- Best Effort is lowest priority
- Detailed raw CSV outputs are first-class artifacts
- Derived summaries are emitted separately
- Detailed traces are supported but disabled by default
- External case files remain external inputs and are mapped into canonical internal domain models

## CLI Overview

The `drts` CLI exposes the following Milestone 2 subcommands:

- `validate-case`
- `normalize-case`
- `inspect-case`
- `analyze`

The CLI contains wiring only. Business logic lives in orchestration, adapters, validation, normalization, analysis, and output modules.

## Development Workflow

```bash
./make.sh setup
./make.sh test
./make.sh validate
./make.sh normalize
./make.sh inspect
./make.sh analyze
```

For local development without installation, `sitecustomize.py` injects `src/` into `sys.path` so `python -m drts_tsn.cli.main --help` works from the repository root.

## Status

The simulation and comparison modules remain future work at the CLI level. The baseline analytical engine currently computes AVB Class A and B WCRT bounds per link and end-to-end, and emits both summary CSVs and explanation-oriented trace CSVs.
