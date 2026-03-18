"""Per-link analytical context builders for baseline AVB WCRT analysis."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.common.constants import DEFAULT_LINK_SPEED_MBPS
from drts_tsn.domain.case import Case
from drts_tsn.domain.credits import idle_slope_share, send_slope_share
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.routes import route_link_ids
from drts_tsn.domain.streams import Stream

from .formulas.transmission_time import transmission_time_us


@dataclass(slots=True, frozen=True)
class LinkFlow:
    """One normalized stream instance as seen on a specific directed link."""

    stream_id: str
    traffic_class: TrafficClass
    priority: int
    period_us: float
    deadline_us: float
    frame_size_bytes: int
    transmission_time_us: float
    reserved_share: float
    send_slope_share: float


@dataclass(slots=True, frozen=True)
class LinkTrafficContext:
    """All baseline analytical inputs for one stream on one directed link."""

    stream_id: str
    route_id: str
    link_id: str
    hop_index: int
    traffic_class: TrafficClass
    priority: int
    link_speed_mbps: float
    reserved_share: float
    send_slope_share: float
    reserved_share_up_to_class: float
    period_us: float
    deadline_us: float
    frame_size_bytes: int
    transmission_time_us: float
    same_priority_flows: tuple[LinkFlow, ...]
    higher_priority_flows: tuple[LinkFlow, ...]
    lower_priority_flows: tuple[LinkFlow, ...]


def _queue_parameters_for_class(
    case: Case,
    traffic_class: TrafficClass,
    *,
    link_speed_mbps: float,
) -> tuple[int, float, float]:
    """Return priority plus normalized idle/send shares for one traffic class."""

    for queue in case.queues:
        if queue.traffic_class != traffic_class:
            continue
        if not queue.uses_cbs or queue.credit_parameters is None:
            return queue.priority, 0.0, 0.0
        return (
            queue.priority,
            idle_slope_share(queue.credit_parameters),
            send_slope_share(queue.credit_parameters),
        )
    raise ValueError(f"Missing queue definition for traffic class '{traffic_class.value}'.")


def _build_link_flow(case: Case, stream: Stream, *, link_speed_mbps: float) -> LinkFlow:
    """Build a per-link stream view with derived transmission and reserved shares."""

    priority, reserved_share, send_slope_share = _queue_parameters_for_class(
        case,
        stream.traffic_class,
        link_speed_mbps=link_speed_mbps,
    )
    return LinkFlow(
        stream_id=stream.id,
        traffic_class=stream.traffic_class,
        priority=priority,
        period_us=stream.period_us,
        deadline_us=stream.deadline_us,
        frame_size_bytes=stream.max_frame_size_bytes,
        transmission_time_us=transmission_time_us(stream.max_frame_size_bytes, link_speed_mbps),
        reserved_share=reserved_share,
        send_slope_share=send_slope_share,
    )


def build_link_traffic_contexts(case: Case) -> list[LinkTrafficContext]:
    """Return deterministic per-link analytical contexts for all AVB streams."""

    route_by_id = {(route.route_id or route.stream_id): route for route in case.routes}
    route_links_by_stream = {
        stream.id: route_link_ids(route_by_id[stream.route_id or stream.id])
        for stream in case.streams
        if (stream.route_id or stream.id) in route_by_id
    }
    link_speed_by_id = {
        link.id: float(link.speed_mbps or DEFAULT_LINK_SPEED_MBPS)
        for link in case.topology.links
    }

    contexts: list[LinkTrafficContext] = []
    for stream in case.streams:
        if stream.traffic_class == TrafficClass.BEST_EFFORT:
            continue
        route_id = stream.route_id or stream.id
        link_ids = route_links_by_stream.get(stream.id, [])
        for hop_index, link_id in enumerate(link_ids):
            link_speed_mbps = link_speed_by_id.get(link_id, DEFAULT_LINK_SPEED_MBPS)
            current_flow = _build_link_flow(case, stream, link_speed_mbps=link_speed_mbps)
            streams_on_link = [
                candidate
                for candidate in case.streams
                if link_id in route_links_by_stream.get(candidate.id, [])
            ]
            candidate_flows = [
                _build_link_flow(case, candidate, link_speed_mbps=link_speed_mbps)
                for candidate in streams_on_link
                if candidate.id != stream.id
            ]
            same_priority_flows = tuple(
                flow for flow in candidate_flows if flow.priority == current_flow.priority
            )
            higher_priority_flows = tuple(
                flow for flow in candidate_flows if flow.priority > current_flow.priority
            )
            lower_priority_flows = tuple(
                flow for flow in candidate_flows if flow.priority < current_flow.priority
            )
            representative_flows_by_class = {
                flow.traffic_class: flow
                for flow in (current_flow, *higher_priority_flows)
                if flow.traffic_class != TrafficClass.BEST_EFFORT
            }
            reserved_share_up_to_class = sum(
                flow.reserved_share
                for flow in representative_flows_by_class.values()
            )
            contexts.append(
                LinkTrafficContext(
                    stream_id=stream.id,
                    route_id=route_id,
                    link_id=link_id,
                    hop_index=hop_index,
                    traffic_class=stream.traffic_class,
                    priority=current_flow.priority,
                    link_speed_mbps=link_speed_mbps,
                    reserved_share=current_flow.reserved_share,
                    send_slope_share=current_flow.send_slope_share,
                    reserved_share_up_to_class=reserved_share_up_to_class,
                    period_us=stream.period_us,
                    deadline_us=stream.deadline_us,
                    frame_size_bytes=stream.max_frame_size_bytes,
                    transmission_time_us=current_flow.transmission_time_us,
                    same_priority_flows=tuple(
                        sorted(same_priority_flows, key=lambda flow: flow.stream_id)
                    ),
                    higher_priority_flows=tuple(
                        sorted(higher_priority_flows, key=lambda flow: (-flow.priority, flow.stream_id))
                    ),
                    lower_priority_flows=tuple(
                        sorted(lower_priority_flows, key=lambda flow: (flow.priority, flow.stream_id))
                    ),
                )
            )
    return sorted(contexts, key=lambda context: (context.stream_id, context.hop_index, context.link_id))
