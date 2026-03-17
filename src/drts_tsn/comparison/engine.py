"""Top-level comparison engine for analytical and simulation artifacts."""

from __future__ import annotations

from drts_tsn.common.time_utils import utc_timestamp_compact
from drts_tsn.domain.enums import ResultStatus
from drts_tsn.domain.results import AnalysisRunResult, ComparisonEntry, ComparisonRunResult, SimulationRunResult

from .aligner import align_stream_rows
from .diagnostics import build_diagnostic_row
from .metrics import absolute_difference, exceeds_analysis, ratio, signed_margin
from .outputs.comparison_result_builder import (
    COMPARISON_SCHEMA_VERSION,
    build_comparison_tables,
)


def _analysis_stream_rows(result: AnalysisRunResult) -> list[dict[str, object]]:
    """Return stable analysis stream rows, falling back to legacy fields if needed."""

    table_rows = result.tables.get("stream_wcrt_summary")
    if table_rows is not None:
        return list(table_rows)
    return [
        {
            "stream_id": row.stream_id,
            "route_id": None,
            "traffic_class": None,
            "hop_count": None,
            "deadline_us": None,
            "end_to_end_wcrt_us": row.wcrt_us,
            "expected_wcrt_us": None,
            "status": row.status.value,
        }
        for row in result.stream_results
    ]


def _simulation_stream_rows(result: SimulationRunResult) -> list[dict[str, object]]:
    """Return stable simulation stream rows, falling back to legacy fields if needed."""

    table_rows = result.tables.get("stream_summary")
    if table_rows is not None:
        return list(table_rows)
    return [
        {
            "stream_id": row.stream_id,
            "traffic_class": None,
            "route_id": None,
            "hop_count": None,
            "release_count": row.frame_count,
            "delivery_count": row.frame_count,
            "max_response_time_us": row.max_response_time_us,
            "mean_response_time_us": row.max_response_time_us,
            "status": row.status.value,
        }
        for row in result.stream_results
    ]


def _comparison_status(
    *,
    simulation_exceeded: bool | None,
    has_missing_side: bool,
    class_mismatch: bool,
    path_mismatch: bool,
    duplicate_flagged: bool,
) -> ResultStatus:
    """Return a concise result status for one stream comparison row."""

    if has_missing_side or class_mismatch or path_mismatch or duplicate_flagged:
        return ResultStatus.ERROR
    if simulation_exceeded:
        return ResultStatus.ERROR
    return ResultStatus.OK


def _engine_status(
    *,
    entries: list[ComparisonEntry],
    diagnostics: list[dict[str, object]],
) -> str:
    """Return a high-level engine status for the aggregate comparison summary."""

    if any(entry.status == ResultStatus.ERROR for entry in entries):
        return "issues_detected"
    if any(str(row.get("severity")) == "error" for row in diagnostics):
        return "issues_detected"
    return "ok"


class ComparisonEngine:
    """Compare simulation and analytical outputs in a dedicated subsystem."""

    def run(
        self,
        simulation_result: SimulationRunResult,
        analysis_result: AnalysisRunResult,
    ) -> ComparisonRunResult:
        """Return a structured comparison result from stable result artifacts."""

        analysis_rows = _analysis_stream_rows(analysis_result)
        simulation_rows = _simulation_stream_rows(simulation_result)
        alignment = align_stream_rows(
            analysis_rows=analysis_rows,
            simulation_rows=simulation_rows,
        )
        diagnostics = list(alignment.diagnostics)
        duplicate_stream_ids = {
            str(row["stream_id"])
            for row in diagnostics
            if row["diagnostic_code"].startswith("comparison.duplicate.")
        }

        entries: list[ComparisonEntry] = []
        for aligned in alignment.aligned_rows:
            analysis_row = aligned.analysis_row or {}
            simulation_row = aligned.simulation_row or {}
            analysis_wcrt_us = analysis_row.get("end_to_end_wcrt_us")
            simulation_wcrt_us = simulation_row.get("max_response_time_us")
            expected_wcrt_us = analysis_row.get("expected_wcrt_us")
            margin_us = signed_margin(analysis_wcrt_us, simulation_wcrt_us)
            absolute_difference_us = absolute_difference(analysis_wcrt_us, simulation_wcrt_us)
            simulation_exceeded = exceeds_analysis(analysis_wcrt_us, simulation_wcrt_us)
            class_mismatch = (
                analysis_row.get("traffic_class") is not None
                and simulation_row.get("traffic_class") is not None
                and analysis_row.get("traffic_class") != simulation_row.get("traffic_class")
            )
            path_mismatch = (
                (
                    analysis_row.get("route_id") is not None
                    and simulation_row.get("route_id") is not None
                    and analysis_row.get("route_id") != simulation_row.get("route_id")
                )
                or (
                    analysis_row.get("hop_count") is not None
                    and simulation_row.get("hop_count") is not None
                    and analysis_row.get("hop_count") != simulation_row.get("hop_count")
                )
            )
            discrepancy_flags: list[str] = []
            notes: list[str] = []
            if aligned.analysis_row is None:
                discrepancy_flags.append("missing_analysis")
                diagnostics.append(
                    build_diagnostic_row(
                        diagnostic_code="comparison.missing.analysis_stream",
                        severity="error",
                        stream_id=aligned.stream_id,
                        source="analysis",
                        message=f"Stream '{aligned.stream_id}' is missing from analysis results.",
                    )
                )
                notes.append("Missing analytical result.")
            if aligned.simulation_row is None:
                discrepancy_flags.append("missing_simulation")
                diagnostics.append(
                    build_diagnostic_row(
                        diagnostic_code="comparison.missing.simulation_stream",
                        severity="error",
                        stream_id=aligned.stream_id,
                        source="simulation",
                        message=f"Stream '{aligned.stream_id}' is missing from simulation results.",
                    )
                )
                notes.append("Missing simulation result.")
            if aligned.stream_id in duplicate_stream_ids:
                discrepancy_flags.append("duplicate_stream_id")
            if class_mismatch:
                discrepancy_flags.append("class_mismatch")
                diagnostics.append(
                    build_diagnostic_row(
                        diagnostic_code="comparison.metadata.class_mismatch",
                        severity="error",
                        stream_id=aligned.stream_id,
                        message=(
                            f"Stream '{aligned.stream_id}' has analysis class "
                            f"'{analysis_row.get('traffic_class')}' but simulation class "
                            f"'{simulation_row.get('traffic_class')}'."
                        ),
                    )
                )
                notes.append("Traffic class mismatch across artifacts.")
            if path_mismatch:
                discrepancy_flags.append("path_mismatch")
                diagnostics.append(
                    build_diagnostic_row(
                        diagnostic_code="comparison.metadata.route_mismatch",
                        severity="error",
                        stream_id=aligned.stream_id,
                        message=(
                            f"Stream '{aligned.stream_id}' has analysis route "
                            f"'{analysis_row.get('route_id')}' but simulation route "
                            f"'{simulation_row.get('route_id')}'."
                        ),
                    )
                )
                notes.append("Route mismatch across artifacts.")
            if simulation_exceeded:
                discrepancy_flags.append("simulation_exceeded_analysis")
                diagnostics.append(
                    build_diagnostic_row(
                        diagnostic_code="comparison.simulation.exceeds_analysis",
                        severity="warning",
                        stream_id=aligned.stream_id,
                        message=(
                            f"Simulation exceeds analysis for stream '{aligned.stream_id}' by "
                            f"{abs(margin_us or 0.0):.6f} us."
                        ),
                    )
                )
                notes.append("Observed simulation exceeds analytical bound.")
            expected_minus_analysis_us = signed_margin(expected_wcrt_us, analysis_wcrt_us)
            expected_minus_simulation_us = signed_margin(expected_wcrt_us, simulation_wcrt_us)
            if expected_wcrt_us is not None and analysis_wcrt_us is not None:
                if absolute_difference(expected_wcrt_us, analysis_wcrt_us) not in (None, 0.0):
                    discrepancy_flags.append("expected_differs_from_analysis")
                    diagnostics.append(
                        build_diagnostic_row(
                            diagnostic_code="comparison.reference.analysis_mismatch",
                            severity="warning",
                            stream_id=aligned.stream_id,
                            source="expected",
                            message=(
                                f"Expected/reference WCRT differs from analysis for stream "
                                f"'{aligned.stream_id}'."
                            ),
                        )
                    )
                    notes.append("Expected/reference WCRT differs from analysis.")

            status = _comparison_status(
                simulation_exceeded=simulation_exceeded,
                has_missing_side=aligned.analysis_row is None or aligned.simulation_row is None,
                class_mismatch=class_mismatch,
                path_mismatch=path_mismatch,
                duplicate_flagged=aligned.stream_id in duplicate_stream_ids,
            )
            entries.append(
                ComparisonEntry(
                    stream_id=aligned.stream_id,
                    analysis_traffic_class=(
                        str(analysis_row["traffic_class"])
                        if analysis_row.get("traffic_class") is not None
                        else None
                    ),
                    simulation_traffic_class=(
                        str(simulation_row["traffic_class"])
                        if simulation_row.get("traffic_class") is not None
                        else None
                    ),
                    analysis_route_id=(
                        str(analysis_row["route_id"])
                        if analysis_row.get("route_id") is not None
                        else None
                    ),
                    simulation_route_id=(
                        str(simulation_row["route_id"])
                        if simulation_row.get("route_id") is not None
                        else None
                    ),
                    analysis_hop_count=(
                        int(analysis_row["hop_count"])
                        if analysis_row.get("hop_count") is not None
                        else None
                    ),
                    simulation_hop_count=(
                        int(simulation_row["hop_count"])
                        if simulation_row.get("hop_count") is not None
                        else None
                    ),
                    analytical_wcrt_us=(
                        float(analysis_wcrt_us) if analysis_wcrt_us is not None else None
                    ),
                    simulated_worst_response_time_us=(
                        float(simulation_wcrt_us) if simulation_wcrt_us is not None else None
                    ),
                    expected_wcrt_us=(
                        float(expected_wcrt_us) if expected_wcrt_us is not None else None
                    ),
                    absolute_difference_us=absolute_difference_us,
                    analysis_minus_simulation_margin_us=margin_us,
                    analysis_to_simulation_ratio=ratio(analysis_wcrt_us, simulation_wcrt_us),
                    simulation_exceeded_analysis=simulation_exceeded,
                    class_mismatch=class_mismatch,
                    path_mismatch=path_mismatch,
                    expected_minus_analysis_us=expected_minus_analysis_us,
                    expected_minus_simulation_us=expected_minus_simulation_us,
                    discrepancy_flags=discrepancy_flags,
                    status=status,
                    notes=notes,
                )
            )

        case_id = simulation_result.case_id or analysis_result.case_id
        matched_entries = [
            entry
            for entry in entries
            if entry.analytical_wcrt_us is not None and entry.simulated_worst_response_time_us is not None
        ]
        negative_margins = [
            abs(entry.analysis_minus_simulation_margin_us)
            for entry in entries
            if entry.analysis_minus_simulation_margin_us is not None
            and entry.analysis_minus_simulation_margin_us < 0.0
        ]
        result = ComparisonRunResult(
            case_id=case_id,
            run_id=f"cmp-{utc_timestamp_compact()}",
            entries=entries,
            summary={
                "schema_version": COMPARISON_SCHEMA_VERSION,
                "engine_status": _engine_status(entries=entries, diagnostics=diagnostics),
                "stream_count": len(entries),
                "matched_stream_count": len(matched_entries),
                "missing_analysis_count": sum(
                    1 for entry in entries if "missing_analysis" in entry.discrepancy_flags
                ),
                "missing_simulation_count": sum(
                    1 for entry in entries if "missing_simulation" in entry.discrepancy_flags
                ),
                "duplicate_analysis_count": sum(
                    1
                    for row in diagnostics
                    if row["diagnostic_code"] == "comparison.duplicate.analysis_stream_id"
                ),
                "duplicate_simulation_count": sum(
                    1
                    for row in diagnostics
                    if row["diagnostic_code"] == "comparison.duplicate.simulation_stream_id"
                ),
                "simulation_exceeded_analysis_count": sum(
                    1 for entry in entries if entry.simulation_exceeded_analysis
                ),
                "reference_row_count": sum(1 for entry in entries if entry.expected_wcrt_us is not None),
                "max_absolute_difference_us": max(
                    (entry.absolute_difference_us or 0.0) for entry in matched_entries
                )
                if matched_entries
                else None,
                "max_simulation_over_analysis_us": max(negative_margins) if negative_margins else 0.0,
            },
            diagnostics=diagnostics,
            artifacts={
                "analysis_result": analysis_result.artifacts.get("self", ""),
                "simulation_result": simulation_result.artifacts.get("self", ""),
            },
        )
        result.tables = build_comparison_tables(
            result=result,
            analysis_run_id=analysis_result.run_id,
            simulation_run_id=simulation_result.run_id,
        )
        return result
