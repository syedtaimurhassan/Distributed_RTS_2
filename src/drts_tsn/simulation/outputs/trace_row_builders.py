"""Stable row builders for simulation trace and summary tables."""

from __future__ import annotations

from drts_tsn.domain.enums import ResultStatus, TrafficClass


def build_frame_release_row(
    *,
    timestamp_us: float,
    stream_id: str,
    frame_id: str,
    route_id: str,
    release_index: int,
    traffic_class: TrafficClass,
    frame_size_bytes: int,
) -> dict[str, object]:
    """Return one frame-release trace row."""

    return {
        "timestamp_us": timestamp_us,
        "stream_id": stream_id,
        "frame_id": frame_id,
        "route_id": route_id,
        "release_index": release_index,
        "traffic_class": traffic_class.value,
        "frame_size_bytes": frame_size_bytes,
    }


def build_enqueue_row(
    *,
    timestamp_us: float,
    stream_id: str,
    frame_id: str,
    port_id: str,
    link_id: str,
    queue_id: str,
    traffic_class: TrafficClass,
    hop_index: int,
    queue_depth: int,
) -> dict[str, object]:
    """Return one enqueue trace row."""

    return {
        "timestamp_us": timestamp_us,
        "stream_id": stream_id,
        "frame_id": frame_id,
        "port_id": port_id,
        "link_id": link_id,
        "queue_id": queue_id,
        "traffic_class": traffic_class.value,
        "hop_index": hop_index,
        "queue_depth": queue_depth,
    }


def build_transmission_row(
    *,
    stream_id: str,
    frame_id: str,
    port_id: str,
    link_id: str,
    queue_id: str,
    hop_index: int,
    traffic_class: TrafficClass,
    release_time_us: float,
    enqueue_time_us: float,
    start_time_us: float,
    end_time_us: float,
    queueing_delay_us: float,
    transmission_time_us: float,
    response_time_so_far_us: float,
    credit_before: float | None,
    credit_after: float | None,
    service_spacing_us: float,
) -> dict[str, object]:
    """Return one transmission trace row."""

    return {
        "stream_id": stream_id,
        "frame_id": frame_id,
        "port_id": port_id,
        "link_id": link_id,
        "queue_id": queue_id,
        "hop_index": hop_index,
        "traffic_class": traffic_class.value,
        "release_time_us": release_time_us,
        "enqueue_time_us": enqueue_time_us,
        "start_time_us": start_time_us,
        "end_time_us": end_time_us,
        "queueing_delay_us": queueing_delay_us,
        "transmission_time_us": transmission_time_us,
        "response_time_so_far_us": response_time_so_far_us,
        "credit_before": credit_before,
        "credit_after": credit_after,
        "service_spacing_us": service_spacing_us,
    }


def build_forwarding_row(
    *,
    timestamp_us: float,
    stream_id: str,
    frame_id: str,
    from_link_id: str,
    to_link_id: str,
    from_hop_index: int,
    to_hop_index: int,
) -> dict[str, object]:
    """Return one forwarding trace row."""

    return {
        "timestamp_us": timestamp_us,
        "stream_id": stream_id,
        "frame_id": frame_id,
        "from_link_id": from_link_id,
        "to_link_id": to_link_id,
        "from_hop_index": from_hop_index,
        "to_hop_index": to_hop_index,
    }


def build_delivery_row(
    *,
    timestamp_us: float,
    stream_id: str,
    frame_id: str,
    route_id: str,
    release_index: int,
    hop_count: int,
    release_time_us: float,
    delivery_time_us: float,
) -> dict[str, object]:
    """Return one delivery trace row."""

    return {
        "timestamp_us": timestamp_us,
        "stream_id": stream_id,
        "frame_id": frame_id,
        "route_id": route_id,
        "release_index": release_index,
        "hop_count": hop_count,
        "release_time_us": release_time_us,
        "delivery_time_us": delivery_time_us,
    }


def build_response_time_row(
    *,
    stream_id: str,
    frame_id: str,
    release_index: int,
    release_time_us: float,
    delivery_time_us: float,
    response_time_us: float,
    deadline_us: float,
) -> dict[str, object]:
    """Return one response-time trace row."""

    return {
        "stream_id": stream_id,
        "frame_id": frame_id,
        "release_index": release_index,
        "release_time_us": release_time_us,
        "delivery_time_us": delivery_time_us,
        "response_time_us": response_time_us,
        "deadline_us": deadline_us,
        "meets_deadline": response_time_us <= deadline_us,
    }


def build_stream_summary_row(
    *,
    stream_id: str,
    traffic_class: TrafficClass,
    release_count: int,
    delivery_count: int,
    max_response_time_us: float | None,
    mean_response_time_us: float | None,
    status: ResultStatus,
) -> dict[str, object]:
    """Return one per-stream summary row."""

    return {
        "stream_id": stream_id,
        "traffic_class": traffic_class.value,
        "release_count": release_count,
        "delivery_count": delivery_count,
        "max_response_time_us": max_response_time_us,
        "mean_response_time_us": mean_response_time_us,
        "status": status.value,
    }


def build_hop_summary_row(
    *,
    stream_id: str,
    link_id: str,
    hop_index: int,
    transmission_count: int,
    max_queueing_delay_us: float,
    max_response_time_so_far_us: float,
) -> dict[str, object]:
    """Return one per-stream per-hop summary row."""

    return {
        "stream_id": stream_id,
        "link_id": link_id,
        "hop_index": hop_index,
        "transmission_count": transmission_count,
        "max_queueing_delay_us": max_queueing_delay_us,
        "max_response_time_so_far_us": max_response_time_so_far_us,
    }


def build_queue_summary_row(
    *,
    port_id: str,
    link_id: str,
    queue_id: str,
    traffic_class: TrafficClass,
    enqueued_count: int,
    transmitted_count: int,
    max_depth: int,
    final_depth: int,
    current_credit: float | None,
    next_eligible_time_us: float | None,
) -> dict[str, object]:
    """Return one queue summary row."""

    return {
        "port_id": port_id,
        "link_id": link_id,
        "queue_id": queue_id,
        "traffic_class": traffic_class.value,
        "enqueued_count": enqueued_count,
        "transmitted_count": transmitted_count,
        "max_depth": max_depth,
        "final_depth": final_depth,
        "current_credit": current_credit,
        "next_eligible_time_us": next_eligible_time_us,
    }


def build_run_summary_row(
    *,
    case_id: str,
    run_id: str,
    engine_status: str,
    stop_reason: str,
    processed_event_count: int,
    released_frame_count: int,
    delivered_frame_count: int,
    transmission_count: int,
    simulated_time_us: float,
    trace_enabled: bool,
) -> dict[str, object]:
    """Return one run summary row."""

    return {
        "case_id": case_id,
        "run_id": run_id,
        "engine_status": engine_status,
        "stop_reason": stop_reason,
        "processed_event_count": processed_event_count,
        "released_frame_count": released_frame_count,
        "delivered_frame_count": delivered_frame_count,
        "transmission_count": transmission_count,
        "simulated_time_us": simulated_time_us,
        "trace_enabled": trace_enabled,
    }
