"""Checks required before baseline simulation processing."""

from __future__ import annotations

from drts_tsn.domain.case import Case
from drts_tsn.domain.routes import route_link_ids

from .errors import ValidationIssue


def validate_simulation_preconditions(case: Case) -> list[ValidationIssue]:
    """Validate conditions specifically required by the simulation engine."""

    issues: list[ValidationIssue] = []
    if not case.streams:
        issues.append(
            ValidationIssue(
                code="simulation.streams.required",
                message="Simulation requires at least one stream.",
            )
        )
        return issues

    route_by_id = {(route.route_id or route.stream_id): route for route in case.routes}
    link_ids = {link.id for link in case.topology.links}
    for stream in case.streams:
        route = route_by_id.get(stream.route_id or stream.id)
        if route is None:
            issues.append(
                ValidationIssue(
                    code="simulation.route.required",
                    message=f"Simulation stream '{stream.id}' requires a normalized route.",
                    location=stream.id,
                )
            )
            continue
        path_link_ids = route_link_ids(route)
        if not path_link_ids:
            issues.append(
                ValidationIssue(
                    code="simulation.route.links.required",
                    message=(
                        f"Simulation stream '{stream.id}' requires at least one resolved directed link "
                        "on its route."
                    ),
                    location=stream.id,
                )
            )
            continue
        unknown_link_ids = sorted(link_id for link_id in path_link_ids if link_id not in link_ids)
        if unknown_link_ids:
            issues.append(
                ValidationIssue(
                    code="simulation.route.link.unknown",
                    message=(
                        f"Simulation stream '{stream.id}' route references unknown links: "
                        + ",".join(unknown_link_ids)
                    ),
                    location=stream.id,
                )
            )
    return issues
