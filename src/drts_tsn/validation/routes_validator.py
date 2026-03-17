"""Route-level validation checks."""

from __future__ import annotations

from drts_tsn.domain.case import Case

from .errors import ValidationIssue


def validate_routes(case: Case) -> list[ValidationIssue]:
    """Validate route presence and hop references."""

    issues: list[ValidationIssue] = []
    stream_ids = {stream.id for stream in case.streams}
    node_ids = {node.id for node in case.topology.nodes}
    route_ids = [route.route_id or route.stream_id for route in case.routes]
    if len(route_ids) != len(set(route_ids)):
        issues.append(
            ValidationIssue(
                code="routes.id.duplicate",
                message="Route identifiers must be unique after normalization.",
            )
        )
    link_lookup = {
        (link.source_node_id, link.target_node_id): link.id
        for link in case.topology.links
    }
    for route in case.routes:
        if route.stream_id not in stream_ids:
            issues.append(
                ValidationIssue(
                    code="routes.stream.missing",
                    message=f"Route references missing stream '{route.stream_id}'.",
                    location=route.stream_id,
                )
            )
        if not route.hops:
            issues.append(
                ValidationIssue(
                    code="routes.hops.empty",
                    message=f"Route for stream '{route.stream_id}' has no hops.",
                    location=route.stream_id,
                )
            )
        for hop in route.hops:
            if hop.node_id not in node_ids:
                issues.append(
                    ValidationIssue(
                        code="routes.hop.unknown-node",
                        message=f"Route for stream '{route.stream_id}' references unknown node '{hop.node_id}'.",
                        location=route.stream_id,
                    )
                )
        for left_hop, right_hop in zip(route.hops, route.hops[1:]):
            if (left_hop.node_id, right_hop.node_id) not in link_lookup:
                issues.append(
                    ValidationIssue(
                        code="routes.link.missing",
                        message=(
                            f"Route for stream '{route.stream_id}' has no topology link between "
                            f"'{left_hop.node_id}' and '{right_hop.node_id}'."
                        ),
                        location=route.stream_id,
                    )
                )
            elif left_hop.link_id and left_hop.link_id != link_lookup[(left_hop.node_id, right_hop.node_id)]:
                issues.append(
                    ValidationIssue(
                        code="routes.link.mismatch",
                        message=(
                            f"Route for stream '{route.stream_id}' resolved an unexpected link "
                            f"for hop '{left_hop.node_id}' -> '{right_hop.node_id}'."
                        ),
                        location=route.stream_id,
                    )
                )
        if len({hop.node_id for hop in route.hops}) != len(route.hops):
            issues.append(
                ValidationIssue(
                    code="routes.cycle.unsupported",
                    message=f"Route for stream '{route.stream_id}' repeats nodes in a simplified line topology.",
                    location=route.stream_id,
                )
            )
    return issues
