"""Small numeric helpers shared by scaffold code."""

from __future__ import annotations

import math


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a floating-point value into the provided range."""

    return max(minimum, min(maximum, value))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Return a stable default when the denominator is zero."""

    if denominator == 0:
        return default
    return numerator / denominator


def serialization_delay_us(frame_size_bytes: int, link_speed_mbps: float) -> float:
    """Return serialization delay in microseconds for a frame on a link."""

    if link_speed_mbps <= 0:
        raise ValueError("Link speed must be positive.")
    return (frame_size_bytes * 8.0) / link_speed_mbps


def ceiling_division_ratio(window_us: float, period_us: float) -> int:
    """Return ceil(window / period) for strictly positive periods."""

    if period_us <= 0:
        raise ValueError("Period must be positive.")
    if window_us <= 0:
        return 0
    return int(math.ceil(window_us / period_us))


def integer_hyperperiod(values: list[float], *, limit: int = 1_000_000) -> int:
    """Return an integer hyperperiod for microsecond periods, capped to a safe limit."""

    if not values:
        return 1
    integers = [max(1, int(round(value))) for value in values]
    hyperperiod = integers[0]
    for integer in integers[1:]:
        hyperperiod = math.lcm(hyperperiod, integer)
        if hyperperiod > limit:
            return limit
    return hyperperiod
