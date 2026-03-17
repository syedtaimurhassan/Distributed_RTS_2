"""Parser for external route payloads."""

from __future__ import annotations

from typing import Any


def parse_routes_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract route rows from the external payload."""

    rows = list(payload) if isinstance(payload, list) else list(payload.get("routes", []))
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Route at index {index} must be an object.")
        if "stream_id" not in row:
            raise ValueError(f"Route at index {index} is missing required field 'stream_id'.")
        hops = row.get("hops", [])
        if not isinstance(hops, list) or not hops:
            raise ValueError(f"Route at index {index} must contain a non-empty 'hops' list.")
        for hop_index, hop in enumerate(hops):
            if not isinstance(hop, dict):
                raise ValueError(f"Route hop {hop_index} at route index {index} must be an object.")
            if "node_id" not in hop:
                raise ValueError(
                    f"Route hop {hop_index} at route index {index} is missing 'node_id'."
                )
    return rows
