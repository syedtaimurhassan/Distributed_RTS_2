"""Unit tests for the comparison baseline."""

from __future__ import annotations

import pytest

from drts_tsn.analysis.engine import AnalysisEngine
from drts_tsn.comparison.engine import ComparisonEngine
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.simulation.engine import SimulationEngine


def test_comparison_engine_aligns_matching_baseline_results(sample_case_path) -> None:
    """Simulation and analysis should match on the bundled baseline case."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    simulation_result = SimulationEngine().run(prepared.normalized_case)
    analysis_result = AnalysisEngine().run(prepared.normalized_case)

    comparison = ComparisonEngine().run(simulation_result, analysis_result)

    assert len(comparison.entries) == 1
    assert comparison.entries[0].absolute_difference_us == pytest.approx(0.0)
    assert comparison.entries[0].within_tolerance is True
    assert comparison.summary["within_tolerance_count"] == 1
