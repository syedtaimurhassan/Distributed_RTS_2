"""Higher-priority interference terms for baseline AVB analysis."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.analysis.link_model import LinkFlow
from drts_tsn.domain.enums import TrafficClass

from .credit_recovery import blocking_credit_recovery_us


@dataclass(slots=True, frozen=True)
class HigherPriorityTerm:
    """One higher-priority interference candidate."""

    competitor_stream_id: str
    competitor_class: str
    transmission_time_us: float
    blocking_credit_recovery_us: float
    selected: bool
    contribution_us: float


@dataclass(slots=True, frozen=True)
class HigherPriorityInterference:
    """Aggregate higher-priority interference for one analyzed link context."""

    total_us: float
    selected_stream_id: str | None
    terms: tuple[HigherPriorityTerm, ...]


def compute_higher_priority_interference(
    *,
    analyzed_class: TrafficClass,
    higher_priority_flows: tuple[LinkFlow, ...],
    lower_priority_blocking_us: float,
) -> HigherPriorityInterference:
    """Return higher-priority interference for baseline AVB Class A/B."""

    if analyzed_class == TrafficClass.CLASS_A or not higher_priority_flows:
        return HigherPriorityInterference(total_us=0.0, selected_stream_id=None, terms=())

    selected_flow = max(
        higher_priority_flows,
        key=lambda flow: (flow.transmission_time_us, flow.stream_id),
    )
    blocking_recovery_us = blocking_credit_recovery_us(
        lower_priority_blocking_us,
        idle_slope_share=selected_flow.reserved_share,
        send_slope_share=selected_flow.send_slope_share,
    )
    return HigherPriorityInterference(
        total_us=selected_flow.transmission_time_us + blocking_recovery_us,
        selected_stream_id=selected_flow.stream_id,
        terms=tuple(
            HigherPriorityTerm(
                competitor_stream_id=flow.stream_id,
                competitor_class=flow.traffic_class.value,
                transmission_time_us=flow.transmission_time_us,
                blocking_credit_recovery_us=blocking_recovery_us if flow.stream_id == selected_flow.stream_id else 0.0,
                selected=flow.stream_id == selected_flow.stream_id,
                contribution_us=(
                    flow.transmission_time_us + blocking_recovery_us
                    if flow.stream_id == selected_flow.stream_id
                    else 0.0
                ),
            )
            for flow in higher_priority_flows
        ),
    )
