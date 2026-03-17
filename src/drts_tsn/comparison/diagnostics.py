"""Diagnostic helpers for comparison outputs."""

from __future__ import annotations

from drts_tsn.domain.results import ComparisonEntry


def build_diagnostics(entries: list[ComparisonEntry]) -> list[str]:
    """Build high-level diagnostic messages for a comparison result."""

    if not entries:
        return ["No comparable stream results were available."]
    missing = [entry.stream_id for entry in entries if entry.absolute_difference_us is None]
    if missing:
        return [
            "Comparison contains streams without both analytical and simulation values.",
            f"Incomplete streams: {', '.join(missing)}",
        ]
    failing = [entry.stream_id for entry in entries if entry.within_tolerance is False]
    if failing:
        return [
            "Comparison completed and found streams outside tolerance.",
            f"Outside tolerance: {', '.join(failing)}",
        ]
    return ["Comparison completed with all comparable streams within tolerance."]
