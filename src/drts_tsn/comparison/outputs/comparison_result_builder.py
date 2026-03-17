"""Builders for top-level comparison result containers."""

from __future__ import annotations

from drts_tsn.domain.results import ComparisonRunResult


def comparison_result_to_rows(result: ComparisonRunResult) -> list[dict[str, object]]:
    """Return flat per-stream comparison rows."""

    return [
        {
            "stream_id": entry.stream_id,
            "simulation_response_time_us": entry.simulation_response_time_us,
            "analysis_response_time_us": entry.analysis_response_time_us,
            "absolute_difference_us": entry.absolute_difference_us,
            "within_tolerance": entry.within_tolerance,
            "status": entry.status.value,
        }
        for entry in result.entries
    ]


def comparison_summary_rows(result: ComparisonRunResult) -> list[dict[str, object]]:
    """Return a one-row comparison summary CSV payload."""

    return [dict(result.summary)]
