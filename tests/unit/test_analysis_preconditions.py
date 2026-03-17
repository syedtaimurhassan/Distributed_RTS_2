"""Unit tests for analytical precondition enforcement."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from drts_tsn.analysis.config import AnalysisConfig
from drts_tsn.analysis.engine import AnalysisEngine
from drts_tsn.analysis.preconditions import AnalysisPreconditionError
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.validation.analysis_preconditions import validate_analysis_preconditions


def test_analysis_rejects_reserved_bandwidth_exceeding_one(sample_case_path) -> None:
    """Reserved bandwidth above one should be rejected before analysis runs."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    invalid_case = deepcopy(prepared.normalized_case)
    invalid_case.queues = [
        replace(
            queue,
            credit_parameters=replace(
                queue.credit_parameters,
                idle_slope_mbps=120.0,
                send_slope_mbps=120.0,
            ),
        )
        if queue.traffic_class == TrafficClass.CLASS_A and queue.credit_parameters is not None
        else queue
        for queue in invalid_case.queues
    ]

    issues = validate_analysis_preconditions(invalid_case)

    assert any(issue.code == "analysis.reserved-bandwidth.exceeded" for issue in issues)
    with pytest.raises(AnalysisPreconditionError, match="analysis.reserved-bandwidth.exceeded"):
        AnalysisEngine().run(invalid_case)


def test_analysis_preconditions_detect_missing_resolved_route_links(sample_case_path) -> None:
    """AVB streams with no resolved link sequence should fail analytical preconditions."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    invalid_case = deepcopy(prepared.normalized_case)
    invalid_case.routes[0].hops = invalid_case.routes[0].hops[:1]

    issues = validate_analysis_preconditions(invalid_case)

    assert any(issue.code == "analysis.route.links.required" for issue in issues)


def test_non_strict_analysis_reports_structured_precondition_failures(sample_case_path) -> None:
    """Non-strict analysis should keep structured precondition diagnostics in its JSON summary."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    invalid_case = deepcopy(prepared.normalized_case)
    invalid_case.queues = [
        replace(
            queue,
            credit_parameters=replace(
                queue.credit_parameters,
                idle_slope_mbps=120.0,
                send_slope_mbps=120.0,
            ),
        )
        if queue.traffic_class == TrafficClass.CLASS_A and queue.credit_parameters is not None
        else queue
        for queue in invalid_case.queues
    ]

    result = AnalysisEngine().run(invalid_case, AnalysisConfig(strict_validation=False))

    assert result.summary["engine_status"] == "preconditions_failed"
    assert result.summary["precondition_failure_count"] == 2
    assert result.tables["run_summary"][0]["status"] == "preconditions_failed"
    assert all(
        failure["code"] == "analysis.reserved-bandwidth.exceeded"
        for failure in result.summary["precondition_failures"]
    )
