"""Smoke tests for loading, normalizing, and validating a sample case."""

from __future__ import annotations

import pytest

from drts_tsn.domain.enums import TrafficClass
from drts_tsn.orchestration.run_manager import prepare_case


def test_prepare_case_smoke(sample_case_path) -> None:
    """The bundled sample case should load and validate."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)

    assert prepared.normalized_case.metadata.case_id == "test-case-1"
    assert len(prepared.normalized_case.streams) == 1
    assert len(prepared.normalized_case.queues) == 3
    assert prepared.normalized_case.queues[0].traffic_class == TrafficClass.CLASS_A
    assert prepared.normalized_case.streams[0].deadline_us == 1000.0
    assert prepared.normalized_case.streams[0].route_id == "route-stream-a"
    assert prepared.normalized_case.routes[0].hops[0].link_id == "link-1"
    assert prepared.normalized_case.routes[0].hops[0].transmission_time_us == pytest.approx(20.48)
    assert prepared.normalized_case.routes[0].hops[1].link_id == "link-2"
    assert prepared.validation_report.is_valid
