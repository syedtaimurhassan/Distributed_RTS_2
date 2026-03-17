"""Per-port simulation state."""

from __future__ import annotations

from dataclasses import dataclass, field

from .credit_state import CreditState
from .queue_state import QueueState


@dataclass(slots=True)
class PortState:
    """Mutable state associated with a single egress port."""

    port_id: str
    link_id: str
    source_node_id: str
    target_node_id: str
    speed_mbps: float
    queues: dict[str, QueueState] = field(default_factory=dict)
    credits: dict[str, CreditState] = field(default_factory=dict)
    current_transmission_frame_id: str | None = None
    scheduled_scheduler_time_us: float | None = None
