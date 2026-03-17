"""Combined end-to-end pipeline for one case."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.analysis.config import load_analysis_config
from drts_tsn.analysis.engine import AnalysisEngine
from drts_tsn.analysis.outputs.analysis_result_builder import ANALYSIS_TABLE_FIELDS
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
    ANALYSIS_CREDIT_RECOVERY_TRACE_CSV,
    ANALYSIS_END_TO_END_ACCUMULATION_TRACE_CSV,
    ANALYSIS_HIGHER_PRIORITY_TRACE_CSV,
    ANALYSIS_LINK_INTERFERENCE_TRACE_CSV,
    ANALYSIS_LOWER_PRIORITY_TRACE_CSV,
    ANALYSIS_PER_LINK_FORMULA_TRACE_CSV,
    ANALYSIS_PER_LINK_WCRT_SUMMARY_CSV,
    ANALYSIS_RUN_SUMMARY_CSV,
    ANALYSIS_SAME_PRIORITY_TRACE_CSV,
    ANALYSIS_STREAM_WCRT_SUMMARY_CSV,
    COMPARISON_AGGREGATE_COMPARISON_CSV,
    COMPARISON_DIAGNOSTICS_CSV,
    COMPARISON_EXPECTED_WCRT_COMPARISON_CSV,
    COMPARISON_STREAM_COMPARISON_CSV,
    SIMULATION_CREDIT_TRACE_CSV,
    SIMULATION_DELIVERY_TRACE_CSV,
    SIMULATION_ENQUEUE_TRACE_CSV,
    SIMULATION_FORWARDING_TRACE_CSV,
    SIMULATION_FRAME_RELEASE_TRACE_CSV,
    SIMULATION_HOP_SUMMARY_CSV,
    SIMULATION_QUEUE_SUMMARY_CSV,
    SIMULATION_RESPONSE_TIME_TRACE_CSV,
    SIMULATION_RUN_SUMMARY_CSV,
    SIMULATION_SCHEDULER_DECISION_TRACE_CSV,
    SIMULATION_STREAM_SUMMARY_CSV,
    SIMULATION_TRANSMISSION_TRACE_CSV,
)
from drts_tsn.simulation.config import load_simulation_config
from drts_tsn.simulation.engine import SimulationEngine
from drts_tsn.simulation.outputs.simulation_result_builder import SIMULATION_TABLE_FIELDS

from .pipeline_compare import execute as execute_compare
from .run_manager import export_prepared_case, prepare_case


def _write_analysis_bundle(
    *,
    result: object,
    layout: RunLayout,
    normalized_path: Path,
    output_config_path: Path | None,
) -> tuple[Path, list[ArtifactRecord]]:
    """Write stable analysis artifacts into the provided run layout."""

    output_config = load_output_config(output_config_path)
    result.run_id = layout.run_id
    result.artifacts["normalized_case"] = str(normalized_path)
    result_path = layout.analysis_results_dir / "analysis_result.json"
    artifact_records: list[ArtifactRecord] = [
        ArtifactRecord(name="analysis_result", path=str(result_path), kind="json"),
    ]
    if result.tables.get("run_summary"):
        result.tables["run_summary"] = [{**row, "run_id": layout.run_id} for row in result.tables["run_summary"]]
    if output_config.write_json:
        write_json_artifact(result, result_path)
    if output_config.write_csv:
        for table_name, filename, directory in (
            ("stream_wcrt_summary", ANALYSIS_STREAM_WCRT_SUMMARY_CSV, layout.analysis_results_dir),
            ("per_link_wcrt_summary", ANALYSIS_PER_LINK_WCRT_SUMMARY_CSV, layout.analysis_results_dir),
            ("run_summary", ANALYSIS_RUN_SUMMARY_CSV, layout.analysis_results_dir),
            ("link_interference_trace", ANALYSIS_LINK_INTERFERENCE_TRACE_CSV, layout.analysis_traces_dir),
            ("same_priority_trace", ANALYSIS_SAME_PRIORITY_TRACE_CSV, layout.analysis_traces_dir),
            ("credit_recovery_trace", ANALYSIS_CREDIT_RECOVERY_TRACE_CSV, layout.analysis_traces_dir),
            ("lower_priority_trace", ANALYSIS_LOWER_PRIORITY_TRACE_CSV, layout.analysis_traces_dir),
            ("higher_priority_trace", ANALYSIS_HIGHER_PRIORITY_TRACE_CSV, layout.analysis_traces_dir),
            ("per_link_formula_trace", ANALYSIS_PER_LINK_FORMULA_TRACE_CSV, layout.analysis_traces_dir),
            ("end_to_end_accumulation_trace", ANALYSIS_END_TO_END_ACCUMULATION_TRACE_CSV, layout.analysis_traces_dir),
        ):
            path = write_csv_artifact(
                result.tables.get(table_name, []),
                directory / filename,
                fieldnames=ANALYSIS_TABLE_FIELDS.get(table_name),
            )
            artifact_records.append(ArtifactRecord(name=filename, path=str(path), kind="csv"))
    return result_path, artifact_records


def _write_simulation_bundle(
    *,
    result: object,
    layout: RunLayout,
    normalized_path: Path,
    output_config_path: Path | None,
) -> tuple[Path, list[ArtifactRecord]]:
    """Write stable simulation artifacts into the provided run layout."""

    output_config = load_output_config(output_config_path)
    result.run_id = layout.run_id
    result.artifacts["normalized_case"] = str(normalized_path)
    result_path = layout.simulation_results_dir / "simulation_result.json"
    artifact_records: list[ArtifactRecord] = [
        ArtifactRecord(name="simulation_result", path=str(result_path), kind="json"),
    ]
    if result.tables.get("run_summary"):
        result.tables["run_summary"] = [{**row, "run_id": layout.run_id} for row in result.tables["run_summary"]]
    if output_config.write_json:
        write_json_artifact(result, result_path)
    if output_config.write_csv:
        for table_name, filename, directory in (
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
            (
                "scheduler_decision_trace",
                SIMULATION_SCHEDULER_DECISION_TRACE_CSV,
                layout.simulation_traces_dir,
            ),
        ):
            path = write_csv_artifact(
                result.tables.get(table_name, []),
                directory / filename,
                fieldnames=SIMULATION_TABLE_FIELDS.get(table_name),
            )
            artifact_records.append(ArtifactRecord(name=filename, path=str(path), kind="csv"))
    return result_path, artifact_records


def execute(
    case_path: str | Path,
    *,
    simulation_config_path: Path | None = None,
    analysis_config_path: Path | None = None,
    output_config_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> tuple[dict[str, object], RunLayout]:
    """Run preparation, analysis, simulation, and comparison in one run directory."""

    analysis_config = load_analysis_config(analysis_config_path)
    simulation_config = load_simulation_config(simulation_config_path)
    prepared = prepare_case(case_path, include_analysis_checks=analysis_config.strict_validation)
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
    command_parts = ["run-case", str(prepared.case_directory)]
    if simulation_config_path is not None:
        command_parts.extend(["--simulation-config", str(simulation_config_path)])
    if analysis_config_path is not None:
        command_parts.extend(["--analysis-config", str(analysis_config_path)])
    if output_config_path is not None:
        command_parts.extend(["--output-config", str(output_config_path)])
    if run_id is not None:
        command_parts.extend(["--run-id", layout.run_id])
    command_invoked = " ".join(command_parts)

    analysis_result = AnalysisEngine().run(prepared.normalized_case, analysis_config)
    simulation_result = SimulationEngine().run(prepared.normalized_case, simulation_config)

    analysis_path, analysis_artifacts = _write_analysis_bundle(
        result=analysis_result,
        layout=layout,
        normalized_path=normalized_path,
        output_config_path=output_config_path,
    )
    simulation_path, simulation_artifacts = _write_simulation_bundle(
        result=simulation_result,
        layout=layout,
        normalized_path=normalized_path,
        output_config_path=output_config_path,
    )
    comparison_result, _ = execute_compare(
        simulation_result_path=simulation_path,
        analysis_result_path=analysis_path,
        output_config_path=output_config_path,
        output_root=layout.output_root,
        run_id=layout.run_id,
        write_metadata=False,
    )

    if output_config.write_json and output_config.write_metadata:
        comparison_artifacts: list[ArtifactRecord] = []
        if output_config.write_json:
            comparison_artifacts.append(
                ArtifactRecord(
                    name="comparison_result",
                    path=str(layout.comparison_results_dir / "comparison_result.json"),
                    kind="json",
                )
            )
        if output_config.write_csv:
            comparison_artifacts.extend(
                [
                    ArtifactRecord(
                        name=COMPARISON_STREAM_COMPARISON_CSV,
                        path=str(layout.comparison_results_dir / COMPARISON_STREAM_COMPARISON_CSV),
                        kind="csv",
                    ),
                    ArtifactRecord(
                        name=COMPARISON_AGGREGATE_COMPARISON_CSV,
                        path=str(layout.comparison_results_dir / COMPARISON_AGGREGATE_COMPARISON_CSV),
                        kind="csv",
                    ),
                    ArtifactRecord(
                        name=COMPARISON_DIAGNOSTICS_CSV,
                        path=str(layout.comparison_results_dir / COMPARISON_DIAGNOSTICS_CSV),
                        kind="csv",
                    ),
                ]
            )
        expected_wcrt_path = layout.comparison_results_dir / COMPARISON_EXPECTED_WCRT_COMPARISON_CSV
        if output_config.write_csv and expected_wcrt_path.exists():
            comparison_artifacts.append(
                ArtifactRecord(
                    name=COMPARISON_EXPECTED_WCRT_COMPARISON_CSV,
                    path=str(expected_wcrt_path),
                    kind="csv",
                )
            )
        artifact_records = [
            ArtifactRecord(name="normalized_case", path=str(normalized_path), kind="json"),
            *analysis_artifacts,
            *simulation_artifacts,
            *comparison_artifacts,
        ]
        run_manifest_paths = write_run_manifest_bundle(
            build_run_manifest(
                pipeline="run-case",
                run_id=layout.run_id,
                run_dir=layout.run_dir,
                status="success",
                pipeline_status="success",
                case_id=prepared.normalized_case.metadata.case_id,
                case_name=prepared.normalized_case.metadata.name,
                case_path=prepared.case_directory,
                command_invoked=command_invoked,
                config_snapshot={
                    "analysis": snapshot_config(
                        config=analysis_config,
                        source_path=analysis_config_path,
                    ),
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
                extra={
                    "component_statuses": {
                        "analysis": analysis_result.summary.get("engine_status"),
                        "simulation": simulation_result.summary.get("engine_status"),
                        "comparison": comparison_result.summary.get("engine_status"),
                    }
                },
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
                pipeline="run-case",
                run_id=layout.run_id,
                run_dir=layout.run_dir,
                status="success",
                pipeline_status="success",
                case_id=prepared.normalized_case.metadata.case_id,
                case_name=prepared.normalized_case.metadata.name,
                case_path=prepared.case_directory,
                command_invoked=command_invoked,
                config_snapshot={
                    "analysis": snapshot_config(
                        config=analysis_config,
                        source_path=analysis_config_path,
                    ),
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
                extra={
                    "component_statuses": {
                        "analysis": analysis_result.summary.get("engine_status"),
                        "simulation": simulation_result.summary.get("engine_status"),
                        "comparison": comparison_result.summary.get("engine_status"),
                    }
                },
            ),
            metadata_dir=layout.metadata_dir,
        )
    return {
        "simulation_result": simulation_result,
        "analysis_result": analysis_result,
        "comparison_result": comparison_result,
    }, layout
