"""Transmission handlers for the baseline discrete-event simulator."""

from __future__ import annotations

from drts_tsn.common.math_utils import serialization_delay_us
from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.outputs.trace_row_builders import build_transmission_row
from drts_tsn.simulation.policies.transmission_selection import select_transmission_candidate

from .credit_service import consume_credit_after_transmission
from .scheduler_service import schedule_next_transmission


def start_transmission(port_id: str, context: SimulationContext) -> None:
    """Start one non-preemptive transmission on the selected port, if eligible."""

    port_state = context.network_state.ports[port_id]
    port_state.scheduled_scheduler_time_us = None
    if port_state.current_transmission_frame_id is not None:
        return

    candidate = select_transmission_candidate(port_state, context)
    if candidate is None:
        schedule_next_transmission(port_id, context)
        return

    queue_state = port_state.queues[candidate.queue_id]
    if not queue_state.pending_frame_ids or queue_state.pending_frame_ids[0] != candidate.frame_id:
        raise ValueError(
            f"Transmission candidate '{candidate.frame_id}' is not at the FIFO head of queue '{candidate.queue_id}'."
        )

    frame_state = context.network_state.frames[candidate.frame_id]
    start_time_us = context.clock.current_time_us
    transmission_time_us = serialization_delay_us(frame_state.frame_size_bytes, port_state.speed_mbps)

    queue_state.pending_frame_ids.pop(0)
    frame_state.transmission_start_timestamps_by_hop[frame_state.current_hop_index] = start_time_us
    port_state.current_transmission_frame_id = candidate.frame_id
    context.network_state.statistics.transmissions_started += 1

    context.event_queue.push(
        start_time_us + transmission_time_us,
        SimulationEventType.TRANSMISSION_END.value,
        {
            "port_id": port_id,
            "queue_id": candidate.queue_id,
            "frame_id": candidate.frame_id,
            "hop_index": frame_state.current_hop_index,
            "start_time_us": start_time_us,
            "transmission_time_us": transmission_time_us,
        },
    )
    context.network_state.statistics.scheduled_events += 1
    context.trace_collector.record(
        timestamp_us=start_time_us,
        event_type="transmission_start",
        description=f"Started transmitting frame '{candidate.frame_id}' on port '{port_id}'.",
        attributes={"queue_id": candidate.queue_id, "hop_index": frame_state.current_hop_index},
    )


def finish_transmission(
    *,
    port_id: str,
    queue_id: str,
    frame_id: str,
    hop_index: int,
    start_time_us: float,
    transmission_time_us: float,
    context: SimulationContext,
) -> None:
    """Finish one transmission, record hop metrics, and trigger next progress."""

    port_state = context.network_state.ports[port_id]
    if port_state.current_transmission_frame_id != frame_id:
        raise ValueError(
            f"Port '{port_id}' finished frame '{frame_id}' while transmitting '{port_state.current_transmission_frame_id}'."
        )

    frame_state = context.network_state.frames[frame_id]
    queue_state = port_state.queues[queue_id]
    enqueue_time_us = frame_state.enqueue_timestamps_by_hop[hop_index]
    end_time_us = context.clock.current_time_us
    queueing_delay_us = start_time_us - enqueue_time_us
    response_time_so_far_us = end_time_us - frame_state.release_time_us

    credit_before, credit_after, service_spacing_us = consume_credit_after_transmission(
        port_id=port_id,
        queue_id=queue_id,
        transmission_time_us=transmission_time_us,
        context=context,
    )

    frame_state.transmission_end_timestamps_by_hop[hop_index] = end_time_us
    port_state.current_transmission_frame_id = None
    queue_state.transmitted_count += 1
    context.network_state.statistics.transmitted_frames += 1

    context.metric_collector.record(
        "transmission_trace",
        build_transmission_row(
            stream_id=frame_state.stream_id,
            frame_id=frame_id,
            port_id=port_id,
            link_id=port_state.link_id,
            queue_id=queue_id,
            hop_index=hop_index,
            traffic_class=frame_state.traffic_class,
            release_time_us=frame_state.release_time_us,
            enqueue_time_us=enqueue_time_us,
            start_time_us=start_time_us,
            end_time_us=end_time_us,
            queueing_delay_us=queueing_delay_us,
            transmission_time_us=transmission_time_us,
            response_time_so_far_us=response_time_so_far_us,
            credit_before=credit_before,
            credit_after=credit_after,
            service_spacing_us=service_spacing_us,
        ),
    )
    context.trace_collector.record(
        timestamp_us=end_time_us,
        event_type="transmission_end",
        description=f"Finished transmitting frame '{frame_id}' on port '{port_id}'.",
        attributes={"queue_id": queue_id, "hop_index": hop_index},
    )

    is_last_hop = hop_index >= len(frame_state.route_link_ids) - 1
    if is_last_hop:
        context.event_queue.push(
            end_time_us,
            SimulationEventType.DELIVERY_COMPLETE.value,
            {"frame_id": frame_id},
        )
    else:
        context.event_queue.push(
            end_time_us,
            SimulationEventType.FORWARD_FRAME.value,
            {"frame_id": frame_id},
        )
    context.network_state.statistics.scheduled_events += 1
    schedule_next_transmission(port_id, context)
