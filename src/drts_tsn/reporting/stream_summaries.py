"""Stream summary helpers."""

from __future__ import annotations

from drts_tsn.domain.results import AnalysisRunResult, ComparisonRunResult, SimulationRunResult


def simulation_stream_rows(result: SimulationRunResult) -> list[dict[str, object]]:
    """Return flat simulation stream rows."""

    return [
        {
            "stream_id": row.stream_id,
            "max_response_time_us": row.max_response_time_us,
            "frame_count": row.frame_count,
            "status": row.status.value,
        }
        for row in result.stream_results
    ]


def analysis_stream_rows(result: AnalysisRunResult) -> list[dict[str, object]]:
    """Return flat analysis stream rows."""

    return [
        {
            "stream_id": row.stream_id,
            "wcrt_us": row.wcrt_us,
            "status": row.status.value,
        }
        for row in result.stream_results
    ]


def comparison_stream_rows(result: ComparisonRunResult) -> list[dict[str, object]]:
    """Return flat comparison rows."""

    return [
        {
            "stream_id": row.stream_id,
            "simulated_worst_response_time_us": row.simulated_worst_response_time_us,
            "analytical_wcrt_us": row.analytical_wcrt_us,
            "absolute_difference_us": row.absolute_difference_us,
            "analysis_minus_simulation_margin_us": row.analysis_minus_simulation_margin_us,
            "simulation_exceeded_analysis": row.simulation_exceeded_analysis,
            "status": row.status.value,
        }
        for row in result.entries
    ]
