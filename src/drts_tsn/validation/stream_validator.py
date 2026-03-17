"""Stream-level validation checks."""

from __future__ import annotations

from drts_tsn.domain.case import Case

from .errors import ValidationIssue


def validate_streams(case: Case) -> list[ValidationIssue]:
    """Validate stream definitions and baseline field values."""

    issues: list[ValidationIssue] = []
    node_ids = {node.id for node in case.topology.nodes}
    routes_by_id = {
        (route.route_id or route.stream_id): route
        for route in case.routes
    }
    for stream in case.streams:
        if stream.source_node_id not in node_ids:
            issues.append(
                ValidationIssue(
                    code="streams.source.unknown-node",
                    message=f"Stream '{stream.id}' references unknown source node '{stream.source_node_id}'.",
                    location=stream.id,
                )
            )
        if stream.destination_node_id not in node_ids:
            issues.append(
                ValidationIssue(
                    code="streams.destination.unknown-node",
                    message=(
                        f"Stream '{stream.id}' references unknown destination node "
                        f"'{stream.destination_node_id}'."
                    ),
                    location=stream.id,
                )
            )
        if stream.period_us <= 0:
            issues.append(
                ValidationIssue(
                    code="streams.period.invalid",
                    message=f"Stream '{stream.id}' has a non-positive period.",
                    location=stream.id,
                )
            )
        if stream.deadline_us <= 0:
            issues.append(
                ValidationIssue(
                    code="streams.deadline.invalid",
                    message=f"Stream '{stream.id}' has a non-positive deadline.",
                    location=stream.id,
                )
            )
        if stream.max_frame_size_bytes <= 0:
            issues.append(
                ValidationIssue(
                    code="streams.frame.invalid",
                    message=f"Stream '{stream.id}' has a non-positive frame size.",
                    location=stream.id,
                )
            )
        if stream.route_id is None or stream.route_id not in routes_by_id:
            issues.append(
                ValidationIssue(
                    code="streams.route.missing",
                    message=(
                        f"Stream '{stream.id}' does not reference a valid normalized route. "
                        "Ensure routes.json provides a route for the stream."
                    ),
                    location=stream.id,
                )
            )
            continue
        route = routes_by_id[stream.route_id]
        if not route.hops or route.hops[0].node_id != stream.source_node_id:
            issues.append(
                ValidationIssue(
                    code="streams.route.source-mismatch",
                    message=f"Stream '{stream.id}' route does not start at the stream source node.",
                    location=stream.id,
                )
            )
        if route.hops[-1].node_id != stream.destination_node_id:
            issues.append(
                ValidationIssue(
                    code="streams.route.destination-mismatch",
                    message=f"Stream '{stream.id}' route does not end at the stream destination node.",
                    location=stream.id,
                )
            )
    return issues
