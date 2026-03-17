"""Canonicalize identifiers used across the internal domain model."""

from __future__ import annotations

from dataclasses import replace

from drts_tsn.common.ids import slugify_identifier
from drts_tsn.domain.case import Case
from drts_tsn.domain.routes import Route, RouteHop
from drts_tsn.domain.streams import Stream
from drts_tsn.domain.topology import Link, Node, Port, Topology


def canonicalize_case_identifiers(case: Case) -> Case:
    """Return a case with stable lowercase identifiers."""

    node_map = {node.id: slugify_identifier(node.id) for node in case.topology.nodes}
    stream_map = {stream.id: slugify_identifier(stream.id) for stream in case.streams}
    link_map = {link.id: slugify_identifier(link.id) for link in case.topology.links}

    topology = Topology(
        nodes=[
            replace(node, id=node_map[node.id])
            for node in case.topology.nodes
        ],
        links=[
            replace(
                link,
                id=link_map[link.id],
                source_node_id=node_map.get(link.source_node_id, slugify_identifier(link.source_node_id)),
                target_node_id=node_map.get(link.target_node_id, slugify_identifier(link.target_node_id)),
            )
            for link in case.topology.links
        ],
        ports=[
            replace(
                port,
                id=slugify_identifier(port.id),
                node_id=node_map.get(port.node_id, slugify_identifier(port.node_id)),
            )
            for port in case.topology.ports
        ],
    )
    streams = [
        replace(
            stream,
            id=stream_map[stream.id],
            source_node_id=node_map.get(stream.source_node_id, slugify_identifier(stream.source_node_id)),
            destination_node_id=node_map.get(
                stream.destination_node_id,
                slugify_identifier(stream.destination_node_id),
            ),
            route_id=slugify_identifier(stream.route_id) if stream.route_id else None,
        )
        for stream in case.streams
    ]
    routes = [
        Route(
            route_id=slugify_identifier(route.route_id) if route.route_id else None,
            stream_id=stream_map.get(route.stream_id, slugify_identifier(route.stream_id)),
            hops=[
                RouteHop(
                    node_id=node_map.get(hop.node_id, slugify_identifier(hop.node_id)),
                    link_id=slugify_identifier(hop.link_id) if hop.link_id else None,
                    transmission_time_us=hop.transmission_time_us,
                    egress_port_id=slugify_identifier(hop.egress_port_id) if hop.egress_port_id else None,
                )
                for hop in route.hops
            ],
        )
        for route in case.routes
    ]
    expected_results = [
        replace(
            expected,
            stream_id=stream_map.get(expected.stream_id, slugify_identifier(expected.stream_id)),
        )
        for expected in case.expected_results
    ]
    metadata = replace(case.metadata, case_id=slugify_identifier(case.metadata.case_id))
    return replace(
        case,
        metadata=metadata,
        topology=topology,
        streams=streams,
        routes=routes,
        expected_results=expected_results,
    )
