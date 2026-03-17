"""Parser for the external topology payload."""

from __future__ import annotations

from typing import Any


def parse_topology_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized raw topology dictionary from the external payload."""

    if not isinstance(payload, dict):
        raise ValueError("Topology file must contain a JSON object.")
    nodes = payload.get("nodes", [])
    links = payload.get("links", [])
    if not isinstance(nodes, list):
        raise ValueError("Topology field 'nodes' must be a list.")
    if not isinstance(links, list):
        raise ValueError("Topology field 'links' must be a list.")
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"Topology node at index {index} must be an object.")
        if "id" not in node:
            raise ValueError(f"Topology node at index {index} is missing required field 'id'.")
    for index, link in enumerate(links):
        if not isinstance(link, dict):
            raise ValueError(f"Topology link at index {index} must be an object.")
        for field in ("id", "source", "target"):
            if field not in link:
                raise ValueError(
                    f"Topology link at index {index} is missing required field '{field}'."
                )
    return {"nodes": list(nodes), "links": list(links)}
