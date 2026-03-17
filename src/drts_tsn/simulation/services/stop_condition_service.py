"""Stop-condition helpers for the baseline simulator."""

from __future__ import annotations

from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.event_types import SimulationEventType


def can_schedule_release(
    stream_id: str,
    *,
    next_release_time_us: float,
    context: SimulationContext,
) -> bool:
    """Return whether another release should be scheduled for a stream."""

    stream_state = context.network_state.streams[stream_id]
    if context.config.max_releases_per_stream is not None:
        if stream_state.released_frames >= context.config.max_releases_per_stream:
            return False
    if next_release_time_us >= context.release_horizon_us - 1e-9:
        return False
    if context.config.time_limit_us is not None and next_release_time_us > context.config.time_limit_us:
        return False
    return True


def target_deliveries_reached(context: SimulationContext) -> bool:
    """Return whether the configured delivery target has been observed."""

    if context.config.max_deliveries_total is not None:
        return context.network_state.statistics.delivered_frames >= context.config.max_deliveries_total
    if not context.config.stop_when_all_streams_observed:
        return False
    if context.config.max_releases_per_stream is None:
        return False
    return all(
        stream_state.completed_frames >= context.config.max_releases_per_stream
        for stream_state in context.network_state.streams.values()
    )


def request_finalize(context: SimulationContext, *, reason: str) -> None:
    """Request run finalization when it has not already been scheduled."""

    statistics = context.network_state.statistics
    if statistics.finalized or statistics.stop_reason == reason:
        return
    statistics.stop_reason = reason
    context.event_queue.push(
        context.clock.current_time_us,
        SimulationEventType.FINALIZE_RUN.value,
        {"reason": reason},
    )
    statistics.scheduled_events += 1


def should_stop(context: SimulationContext) -> bool:
    """Return whether the engine should stop processing events."""

    statistics = context.network_state.statistics
    if statistics.finalized:
        return True
    if statistics.processed_events >= context.config.max_events:
        statistics.stop_reason = "max_events_reached"
        return True
    if context.config.time_limit_us is not None and context.clock.current_time_us >= context.config.time_limit_us:
        statistics.stop_reason = "time_limit_reached"
        return True
    return False
