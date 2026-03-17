"""Comparison metric helpers."""

from __future__ import annotations


def absolute_difference(left: float | None, right: float | None) -> float | None:
    """Return absolute error when both values are present."""

    if left is None or right is None:
        return None
    return abs(left - right)
