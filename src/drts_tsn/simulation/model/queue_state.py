"""Per-queue simulation state."""

from __future__ import annotations

from dataclasses import dataclass, field

from drts_tsn.domain.enums import TrafficClass


@dataclass(slots=True)
class QueueState:
    """Mutable state associated with a queue."""

    queue_id: str
    traffic_class: TrafficClass
    pending_frame_ids: list[str] = field(default_factory=list)
    enqueued_count: int = 0
    transmitted_count: int = 0
    max_depth: int = 0
    scheduled_credit_update_time_us: float | None = None
