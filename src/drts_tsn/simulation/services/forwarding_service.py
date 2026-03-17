"""Forwarding service for hop-by-hop line-topology frame progress."""

from __future__ import annotations

from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.outputs.trace_row_builders import build_forwarding_row


def forward_frame(frame_id: str, context: SimulationContext) -> None:
    """Advance one frame from its completed hop to the next egress port."""

    frame_state = context.network_state.frames[frame_id]
    previous_hop_index = frame_state.current_hop_index
    if previous_hop_index >= len(frame_state.route_link_ids) - 1:
        raise ValueError(f"Frame '{frame_id}' cannot be forwarded beyond its final hop.")

    from_link_id = frame_state.route_link_ids[previous_hop_index]
    next_hop_index = previous_hop_index + 1
    to_link_id = frame_state.route_link_ids[next_hop_index]
    frame_state.current_hop_index = next_hop_index
    frame_state.current_link_id = to_link_id
    context.network_state.statistics.forwarded_frames += 1

    context.metric_collector.record(
        "forwarding_trace",
        build_forwarding_row(
            timestamp_us=context.clock.current_time_us,
            stream_id=frame_state.stream_id,
            frame_id=frame_id,
            from_link_id=from_link_id,
            to_link_id=to_link_id,
            from_hop_index=previous_hop_index,
            to_hop_index=next_hop_index,
        ),
    )
    context.trace_collector.record(
        timestamp_us=context.clock.current_time_us,
        event_type="forward_frame",
        description=f"Forwarded frame '{frame_id}' from '{from_link_id}' to '{to_link_id}'.",
        attributes={"from_hop_index": previous_hop_index, "to_hop_index": next_hop_index},
    )
    context.event_queue.push(
        context.clock.current_time_us,
        SimulationEventType.ENQUEUE_FRAME.value,
        {"frame_id": frame_id, "port_id": to_link_id},
    )
    context.network_state.statistics.scheduled_events += 1
