"""Diagnostic helpers for comparison outputs."""

from __future__ import annotations


def build_diagnostic_row(
    *,
    diagnostic_code: str,
    severity: str,
    message: str,
    stream_id: str | None = None,
    source: str = "comparison",
) -> dict[str, object]:
    """Return one machine-readable comparison diagnostic row."""

    return {
        "diagnostic_code": diagnostic_code,
        "severity": severity,
        "stream_id": stream_id,
        "source": source,
        "message": message,
    }
