"""Parser for external route payloads."""

from __future__ import annotations

from typing import Any


def _canonical_stream_id(raw_value: object) -> str:
    """Return a canonical external stream identifier."""

    if isinstance(raw_value, int):
        return f"stream-{raw_value}"
    raw_text = str(raw_value)
    return raw_text if not raw_text.isdigit() else f"stream-{raw_text}"


def parse_routes_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract route rows from the external payload."""

    rows = list(payload) if isinstance(payload, list) else list(payload.get("routes", []))
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Route at index {index} must be an object.")
        stream_id = row.get("stream_id")
        hops = row.get("hops", [])
        if stream_id is None and row.get("flow_id") is not None:
            stream_id = _canonical_stream_id(row["flow_id"])
            paths = row.get("paths", [])
            if isinstance(paths, list) and paths:
                first_path = paths[0]
                if isinstance(first_path, list):
                    hops = [
                        {
                            "node_id": hop.get("node"),
                            "egress_port_id": hop.get("port"),
                        }
                        for hop in first_path
                    ]
        if stream_id is None:
            raise ValueError(f"Route at index {index} is missing required field 'stream_id'.")
        if not isinstance(hops, list) or not hops:
            raise ValueError(f"Route at index {index} must contain a non-empty 'hops' list.")
        for hop_index, hop in enumerate(hops):
            if not isinstance(hop, dict):
                raise ValueError(f"Route hop {hop_index} at route index {index} must be an object.")
            if "node_id" not in hop:
                raise ValueError(
                    f"Route hop {hop_index} at route index {index} is missing 'node_id'."
                )
        normalized_rows.append(
            {
                **row,
                "stream_id": str(stream_id),
                "id": row.get("id") or row.get("route_id") or f"route-{stream_id}",
                "hops": hops,
            }
        )
    return normalized_rows
