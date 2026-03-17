"""Integration coverage for the end-to-end run-case pipeline."""

from __future__ import annotations

from drts_tsn.orchestration.pipeline_run_case import execute


def test_run_case_pipeline_writes_expected_artifacts(sample_case_path, tmp_path) -> None:
    """The combined pipeline should write JSON and CSV artifacts for the baseline."""

    _, layout = execute(sample_case_path, output_root=tmp_path, run_id="pipeline-test")

    assert (layout.simulation_results_dir / "simulation_result.json").exists()
    assert (layout.simulation_results_dir / "stream_summary.csv").exists()
    assert (layout.simulation_results_dir / "hop_summary.csv").exists()
    assert (layout.simulation_results_dir / "queue_summary.csv").exists()
    assert (layout.analysis_results_dir / "analysis_result.json").exists()
    assert (layout.analysis_results_dir / "stream_wcrt_summary.csv").exists()
    assert (layout.analysis_results_dir / "per_link_wcrt_summary.csv").exists()
    assert (layout.comparison_results_dir / "comparison_result.json").exists()
    assert (layout.comparison_results_dir / "stream_comparison.csv").exists()
    assert (layout.comparison_results_dir / "aggregate_comparison.csv").exists()
    assert (layout.comparison_results_dir / "comparison_diagnostics.csv").exists()
