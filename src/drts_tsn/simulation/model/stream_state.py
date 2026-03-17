"""Per-stream simulation state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StreamState:
    """Mutable counters for a stream during simulation."""

    stream_id: str
    route_id: str
    released_frames: int = 0
    completed_frames: int = 0
    next_release_index: int = 0
