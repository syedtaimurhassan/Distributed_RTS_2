"""Integration coverage for the end-to-end run-case pipeline."""

from __future__ import annotations

from drts_tsn.io.json_io import read_json
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
    run_manifest_json = read_json(layout.metadata_dir / "run_manifest.json")
    assert run_manifest_json["pipeline"] == "run-case"
    assert run_manifest_json["case"]["case_path"]
    assert run_manifest_json["config_snapshot"]["analysis"]["values"]["strict_validation"] is True
    assert (layout.metadata_dir / "artifact_index.json").exists()


def test_run_case_pipeline_handles_bundled_assignment_case(repo_root, tmp_path) -> None:
    """The bundled assignment case should complete analyze+simulate+compare."""

    result_map, layout = execute(
        repo_root / "cases" / "external" / "test-case-1",
        output_root=tmp_path,
        run_id="assignment-case-pipeline-test",
    )

    analysis_result = result_map["analysis_result"]
    simulation_result = result_map["simulation_result"]
    comparison_result = result_map["comparison_result"]
    assert analysis_result.summary["engine_status"] == "ok"
    assert simulation_result.summary["engine_status"] == "ok"
    assert comparison_result.summary["missing_analysis_count"] == 0
    assert comparison_result.summary["missing_simulation_count"] == 0
    assert comparison_result.summary["stream_count"] == 8
    assert (layout.comparison_results_dir / "expected_wcrt_comparison.csv").exists()
