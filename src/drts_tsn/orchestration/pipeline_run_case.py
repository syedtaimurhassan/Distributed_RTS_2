"""Combined end-to-end pipeline for one case."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.analysis.config import load_analysis_config
from drts_tsn.analysis.engine import AnalysisEngine
from drts_tsn.comparison.engine import ComparisonEngine
from drts_tsn.comparison.outputs.comparison_result_builder import (
    comparison_result_to_rows,
    comparison_summary_rows,
)
from drts_tsn.io.paths import outputs_root
from drts_tsn.output.artifact_index import ArtifactRecord, write_artifact_index
from drts_tsn.output.csv_writers import write_csv_artifact
from drts_tsn.output.json_writers import write_json_artifact
from drts_tsn.output.metadata_writer import write_run_metadata
from drts_tsn.output.run_layout import RunLayout, create_run_layout
from drts_tsn.output.writers import load_output_config
from drts_tsn.reporting.csv_catalog import (
    ANALYSIS_DETAILS_CSV,
    ANALYSIS_STREAMS_CSV,
    COMPARISON_STREAMS_CSV,
    COMPARISON_SUMMARY_CSV,
    SIMULATION_DETAILS_CSV,
    SIMULATION_STREAMS_CSV,
)
from drts_tsn.reporting.stream_summaries import analysis_stream_rows, simulation_stream_rows
from drts_tsn.simulation.config import load_simulation_config
from drts_tsn.simulation.engine import SimulationEngine

from .run_manager import export_prepared_case, prepare_case


def execute(
    case_path: str | Path,
    *,
    simulation_config_path: Path | None = None,
    analysis_config_path: Path | None = None,
    output_config_path: Path | None = None,
    output_root: Path | None = None,
    run_id: str | None = None,
) -> tuple[dict[str, object], RunLayout]:
    """Run preparation, simulation, analysis, and comparison in one run directory."""

    prepared = prepare_case(case_path, include_analysis_checks=True)
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

    simulation_result = SimulationEngine().run(
        prepared.normalized_case, load_simulation_config(simulation_config_path)
    )
    analysis_result = AnalysisEngine().run(
        prepared.normalized_case, load_analysis_config(analysis_config_path)
    )
    comparison_result = ComparisonEngine().run(simulation_result, analysis_result)

    simulation_path = layout.simulation_results_dir / "simulation_result.json"
    analysis_path = layout.analysis_results_dir / "analysis_result.json"
    comparison_path = layout.comparison_results_dir / "comparison_result.json"

    if output_config.write_json:
        write_json_artifact(simulation_result, simulation_path)
        write_json_artifact(analysis_result, analysis_path)
        write_json_artifact(comparison_result, comparison_path)
    if output_config.write_csv:
        write_csv_artifact(simulation_result.detail_rows, layout.simulation_results_dir / SIMULATION_DETAILS_CSV)
        write_csv_artifact(simulation_stream_rows(simulation_result), layout.simulation_results_dir / SIMULATION_STREAMS_CSV)
        write_csv_artifact(analysis_result.detail_rows, layout.analysis_results_dir / ANALYSIS_DETAILS_CSV)
        write_csv_artifact(analysis_stream_rows(analysis_result), layout.analysis_results_dir / ANALYSIS_STREAMS_CSV)
        write_csv_artifact(comparison_result_to_rows(comparison_result), layout.comparison_results_dir / COMPARISON_STREAMS_CSV)
        write_csv_artifact(comparison_summary_rows(comparison_result), layout.comparison_results_dir / COMPARISON_SUMMARY_CSV)
    if output_config.write_trace_csv:
        if simulation_result.trace_rows:
            write_csv_artifact(simulation_result.trace_rows, layout.simulation_traces_dir / "simulation_trace.csv")
        if analysis_result.trace_rows:
            write_csv_artifact(analysis_result.trace_rows, layout.analysis_traces_dir / "analysis_trace.csv")
    if output_config.write_json and output_config.write_metadata:
        write_run_metadata(
            {"pipeline": "run-case", "case_id": prepared.normalized_case.metadata.case_id, "run_id": layout.run_id},
            layout.metadata_dir / "run_metadata.json",
        )
        write_artifact_index(
            [
                ArtifactRecord(name="normalized_case", path=str(normalized_path), kind="json"),
                ArtifactRecord(name="simulation_result", path=str(simulation_path), kind="json"),
                ArtifactRecord(name="analysis_result", path=str(analysis_path), kind="json"),
                ArtifactRecord(name="comparison_result", path=str(comparison_path), kind="json"),
            ],
            layout.metadata_dir / "artifact_index.json",
        )
    return {
        "simulation_result": simulation_result,
        "analysis_result": analysis_result,
        "comparison_result": comparison_result,
    }, layout
