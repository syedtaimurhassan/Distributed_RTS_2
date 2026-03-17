"""Same-priority interference terms for baseline AVB analysis."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.analysis.link_model import LinkFlow
from drts_tsn.common.math_utils import ceiling_division_ratio

from .credit_recovery import credit_recovery_us


@dataclass(slots=True, frozen=True)
class SamePriorityTerm:
    """One same-priority interference contribution."""

    competitor_stream_id: str
    transmission_time_us: float
    credit_recovery_us: float
    eligible_interval_us: float
    queued_ahead_count: int
    contribution_us: float


@dataclass(slots=True, frozen=True)
class SamePriorityInterference:
    """Aggregate same-priority interference for one analyzed link context."""

    total_us: float
    terms: tuple[SamePriorityTerm, ...]


def _queued_ahead_count(
    *,
    analyzed_deadline_us: float,
    analyzed_period_us: float,
    competitor_period_us: float,
) -> int:
    """Return the bounded number of same-priority queued-ahead frames."""

    if analyzed_deadline_us <= analyzed_period_us:
        return 1
    return max(1, ceiling_division_ratio(analyzed_deadline_us, competitor_period_us))


def compute_same_priority_interference(
    *,
    analyzed_deadline_us: float,
    analyzed_period_us: float,
    same_priority_flows: tuple[LinkFlow, ...],
) -> SamePriorityInterference:
    """Return same-priority interference using eligible intervals."""

    terms: list[SamePriorityTerm] = []
    for flow in same_priority_flows:
        recovery_us = credit_recovery_us(flow.transmission_time_us, flow.reserved_share)
        eligible_interval_us = flow.transmission_time_us + recovery_us
        queued_ahead_count = _queued_ahead_count(
            analyzed_deadline_us=analyzed_deadline_us,
            analyzed_period_us=analyzed_period_us,
            competitor_period_us=flow.period_us,
        )
        terms.append(
            SamePriorityTerm(
                competitor_stream_id=flow.stream_id,
                transmission_time_us=flow.transmission_time_us,
                credit_recovery_us=recovery_us,
                eligible_interval_us=eligible_interval_us,
                queued_ahead_count=queued_ahead_count,
                contribution_us=queued_ahead_count * eligible_interval_us,
            )
        )
    return SamePriorityInterference(
        total_us=sum(term.contribution_us for term in terms),
        terms=tuple(terms),
    )
