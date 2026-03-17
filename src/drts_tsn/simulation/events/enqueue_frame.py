"""Frame-enqueue event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EnqueueFrameEvent:
    """Enqueue a frame into a port queue."""

    time_us: float
    frame_id: str
    port_id: str
