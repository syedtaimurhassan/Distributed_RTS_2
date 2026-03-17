"""Frame enqueue service for the baseline discrete-event simulator."""

from __future__ import annotations

from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.outputs.trace_row_builders import build_enqueue_row

from .scheduler_service import schedule_next_transmission


def enqueue_frame(frame_id: str, port_id: str, context: SimulationContext) -> None:
    """Place one frame into the correct egress queue and request scheduling."""

    frame_state = context.network_state.frames[frame_id]
    port_state = context.network_state.ports[port_id]
    queue_id = context.queue_ids_by_port_and_class[(port_id, frame_state.traffic_class)]
    queue_state = port_state.queues[queue_id]

    queue_state.pending_frame_ids.append(frame_id)
    queue_state.enqueued_count += 1
    queue_state.max_depth = max(queue_state.max_depth, len(queue_state.pending_frame_ids))
    context.network_state.statistics.enqueued_frames += 1
    frame_state.current_link_id = port_state.link_id
    frame_state.enqueue_timestamps_by_hop[frame_state.current_hop_index] = context.clock.current_time_us

    context.metric_collector.record(
        "enqueue_trace",
        build_enqueue_row(
            timestamp_us=context.clock.current_time_us,
            stream_id=frame_state.stream_id,
            frame_id=frame_id,
            port_id=port_id,
            link_id=port_state.link_id,
            queue_id=queue_id,
            traffic_class=frame_state.traffic_class,
            hop_index=frame_state.current_hop_index,
            queue_depth=len(queue_state.pending_frame_ids),
        ),
    )
    context.trace_collector.record(
        timestamp_us=context.clock.current_time_us,
        event_type="enqueue_frame",
        description=f"Enqueued frame '{frame_id}' into queue '{queue_id}'.",
        attributes={"port_id": port_id, "queue_id": queue_id},
    )
    schedule_next_transmission(port_id, context)
