"""Golden regression checks for the provided assignment reference case."""

from __future__ import annotations

import pytest

from drts_tsn.analysis.outputs.analysis_result_builder import ANALYSIS_SCHEMA_VERSION, ANALYSIS_TABLE_FIELDS
from drts_tsn.io.json_io import read_json
from drts_tsn.orchestration.pipeline_analyze import execute
from drts_tsn.reporting.csv_catalog import (
    ANALYSIS_PER_LINK_FORMULA_TRACE_CSV,
    ANALYSIS_PER_LINK_WCRT_SUMMARY_CSV,
    ANALYSIS_RUN_SUMMARY_CSV,
    ANALYSIS_STREAM_WCRT_SUMMARY_CSV,
)


def test_assignment_reference_case_matches_expected_wcrt_invariants(
    repo_root,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The provided assignment case should keep its load-bearing analysis invariants stable."""

    case_path = repo_root / "cases" / "external" / "test-case-1"
    result, layout = execute(case_path, output_root=tmp_path, run_id="golden-assignment-analysis")

    stream_rows = assert_csv_contract(
        layout.analysis_results_dir / ANALYSIS_STREAM_WCRT_SUMMARY_CSV,
        ANALYSIS_TABLE_FIELDS["stream_wcrt_summary"],
    )
    run_rows = assert_csv_contract(
        layout.analysis_results_dir / ANALYSIS_RUN_SUMMARY_CSV,
        ANALYSIS_TABLE_FIELDS["run_summary"],
    )
    per_link_rows = assert_csv_contract(
        layout.analysis_results_dir / ANALYSIS_PER_LINK_WCRT_SUMMARY_CSV,
        ANALYSIS_TABLE_FIELDS["per_link_wcrt_summary"],
    )
    formula_rows = assert_csv_contract(
        layout.analysis_traces_dir / ANALYSIS_PER_LINK_FORMULA_TRACE_CSV,
        ANALYSIS_TABLE_FIELDS["per_link_formula_trace"],
    )

    assert result.summary["schema_version"] == ANALYSIS_SCHEMA_VERSION
    assert result.summary["engine_status"] == "ok"
    assert result.summary["precondition_failure_count"] == 0

    assert len(stream_rows) == 8
    assert all(row["analyzed"] == "True" for row in stream_rows)
    assert all(row["status"] == "ok" for row in stream_rows)
    for row in stream_rows:
        assert float(row["end_to_end_wcrt_us"]) == pytest.approx(float(row["expected_wcrt_us"]))
        assert row["meets_deadline"] == "True"

    assert len(per_link_rows) == 16
    assert len(formula_rows) == len(per_link_rows) * 5
    assert {row["term_name"] for row in formula_rows} == {"Ci", "SPI", "LPI", "HPI", "W_link"}

    run_summary = run_rows[0]
    assert int(run_summary["analyzed_stream_count"]) == 8
    assert int(run_summary["skipped_best_effort_count"]) == 2
    assert int(run_summary["per_link_row_count"]) == 16
    assert run_summary["status"] == "ok"

    manifest = read_json(layout.metadata_dir / "analysis_manifest.json")
    assert manifest["schema_version"] == ANALYSIS_SCHEMA_VERSION
