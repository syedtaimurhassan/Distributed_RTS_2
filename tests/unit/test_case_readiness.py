"""Unit coverage for readiness-stage classification."""

from __future__ import annotations

from drts_tsn.orchestration.run_manager import prepare_case


def test_sample_case_is_ready_for_all_stages(sample_case_path) -> None:
    """The sample fixture should pass all readiness stages."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    readiness = prepared.readiness_report

    assert readiness.schema_valid
    assert readiness.normalization_valid
    assert readiness.baseline_runnable
    assert readiness.simulation_ready
    assert readiness.analysis_ready


def test_invalid_reserved_bandwidth_case_is_not_analysis_ready(
    invalid_reserved_bandwidth_case_path,
) -> None:
    """A case can be structurally valid but fail analysis-readiness preconditions."""

    prepared = prepare_case(invalid_reserved_bandwidth_case_path, include_analysis_checks=True)
    readiness = prepared.readiness_report

    assert readiness.normalization_valid
    assert readiness.baseline_runnable
    assert readiness.simulation_ready
    assert not readiness.analysis_ready
    assert any(
        issue.code == "analysis.reserved-bandwidth.exceeded"
        for issue in readiness.analysis_report.issues
    )
