"""Checks for baseline assignment assumptions."""

from __future__ import annotations

from collections import Counter, defaultdict, deque

from drts_tsn.domain.case import Case
from drts_tsn.domain.routes import active_route_link_ids

from .errors import ValidationIssue


def _build_active_route_graph(case: Case) -> tuple[list[ValidationIssue], dict[str, set[str]], Counter[str], Counter[str], Counter[str]]:
    """Build graph counters from links actively traversed by normalized routes."""

    issues: list[ValidationIssue] = []
    adjacency: dict[str, set[str]] = defaultdict(set)
    degrees: Counter[str] = Counter()
    incoming: Counter[str] = Counter()
    outgoing: Counter[str] = Counter()

    link_by_id = {link.id: link for link in case.topology.links}
    used_link_ids = sorted(active_route_link_ids(case.routes))
    if not used_link_ids:
        issues.append(
            ValidationIssue(
                code="assumptions.active-routes.empty",
                message="Baseline assumptions require at least one directed link used by active routes.",
                severity="error",
            )
        )
        return issues, adjacency, degrees, incoming, outgoing

    unknown_link_ids = [link_id for link_id in used_link_ids if link_id not in link_by_id]
    if unknown_link_ids:
        issues.append(
            ValidationIssue(
                code="assumptions.active-routes.unknown-link",
                message=(
                    "Active routes reference link identifiers that are absent in topology: "
                    + ",".join(unknown_link_ids)
                ),
                severity="error",
            )
        )

    for link_id in used_link_ids:
        link = link_by_id.get(link_id)
        if link is None:
            continue
        adjacency[link.source_node_id].add(link.target_node_id)
        adjacency[link.target_node_id].add(link.source_node_id)
        degrees[link.source_node_id] += 1
        degrees[link.target_node_id] += 1
        outgoing[link.source_node_id] += 1
        incoming[link.target_node_id] += 1

    return issues, adjacency, degrees, incoming, outgoing


def _connected_nodes(adjacency: dict[str, set[str]]) -> set[str]:
    """Return node ids reachable from one active node in the undirected view."""

    if not adjacency:
        return set()
    visited: set[str] = set()
    queue: deque[str] = deque([next(iter(adjacency))])
    while queue:
        node_id = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)
        for neighbor in adjacency[node_id]:
            if neighbor not in visited:
                queue.append(neighbor)
    return visited


def _validate_line_topology_on_active_routes(
    *,
    adjacency: dict[str, set[str]],
    degrees: Counter[str],
    issues: list[ValidationIssue],
) -> None:
    """Validate that active directed links form one simple line segment."""

    branching_nodes = [node_id for node_id, degree in degrees.items() if degree > 2]
    if branching_nodes:
        issues.append(
            ValidationIssue(
                code="assumptions.line-topology.branching",
                message=(
                    "Active routes do not form a simple line: at least one active node has degree > 2 "
                    "in the active-link graph."
                ),
                severity="error",
                location=",".join(sorted(branching_nodes)),
            )
        )

    active_node_ids = set(adjacency)
    disconnected_nodes = sorted(active_node_ids - _connected_nodes(adjacency))
    if disconnected_nodes:
        issues.append(
            ValidationIssue(
                code="assumptions.line-topology.disconnected",
                message="Active routes must share one connected line segment in baseline mode.",
                severity="error",
                location=",".join(disconnected_nodes),
            )
        )

    active_link_count = int(sum(len(neighbors) for neighbors in adjacency.values()) / 2)
    if active_link_count and active_link_count != len(active_node_ids) - 1:
        issues.append(
            ValidationIssue(
                code="assumptions.line-topology.cardinality",
                message=(
                    "Active routes must satisfy active_link_count = active_node_count - 1 "
                    "to form one simple line."
                ),
                severity="error",
            )
        )


def _validate_single_direction_on_active_routes(
    *,
    adjacency: dict[str, set[str]],
    incoming: Counter[str],
    outgoing: Counter[str],
    issues: list[ValidationIssue],
) -> None:
    """Validate one-direction traffic on the active directed line."""

    active_node_ids = set(adjacency)
    invalid_direction_nodes = sorted(
        node_id for node_id in active_node_ids if incoming[node_id] > 1 or outgoing[node_id] > 1
    )
    if invalid_direction_nodes:
        issues.append(
            ValidationIssue(
                code="assumptions.single-direction.directionality",
                message=(
                    "Active routes violate one-direction traffic: at least one active node has "
                    "multiple incoming or outgoing active links."
                ),
                severity="error",
                location=",".join(invalid_direction_nodes),
            )
        )

    source_nodes = sorted(node_id for node_id in active_node_ids if outgoing[node_id] == 1 and incoming[node_id] == 0)
    sink_nodes = sorted(node_id for node_id in active_node_ids if incoming[node_id] == 1 and outgoing[node_id] == 0)
    if len(source_nodes) != 1 or len(sink_nodes) != 1:
        issues.append(
            ValidationIssue(
                code="assumptions.single-direction.endpoints",
                message=(
                    "Active routes violate one-direction traffic: expected exactly one active source "
                    "endpoint and one active sink endpoint."
                ),
                severity="error",
            )
        )


def validate_assumptions(case: Case) -> list[ValidationIssue]:
    """Validate baseline runnability assumptions on active directed routes."""

    requires_line_topology = "line-topology" in case.assumptions
    requires_single_direction = "single-direction" in case.assumptions
    if not requires_line_topology and not requires_single_direction:
        return []

    graph_issues, adjacency, degrees, incoming, outgoing = _build_active_route_graph(case)
    issues: list[ValidationIssue] = list(graph_issues)
    if not adjacency:
        return issues
    if requires_line_topology:
        _validate_line_topology_on_active_routes(adjacency=adjacency, degrees=degrees, issues=issues)
    if requires_single_direction:
        _validate_single_direction_on_active_routes(
            adjacency=adjacency,
            incoming=incoming,
            outgoing=outgoing,
            issues=issues,
        )
    return issues
