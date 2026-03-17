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
            "simulation_response_time_us": row.simulation_response_time_us,
            "analysis_response_time_us": row.analysis_response_time_us,
            "absolute_difference_us": row.absolute_difference_us,
            "within_tolerance": row.within_tolerance,
            "status": row.status.value,
        }
        for row in result.entries
    ]
