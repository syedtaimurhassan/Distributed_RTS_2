"""Delivery and response-time accounting for simulated frames."""

from __future__ import annotations

from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.outputs.trace_row_builders import (
    build_delivery_row,
    build_response_time_row,
)

from .stop_condition_service import request_finalize, target_deliveries_reached


def complete_delivery(frame_id: str, context: SimulationContext) -> None:
    """Mark one frame as delivered and emit end-to-end response-time rows."""

    frame_state = context.network_state.frames[frame_id]
    stream = context.streams_by_id[frame_state.stream_id]
    stream_state = context.network_state.streams[frame_state.stream_id]
    delivery_time_us = context.clock.current_time_us
    response_time_us = delivery_time_us - frame_state.release_time_us

    frame_state.delivery_time_us = delivery_time_us
    stream_state.completed_frames += 1
    context.network_state.statistics.delivered_frames += 1
    context.metric_collector.record(
        "delivery_trace",
        build_delivery_row(
            timestamp_us=delivery_time_us,
            stream_id=frame_state.stream_id,
            frame_id=frame_id,
            route_id=frame_state.route_id,
            release_index=frame_state.release_index,
            hop_count=len(frame_state.route_link_ids),
            release_time_us=frame_state.release_time_us,
            delivery_time_us=delivery_time_us,
        ),
    )
    context.metric_collector.record(
        "response_time_trace",
        build_response_time_row(
            stream_id=frame_state.stream_id,
            frame_id=frame_id,
            release_index=frame_state.release_index,
            release_time_us=frame_state.release_time_us,
            delivery_time_us=delivery_time_us,
            response_time_us=response_time_us,
            deadline_us=stream.deadline_us,
        ),
    )
    context.metric_collector.record_frame_response_time(frame_state.stream_id, response_time_us)
    context.trace_collector.record(
        timestamp_us=delivery_time_us,
        event_type="delivery_complete",
        description=f"Delivered frame '{frame_id}' for stream '{frame_state.stream_id}'.",
        attributes={"response_time_us": response_time_us},
    )
    if target_deliveries_reached(context):
        request_finalize(context, reason="delivery_target_reached")
