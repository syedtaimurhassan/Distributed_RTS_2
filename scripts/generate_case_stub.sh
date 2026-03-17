#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASE_NAME="${1:-new-case}"
TARGET_DIR="$ROOT_DIR/cases/external/custom/$CASE_NAME"

mkdir -p "$TARGET_DIR"
cp "$ROOT_DIR/cases/external/test-case-1/manifest.yaml" "$TARGET_DIR/manifest.yaml"
cp "$ROOT_DIR/cases/external/test-case-1/topology.json" "$TARGET_DIR/topology.json"
cp "$ROOT_DIR/cases/external/test-case-1/routes.json" "$TARGET_DIR/routes.json"
cp "$ROOT_DIR/cases/external/test-case-1/streams.json" "$TARGET_DIR/streams.json"
cp "$ROOT_DIR/cases/external/test-case-1/expected_wcrts.csv" "$TARGET_DIR/expected_wcrts.csv"
