"""Scheduling service for queue eligibility and transmission wakeups."""

from __future__ import annotations

from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.policies.cbs import refresh_credit_state
from drts_tsn.simulation.policies.transmission_selection import select_transmission_candidate

from .credit_service import request_credit_update


def request_transmission_start(port_id: str, *, time_us: float, context: SimulationContext) -> None:
    """Request a scheduler wakeup for one port when not already scheduled earlier."""

    port_state = context.network_state.ports[port_id]
    scheduled_time_us = port_state.scheduled_scheduler_time_us
    if scheduled_time_us is not None and scheduled_time_us <= time_us + 1e-9:
        return
    port_state.scheduled_scheduler_time_us = time_us
    context.event_queue.push(
        time_us,
        SimulationEventType.TRANSMISSION_START.value,
        {"port_id": port_id},
    )
    context.network_state.statistics.scheduled_events += 1


def schedule_next_transmission(port_id: str, context: SimulationContext) -> None:
    """Schedule immediate or future port progress depending on queue eligibility."""

    port_state = context.network_state.ports[port_id]
    if port_state.current_transmission_frame_id is not None:
        return
    candidate = select_transmission_candidate(port_state, context)
    if candidate is not None:
        request_transmission_start(port_id, time_us=context.clock.current_time_us, context=context)
        return

    earliest_credit_update_time_us: float | None = None
    earliest_queue_id: str | None = None
    for queue_id, queue_state in port_state.queues.items():
        if not queue_state.pending_frame_ids or queue_id not in port_state.credits:
            continue
        credit_state = port_state.credits[queue_id]
        refresh_credit_state(credit_state, now_us=context.clock.current_time_us)
        if credit_state.next_eligible_time_us <= context.clock.current_time_us + 1e-9:
            request_transmission_start(port_id, time_us=context.clock.current_time_us, context=context)
            return
        if earliest_credit_update_time_us is None or credit_state.next_eligible_time_us < earliest_credit_update_time_us:
            earliest_credit_update_time_us = credit_state.next_eligible_time_us
            earliest_queue_id = queue_id
    if earliest_credit_update_time_us is not None and earliest_queue_id is not None:
        request_credit_update(earliest_queue_id, time_us=earliest_credit_update_time_us, context=context)
