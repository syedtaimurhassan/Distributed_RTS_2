"""Per-frame simulation state."""

from __future__ import annotations

from dataclasses import dataclass, field

from drts_tsn.domain.enums import TrafficClass


@dataclass(slots=True)
class FrameState:
    """Mutable state for an individual frame instance."""

    frame_id: str
    stream_id: str
    traffic_class: TrafficClass
    route_id: str
    release_index: int
    release_time_us: float
    frame_size_bytes: int
    route_link_ids: list[str] = field(default_factory=list)
    current_hop_index: int = 0
    current_link_id: str | None = None
    enqueue_timestamps_by_hop: dict[int, float] = field(default_factory=dict)
    transmission_start_timestamps_by_hop: dict[int, float] = field(default_factory=dict)
    transmission_end_timestamps_by_hop: dict[int, float] = field(default_factory=dict)
    delivery_time_us: float | None = None
