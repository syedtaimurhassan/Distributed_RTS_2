"""Named event types for the simulation scaffold."""

from __future__ import annotations

from enum import Enum


class SimulationEventType(str, Enum):
    """Core event types reserved for the simulation engine."""

    RELEASE_FRAME = "release_frame"
    ENQUEUE_FRAME = "enqueue_frame"
    TRANSMISSION_START = "transmission_start"
    TRANSMISSION_END = "transmission_end"
    FORWARD_FRAME = "forward_frame"
    DELIVERY_COMPLETE = "delivery_complete"
    CREDIT_UPDATE = "credit_update"
    FINALIZE_RUN = "finalize_run"
