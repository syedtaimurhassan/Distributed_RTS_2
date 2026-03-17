"""Bandwidth feasibility helpers for baseline AVB analysis."""

from __future__ import annotations


def reserved_bandwidth_feasible(cumulative_reserved_share: float, *, limit: float = 1.0) -> bool:
    """Return whether the reserved bandwidth bound is satisfied."""

    return cumulative_reserved_share <= limit + 1e-9
