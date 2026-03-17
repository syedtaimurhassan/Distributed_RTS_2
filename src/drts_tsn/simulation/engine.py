"""Top-level discrete-event simulation engine for the simplified TSN baseline."""

from __future__ import annotations

from drts_tsn.common.time_utils import utc_timestamp_compact
from drts_tsn.domain.case import Case
from drts_tsn.domain.results import SimulationRunResult

from .config import SimulationConfig
from .context import SimulationContext, build_simulation_context
from .dispatcher import dispatch_event
from .event_types import SimulationEventType
from .outputs.simulation_result_builder import build_simulation_result
from .services.credit_service import synchronize_port_credits
from .services.stop_condition_service import should_stop


class SimulationEngine:
    """Run the baseline line-topology simulator using next-event time advance."""

    def _schedule_initial_releases(self, case: Case, context: SimulationContext) -> None:
        """Seed the event list with initial frame releases for all streams."""

        for stream in case.streams:
            context.event_queue.push(
                0.0,
                SimulationEventType.RELEASE_FRAME.value,
                {"stream_id": stream.id},
            )
            context.network_state.statistics.scheduled_events += 1

    def run(self, case: Case, config: SimulationConfig | None = None) -> SimulationRunResult:
        """Run the baseline discrete-event simulator and return structured artifacts."""

        active_config = config or SimulationConfig()
        context = build_simulation_context(case, active_config)
        run_id = utc_timestamp_compact()
        engine_status = "ok"

        context.trace_collector.record(
            timestamp_us=0.0,
            event_type="simulation_start",
            description="Simulation baseline started.",
            attributes={"case_id": case.metadata.case_id},
        )
        self._schedule_initial_releases(case, context)

        while not context.event_queue.is_empty():
            if should_stop(context):
                engine_status = "stopped"
                break

            next_event = context.event_queue.peek()
            if next_event is None:
                break
            if active_config.time_limit_us is not None and next_event.time_us > active_config.time_limit_us:
                context.network_state.statistics.stop_reason = "time_limit_reached"
                context.clock.advance_to(active_config.time_limit_us)
                engine_status = "stopped"
                break

            event = context.event_queue.pop()
            context.clock.advance_to(event.time_us)
            context.network_state.statistics.processed_events += 1
            dispatch_event(event, context)
            if context.network_state.statistics.finalized:
                break

        if context.network_state.statistics.stop_reason is None:
            context.network_state.statistics.stop_reason = (
                "delivery_target_reached"
                if context.network_state.statistics.finalized
                else "event_queue_empty"
            )
        for port_id in context.network_state.ports:
            synchronize_port_credits(port_id, context=context, reason="simulation_end")
        context.trace_collector.record(
            timestamp_us=context.clock.current_time_us,
            event_type="simulation_end",
            description="Simulation baseline finished.",
            attributes={
                "engine_status": engine_status,
                "stop_reason": context.network_state.statistics.stop_reason,
            },
        )
        return build_simulation_result(
            case=case,
            run_id=run_id,
            metric_collector=context.metric_collector,
            network_state=context.network_state,
            trace_collector=context.trace_collector,
            engine_status=engine_status,
            simulated_time_us=context.clock.current_time_us,
        )
