"""Integration coverage for the standalone comparison pipeline."""

from __future__ import annotations

from drts_tsn.orchestration.pipeline_analyze import execute as execute_analyze
from drts_tsn.orchestration.pipeline_compare import execute as execute_compare
from drts_tsn.orchestration.pipeline_simulate import execute as execute_simulate
from drts_tsn.reporting.csv_catalog import (
    COMPARISON_AGGREGATE_COMPARISON_CSV,
    COMPARISON_DIAGNOSTICS_CSV,
    COMPARISON_EXPECTED_WCRT_COMPARISON_CSV,
    COMPARISON_STREAM_COMPARISON_CSV,
)
from drts_tsn.comparison.outputs.comparison_result_builder import COMPARISON_TABLE_FIELDS


def test_compare_pipeline_writes_required_artifacts(
    sample_case_path,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The comparison pipeline should consume result artifacts and emit stable CSVs."""

    _, analyze_layout = execute_analyze(sample_case_path, output_root=tmp_path, run_id="compare-analysis")
    _, simulate_layout = execute_simulate(sample_case_path, output_root=tmp_path, run_id="compare-simulate")
    result, compare_layout = execute_compare(
        simulation_result_path=simulate_layout.simulation_results_dir / "simulation_result.json",
        analysis_result_path=analyze_layout.analysis_results_dir / "analysis_result.json",
        output_root=tmp_path,
        run_id="compare-pipeline",
    )

    assert result.summary["engine_status"] == "ok"
    assert result.tables["stream_comparison"]
    assert result.tables["aggregate_comparison"]

    results_root = compare_layout.comparison_results_dir
    assert_csv_contract(
        results_root / COMPARISON_STREAM_COMPARISON_CSV,
        COMPARISON_TABLE_FIELDS["stream_comparison"],
    )
    assert_csv_contract(
        results_root / COMPARISON_AGGREGATE_COMPARISON_CSV,
        COMPARISON_TABLE_FIELDS["aggregate_comparison"],
    )
    assert_csv_contract(
        results_root / COMPARISON_DIAGNOSTICS_CSV,
        COMPARISON_TABLE_FIELDS["comparison_diagnostics"],
    )
    expected_rows = assert_csv_contract(
        results_root / COMPARISON_EXPECTED_WCRT_COMPARISON_CSV,
        COMPARISON_TABLE_FIELDS["expected_wcrt_comparison"],
    )
    assert len(expected_rows) == 1
    assert expected_rows[0]["stream_id"] == "stream-a"


def test_compare_pipeline_assignment_case_has_no_missing_or_duplicate_stream_alignment(
    repo_root,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The provided assignment case should compare with clean stream-ID alignment."""

    case_path = repo_root / "cases" / "external" / "test-case-1"
    _, analyze_layout = execute_analyze(
        case_path,
        output_root=tmp_path,
        run_id="compare-assignment-analysis",
    )
    _, simulate_layout = execute_simulate(
        case_path,
        output_root=tmp_path,
        run_id="compare-assignment-simulate",
    )
    result, compare_layout = execute_compare(
        simulation_result_path=simulate_layout.simulation_results_dir / "simulation_result.json",
        analysis_result_path=analyze_layout.analysis_results_dir / "analysis_result.json",
        output_root=tmp_path,
        run_id="compare-assignment",
    )

    stream_rows = assert_csv_contract(
        compare_layout.comparison_results_dir / COMPARISON_STREAM_COMPARISON_CSV,
        COMPARISON_TABLE_FIELDS["stream_comparison"],
    )
    aggregate_rows = assert_csv_contract(
        compare_layout.comparison_results_dir / COMPARISON_AGGREGATE_COMPARISON_CSV,
        COMPARISON_TABLE_FIELDS["aggregate_comparison"],
    )
    expected_rows = assert_csv_contract(
        compare_layout.comparison_results_dir / COMPARISON_EXPECTED_WCRT_COMPARISON_CSV,
        COMPARISON_TABLE_FIELDS["expected_wcrt_comparison"],
    )

    stream_ids = [str(row["stream_id"]) for row in stream_rows]
    aggregate_row = aggregate_rows[0]
    assert result.summary["engine_status"] == "ok"
    assert len(stream_ids) == len(set(stream_ids))
    assert int(aggregate_row["missing_analysis_count"]) == 0
    assert int(aggregate_row["missing_simulation_count"]) == 0
    assert int(aggregate_row["duplicate_analysis_count"]) == 0
    assert int(aggregate_row["duplicate_simulation_count"]) == 0
    assert int(aggregate_row["matched_stream_count"]) == len(stream_rows)
    assert int(aggregate_row["reference_row_count"]) == len(expected_rows)
    assert {str(row["stream_id"]) for row in expected_rows} == set(stream_ids)
