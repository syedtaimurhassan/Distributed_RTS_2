"""Metric and artifact-table collection helpers for simulation runs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean

from drts_tsn.domain.case import Case
from drts_tsn.domain.enums import ResultStatus
from drts_tsn.domain.results import SimulationStreamResult
from drts_tsn.simulation.model.network_state import NetworkState

from .trace_row_builders import (
    build_hop_summary_row,
    build_queue_summary_row,
    build_run_summary_row,
    build_stream_summary_row,
)


SIMULATION_TABLE_NAMES = (
    "frame_release_trace",
    "enqueue_trace",
    "transmission_trace",
    "forwarding_trace",
    "delivery_trace",
    "response_time_trace",
    "credit_trace",
    "scheduler_decision_trace",
    "stream_summary",
    "hop_summary",
    "queue_summary",
    "run_summary",
)


@dataclass(slots=True)
class MetricCollector:
    """Collect detailed tables and per-stream response-time metrics."""

    tables: dict[str, list[dict[str, object]]] = field(
        default_factory=lambda: {name: [] for name in SIMULATION_TABLE_NAMES}
    )
    frame_response_times_by_stream: dict[str, list[float]] = field(default_factory=dict)
    stream_results: list[SimulationStreamResult] = field(default_factory=list)
    detail_rows: list[dict[str, object]] = field(default_factory=list)

    def record(self, table_name: str, row: dict[str, object]) -> None:
        """Record one row into a named simulation table."""

        self.tables[table_name].append(row)

    def record_frame_response_time(self, stream_id: str, response_time_us: float) -> None:
        """Record an end-to-end response time for one frame instance."""

        self.frame_response_times_by_stream.setdefault(stream_id, []).append(response_time_us)

    def finalize(
        self,
        *,
        case: Case,
        network_state: NetworkState,
        run_id: str,
        engine_status: str,
        stop_reason: str,
        simulated_time_us: float,
        trace_enabled: bool,
    ) -> None:
        """Build summary tables and per-stream result objects from raw rows."""

        self.detail_rows = list(self.tables["transmission_trace"])
        self.stream_results = []
        routes_by_stream = {route.stream_id: route for route in case.routes}
        for table_name in ("stream_summary", "hop_summary", "queue_summary", "run_summary"):
            self.tables[table_name] = []
        for stream in case.streams:
            response_times = self.frame_response_times_by_stream.get(stream.id, [])
            stream_state = network_state.streams[stream.id]
            route = routes_by_stream.get(stream.id)
            status = (
                ResultStatus.OK
                if stream_state.completed_frames == stream_state.released_frames and stream_state.completed_frames > 0
                else ResultStatus.ERROR
            )
            max_response_time_us = max(response_times, default=None)
            mean_response_time_us = mean(response_times) if response_times else None
            self.tables["stream_summary"].append(
                build_stream_summary_row(
                    stream_id=stream.id,
                    traffic_class=stream.traffic_class,
                    route_id=stream.route_id,
                    hop_count=max(len(route.hops) - 1, 0) if route is not None else 0,
                    release_count=stream_state.released_frames,
                    delivery_count=stream_state.completed_frames,
                    max_response_time_us=max_response_time_us,
                    mean_response_time_us=mean_response_time_us,
                    status=status,
                )
            )
            self.stream_results.append(
                SimulationStreamResult(
                    stream_id=stream.id,
                    max_response_time_us=max_response_time_us,
                    frame_count=stream_state.completed_frames,
                    status=status,
                    notes=[
                        f"Released {stream_state.released_frames} frame(s).",
                        f"Delivered {stream_state.completed_frames} frame(s).",
                    ],
                )
            )

        hop_groups: dict[tuple[str, str, int], list[dict[str, object]]] = defaultdict(list)
        for row in self.tables["transmission_trace"]:
            hop_groups[(str(row["stream_id"]), str(row["link_id"]), int(row["hop_index"]))].append(row)
        for (stream_id, link_id, hop_index), rows in sorted(hop_groups.items()):
            self.tables["hop_summary"].append(
                build_hop_summary_row(
                    stream_id=stream_id,
                    link_id=link_id,
                    hop_index=hop_index,
                    transmission_count=len(rows),
                    max_queueing_delay_us=max(float(row["queueing_delay_us"]) for row in rows),
                    max_response_time_so_far_us=max(float(row["response_time_so_far_us"]) for row in rows),
                )
            )

        for port in network_state.ports.values():
            for queue_id, queue_state in port.queues.items():
                credit_state = port.credits.get(queue_id)
                self.tables["queue_summary"].append(
                    build_queue_summary_row(
                        port_id=port.port_id,
                        link_id=port.link_id,
                        queue_id=queue_id,
                        traffic_class=queue_state.traffic_class,
                        enqueued_count=queue_state.enqueued_count,
                        transmitted_count=queue_state.transmitted_count,
                        max_depth=queue_state.max_depth,
                        final_depth=len(queue_state.pending_frame_ids),
                        current_credit=credit_state.current_credit if credit_state is not None else None,
                        next_eligible_time_us=(
                            credit_state.next_eligible_time_us if credit_state is not None else None
                        ),
                    )
                )

        self.tables["run_summary"].append(
            build_run_summary_row(
                case_id=case.metadata.case_id,
                run_id=run_id,
                engine_status=engine_status,
                stop_reason=stop_reason,
                processed_event_count=network_state.statistics.processed_events,
                released_frame_count=network_state.statistics.released_frames,
                delivered_frame_count=network_state.statistics.delivered_frames,
                transmission_count=network_state.statistics.transmitted_frames,
                simulated_time_us=simulated_time_us,
                trace_enabled=trace_enabled,
            )
        )
