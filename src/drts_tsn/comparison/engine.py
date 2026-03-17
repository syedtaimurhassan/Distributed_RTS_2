"""Top-level comparison engine scaffold."""

from __future__ import annotations

from drts_tsn.common.time_utils import utc_timestamp_compact
from drts_tsn.domain.results import AnalysisRunResult, ComparisonEntry, ComparisonRunResult, ResultStatus, SimulationRunResult

from .aligner import align_stream_results
from .diagnostics import build_diagnostics
from .metrics import absolute_difference
from .tolerances import within_tolerance


class ComparisonEngine:
    """Compare simulation and analytical outputs in a dedicated subsystem."""

    def run(
        self,
        simulation_result: SimulationRunResult,
        analysis_result: AnalysisRunResult,
    ) -> ComparisonRunResult:
        """Return a structured comparison result."""

        entries: list[ComparisonEntry] = []
        for simulation_stream, analysis_stream, stream_id in align_stream_results(
            simulation_result, analysis_result
        ):
            simulation_value = (
                simulation_stream.max_response_time_us if simulation_stream is not None else None
            )
            analysis_value = analysis_stream.wcrt_us if analysis_stream is not None else None
            difference = absolute_difference(simulation_value, analysis_value)
            in_tolerance = within_tolerance(difference)
            status = ResultStatus.OK
            notes: list[str] = []
            if difference is None:
                notes.append("At least one side did not produce a comparable numeric value.")
            elif in_tolerance is False:
                status = ResultStatus.ERROR
                notes.append("Difference exceeds the configured tolerance.")
            entries.append(
                ComparisonEntry(
                    stream_id=stream_id,
                    simulation_response_time_us=simulation_value,
                    analysis_response_time_us=analysis_value,
                    absolute_difference_us=difference,
                    within_tolerance=in_tolerance,
                    status=status,
                    notes=notes,
                )
            )
        case_id = simulation_result.case_id or analysis_result.case_id
        comparable_entries = [entry for entry in entries if entry.absolute_difference_us is not None]
        return ComparisonRunResult(
            case_id=case_id,
            run_id=f"cmp-{utc_timestamp_compact()}",
            entries=entries,
            summary={
                "engine_status": "ok",
                "entry_count": len(entries),
                "comparable_entry_count": len(comparable_entries),
                "within_tolerance_count": sum(
                    1 for entry in comparable_entries if entry.within_tolerance
                ),
                "max_absolute_difference_us": max(
                    (entry.absolute_difference_us or 0.0) for entry in comparable_entries
                )
                if comparable_entries
                else None,
            },
            diagnostics=build_diagnostics(entries),
        )
