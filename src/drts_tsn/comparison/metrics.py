"""Pure metric helpers for aligned analysis and simulation outputs."""

from __future__ import annotations


def absolute_difference(left: float | None, right: float | None) -> float | None:
    """Return the absolute difference when both values are present."""

    if left is None or right is None:
        return None
    return abs(left - right)


def signed_margin(analysis_value: float | None, simulation_value: float | None) -> float | None:
    """Return `analysis - simulation` when both values are present."""

    if analysis_value is None or simulation_value is None:
        return None
    return analysis_value - simulation_value


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    """Return a ratio when both values are present and the denominator is positive."""

    if numerator is None or denominator is None or denominator <= 0.0:
        return None
    return numerator / denominator


def exceeds_analysis(analysis_value: float | None, simulation_value: float | None) -> bool | None:
    """Return whether the simulated value exceeds the analytical bound."""

    if analysis_value is None or simulation_value is None:
        return None
    return simulation_value > analysis_value
