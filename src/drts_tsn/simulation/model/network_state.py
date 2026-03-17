"""Aggregate network state for a simulation run."""

from __future__ import annotations

from dataclasses import dataclass, field

from .frame_state import FrameState
from .port_state import PortState
from .statistics_state import StatisticsState
from .stream_state import StreamState


@dataclass(slots=True)
class NetworkState:
    """High-level mutable network state."""

    ports: dict[str, PortState] = field(default_factory=dict)
    streams: dict[str, StreamState] = field(default_factory=dict)
    frames: dict[str, FrameState] = field(default_factory=dict)
    statistics: StatisticsState = field(default_factory=StatisticsState)
