"""Canonical topology entities for normalized TSN cases."""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import NodeType


@dataclass(slots=True, frozen=True)
class Node:
    """A node in the network topology."""

    id: str
    type: NodeType
    name: str | None = None


@dataclass(slots=True, frozen=True)
class Port:
    """A directional port attached to a node."""

    id: str
    node_id: str
    egress: bool = True


@dataclass(slots=True, frozen=True)
class Link:
    """A directional link in the simplified baseline topology."""

    id: str
    source_node_id: str
    target_node_id: str
    speed_mbps: float | None = None


@dataclass(slots=True)
class Topology:
    """Canonical topology container."""

    nodes: list[Node] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    ports: list[Port] = field(default_factory=list)


def ordered_line_links(topology: Topology) -> list[Link]:
    """Return links ordered along the directed line topology."""

    if not topology.links:
        return []
    incoming = {link.target_node_id for link in topology.links}
    outgoing_by_source = {link.source_node_id: link for link in topology.links}
    start_candidates = [node.id for node in topology.nodes if node.id not in incoming]
    if len(start_candidates) != 1:
        raise ValueError("Expected exactly one source node for a single-direction line topology.")
    ordered: list[Link] = []
    current_node_id = start_candidates[0]
    while current_node_id in outgoing_by_source:
        link = outgoing_by_source[current_node_id]
        ordered.append(link)
        current_node_id = link.target_node_id
    if len(ordered) != len(topology.links):
        raise ValueError("Topology links do not form a simple directed line.")
    return ordered
