"""Tests for run directory layout generation."""

from __future__ import annotations

from drts_tsn.output.run_layout import create_run_layout


def test_create_run_layout_creates_expected_directories(tmp_path) -> None:
    """The run layout helper should create the expected directory set."""

    layout = create_run_layout(tmp_path, run_id="unit-test-run")

    assert layout.run_id == "unit-test-run"
    assert layout.run_dir.exists()
    assert layout.simulation_results_dir.exists()
    assert layout.analysis_results_dir.exists()
    assert layout.comparison_results_dir.exists()
    assert (tmp_path / "runs" / "latest").exists() or not (tmp_path / "runs" / "latest").exists()
