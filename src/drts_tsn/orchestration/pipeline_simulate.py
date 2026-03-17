"""Simulation pipeline that prepares cases and writes simulator artifacts."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.io.paths import outputs_root
from drts_tsn.output.artifact_index import ArtifactRecord, write_artifact_index
from drts_tsn.output.csv_writers import write_csv_artifact
from drts_tsn.output.json_writers import write_json_artifact
from drts_tsn.output.metadata_writer import write_run_metadata
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

from .run_manager import export_prepared_case, prepare_case


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
    prepared.validation_report.raise_for_errors()
    output_config = load_output_config(output_config_path)
    layout = create_run_layout(
        output_root or outputs_root(),
        run_id=run_id,
        symlink_latest=output_config.symlink_latest,
    )
    normalized_path = export_prepared_case(
        prepared, layout.normalized_dir / f"{prepared.normalized_case.metadata.case_id}.json"
    )
    result = SimulationEngine().run(
        prepared.normalized_case,
        load_simulation_config(simulation_config_path),
    )
    result.run_id = layout.run_id
    if result.tables.get("run_summary"):
        result.tables["run_summary"] = [{**row, "run_id": layout.run_id} for row in result.tables["run_summary"]]
    result.artifacts["normalized_case"] = str(normalized_path)
    result_path = layout.simulation_results_dir / "simulation_result.json"

    csv_artifacts: list[ArtifactRecord] = []
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
            csv_artifacts.append(ArtifactRecord(name=filename, path=str(path), kind="csv"))
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
        csv_artifacts.extend(
            [
                ArtifactRecord(name=SIMULATION_DETAILS_CSV, path=str(legacy_detail_path), kind="csv"),
                ArtifactRecord(name=SIMULATION_STREAMS_CSV, path=str(legacy_stream_path), kind="csv"),
            ]
        )
    if output_config.write_json and output_config.write_metadata:
        manifest_path = layout.metadata_dir / "simulation_manifest.json"
        write_run_metadata(
            {
                "pipeline": "simulate",
                "case_id": result.case_id,
                "run_id": layout.run_id,
                "schema_version": SIMULATION_SCHEMA_VERSION,
            },
            layout.metadata_dir / "run_metadata.json",
        )
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
        write_artifact_index(
            [
                ArtifactRecord(name="normalized_case", path=str(normalized_path), kind="json"),
                ArtifactRecord(name="simulation_result", path=str(result_path), kind="json"),
                ArtifactRecord(name="simulation_manifest", path=str(manifest_path), kind="json"),
                *csv_artifacts,
            ],
            layout.metadata_dir / "artifact_index.json",
        )
    if output_config.write_trace_csv and result.trace_rows:
        write_csv_artifact(result.trace_rows, layout.simulation_traces_dir / "simulation_trace.csv")
    return result, layout
