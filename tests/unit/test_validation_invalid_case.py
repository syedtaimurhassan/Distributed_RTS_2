"""Validation coverage for invalid fixture cases."""

from __future__ import annotations

from drts_tsn.orchestration.run_manager import prepare_case


def test_invalid_fixture_case_reports_actionable_errors(invalid_case_path) -> None:
    """The invalid fixture should fail validation with useful route/node messages."""

    prepared = prepare_case(invalid_case_path)

    assert not prepared.validation_report.is_valid
    codes = {issue.code for issue in prepared.validation_report.issues}
    assert "routes.hop.unknown-node" in codes
    assert "routes.link.missing" in codes
