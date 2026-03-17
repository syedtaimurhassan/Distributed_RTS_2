"""Base trace row models shared by subsystem trace collectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TraceRow:
    """A generic trace row emitted by a subsystem collector."""

    timestamp_us: float
    event_type: str
    description: str
    attributes: dict[str, Any] = field(default_factory=dict)
