"""Per-link AVB WCRT analysis service for the baseline model."""

from __future__ import annotations

from dataclasses import dataclass, field

from drts_tsn.analysis.formulas.bandwidth_checks import reserved_bandwidth_feasible
from drts_tsn.analysis.formulas.class_a_wcrt import compute_class_a_wcrt_us
from drts_tsn.analysis.formulas.class_b_wcrt import compute_class_b_wcrt_us
from drts_tsn.analysis.formulas.higher_priority_interference import compute_higher_priority_interference
from drts_tsn.analysis.formulas.lower_priority_interference import compute_lower_priority_interference
from drts_tsn.analysis.formulas.same_priority_interference import compute_same_priority_interference
from drts_tsn.analysis.link_model import LinkTrafficContext
from drts_tsn.analysis.outputs.explanation_row_builders import (
    build_credit_recovery_trace_row,
    build_formula_trace_row,
    build_higher_priority_trace_row,
    build_link_interference_trace_row,
    build_lower_priority_trace_row,
    build_per_link_summary_row,
    build_same_priority_trace_row,
)
from drts_tsn.domain.enums import TrafficClass


@dataclass(slots=True)
class PerLinkAnalysisOutput:
    """Structured per-link analytical outputs and trace tables."""

    per_link_row: dict[str, object]
    link_interference_row: dict[str, object]
    same_priority_rows: list[dict[str, object]] = field(default_factory=list)
    credit_recovery_rows: list[dict[str, object]] = field(default_factory=list)
    lower_priority_rows: list[dict[str, object]] = field(default_factory=list)
    higher_priority_rows: list[dict[str, object]] = field(default_factory=list)
    formula_rows: list[dict[str, object]] = field(default_factory=list)
    per_link_wcrt_us: float = 0.0


def _require_flow_parameter(
    flow_parameters_by_stream_id: dict[str, tuple[float, float]],
    *,
    stream_id: str,
    context: LinkTrafficContext,
) -> tuple[float, float]:
    """Return cached reserved/send shares or raise a contextual error."""

    parameters = flow_parameters_by_stream_id.get(stream_id)
    if parameters is None:
        raise ValueError(
            f"Missing analytical flow parameters for stream '{stream_id}' while processing "
            f"stream '{context.stream_id}' on link '{context.link_id}'."
        )
    return parameters


def analyze_link(context: LinkTrafficContext) -> PerLinkAnalysisOutput:
    """Return the baseline per-link AVB WCRT breakdown and trace rows."""

    if not reserved_bandwidth_feasible(context.reserved_share_up_to_class):
        raise ValueError(
            "Reserved bandwidth exceeds 1.0 in per-link analysis context: "
            f"stream='{context.stream_id}', class='{context.traffic_class.value}', "
            f"link='{context.link_id}', "
            f"reserved_share={context.reserved_share:.6f}, "
            f"reserved_share_up_to_class={context.reserved_share_up_to_class:.6f}."
        )
    try:
        same_priority = compute_same_priority_interference(
            analyzed_deadline_us=context.deadline_us,
            analyzed_period_us=context.period_us,
            same_priority_flows=context.same_priority_flows,
        )
        lower_priority = compute_lower_priority_interference(context.lower_priority_flows)
        higher_priority = compute_higher_priority_interference(
            analyzed_class=context.traffic_class,
            higher_priority_flows=context.higher_priority_flows,
            lower_priority_blocking_us=lower_priority.total_us,
        )

        if context.traffic_class == TrafficClass.CLASS_A:
            per_link_wcrt_us = compute_class_a_wcrt_us(
                transmission_time_us=context.transmission_time_us,
                same_priority_interference_us=same_priority.total_us,
                lower_priority_interference_us=lower_priority.total_us,
            )
        elif context.traffic_class == TrafficClass.CLASS_B:
            per_link_wcrt_us = compute_class_b_wcrt_us(
                transmission_time_us=context.transmission_time_us,
                same_priority_interference_us=same_priority.total_us,
                lower_priority_interference_us=lower_priority.total_us,
                higher_priority_interference_us=higher_priority.total_us,
            )
        else:  # pragma: no cover - guarded upstream
            raise ValueError("Best-effort traffic is excluded from analytical WCRT computation.")
    except ValueError as exc:
        raise ValueError(
            "Per-link analytical computation failed: "
            f"stream='{context.stream_id}', class='{context.traffic_class.value}', "
            f"link='{context.link_id}', hop_index={context.hop_index}. "
            f"Cause: {exc}"
        ) from exc

    same_priority_parameters = {
        flow.stream_id: (flow.reserved_share, flow.send_slope_share)
        for flow in context.same_priority_flows
    }
    higher_priority_parameters = {
        flow.stream_id: (flow.reserved_share, flow.send_slope_share)
        for flow in context.higher_priority_flows
    }
    same_priority_rows = [
        build_same_priority_trace_row(context, term)
        for term in same_priority.terms
    ]
    credit_recovery_rows = [
        build_credit_recovery_trace_row(
            context,
            source_term="same_priority",
            related_stream_id=term.competitor_stream_id,
            base_time_us=term.transmission_time_us,
            idle_slope_share=_require_flow_parameter(
                same_priority_parameters,
                stream_id=term.competitor_stream_id,
                context=context,
            )[0],
            send_slope_share=_require_flow_parameter(
                same_priority_parameters,
                stream_id=term.competitor_stream_id,
                context=context,
            )[1],
            credit_recovery_us=term.credit_recovery_us,
        )
        for term in same_priority.terms
    ]
    lower_priority_rows = [
        build_lower_priority_trace_row(context, term)
        for term in lower_priority.terms
    ]
    higher_priority_rows = [
        build_higher_priority_trace_row(context, term)
        for term in higher_priority.terms
    ]
    for term in higher_priority.terms:
        if term.blocking_credit_recovery_us > 0:
            idle_slope_share, send_slope_share = _require_flow_parameter(
                higher_priority_parameters,
                stream_id=term.competitor_stream_id,
                context=context,
            )
            credit_recovery_rows.append(
                build_credit_recovery_trace_row(
                    context,
                    source_term="higher_priority_blocking",
                    related_stream_id=term.competitor_stream_id,
                    base_time_us=lower_priority.total_us,
                    idle_slope_share=idle_slope_share,
                    send_slope_share=send_slope_share,
                    credit_recovery_us=term.blocking_credit_recovery_us,
                )
            )

    formula_rows = [
        build_formula_trace_row(
            context,
            term_name="Ci",
            term_value_us=context.transmission_time_us,
        ),
        build_formula_trace_row(
            context,
            term_name="SPI",
            term_value_us=same_priority.total_us,
        ),
        build_formula_trace_row(
            context,
            term_name="LPI",
            term_value_us=lower_priority.total_us,
        ),
        build_formula_trace_row(
            context,
            term_name="HPI",
            term_value_us=higher_priority.total_us,
        ),
        build_formula_trace_row(
            context,
            term_name="W_link",
            term_value_us=per_link_wcrt_us,
        ),
    ]

    return PerLinkAnalysisOutput(
        per_link_row=build_per_link_summary_row(
            context,
            same_priority_interference_us=same_priority.total_us,
            lower_priority_interference_us=lower_priority.total_us,
            higher_priority_interference_us=higher_priority.total_us,
            per_link_wcrt_us=per_link_wcrt_us,
        ),
        link_interference_row=build_link_interference_trace_row(
            context,
            selected_lower_priority_stream_id=lower_priority.selected_stream_id,
            selected_higher_priority_stream_id=higher_priority.selected_stream_id,
        ),
        same_priority_rows=same_priority_rows,
        credit_recovery_rows=credit_recovery_rows,
        lower_priority_rows=lower_priority_rows,
        higher_priority_rows=higher_priority_rows,
        formula_rows=formula_rows,
        per_link_wcrt_us=per_link_wcrt_us,
    )
