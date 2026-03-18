"""Shared context object and runtime-state initialization for simulation."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.common.constants import DEFAULT_LINK_SPEED_MBPS
from drts_tsn.common.math_utils import integer_hyperperiod
from drts_tsn.domain.case import Case
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.routes import active_route_link_ids, route_link_ids_by_stream
from drts_tsn.domain.streams import Stream
from drts_tsn.domain.topology import Link

from .clock import SimulationClock
from .config import SimulationConfig
from .event_queue import EventQueue
from .model.credit_state import CreditState
from .model.network_state import NetworkState
from .model.port_state import PortState
from .model.queue_state import QueueState
from .model.stream_state import StreamState
from .outputs.metric_collector import MetricCollector
from .outputs.trace_collector import TraceCollector


@dataclass(slots=True)
class SimulationContext:
    """Runtime state and immutable lookups shared by simulation services."""

    case: Case
    config: SimulationConfig
    clock: SimulationClock
    event_queue: EventQueue
    network_state: NetworkState
    trace_collector: TraceCollector
    metric_collector: MetricCollector
    streams_by_id: dict[str, Stream]
    route_links_by_stream_id: dict[str, list[str]]
    link_by_id: dict[str, Link]
    queue_ids_by_port_and_class: dict[tuple[str, TrafficClass], str]
    release_horizon_us: float


def _resolve_release_horizon_us(case: Case, config: SimulationConfig) -> float:
    """Return the release horizon used to schedule periodic frame releases."""

    horizon_us = float(
        integer_hyperperiod(
            [stream.period_us for stream in case.streams],
            limit=config.max_hyperperiod_us,
        )
    )
    if config.time_limit_us is not None:
        horizon_us = min(horizon_us, config.time_limit_us)
    return horizon_us


def build_simulation_context(case: Case, config: SimulationConfig) -> SimulationContext:
    """Construct the mutable runtime state and immutable lookups for one run."""

    streams_by_id = {stream.id: stream for stream in case.streams}
    route_links_by_stream_id = route_link_ids_by_stream(case.routes)
    link_by_id = {link.id: link for link in case.topology.links}
    active_route_link_id_set = active_route_link_ids(case.routes)
    if not active_route_link_id_set:
        raise ValueError("Simulation requires at least one directed link used by active routes.")
    unresolved_active_links = sorted(link_id for link_id in active_route_link_id_set if link_id not in link_by_id)
    if unresolved_active_links:
        raise ValueError(
            "Simulation route resolution references unknown topology links: "
            + ",".join(unresolved_active_links)
        )
    active_links = [link_by_id[link_id] for link_id in sorted(active_route_link_id_set)]
    empty_stream_paths = sorted(stream_id for stream_id, path_link_ids in route_links_by_stream_id.items() if not path_link_ids)
    if empty_stream_paths:
        raise ValueError(
            "Simulation requires resolved directed paths for all routed streams; empty paths for: "
            + ",".join(empty_stream_paths)
        )
    network_state = NetworkState()
    queue_ids_by_port_and_class: dict[tuple[str, TrafficClass], str] = {}
    for link in active_links:
        port_id = link.id
        queues: dict[str, QueueState] = {}
        credits: dict[str, CreditState] = {}
        for queue in sorted(case.queues, key=lambda item: item.priority, reverse=True):
            queue_id = f"{port_id}:{queue.traffic_class.value}"
            queues[queue_id] = QueueState(queue_id=queue_id, traffic_class=queue.traffic_class)
            queue_ids_by_port_and_class[(port_id, queue.traffic_class)] = queue_id
            if queue.uses_cbs:
                credits[queue_id] = CreditState(traffic_class=queue.traffic_class)
        network_state.ports[port_id] = PortState(
            port_id=port_id,
            link_id=link.id,
            source_node_id=link.source_node_id,
            target_node_id=link.target_node_id,
            speed_mbps=float(link.speed_mbps or DEFAULT_LINK_SPEED_MBPS),
            queues=queues,
            credits=credits,
        )
    for stream in case.streams:
        route_id = stream.route_id or stream.id
        network_state.streams[stream.id] = StreamState(
            stream_id=stream.id,
            route_id=route_id,
        )
    return SimulationContext(
        case=case,
        config=config,
        clock=SimulationClock(),
        event_queue=EventQueue(),
        network_state=network_state,
        trace_collector=TraceCollector(enabled=config.trace_enabled),
        metric_collector=MetricCollector(),
        streams_by_id=streams_by_id,
        route_links_by_stream_id=route_links_by_stream_id,
        link_by_id=link_by_id,
        queue_ids_by_port_and_class=queue_ids_by_port_and_class,
        release_horizon_us=_resolve_release_horizon_us(case, config),
    )
