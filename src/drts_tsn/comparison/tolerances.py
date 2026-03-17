"""Tolerance helpers for result comparison."""

from __future__ import annotations


DEFAULT_ABSOLUTE_TOLERANCE_US = 1e-6


def within_tolerance(
    difference_us: float | None,
    *,
    absolute_tolerance_us: float = DEFAULT_ABSOLUTE_TOLERANCE_US,
) -> bool | None:
    """Return whether a difference lies within tolerance."""

    if difference_us is None:
        return None
    return difference_us <= absolute_tolerance_us
