"""Topology-level validation checks."""

from __future__ import annotations

from drts_tsn.domain.case import Case

from .errors import ValidationIssue


def validate_topology(case: Case) -> list[ValidationIssue]:
    """Validate basic topology integrity."""

    issues: list[ValidationIssue] = []
    if not case.topology.nodes:
        issues.append(ValidationIssue(code="topology.nodes.empty", message="Topology has no nodes."))
    if not case.topology.links:
        issues.append(ValidationIssue(code="topology.links.empty", message="Topology has no links."))
    node_ids_in_order = [node.id for node in case.topology.nodes]
    if len(node_ids_in_order) != len(set(node_ids_in_order)):
        issues.append(
            ValidationIssue(
                code="topology.nodes.duplicate-id",
                message="Topology contains duplicate node identifiers.",
            )
        )
    node_ids = {node.id for node in case.topology.nodes}
    link_ids_in_order = [link.id for link in case.topology.links]
    if len(link_ids_in_order) != len(set(link_ids_in_order)):
        issues.append(
            ValidationIssue(
                code="topology.links.duplicate-id",
                message="Topology contains duplicate link identifiers.",
            )
        )
    for link in case.topology.links:
        if link.source_node_id not in node_ids or link.target_node_id not in node_ids:
            issues.append(
                ValidationIssue(
                    code="topology.link.unknown-node",
                    message=f"Link '{link.id}' references unknown nodes.",
                    location=link.id,
                )
            )
        if link.source_node_id == link.target_node_id:
            issues.append(
                ValidationIssue(
                    code="topology.link.self-loop",
                    message=f"Link '{link.id}' must not be a self-loop in baseline mode.",
                    location=link.id,
                )
            )
    return issues
