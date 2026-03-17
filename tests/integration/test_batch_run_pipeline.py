"""Integration coverage for batch execution and catalog generation."""

from __future__ import annotations

import shutil
from pathlib import Path

from drts_tsn.io.json_io import read_json
from drts_tsn.orchestration.batch_manager import run_batch
from drts_tsn.reporting.csv_catalog import BATCH_FAILURE_CATALOG_CSV, BATCH_RUN_CATALOG_CSV


_BATCH_CATALOG_FIELDS = [
    "batch_id",
    "operation",
    "case_name",
    "case_path",
    "status",
    "run_id",
    "run_dir",
    "case_id",
    "pipeline_status",
    "run_manifest_path",
    "artifact_index_path",
    "failure_diagnostic_path",
    "error_type",
    "error_message",
]


def test_batch_run_continues_after_case_failure_and_writes_catalogs(
    sample_case_path,
    invalid_case_path,
    tmp_path,
    assert_csv_contract,
) -> None:
    """Batch execution should continue across failures and write stable catalogs."""

    cases_root = tmp_path / "cases"
    cases_root.mkdir()
    shutil.copytree(invalid_case_path, cases_root / "01-invalid-case")
    shutil.copytree(sample_case_path, cases_root / "02-valid-case")

    outcomes, layout = run_batch(
        cases_root,
        operation="run-case",
        output_root=tmp_path / "outputs",
        batch_id="batch-pipeline-test",
    )

    assert len(outcomes) == 2
    status_by_name = {str(row["case_name"]): str(row["status"]) for row in outcomes}
    assert status_by_name["01-invalid-case"] == "failed"
    assert status_by_name["02-valid-case"] == "success"

    catalog_rows = assert_csv_contract(layout.catalog_dir / BATCH_RUN_CATALOG_CSV, _BATCH_CATALOG_FIELDS)
    failure_rows = assert_csv_contract(layout.failures_dir / BATCH_FAILURE_CATALOG_CSV, _BATCH_CATALOG_FIELDS)
    assert len(catalog_rows) == 2
    assert len(failure_rows) == 1
    assert (layout.catalog_dir / "batch_run_catalog.json").exists()
    assert (layout.failures_dir / "batch_failures.json").exists()

    batch_manifest = read_json(layout.metadata_dir / "batch_manifest.json")
    assert batch_manifest["batch_id"] == "batch-pipeline-test"
    assert batch_manifest["status"] == "partial_failure"
    assert batch_manifest["success_count"] == 1
    assert batch_manifest["failure_count"] == 1
    assert batch_manifest["config_snapshot"]["analysis"]["values"]["strict_validation"] is True
    assert (layout.metadata_dir / "artifact_index.json").exists()

    valid_row = next(row for row in outcomes if row["status"] == "success")
    valid_run_dir = Path(str(valid_row["run_dir"]))
    assert (valid_run_dir / "metadata" / "run_manifest.json").exists()
    assert (valid_run_dir / "comparison" / "results" / "comparison_result.json").exists()

    failed_row = next(row for row in outcomes if row["status"] == "failed")
    assert Path(str(failed_row["failure_diagnostic_path"])).exists()
