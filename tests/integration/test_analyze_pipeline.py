"""Integration coverage for the Milestone 2 analyze pipeline."""

from __future__ import annotations

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
    assert result_path.exists()
    assert manifest_path.exists()

    result_json = read_json(result_path)
    manifest_json = read_json(manifest_path)

    assert result_json["summary"]["schema_version"] == ANALYSIS_SCHEMA_VERSION
    assert manifest_json["schema_version"] == ANALYSIS_SCHEMA_VERSION

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
