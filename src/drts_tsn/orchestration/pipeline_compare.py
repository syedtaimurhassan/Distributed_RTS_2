"""Comparison pipeline for previously generated analysis and simulation artifacts."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.comparison.engine import ComparisonEngine
from drts_tsn.comparison.outputs.comparison_result_builder import (
    COMPARISON_SCHEMA_VERSION,
    COMPARISON_TABLE_FIELDS,
)
from drts_tsn.domain.enums import ResultStatus
from drts_tsn.domain.results import (
    AnalysisRunResult,
    AnalysisStreamResult,
    ComparisonRunResult,
    SimulationRunResult,
    SimulationStreamResult,
)
from drts_tsn.io.json_io import read_json
from drts_tsn.io.paths import outputs_root
from drts_tsn.output.artifact_index import ArtifactRecord, write_artifact_index
from drts_tsn.output.csv_writers import write_csv_artifact
from drts_tsn.output.json_writers import write_json_artifact
from drts_tsn.output.metadata_writer import write_run_metadata
from drts_tsn.output.run_layout import RunLayout, create_run_layout
from drts_tsn.output.writers import load_output_config
from drts_tsn.reporting.csv_catalog import (
    COMPARISON_AGGREGATE_COMPARISON_CSV,
    COMPARISON_DIAGNOSTICS_CSV,
    COMPARISON_EXPECTED_WCRT_COMPARISON_CSV,
    COMPARISON_STREAM_COMPARISON_CSV,
)


def _load_simulation_result(path: Path) -> SimulationRunResult:
    """Load a serialized simulation result artifact."""

    data = dict(read_json(path))
    result = SimulationRunResult(
        case_id=str(data["case_id"]),
        run_id=str(data["run_id"]),
        stream_results=[
            SimulationStreamResult(
                stream_id=str(row["stream_id"]),
                max_response_time_us=row.get("max_response_time_us"),
                frame_count=int(row.get("frame_count", 0)),
                status=ResultStatus(str(row.get("status", "stub"))),
                notes=list(row.get("notes", [])),
            )
            for row in data.get("stream_results", [])
        ],
        detail_rows=list(data.get("detail_rows", [])),
        summary=dict(data.get("summary", {})),
        trace_rows=list(data.get("trace_rows", [])),
        tables={str(name): list(rows) for name, rows in dict(data.get("tables", {})).items()},
        artifacts=dict(data.get("artifacts", {})),
    )
    result.artifacts["self"] = str(path)
    return result


def _load_analysis_result(path: Path) -> AnalysisRunResult:
    """Load a serialized analysis result artifact."""

    data = dict(read_json(path))
    result = AnalysisRunResult(
        case_id=str(data["case_id"]),
        run_id=str(data["run_id"]),
        stream_results=[
            AnalysisStreamResult(
                stream_id=str(row["stream_id"]),
                wcrt_us=row.get("wcrt_us"),
                status=ResultStatus(str(row.get("status", "stub"))),
                notes=list(row.get("notes", [])),
            )
            for row in data.get("stream_results", [])
        ],
        detail_rows=list(data.get("detail_rows", [])),
        summary=dict(data.get("summary", {})),
        trace_rows=list(data.get("trace_rows", [])),
        tables={str(name): list(rows) for name, rows in dict(data.get("tables", {})).items()},
        artifacts=dict(data.get("artifacts", {})),
    )
    result.artifacts["self"] = str(path)
    return result


def _build_comparison_manifest(
    *,
    case_id: str,
    run_id: str,
    simulation_result_path: Path,
    analysis_result_path: Path,
    result_path: Path,
    csv_artifacts: list[dict[str, object]],
) -> dict[str, object]:
    """Return stable metadata that describes generated comparison artifacts."""

    return {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "pipeline": "compare",
        "case_id": case_id,
        "run_id": run_id,
        "simulation_result": str(simulation_result_path),
        "analysis_result": str(analysis_result_path),
        "comparison_result": str(result_path),
        "csv_artifacts": csv_artifacts,
    }


def _write_comparison_artifacts(
    *,
    result: ComparisonRunResult,
    layout: RunLayout,
    output_config_path: Path | None,
    simulation_result_path: Path,
    analysis_result_path: Path,
    write_metadata: bool,
) -> None:
    """Write comparison artifacts into a prepared run layout."""

    output_config = load_output_config(output_config_path)
    result.run_id = layout.run_id
    result_path = layout.comparison_results_dir / "comparison_result.json"
    result.tables["aggregate_comparison"] = [
        {**row, "run_id": layout.run_id} for row in result.tables["aggregate_comparison"]
    ]

    csv_artifacts: list[ArtifactRecord] = []
    csv_manifest_entries: list[dict[str, object]] = []

    if output_config.write_json:
        write_json_artifact(result, result_path)
    if output_config.write_csv:
        table_specs = [
            ("stream_comparison", COMPARISON_STREAM_COMPARISON_CSV),
            ("aggregate_comparison", COMPARISON_AGGREGATE_COMPARISON_CSV),
            ("comparison_diagnostics", COMPARISON_DIAGNOSTICS_CSV),
        ]
        if result.tables.get("expected_wcrt_comparison"):
            table_specs.append(("expected_wcrt_comparison", COMPARISON_EXPECTED_WCRT_COMPARISON_CSV))
        for table_name, filename in table_specs:
            path = write_csv_artifact(
                result.tables.get(table_name, []),
                layout.comparison_results_dir / filename,
                fieldnames=COMPARISON_TABLE_FIELDS.get(table_name),
            )
            csv_artifacts.append(ArtifactRecord(name=filename, path=str(path), kind="csv"))
            csv_manifest_entries.append(
                {
                    "table_name": table_name,
                    "name": filename,
                    "kind": "csv",
                    "path": str(path),
                    "required_columns": COMPARISON_TABLE_FIELDS.get(table_name, []),
                }
            )
    if output_config.write_json and output_config.write_metadata and write_metadata:
        manifest_path = layout.metadata_dir / "comparison_manifest.json"
        write_run_metadata(
            {
                "pipeline": "compare",
                "case_id": result.case_id,
                "run_id": layout.run_id,
                "schema_version": COMPARISON_SCHEMA_VERSION,
            },
            layout.metadata_dir / "run_metadata.json",
        )
        write_json_artifact(
            _build_comparison_manifest(
                case_id=result.case_id,
                run_id=layout.run_id,
                simulation_result_path=simulation_result_path,
                analysis_result_path=analysis_result_path,
                result_path=result_path,
                csv_artifacts=csv_manifest_entries,
            ),
            manifest_path,
        )
        write_artifact_index(
            [
                ArtifactRecord(
                    name="simulation_input",
                    path=str(simulation_result_path),
                    kind="json",
                ),
                ArtifactRecord(
                    name="analysis_input",
                    path=str(analysis_result_path),
                    kind="json",
                ),
                ArtifactRecord(name="comparison_result", path=str(result_path), kind="json"),
                ArtifactRecord(name="comparison_manifest", path=str(manifest_path), kind="json"),
                *csv_artifacts,
            ],
            layout.metadata_dir / "artifact_index.json",
        )


def execute(
    *,
    simulation_result_path: Path,
    analysis_result_path: Path,
    output_config_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
    write_metadata: bool = True,
) -> tuple[ComparisonRunResult, RunLayout]:
    """Run comparison against serialized analysis and simulation artifacts."""

    simulation_result = _load_simulation_result(simulation_result_path)
    analysis_result = _load_analysis_result(analysis_result_path)
    layout = create_run_layout(
        output_root or outputs_root(),
        run_id=run_id,
        symlink_latest=load_output_config(output_config_path).symlink_latest,
    )
    result = ComparisonEngine().run(simulation_result, analysis_result)
    _write_comparison_artifacts(
        result=result,
        layout=layout,
        output_config_path=output_config_path,
        simulation_result_path=simulation_result_path,
        analysis_result_path=analysis_result_path,
        write_metadata=write_metadata,
    )
    return result, layout
