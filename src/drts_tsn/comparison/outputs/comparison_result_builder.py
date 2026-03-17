"""Builders for top-level comparison result containers and named tables."""

from __future__ import annotations

from drts_tsn.domain.results import ComparisonEntry, ComparisonRunResult

from .comparison_row_builders import build_expected_wcrt_row, build_stream_comparison_row


COMPARISON_SCHEMA_VERSION = "comparison.v1"


COMPARISON_TABLE_FIELDS: dict[str, list[str]] = {
    "stream_comparison": [
        "stream_id",
        "analysis_traffic_class",
        "simulation_traffic_class",
        "analysis_route_id",
        "simulation_route_id",
        "analysis_hop_count",
        "simulation_hop_count",
        "analytical_wcrt_us",
        "simulated_worst_response_time_us",
        "expected_wcrt_us",
        "absolute_difference_us",
        "analysis_minus_simulation_margin_us",
        "analysis_to_simulation_ratio",
        "simulation_exceeded_analysis",
        "class_mismatch",
        "path_mismatch",
        "status",
        "discrepancy_flags",
        "notes",
    ],
    "aggregate_comparison": [
        "case_id",
        "run_id",
        "analysis_run_id",
        "simulation_run_id",
        "engine_status",
        "stream_count",
        "matched_stream_count",
        "missing_analysis_count",
        "missing_simulation_count",
        "duplicate_analysis_count",
        "duplicate_simulation_count",
        "simulation_exceeded_analysis_count",
        "reference_row_count",
        "max_absolute_difference_us",
        "max_simulation_over_analysis_us",
    ],
    "comparison_diagnostics": [
        "diagnostic_code",
        "severity",
        "stream_id",
        "source",
        "message",
    ],
    "expected_wcrt_comparison": [
        "stream_id",
        "expected_wcrt_us",
        "analytical_wcrt_us",
        "simulated_worst_response_time_us",
        "expected_minus_analysis_us",
        "expected_minus_simulation_us",
        "status",
        "discrepancy_flags",
        "notes",
    ],
}


def _normalize_table_rows(
    table_name: str,
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Project one table onto its declared output contract."""

    fieldnames = COMPARISON_TABLE_FIELDS[table_name]
    normalized_rows: list[dict[str, object]] = []
    for row in rows:
        extra_fields = sorted(set(row) - set(fieldnames))
        if extra_fields:
            raise ValueError(
                f"Unexpected column(s) in comparison table '{table_name}': {', '.join(extra_fields)}."
            )
        normalized_rows.append({fieldname: row.get(fieldname) for fieldname in fieldnames})
    return normalized_rows


def normalize_comparison_tables(
    tables: dict[str, list[dict[str, object]]],
) -> dict[str, list[dict[str, object]]]:
    """Return comparison tables with stable names, ordering, and columns."""

    unexpected_tables = sorted(set(tables) - set(COMPARISON_TABLE_FIELDS))
    if unexpected_tables:
        raise ValueError(f"Unexpected comparison table(s): {', '.join(unexpected_tables)}.")
    return {
        table_name: _normalize_table_rows(table_name, tables.get(table_name, []))
        for table_name in COMPARISON_TABLE_FIELDS
    }


def comparison_entries_to_rows(entries: list[ComparisonEntry]) -> list[dict[str, object]]:
    """Return flat per-stream comparison rows."""

    return [build_stream_comparison_row(entry) for entry in entries]


def expected_wcrt_rows(entries: list[ComparisonEntry]) -> list[dict[str, object]]:
    """Return rows for streams that have expected/reference WCRT values."""

    return [
        build_expected_wcrt_row(entry)
        for entry in entries
        if entry.expected_wcrt_us is not None
    ]


def build_comparison_tables(
    *,
    result: ComparisonRunResult,
    analysis_run_id: str,
    simulation_run_id: str,
) -> dict[str, list[dict[str, object]]]:
    """Build stable comparison table payloads from a comparison result."""

    return normalize_comparison_tables(
        {
            "stream_comparison": comparison_entries_to_rows(result.entries),
            "aggregate_comparison": [
                {
                    "case_id": result.case_id,
                    "run_id": result.run_id,
                    "analysis_run_id": analysis_run_id,
                    "simulation_run_id": simulation_run_id,
                    "engine_status": result.summary.get("engine_status"),
                    "stream_count": result.summary.get("stream_count"),
                    "matched_stream_count": result.summary.get("matched_stream_count"),
                    "missing_analysis_count": result.summary.get("missing_analysis_count"),
                    "missing_simulation_count": result.summary.get("missing_simulation_count"),
                    "duplicate_analysis_count": result.summary.get("duplicate_analysis_count"),
                    "duplicate_simulation_count": result.summary.get("duplicate_simulation_count"),
                    "simulation_exceeded_analysis_count": result.summary.get(
                        "simulation_exceeded_analysis_count"
                    ),
                    "reference_row_count": result.summary.get("reference_row_count"),
                    "max_absolute_difference_us": result.summary.get("max_absolute_difference_us"),
                    "max_simulation_over_analysis_us": result.summary.get(
                        "max_simulation_over_analysis_us"
                    ),
                }
            ],
            "comparison_diagnostics": list(result.diagnostics),
            "expected_wcrt_comparison": expected_wcrt_rows(result.entries),
        }
    )
