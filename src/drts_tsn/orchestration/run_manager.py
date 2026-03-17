"""Reusable case preparation helpers shared by orchestration pipelines."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from drts_tsn.adapters.external_cases.loader import ExternalCaseBundle, load_external_case
from drts_tsn.adapters.external_cases.mapper import map_external_case
from drts_tsn.adapters.exports.normalized_case_exporter import (
    export_normalized_case,
    export_normalized_case_bundle,
)
from drts_tsn.domain.case import Case
from drts_tsn.io.paths import resolve_case_path
from drts_tsn.normalization.normalize_case import normalize_case
from drts_tsn.reporting.case_overview import build_case_inspection, build_case_overview
from drts_tsn.validation.case_validator import validate_case
from drts_tsn.validation.errors import ValidationReport


@dataclass(slots=True)
class PreparedCase:
    """Bundle together the main intermediate representations for a case."""

    case_directory: Path
    external_bundle: ExternalCaseBundle
    mapped_case: Case
    normalized_case: Case
    validation_report: ValidationReport


def prepare_case(case_path: str | Path, *, include_analysis_checks: bool = False) -> PreparedCase:
    """Load, map, normalize, and validate an external case directory."""

    resolved_path = resolve_case_path(case_path)
    external_bundle = load_external_case(resolved_path)
    mapped_case = map_external_case(external_bundle)
    normalized_case = normalize_case(mapped_case)
    report = validate_case(normalized_case, include_analysis_checks=include_analysis_checks)
    return PreparedCase(
        case_directory=resolved_path,
        external_bundle=external_bundle,
        mapped_case=mapped_case,
        normalized_case=normalized_case,
        validation_report=report,
    )


def inspect_prepared_case(prepared_case: PreparedCase) -> dict[str, Any]:
    """Return a flat case summary for console rendering."""

    return {
        **build_case_overview(prepared_case.normalized_case),
        "case_directory": str(prepared_case.case_directory),
        "missing_optional_files": ",".join(prepared_case.external_bundle.missing_optional_files) or "-",
        "validation_issue_count": len(prepared_case.validation_report.issues),
    }


def inspect_prepared_case_detailed(prepared_case: PreparedCase) -> dict[str, Any]:
    """Return a detailed structured inspection view."""

    inspection = build_case_inspection(prepared_case.normalized_case)
    inspection["overview"]["case_directory"] = str(prepared_case.case_directory)
    inspection["overview"]["missing_optional_files"] = (
        ",".join(prepared_case.external_bundle.missing_optional_files) or "-"
    )
    inspection["overview"]["validation_issue_count"] = len(prepared_case.validation_report.issues)
    return inspection


def export_prepared_case(prepared_case: PreparedCase, destination: Path) -> Path:
    """Export the normalized case representation to disk."""

    return export_normalized_case(prepared_case.normalized_case, destination)


def export_prepared_case_bundle(prepared_case: PreparedCase, destination_directory: Path) -> dict[str, Path]:
    """Export the normalized case representation plus core CSVs."""

    return export_normalized_case_bundle(prepared_case.normalized_case, destination_directory)
