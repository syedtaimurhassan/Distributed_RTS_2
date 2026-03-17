"""Integration coverage for the standalone simulation pipeline."""

from __future__ import annotations

from drts_tsn.orchestration.pipeline_simulate import execute
from drts_tsn.simulation.outputs.simulation_result_builder import SIMULATION_TABLE_FIELDS


def test_simulate_pipeline_writes_required_artifacts(
    sample_case_path,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The simulation pipeline should emit stable trace and summary artifacts."""

    result, layout = execute(sample_case_path, output_root=tmp_path, run_id="simulate-pipeline-test")

    assert result.summary["engine_status"] == "ok"
    assert result.tables["response_time_trace"]
    assert result.tables["stream_summary"]

    results_root = layout.simulation_results_dir
    traces_root = layout.simulation_traces_dir
    assert_csv_contract(results_root / "stream_summary.csv", SIMULATION_TABLE_FIELDS["stream_summary"])
    assert_csv_contract(results_root / "hop_summary.csv", SIMULATION_TABLE_FIELDS["hop_summary"])
    assert_csv_contract(results_root / "queue_summary.csv", SIMULATION_TABLE_FIELDS["queue_summary"])
    assert_csv_contract(results_root / "run_summary.csv", SIMULATION_TABLE_FIELDS["run_summary"])
    assert_csv_contract(traces_root / "frame_release_trace.csv", SIMULATION_TABLE_FIELDS["frame_release_trace"])
    assert_csv_contract(traces_root / "enqueue_trace.csv", SIMULATION_TABLE_FIELDS["enqueue_trace"])
    assert_csv_contract(traces_root / "transmission_trace.csv", SIMULATION_TABLE_FIELDS["transmission_trace"])
    assert_csv_contract(traces_root / "forwarding_trace.csv", SIMULATION_TABLE_FIELDS["forwarding_trace"])
    assert_csv_contract(traces_root / "delivery_trace.csv", SIMULATION_TABLE_FIELDS["delivery_trace"])
    response_rows = assert_csv_contract(
        traces_root / "response_time_trace.csv",
        SIMULATION_TABLE_FIELDS["response_time_trace"],
    )
    assert len(response_rows) == 1
    assert response_rows[0]["stream_id"] == "stream-a"
