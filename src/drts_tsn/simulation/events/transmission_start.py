"""Transmission-start event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TransmissionStartEvent:
    """Start transmitting a frame."""

    time_us: float
    port_id: str
