"""Analysis pipeline that prepares normalized cases and writes analysis artifacts."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.analysis.config import load_analysis_config
from drts_tsn.analysis.engine import AnalysisEngine
from drts_tsn.analysis.outputs.analysis_result_builder import (
    ANALYSIS_SCHEMA_VERSION,
    ANALYSIS_TABLE_FIELDS,
)
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
)

from .run_manager import assert_case_readiness, export_prepared_case, prepare_case


def _build_analysis_manifest(
    *,
    case_id: str,
    run_id: str,
    normalized_path: Path,
    result_path: Path,
    csv_artifacts: list[dict[str, object]],
) -> dict[str, object]:
    """Return stable metadata that describes generated analysis artifacts."""
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "pipeline": "analyze",
        "case_id": case_id,
        "run_id": run_id,
        "normalized_case": str(normalized_path),
        "analysis_result": str(result_path),
        "csv_artifacts": csv_artifacts,
    }


def execute(
    case_path: str | Path,
    *,
    analysis_config_path: Path | None = None,
    output_config_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> tuple[object, RunLayout]:
    """Run the baseline analytical pipeline for one case."""

    analysis_config = load_analysis_config(analysis_config_path)
    prepared = prepare_case(case_path, include_analysis_checks=analysis_config.strict_validation)
    assert_case_readiness(
        prepared,
        stage="analysis" if analysis_config.strict_validation else "baseline",
    )
    output_config = load_output_config(output_config_path)
    layout = create_run_layout(
        output_root or outputs_root(),
        run_id=run_id,
        symlink_latest=output_config.symlink_latest,
    )
    normalized_path = export_prepared_case(
        prepared, layout.normalized_dir / f"{prepared.normalized_case.metadata.case_id}.json"
    )
    command_parts = ["analyze", str(prepared.case_directory)]
    if analysis_config_path is not None:
        command_parts.extend(["--analysis-config", str(analysis_config_path)])
    if output_config_path is not None:
        command_parts.extend(["--output-config", str(output_config_path)])
    if run_id is not None:
        command_parts.extend(["--run-id", layout.run_id])
    command_invoked = " ".join(command_parts)
    result = AnalysisEngine().run(prepared.normalized_case, analysis_config)
    result.run_id = layout.run_id
    if result.tables.get("run_summary"):
        result.tables["run_summary"] = [
            {
                **row,
                "run_id": layout.run_id,
            }
            for row in result.tables["run_summary"]
        ]
    result.artifacts["normalized_case"] = str(normalized_path)
    result_path = layout.analysis_results_dir / "analysis_result.json"

    artifact_records: list[ArtifactRecord] = [
        ArtifactRecord(name="normalized_case", path=str(normalized_path), kind="json"),
        ArtifactRecord(name="analysis_result", path=str(result_path), kind="json"),
    ]
    csv_manifest_entries: list[dict[str, object]] = []
    if output_config.write_json:
        write_json_artifact(result, result_path)
    if output_config.write_csv:
        result_tables = (
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
        )
        for table_name, filename, directory in result_tables:
            rows = result.tables.get(table_name, [])
            path = write_csv_artifact(
                rows,
                directory / filename,
                fieldnames=ANALYSIS_TABLE_FIELDS.get(table_name),
            )
            artifact_records.append(ArtifactRecord(name=filename, path=str(path), kind="csv"))
            csv_manifest_entries.append(
                {
                    "table_name": table_name,
                    "name": filename,
                    "kind": "csv",
                    "path": str(path),
                    "required_columns": ANALYSIS_TABLE_FIELDS.get(table_name, []),
                }
            )
    if output_config.write_json and output_config.write_metadata:
        manifest_path = layout.metadata_dir / "analysis_manifest.json"
        write_json_artifact(
            _build_analysis_manifest(
                case_id=result.case_id,
                run_id=layout.run_id,
                normalized_path=normalized_path,
                result_path=result_path,
                csv_artifacts=csv_manifest_entries,
            ),
            manifest_path,
        )
        artifact_records.append(ArtifactRecord(name="analysis_manifest", path=str(manifest_path), kind="json"))
        run_manifest_paths = write_run_manifest_bundle(
            build_run_manifest(
                pipeline="analyze",
                run_id=layout.run_id,
                run_dir=layout.run_dir,
                status="success",
                pipeline_status=str(result.summary.get("engine_status")),
                case_id=result.case_id,
                case_name=prepared.normalized_case.metadata.name,
                case_path=prepared.case_directory,
                command_invoked=command_invoked,
                config_snapshot={
                    "analysis": snapshot_config(
                        config=analysis_config,
                        source_path=analysis_config_path,
                    ),
                    "output": snapshot_config(
                        config=output_config,
                        source_path=output_config_path,
                    ),
                },
                artifact_records=artifact_records,
                extra={"analysis_schema_version": ANALYSIS_SCHEMA_VERSION},
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
                pipeline="analyze",
                run_id=layout.run_id,
                run_dir=layout.run_dir,
                status="success",
                pipeline_status=str(result.summary.get("engine_status")),
                case_id=result.case_id,
                case_name=prepared.normalized_case.metadata.name,
                case_path=prepared.case_directory,
                command_invoked=command_invoked,
                config_snapshot={
                    "analysis": snapshot_config(
                        config=analysis_config,
                        source_path=analysis_config_path,
                    ),
                    "output": snapshot_config(
                        config=output_config,
                        source_path=output_config_path,
                    ),
                },
                artifact_records=artifact_records,
                extra={"analysis_schema_version": ANALYSIS_SCHEMA_VERSION},
            ),
            metadata_dir=layout.metadata_dir,
        )
    if output_config.write_trace_csv and result.trace_rows:
        write_csv_artifact(result.trace_rows, layout.analysis_traces_dir / "analysis_trace.csv")
    return result, layout
