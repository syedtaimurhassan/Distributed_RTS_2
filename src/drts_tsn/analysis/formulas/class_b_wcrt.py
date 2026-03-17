"""Per-link Class B WCRT composition for the baseline model."""

from __future__ import annotations


def compute_class_b_wcrt_us(
    *,
    transmission_time_us: float,
    same_priority_interference_us: float,
    lower_priority_interference_us: float,
    higher_priority_interference_us: float,
) -> float:
    """Return the baseline Class B per-link WCRT."""

    return (
        transmission_time_us
        + same_priority_interference_us
        + lower_priority_interference_us
        + higher_priority_interference_us
    )
