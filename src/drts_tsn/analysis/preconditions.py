"""Analytical precondition helpers."""

from __future__ import annotations

from drts_tsn.domain.case import Case
from drts_tsn.validation.errors import ValidationIssue
from drts_tsn.validation.analysis_preconditions import validate_analysis_preconditions


class AnalysisPreconditionError(ValueError):
    """Raised when analytical preconditions fail in strict mode."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        super().__init__(format_precondition_failures(issues))
        self.issues = issues


def check_preconditions(case: Case) -> list[ValidationIssue]:
    """Return structured precondition failures for the analytical engine."""

    return validate_analysis_preconditions(case)


def format_precondition_failures(issues: list[ValidationIssue]) -> str:
    """Render precondition failures into a stable diagnostic string."""

    if not issues:
        return "Analysis preconditions failed."
    details = "\n".join(
        f"- {' | '.join(part for part in (issue.code, issue.location, issue.message) if part)}"
        for issue in issues
    )
    return f"Analysis preconditions failed ({len(issues)} issue(s)):\n{details}"
