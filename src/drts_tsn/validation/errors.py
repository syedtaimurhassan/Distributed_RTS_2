"""Validation issue models and aggregate error types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class ValidationIssue:
    """A single validation issue."""

    code: str
    message: str
    severity: str = "error"
    location: str | None = None


@dataclass(slots=True)
class ValidationReport:
    """A collection of validation issues for a case."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return whether the report contains no errors."""

        return all(issue.severity != "error" for issue in self.issues)

    def extend(self, issues: list[ValidationIssue]) -> None:
        """Append issues to the report."""

        self.issues.extend(issues)

    def error_issues(self) -> list[ValidationIssue]:
        """Return only error-severity issues in stable input order."""

        return [issue for issue in self.issues if issue.severity == "error"]

    def format_lines(self) -> list[str]:
        """Render issues into concise, actionable diagnostic lines."""

        return [
            " | ".join(
                part
                for part in (
                    issue.code,
                    issue.location,
                    issue.message,
                )
                if part
            )
            for issue in self.issues
        ]

    def raise_for_errors(self) -> None:
        """Raise a typed exception if any error issues exist."""

        if not self.is_valid:
            raise CaseValidationError(self)


class CaseValidationError(Exception):
    """Raised when a case fails validation."""

    def __init__(self, report: ValidationReport) -> None:
        message = "Case validation failed"
        if report.issues:
            message = "Case validation failed: " + "; ".join(report.format_lines())
        super().__init__(message)
        self.report = report
