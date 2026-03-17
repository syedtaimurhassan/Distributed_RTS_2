"""Row builders for stable analytical CSV outputs."""

from __future__ import annotations

from drts_tsn.analysis.formulas.higher_priority_interference import HigherPriorityTerm
from drts_tsn.analysis.formulas.lower_priority_interference import LowerPriorityTerm
from drts_tsn.analysis.formulas.same_priority_interference import SamePriorityTerm
from drts_tsn.analysis.link_model import LinkTrafficContext
from drts_tsn.domain.enums import ResultStatus


def build_per_link_summary_row(
    context: LinkTrafficContext,
    *,
    same_priority_interference_us: float,
    lower_priority_interference_us: float,
    higher_priority_interference_us: float,
    per_link_wcrt_us: float,
) -> dict[str, object]:
    """Return the per-link WCRT summary row."""

    return {
        "stream_id": context.stream_id,
        "route_id": context.route_id,
        "link_id": context.link_id,
        "hop_index": context.hop_index,
        "traffic_class": context.traffic_class.value,
        "transmission_time_us": context.transmission_time_us,
        "same_priority_interference_us": same_priority_interference_us,
        "lower_priority_interference_us": lower_priority_interference_us,
        "higher_priority_interference_us": higher_priority_interference_us,
        "per_link_wcrt_us": per_link_wcrt_us,
        "reserved_share": context.reserved_share,
        "reserved_share_up_to_class": context.reserved_share_up_to_class,
    }


def build_link_interference_trace_row(
    context: LinkTrafficContext,
    *,
    selected_lower_priority_stream_id: str | None,
    selected_higher_priority_stream_id: str | None,
) -> dict[str, object]:
    """Return one link-level interference summary row."""

    return {
        "stream_id": context.stream_id,
        "link_id": context.link_id,
        "hop_index": context.hop_index,
        "traffic_class": context.traffic_class.value,
        "same_priority_stream_count": len(context.same_priority_flows),
        "lower_priority_candidate_count": len(context.lower_priority_flows),
        "higher_priority_candidate_count": len(context.higher_priority_flows),
        "selected_lower_priority_stream_id": selected_lower_priority_stream_id or "",
        "selected_higher_priority_stream_id": selected_higher_priority_stream_id or "",
        "reserved_share": context.reserved_share,
        "reserved_share_up_to_class": context.reserved_share_up_to_class,
    }


def build_same_priority_trace_row(context: LinkTrafficContext, term: SamePriorityTerm) -> dict[str, object]:
    """Return one same-priority interference trace row."""

    return {
        "stream_id": context.stream_id,
        "link_id": context.link_id,
        "hop_index": context.hop_index,
        "traffic_class": context.traffic_class.value,
        "competitor_stream_id": term.competitor_stream_id,
        "queued_ahead_count": term.queued_ahead_count,
        "transmission_time_us": term.transmission_time_us,
        "credit_recovery_us": term.credit_recovery_us,
        "eligible_interval_us": term.eligible_interval_us,
        "contribution_us": term.contribution_us,
    }


def build_credit_recovery_trace_row(
    context: LinkTrafficContext,
    *,
    source_term: str,
    related_stream_id: str,
    base_time_us: float,
    idle_slope_share: float,
    send_slope_share: float,
    credit_recovery_us: float,
) -> dict[str, object]:
    """Return one credit-recovery trace row."""

    return {
        "stream_id": context.stream_id,
        "link_id": context.link_id,
        "hop_index": context.hop_index,
        "traffic_class": context.traffic_class.value,
        "source_term": source_term,
        "related_stream_id": related_stream_id,
        "base_time_us": base_time_us,
        "idle_slope_share": idle_slope_share,
        "send_slope_share": send_slope_share,
        "credit_recovery_us": credit_recovery_us,
    }


def build_lower_priority_trace_row(context: LinkTrafficContext, term: LowerPriorityTerm) -> dict[str, object]:
    """Return one lower-priority blocking trace row."""

    return {
        "stream_id": context.stream_id,
        "link_id": context.link_id,
        "hop_index": context.hop_index,
        "traffic_class": context.traffic_class.value,
        "competitor_stream_id": term.competitor_stream_id,
        "competitor_class": term.competitor_class,
        "transmission_time_us": term.transmission_time_us,
        "selected": term.selected,
    }


def build_higher_priority_trace_row(context: LinkTrafficContext, term: HigherPriorityTerm) -> dict[str, object]:
    """Return one higher-priority interference trace row."""

    return {
        "stream_id": context.stream_id,
        "link_id": context.link_id,
        "hop_index": context.hop_index,
        "traffic_class": context.traffic_class.value,
        "competitor_stream_id": term.competitor_stream_id,
        "competitor_class": term.competitor_class,
        "transmission_time_us": term.transmission_time_us,
        "blocking_credit_recovery_us": term.blocking_credit_recovery_us,
        "selected": term.selected,
        "contribution_us": term.contribution_us,
    }


def build_formula_trace_row(
    context: LinkTrafficContext,
    *,
    term_name: str,
    term_value_us: float,
) -> dict[str, object]:
    """Return one per-link formula component trace row."""

    return {
        "stream_id": context.stream_id,
        "link_id": context.link_id,
        "hop_index": context.hop_index,
        "traffic_class": context.traffic_class.value,
        "term_name": term_name,
        "term_value_us": term_value_us,
    }


def build_end_to_end_accumulation_row(
    *,
    stream_id: str,
    route_id: str,
    hop_index: int,
    link_id: str,
    per_link_wcrt_us: float,
    cumulative_wcrt_us: float,
) -> dict[str, object]:
    """Return one end-to-end accumulation trace row."""

    return {
        "stream_id": stream_id,
        "route_id": route_id,
        "hop_index": hop_index,
        "link_id": link_id,
        "per_link_wcrt_us": per_link_wcrt_us,
        "cumulative_wcrt_us": cumulative_wcrt_us,
    }


def build_stream_summary_row(
    *,
    stream_id: str,
    route_id: str,
    traffic_class: str,
    hop_count: int,
    deadline_us: float,
    end_to_end_wcrt_us: float | None,
    analyzed: bool,
    expected_wcrt_us: float | None,
    status: ResultStatus,
) -> dict[str, object]:
    """Return one stream-level WCRT summary row."""

    return {
        "stream_id": stream_id,
        "route_id": route_id,
        "traffic_class": traffic_class,
        "hop_count": hop_count,
        "deadline_us": deadline_us,
        "end_to_end_wcrt_us": end_to_end_wcrt_us,
        "meets_deadline": (
            end_to_end_wcrt_us <= deadline_us
            if end_to_end_wcrt_us is not None and analyzed
            else None
        ),
        "expected_wcrt_us": expected_wcrt_us,
        "analyzed": analyzed,
        "status": status.value,
    }


def build_run_summary_row(
    *,
    case_id: str,
    run_id: str,
    analyzed_stream_count: int,
    skipped_best_effort_count: int,
    per_link_row_count: int,
    same_priority_row_count: int,
    lower_priority_row_count: int,
    higher_priority_row_count: int,
    formula_row_count: int,
    status: str,
) -> dict[str, object]:
    """Return one analysis run summary row."""

    return {
        "case_id": case_id,
        "run_id": run_id,
        "analyzed_stream_count": analyzed_stream_count,
        "skipped_best_effort_count": skipped_best_effort_count,
        "per_link_row_count": per_link_row_count,
        "same_priority_row_count": same_priority_row_count,
        "lower_priority_row_count": lower_priority_row_count,
        "higher_priority_row_count": higher_priority_row_count,
        "formula_row_count": formula_row_count,
        "status": status,
    }
