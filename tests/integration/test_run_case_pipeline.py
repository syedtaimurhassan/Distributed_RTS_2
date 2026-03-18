"""Integration coverage for the end-to-end run-case pipeline."""

from __future__ import annotations

import pytest

from drts_tsn.analysis.outputs.analysis_result_builder import ANALYSIS_TABLE_FIELDS
from drts_tsn.comparison.outputs.comparison_result_builder import COMPARISON_TABLE_FIELDS
from drts_tsn.io.json_io import read_json
from drts_tsn.orchestration.pipeline_run_case import execute
from drts_tsn.simulation.outputs.simulation_result_builder import SIMULATION_TABLE_FIELDS
from drts_tsn.validation.errors import CaseReadinessError


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


def test_run_case_pipeline_assignment_case_emits_full_baseline_artifact_contracts(
    repo_root,
    tmp_path,
    assert_csv_contract,
) -> None:
    """Provided assignment case should emit stable analysis/simulation/comparison contracts."""

    _, layout = execute(
        repo_root / "cases" / "external" / "test-case-1",
        output_root=tmp_path,
        run_id="assignment-case-artifact-contracts",
    )

    assert (layout.normalized_dir / "test-case-1.json").exists()
    assert_csv_contract(
        layout.analysis_results_dir / "stream_wcrt_summary.csv",
        ANALYSIS_TABLE_FIELDS["stream_wcrt_summary"],
    )
    assert_csv_contract(
        layout.analysis_results_dir / "per_link_wcrt_summary.csv",
        ANALYSIS_TABLE_FIELDS["per_link_wcrt_summary"],
    )
    assert_csv_contract(
        layout.analysis_traces_dir / "per_link_formula_trace.csv",
        ANALYSIS_TABLE_FIELDS["per_link_formula_trace"],
    )
    assert_csv_contract(
        layout.analysis_traces_dir / "end_to_end_accumulation_trace.csv",
        ANALYSIS_TABLE_FIELDS["end_to_end_accumulation_trace"],
    )
    assert_csv_contract(
        layout.simulation_results_dir / "stream_summary.csv",
        SIMULATION_TABLE_FIELDS["stream_summary"],
    )
    assert_csv_contract(
        layout.simulation_results_dir / "run_summary.csv",
        SIMULATION_TABLE_FIELDS["run_summary"],
    )
    assert_csv_contract(
        layout.simulation_traces_dir / "response_time_trace.csv",
        SIMULATION_TABLE_FIELDS["response_time_trace"],
    )
    assert_csv_contract(
        layout.comparison_results_dir / "stream_comparison.csv",
        COMPARISON_TABLE_FIELDS["stream_comparison"],
    )
    assert_csv_contract(
        layout.comparison_results_dir / "aggregate_comparison.csv",
        COMPARISON_TABLE_FIELDS["aggregate_comparison"],
    )
    assert_csv_contract(
        layout.comparison_results_dir / "comparison_diagnostics.csv",
        COMPARISON_TABLE_FIELDS["comparison_diagnostics"],
    )
    assert_csv_contract(
        layout.comparison_results_dir / "expected_wcrt_comparison.csv",
        COMPARISON_TABLE_FIELDS["expected_wcrt_comparison"],
    )
    run_manifest_json = read_json(layout.metadata_dir / "run_manifest.json")
    assert run_manifest_json["pipeline"] == "run-case"
    assert run_manifest_json["component_statuses"]["analysis"] == "ok"
    assert run_manifest_json["component_statuses"]["simulation"] == "ok"
    assert run_manifest_json["component_statuses"]["comparison"] == "ok"
    assert (layout.metadata_dir / "artifact_index.json").exists()


def test_run_case_pipeline_assignment_case_comparison_rows_are_aligned_and_unique(
    repo_root,
    tmp_path,
    assert_csv_contract,
) -> None:
    """Comparison rows for the provided assignment case should have unique aligned stream IDs."""

    _, layout = execute(
        repo_root / "cases" / "external" / "test-case-1",
        output_root=tmp_path,
        run_id="assignment-case-comparison-alignment",
    )
    stream_rows = assert_csv_contract(
        layout.comparison_results_dir / "stream_comparison.csv",
        COMPARISON_TABLE_FIELDS["stream_comparison"],
    )
    aggregate_rows = assert_csv_contract(
        layout.comparison_results_dir / "aggregate_comparison.csv",
        COMPARISON_TABLE_FIELDS["aggregate_comparison"],
    )
    expected_rows = assert_csv_contract(
        layout.comparison_results_dir / "expected_wcrt_comparison.csv",
        COMPARISON_TABLE_FIELDS["expected_wcrt_comparison"],
    )

    stream_ids = [str(row["stream_id"]) for row in stream_rows]
    assert len(stream_ids) == len(set(stream_ids))
    assert all(row["analytical_wcrt_us"] not in ("", None) for row in stream_rows)
    assert all(row["simulated_worst_response_time_us"] not in ("", None) for row in stream_rows)
    aggregate_row = aggregate_rows[0]
    assert int(aggregate_row["missing_analysis_count"]) == 0
    assert int(aggregate_row["missing_simulation_count"]) == 0
    assert int(aggregate_row["duplicate_analysis_count"]) == 0
    assert int(aggregate_row["duplicate_simulation_count"]) == 0
    assert int(aggregate_row["matched_stream_count"]) == len(stream_rows)
    assert int(aggregate_row["stream_count"]) == len(stream_rows)
    assert int(aggregate_row["reference_row_count"]) == len(expected_rows)
    expected_ids = {str(row["stream_id"]) for row in expected_rows}
    assert expected_ids == set(stream_ids)


def test_run_case_pipeline_assignment_case_stream_ids_align_across_all_baseline_artifacts(
    repo_root,
    tmp_path,
    assert_csv_contract,
) -> None:
    """Canonical stream IDs should align across normalized, analysis, simulation, and comparison artifacts."""

    _, layout = execute(
        repo_root / "cases" / "external" / "test-case-1",
        output_root=tmp_path,
        run_id="assignment-case-stream-id-alignment",
    )
    normalized = read_json(layout.normalized_dir / "test-case-1.json")
    normalized_streams = list(normalized.get("streams", []))
    normalized_ids = {str(row["id"]) for row in normalized_streams}
    normalized_avb_ids = {
        str(row["id"])
        for row in normalized_streams
        if str(row.get("traffic_class", "")).strip().lower() in {"class_a", "class_b"}
    }

    analysis_rows = assert_csv_contract(
        layout.analysis_results_dir / "stream_wcrt_summary.csv",
        ANALYSIS_TABLE_FIELDS["stream_wcrt_summary"],
    )
    simulation_rows = assert_csv_contract(
        layout.simulation_results_dir / "stream_summary.csv",
        SIMULATION_TABLE_FIELDS["stream_summary"],
    )
    comparison_rows = assert_csv_contract(
        layout.comparison_results_dir / "stream_comparison.csv",
        COMPARISON_TABLE_FIELDS["stream_comparison"],
    )
    expected_rows = assert_csv_contract(
        layout.comparison_results_dir / "expected_wcrt_comparison.csv",
        COMPARISON_TABLE_FIELDS["expected_wcrt_comparison"],
    )

    analysis_ids = {str(row["stream_id"]) for row in analysis_rows}
    simulation_ids = {str(row["stream_id"]) for row in simulation_rows}
    simulation_avb_ids = {
        str(row["stream_id"])
        for row in simulation_rows
        if str(row.get("traffic_class", "")).strip().lower() in {"class_a", "class_b"}
    }
    comparison_ids = {str(row["stream_id"]) for row in comparison_rows}
    expected_ids = {str(row["stream_id"]) for row in expected_rows}

    assert normalized_avb_ids
    assert normalized_ids == simulation_ids
    assert normalized_avb_ids == analysis_ids
    assert normalized_avb_ids == simulation_avb_ids
    assert normalized_avb_ids == comparison_ids
    assert normalized_avb_ids == expected_ids


def test_run_case_pipeline_fails_early_when_analysis_readiness_fails(
    invalid_reserved_bandwidth_case_path,
    tmp_path,
) -> None:
    """run-case should report readiness failure before executing downstream stages."""

    with pytest.raises(CaseReadinessError, match="stage 'analysis'"):
        execute(
            invalid_reserved_bandwidth_case_path,
            output_root=tmp_path,
            run_id="run-case-invalid-readiness",
        )
