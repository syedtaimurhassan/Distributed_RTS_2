"""Credit-update event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CreditUpdateEvent:
    """Update CBS credit for a queue."""

    time_us: float
    queue_id: str
