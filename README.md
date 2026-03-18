# DRTS Mini Project 2

mini-project on Time-Sensitive Networking (TSN) worst-case response-time (WCRT) analysis, discrete-event simulation, and result comparison.

## Overview

This repository implements the workflow for the mini-project:

- load an external TSN case from disk
- normalize it into one canonical internal case model
- validate structural and baseline-scope assumptions
- run analytical AVB WCRT computation
- run a baseline discrete-event TSN/CBS simulation
- compare analytical and simulated results
- export machine-readable JSON and CSV artifacts for later reporting

The project is structured so that the normalized internal case model is the single source of truth. External case files are parsed once in the adapter layer, and analysis and simulation both operate on the same canonical domain model.

Validation and execution use explicit readiness stages:

- `schema-valid`: external files can be loaded and parsed
- `normalization-valid`: canonical topology/routes/streams/queues are structurally valid
- `baseline-runnable`: baseline assumptions checks pass
- `simulation-ready`: simulation preconditions pass
- `analysis-ready`: analysis preconditions pass

## Repository Layout

```text
.
├── src/drts_tsn/          # main package
├── cases/external/        # external case folders
├── cases/normalized/      # normalized case exports
├── configs/               # YAML configs
├── outputs/               # generated run and batch artifacts
├── tests/                 # unit, integration, golden tests
├── docs/                  # architecture and development notes
├── make.sh                # developer entrypoints
├── requirements.txt
└── pyproject.toml
```

Top-level package responsibilities:

- `cli/`: argument parsing and command dispatch
- `adapters/`: external case loading/parsing and normalized export helpers
- `domain/`: canonical case and result models
- `validation/`: reusable validation and precondition checks
- `normalization/`: canonicalization and derived parameters
- `analysis/`: analytical WCRT engine and traces
- `simulation/`: discrete-event engine and traces
- `comparison/`: result alignment, metrics, and diagnostics
- `orchestration/`: end-to-end pipelines used by the CLI
- `output/`: run layouts, manifests, and artifact writers

## Requirements

- Python `3.11+`
- Bash for `make.sh`
- macOS/Linux or another environment that supports the shell workflow

Runtime and development dependencies are declared in:

- `pyproject.toml`
- `requirements.txt`

## Quick Start

### Recommended setup

```bash
./make.sh setup
. .venv/bin/activate
drts --help
```

### Manual setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
drts --help
```

### Run without installing

From the repository root:

```bash
python -m drts_tsn.cli.main --help
```

This works locally because `sitecustomize.py` adds `src/` to `sys.path` when you run from the repo root.

## Sample Case

A bundled example case is available at:

```text
cases/external/test-case-1/
```

The loader accepts the default filenames:

- `topology.json`
- `routes.json`
- `streams.json`
- optional `expected_wcrts.csv`
- optional `manifest.yaml`

It also supports assignment-style inferred filenames such as:

- `*-topology.json`
- `*-routes.json`
- `*-streams.json`
- optional `*-WCRTs.csv`

## How the Pipeline Works

For a normal case run, the project executes these stages:

1. load an external case directory
2. parse raw topology, routes, streams, and optional expected WCRT data
3. map the raw content to a canonical internal `Case`
4. normalize IDs, routes, directed links, and derived transmission parameters
5. validate baseline assumptions and structural correctness
6. run analysis and/or simulation
7. compare analysis and simulation results if both exist
8. write JSON, CSV, and metadata artifacts

This separation is intentional:

- analysis and simulation do not parse external case files directly
- both consume the same normalized case model
- comparison consumes written analysis/simulation result artifacts
- CLI commands only wire arguments to orchestration code

## CLI Usage

The main CLI entrypoint is:

```bash
drts <command> [options]
```

You can also use:

```bash
python -m drts_tsn.cli.main <command> [options]
```

Global option:

- `--logging-config <path>`: load a logging YAML file before command execution

Available commands:

### `validate-case`

Validate one external case directory at an explicit readiness stage.

```bash
drts validate-case cases/external/test-case-1
drts validate-case cases/external/test-case-1 --stage analysis
```

Supported stages:

- `schema`
- `normalization` (default)
- `baseline`
- `simulation`
- `analysis`
- `all`

Interpretation:

- `normalization` checks structural validity of the normalized case model
- `baseline` adds baseline-runnability checks
- `simulation` adds simulation precondition checks
- `analysis` adds analysis precondition checks
- `all` requires all readiness stages to pass

### `normalize-case`

Normalize one case and export the normalized bundle.

```bash
drts normalize-case cases/external/test-case-1
drts normalize-case cases/external/test-case-1 --output-dir /tmp/test-case-1-normalized
```

Default output location when `--output-dir` is omitted:

```text
cases/normalized/<case_id>/
```

### `inspect-case`

Print a human-readable overview of the normalized case.

```bash
drts inspect-case cases/external/test-case-1
```

### `analyze`

Run the baseline analytical AVB WCRT pipeline.

```bash
drts analyze cases/external/test-case-1 --run-id demo-analysis
drts analyze cases/external/test-case-1 --analysis-config configs/analysis/default.yaml
```

Options:

- `--analysis-config <path>`
- `--output-config <path>`
- `--run-id <id>`

### `simulate`

Run the baseline TSN/CBS discrete-event simulation.

```bash
drts simulate cases/external/test-case-1 --run-id demo-simulation
drts simulate cases/external/test-case-1 --simulation-config configs/simulation/default.yaml
```

Options:

- `--simulation-config <path>`
- `--output-config <path>`
- `--run-id <id>`

### `compare`

Compare previously generated analysis and simulation results.

```bash
drts compare \
  --analysis-result outputs/runs/demo-analysis/analysis/results/analysis_result.json \
  --simulation-result outputs/runs/demo-simulation/simulation/results/simulation_result.json \
  --run-id demo-compare
```

Options:

- `--analysis-result <path>` required
- `--simulation-result <path>` required
- `--output-config <path>`
- `--run-id <id>`

### `run-case`

Run the full end-to-end pipeline for one case:

- normalize and validate once
- run analysis
- run simulation
- run comparison

```bash
drts run-case cases/external/test-case-1 --run-id demo-run
```

Options:

- `--analysis-config <path>`
- `--simulation-config <path>`
- `--output-config <path>`
- `--run-id <id>`

### `batch-run`

Run one pipeline across all discovered case directories under a root.

Supported operations:

- `analyze`
- `simulate`
- `run-case`

Examples:

```bash
drts batch-run cases/external --operation run-case --batch-id demo-batch
drts batch-run cases/external --operation analyze --batch-id analysis-batch
```

Options:

- `--operation <simulate|analyze|run-case>`
- `--analysis-config <path>`
- `--simulation-config <path>`
- `--output-config <path>`
- `--output-root <path>`
- `--batch-id <id>`

Batch execution continues after per-case failures and writes aggregate catalogs plus per-failure diagnostics. The overall command returns a non-zero status if any case fails.

## `make.sh` Commands

The repository also provides shell shortcuts:

```bash
./make.sh setup
./make.sh test
./make.sh validate
./make.sh readiness
./make.sh normalize
./make.sh inspect
./make.sh analyze
./make.sh simulate
./make.sh compare
./make.sh run
./make.sh batch
./make.sh clean
```

Behavior:

- `setup`: create `.venv`, install dependencies, install the project in editable mode
- `test`: run `pytest`
- `validate`, `normalize`, `inspect`, `analyze`, `simulate`, `run`: execute the matching CLI command for `CASE_DIR`
- `readiness`: run `validate-case --stage $READINESS_STAGE` (default `analysis`)
- `compare`: compare the latest analysis and simulation outputs unless explicit result paths are provided
- `batch`: execute `batch-run` for `CASES_ROOT`
- `clean`: remove generated run and batch artifacts

Useful environment overrides:

- `CASE_DIR`
- `READINESS_STAGE`
- `CASES_ROOT`
- `BATCH_OPERATION`
- `BATCH_ID`
- `OUTPUT_ROOT`
- `ANALYSIS_CONFIG`
- `SIMULATION_CONFIG`
- `OUTPUT_CONFIG`
- `ANALYSIS_RESULT`
- `SIMULATION_RESULT`

Example:

```bash
CASE_DIR="$PWD/cases/external/test-case-1" ./make.sh analyze
CASE_DIR="$PWD/cases/external/test-case-1" READINESS_STAGE=analysis ./make.sh readiness
BATCH_OPERATION=run-case BATCH_ID=demo-batch ./make.sh batch
```

## Recommended Example-Case Workflow

Use this command sequence for the bundled assignment case:

```bash
drts validate-case cases/external/test-case-1 --stage analysis
drts normalize-case cases/external/test-case-1 --output-dir /tmp/test-case-1-normalized
drts run-case cases/external/test-case-1 --run-id demo-run
```

If you want explicit step-by-step `analyze -> simulate -> compare` execution:

```bash
drts analyze cases/external/test-case-1 --run-id demo-analysis
drts simulate cases/external/test-case-1 --run-id demo-simulation
drts compare \
  --analysis-result outputs/runs/demo-analysis/analysis/results/analysis_result.json \
  --simulation-result outputs/runs/demo-simulation/simulation/results/simulation_result.json \
  --run-id demo-compare
```

## Configuration

Configuration files live under `configs/`.

### Analysis config

`configs/analysis/default.yaml`

- `strict_validation`
- `emit_explanations`
- `fixed_point_limit`
- `response_time_limit_us`

### Simulation config

`configs/simulation/default.yaml`

- `trace_enabled`
- `max_events`
- `max_hyperperiod_us`
- `time_limit_us`
- `max_releases_per_stream`
- `max_deliveries_total`
- `stop_when_all_streams_observed`

### Output config

`configs/output/default.yaml`

- `write_json`
- `write_csv`
- `write_metadata`
- `write_trace_csv`
- `symlink_latest`

### Logging config

Logging YAML files are available under `configs/logging/` and can be passed through `--logging-config`.

## Outputs and Artifacts

### Normalized export bundle

`normalize-case` writes:

- `normalized_case.json`
- `nodes.csv`
- `links.csv`
- `routes.csv`
- `streams.csv`
- `link_stream_map.csv`

### Single-run layout

Each analysis, simulation, compare, or run-case execution writes into:

```text
outputs/runs/<run-id>/
├── normalized/
├── analysis/results/
├── analysis/traces/
├── simulation/results/
├── simulation/traces/
├── comparison/results/
├── reports/
└── metadata/
```

Common metadata files:

- `metadata/run_manifest.json`
- `metadata/run_metadata.json`
- `metadata/artifact_index.json`

Pipeline-specific manifests may also be present:

- `metadata/analysis_manifest.json`
- `metadata/simulation_manifest.json`
- `metadata/comparison_manifest.json`

When enabled, `outputs/runs/latest` points to the latest run.

### Analysis artifacts

- `analysis_result.json`
- `stream_wcrt_summary.csv`
- `per_link_wcrt_summary.csv`
- `run_summary.csv`
- `link_interference_trace.csv`
- `same_priority_trace.csv`
- `credit_recovery_trace.csv`
- `lower_priority_trace.csv`
- `higher_priority_trace.csv`
- `per_link_formula_trace.csv`
- `end_to_end_accumulation_trace.csv`

### Simulation artifacts

- `simulation_result.json`
- `stream_summary.csv`
- `hop_summary.csv`
- `queue_summary.csv`
- `run_summary.csv`
- `frame_release_trace.csv`
- `enqueue_trace.csv`
- `transmission_trace.csv`
- `forwarding_trace.csv`
- `delivery_trace.csv`
- `response_time_trace.csv`
- `credit_trace.csv`
- `scheduler_decision_trace.csv`

Compatibility exports:

- `simulation_frame_hops.csv`
- `simulation_streams.csv`

### Comparison artifacts

- `comparison_result.json`
- `stream_comparison.csv`
- `aggregate_comparison.csv`
- `comparison_diagnostics.csv`
- optional `expected_wcrt_comparison.csv`

### Batch layout

Batch execution writes into:

```text
outputs/batches/<batch-id>/
├── catalog/
├── failures/
└── metadata/
```

Important batch files:

- `catalog/batch_run_catalog.csv`
- `catalog/batch_run_catalog.json`
- `failures/batch_failures.csv`
- `failures/batch_failures.json`
- per-failure diagnostic JSON files
- `metadata/batch_manifest.json`
- `metadata/artifact_index.json`

When enabled, `outputs/batches/latest` points to the latest batch run.

## Typical Workflows

### Validate and inspect a case

```bash
drts validate-case cases/external/test-case-1
drts inspect-case cases/external/test-case-1
```

### Export a normalized case bundle

```bash
drts normalize-case cases/external/test-case-1 --output-dir /tmp/test-case-1-normalized
```

### Run analysis and simulation separately, then compare

```bash
drts analyze cases/external/test-case-1 --run-id a1
drts simulate cases/external/test-case-1 --run-id s1
drts compare \
  --analysis-result outputs/runs/a1/analysis/results/analysis_result.json \
  --simulation-result outputs/runs/s1/simulation/results/simulation_result.json \
  --run-id c1
```

### Run the full pipeline for one case

```bash
drts run-case cases/external/test-case-1 --run-id full-1
```

### Run the full pipeline for all discovered cases

```bash
drts batch-run cases/external --operation run-case --batch-id batch-1
```

## Testing

Run the full test suite with:

```bash
./make.sh test
```

or:

```bash
pytest
```

Current automated coverage includes:

- parsing and normalization
- validation and invalid-case handling
- analytical formulas and preconditions
- simulator event ordering and CBS behavior
- comparison alignment and metrics
- CLI wiring
- output layout and batch execution

## Development Notes

- package version: `0.1.0`
- Python package name: `drts-mini-project-2`
- console script: `drts`
- source layout: `src/`

