"""Integration tests for the Milestone 2 CLI entrypoint."""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

from drts_tsn.io.json_io import read_json, write_json
from drts_tsn.io.manifest import write_manifest
from drts_tsn.io.yaml_io import write_yaml


def test_python_module_help_runs(repo_root) -> None:
    """`python -m drts_tsn.cli.main --help` should succeed."""

    completed = subprocess.run(
        [sys.executable, "-m", "drts_tsn.cli.main", "--help"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "validate-case" in completed.stdout
    assert "normalize-case" in completed.stdout
    assert "inspect-case" in completed.stdout
    assert "analyze" in completed.stdout
    assert "simulate" in completed.stdout
    assert "compare" in completed.stdout
    assert "run-case" in completed.stdout
    assert "batch-run" in completed.stdout


def test_validate_case_command_runs_for_sample_case(repo_root, sample_case_path) -> None:
    """The validate command should succeed for the bundled sample case."""

    completed = subprocess.run(
        [sys.executable, "-m", "drts_tsn.cli.main", "validate-case", str(sample_case_path)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "Validation passed with no issues." in completed.stdout


def test_inspect_case_command_runs(repo_root, sample_case_path) -> None:
    """The inspect command should run against the bundled sample case."""

    completed = subprocess.run(
        [sys.executable, "-m", "drts_tsn.cli.main", "inspect-case", str(sample_case_path)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "case_id" in completed.stdout
    assert "Nodes" in completed.stdout
    assert "Streams" in completed.stdout


def test_validate_case_command_fails_cleanly_for_invalid_fixture(repo_root, invalid_case_path) -> None:
    """The validate command should return a validation exit code for invalid cases."""

    completed = subprocess.run(
        [sys.executable, "-m", "drts_tsn.cli.main", "validate-case", str(invalid_case_path)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "routes.hop.unknown-node" in completed.stdout


def test_validate_case_command_returns_validation_failure_for_missing_required_file(
    repo_root,
    tmp_path: Path,
) -> None:
    """Missing required external files should be treated as invalid case input."""

    case_dir = tmp_path / "missing-streams"
    case_dir.mkdir()
    write_manifest({"case_id": "missing-streams"}, case_dir)
    write_json(
        {
            "nodes": [{"id": "n1", "type": "end_system"}],
            "links": [],
        },
        case_dir / "topology.json",
    )
    write_json(
        {
            "routes": [{"stream_id": "s1", "hops": [{"node_id": "n1"}]}],
        },
        case_dir / "routes.json",
    )

    completed = subprocess.run(
        [sys.executable, "-m", "drts_tsn.cli.main", "validate-case", str(case_dir)],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "missing required files" in completed.stderr


def test_normalize_case_command_writes_json_and_csv_bundle(repo_root, sample_case_path, tmp_path) -> None:
    """The normalize command should emit the full normalized artifact bundle."""

    output_dir = tmp_path / "normalized-output"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "normalize-case",
            str(sample_case_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert (output_dir / "normalized_case.json").exists()
    assert (output_dir / "nodes.csv").exists()
    assert (output_dir / "links.csv").exists()
    assert (output_dir / "routes.csv").exists()
    assert (output_dir / "streams.csv").exists()
    assert (output_dir / "link_stream_map.csv").exists()


def test_analyze_command_writes_required_analysis_artifacts(repo_root, sample_case_path) -> None:
    """The analyze command should emit the baseline analysis artifact bundle."""

    run_id = f"cli-analysis-test-{uuid.uuid4().hex}"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "analyze",
            str(sample_case_path),
            "--run-id",
            run_id,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    run_root = repo_root / "outputs" / "runs" / run_id / "analysis" / "results"
    assert (run_root / "analysis_result.json").exists()
    assert (run_root / "stream_wcrt_summary.csv").exists()
    assert (run_root / "per_link_wcrt_summary.csv").exists()
    assert (run_root / "run_summary.csv").exists()


def test_analyze_command_fails_cleanly_for_reserved_bandwidth_violation(
    repo_root,
    invalid_reserved_bandwidth_case_path,
) -> None:
    """The analyze command should report analytical precondition failures clearly."""

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "analyze",
            str(invalid_reserved_bandwidth_case_path),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "analysis.reserved-bandwidth.exceeded" in completed.stderr
    assert "stream-a:link-1" in completed.stderr


def test_analyze_command_honors_non_strict_analysis_config(
    repo_root,
    invalid_reserved_bandwidth_case_path,
    tmp_path: Path,
) -> None:
    """Non-strict analysis config should allow diagnostic result emission for precondition failures."""

    config_path = tmp_path / "analysis-nonstrict.yaml"
    write_yaml(
        {
            "strict_validation": False,
            "emit_explanations": True,
            "fixed_point_limit": 100,
            "response_time_limit_us": 1000000.0,
        },
        config_path,
    )
    run_id = f"cli-analysis-nonstrict-{uuid.uuid4().hex}"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "analyze",
            str(invalid_reserved_bandwidth_case_path),
            "--analysis-config",
            str(config_path),
            "--run-id",
            run_id,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    result_path = repo_root / "outputs" / "runs" / run_id / "analysis" / "results" / "analysis_result.json"
    assert result_path.exists()
    result_json = read_json(result_path)
    assert result_json["summary"]["engine_status"] == "preconditions_failed"
    assert result_json["summary"]["precondition_failure_count"] == 2


def test_simulate_command_writes_required_simulation_artifacts(repo_root, sample_case_path) -> None:
    """The simulate command should emit the baseline simulation artifact bundle."""

    run_id = f"cli-simulate-test-{uuid.uuid4().hex}"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "simulate",
            str(sample_case_path),
            "--run-id",
            run_id,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    results_root = repo_root / "outputs" / "runs" / run_id / "simulation" / "results"
    traces_root = repo_root / "outputs" / "runs" / run_id / "simulation" / "traces"
    assert (results_root / "simulation_result.json").exists()
    assert (results_root / "stream_summary.csv").exists()
    assert (results_root / "hop_summary.csv").exists()
    assert (results_root / "queue_summary.csv").exists()
    assert (results_root / "run_summary.csv").exists()
    assert (traces_root / "frame_release_trace.csv").exists()
    assert (traces_root / "enqueue_trace.csv").exists()
    assert (traces_root / "transmission_trace.csv").exists()
    assert (traces_root / "forwarding_trace.csv").exists()
    assert (traces_root / "delivery_trace.csv").exists()
    assert (traces_root / "response_time_trace.csv").exists()
    assert (traces_root / "credit_trace.csv").exists()
    assert (traces_root / "scheduler_decision_trace.csv").exists()


def test_compare_command_writes_required_comparison_artifacts(repo_root, sample_case_path) -> None:
    """The compare command should align prior analysis and simulation outputs."""

    analysis_run_id = f"cli-compare-analysis-{uuid.uuid4().hex}"
    simulation_run_id = f"cli-compare-simulation-{uuid.uuid4().hex}"
    comparison_run_id = f"cli-compare-{uuid.uuid4().hex}"
    analyze_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "analyze",
            str(sample_case_path),
            "--run-id",
            analysis_run_id,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    simulate_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "simulate",
            str(sample_case_path),
            "--run-id",
            simulation_run_id,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert analyze_completed.returncode == 0
    assert simulate_completed.returncode == 0

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "compare",
            "--simulation-result",
            str(
                repo_root
                / "outputs"
                / "runs"
                / simulation_run_id
                / "simulation"
                / "results"
                / "simulation_result.json"
            ),
            "--analysis-result",
            str(
                repo_root
                / "outputs"
                / "runs"
                / analysis_run_id
                / "analysis"
                / "results"
                / "analysis_result.json"
            ),
            "--run-id",
            comparison_run_id,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    results_root = repo_root / "outputs" / "runs" / comparison_run_id / "comparison" / "results"
    assert (results_root / "comparison_result.json").exists()
    assert (results_root / "stream_comparison.csv").exists()
    assert (results_root / "aggregate_comparison.csv").exists()
    assert (results_root / "comparison_diagnostics.csv").exists()
    assert (results_root / "expected_wcrt_comparison.csv").exists()


def test_run_case_command_writes_end_to_end_artifacts(repo_root, sample_case_path) -> None:
    """The run-case command should write analysis, simulation, and comparison artifacts."""

    run_id = f"cli-run-case-{uuid.uuid4().hex}"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "run-case",
            str(sample_case_path),
            "--run-id",
            run_id,
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    run_root = repo_root / "outputs" / "runs" / run_id
    assert (run_root / "normalized" / "test-case-1.json").exists()
    assert (run_root / "analysis" / "results" / "analysis_result.json").exists()
    assert (run_root / "simulation" / "results" / "simulation_result.json").exists()
    assert (run_root / "comparison" / "results" / "comparison_result.json").exists()
    assert (run_root / "comparison" / "results" / "stream_comparison.csv").exists()


def test_batch_run_command_runs_for_external_cases_root(repo_root, sample_case_path) -> None:
    """The batch-run command should discover the sample case and execute the selected operation."""

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "drts_tsn.cli.main",
            "batch-run",
            str(sample_case_path.parent),
            "--operation",
            "run-case",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "case_count" in completed.stdout
    assert "test-case-1" in completed.stdout
