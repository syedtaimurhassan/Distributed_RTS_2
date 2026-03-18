"""Submission-readiness checks for documented baseline workflows."""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path


def _run_make(repo_root: Path, command: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run one make.sh command and capture output for assertions."""

    return subprocess.run(
        ["./make.sh", command],
        cwd=repo_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_make_sh_submission_sequence_runs_for_provided_case(repo_root, tmp_path: Path) -> None:
    """Documented make.sh readiness->normalize->run-case path should remain executable."""

    case_path = repo_root / "cases" / "external" / "test-case-1"
    run_id = f"submission-ready-{uuid.uuid4().hex}"
    normalize_output = tmp_path / "normalized-assignment-case"
    base_env = os.environ.copy()
    base_env.update(
        {
            "CASE_DIR": str(case_path),
            "READINESS_STAGE": "all",
            "NORMALIZED_OUTPUT_DIR": str(normalize_output),
            "RUN_ID": run_id,
        }
    )

    readiness = _run_make(repo_root, "readiness", base_env)
    normalize = _run_make(repo_root, "normalize", base_env)
    run_case = _run_make(repo_root, "run-case", base_env)

    assert readiness.returncode == 0, readiness.stderr or readiness.stdout
    assert normalize.returncode == 0, normalize.stderr or normalize.stdout
    assert run_case.returncode == 0, run_case.stderr or run_case.stdout

    assert (normalize_output / "normalized_case.json").exists()
    assert (normalize_output / "artifact_index.json").exists()

    run_root = repo_root / "outputs" / "runs" / run_id
    assert (run_root / "analysis" / "results" / "analysis_result.json").exists()
    assert (run_root / "simulation" / "results" / "simulation_result.json").exists()
    assert (run_root / "comparison" / "results" / "comparison_result.json").exists()
    assert (run_root / "comparison" / "results" / "expected_wcrt_comparison.csv").exists()
    assert (run_root / "simulation" / "traces" / "credit_trace.csv").exists()
    assert (run_root / "analysis" / "traces" / "per_link_formula_trace.csv").exists()
    assert (run_root / "metadata" / "run_manifest.json").exists()
    assert (run_root / "metadata" / "artifact_index.json").exists()


def test_readme_includes_submission_ready_make_workflow(repo_root) -> None:
    """README should keep the submission-ready make workflow commands explicit."""

    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "## Submission-Ready Baseline Sequence" in readme_text
    assert 'READINESS_STAGE=all ./make.sh readiness' in readme_text
    assert 'NORMALIZED_OUTPUT_DIR="$PWD/cases/normalized/test-case-1" ./make.sh normalize' in readme_text
    assert 'RUN_ID=submission-test-case-1 ./make.sh run-case' in readme_text
