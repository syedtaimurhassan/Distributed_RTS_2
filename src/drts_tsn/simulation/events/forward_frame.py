"""Forward-frame event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ForwardFrameEvent:
    """Forward a frame to the next hop."""

    time_us: float
    frame_id: str
