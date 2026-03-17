"""Builders for stable comparison CSV row payloads."""

from __future__ import annotations

from drts_tsn.domain.results import ComparisonEntry


def build_stream_comparison_row(entry: ComparisonEntry) -> dict[str, object]:
    """Return one flat per-stream comparison row."""

    return {
        "stream_id": entry.stream_id,
        "analysis_traffic_class": entry.analysis_traffic_class,
        "simulation_traffic_class": entry.simulation_traffic_class,
        "analysis_route_id": entry.analysis_route_id,
        "simulation_route_id": entry.simulation_route_id,
        "analysis_hop_count": entry.analysis_hop_count,
        "simulation_hop_count": entry.simulation_hop_count,
        "analytical_wcrt_us": entry.analytical_wcrt_us,
        "simulated_worst_response_time_us": entry.simulated_worst_response_time_us,
        "expected_wcrt_us": entry.expected_wcrt_us,
        "absolute_difference_us": entry.absolute_difference_us,
        "analysis_minus_simulation_margin_us": entry.analysis_minus_simulation_margin_us,
        "analysis_to_simulation_ratio": entry.analysis_to_simulation_ratio,
        "simulation_exceeded_analysis": entry.simulation_exceeded_analysis,
        "class_mismatch": entry.class_mismatch,
        "path_mismatch": entry.path_mismatch,
        "status": entry.status.value,
        "discrepancy_flags": "|".join(entry.discrepancy_flags),
        "notes": " | ".join(entry.notes),
    }


def build_expected_wcrt_row(entry: ComparisonEntry) -> dict[str, object]:
    """Return one comparison row against expected/reference WCRT data."""

    return {
        "stream_id": entry.stream_id,
        "expected_wcrt_us": entry.expected_wcrt_us,
        "analytical_wcrt_us": entry.analytical_wcrt_us,
        "simulated_worst_response_time_us": entry.simulated_worst_response_time_us,
        "expected_minus_analysis_us": entry.expected_minus_analysis_us,
        "expected_minus_simulation_us": entry.expected_minus_simulation_us,
        "status": entry.status.value,
        "discrepancy_flags": "|".join(entry.discrepancy_flags),
        "notes": " | ".join(entry.notes),
    }
