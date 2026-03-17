"""Placeholder CBS-specific validation checks."""

from __future__ import annotations

from drts_tsn.domain.case import Case
from drts_tsn.domain.enums import TrafficClass

from .errors import ValidationIssue


def validate_cbs_settings(case: Case) -> list[ValidationIssue]:
    """Validate baseline queue and CBS settings."""

    issues: list[ValidationIssue] = []
    queue_by_class = {queue.traffic_class: queue for queue in case.queues}
    for traffic_class in (
        TrafficClass.CLASS_A,
        TrafficClass.CLASS_B,
        TrafficClass.BEST_EFFORT,
    ):
        if traffic_class not in queue_by_class:
            issues.append(
                ValidationIssue(
                    code="queues.class.missing",
                    message=f"Missing queue definition for traffic class '{traffic_class.value}'.",
                )
            )
    for traffic_class in (TrafficClass.CLASS_A, TrafficClass.CLASS_B):
        queue = queue_by_class.get(traffic_class)
        if queue is None:
            continue
        if not queue.uses_cbs or queue.credit_parameters is None:
            issues.append(
                ValidationIssue(
                    code="queues.cbs.required",
                    message=f"Traffic class '{traffic_class.value}' must use CBS in the baseline model.",
                )
            )
            continue
        if queue.credit_parameters.idle_slope_mbps <= 0:
            issues.append(
                ValidationIssue(
                    code="queues.cbs.idle.invalid",
                    message=f"Traffic class '{traffic_class.value}' has a non-positive idle slope.",
                )
            )
        if (queue.credit_parameters.send_slope_mbps or 0.0) <= 0:
            issues.append(
                ValidationIssue(
                    code="queues.cbs.send.invalid",
                    message=f"Traffic class '{traffic_class.value}' has a non-positive send slope.",
                )
            )
    be_queue = queue_by_class.get(TrafficClass.BEST_EFFORT)
    if be_queue is not None and be_queue.uses_cbs:
        issues.append(
            ValidationIssue(
                code="queues.be.cbs.unsupported",
                message="Best-effort traffic must not use CBS in the baseline model.",
            )
        )
    return issues
