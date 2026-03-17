"""Checks required before analytical WCRT processing."""

from __future__ import annotations

from drts_tsn.common.constants import DEFAULT_LINK_SPEED_MBPS
from drts_tsn.domain.case import Case
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.routes import route_link_ids

from .errors import ValidationIssue


def _reserved_share_for_class(case: Case, traffic_class: TrafficClass, *, link_speed_mbps: float) -> float:
    """Return the normalized reserved share for a traffic class on one link."""

    for queue in case.queues:
        if queue.traffic_class != traffic_class:
            continue
        if not queue.uses_cbs or queue.credit_parameters is None:
            return 0.0
        return queue.credit_parameters.idle_slope_mbps / link_speed_mbps
    return 0.0


def validate_analysis_preconditions(case: Case) -> list[ValidationIssue]:
    """Validate conditions specifically required by the analytical engine."""

    issues: list[ValidationIssue] = []
    if not case.routes:
        issues.append(
            ValidationIssue(
                code="analysis.routes.required",
                message="Analytical processing requires route definitions.",
            )
        )
    if not case.queues:
        issues.append(
            ValidationIssue(
                code="analysis.queues.required",
                message="Analytical processing requires normalized queue definitions.",
            )
        )
    if not any(stream.traffic_class.value in {"class_a", "class_b"} for stream in case.streams):
        issues.append(
            ValidationIssue(
                code="analysis.avb.required",
                message="Analytical processing requires at least one AVB Class A or B stream.",
            )
        )
    if issues:
        return issues

    route_by_id = {(route.route_id or route.stream_id): route for route in case.routes}
    link_speeds = {
        link.id: float(link.speed_mbps or DEFAULT_LINK_SPEED_MBPS)
        for link in case.topology.links
    }
    for stream in case.streams:
        if stream.traffic_class == TrafficClass.BEST_EFFORT:
            continue
        route = route_by_id.get(stream.route_id or stream.id)
        if route is None:
            issues.append(
                ValidationIssue(
                    code="analysis.route.required",
                    message=(
                        f"Analytical AVB stream '{stream.id}' requires a normalized route "
                        "with resolved directed links."
                    ),
                    location=stream.id,
                )
            )
            continue
        link_ids = route_link_ids(route)
        if not link_ids:
            issues.append(
                ValidationIssue(
                    code="analysis.route.links.required",
                    message=(
                        f"Analytical AVB stream '{stream.id}' requires at least one resolved "
                        "directed link on its route."
                    ),
                    location=stream.id,
                )
            )
            continue
        relevant_classes = [stream.traffic_class]
        if stream.traffic_class == TrafficClass.CLASS_B:
            relevant_classes.insert(0, TrafficClass.CLASS_A)
        for link_id in link_ids:
            link_speed_mbps = link_speeds.get(link_id, DEFAULT_LINK_SPEED_MBPS)
            cumulative_reserved_share = sum(
                _reserved_share_for_class(case, traffic_class, link_speed_mbps=link_speed_mbps)
                for traffic_class in relevant_classes
            )
            if cumulative_reserved_share > 1.0 + 1e-9:
                issues.append(
                    ValidationIssue(
                        code="analysis.reserved-bandwidth.exceeded",
                        message=(
                            f"Reserved bandwidth for stream '{stream.id}' on link '{link_id}' "
                            f"exceeds 1.0 for the analyzed class and higher priorities."
                        ),
                        location=f"{stream.id}:{link_id}",
                    )
                )
    return issues
