"""Unit tests for the simulation baseline."""

from __future__ import annotations

import pytest

from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.simulation.config import SimulationConfig
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


def test_simulation_engine_honors_delivery_target_stop_condition(repo_root) -> None:
    """Simulation should stop early once the configured delivery target is reached."""

    prepared = prepare_case(repo_root / "cases" / "external" / "test-case-1")
    result = SimulationEngine().run(
        prepared.normalized_case,
        SimulationConfig(max_releases_per_stream=1, max_deliveries_total=3),
    )

    run_summary = result.tables["run_summary"][0]
    assert run_summary["stop_reason"] == "delivery_target_reached"
    assert int(run_summary["delivered_frame_count"]) >= 3
    assert int(run_summary["delivered_frame_count"]) < 10
    assert len(result.tables["response_time_trace"]) == int(run_summary["delivered_frame_count"])
