"""Build top-level analytical result containers and named output tables."""

from __future__ import annotations

from drts_tsn.domain.case import Case
from drts_tsn.domain.results import AnalysisRunResult, AnalysisStreamResult
from drts_tsn.validation.errors import ValidationIssue


ANALYSIS_SCHEMA_VERSION = "analysis.v1"


ANALYSIS_TABLE_FIELDS: dict[str, list[str]] = {
    "stream_wcrt_summary": [
        "stream_id",
        "route_id",
        "traffic_class",
        "hop_count",
        "deadline_us",
        "end_to_end_wcrt_us",
        "meets_deadline",
        "expected_wcrt_us",
        "analyzed",
        "status",
    ],
    "per_link_wcrt_summary": [
        "stream_id",
        "route_id",
        "link_id",
        "hop_index",
        "traffic_class",
        "transmission_time_us",
        "same_priority_interference_us",
        "lower_priority_interference_us",
        "higher_priority_interference_us",
        "per_link_wcrt_us",
        "reserved_share",
        "reserved_share_up_to_class",
    ],
    "link_interference_trace": [
        "stream_id",
        "link_id",
        "hop_index",
        "traffic_class",
        "same_priority_stream_count",
        "lower_priority_candidate_count",
        "higher_priority_candidate_count",
        "selected_lower_priority_stream_id",
        "selected_higher_priority_stream_id",
        "reserved_share",
        "reserved_share_up_to_class",
    ],
    "same_priority_trace": [
        "stream_id",
        "link_id",
        "hop_index",
        "traffic_class",
        "competitor_stream_id",
        "queued_ahead_count",
        "transmission_time_us",
        "credit_recovery_us",
        "eligible_interval_us",
        "contribution_us",
    ],
    "credit_recovery_trace": [
        "stream_id",
        "link_id",
        "hop_index",
        "traffic_class",
        "source_term",
        "related_stream_id",
        "base_time_us",
        "idle_slope_share",
        "send_slope_share",
        "credit_recovery_us",
    ],
    "lower_priority_trace": [
        "stream_id",
        "link_id",
        "hop_index",
        "traffic_class",
        "competitor_stream_id",
        "competitor_class",
        "transmission_time_us",
        "selected",
    ],
    "higher_priority_trace": [
        "stream_id",
        "link_id",
        "hop_index",
        "traffic_class",
        "competitor_stream_id",
        "competitor_class",
        "transmission_time_us",
        "blocking_credit_recovery_us",
        "selected",
        "contribution_us",
    ],
    "per_link_formula_trace": [
        "stream_id",
        "link_id",
        "hop_index",
        "traffic_class",
        "term_name",
        "term_value_us",
    ],
    "end_to_end_accumulation_trace": [
        "stream_id",
        "route_id",
        "hop_index",
        "link_id",
        "per_link_wcrt_us",
        "cumulative_wcrt_us",
    ],
    "run_summary": [
        "case_id",
        "run_id",
        "analyzed_stream_count",
        "skipped_best_effort_count",
        "per_link_row_count",
        "same_priority_row_count",
        "lower_priority_row_count",
        "higher_priority_row_count",
        "formula_row_count",
        "status",
    ],
}


def _normalize_table_rows(
    table_name: str,
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Project one table onto its declared output contract."""

    fieldnames = ANALYSIS_TABLE_FIELDS[table_name]
    normalized_rows: list[dict[str, object]] = []
    for row in rows:
        extra_fields = sorted(set(row) - set(fieldnames))
        if extra_fields:
            raise ValueError(
                f"Unexpected column(s) in analysis table '{table_name}': {', '.join(extra_fields)}."
            )
        normalized_rows.append({fieldname: row.get(fieldname) for fieldname in fieldnames})
    return normalized_rows


def normalize_analysis_tables(tables: dict[str, list[dict[str, object]]]) -> dict[str, list[dict[str, object]]]:
    """Return analysis tables with stable names, ordering, and columns."""

    unexpected_tables = sorted(set(tables) - set(ANALYSIS_TABLE_FIELDS))
    if unexpected_tables:
        raise ValueError(
            f"Unexpected analysis table(s): {', '.join(unexpected_tables)}."
        )
    return {
        table_name: _normalize_table_rows(table_name, tables.get(table_name, []))
        for table_name in ANALYSIS_TABLE_FIELDS
    }


def _flatten_trace_tables(tables: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    """Flatten named trace tables into one generic trace row list."""

    flattened: list[dict[str, object]] = []
    for table_name in (
        "link_interference_trace",
        "same_priority_trace",
        "credit_recovery_trace",
        "lower_priority_trace",
        "higher_priority_trace",
        "per_link_formula_trace",
        "end_to_end_accumulation_trace",
    ):
        for row in tables.get(table_name, []):
            flattened.append({"trace_table": table_name, **row})
    return flattened


def build_analysis_result(
    *,
    case: Case,
    run_id: str,
    stream_results: list[AnalysisStreamResult],
    tables: dict[str, list[dict[str, object]]],
    precondition_failures: list[ValidationIssue],
) -> AnalysisRunResult:
    """Assemble a serializable analysis result with named CSV table payloads."""

    engine_status = "ok" if not precondition_failures else "preconditions_failed"
    raw_run_summary_rows = tables.get("run_summary", []) or [
        {
            "case_id": case.metadata.case_id,
            "run_id": run_id,
            "analyzed_stream_count": 0,
            "skipped_best_effort_count": 0,
            "per_link_row_count": len(tables.get("per_link_wcrt_summary", [])),
            "same_priority_row_count": len(tables.get("same_priority_trace", [])),
            "lower_priority_row_count": len(tables.get("lower_priority_trace", [])),
            "higher_priority_row_count": len(tables.get("higher_priority_trace", [])),
            "formula_row_count": len(tables.get("per_link_formula_trace", [])),
            "status": engine_status,
        }
    ]
    run_summary_rows = [
        {
            **row,
            "run_id": run_id,
            "status": engine_status,
        }
        for row in raw_run_summary_rows
    ]
    normalized_tables = normalize_analysis_tables(
        {
            **tables,
            "run_summary": run_summary_rows,
        }
    )
    precondition_failure_rows = [
        {
            "code": issue.code,
            "location": issue.location,
            "message": issue.message,
            "severity": issue.severity,
        }
        for issue in precondition_failures
    ]
    return AnalysisRunResult(
        case_id=case.metadata.case_id,
        run_id=run_id,
        stream_results=stream_results,
        detail_rows=normalized_tables.get("per_link_wcrt_summary", []),
        summary={
            "schema_version": ANALYSIS_SCHEMA_VERSION,
            "engine_status": engine_status,
            "stream_count": len(stream_results),
            "analyzed_stream_count": sum(
                1 for row in normalized_tables.get("stream_wcrt_summary", []) if row.get("analyzed")
            ),
            "detail_row_count": len(normalized_tables.get("per_link_wcrt_summary", [])),
            "precondition_failure_count": len(precondition_failures),
            "precondition_failures": precondition_failure_rows,
        },
        trace_rows=_flatten_trace_tables(normalized_tables),
        tables=normalized_tables,
    )
