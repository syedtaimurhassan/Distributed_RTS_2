"""Summary-table helpers for reporting outputs."""

from __future__ import annotations


def summarize_counts(**counts: int) -> list[dict[str, object]]:
    """Return count rows suitable for CSV or console rendering."""

    return [{"metric": key, "value": value} for key, value in counts.items()]
