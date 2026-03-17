"""Event dispatch for the baseline discrete-event simulator."""

from __future__ import annotations

from .context import SimulationContext
from .event_queue import ScheduledEvent
from .event_types import SimulationEventType
from .services.credit_service import resolve_queue_port_id, update_credit
from .services.enqueue_service import enqueue_frame
from .services.forwarding_service import forward_frame
from .services.release_service import release_frame
from .services.response_time_service import complete_delivery
from .services.scheduler_service import schedule_next_transmission
from .services.transmission_service import finish_transmission, start_transmission


def dispatch_event(event: ScheduledEvent, context: SimulationContext) -> None:
    """Dispatch one scheduled event to the appropriate service routine."""

    event_type = SimulationEventType(event.event_name)
    if event_type is SimulationEventType.RELEASE_FRAME:
        release_frame(str(event.payload["stream_id"]), context)
        return
    if event_type is SimulationEventType.ENQUEUE_FRAME:
        enqueue_frame(str(event.payload["frame_id"]), str(event.payload["port_id"]), context)
        return
    if event_type is SimulationEventType.TRANSMISSION_START:
        start_transmission(str(event.payload["port_id"]), context)
        return
    if event_type is SimulationEventType.TRANSMISSION_END:
        finish_transmission(
            port_id=str(event.payload["port_id"]),
            queue_id=str(event.payload["queue_id"]),
            frame_id=str(event.payload["frame_id"]),
            hop_index=int(event.payload["hop_index"]),
            start_time_us=float(event.payload["start_time_us"]),
            transmission_time_us=float(event.payload["transmission_time_us"]),
            context=context,
        )
        return
    if event_type is SimulationEventType.FORWARD_FRAME:
        forward_frame(str(event.payload["frame_id"]), context)
        return
    if event_type is SimulationEventType.DELIVERY_COMPLETE:
        complete_delivery(str(event.payload["frame_id"]), context)
        return
    if event_type is SimulationEventType.CREDIT_UPDATE:
        queue_id = str(event.payload["queue_id"])
        update_credit(queue_id, context)
        schedule_next_transmission(resolve_queue_port_id(queue_id, context), context)
        return
    if event_type is SimulationEventType.FINALIZE_RUN:
        context.network_state.statistics.finalized = True
        context.network_state.statistics.stop_reason = str(
            event.payload.get("reason", context.network_state.statistics.stop_reason or "completed")
        )
        context.trace_collector.record(
            timestamp_us=context.clock.current_time_us,
            event_type="finalize_run",
            description="Finalized simulation run.",
            attributes={"reason": context.network_state.statistics.stop_reason},
        )
        return
    raise ValueError(f"Unsupported simulation event type '{event.event_name}'.")
