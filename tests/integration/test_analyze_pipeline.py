"""Integration coverage for the Milestone 2 analyze pipeline."""

from __future__ import annotations

import pytest

from drts_tsn.analysis.outputs.analysis_result_builder import ANALYSIS_SCHEMA_VERSION, ANALYSIS_TABLE_FIELDS
from drts_tsn.io.json_io import read_json
from drts_tsn.orchestration.pipeline_analyze import execute
from drts_tsn.reporting.csv_catalog import (
    ANALYSIS_CREDIT_RECOVERY_TRACE_CSV,
    ANALYSIS_END_TO_END_ACCUMULATION_TRACE_CSV,
    ANALYSIS_HIGHER_PRIORITY_TRACE_CSV,
    ANALYSIS_LINK_INTERFERENCE_TRACE_CSV,
    ANALYSIS_LOWER_PRIORITY_TRACE_CSV,
    ANALYSIS_PER_LINK_FORMULA_TRACE_CSV,
    ANALYSIS_PER_LINK_WCRT_SUMMARY_CSV,
    ANALYSIS_RUN_SUMMARY_CSV,
    ANALYSIS_SAME_PRIORITY_TRACE_CSV,
    ANALYSIS_STREAM_WCRT_SUMMARY_CSV,
)
from drts_tsn.validation.errors import CaseValidationError


def test_analyze_pipeline_writes_required_summary_and_trace_artifacts(
    sample_case_path,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The analyze pipeline should emit the required Milestone 2 artifact set."""

    result, layout = execute(sample_case_path, output_root=tmp_path, run_id="analysis-pipeline-test")

    assert result.stream_results[0].wcrt_us == 40.96
    result_path = layout.analysis_results_dir / "analysis_result.json"
    manifest_path = layout.metadata_dir / "analysis_manifest.json"
    run_manifest_path = layout.metadata_dir / "run_manifest.json"
    artifact_index_path = layout.metadata_dir / "artifact_index.json"
    assert result_path.exists()
    assert manifest_path.exists()
    assert run_manifest_path.exists()
    assert artifact_index_path.exists()

    result_json = read_json(result_path)
    manifest_json = read_json(manifest_path)
    run_manifest_json = read_json(run_manifest_path)

    assert result_json["summary"]["schema_version"] == ANALYSIS_SCHEMA_VERSION
    assert manifest_json["schema_version"] == ANALYSIS_SCHEMA_VERSION
    assert run_manifest_json["pipeline"] == "analyze"
    assert run_manifest_json["case"]["case_path"]
    assert run_manifest_json["command_invoked"].startswith("analyze ")
    assert run_manifest_json["config_snapshot"]["analysis"]["values"]["strict_validation"] is True
    assert set(result_json["tables"]) == set(ANALYSIS_TABLE_FIELDS)
    for table_name, fieldnames in ANALYSIS_TABLE_FIELDS.items():
        for row in result_json["tables"].get(table_name, []):
            assert set(row) == set(fieldnames)

    csv_targets = {
        "stream_wcrt_summary": layout.analysis_results_dir / ANALYSIS_STREAM_WCRT_SUMMARY_CSV,
        "per_link_wcrt_summary": layout.analysis_results_dir / ANALYSIS_PER_LINK_WCRT_SUMMARY_CSV,
        "run_summary": layout.analysis_results_dir / ANALYSIS_RUN_SUMMARY_CSV,
        "link_interference_trace": layout.analysis_traces_dir / ANALYSIS_LINK_INTERFERENCE_TRACE_CSV,
        "same_priority_trace": layout.analysis_traces_dir / ANALYSIS_SAME_PRIORITY_TRACE_CSV,
        "credit_recovery_trace": layout.analysis_traces_dir / ANALYSIS_CREDIT_RECOVERY_TRACE_CSV,
        "lower_priority_trace": layout.analysis_traces_dir / ANALYSIS_LOWER_PRIORITY_TRACE_CSV,
        "higher_priority_trace": layout.analysis_traces_dir / ANALYSIS_HIGHER_PRIORITY_TRACE_CSV,
        "per_link_formula_trace": layout.analysis_traces_dir / ANALYSIS_PER_LINK_FORMULA_TRACE_CSV,
        "end_to_end_accumulation_trace": layout.analysis_traces_dir / ANALYSIS_END_TO_END_ACCUMULATION_TRACE_CSV,
    }
    for table_name, path in csv_targets.items():
        assert path.exists()
        assert_csv_contract(path, ANALYSIS_TABLE_FIELDS[table_name])


def test_analyze_pipeline_supports_provided_assignment_case_bundle(
    repo_root,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The provided assignment case should run through analyze and emit baseline traces."""

    assignment_case_path = repo_root / "cases" / "external" / "test-case-1"
    result, layout = execute(
        assignment_case_path,
        output_root=tmp_path,
        run_id="analysis-assignment-case",
    )

    stream_rows = assert_csv_contract(
        layout.analysis_results_dir / ANALYSIS_STREAM_WCRT_SUMMARY_CSV,
        ANALYSIS_TABLE_FIELDS["stream_wcrt_summary"],
    )
    higher_priority_rows = assert_csv_contract(
        layout.analysis_traces_dir / ANALYSIS_HIGHER_PRIORITY_TRACE_CSV,
        ANALYSIS_TABLE_FIELDS["higher_priority_trace"],
    )
    formula_rows = assert_csv_contract(
        layout.analysis_traces_dir / ANALYSIS_PER_LINK_FORMULA_TRACE_CSV,
        ANALYSIS_TABLE_FIELDS["per_link_formula_trace"],
    )
    assert result.summary["engine_status"] == "ok"
    assert any(row["traffic_class"] == "class_b" for row in stream_rows)
    assert any(float(row["contribution_us"]) > 0.0 for row in higher_priority_rows)
    assert "W_link" in {row["term_name"] for row in formula_rows}


def test_analyze_pipeline_rejects_invalid_reserved_bandwidth_fixture(
    invalid_reserved_bandwidth_case_path,
    tmp_path,
) -> None:
    """Strict analysis should fail loudly when reserved-share preconditions are violated."""

    with pytest.raises(CaseValidationError, match="analysis.reserved-bandwidth.exceeded"):
        execute(
            invalid_reserved_bandwidth_case_path,
            output_root=tmp_path,
            run_id="analysis-invalid-reserved",
        )
