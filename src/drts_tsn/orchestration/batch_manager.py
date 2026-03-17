"""Batch execution helper for case directories."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.adapters.external_cases.schema_checks import missing_required_files

from .pipeline_analyze import execute as analyze_case
from .pipeline_run_case import execute as run_case
from .pipeline_simulate import execute as simulate_case


def _discover_case_directories(root: Path) -> list[Path]:
    """Discover directories that look like external case roots."""

    discovered: list[Path] = []
    for directory in sorted([root, *root.rglob("*")]):
        if directory.is_dir() and not missing_required_files(directory):
            discovered.append(directory)
    return discovered


def run_batch(cases_root: Path, *, operation: str = "run-case") -> list[dict[str, object]]:
    """Run a selected pipeline over each child case directory."""

    outcomes: list[dict[str, object]] = []
    operations = {
        "simulate": simulate_case,
        "analyze": analyze_case,
        "run-case": run_case,
    }
    pipeline = operations[operation]
    for case_dir in _discover_case_directories(cases_root):
        try:
            pipeline(case_dir)
            outcomes.append({"case": case_dir.name, "status": "ok"})
        except Exception as exc:  # noqa: BLE001
            outcomes.append({"case": case_dir.name, "status": "error", "error": str(exc)})
    return outcomes
