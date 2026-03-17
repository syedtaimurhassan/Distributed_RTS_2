"""Scheduling service for queue eligibility and transmission wakeups."""

from __future__ import annotations

from drts_tsn.domain.enums import TrafficClass
from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.outputs.trace_row_builders import build_scheduler_decision_row
from drts_tsn.simulation.policies.transmission_selection import SchedulerDecision, build_scheduler_decision

from .credit_service import request_credit_update, synchronize_port_credits


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


def _record_scheduler_decision(port_id: str, *, reason: str, context: SimulationContext) -> SchedulerDecision:
    """Record one scheduler-decision trace row and return the decision."""

    port_state = context.network_state.ports[port_id]
    decision = build_scheduler_decision(port_state, context)
    class_a = decision.snapshots[TrafficClass.CLASS_A]
    class_b = decision.snapshots[TrafficClass.CLASS_B]
    best_effort = decision.snapshots[TrafficClass.BEST_EFFORT]
    context.metric_collector.record(
        "scheduler_decision_trace",
        build_scheduler_decision_row(
            timestamp_us=context.clock.current_time_us,
            port_id=port_id,
            link_id=port_state.link_id,
            class_a_head_frame_id=class_a.head_frame_id,
            class_a_queue_depth=class_a.queue_depth,
            class_a_credit=class_a.credit,
            class_b_head_frame_id=class_b.head_frame_id,
            class_b_queue_depth=class_b.queue_depth,
            class_b_credit=class_b.credit,
            be_head_frame_id=best_effort.head_frame_id,
            be_queue_depth=best_effort.queue_depth,
            current_transmission_frame_id=port_state.current_transmission_frame_id,
            selected_queue_id=decision.candidate.queue_id if decision.candidate is not None else None,
            selected_frame_id=decision.candidate.frame_id if decision.candidate is not None else None,
            selected_traffic_class=(
                decision.candidate.traffic_class.value if decision.candidate is not None else None
            ),
            decision_reason=f"{decision.reason}:{reason}",
        ),
    )
    return decision


def schedule_next_transmission(port_id: str, context: SimulationContext, *, reason: str = "scheduler") -> None:
    """Schedule immediate or future port progress depending on queue eligibility."""

    port_state = context.network_state.ports[port_id]
    synchronize_port_credits(port_id, context=context, reason=f"scheduler:{reason}")
    decision = _record_scheduler_decision(port_id, reason=reason, context=context)
    if port_state.current_transmission_frame_id is not None:
        return
    if decision.candidate is not None:
        request_transmission_start(port_id, time_us=context.clock.current_time_us, context=context)
        return

    earliest_credit_update_time_us: float | None = None
    earliest_queue_id: str | None = None
    for queue_id, queue_state in port_state.queues.items():
        if not queue_state.pending_frame_ids or queue_id not in port_state.credits:
            continue
        credit_state = port_state.credits[queue_id]
        if credit_state.current_credit >= 0:
            continue
        if earliest_credit_update_time_us is None or credit_state.next_eligible_time_us < earliest_credit_update_time_us:
            earliest_credit_update_time_us = credit_state.next_eligible_time_us
            earliest_queue_id = queue_id
    if earliest_credit_update_time_us is not None and earliest_queue_id is not None:
        request_credit_update(earliest_queue_id, time_us=earliest_credit_update_time_us, context=context)
