"""Unit tests for canonical CBS slope normalization and per-link reservation semantics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from drts_tsn.analysis.link_model import build_link_traffic_contexts
from drts_tsn.domain.credits import effective_idle_slope_mbps, effective_send_slope_mbps
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.validation.analysis_preconditions import validate_analysis_preconditions


def test_normalization_stores_explicit_share_and_reference_rate(sample_case_path) -> None:
    """Normalized queue definitions should carry both share and reference-rate values."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    queue_by_class = {queue.traffic_class: queue for queue in prepared.normalized_case.queues}
    class_a = queue_by_class[TrafficClass.CLASS_A].credit_parameters
    class_b = queue_by_class[TrafficClass.CLASS_B].credit_parameters
    assert class_a is not None and class_b is not None

    assert class_a.idle_slope_share == 0.5
    assert class_a.send_slope_share == 0.5
    assert class_a.idle_slope_mbps == 50.0
    assert class_a.send_slope_mbps == 50.0
    assert class_a.slope_reference_speed_mbps == 100.0
    assert class_b.idle_slope_share == 0.5
    assert class_b.send_slope_share == 0.5
    assert class_b.idle_slope_mbps == 50.0
    assert class_b.send_slope_mbps == 50.0
    assert class_b.slope_reference_speed_mbps == 100.0


def test_effective_slope_rates_are_derived_per_link(sample_case_path) -> None:
    """Effective Mbps values should be computed from canonical shares per link speed."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    queue_by_class = {queue.traffic_class: queue for queue in prepared.normalized_case.queues}
    class_a = queue_by_class[TrafficClass.CLASS_A].credit_parameters
    assert class_a is not None

    assert effective_idle_slope_mbps(class_a, link_speed_mbps=100.0) == 50.0
    assert effective_send_slope_mbps(class_a, link_speed_mbps=100.0) == 50.0
    assert effective_idle_slope_mbps(class_a, link_speed_mbps=1000.0) == 500.0
    assert effective_send_slope_mbps(class_a, link_speed_mbps=1000.0) == 500.0


def test_assignment_case_contexts_use_normalized_reservation_shares(repo_root) -> None:
    """Provided assignment case should derive per-link reserved shares from normalized slope shares."""

    prepared = prepare_case(
        repo_root / "cases" / "external" / "test-case-1",
        include_analysis_checks=True,
    )
    contexts = build_link_traffic_contexts(prepared.normalized_case)
    class_a_contexts = [context for context in contexts if context.traffic_class == TrafficClass.CLASS_A]
    class_b_contexts = [context for context in contexts if context.traffic_class == TrafficClass.CLASS_B]

    assert class_a_contexts
    assert class_b_contexts
    assert all(context.reserved_share == 0.5 for context in class_a_contexts)
    assert all(context.reserved_share == 0.5 for context in class_b_contexts)
    assert all(context.reserved_share_up_to_class == 1.0 for context in class_b_contexts)
    assert validate_analysis_preconditions(prepared.normalized_case) == []


def test_analysis_preconditions_fail_when_cumulative_reserved_share_exceeds_one(repo_root) -> None:
    """Reserved-bandwidth precondition should fail once class-plus-higher shares exceed 1.0."""

    prepared = prepare_case(
        repo_root / "cases" / "external" / "test-case-1",
        include_analysis_checks=True,
    )
    invalid_case = deepcopy(prepared.normalized_case)
    invalid_case.queues = [
        replace(
            queue,
            credit_parameters=replace(
                queue.credit_parameters,
                idle_slope_share=0.6,
                send_slope_share=0.6,
                idle_slope_mbps=60.0,
                send_slope_mbps=60.0,
            ),
        )
        if queue.traffic_class == TrafficClass.CLASS_B and queue.credit_parameters is not None
        else queue
        for queue in invalid_case.queues
    ]

    issues = validate_analysis_preconditions(invalid_case)
    assert any(issue.code == "analysis.reserved-bandwidth.exceeded" for issue in issues)


def test_precondition_diagnostics_report_per_link_effective_mbps_from_shared_reservation(repo_root) -> None:
    """Diagnostics should derive effective Mbps per link from one canonical normalized share."""

    prepared = prepare_case(
        repo_root / "cases" / "external" / "test-case-1",
        include_analysis_checks=True,
    )
    invalid_case = deepcopy(prepared.normalized_case)
    link_speed_overrides = {"link5": 100.0, "link2": 1000.0}
    invalid_case.topology.links = [
        replace(
            link,
            speed_mbps=link_speed_overrides.get(link.id, link.speed_mbps),
        )
        for link in invalid_case.topology.links
    ]
    invalid_case.queues = [
        replace(
            queue,
            credit_parameters=replace(
                queue.credit_parameters,
                idle_slope_share=1.2,
                send_slope_share=1.2,
                idle_slope_mbps=120.0,
                send_slope_mbps=120.0,
            ),
        )
        if queue.traffic_class == TrafficClass.CLASS_A and queue.credit_parameters is not None
        else queue
        for queue in invalid_case.queues
    ]

    issues = validate_analysis_preconditions(invalid_case)
    reserved_issues = [issue for issue in issues if issue.code == "analysis.reserved-bandwidth.exceeded"]

    assert len(reserved_issues) >= 2
    issue_link_1 = next(issue for issue in reserved_issues if issue.location == "stream-0:link5")
    issue_link_2 = next(issue for issue in reserved_issues if issue.location == "stream-0:link2")
    assert "effective_idle_slope_mbps=120.000000 at link_speed_mbps=100.000000" in issue_link_1.message
    assert "effective_idle_slope_mbps=1200.000000 at link_speed_mbps=1000.000000" in issue_link_2.message
