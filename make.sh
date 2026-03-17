#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
CASE_DIR="${CASE_DIR:-$ROOT_DIR/cases/external/test-case-1}"
CASES_ROOT="${CASES_ROOT:-$ROOT_DIR/cases/external}"

ensure_python() {
  if [[ -x "$PYTHON_BIN" ]]; then
    echo "$PYTHON_BIN"
    return
  fi
  command -v python3
}

run_cli() {
  local py_bin
  py_bin="$(ensure_python)"
  PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$py_bin" -m drts_tsn.cli.main "$@"
}

case "${1:-help}" in
  setup)
    python3 -m venv "$VENV_DIR"
    "$PIP_BIN" install --upgrade pip
    "$PIP_BIN" install -r "$ROOT_DIR/requirements.txt"
    "$PIP_BIN" install -e "$ROOT_DIR"
    ;;
  test)
    PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$(ensure_python)" -m pytest
    ;;
  validate)
    run_cli validate-case "$CASE_DIR"
    ;;
  normalize)
    run_cli normalize-case "$CASE_DIR"
    ;;
  inspect)
    run_cli inspect-case "$CASE_DIR"
    ;;
  analyze)
    run_cli analyze "$CASE_DIR"
    ;;
  simulate)
    run_cli simulate "$CASE_DIR"
    ;;
  compare)
    ANALYSIS_RESULT="${ANALYSIS_RESULT:-$ROOT_DIR/outputs/runs/latest/analysis/results/analysis_result.json}"
    SIMULATION_RESULT="${SIMULATION_RESULT:-$ROOT_DIR/outputs/runs/latest/simulation/results/simulation_result.json}"
    run_cli compare --simulation-result "$SIMULATION_RESULT" --analysis-result "$ANALYSIS_RESULT"
    ;;
  run)
    run_cli run-case "$CASE_DIR"
    ;;
  batch)
    BATCH_OPERATION="${BATCH_OPERATION:-run-case}"
    batch_args=(batch-run "$CASES_ROOT" --operation "$BATCH_OPERATION")
    [[ -n "${BATCH_ID:-}" ]] && batch_args+=(--batch-id "$BATCH_ID")
    [[ -n "${OUTPUT_ROOT:-}" ]] && batch_args+=(--output-root "$OUTPUT_ROOT")
    [[ -n "${ANALYSIS_CONFIG:-}" ]] && batch_args+=(--analysis-config "$ANALYSIS_CONFIG")
    [[ -n "${SIMULATION_CONFIG:-}" ]] && batch_args+=(--simulation-config "$SIMULATION_CONFIG")
    [[ -n "${OUTPUT_CONFIG:-}" ]] && batch_args+=(--output-config "$OUTPUT_CONFIG")
    run_cli "${batch_args[@]}"
    ;;
  clean)
    [[ -d "$ROOT_DIR/outputs/runs" ]] && find "$ROOT_DIR/outputs/runs" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' -exec rm -rf {} +
    [[ -d "$ROOT_DIR/outputs/batches" ]] && find "$ROOT_DIR/outputs/batches" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' -exec rm -rf {} +
    ;;
  help|--help|-h|*)
    cat <<'EOF'
Usage: ./make.sh <command>

Commands:
  setup      Create .venv and install dependencies
  test       Run pytest
  validate   Validate the default case
  normalize  Normalize the default case
  inspect    Inspect the default case
  analyze    Run baseline AVB analysis on the default case
  simulate   Run baseline TSN/CBS simulation on the default case
  compare    Compare the latest analysis and simulation run results
  run        Run analyze + simulate + compare for the default case
  batch      Run a selected operation over all discovered case directories
  clean      Remove generated run and batch directories
EOF
    ;;
esac
