"""Checks for baseline assignment assumptions."""

from __future__ import annotations

from collections import Counter

from drts_tsn.domain.case import Case

from .errors import ValidationIssue


def validate_assumptions(case: Case) -> list[ValidationIssue]:
    """Validate simplified baseline assumptions such as line topology."""

    issues: list[ValidationIssue] = []
    if "line-topology" in case.assumptions:
        degrees: Counter[str] = Counter()
        incoming: Counter[str] = Counter()
        outgoing: Counter[str] = Counter()
        for link in case.topology.links:
            degrees[link.source_node_id] += 1
            degrees[link.target_node_id] += 1
            outgoing[link.source_node_id] += 1
            incoming[link.target_node_id] += 1
        branching_nodes = [node_id for node_id, degree in degrees.items() if degree > 2]
        if branching_nodes:
            issues.append(
                ValidationIssue(
                    code="assumptions.line-topology.branching",
                    message="Topology is not a simple line under current assumptions.",
                    severity="error",
                    location=",".join(sorted(branching_nodes)),
                )
            )
        if case.topology.links and len(case.topology.links) != len(case.topology.nodes) - 1:
            issues.append(
                ValidationIssue(
                    code="assumptions.line-topology.cardinality",
                    message="A simplified line topology must contain exactly N-1 directed links.",
                    severity="error",
                )
            )
        invalid_direction_nodes = sorted(
            {
                node.id
                for node in case.topology.nodes
                if incoming[node.id] > 1 or outgoing[node.id] > 1
            }
        )
        if invalid_direction_nodes:
            issues.append(
                ValidationIssue(
                    code="assumptions.line-topology.directionality",
                    message="A simplified directed line topology cannot branch or merge.",
                    severity="error",
                    location=",".join(invalid_direction_nodes),
                )
            )
    if "single-direction" in case.assumptions:
        route_starts = {route.hops[0].node_id for route in case.routes if route.hops}
        if len(route_starts) > 1:
            issues.append(
                ValidationIssue(
                    code="assumptions.single-direction.multiple-sources",
                    message="All routes must follow the same direction of traffic in the baseline model.",
                    severity="error",
                )
            )
    return issues
