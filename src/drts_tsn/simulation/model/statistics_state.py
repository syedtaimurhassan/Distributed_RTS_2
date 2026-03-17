"""Aggregate mutable simulation statistics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StatisticsState:
    """Summary counters maintained by the simulation engine."""

    processed_events: int = 0
    scheduled_events: int = 0
    released_frames: int = 0
    enqueued_frames: int = 0
    transmissions_started: int = 0
    transmitted_frames: int = 0
    forwarded_frames: int = 0
    delivered_frames: int = 0
    finalized: bool = False
    stop_reason: str | None = None
