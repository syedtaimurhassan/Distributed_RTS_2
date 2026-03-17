"""Unit tests for the Milestone 2 analysis formula modules."""

from __future__ import annotations

import pytest

from drts_tsn.analysis.formulas.class_a_wcrt import compute_class_a_wcrt_us
from drts_tsn.analysis.formulas.class_b_wcrt import compute_class_b_wcrt_us
from drts_tsn.analysis.formulas.credit_recovery import (
    blocking_credit_recovery_us,
    credit_recovery_us,
)
from drts_tsn.analysis.formulas.higher_priority_interference import compute_higher_priority_interference
from drts_tsn.analysis.formulas.lower_priority_interference import compute_lower_priority_interference
from drts_tsn.analysis.formulas.same_priority_interference import compute_same_priority_interference
from drts_tsn.analysis.formulas.transmission_time import transmission_time_us
from drts_tsn.analysis.link_model import LinkFlow
from drts_tsn.domain.enums import TrafficClass


def _flow(
    stream_id: str,
    *,
    traffic_class: TrafficClass,
    priority: int,
    transmission_us: float,
    reserved_share: float,
    period_us: float = 1000.0,
    deadline_us: float = 1000.0,
    send_slope_share: float = 0.5,
) -> LinkFlow:
    """Build a compact link-flow fixture."""

    return LinkFlow(
        stream_id=stream_id,
        traffic_class=traffic_class,
        priority=priority,
        period_us=period_us,
        deadline_us=deadline_us,
        frame_size_bytes=256,
        transmission_time_us=transmission_us,
        reserved_share=reserved_share,
        send_slope_share=send_slope_share,
    )


def test_transmission_and_credit_recovery_formulas() -> None:
    """Transmission and credit-recovery helpers should stay deterministic."""

    assert transmission_time_us(256, 100.0) == pytest.approx(20.48)
    assert credit_recovery_us(20.48, 0.5) == pytest.approx(20.48)
    assert blocking_credit_recovery_us(12.8, idle_slope_share=0.5, send_slope_share=0.5) == pytest.approx(
        12.8
    )


def test_same_priority_interference_includes_credit_recovery() -> None:
    """SPI should use eligible intervals rather than raw transmission times."""

    competitor = _flow(
        "stream-peer",
        traffic_class=TrafficClass.CLASS_A,
        priority=2,
        transmission_us=20.48,
        reserved_share=0.5,
    )

    interference = compute_same_priority_interference(
        analyzed_deadline_us=1000.0,
        analyzed_period_us=1000.0,
        same_priority_flows=(competitor,),
    )

    assert interference.total_us == pytest.approx(40.96)
    assert interference.terms[0].queued_ahead_count == 1
    assert interference.terms[0].eligible_interval_us == pytest.approx(40.96)


def test_same_priority_interference_uses_one_frame_rule_when_deadline_does_not_exceed_period() -> None:
    """The baseline one-frame rule should cap same-priority backlog when deadline <= period."""

    competitor = _flow(
        "stream-peer",
        traffic_class=TrafficClass.CLASS_A,
        priority=2,
        transmission_us=20.48,
        reserved_share=0.5,
        period_us=250.0,
    )

    interference = compute_same_priority_interference(
        analyzed_deadline_us=1000.0,
        analyzed_period_us=1000.0,
        same_priority_flows=(competitor,),
    )

    assert interference.terms[0].queued_ahead_count == 1
    assert interference.total_us == pytest.approx(40.96)


def test_lower_priority_interference_selects_maximum_frame() -> None:
    """LPI should be the maximum lower-priority transmission time."""

    interference = compute_lower_priority_interference(
        (
            _flow(
                "stream-b",
                traffic_class=TrafficClass.CLASS_B,
                priority=1,
                transmission_us=18.0,
                reserved_share=0.5,
            ),
            _flow(
                "stream-be",
                traffic_class=TrafficClass.BEST_EFFORT,
                priority=0,
                transmission_us=120.0,
                reserved_share=0.0,
                send_slope_share=0.0,
            ),
        )
    )

    assert interference.total_us == pytest.approx(120.0)
    assert interference.selected_stream_id == "stream-be"


def test_class_a_has_no_higher_priority_interference() -> None:
    """Class A must never report higher-priority interference in the baseline model."""

    higher_priority = compute_higher_priority_interference(
        analyzed_class=TrafficClass.CLASS_A,
        higher_priority_flows=(
            _flow(
                "stream-a-peer",
                traffic_class=TrafficClass.CLASS_A,
                priority=2,
                transmission_us=20.48,
                reserved_share=0.5,
            ),
        ),
        lower_priority_blocking_us=12.8,
    )

    assert higher_priority.total_us == 0.0
    assert higher_priority.selected_stream_id is None
    assert higher_priority.terms == ()


def test_higher_priority_interference_for_class_b_uses_max_a_and_blocking_credit() -> None:
    """Class B HPI should include one max Class A frame plus blocking credit recovery."""

    higher_priority = compute_higher_priority_interference(
        analyzed_class=TrafficClass.CLASS_B,
        higher_priority_flows=(
            _flow(
                "stream-a",
                traffic_class=TrafficClass.CLASS_A,
                priority=2,
                transmission_us=20.48,
                reserved_share=0.5,
            ),
        ),
        lower_priority_blocking_us=12.8,
    )

    assert higher_priority.total_us == pytest.approx(33.28)
    assert higher_priority.selected_stream_id == "stream-a"
    assert higher_priority.terms[0].blocking_credit_recovery_us == pytest.approx(12.8)


def test_class_b_higher_priority_interference_selects_maximum_class_a_frame() -> None:
    """Class B HPI should select the largest Class A frame contribution on the link."""

    higher_priority = compute_higher_priority_interference(
        analyzed_class=TrafficClass.CLASS_B,
        higher_priority_flows=(
            _flow(
                "stream-a-small",
                traffic_class=TrafficClass.CLASS_A,
                priority=2,
                transmission_us=18.0,
                reserved_share=0.5,
            ),
            _flow(
                "stream-a-large",
                traffic_class=TrafficClass.CLASS_A,
                priority=2,
                transmission_us=20.48,
                reserved_share=0.5,
            ),
        ),
        lower_priority_blocking_us=12.8,
    )

    assert higher_priority.selected_stream_id == "stream-a-large"
    assert higher_priority.total_us == pytest.approx(33.28)
    assert [term.selected for term in higher_priority.terms] == [False, True]


def test_class_a_and_class_b_wcrt_composition() -> None:
    """Per-link WCRT formulas should compose the expected term families."""

    assert compute_class_a_wcrt_us(
        transmission_time_us=20.48,
        same_priority_interference_us=40.96,
        lower_priority_interference_us=12.8,
    ) == pytest.approx(74.24)
    assert compute_class_b_wcrt_us(
        transmission_time_us=20.48,
        same_priority_interference_us=40.96,
        lower_priority_interference_us=12.8,
        higher_priority_interference_us=33.28,
    ) == pytest.approx(107.52)


def test_class_b_and_class_a_use_the_same_lower_priority_structure() -> None:
    """LPI should be independent of whether the analyzed AVB class is A or B."""

    lower_priority = compute_lower_priority_interference(
        (
            _flow(
                "stream-be-small",
                traffic_class=TrafficClass.BEST_EFFORT,
                priority=0,
                transmission_us=80.0,
                reserved_share=0.0,
                send_slope_share=0.0,
            ),
            _flow(
                "stream-be-large",
                traffic_class=TrafficClass.BEST_EFFORT,
                priority=0,
                transmission_us=120.0,
                reserved_share=0.0,
                send_slope_share=0.0,
            ),
        )
    )

    class_a_wcrt = compute_class_a_wcrt_us(
        transmission_time_us=20.48,
        same_priority_interference_us=0.0,
        lower_priority_interference_us=lower_priority.total_us,
    )
    class_b_wcrt = compute_class_b_wcrt_us(
        transmission_time_us=20.48,
        same_priority_interference_us=0.0,
        lower_priority_interference_us=lower_priority.total_us,
        higher_priority_interference_us=0.0,
    )

    assert lower_priority.total_us == pytest.approx(120.0)
    assert class_a_wcrt == pytest.approx(140.48)
    assert class_b_wcrt == pytest.approx(140.48)
