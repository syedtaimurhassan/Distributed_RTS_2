"""Map raw external case bundles into canonical domain models."""

from __future__ import annotations

from drts_tsn.common.constants import CLASS_PRIORITY_ORDER
from drts_tsn.domain.case import Case, CaseMetadata
from drts_tsn.domain.enums import NodeType, TrafficClass
from drts_tsn.domain.results import ExpectedResult
from drts_tsn.domain.routes import Route, RouteHop
from drts_tsn.domain.streams import Stream
from drts_tsn.domain.topology import Link, Node, Topology

from .loader import ExternalCaseBundle


def map_external_case(bundle: ExternalCaseBundle) -> Case:
    """Map a raw external bundle into the canonical internal case model."""

    known_manifest_fields = {
        "case_id",
        "name",
        "description",
        "topology",
        "routes",
        "streams",
        "expected_wcrts",
        "assumptions",
    }
    metadata = CaseMetadata(
        case_id=str(bundle.manifest.get("case_id") or bundle.case_directory.name),
        name=str(bundle.manifest.get("name") or bundle.case_directory.name),
        description=str(bundle.manifest.get("description") or ""),
        source_directory=bundle.case_directory,
        tags=list(bundle.manifest.get("assumptions", [])),
    )
    topology = Topology(
        nodes=[
            Node(
                id=str(node["id"]),
                type=NodeType.from_external(str(node.get("type", "switch"))),
                name=node.get("name"),
            )
            for node in bundle.topology.get("nodes", [])
        ],
        links=[
            Link(
                id=str(link["id"]),
                source_node_id=str(link["source"]),
                target_node_id=str(link["target"]),
                speed_mbps=float(
                    link.get("speed_mbps", link.get("bandwidth_mbps"))
                )
                if (link.get("speed_mbps") is not None or link.get("bandwidth_mbps") is not None)
                else None,
            )
            for link in bundle.topology.get("links", [])
        ],
    )
    streams = [
        Stream(
            id=str(stream["id"]),
            name=str(stream.get("name") or stream["id"]),
            source_node_id=str(stream["source"]),
            destination_node_id=str(stream["destination"]),
            traffic_class=TrafficClass.from_external(
                str(
                    stream.get("traffic_class")
                    or stream.get("class")
                    or stream.get("priority_class")
                )
            ),
            period_us=float(stream.get("period_us", stream.get("period"))),
            deadline_us=float(
                stream.get(
                    "deadline_us",
                    stream.get("deadline", stream.get("period_us", stream.get("period"))),
                )
            ),
            max_frame_size_bytes=int(
                stream.get(
                    "max_frame_size_bytes",
                    stream.get("size_bytes", stream.get("frame_size_bytes")),
                )
            ),
            route_id=str(stream.get("route_id")) if stream.get("route_id") is not None else None,
            priority=(
                int(stream["priority"])
                if stream.get("priority") is not None
                else CLASS_PRIORITY_ORDER[
                    TrafficClass.from_external(
                        str(
                            stream.get("traffic_class")
                            or stream.get("class")
                            or stream.get("priority_class")
                        )
                    ).value
                ]
            ),
        )
        for stream in bundle.streams
    ]
    routes = [
        Route(
            route_id=str(route.get("id") or route.get("route_id") or route["stream_id"]),
            stream_id=str(route["stream_id"]),
            hops=[
                RouteHop(
                    node_id=str(hop["node_id"]),
                    egress_port_id=hop.get("egress_port_id"),
                )
                for hop in route.get("hops", [])
            ],
        )
        for route in bundle.routes
    ]
    expected_results = [
        ExpectedResult(
            stream_id=str(row["stream_id"]),
            expected_wcrt_us=float(row["expected_wcrt_us"]),
        )
        for row in bundle.expected_wcrts
    ]
    return Case(
        metadata=metadata,
        topology=topology,
        streams=streams,
        routes=routes,
        expected_results=expected_results,
        assumptions=list(bundle.manifest.get("assumptions", [])),
        parameters={
            key: value
            for key, value in bundle.manifest.items()
            if key not in known_manifest_fields
        },
    )
