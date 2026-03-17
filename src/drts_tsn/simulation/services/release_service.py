"""Frame release service."""

from __future__ import annotations

from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.model.frame_state import FrameState
from drts_tsn.simulation.outputs.trace_row_builders import build_frame_release_row

from .stop_condition_service import can_schedule_release


def release_frame(stream_id: str, context: SimulationContext) -> None:
    """Instantiate one frame and enqueue it at the first hop."""

    stream = context.streams_by_id[stream_id]
    route_link_ids = context.route_links_by_stream_id.get(stream_id, [])
    if not route_link_ids:
        raise ValueError(f"Simulation requires a resolved directed path for stream '{stream_id}'.")
    stream_state = context.network_state.streams[stream_id]
    release_index = stream_state.next_release_index
    frame_id = f"{stream_id}-rel-{release_index}"
    frame_state = FrameState(
        frame_id=frame_id,
        stream_id=stream_id,
        traffic_class=stream.traffic_class,
        route_id=stream.route_id or stream.id,
        release_index=release_index,
        release_time_us=context.clock.current_time_us,
        frame_size_bytes=stream.max_frame_size_bytes,
        route_link_ids=list(route_link_ids),
        current_hop_index=0,
        current_link_id=route_link_ids[0],
    )
    context.network_state.frames[frame_id] = frame_state
    stream_state.released_frames += 1
    stream_state.next_release_index += 1
    context.network_state.statistics.released_frames += 1
    context.metric_collector.record(
        "frame_release_trace",
        build_frame_release_row(
            timestamp_us=context.clock.current_time_us,
            stream_id=stream_id,
            frame_id=frame_id,
            route_id=frame_state.route_id,
            release_index=release_index,
            traffic_class=stream.traffic_class,
            frame_size_bytes=stream.max_frame_size_bytes,
        ),
    )
    context.trace_collector.record(
        timestamp_us=context.clock.current_time_us,
        event_type="frame_release",
        description=f"Released frame '{frame_id}' for stream '{stream_id}'.",
        attributes={"stream_id": stream_id, "frame_id": frame_id},
    )
    context.event_queue.push(
        context.clock.current_time_us,
        SimulationEventType.ENQUEUE_FRAME.value,
        {"frame_id": frame_id, "port_id": route_link_ids[0]},
    )
    context.network_state.statistics.scheduled_events += 1

    next_release_time_us = (release_index + 1) * stream.period_us
    if can_schedule_release(stream_id, next_release_time_us=next_release_time_us, context=context):
        context.event_queue.push(
            next_release_time_us,
            SimulationEventType.RELEASE_FRAME.value,
            {"stream_id": stream_id},
        )
        context.network_state.statistics.scheduled_events += 1
