"""Parser for the external topology payload."""

from __future__ import annotations

from typing import Any


def parse_topology_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized raw topology dictionary from the external payload."""

    if not isinstance(payload, dict):
        raise ValueError("Topology file must contain a JSON object.")
    topology_payload = payload.get("topology", payload)
    if not isinstance(topology_payload, dict):
        raise ValueError("Topology payload must resolve to an object.")
    if "nodes" in topology_payload:
        nodes = topology_payload.get("nodes", [])
    else:
        nodes = [
            {"id": node["id"], "type": "switch", "name": node.get("name")}
            for node in topology_payload.get("switches", [])
        ] + [
            {"id": node["id"], "type": "end_system", "name": node.get("name")}
            for node in topology_payload.get("end_systems", [])
        ]
    if "links" in topology_payload:
        links = [
            {
                "id": link["id"],
                "source": link.get("source"),
                "target": link.get("target", link.get("destination")),
                "speed_mbps": link.get("speed_mbps", link.get("bandwidth_mbps")),
            }
            for link in topology_payload.get("links", [])
        ]
    else:
        links = []
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
