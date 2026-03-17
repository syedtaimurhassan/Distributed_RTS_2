"""Helpers that render structured objects for console output."""

from __future__ import annotations

from typing import Any

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover - dependency fallback
    def tabulate(rows: list[dict[str, Any]], headers: str = "keys", tablefmt: str = "plain") -> str:
        if not rows:
            return ""
        keys = list(rows[0].keys()) if headers == "keys" else list(headers)
        lines = [" | ".join(keys)]
        for row in rows:
            lines.append(" | ".join(str(row.get(key, "")) for key in keys))
        return "\n".join(lines)

from drts_tsn.validation.errors import ValidationReport


def render_validation_report(report: ValidationReport) -> str:
    """Render a validation report as a table."""

    if not report.issues:
        return "Validation passed with no issues."
    rows = [
        {
            "severity": issue.severity,
            "code": issue.code,
            "location": issue.location or "-",
            "message": issue.message,
        }
        for issue in report.issues
    ]
    return tabulate(rows, headers="keys", tablefmt="github")


def render_mapping(summary: dict[str, Any]) -> str:
    """Render a mapping as a simple two-column table."""

    rows = [{"field": key, "value": value} for key, value in summary.items()]
    return tabulate(rows, headers="keys", tablefmt="github")


def render_case_inspection(inspection: dict[str, Any]) -> str:
    """Render a multi-section case inspection view."""

    sections: list[str] = []
    sections.append("Overview")
    sections.append(render_mapping(dict(inspection["overview"])))
    for key in ("class_counts", "nodes", "links", "routes", "streams"):
        rows = inspection[key]
        sections.append("")
        sections.append(key.replace("_", " ").title())
        if rows:
            sections.append(tabulate(rows, headers="keys", tablefmt="github"))
        else:
            sections.append("(none)")
    return "\n".join(sections)
