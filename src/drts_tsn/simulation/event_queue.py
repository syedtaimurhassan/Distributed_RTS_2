"""Priority queue for scheduled simulation events."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class ScheduledEvent:
    """A heap-ordered simulation event."""

    time_us: float
    sequence: int
    event_name: str = field(compare=False)
    payload: dict[str, Any] = field(default_factory=dict, compare=False)


class EventQueue:
    """A minimal heap-based event queue."""

    def __init__(self) -> None:
        self._events: list[ScheduledEvent] = []
        self._sequence = 0

    def push(self, time_us: float, event_name: str, payload: dict[str, Any] | None = None) -> None:
        """Schedule an event."""

        self._sequence += 1
        heapq.heappush(
            self._events,
            ScheduledEvent(
                time_us=time_us,
                sequence=self._sequence,
                event_name=event_name,
                payload=payload or {},
            ),
        )

    def pop(self) -> ScheduledEvent:
        """Pop the next event in time order."""

        return heapq.heappop(self._events)

    def peek(self) -> ScheduledEvent | None:
        """Return the next event without removing it."""

        return self._events[0] if self._events else None

    def is_empty(self) -> bool:
        """Return whether the queue has no pending events."""

        return not self._events

    def __len__(self) -> int:
        """Return the number of pending events."""

        return len(self._events)
