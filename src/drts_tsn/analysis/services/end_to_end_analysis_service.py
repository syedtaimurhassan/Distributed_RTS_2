"""End-to-end AVB WCRT analysis service for normalized baseline cases."""

from __future__ import annotations

from collections import defaultdict

from drts_tsn.analysis.end_to_end import accumulate_link_delays, aggregate_link_delays
from drts_tsn.analysis.link_model import LinkTrafficContext, build_link_traffic_contexts
from drts_tsn.analysis.outputs.explanation_row_builders import (
    build_end_to_end_accumulation_row,
    build_run_summary_row,
    build_stream_summary_row,
)
from drts_tsn.analysis.services.expected_result_loader import load_expected_results
from drts_tsn.analysis.services.per_link_analysis_service import analyze_link
from drts_tsn.domain.case import Case
from drts_tsn.domain.enums import ResultStatus, TrafficClass
from drts_tsn.domain.results import AnalysisStreamResult


def analyze_case_end_to_end(
    case: Case,
) -> tuple[list[AnalysisStreamResult], dict[str, list[dict[str, object]]]]:
    """Return analytical stream results plus named output tables."""

    contexts = build_link_traffic_contexts(case)
    contexts_by_stream: dict[str, list[LinkTrafficContext]] = defaultdict(list)
    for context in contexts:
        contexts_by_stream[context.stream_id].append(context)

    expected_results = load_expected_results(case)
    tables: dict[str, list[dict[str, object]]] = {
        "stream_wcrt_summary": [],
        "per_link_wcrt_summary": [],
        "link_interference_trace": [],
        "same_priority_trace": [],
        "credit_recovery_trace": [],
        "lower_priority_trace": [],
        "higher_priority_trace": [],
        "per_link_formula_trace": [],
        "end_to_end_accumulation_trace": [],
        "run_summary": [],
    }
    stream_results: list[AnalysisStreamResult] = []
    analyzed_stream_count = 0
    skipped_best_effort_count = 0

    for stream in case.streams:
        route_id = stream.route_id or stream.id
        if stream.traffic_class == TrafficClass.BEST_EFFORT:
            skipped_best_effort_count += 1
            stream_results.append(
                AnalysisStreamResult(
                    stream_id=stream.id,
                    wcrt_us=None,
                    status=ResultStatus.OK,
                    notes=["Best-effort traffic is excluded from the analytical AVB baseline."],
                )
            )
            continue

        analyzed_stream_count += 1
        stream_contexts = contexts_by_stream.get(stream.id, [])
        if not stream_contexts:
            raise ValueError(
                f"No analytical link contexts were generated for AVB stream '{stream.id}'. "
                "Ensure the stream route resolves to at least one directed link."
            )
        per_link_outputs = [analyze_link(context) for context in stream_contexts]
        per_link_wcrts = [output.per_link_wcrt_us for output in per_link_outputs]
        end_to_end_wcrt_us = aggregate_link_delays(per_link_wcrts)
        stream_results.append(
            AnalysisStreamResult(
                stream_id=stream.id,
                wcrt_us=end_to_end_wcrt_us,
                status=ResultStatus.OK,
                notes=[f"Computed across {len(per_link_outputs)} link(s)."],
            )
        )
        tables["stream_wcrt_summary"].append(
            build_stream_summary_row(
                stream_id=stream.id,
                route_id=route_id,
                traffic_class=stream.traffic_class.value,
                hop_count=len(per_link_outputs),
                deadline_us=stream.deadline_us,
                end_to_end_wcrt_us=end_to_end_wcrt_us,
                analyzed=True,
                expected_wcrt_us=expected_results.get(stream.id),
                status=ResultStatus.OK,
            )
        )

        cumulative_wcrts = accumulate_link_delays(per_link_wcrts)
        for output, cumulative_wcrt_us in zip(per_link_outputs, cumulative_wcrts, strict=False):
            per_link_row = output.per_link_row
            tables["per_link_wcrt_summary"].append(per_link_row)
            tables["link_interference_trace"].append(output.link_interference_row)
            tables["same_priority_trace"].extend(output.same_priority_rows)
            tables["credit_recovery_trace"].extend(output.credit_recovery_rows)
            tables["lower_priority_trace"].extend(output.lower_priority_rows)
            tables["higher_priority_trace"].extend(output.higher_priority_rows)
            tables["per_link_formula_trace"].extend(output.formula_rows)
            tables["end_to_end_accumulation_trace"].append(
                build_end_to_end_accumulation_row(
                    stream_id=stream.id,
                    route_id=route_id,
                    hop_index=int(per_link_row["hop_index"]),
                    link_id=str(per_link_row["link_id"]),
                    per_link_wcrt_us=float(per_link_row["per_link_wcrt_us"]),
                    cumulative_wcrt_us=cumulative_wcrt_us,
                )
            )

    tables["run_summary"].append(
        build_run_summary_row(
            case_id=case.metadata.case_id,
            run_id="pending",
            analyzed_stream_count=analyzed_stream_count,
            skipped_best_effort_count=skipped_best_effort_count,
            per_link_row_count=len(tables["per_link_wcrt_summary"]),
            same_priority_row_count=len(tables["same_priority_trace"]),
            lower_priority_row_count=len(tables["lower_priority_trace"]),
            higher_priority_row_count=len(tables["higher_priority_trace"]),
            formula_row_count=len(tables["per_link_formula_trace"]),
            status="ok",
        )
    )
    return stream_results, tables
