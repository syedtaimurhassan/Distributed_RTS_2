"""Normalize priority-class-related case data."""

from __future__ import annotations

from dataclasses import replace

from drts_tsn.common.constants import (
    CLASS_PRIORITY_ORDER,
    DEFAULT_CBS_SLOPE_SHARE,
    DEFAULT_LINK_SPEED_MBPS,
)
from drts_tsn.domain.case import Case
from drts_tsn.domain.credits import CreditParameters
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.queues import QueueDefinition


def _resolve_slope_value(raw_value: object, *, link_speed_mbps: float) -> float:
    """Resolve a configured slope into Mbps."""

    numeric = float(raw_value)
    if numeric <= 1.0:
        return numeric * link_speed_mbps
    return numeric


def derive_priority_classes(case: Case) -> Case:
    """Populate baseline queue definitions for the normalized case."""

    queue_profiles = case.parameters.get("queue_profiles", {})
    representative_link_speed = case.topology.links[0].speed_mbps or DEFAULT_LINK_SPEED_MBPS

    def profile(traffic_class: TrafficClass) -> dict[str, object]:
        raw = queue_profiles.get(traffic_class.value, {}) if isinstance(queue_profiles, dict) else {}
        if not isinstance(raw, dict):
            return {}
        return raw

    class_a_profile = profile(TrafficClass.CLASS_A)
    class_b_profile = profile(TrafficClass.CLASS_B)
    queues = [
        QueueDefinition(
            traffic_class=TrafficClass.CLASS_A,
            priority=CLASS_PRIORITY_ORDER[TrafficClass.CLASS_A.value],
            uses_cbs=True,
            credit_parameters=CreditParameters(
                idle_slope_mbps=_resolve_slope_value(
                    class_a_profile.get("idle_slope", DEFAULT_CBS_SLOPE_SHARE),
                    link_speed_mbps=representative_link_speed,
                ),
                send_slope_mbps=_resolve_slope_value(
                    class_a_profile.get("send_slope", DEFAULT_CBS_SLOPE_SHARE),
                    link_speed_mbps=representative_link_speed,
                ),
            ),
        ),
        QueueDefinition(
            traffic_class=TrafficClass.CLASS_B,
            priority=CLASS_PRIORITY_ORDER[TrafficClass.CLASS_B.value],
            uses_cbs=True,
            credit_parameters=CreditParameters(
                idle_slope_mbps=_resolve_slope_value(
                    class_b_profile.get("idle_slope", DEFAULT_CBS_SLOPE_SHARE),
                    link_speed_mbps=representative_link_speed,
                ),
                send_slope_mbps=_resolve_slope_value(
                    class_b_profile.get("send_slope", DEFAULT_CBS_SLOPE_SHARE),
                    link_speed_mbps=representative_link_speed,
                ),
            ),
        ),
        QueueDefinition(
            traffic_class=TrafficClass.BEST_EFFORT,
            priority=CLASS_PRIORITY_ORDER[TrafficClass.BEST_EFFORT.value],
            uses_cbs=False,
            credit_parameters=None,
        ),
    ]
    return replace(case, queues=queues)
