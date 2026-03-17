#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"
CASE_DIR="${CASE_DIR:-$ROOT_DIR/cases/external/test-case-1}"

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
  clean)
    find "$ROOT_DIR/outputs/runs" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
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
  clean      Remove generated run directories
EOF
    ;;
esac
