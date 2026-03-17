"""Builders for comparison CSV rows."""

from __future__ import annotations

from drts_tsn.domain.results import ComparisonEntry


def build_comparison_row(entry: ComparisonEntry) -> dict[str, object]:
    """Return a flat row representation for a comparison entry."""

    return {
        "stream_id": entry.stream_id,
        "simulation_response_time_us": entry.simulation_response_time_us,
        "analysis_response_time_us": entry.analysis_response_time_us,
        "absolute_difference_us": entry.absolute_difference_us,
        "within_tolerance": entry.within_tolerance,
        "status": entry.status.value,
        "notes": " | ".join(entry.notes),
    }
