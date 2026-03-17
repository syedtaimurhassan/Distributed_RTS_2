"""Batch execution helpers for repeated multi-case runs."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from drts_tsn.adapters.external_cases.schema_checks import infer_case_filenames, missing_required_files
from drts_tsn.analysis.config import load_analysis_config
from drts_tsn.common.ids import compose_identifier
from drts_tsn.io.manifest import load_manifest
from drts_tsn.io.paths import outputs_root
from drts_tsn.output.artifact_index import ArtifactRecord, write_artifact_index
from drts_tsn.output.csv_writers import write_csv_artifact
from drts_tsn.output.json_writers import write_json_artifact
from drts_tsn.output.metadata_writer import build_batch_manifest, snapshot_config
from drts_tsn.output.run_layout import BatchLayout, create_batch_layout
from drts_tsn.output.writers import load_output_config
from drts_tsn.reporting.csv_catalog import BATCH_FAILURE_CATALOG_CSV, BATCH_RUN_CATALOG_CSV
from drts_tsn.simulation.config import load_simulation_config

from .pipeline_analyze import execute as analyze_case
from .pipeline_run_case import execute as run_case
from .pipeline_simulate import execute as simulate_case


def _discover_case_directories(root: Path) -> list[Path]:
    """Discover directories that look like external case roots."""

    discovered: list[Path] = []
    for directory in sorted([root, *root.rglob("*")]):
        if not directory.is_dir():
            continue
        manifest = load_manifest(directory)
        filenames = infer_case_filenames(directory, manifest=manifest)
        if not missing_required_files(directory, filenames):
            discovered.append(directory)
    return discovered


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


def _build_config_snapshot(
    *,
    operation: str,
    simulation_config_path: Path | None,
    analysis_config_path: Path | None,
    output_config_path: Path | None,
) -> dict[str, Any]:
    """Return the batch-level config snapshot for the selected operation."""

    snapshot: dict[str, Any] = {
        "output": snapshot_config(
            config=load_output_config(output_config_path),
            source_path=output_config_path,
        ),
    }
    if operation in {"analyze", "run-case"}:
        snapshot["analysis"] = snapshot_config(
            config=load_analysis_config(analysis_config_path),
            source_path=analysis_config_path,
        )
    if operation in {"simulate", "run-case"}:
        snapshot["simulation"] = snapshot_config(
            config=load_simulation_config(simulation_config_path),
            source_path=simulation_config_path,
        )
    return snapshot


def _record_success(
    *,
    batch_id: str,
    operation: str,
    case_dir: Path,
    result: object,
    layout: object,
) -> dict[str, object]:
    """Return a catalog row for a successful case run."""

    if operation == "run-case":
        result_map = dict(result)
        case_id = str(result_map["analysis_result"].case_id)
        pipeline_status = str(result_map["comparison_result"].summary.get("engine_status", "ok"))
    else:
        case_id = str(result.case_id)
        pipeline_status = str(result.summary.get("engine_status", "ok"))
    layout_run_dir = getattr(layout, "run_dir")
    metadata_dir = getattr(layout, "metadata_dir")
    run_manifest_path = metadata_dir / "run_manifest.json"
    artifact_index_path = metadata_dir / "artifact_index.json"
    return {
        "batch_id": batch_id,
        "operation": operation,
        "case_name": case_dir.name,
        "case_path": str(case_dir),
        "status": "success",
        "run_id": getattr(layout, "run_id"),
        "run_dir": str(layout_run_dir),
        "case_id": case_id,
        "pipeline_status": pipeline_status,
        "run_manifest_path": str(run_manifest_path) if run_manifest_path.exists() else "",
        "artifact_index_path": str(artifact_index_path) if artifact_index_path.exists() else "",
        "failure_diagnostic_path": "",
        "error_type": "",
        "error_message": "",
    }


def _record_failure(
    *,
    batch_id: str,
    operation: str,
    case_dir: Path,
    run_id: str,
    run_dir: Path,
    failures_dir: Path,
    exc: Exception,
    index: int,
) -> dict[str, object]:
    """Return a catalog row for a failed case run and write a failure diagnostic."""

    diagnostic_path = failures_dir / f"{index:03d}-{compose_identifier(case_dir.name)}.json"
    write_json_artifact(
        {
            "batch_id": batch_id,
            "operation": operation,
            "case_name": case_dir.name,
            "case_path": str(case_dir),
            "run_id": run_id,
            "run_dir": str(run_dir),
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        },
        diagnostic_path,
    )
    return {
        "batch_id": batch_id,
        "operation": operation,
        "case_name": case_dir.name,
        "case_path": str(case_dir),
        "status": "failed",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "case_id": "",
        "pipeline_status": "failed",
        "run_manifest_path": "",
        "artifact_index_path": "",
        "failure_diagnostic_path": str(diagnostic_path),
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
    }


def _build_batch_command(
    *,
    cases_root: Path,
    operation: str,
    batch_id: str,
    output_root: Path,
    simulation_config_path: Path | None,
    analysis_config_path: Path | None,
    output_config_path: Path | None,
) -> str:
    """Return the batch command string recorded in batch metadata."""

    command_parts = [
        "batch-run",
        str(cases_root),
        "--operation",
        operation,
        "--batch-id",
        batch_id,
        "--output-root",
        str(output_root),
    ]
    if analysis_config_path is not None:
        command_parts.extend(["--analysis-config", str(analysis_config_path)])
    if simulation_config_path is not None:
        command_parts.extend(["--simulation-config", str(simulation_config_path)])
    if output_config_path is not None:
        command_parts.extend(["--output-config", str(output_config_path)])
    return " ".join(command_parts)


def _execute_pipeline(
    *,
    operation: str,
    case_dir: Path,
    run_id: str,
    output_root: Path,
    simulation_config_path: Path | None,
    analysis_config_path: Path | None,
    output_config_path: Path | None,
) -> tuple[object, object]:
    """Execute the selected pipeline with its supported keyword arguments."""

    if operation == "simulate":
        return simulate_case(
            case_dir,
            simulation_config_path=simulation_config_path,
            output_config_path=output_config_path,
            output_root=output_root,
            run_id=run_id,
        )
    if operation == "analyze":
        return analyze_case(
            case_dir,
            analysis_config_path=analysis_config_path,
            output_config_path=output_config_path,
            output_root=output_root,
            run_id=run_id,
        )
    return run_case(
        case_dir,
        simulation_config_path=simulation_config_path,
        analysis_config_path=analysis_config_path,
        output_config_path=output_config_path,
        output_root=output_root,
        run_id=run_id,
    )


def run_batch(
    cases_root: Path,
    *,
    operation: str = "run-case",
    simulation_config_path: Path | None = None,
    analysis_config_path: Path | None = None,
    output_config_path: Path | None = None,
    output_root: Path | None = None,
    batch_id: str | None = None,
) -> tuple[list[dict[str, object]], BatchLayout]:
    """Run a selected pipeline over discovered case directories and write a batch catalog."""

    resolved_cases_root = Path(cases_root).resolve()
    output_config = load_output_config(output_config_path)
    resolved_output_root = output_root or outputs_root()
    batch_layout = create_batch_layout(
        resolved_output_root,
        batch_id=batch_id,
        symlink_latest=output_config.symlink_latest,
    )
    outcomes: list[dict[str, object]] = []
    discovered_cases = _discover_case_directories(resolved_cases_root)
    for index, case_dir in enumerate(discovered_cases, start=1):
        case_run_id = compose_identifier(batch_layout.batch_id, f"{index:03d}", case_dir.name)
        predicted_run_dir = resolved_output_root / "runs" / case_run_id
        try:
            result, layout = _execute_pipeline(
                operation=operation,
                case_dir=case_dir,
                run_id=case_run_id,
                output_root=resolved_output_root,
                simulation_config_path=simulation_config_path,
                analysis_config_path=analysis_config_path,
                output_config_path=output_config_path,
            )
            outcomes.append(
                _record_success(
                    batch_id=batch_layout.batch_id,
                    operation=operation,
                    case_dir=case_dir,
                    result=result,
                    layout=layout,
                )
            )
        except Exception as exc:  # noqa: BLE001
            outcomes.append(
                _record_failure(
                    batch_id=batch_layout.batch_id,
                    operation=operation,
                    case_dir=case_dir,
                    run_id=case_run_id,
                    run_dir=predicted_run_dir,
                    failures_dir=batch_layout.failures_dir,
                    exc=exc,
                    index=index,
                )
            )

    success_count = sum(1 for outcome in outcomes if outcome["status"] == "success")
    failure_rows = [outcome for outcome in outcomes if outcome["status"] != "success"]
    failure_count = len(failure_rows)
    command_invoked = _build_batch_command(
        cases_root=resolved_cases_root,
        operation=operation,
        batch_id=batch_layout.batch_id,
        output_root=resolved_output_root,
        simulation_config_path=simulation_config_path,
        analysis_config_path=analysis_config_path,
        output_config_path=output_config_path,
    )

    catalog_csv_path = write_csv_artifact(
        outcomes,
        batch_layout.catalog_dir / BATCH_RUN_CATALOG_CSV,
        fieldnames=_BATCH_CATALOG_FIELDS,
    )
    catalog_json_path = write_json_artifact(outcomes, batch_layout.catalog_dir / "batch_run_catalog.json")
    failures_csv_path = write_csv_artifact(
        failure_rows,
        batch_layout.failures_dir / BATCH_FAILURE_CATALOG_CSV,
        fieldnames=_BATCH_CATALOG_FIELDS,
    )
    failures_json_path = write_json_artifact(failure_rows, batch_layout.failures_dir / "batch_failures.json")

    artifact_records = [
        ArtifactRecord(name=BATCH_RUN_CATALOG_CSV, path=str(catalog_csv_path), kind="csv"),
        ArtifactRecord(name="batch_run_catalog.json", path=str(catalog_json_path), kind="json"),
        ArtifactRecord(name=BATCH_FAILURE_CATALOG_CSV, path=str(failures_csv_path), kind="csv"),
        ArtifactRecord(name="batch_failures.json", path=str(failures_json_path), kind="json"),
        *[
            ArtifactRecord(
                name=Path(str(row["failure_diagnostic_path"])).name,
                path=str(row["failure_diagnostic_path"]),
                kind="json",
            )
            for row in failure_rows
            if row["failure_diagnostic_path"]
        ],
    ]
    batch_manifest_path = write_json_artifact(
        build_batch_manifest(
            batch_id=batch_layout.batch_id,
            batch_dir=batch_layout.batch_dir,
            cases_root=resolved_cases_root,
            operation=operation,
            status="success" if failure_count == 0 else "partial_failure",
            success_count=success_count,
            failure_count=failure_count,
            command_invoked=command_invoked,
            config_snapshot=_build_config_snapshot(
                operation=operation,
                simulation_config_path=simulation_config_path,
                analysis_config_path=analysis_config_path,
                output_config_path=output_config_path,
            ),
            artifact_records=artifact_records,
            outcomes=outcomes,
            extra={"discovered_case_count": len(discovered_cases)},
        ),
        batch_layout.metadata_dir / "batch_manifest.json",
    )
    artifact_records.append(ArtifactRecord(name="batch_manifest", path=str(batch_manifest_path), kind="json"))
    artifact_index_path = write_artifact_index(artifact_records, batch_layout.metadata_dir / "artifact_index.json")
    artifact_records.append(ArtifactRecord(name="artifact_index", path=str(artifact_index_path), kind="json"))
    write_json_artifact(
        build_batch_manifest(
            batch_id=batch_layout.batch_id,
            batch_dir=batch_layout.batch_dir,
            cases_root=resolved_cases_root,
            operation=operation,
            status="success" if failure_count == 0 else "partial_failure",
            success_count=success_count,
            failure_count=failure_count,
            command_invoked=command_invoked,
            config_snapshot=_build_config_snapshot(
                operation=operation,
                simulation_config_path=simulation_config_path,
                analysis_config_path=analysis_config_path,
                output_config_path=output_config_path,
            ),
            artifact_records=artifact_records,
            outcomes=outcomes,
            extra={"discovered_case_count": len(discovered_cases)},
        ),
        batch_layout.metadata_dir / "batch_manifest.json",
    )
    return outcomes, batch_layout
