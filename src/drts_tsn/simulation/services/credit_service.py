"""CBS credit services for the baseline simulator."""

from __future__ import annotations

from drts_tsn.simulation.context import SimulationContext
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.policies.cbs import apply_transmission_credit, refresh_credit_state


def resolve_queue_port_id(queue_id: str, context: SimulationContext) -> str:
    """Resolve the owning port for a queue without depending on queue-id formatting."""

    for port_id, port_state in context.network_state.ports.items():
        if queue_id in port_state.queues:
            return port_id
    raise ValueError(f"Unknown simulation queue '{queue_id}'.")


def reserved_share_for_queue(port_id: str, queue_id: str, context: SimulationContext) -> float:
    """Return the normalized reserved share for one queue on one port."""

    queue_state = context.network_state.ports[port_id].queues[queue_id]
    if queue_state.traffic_class == TrafficClass.BEST_EFFORT:
        return 1.0
    queue_definition = next(
        queue for queue in context.case.queues if queue.traffic_class == queue_state.traffic_class
    )
    if queue_definition.credit_parameters is None:
        return 1.0
    port_speed_mbps = context.network_state.ports[port_id].speed_mbps
    return queue_definition.credit_parameters.idle_slope_mbps / port_speed_mbps


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
    """Refresh credit for one queue and clear its scheduled wakeup marker."""

    port_id = resolve_queue_port_id(queue_id, context)
    port_state = context.network_state.ports[port_id]
    queue_state = port_state.queues[queue_id]
    queue_state.scheduled_credit_update_time_us = None
    credit_state = port_state.credits.get(queue_id)
    if credit_state is None:
        return
    refresh_credit_state(credit_state, now_us=context.clock.current_time_us)
    context.trace_collector.record(
        timestamp_us=context.clock.current_time_us,
        event_type="credit_update",
        description=f"Updated credit state for queue '{queue_id}'.",
        attributes={"port_id": port_id, "queue_id": queue_id},
    )


def consume_credit_after_transmission(
    *,
    port_id: str,
    queue_id: str,
    transmission_time_us: float,
    context: SimulationContext,
) -> tuple[float | None, float | None, float]:
    """Apply simplified CBS post-transmission credit effects and return trace values."""

    credit_state = context.network_state.ports[port_id].credits.get(queue_id)
    if credit_state is None:
        return None, None, transmission_time_us
    reserved_share = reserved_share_for_queue(port_id, queue_id, context)
    credit_before, credit_after = apply_transmission_credit(
        credit_state,
        transmission_time_us=transmission_time_us,
        reserved_share=reserved_share,
        end_time_us=context.clock.current_time_us,
    )
    return credit_before, credit_after, transmission_time_us / reserved_share
