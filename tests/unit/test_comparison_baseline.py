"""Unit tests for the comparison pipeline baseline."""

from __future__ import annotations

import pytest

from drts_tsn.analysis.engine import AnalysisEngine
from drts_tsn.comparison.aligner import align_stream_rows
from drts_tsn.comparison.engine import ComparisonEngine
from drts_tsn.comparison.metrics import absolute_difference, exceeds_analysis, ratio, signed_margin
from drts_tsn.domain.results import AnalysisRunResult, SimulationRunResult
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.simulation.engine import SimulationEngine


def test_align_stream_rows_reports_duplicates_and_missing_entries() -> None:
    """Alignment should remain deterministic and diagnose duplicate IDs."""

    alignment = align_stream_rows(
        analysis_rows=[
            {"stream_id": "stream-a", "end_to_end_wcrt_us": 10.0},
            {"stream_id": "stream-a", "end_to_end_wcrt_us": 11.0},
            {"stream_id": "stream-b", "end_to_end_wcrt_us": 12.0},
        ],
        simulation_rows=[
            {"stream_id": "stream-b", "max_response_time_us": 9.0},
            {"stream_id": "stream-c", "max_response_time_us": 8.0},
        ],
    )

    assert [row.stream_id for row in alignment.aligned_rows] == ["stream-a", "stream-b", "stream-c"]
    assert alignment.aligned_rows[0].analysis_row is not None
    assert alignment.aligned_rows[0].simulation_row is None
    assert alignment.aligned_rows[2].analysis_row is None
    assert alignment.aligned_rows[2].simulation_row is not None
    assert alignment.diagnostics[0]["diagnostic_code"] == "comparison.duplicate.analysis_stream_id"


def test_comparison_metric_helpers_compute_expected_values() -> None:
    """The comparison metric helpers should expose the core bound checks."""

    assert absolute_difference(12.0, 9.5) == pytest.approx(2.5)
    assert signed_margin(12.0, 9.5) == pytest.approx(2.5)
    assert ratio(12.0, 6.0) == pytest.approx(2.0)
    assert ratio(12.0, 0.0) is None
    assert exceeds_analysis(12.0, 12.5) is True
    assert exceeds_analysis(12.0, 11.5) is False


def test_comparison_engine_aligns_matching_baseline_results(sample_case_path) -> None:
    """Simulation and analysis should align cleanly on the bundled baseline case."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    simulation_result = SimulationEngine().run(prepared.normalized_case)
    analysis_result = AnalysisEngine().run(prepared.normalized_case)

    comparison = ComparisonEngine().run(simulation_result, analysis_result)

    assert len(comparison.entries) == 1
    entry = comparison.entries[0]
    assert entry.stream_id == "stream-a"
    assert entry.absolute_difference_us == pytest.approx(0.0)
    assert entry.analysis_minus_simulation_margin_us == pytest.approx(0.0)
    assert entry.simulation_exceeded_analysis is False
    assert entry.analysis_traffic_class == "class_a"
    assert entry.simulation_traffic_class == "class_a"
    assert comparison.summary["matched_stream_count"] == 1
    assert comparison.summary["simulation_exceeded_analysis_count"] == 0
    assert comparison.tables["stream_comparison"][0]["stream_id"] == "stream-a"
    assert comparison.tables["aggregate_comparison"][0]["engine_status"] == "ok"


def test_comparison_engine_marks_issue_status_for_missing_streams() -> None:
    """The aggregate engine status should reflect comparison issues."""

    comparison = ComparisonEngine().run(
        SimulationRunResult(
            case_id="case-a",
            run_id="sim-1",
            tables={"stream_summary": [{"stream_id": "stream-a", "max_response_time_us": 10.0}]},
        ),
        AnalysisRunResult(
            case_id="case-a",
            run_id="ana-1",
            tables={"stream_wcrt_summary": [{"stream_id": "stream-b", "end_to_end_wcrt_us": 9.0}]},
        ),
    )

    assert comparison.summary["engine_status"] == "issues_detected"
    assert comparison.tables["aggregate_comparison"][0]["engine_status"] == "issues_detected"


def test_comparison_engine_ignores_best_effort_rows_from_simulation_stream_summary() -> None:
    """Best-effort streams should not be flagged as missing analysis in AVB comparison."""

    comparison = ComparisonEngine().run(
        SimulationRunResult(
            case_id="case-a",
            run_id="sim-1",
            tables={
                "stream_summary": [
                    {"stream_id": "stream-be", "traffic_class": "best_effort", "max_response_time_us": 10.0},
                    {"stream_id": "stream-a", "traffic_class": "class_a", "max_response_time_us": 9.0},
                ]
            },
        ),
        AnalysisRunResult(
            case_id="case-a",
            run_id="ana-1",
            tables={"stream_wcrt_summary": [{"stream_id": "stream-a", "end_to_end_wcrt_us": 12.0}]},
        ),
    )

    assert [entry.stream_id for entry in comparison.entries] == ["stream-a"]
    assert comparison.summary["missing_analysis_count"] == 0
