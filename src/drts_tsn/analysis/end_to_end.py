"""End-to-end aggregation helpers for analytical results."""

from __future__ import annotations


def aggregate_link_delays(delays_us: list[float | None]) -> float | None:
    """Aggregate per-link delays into an end-to-end WCRT result."""

    if any(delay is None for delay in delays_us):
        return None
    return sum(delay for delay in delays_us if delay is not None)


def accumulate_link_delays(delays_us: list[float]) -> list[float]:
    """Return the running end-to-end accumulation across ordered links."""

    cumulative = 0.0
    rows: list[float] = []
    for delay_us in delays_us:
        cumulative += delay_us
        rows.append(cumulative)
    return rows
