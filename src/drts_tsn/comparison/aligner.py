"""Alignment helpers for simulation and analytical result sets."""

from __future__ import annotations

from drts_tsn.domain.results import AnalysisRunResult, AnalysisStreamResult, SimulationRunResult, SimulationStreamResult


def align_stream_results(
    simulation_result: SimulationRunResult,
    analysis_result: AnalysisRunResult,
) -> list[tuple[SimulationStreamResult | None, AnalysisStreamResult | None, str]]:
    """Align results by stream ID."""

    simulation_by_id = {result.stream_id: result for result in simulation_result.stream_results}
    analysis_by_id = {result.stream_id: result for result in analysis_result.stream_results}
    stream_ids = sorted(set(simulation_by_id) | set(analysis_by_id))
    return [
        (simulation_by_id.get(stream_id), analysis_by_id.get(stream_id), stream_id)
        for stream_id in stream_ids
    ]
