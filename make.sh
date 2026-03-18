#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
CASE_DIR="${CASE_DIR:-$ROOT_DIR/cases/external/test-case-1}"
CASES_ROOT="${CASES_ROOT:-$ROOT_DIR/cases/external}"
RUN_ID="${RUN_ID:-}"
COMPARE_RUN_ID="${COMPARE_RUN_ID:-}"
READINESS_STAGE="${READINESS_STAGE:-all}"
NORMALIZED_OUTPUT_DIR="${NORMALIZED_OUTPUT_DIR:-}"

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
  readiness)
    run_cli validate-case "$CASE_DIR" --stage "$READINESS_STAGE"
    ;;
  normalize)
    normalize_args=(normalize-case "$CASE_DIR")
    [[ -n "$NORMALIZED_OUTPUT_DIR" ]] && normalize_args+=(--output-dir "$NORMALIZED_OUTPUT_DIR")
    run_cli "${normalize_args[@]}"
    ;;
  inspect)
    run_cli inspect-case "$CASE_DIR"
    ;;
  analyze)
    analyze_args=(analyze "$CASE_DIR")
    [[ -n "${ANALYSIS_CONFIG:-}" ]] && analyze_args+=(--analysis-config "$ANALYSIS_CONFIG")
    [[ -n "${OUTPUT_CONFIG:-}" ]] && analyze_args+=(--output-config "$OUTPUT_CONFIG")
    [[ -n "$RUN_ID" ]] && analyze_args+=(--run-id "$RUN_ID")
    run_cli "${analyze_args[@]}"
    ;;
  simulate)
    simulate_args=(simulate "$CASE_DIR")
    [[ -n "${SIMULATION_CONFIG:-}" ]] && simulate_args+=(--simulation-config "$SIMULATION_CONFIG")
    [[ -n "${OUTPUT_CONFIG:-}" ]] && simulate_args+=(--output-config "$OUTPUT_CONFIG")
    [[ -n "$RUN_ID" ]] && simulate_args+=(--run-id "$RUN_ID")
    run_cli "${simulate_args[@]}"
    ;;
  compare)
    if [[ -n "$RUN_ID" ]]; then
      default_analysis_result="$ROOT_DIR/outputs/runs/$RUN_ID/analysis/results/analysis_result.json"
      default_simulation_result="$ROOT_DIR/outputs/runs/$RUN_ID/simulation/results/simulation_result.json"
    else
      default_analysis_result="$ROOT_DIR/outputs/runs/latest/analysis/results/analysis_result.json"
      default_simulation_result="$ROOT_DIR/outputs/runs/latest/simulation/results/simulation_result.json"
    fi
    ANALYSIS_RESULT="${ANALYSIS_RESULT:-$default_analysis_result}"
    SIMULATION_RESULT="${SIMULATION_RESULT:-$default_simulation_result}"
    if [[ ! -f "$ANALYSIS_RESULT" || ! -f "$SIMULATION_RESULT" ]]; then
      cat >&2 <<EOF
compare requires existing analysis and simulation result JSON files.
Resolved analysis result: $ANALYSIS_RESULT
Resolved simulation result: $SIMULATION_RESULT
Set ANALYSIS_RESULT and SIMULATION_RESULT explicitly, or set RUN_ID to a run that already contains both.
EOF
      exit 2
    fi
    compare_args=(compare --simulation-result "$SIMULATION_RESULT" --analysis-result "$ANALYSIS_RESULT")
    [[ -n "${OUTPUT_CONFIG:-}" ]] && compare_args+=(--output-config "$OUTPUT_CONFIG")
    [[ -n "$COMPARE_RUN_ID" ]] && compare_args+=(--run-id "$COMPARE_RUN_ID")
    run_cli "${compare_args[@]}"
    ;;
  run|run-case)
    run_case_args=(run-case "$CASE_DIR")
    [[ -n "${SIMULATION_CONFIG:-}" ]] && run_case_args+=(--simulation-config "$SIMULATION_CONFIG")
    [[ -n "${ANALYSIS_CONFIG:-}" ]] && run_case_args+=(--analysis-config "$ANALYSIS_CONFIG")
    [[ -n "${OUTPUT_CONFIG:-}" ]] && run_case_args+=(--output-config "$OUTPUT_CONFIG")
    [[ -n "$RUN_ID" ]] && run_case_args+=(--run-id "$RUN_ID")
    run_cli "${run_case_args[@]}"
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
  readiness  Validate case run readiness (default stage: all)
  normalize  Normalize the default case (set NORMALIZED_OUTPUT_DIR to override)
  inspect    Inspect the default case
  analyze    Run baseline AVB analysis (supports RUN_ID/ANALYSIS_CONFIG/OUTPUT_CONFIG)
  simulate   Run baseline TSN/CBS simulation (supports RUN_ID/SIMULATION_CONFIG/OUTPUT_CONFIG)
  compare    Compare analysis and simulation results (uses RUN_ID or explicit result paths)
  run        Run normalize + analyze + simulate + compare for the default case
  run-case   Alias for 'run'
  batch      Run a selected operation over all discovered case directories
  clean      Remove generated run and batch directories
EOF
    ;;
esac
