"""Checks required before analytical WCRT processing."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.common.constants import DEFAULT_LINK_SPEED_MBPS
from drts_tsn.domain.case import Case
from drts_tsn.domain.credits import (
    effective_idle_slope_mbps,
    idle_slope_share,
    slope_semantics_summary,
    validate_credit_parameter_consistency,
)
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.routes import route_link_ids

from .errors import ValidationIssue


@dataclass(slots=True, frozen=True)
class ReservedShareComponent:
    """Per-class reserved-bandwidth contribution on one link."""

    traffic_class: TrafficClass
    reserved_share: float
    effective_idle_slope_mbps: float
    semantics: str


def _reserved_component_for_class(
    case: Case,
    traffic_class: TrafficClass,
    *,
    link_speed_mbps: float,
) -> ReservedShareComponent:
    """Return the reserved-share contribution for one class on one link."""

    for queue in case.queues:
        if queue.traffic_class != traffic_class:
            continue
        if not queue.uses_cbs or queue.credit_parameters is None:
            return ReservedShareComponent(
                traffic_class=traffic_class,
                reserved_share=0.0,
                effective_idle_slope_mbps=0.0,
                semantics="non-cbs",
            )
        return ReservedShareComponent(
            traffic_class=traffic_class,
            reserved_share=idle_slope_share(queue.credit_parameters),
            effective_idle_slope_mbps=effective_idle_slope_mbps(
                queue.credit_parameters,
                link_speed_mbps=link_speed_mbps,
            ),
            semantics=slope_semantics_summary(queue.credit_parameters),
        )
    return ReservedShareComponent(
        traffic_class=traffic_class,
        reserved_share=0.0,
        effective_idle_slope_mbps=0.0,
        semantics="missing-queue",
    )


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
            components: list[ReservedShareComponent] = []
            component_error = False
            for traffic_class in relevant_classes:
                queue = next(
                    (
                        candidate_queue
                        for candidate_queue in case.queues
                        if candidate_queue.traffic_class == traffic_class
                    ),
                    None,
                )
                if queue is not None and queue.credit_parameters is not None:
                    consistency_issues = validate_credit_parameter_consistency(queue.credit_parameters)
                    if consistency_issues:
                        issues.append(
                            ValidationIssue(
                                code="analysis.cbs.slope.inconsistent",
                                message=(
                                    f"Inconsistent CBS slope configuration for stream '{stream.id}', "
                                    f"class '{traffic_class.value}', link '{link_id}': "
                                    + "; ".join(consistency_issues)
                                ),
                                location=f"{stream.id}:{link_id}:{traffic_class.value}",
                            )
                        )
                        component_error = True
                        continue
                components.append(
                    _reserved_component_for_class(
                        case,
                        traffic_class,
                        link_speed_mbps=link_speed_mbps,
                    )
                )
            if component_error:
                continue
            cumulative_reserved_share = sum(component.reserved_share for component in components)
            if cumulative_reserved_share > 1.0 + 1e-9:
                component_summary = "; ".join(
                    (
                        f"{component.traffic_class.value}: "
                        f"reserved_share={component.reserved_share:.6f} (normalized share), "
                        f"effective_idle_slope_mbps={component.effective_idle_slope_mbps:.6f} "
                        f"at link_speed_mbps={link_speed_mbps:.6f}, "
                        f"semantics={component.semantics}"
                    )
                    for component in components
                )
                issues.append(
                    ValidationIssue(
                        code="analysis.reserved-bandwidth.exceeded",
                        message=(
                            f"Reserved bandwidth for stream '{stream.id}', class '{stream.traffic_class.value}', "
                            f"on link '{link_id}' exceeds 1.0. "
                            f"cumulative_reserved_share={cumulative_reserved_share:.6f}. "
                            f"Components: {component_summary}"
                        ),
                        location=f"{stream.id}:{link_id}",
                    )
                )
    return issues
