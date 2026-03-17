"""Comparison pipeline for existing or freshly computed results."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.comparison.engine import ComparisonEngine
from drts_tsn.comparison.outputs.comparison_result_builder import (
    comparison_result_to_rows,
    comparison_summary_rows,
)
from drts_tsn.domain.enums import ResultStatus
from drts_tsn.domain.results import AnalysisRunResult, AnalysisStreamResult, ComparisonRunResult, SimulationRunResult, SimulationStreamResult
from drts_tsn.io.paths import outputs_root
from drts_tsn.io.json_io import read_json
from drts_tsn.output.artifact_index import ArtifactRecord, write_artifact_index
from drts_tsn.output.csv_writers import write_csv_artifact
from drts_tsn.output.json_writers import write_json_artifact
from drts_tsn.output.metadata_writer import write_run_metadata
from drts_tsn.output.run_layout import RunLayout, create_run_layout
from drts_tsn.output.writers import load_output_config
from drts_tsn.reporting.csv_catalog import COMPARISON_STREAMS_CSV, COMPARISON_SUMMARY_CSV


def _load_simulation_result(path: Path) -> SimulationRunResult:
    data = dict(read_json(path))
    return SimulationRunResult(
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
        artifacts=dict(data.get("artifacts", {})),
    )


def _load_analysis_result(path: Path) -> AnalysisRunResult:
    data = dict(read_json(path))
    return AnalysisRunResult(
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
        artifacts=dict(data.get("artifacts", {})),
    )


def execute(
    *,
    simulation_result: SimulationRunResult | None = None,
    analysis_result: AnalysisRunResult | None = None,
    simulation_result_path: Path | None = None,
    analysis_result_path: Path | None = None,
    output_config_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> tuple[ComparisonRunResult, RunLayout]:
    """Run the comparison scaffold against result objects or JSON files."""

    if simulation_result is None:
        if simulation_result_path is None:
            raise ValueError("A simulation result object or path is required.")
        simulation_result = _load_simulation_result(simulation_result_path)
    if analysis_result is None:
        if analysis_result_path is None:
            raise ValueError("An analysis result object or path is required.")
        analysis_result = _load_analysis_result(analysis_result_path)

    output_config = load_output_config(output_config_path)
    layout = create_run_layout(
        output_root or outputs_root(),
        run_id=run_id,
        symlink_latest=output_config.symlink_latest,
    )
    result = ComparisonEngine().run(simulation_result, analysis_result)
    result_path = layout.comparison_results_dir / "comparison_result.json"
    if output_config.write_json:
        write_json_artifact(result, result_path)
    if output_config.write_csv:
        write_csv_artifact(comparison_result_to_rows(result), layout.comparison_results_dir / COMPARISON_STREAMS_CSV)
        write_csv_artifact(comparison_summary_rows(result), layout.comparison_results_dir / COMPARISON_SUMMARY_CSV)
    if output_config.write_json and output_config.write_metadata:
        write_run_metadata(
            {"pipeline": "compare", "case_id": result.case_id, "run_id": layout.run_id},
            layout.metadata_dir / "run_metadata.json",
        )
        records = [ArtifactRecord(name="comparison_result", path=str(result_path), kind="json")]
        if simulation_result_path is not None:
            records.append(
                ArtifactRecord(name="simulation_input", path=str(simulation_result_path), kind="json")
            )
        if analysis_result_path is not None:
            records.append(
                ArtifactRecord(name="analysis_input", path=str(analysis_result_path), kind="json")
            )
        write_artifact_index(records, layout.metadata_dir / "artifact_index.json")
    return result, layout
