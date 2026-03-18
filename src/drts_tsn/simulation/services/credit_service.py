"""CBS credit services for the baseline simulator."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.domain.credits import effective_idle_slope_mbps, effective_send_slope_mbps
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.queues import QueueDefinition
from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.policies.cbs import (
    CreditComputation,
    credit_recovery_completion_time_us,
    integrate_credit,
)
from drts_tsn.simulation.outputs.trace_row_builders import build_credit_trace_row


@dataclass(slots=True, frozen=True)
class CreditUpdateRecord:
    """One concrete credit-state change emitted by the simulator."""

    queue_id: str
    computation: CreditComputation
    blocking_frame_id: str | None
    transmitting_frame_id: str | None
    related_frame_id: str | None


def resolve_queue_port_id(queue_id: str, context: SimulationContext) -> str:
    """Resolve the owning port for a queue without depending on queue-id formatting."""

    for port_id, port_state in context.network_state.ports.items():
        if queue_id in port_state.queues:
            return port_id
    raise ValueError(f"Unknown simulation queue '{queue_id}'.")


def _queue_definition_for_queue(queue_id: str, context: SimulationContext) -> QueueDefinition:
    """Return the queue definition associated with one queue state."""

    port_id = resolve_queue_port_id(queue_id, context)
    traffic_class = context.network_state.ports[port_id].queues[queue_id].traffic_class
    for queue_definition in context.case.queues:
        if queue_definition.traffic_class == traffic_class:
            return queue_definition
    raise ValueError(f"Missing queue definition for traffic class '{traffic_class.value}'.")


def idle_slope_mbps_for_queue(queue_id: str, context: SimulationContext) -> float:
    """Return the configured CBS idle slope for one AVB queue."""

    queue_definition = _queue_definition_for_queue(queue_id, context)
    if queue_definition.credit_parameters is None:
        return 0.0
    port_id = resolve_queue_port_id(queue_id, context)
    link_speed_mbps = context.network_state.ports[port_id].speed_mbps
    return effective_idle_slope_mbps(queue_definition.credit_parameters, link_speed_mbps=link_speed_mbps)


def send_slope_mbps_for_queue(queue_id: str, context: SimulationContext) -> float:
    """Return the configured CBS send-slope magnitude for one AVB queue."""

    queue_definition = _queue_definition_for_queue(queue_id, context)
    if queue_definition.credit_parameters is None:
        return 0.0
    port_id = resolve_queue_port_id(queue_id, context)
    link_speed_mbps = context.network_state.ports[port_id].speed_mbps
    return effective_send_slope_mbps(queue_definition.credit_parameters, link_speed_mbps=link_speed_mbps)


def _record_credit_trace(
    *,
    port_id: str,
    queue_id: str,
    computation: CreditComputation,
    related_frame_id: str | None,
    blocking_frame_id: str | None,
    transmitting_frame_id: str | None,
    context: SimulationContext,
) -> None:
    """Write one machine-readable credit trace row."""

    port_state = context.network_state.ports[port_id]
    queue_state = port_state.queues[queue_id]
    context.metric_collector.record(
        "credit_trace",
        build_credit_trace_row(
            timestamp_us=context.clock.current_time_us,
            port_id=port_id,
            link_id=port_state.link_id,
            queue_id=queue_id,
            traffic_class=queue_state.traffic_class,
            credit_before=computation.credit_before,
            credit_after=computation.credit_after,
            change_reason=computation.reason,
            slope_mbps=computation.slope_mbps,
            elapsed_time_us=computation.elapsed_time_us,
            related_frame_id=related_frame_id,
            blocking_frame_id=blocking_frame_id,
            transmitting_frame_id=transmitting_frame_id,
            capped_at_zero=computation.capped_at_zero,
        ),
    )


def synchronize_port_credits(
    port_id: str,
    *,
    context: SimulationContext,
    reason: str,
    related_frame_id: str | None = None,
) -> dict[str, CreditUpdateRecord]:
    """Synchronize all AVB credits on one port to the current simulation time."""

    port_state = context.network_state.ports[port_id]
    transmitting_frame = (
        context.network_state.frames[port_state.current_transmission_frame_id]
        if port_state.current_transmission_frame_id is not None
        else None
    )
    blocking_frame_id = (
        transmitting_frame.frame_id if transmitting_frame is not None and transmitting_frame.traffic_class is TrafficClass.BEST_EFFORT else None
    )
    updates: dict[str, CreditUpdateRecord] = {}
    for queue_id, credit_state in port_state.credits.items():
        queue_state = port_state.queues[queue_id]
        elapsed_time_us = context.clock.current_time_us - credit_state.last_update_time_us
        if elapsed_time_us < -1e-9:
            raise ValueError("CBS credit state cannot move backwards in time.")
        computation = integrate_credit(
            current_credit=credit_state.current_credit,
            elapsed_time_us=max(elapsed_time_us, 0.0),
            idle_slope_mbps=idle_slope_mbps_for_queue(queue_id, context),
            send_slope_mbps=send_slope_mbps_for_queue(queue_id, context),
            transmitting_this_class=(
                transmitting_frame is not None and transmitting_frame.traffic_class == queue_state.traffic_class
            ),
            blocked_by_best_effort=(
                blocking_frame_id is not None and bool(queue_state.pending_frame_ids)
            ),
        )
        credit_state.current_credit = computation.credit_after
        credit_state.last_update_time_us = context.clock.current_time_us
        if computation.credit_after != computation.credit_before or computation.reason not in {"hold", "no_time_elapsed"}:
            _record_credit_trace(
                port_id=port_id,
                queue_id=queue_id,
                computation=CreditComputation(
                    credit_before=computation.credit_before,
                    credit_after=computation.credit_after,
                    reason=f"{computation.reason}:{reason}",
                    slope_mbps=computation.slope_mbps,
                    elapsed_time_us=computation.elapsed_time_us,
                    capped_at_zero=computation.capped_at_zero,
                ),
                related_frame_id=related_frame_id,
                blocking_frame_id=blocking_frame_id,
                transmitting_frame_id=transmitting_frame.frame_id if transmitting_frame is not None else None,
                context=context,
            )
        updates[queue_id] = CreditUpdateRecord(
            queue_id=queue_id,
            computation=computation,
            blocking_frame_id=blocking_frame_id,
            transmitting_frame_id=transmitting_frame.frame_id if transmitting_frame is not None else None,
            related_frame_id=related_frame_id,
        )
    normalize_idle_positive_credits(port_id, context=context, reason=reason, related_frame_id=related_frame_id)
    refresh_next_eligible_times(port_id, context)
    return updates


def normalize_idle_positive_credits(
    port_id: str,
    *,
    context: SimulationContext,
    reason: str,
    related_frame_id: str | None = None,
) -> None:
    """Reset positive credit to zero when a class has no queued or transmitting frame."""

    port_state = context.network_state.ports[port_id]
    transmitting_frame = (
        context.network_state.frames[port_state.current_transmission_frame_id]
        if port_state.current_transmission_frame_id is not None
        else None
    )
    for queue_id, credit_state in port_state.credits.items():
        queue_state = port_state.queues[queue_id]
        transmitting_this_class = (
            transmitting_frame is not None and transmitting_frame.traffic_class == queue_state.traffic_class
        )
        if queue_state.pending_frame_ids or transmitting_this_class or credit_state.current_credit <= 0.0:
            continue
        computation = CreditComputation(
            credit_before=credit_state.current_credit,
            credit_after=0.0,
            reason=f"reset_no_pending:{reason}",
            slope_mbps=0.0,
            elapsed_time_us=0.0,
        )
        credit_state.current_credit = 0.0
        _record_credit_trace(
            port_id=port_id,
            queue_id=queue_id,
            computation=computation,
            related_frame_id=related_frame_id,
            blocking_frame_id=None,
            transmitting_frame_id=transmitting_frame.frame_id if transmitting_frame is not None else None,
            context=context,
        )


def refresh_next_eligible_times(port_id: str, context: SimulationContext) -> None:
    """Recompute zero-crossing eligibility times for all AVB queues on one port."""

    port_state = context.network_state.ports[port_id]
    for queue_id, credit_state in port_state.credits.items():
        queue_state = port_state.queues[queue_id]
        if not queue_state.pending_frame_ids and credit_state.current_credit >= 0:
            credit_state.next_eligible_time_us = context.clock.current_time_us
            continue
        recovery_time_us = credit_recovery_completion_time_us(
            current_credit=credit_state.current_credit,
            idle_slope_mbps=idle_slope_mbps_for_queue(queue_id, context),
            now_us=context.clock.current_time_us,
        )
        credit_state.next_eligible_time_us = recovery_time_us or context.clock.current_time_us


def request_credit_update(queue_id: str, *, time_us: float, context: SimulationContext) -> None:
    """Request a future credit update for one queue when needed."""

    port_id = resolve_queue_port_id(queue_id, context)
    queue_state = context.network_state.ports[port_id].queues[queue_id]
    scheduled_time_us = queue_state.scheduled_credit_update_time_us
    if scheduled_time_us is not None and scheduled_time_us <= time_us + 1e-9:
        return
    queue_state.scheduled_credit_update_time_us = time_us
    context.event_queue.push(
        time_us,
        SimulationEventType.CREDIT_UPDATE.value,
        {"queue_id": queue_id},
    )
    context.network_state.statistics.scheduled_events += 1


def update_credit(queue_id: str, context: SimulationContext) -> None:
    """Refresh credits on the owning port and clear the scheduled wakeup marker."""

    port_id = resolve_queue_port_id(queue_id, context)
    port_state = context.network_state.ports[port_id]
    port_state.queues[queue_id].scheduled_credit_update_time_us = None
    synchronize_port_credits(port_id, context=context, reason="credit_update", related_frame_id=None)
    context.trace_collector.record(
        timestamp_us=context.clock.current_time_us,
        event_type="credit_update",
        description=f"Updated credit state for queue '{queue_id}'.",
        attributes={"port_id": port_id, "queue_id": queue_id},
    )
