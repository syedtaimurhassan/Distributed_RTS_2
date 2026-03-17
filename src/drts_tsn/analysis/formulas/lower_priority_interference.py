"""Lower-priority blocking terms for baseline AVB analysis."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.analysis.link_model import LinkFlow


@dataclass(slots=True, frozen=True)
class LowerPriorityTerm:
    """One lower-priority blocking candidate."""

    competitor_stream_id: str
    competitor_class: str
    transmission_time_us: float
    selected: bool


@dataclass(slots=True, frozen=True)
class LowerPriorityInterference:
    """Aggregate lower-priority blocking information."""

    total_us: float
    selected_stream_id: str | None
    terms: tuple[LowerPriorityTerm, ...]


def compute_lower_priority_interference(lower_priority_flows: tuple[LinkFlow, ...]) -> LowerPriorityInterference:
    """Return the maximum lower-priority serialization delay."""

    selected_stream_id: str | None = None
    selected_transmission_time_us = 0.0
    if lower_priority_flows:
        selected_flow = max(
            lower_priority_flows,
            key=lambda flow: (flow.transmission_time_us, flow.stream_id),
        )
        selected_stream_id = selected_flow.stream_id
        selected_transmission_time_us = selected_flow.transmission_time_us
    return LowerPriorityInterference(
        total_us=selected_transmission_time_us,
        selected_stream_id=selected_stream_id,
        terms=tuple(
            LowerPriorityTerm(
                competitor_stream_id=flow.stream_id,
                competitor_class=flow.traffic_class.value,
                transmission_time_us=flow.transmission_time_us,
                selected=flow.stream_id == selected_stream_id,
            )
            for flow in lower_priority_flows
        ),
    )
