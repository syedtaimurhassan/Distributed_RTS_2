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


def _resolve_slope_values(raw_value: object, *, reference_link_speed_mbps: float) -> tuple[float, float]:
    """Resolve a configured slope into canonical `(share, rate_mbps)` values."""

    numeric = float(raw_value)
    if numeric <= 0:
        raise ValueError("CBS slope values must be positive.")
    if numeric <= 1.0:
        return numeric, numeric * reference_link_speed_mbps
    return numeric / reference_link_speed_mbps, numeric


def derive_priority_classes(case: Case) -> Case:
    """Populate baseline queue definitions for the normalized case."""

    queue_profiles = case.parameters.get("queue_profiles", {})
    # Baseline configuration follows the assignment simplification at 100 Mb/s
    # unless the case/config explicitly overrides the baseline link speed.
    baseline_link_speed_mbps = float(case.parameters.get("link_speed_mbps", DEFAULT_LINK_SPEED_MBPS))

    def profile(traffic_class: TrafficClass) -> dict[str, object]:
        raw = queue_profiles.get(traffic_class.value, {}) if isinstance(queue_profiles, dict) else {}
        if not isinstance(raw, dict):
            return {}
        return raw

    class_a_profile = profile(TrafficClass.CLASS_A)
    class_b_profile = profile(TrafficClass.CLASS_B)
    class_a_idle_share, class_a_idle_mbps = _resolve_slope_values(
        class_a_profile.get("idle_slope", DEFAULT_CBS_SLOPE_SHARE),
        reference_link_speed_mbps=baseline_link_speed_mbps,
    )
    class_a_send_share, class_a_send_mbps = _resolve_slope_values(
        class_a_profile.get("send_slope", DEFAULT_CBS_SLOPE_SHARE),
        reference_link_speed_mbps=baseline_link_speed_mbps,
    )
    class_b_idle_share, class_b_idle_mbps = _resolve_slope_values(
        class_b_profile.get("idle_slope", DEFAULT_CBS_SLOPE_SHARE),
        reference_link_speed_mbps=baseline_link_speed_mbps,
    )
    class_b_send_share, class_b_send_mbps = _resolve_slope_values(
        class_b_profile.get("send_slope", DEFAULT_CBS_SLOPE_SHARE),
        reference_link_speed_mbps=baseline_link_speed_mbps,
    )
    queues = [
        QueueDefinition(
            traffic_class=TrafficClass.CLASS_A,
            priority=CLASS_PRIORITY_ORDER[TrafficClass.CLASS_A.value],
            uses_cbs=True,
            credit_parameters=CreditParameters(
                idle_slope_mbps=class_a_idle_mbps,
                send_slope_mbps=class_a_send_mbps,
                idle_slope_share=class_a_idle_share,
                send_slope_share=class_a_send_share,
                slope_reference_speed_mbps=baseline_link_speed_mbps,
            ),
        ),
        QueueDefinition(
            traffic_class=TrafficClass.CLASS_B,
            priority=CLASS_PRIORITY_ORDER[TrafficClass.CLASS_B.value],
            uses_cbs=True,
            credit_parameters=CreditParameters(
                idle_slope_mbps=class_b_idle_mbps,
                send_slope_mbps=class_b_send_mbps,
                idle_slope_share=class_b_idle_share,
                send_slope_share=class_b_send_share,
                slope_reference_speed_mbps=baseline_link_speed_mbps,
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
