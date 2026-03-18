"""Integration coverage for the standalone simulation pipeline."""

from __future__ import annotations

from drts_tsn.io.json_io import read_json
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
    run_manifest_json = read_json(layout.metadata_dir / "run_manifest.json")
    assert run_manifest_json["pipeline"] == "simulate"
    assert run_manifest_json["command_invoked"].startswith("simulate ")
    assert (layout.metadata_dir / "artifact_index.json").exists()

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
    assert_csv_contract(traces_root / "credit_trace.csv", SIMULATION_TABLE_FIELDS["credit_trace"])
    assert_csv_contract(
        traces_root / "scheduler_decision_trace.csv",
        SIMULATION_TABLE_FIELDS["scheduler_decision_trace"],
    )
    response_rows = assert_csv_contract(
        traces_root / "response_time_trace.csv",
        SIMULATION_TABLE_FIELDS["response_time_trace"],
    )
    assert len(response_rows) == 1
    assert response_rows[0]["stream_id"] == "stream-a"


def test_simulate_pipeline_runs_assignment_case_end_to_end(
    repo_root,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The provided assignment case should complete simulation and emit response-time summaries."""

    result, layout = execute(
        repo_root / "cases" / "external" / "test-case-1",
        output_root=tmp_path,
        run_id="simulate-assignment-case",
    )

    assert result.summary["engine_status"] == "ok"
    assert result.tables["response_time_trace"]
    assert result.tables["stream_summary"]

    response_rows = assert_csv_contract(
        layout.simulation_traces_dir / "response_time_trace.csv",
        SIMULATION_TABLE_FIELDS["response_time_trace"],
    )
    stream_rows = assert_csv_contract(
        layout.simulation_results_dir / "stream_summary.csv",
        SIMULATION_TABLE_FIELDS["stream_summary"],
    )
    run_rows = assert_csv_contract(
        layout.simulation_results_dir / "run_summary.csv",
        SIMULATION_TABLE_FIELDS["run_summary"],
    )

    assert len(stream_rows) == 10
    assert len(response_rows) == 10
    assert all(float(row["response_time_us"]) >= 0.0 for row in response_rows)
    assert int(run_rows[0]["delivered_frame_count"]) == len(response_rows)
    assert run_rows[0]["stop_reason"] == "delivery_target_reached"
