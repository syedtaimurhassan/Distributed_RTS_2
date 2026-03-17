"""Unit tests for the simulation baseline."""

from __future__ import annotations

import pytest

from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.simulation.engine import SimulationEngine


def test_simulation_engine_computes_baseline_response(sample_case_path) -> None:
    """The baseline simulator should produce deterministic end-to-end response times."""

    prepared = prepare_case(sample_case_path)
    result = SimulationEngine().run(prepared.normalized_case)

    assert len(result.stream_results) == 1
    assert result.stream_results[0].max_response_time_us == pytest.approx(40.96)
    assert result.stream_results[0].frame_count == 1
    assert result.summary["engine_status"] == "ok"
    assert len(result.detail_rows) == 2
    assert len(result.tables["frame_release_trace"]) == 1
    assert len(result.tables["enqueue_trace"]) == 2
    assert len(result.tables["transmission_trace"]) == 2
    assert len(result.tables["forwarding_trace"]) == 1
    assert len(result.tables["delivery_trace"]) == 1
    assert result.tables["response_time_trace"][0]["response_time_us"] == pytest.approx(40.96)
    assert len(result.tables["credit_trace"]) >= 2
    assert result.tables["credit_trace"][0]["change_reason"].startswith("transmit:")
    assert len(result.tables["scheduler_decision_trace"]) >= 2
    assert len(result.tables["stream_summary"]) == 1
    assert len(result.tables["hop_summary"]) == 2
    assert len(result.tables["queue_summary"]) == 6
    assert result.tables["run_summary"][0]["stop_reason"] == "delivery_target_reached"
