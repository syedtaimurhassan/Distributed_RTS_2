"""Route and path derivation helpers."""

from __future__ import annotations

from dataclasses import replace

from drts_tsn.common.math_utils import serialization_delay_us
from drts_tsn.domain.case import Case
from drts_tsn.domain.routes import Route


def derive_paths(case: Case) -> Case:
    """Resolve route hop pairs into directional link identifiers."""

    link_lookup = {
        (link.source_node_id, link.target_node_id): link
        for link in case.topology.links
    }
    streams_by_id = {stream.id: stream for stream in case.streams}
    routes: list[Route] = []
    for route in case.routes:
        stream = streams_by_id.get(route.stream_id)
        if stream is None:
            routes.append(route)
            continue
        if len(route.hops) < 2:
            routes.append(route)
            continue
        resolved_hops = []
        for index, hop in enumerate(route.hops):
            if index == len(route.hops) - 1:
                resolved_hops.append(hop)
                continue
            next_hop = route.hops[index + 1]
            link = link_lookup.get((hop.node_id, next_hop.node_id))
            if link is None:
                resolved_hops.append(
                    replace(
                        hop,
                        link_id=None,
                        transmission_time_us=None,
                    )
                )
                continue
            resolved_hops.append(
                replace(
                    hop,
                    link_id=link.id,
                    transmission_time_us=serialization_delay_us(
                        stream.max_frame_size_bytes,
                        float(link.speed_mbps or 100.0),
                    ),
                )
            )
        routes.append(Route(route_id=route.route_id, stream_id=route.stream_id, hops=resolved_hops))
    return replace(case, routes=routes)
