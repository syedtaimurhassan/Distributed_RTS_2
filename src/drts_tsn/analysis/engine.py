"""Top-level analytical AVB WCRT engine for the baseline project scope."""

from __future__ import annotations

from drts_tsn.common.time_utils import utc_timestamp_compact
from drts_tsn.domain.case import Case
from drts_tsn.domain.results import AnalysisRunResult

from .config import AnalysisConfig
from .outputs.analysis_result_builder import build_analysis_result
from .preconditions import AnalysisPreconditionError, check_preconditions
from .services.end_to_end_analysis_service import analyze_case_end_to_end


class AnalysisEngine:
    """Compute analytical AVB WCRT bounds from the normalized case model."""

    def run(self, case: Case, config: AnalysisConfig | None = None) -> AnalysisRunResult:
        """Run the baseline analytical engine and return structured outputs."""

        active_config = config or AnalysisConfig()
        failures = check_preconditions(case)
        run_id = f"ana-{utc_timestamp_compact()}"
        if failures and active_config.strict_validation:
            raise AnalysisPreconditionError(failures)
        if failures:
            return build_analysis_result(
                case=case,
                run_id=run_id,
                stream_results=[],
                tables={},
                precondition_failures=failures,
            )

        stream_results, tables = analyze_case_end_to_end(case)
        return build_analysis_result(
            case=case,
            run_id=run_id,
            stream_results=stream_results,
            tables=tables,
            precondition_failures=failures,
        )
