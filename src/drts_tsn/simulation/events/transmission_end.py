"""Transmission-end event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TransmissionEndEvent:
    """Finish transmitting a frame."""

    time_us: float
    port_id: str
    queue_id: str
    frame_id: str
    hop_index: int
    start_time_us: float
    transmission_time_us: float
