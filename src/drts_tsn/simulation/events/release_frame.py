"""Frame-release event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ReleaseFrameEvent:
    """Release a frame for a specific stream."""

    time_us: float
    stream_id: str
