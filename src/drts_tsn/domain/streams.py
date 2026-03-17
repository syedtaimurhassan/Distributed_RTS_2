"""Canonical stream entities for TSN traffic definitions."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import TrafficClass


@dataclass(slots=True, frozen=True)
class Stream:
    """A canonical traffic stream definition."""

    id: str
    name: str
    source_node_id: str
    destination_node_id: str
    traffic_class: TrafficClass
    period_us: float
    deadline_us: float
    max_frame_size_bytes: int
    route_id: str | None = None
    priority: int | None = None
