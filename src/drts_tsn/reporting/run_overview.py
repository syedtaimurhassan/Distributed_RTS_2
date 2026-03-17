"""Run overview helpers."""

from __future__ import annotations

from drts_tsn.output.run_layout import RunLayout


def build_run_overview(layout: RunLayout) -> dict[str, object]:
    """Return a flat run overview dictionary."""

    return {
        "run_id": layout.run_id,
        "run_dir": str(layout.run_dir),
    }
