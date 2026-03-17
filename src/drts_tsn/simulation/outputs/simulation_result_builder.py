"""Build top-level simulation result containers from collectors."""

from __future__ import annotations

from drts_tsn.domain.case import Case
from drts_tsn.domain.results import SimulationRunResult
from drts_tsn.simulation.model.network_state import NetworkState

from .metric_collector import MetricCollector
from .trace_collector import TraceCollector


SIMULATION_SCHEMA_VERSION = "simulation.v2"


SIMULATION_TABLE_FIELDS: dict[str, list[str]] = {
    "frame_release_trace": [
        "timestamp_us",
        "stream_id",
        "frame_id",
        "route_id",
        "release_index",
        "traffic_class",
        "frame_size_bytes",
    ],
    "enqueue_trace": [
        "timestamp_us",
        "stream_id",
        "frame_id",
        "port_id",
        "link_id",
        "queue_id",
        "traffic_class",
        "hop_index",
        "queue_depth",
    ],
    "transmission_trace": [
        "stream_id",
        "frame_id",
        "port_id",
        "link_id",
        "queue_id",
        "hop_index",
        "traffic_class",
        "release_time_us",
        "enqueue_time_us",
        "start_time_us",
        "end_time_us",
        "queueing_delay_us",
        "transmission_time_us",
        "response_time_so_far_us",
        "credit_before",
        "credit_after",
        "service_spacing_us",
    ],
    "forwarding_trace": [
        "timestamp_us",
        "stream_id",
        "frame_id",
        "from_link_id",
        "to_link_id",
        "from_hop_index",
        "to_hop_index",
    ],
    "delivery_trace": [
        "timestamp_us",
        "stream_id",
        "frame_id",
        "route_id",
        "release_index",
        "hop_count",
        "release_time_us",
        "delivery_time_us",
    ],
    "response_time_trace": [
        "stream_id",
        "frame_id",
        "release_index",
        "release_time_us",
        "delivery_time_us",
        "response_time_us",
        "deadline_us",
        "meets_deadline",
    ],
    "credit_trace": [
        "timestamp_us",
        "port_id",
        "link_id",
        "queue_id",
        "traffic_class",
        "credit_before",
        "credit_after",
        "change_reason",
        "slope_mbps",
        "elapsed_time_us",
        "related_frame_id",
        "blocking_frame_id",
        "transmitting_frame_id",
        "capped_at_zero",
    ],
    "scheduler_decision_trace": [
        "timestamp_us",
        "port_id",
        "link_id",
        "class_a_head_frame_id",
        "class_a_queue_depth",
        "class_a_credit",
        "class_b_head_frame_id",
        "class_b_queue_depth",
        "class_b_credit",
        "be_head_frame_id",
        "be_queue_depth",
        "current_transmission_frame_id",
        "selected_queue_id",
        "selected_frame_id",
        "selected_traffic_class",
        "decision_reason",
    ],
    "stream_summary": [
        "stream_id",
        "traffic_class",
        "release_count",
        "delivery_count",
        "max_response_time_us",
        "mean_response_time_us",
        "status",
    ],
    "hop_summary": [
        "stream_id",
        "link_id",
        "hop_index",
        "transmission_count",
        "max_queueing_delay_us",
        "max_response_time_so_far_us",
    ],
    "queue_summary": [
        "port_id",
        "link_id",
        "queue_id",
        "traffic_class",
        "enqueued_count",
        "transmitted_count",
        "max_depth",
        "final_depth",
        "current_credit",
        "next_eligible_time_us",
    ],
    "run_summary": [
        "case_id",
        "run_id",
        "engine_status",
        "stop_reason",
        "processed_event_count",
        "released_frame_count",
        "delivered_frame_count",
        "transmission_count",
        "simulated_time_us",
        "trace_enabled",
    ],
}


def _normalize_table_rows(
    table_name: str,
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Project one table onto its declared output contract."""

    fieldnames = SIMULATION_TABLE_FIELDS[table_name]
    normalized_rows: list[dict[str, object]] = []
    for row in rows:
        extra_fields = sorted(set(row) - set(fieldnames))
        if extra_fields:
            raise ValueError(
                f"Unexpected column(s) in simulation table '{table_name}': {', '.join(extra_fields)}."
            )
        normalized_rows.append({fieldname: row.get(fieldname) for fieldname in fieldnames})
    return normalized_rows


def normalize_simulation_tables(tables: dict[str, list[dict[str, object]]]) -> dict[str, list[dict[str, object]]]:
    """Return simulation tables with stable names, ordering, and columns."""

    unexpected_tables = sorted(set(tables) - set(SIMULATION_TABLE_FIELDS))
    if unexpected_tables:
        raise ValueError(f"Unexpected simulation table(s): {', '.join(unexpected_tables)}.")
    return {
        table_name: _normalize_table_rows(table_name, tables.get(table_name, []))
        for table_name in SIMULATION_TABLE_FIELDS
    }


def build_simulation_result(
    *,
    case: Case,
    run_id: str,
    metric_collector: MetricCollector,
    network_state: NetworkState,
    trace_collector: TraceCollector,
    engine_status: str,
    simulated_time_us: float,
) -> SimulationRunResult:
    """Assemble a serializable simulation result."""

    stop_reason = network_state.statistics.stop_reason or "completed"
    metric_collector.finalize(
        case=case,
        network_state=network_state,
        run_id=run_id,
        engine_status=engine_status,
        stop_reason=stop_reason,
        simulated_time_us=simulated_time_us,
        trace_enabled=trace_collector.enabled,
    )
    normalized_tables = normalize_simulation_tables(metric_collector.tables)
    simulated_time_us = float(normalized_tables["run_summary"][0]["simulated_time_us"])
    return SimulationRunResult(
        case_id=case.metadata.case_id,
        run_id=run_id,
        stream_results=metric_collector.stream_results,
        detail_rows=normalized_tables.get("transmission_trace", []),
        summary={
            "schema_version": SIMULATION_SCHEMA_VERSION,
            "engine_status": engine_status,
            "stream_count": len(case.streams),
            "detail_row_count": len(normalized_tables.get("transmission_trace", [])),
            "simulated_time_us": simulated_time_us,
            "trace_enabled": trace_collector.enabled,
            "stop_reason": stop_reason,
            "processed_event_count": network_state.statistics.processed_events,
            "delivery_count": network_state.statistics.delivered_frames,
        },
        trace_rows=trace_collector.rows(),
        tables=normalized_tables,
    )
