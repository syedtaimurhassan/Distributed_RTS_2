"""Unit tests for simulation event-queue ordering."""

from __future__ import annotations

from drts_tsn.simulation.event_queue import EventQueue


def test_event_queue_orders_by_time_then_sequence() -> None:
    """Events should pop in chronological order and preserve insertion order on ties."""

    queue = EventQueue()
    queue.push(5.0, "late")
    queue.push(1.0, "early")
    queue.push(5.0, "late-second")

    first = queue.pop()
    second = queue.pop()
    third = queue.pop()

    assert first.event_name == "early"
    assert second.event_name == "late"
    assert third.event_name == "late-second"
