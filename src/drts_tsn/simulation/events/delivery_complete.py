"""Delivery-complete event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DeliveryCompleteEvent:
    """Mark one frame as fully delivered."""

    time_us: float
    frame_id: str
