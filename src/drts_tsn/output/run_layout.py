"""Run directory layout helpers for generated artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drts_tsn.common.time_utils import utc_timestamp_compact
from drts_tsn.io.fs import ensure_directory


@dataclass(slots=True)
class RunLayout:
    """Resolved directory layout for one scaffold run."""

    output_root: Path
    run_id: str
    run_dir: Path
    inputs_dir: Path
    normalized_dir: Path
    simulation_results_dir: Path
    simulation_traces_dir: Path
    analysis_results_dir: Path
    analysis_traces_dir: Path
    comparison_results_dir: Path
    reports_dir: Path
    metadata_dir: Path


def create_run_layout(
    output_root: Path,
    *,
    run_id: str | None = None,
    create: bool = True,
    symlink_latest: bool = True,
) -> RunLayout:
    """Create or resolve a standard run artifact layout."""

    resolved_run_id = run_id or utc_timestamp_compact()
    runs_root = output_root / "runs"
    run_dir = runs_root / resolved_run_id
    layout = RunLayout(
        output_root=output_root,
        run_id=resolved_run_id,
        run_dir=run_dir,
        inputs_dir=run_dir / "inputs",
        normalized_dir=run_dir / "normalized",
        simulation_results_dir=run_dir / "simulation" / "results",
        simulation_traces_dir=run_dir / "simulation" / "traces",
        analysis_results_dir=run_dir / "analysis" / "results",
        analysis_traces_dir=run_dir / "analysis" / "traces",
        comparison_results_dir=run_dir / "comparison" / "results",
        reports_dir=run_dir / "reports",
        metadata_dir=run_dir / "metadata",
    )
    if create:
        for path in (
            runs_root,
            layout.run_dir,
            layout.inputs_dir,
            layout.normalized_dir,
            layout.simulation_results_dir,
            layout.simulation_traces_dir,
            layout.analysis_results_dir,
            layout.analysis_traces_dir,
            layout.comparison_results_dir,
            layout.reports_dir,
            layout.metadata_dir,
        ):
            ensure_directory(path)
        if symlink_latest:
            latest = runs_root / "latest"
            if latest.exists() or latest.is_symlink():
                latest.unlink()
            try:
                latest.symlink_to(run_dir.name)
            except OSError:
                # TODO: Consider a portable fallback if symlinks become problematic.
                pass
    return layout
