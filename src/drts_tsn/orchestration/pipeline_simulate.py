"""Simulation pipeline that prepares cases and writes simulator artifacts."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.io.paths import outputs_root
from drts_tsn.output.artifact_index import ArtifactRecord, write_artifact_index
from drts_tsn.output.csv_writers import write_csv_artifact
from drts_tsn.output.json_writers import write_json_artifact
from drts_tsn.output.metadata_writer import (
    build_run_manifest,
    snapshot_config,
    write_run_manifest_bundle,
)
from drts_tsn.output.run_layout import RunLayout, create_run_layout
from drts_tsn.output.writers import load_output_config
from drts_tsn.reporting.csv_catalog import (
    SIMULATION_CREDIT_TRACE_CSV,
    SIMULATION_DELIVERY_TRACE_CSV,
    SIMULATION_DETAILS_CSV,
    SIMULATION_ENQUEUE_TRACE_CSV,
    SIMULATION_FORWARDING_TRACE_CSV,
    SIMULATION_FRAME_RELEASE_TRACE_CSV,
    SIMULATION_HOP_SUMMARY_CSV,
    SIMULATION_QUEUE_SUMMARY_CSV,
    SIMULATION_RESPONSE_TIME_TRACE_CSV,
    SIMULATION_RUN_SUMMARY_CSV,
    SIMULATION_SCHEDULER_DECISION_TRACE_CSV,
    SIMULATION_STREAMS_CSV,
    SIMULATION_STREAM_SUMMARY_CSV,
    SIMULATION_TRANSMISSION_TRACE_CSV,
)
from drts_tsn.reporting.stream_summaries import simulation_stream_rows
from drts_tsn.simulation.config import load_simulation_config
from drts_tsn.simulation.engine import SimulationEngine
from drts_tsn.simulation.outputs.simulation_result_builder import (
    SIMULATION_SCHEMA_VERSION,
    SIMULATION_TABLE_FIELDS,
)

from .run_manager import assert_case_readiness, export_prepared_case, prepare_case


def _build_simulation_manifest(
    *,
    case_id: str,
    run_id: str,
    normalized_path: Path,
    result_path: Path,
    csv_artifacts: list[dict[str, object]],
) -> dict[str, object]:
    """Return stable metadata that describes generated simulation artifacts."""

    return {
        "schema_version": SIMULATION_SCHEMA_VERSION,
        "pipeline": "simulate",
        "case_id": case_id,
        "run_id": run_id,
        "normalized_case": str(normalized_path),
        "simulation_result": str(result_path),
        "csv_artifacts": csv_artifacts,
    }


def execute(
    case_path: str | Path,
    *,
    simulation_config_path: Path | None = None,
    output_config_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> tuple[object, RunLayout]:
    """Run the baseline simulation pipeline for one case."""

    prepared = prepare_case(case_path)
    assert_case_readiness(prepared, stage="simulation")
    output_config = load_output_config(output_config_path)
    layout = create_run_layout(
        output_root or outputs_root(),
        run_id=run_id,
        symlink_latest=output_config.symlink_latest,
    )
    normalized_path = export_prepared_case(
        prepared, layout.normalized_dir / f"{prepared.normalized_case.metadata.case_id}.json"
    )
    simulation_config = load_simulation_config(simulation_config_path)
    command_parts = ["simulate", str(prepared.case_directory)]
    if simulation_config_path is not None:
        command_parts.extend(["--simulation-config", str(simulation_config_path)])
    if output_config_path is not None:
        command_parts.extend(["--output-config", str(output_config_path)])
    if run_id is not None:
        command_parts.extend(["--run-id", layout.run_id])
    command_invoked = " ".join(command_parts)
    result = SimulationEngine().run(
        prepared.normalized_case,
        simulation_config,
    )
    result.run_id = layout.run_id
    if result.tables.get("run_summary"):
        result.tables["run_summary"] = [{**row, "run_id": layout.run_id} for row in result.tables["run_summary"]]
    result.artifacts["normalized_case"] = str(normalized_path)
    result_path = layout.simulation_results_dir / "simulation_result.json"

    artifact_records: list[ArtifactRecord] = [
        ArtifactRecord(name="normalized_case", path=str(normalized_path), kind="json"),
        ArtifactRecord(name="simulation_result", path=str(result_path), kind="json"),
    ]
    csv_manifest_entries: list[dict[str, object]] = []
    if output_config.write_json:
        write_json_artifact(result, result_path)
    if output_config.write_csv:
        result_tables = (
            ("stream_summary", SIMULATION_STREAM_SUMMARY_CSV, layout.simulation_results_dir),
            ("hop_summary", SIMULATION_HOP_SUMMARY_CSV, layout.simulation_results_dir),
            ("queue_summary", SIMULATION_QUEUE_SUMMARY_CSV, layout.simulation_results_dir),
            ("run_summary", SIMULATION_RUN_SUMMARY_CSV, layout.simulation_results_dir),
            ("frame_release_trace", SIMULATION_FRAME_RELEASE_TRACE_CSV, layout.simulation_traces_dir),
            ("enqueue_trace", SIMULATION_ENQUEUE_TRACE_CSV, layout.simulation_traces_dir),
            ("transmission_trace", SIMULATION_TRANSMISSION_TRACE_CSV, layout.simulation_traces_dir),
            ("forwarding_trace", SIMULATION_FORWARDING_TRACE_CSV, layout.simulation_traces_dir),
            ("delivery_trace", SIMULATION_DELIVERY_TRACE_CSV, layout.simulation_traces_dir),
            ("response_time_trace", SIMULATION_RESPONSE_TIME_TRACE_CSV, layout.simulation_traces_dir),
            ("credit_trace", SIMULATION_CREDIT_TRACE_CSV, layout.simulation_traces_dir),
            ("scheduler_decision_trace", SIMULATION_SCHEDULER_DECISION_TRACE_CSV, layout.simulation_traces_dir),
        )
        for table_name, filename, directory in result_tables:
            path = write_csv_artifact(
                result.tables.get(table_name, []),
                directory / filename,
                fieldnames=SIMULATION_TABLE_FIELDS.get(table_name),
            )
            artifact_records.append(ArtifactRecord(name=filename, path=str(path), kind="csv"))
            csv_manifest_entries.append(
                {
                    "table_name": table_name,
                    "name": filename,
                    "kind": "csv",
                    "path": str(path),
                    "required_columns": SIMULATION_TABLE_FIELDS.get(table_name, []),
                }
            )

        legacy_detail_path = write_csv_artifact(
            result.detail_rows,
            layout.simulation_results_dir / SIMULATION_DETAILS_CSV,
        )
        legacy_stream_path = write_csv_artifact(
            simulation_stream_rows(result),
            layout.simulation_results_dir / SIMULATION_STREAMS_CSV,
        )
        artifact_records.extend(
            [
                ArtifactRecord(name=SIMULATION_DETAILS_CSV, path=str(legacy_detail_path), kind="csv"),
                ArtifactRecord(name=SIMULATION_STREAMS_CSV, path=str(legacy_stream_path), kind="csv"),
            ]
        )
    if output_config.write_json and output_config.write_metadata:
        manifest_path = layout.metadata_dir / "simulation_manifest.json"
        write_json_artifact(
            _build_simulation_manifest(
                case_id=result.case_id,
                run_id=layout.run_id,
                normalized_path=normalized_path,
                result_path=result_path,
                csv_artifacts=csv_manifest_entries,
            ),
            manifest_path,
        )
        artifact_records.extend(
            [
                ArtifactRecord(name="simulation_manifest", path=str(manifest_path), kind="json"),
            ]
        )
        run_manifest_paths = write_run_manifest_bundle(
            build_run_manifest(
                pipeline="simulate",
                run_id=layout.run_id,
                run_dir=layout.run_dir,
                status="success",
                pipeline_status=str(result.summary.get("engine_status")),
                case_id=result.case_id,
                case_name=prepared.normalized_case.metadata.name,
                case_path=prepared.case_directory,
                command_invoked=command_invoked,
                config_snapshot={
                    "simulation": snapshot_config(
                        config=simulation_config,
                        source_path=simulation_config_path,
                    ),
                    "output": snapshot_config(
                        config=output_config,
                        source_path=output_config_path,
                    ),
                },
                artifact_records=artifact_records,
                extra={"simulation_schema_version": SIMULATION_SCHEMA_VERSION},
            ),
            metadata_dir=layout.metadata_dir,
        )
        artifact_records.extend(
            [
                ArtifactRecord(name="run_manifest", path=str(run_manifest_paths["run_manifest"]), kind="json"),
                ArtifactRecord(name="run_metadata", path=str(run_manifest_paths["run_metadata"]), kind="json"),
            ]
        )
        artifact_index_path = write_artifact_index(artifact_records, layout.metadata_dir / "artifact_index.json")
        artifact_records.append(ArtifactRecord(name="artifact_index", path=str(artifact_index_path), kind="json"))
        write_run_manifest_bundle(
            build_run_manifest(
                pipeline="simulate",
                run_id=layout.run_id,
                run_dir=layout.run_dir,
                status="success",
                pipeline_status=str(result.summary.get("engine_status")),
                case_id=result.case_id,
                case_name=prepared.normalized_case.metadata.name,
                case_path=prepared.case_directory,
                command_invoked=command_invoked,
                config_snapshot={
                    "simulation": snapshot_config(
                        config=simulation_config,
                        source_path=simulation_config_path,
                    ),
                    "output": snapshot_config(
                        config=output_config,
                        source_path=output_config_path,
                    ),
                },
                artifact_records=artifact_records,
                extra={"simulation_schema_version": SIMULATION_SCHEMA_VERSION},
            ),
            metadata_dir=layout.metadata_dir,
        )
    if output_config.write_trace_csv and result.trace_rows:
        write_csv_artifact(result.trace_rows, layout.simulation_traces_dir / "simulation_trace.csv")
    return result, layout
