"""Time-related helpers for run identifiers and timestamps."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp_compact() -> str:
    """Return a filesystem-safe UTC timestamp string."""

    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
