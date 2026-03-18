"""Readiness classification for normalized cases."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.domain.case import Case

from .case_validator import validate_case
from .errors import ValidationReport

READINESS_STAGES = ("schema", "normalization", "baseline", "simulation", "analysis", "all")


@dataclass(slots=True)
class CaseReadinessReport:
    """Stage-specific readiness statuses and backing validation reports."""

    schema_valid: bool
    normalization_valid: bool
    baseline_runnable: bool
    simulation_ready: bool
    analysis_ready: bool
    normalization_report: ValidationReport
    baseline_report: ValidationReport
    simulation_report: ValidationReport
    analysis_report: ValidationReport

    def status_for_stage(self, stage: str) -> bool:
        """Return boolean readiness for one stage label."""

        if stage == "schema":
            return self.schema_valid
        if stage == "normalization":
            return self.normalization_valid
        if stage == "baseline":
            return self.baseline_runnable
        if stage == "simulation":
            return self.simulation_ready
        if stage == "analysis":
            return self.analysis_ready
        if stage == "all":
            return all(
                (
                    self.schema_valid,
                    self.normalization_valid,
                    self.baseline_runnable,
                    self.simulation_ready,
                    self.analysis_ready,
                )
            )
        raise ValueError(f"Unsupported readiness stage '{stage}'.")

    def report_for_stage(self, stage: str) -> ValidationReport:
        """Return the report most relevant to one stage label."""

        if stage == "normalization":
            return self.normalization_report
        if stage == "baseline":
            return self.baseline_report
        if stage == "simulation":
            return self.simulation_report
        if stage in {"analysis", "all"}:
            return self.analysis_report
        if stage == "schema":
            return ValidationReport()
        raise ValueError(f"Unsupported readiness stage '{stage}'.")

    def status_mapping(self) -> dict[str, bool]:
        """Return a stable flat status mapping for rendering."""

        return {
            "schema_valid": self.schema_valid,
            "normalization_valid": self.normalization_valid,
            "baseline_runnable": self.baseline_runnable,
            "simulation_ready": self.simulation_ready,
            "analysis_ready": self.analysis_ready,
        }


def evaluate_case_readiness(case: Case) -> CaseReadinessReport:
    """Build readiness status reports for all standard pipeline stages."""

    normalization_report = validate_case(case, include_baseline_checks=False)
    baseline_report = validate_case(case, include_baseline_checks=True)
    simulation_report = validate_case(
        case,
        include_baseline_checks=True,
        include_simulation_checks=True,
    )
    analysis_report = validate_case(
        case,
        include_baseline_checks=True,
        include_analysis_checks=True,
    )
    normalization_valid = normalization_report.is_valid
    baseline_runnable = normalization_valid and baseline_report.is_valid
    simulation_ready = baseline_runnable and simulation_report.is_valid
    analysis_ready = baseline_runnable and analysis_report.is_valid
    return CaseReadinessReport(
        schema_valid=True,
        normalization_valid=normalization_valid,
        baseline_runnable=baseline_runnable,
        simulation_ready=simulation_ready,
        analysis_ready=analysis_ready,
        normalization_report=normalization_report,
        baseline_report=baseline_report,
        simulation_report=simulation_report,
        analysis_report=analysis_report,
    )
