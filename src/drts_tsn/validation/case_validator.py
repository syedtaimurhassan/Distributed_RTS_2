"""Top-level canonical case validation orchestration."""

from __future__ import annotations

from drts_tsn.domain.case import Case

from .analysis_preconditions import validate_analysis_preconditions
from .assumptions_validator import validate_assumptions
from .cbs_validator import validate_cbs_settings
from .errors import ValidationReport
from .routes_validator import validate_routes
from .stream_validator import validate_streams
from .topology_validator import validate_topology


def validate_case(case: Case, *, include_analysis_checks: bool = False) -> ValidationReport:
    """Run the reusable validation pipeline over a canonical case."""

    report = ValidationReport()
    report.extend(validate_topology(case))
    report.extend(validate_routes(case))
    report.extend(validate_streams(case))
    report.extend(validate_cbs_settings(case))
    report.extend(validate_assumptions(case))
    if include_analysis_checks:
        report.extend(validate_analysis_preconditions(case))
    return report
