"""Case overview helpers."""

from __future__ import annotations

from collections import Counter

from drts_tsn.domain.case import Case
from drts_tsn.domain.enums import TrafficClass


def build_case_overview(case: Case) -> dict[str, object]:
    """Return a flat case overview dictionary."""

    return {
        "case_id": case.metadata.case_id,
        "name": case.metadata.name,
        "stream_count": len(case.streams),
        "route_count": len(case.routes),
        "node_count": len(case.topology.nodes),
        "link_count": len(case.topology.links),
    }


def build_case_inspection(case: Case) -> dict[str, object]:
    """Return structured data for a human-readable case inspection view."""

    class_counts = Counter(stream.traffic_class.display_name for stream in case.streams)
    return {
        "overview": {
            **build_case_overview(case),
            "assumptions": ",".join(case.assumptions) or "-",
        },
        "class_counts": [
            {
                "traffic_class": traffic_class.display_name,
                "count": class_counts.get(traffic_class.display_name, 0),
            }
            for traffic_class in (
                TrafficClass.CLASS_A,
                TrafficClass.CLASS_B,
                TrafficClass.BEST_EFFORT,
            )
        ],
        "nodes": [
            {"node_id": node.id, "node_type": node.type.value, "name": node.name or ""}
            for node in case.topology.nodes
        ],
        "links": [
            {
                "link_id": link.id,
                "source": link.source_node_id,
                "target": link.target_node_id,
                "speed_mbps": link.speed_mbps,
            }
            for link in case.topology.links
        ],
        "routes": [
            {
                "route_id": route.route_id or route.stream_id,
                "stream_id": route.stream_id,
                "path": " -> ".join(hop.node_id for hop in route.hops),
                "link_count": max(len(route.hops) - 1, 0),
            }
            for route in case.routes
        ],
        "streams": [
            {
                "stream_id": stream.id,
                "traffic_class": stream.traffic_class.display_name,
                "priority": stream.priority,
                "period_us": stream.period_us,
                "deadline_us": stream.deadline_us,
                "frame_size_bytes": stream.max_frame_size_bytes,
                "route_id": stream.route_id or "",
            }
            for stream in case.streams
        ],
    }
