"""Export canonical normalized cases to disk."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.common.dataclass_tools import to_plain_data
from drts_tsn.domain.case import Case
from drts_tsn.io.csv_io import write_csv_rows
from drts_tsn.io.json_io import write_json


def export_normalized_case(case: Case, destination: Path) -> Path:
    """Write a normalized case JSON artifact."""

    return write_json(to_plain_data(case), destination)


def export_normalized_case_bundle(case: Case, destination_directory: Path) -> dict[str, Path]:
    """Write the normalized JSON artifact plus the core CSV exports."""

    destination_directory.mkdir(parents=True, exist_ok=True)
    routes_by_id = {
        (route.route_id or route.stream_id): route
        for route in case.routes
    }

    artifacts = {
        "normalized_case.json": export_normalized_case(
            case,
            destination_directory / "normalized_case.json",
        ),
        "nodes.csv": write_csv_rows(
            [
                {
                    "node_id": node.id,
                    "node_type": node.type.value,
                    "name": node.name or "",
                }
                for node in case.topology.nodes
            ],
            destination_directory / "nodes.csv",
        ),
        "links.csv": write_csv_rows(
            [
                {
                    "link_id": link.id,
                    "source_node_id": link.source_node_id,
                    "target_node_id": link.target_node_id,
                    "speed_mbps": link.speed_mbps,
                }
                for link in case.topology.links
            ],
            destination_directory / "links.csv",
        ),
        "routes.csv": write_csv_rows(
            [
                {
                    "route_id": route.route_id or route.stream_id,
                    "stream_id": route.stream_id,
                    "hop_index": hop_index,
                    "node_id": hop.node_id,
                    "link_id": hop.link_id or "",
                    "transmission_time_us": hop.transmission_time_us,
                }
                for route in case.routes
                for hop_index, hop in enumerate(route.hops)
            ],
            destination_directory / "routes.csv",
        ),
        "streams.csv": write_csv_rows(
            [
                {
                    "stream_id": stream.id,
                    "name": stream.name,
                    "source_node_id": stream.source_node_id,
                    "destination_node_id": stream.destination_node_id,
                    "traffic_class": stream.traffic_class.value,
                    "priority": stream.priority,
                    "period_us": stream.period_us,
                    "deadline_us": stream.deadline_us,
                    "max_frame_size_bytes": stream.max_frame_size_bytes,
                    "route_id": stream.route_id or "",
                }
                for stream in case.streams
            ],
            destination_directory / "streams.csv",
        ),
        "link_stream_map.csv": write_csv_rows(
            [
                {
                    "stream_id": stream.id,
                    "route_id": stream.route_id or "",
                    "link_id": hop.link_id or "",
                    "hop_index": hop_index,
                    "transmission_time_us": hop.transmission_time_us,
                }
                for stream in case.streams
                for route in [routes_by_id.get(stream.route_id or stream.id)]
                for hop_index, hop in enumerate(route.hops[:-1] if route is not None else [])
            ],
            destination_directory / "link_stream_map.csv",
        ),
    }
    return artifacts
