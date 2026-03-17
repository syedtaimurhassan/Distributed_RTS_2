"""Unit tests for CBS behavior in the baseline simulator."""

from __future__ import annotations

from drts_tsn.domain.case import Case, CaseMetadata
from drts_tsn.domain.credits import CreditParameters
from drts_tsn.domain.enums import NodeType, TrafficClass
from drts_tsn.domain.queues import QueueDefinition
from drts_tsn.domain.routes import Route, RouteHop
from drts_tsn.domain.streams import Stream
from drts_tsn.domain.topology import Link, Node, Topology
from drts_tsn.simulation.config import SimulationConfig
from drts_tsn.simulation.context import build_simulation_context
from drts_tsn.simulation.dispatcher import dispatch_event
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.model.frame_state import FrameState
from drts_tsn.simulation.services.credit_service import (
    synchronize_port_credits,
    update_credit,
)
from drts_tsn.simulation.services.scheduler_service import schedule_next_transmission


def _build_single_link_case() -> Case:
    """Return a minimal normalized one-link case for simulator unit tests."""

    return Case(
        metadata=CaseMetadata(case_id="cbs-unit", name="cbs-unit"),
        topology=Topology(
            nodes=[
                Node(id="talker", type=NodeType.END_SYSTEM),
                Node(id="listener", type=NodeType.END_SYSTEM),
            ],
            links=[Link(id="link-1", source_node_id="talker", target_node_id="listener", speed_mbps=100.0)],
        ),
        streams=[
            Stream(
                id="stream-a",
                name="stream-a",
                source_node_id="talker",
                destination_node_id="listener",
                traffic_class=TrafficClass.CLASS_A,
                period_us=1000.0,
                deadline_us=1000.0,
                max_frame_size_bytes=128,
                route_id="route-a",
                priority=2,
            ),
            Stream(
                id="stream-b",
                name="stream-b",
                source_node_id="talker",
                destination_node_id="listener",
                traffic_class=TrafficClass.CLASS_B,
                period_us=1000.0,
                deadline_us=1000.0,
                max_frame_size_bytes=128,
                route_id="route-b",
                priority=1,
            ),
            Stream(
                id="stream-be",
                name="stream-be",
                source_node_id="talker",
                destination_node_id="listener",
                traffic_class=TrafficClass.BEST_EFFORT,
                period_us=1000.0,
                deadline_us=1000.0,
                max_frame_size_bytes=128,
                route_id="route-be",
                priority=0,
            ),
        ],
        routes=[
            Route(route_id="route-a", stream_id="stream-a", hops=[RouteHop(node_id="talker", link_id="link-1"), RouteHop(node_id="listener")]),
            Route(route_id="route-b", stream_id="stream-b", hops=[RouteHop(node_id="talker", link_id="link-1"), RouteHop(node_id="listener")]),
            Route(route_id="route-be", stream_id="stream-be", hops=[RouteHop(node_id="talker", link_id="link-1"), RouteHop(node_id="listener")]),
        ],
        queues=[
            QueueDefinition(
                traffic_class=TrafficClass.CLASS_A,
                priority=2,
                uses_cbs=True,
                credit_parameters=CreditParameters(idle_slope_mbps=50.0, send_slope_mbps=50.0),
            ),
            QueueDefinition(
                traffic_class=TrafficClass.CLASS_B,
                priority=1,
                uses_cbs=True,
                credit_parameters=CreditParameters(idle_slope_mbps=50.0, send_slope_mbps=50.0),
            ),
            QueueDefinition(
                traffic_class=TrafficClass.BEST_EFFORT,
                priority=0,
                uses_cbs=False,
            ),
        ],
    )


def _seed_pending_frame(context, *, stream_id: str, frame_id: str | None = None) -> str:
    """Create one pending frame at the first hop for a stream and return its queue id."""

    stream = context.streams_by_id[stream_id]
    resolved_frame_id = frame_id or f"{stream_id}-frame"
    context.network_state.frames[resolved_frame_id] = FrameState(
        frame_id=resolved_frame_id,
        stream_id=stream_id,
        traffic_class=stream.traffic_class,
        route_id=stream.route_id or stream.id,
        release_index=0,
        release_time_us=0.0,
        frame_size_bytes=stream.max_frame_size_bytes,
        route_link_ids=["link-1"],
        current_hop_index=0,
        current_link_id="link-1",
        enqueue_timestamps_by_hop={0: context.clock.current_time_us},
    )
    queue_id = context.queue_ids_by_port_and_class[("link-1", stream.traffic_class)]
    queue_state = context.network_state.ports["link-1"].queues[queue_id]
    queue_state.pending_frame_ids.append(resolved_frame_id)
    return queue_id


def _seed_transmitting_frame(context, *, stream_id: str, frame_id: str) -> None:
    """Create one frame state and mark it as the current non-preemptive transmission."""

    stream = context.streams_by_id[stream_id]
    context.network_state.frames[frame_id] = FrameState(
        frame_id=frame_id,
        stream_id=stream_id,
        traffic_class=stream.traffic_class,
        route_id=stream.route_id or stream.id,
        release_index=0,
        release_time_us=0.0,
        frame_size_bytes=stream.max_frame_size_bytes,
        route_link_ids=["link-1"],
        current_hop_index=0,
        current_link_id="link-1",
        enqueue_timestamps_by_hop={0: 0.0},
        transmission_start_timestamps_by_hop={0: 0.0},
    )
    context.network_state.ports["link-1"].current_transmission_frame_id = frame_id


def test_class_a_selected_over_class_b_and_be_when_eligible() -> None:
    """Class A should win strict priority when its credit is non-negative."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    _seed_pending_frame(context, stream_id="stream-a")
    _seed_pending_frame(context, stream_id="stream-b")
    _seed_pending_frame(context, stream_id="stream-be")

    schedule_next_transmission("link-1", context, reason="unit")

    decision = context.metric_collector.tables["scheduler_decision_trace"][-1]
    assert decision["selected_traffic_class"] == TrafficClass.CLASS_A.value
    assert decision["decision_reason"] == "selected_class_a:unit"
    assert context.event_queue.peek().event_name == SimulationEventType.TRANSMISSION_START.value


def test_class_b_selected_over_be_when_class_a_is_ineligible() -> None:
    """Class B should win over BE when Class A is present but blocked on negative credit."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    _seed_pending_frame(context, stream_id="stream-a")
    _seed_pending_frame(context, stream_id="stream-b")
    _seed_pending_frame(context, stream_id="stream-be")
    class_a_queue_id = context.queue_ids_by_port_and_class[("link-1", TrafficClass.CLASS_A)]
    context.network_state.ports["link-1"].credits[class_a_queue_id].current_credit = -10.0

    schedule_next_transmission("link-1", context, reason="unit")

    decision = context.metric_collector.tables["scheduler_decision_trace"][-1]
    assert decision["selected_traffic_class"] == TrafficClass.CLASS_B.value
    assert decision["decision_reason"] == "selected_class_b_after_higher_ineligible:unit"


def test_class_b_selected_over_be_when_class_a_is_empty() -> None:
    """Class B should win over BE when Class A has no pending frame."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    _seed_pending_frame(context, stream_id="stream-b")
    _seed_pending_frame(context, stream_id="stream-be")

    schedule_next_transmission("link-1", context, reason="unit")

    decision = context.metric_collector.tables["scheduler_decision_trace"][-1]
    assert decision["selected_traffic_class"] == TrafficClass.CLASS_B.value
    assert decision["decision_reason"] == "selected_class_b:unit"


def test_avb_queue_is_blocked_when_credit_is_negative() -> None:
    """Negative credit should block AVB transmission and schedule a wakeup at zero crossing."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    class_a_queue_id = _seed_pending_frame(context, stream_id="stream-a")
    context.network_state.ports["link-1"].credits[class_a_queue_id].current_credit = -100.0

    schedule_next_transmission("link-1", context, reason="unit")

    decision = context.metric_collector.tables["scheduler_decision_trace"][-1]
    assert decision["selected_queue_id"] is None
    assert decision["decision_reason"] == "waiting_for_credit_recovery:unit"
    scheduled = context.event_queue.peek()
    assert scheduled.event_name == SimulationEventType.CREDIT_UPDATE.value
    assert scheduled.time_us == 2.0


def test_positive_credit_resets_to_zero_when_no_avb_frame_is_pending() -> None:
    """Positive idle credit must reset to zero once the queue is empty."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    class_a_queue_id = context.queue_ids_by_port_and_class[("link-1", TrafficClass.CLASS_A)]
    context.network_state.ports["link-1"].credits[class_a_queue_id].current_credit = 25.0

    update_credit(class_a_queue_id, context)

    credit_state = context.network_state.ports["link-1"].credits[class_a_queue_id]
    assert credit_state.current_credit == 0.0
    assert context.metric_collector.tables["credit_trace"][-1]["change_reason"] == "reset_no_pending:credit_update"


def test_negative_credit_recovers_toward_zero() -> None:
    """Negative credit should recover under idle slope until it reaches zero."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    class_a_queue_id = context.queue_ids_by_port_and_class[("link-1", TrafficClass.CLASS_A)]
    credit_state = context.network_state.ports["link-1"].credits[class_a_queue_id]
    credit_state.current_credit = -100.0
    credit_state.last_update_time_us = 0.0
    context.clock.advance_to(1.0)

    update_credit(class_a_queue_id, context)

    assert credit_state.current_credit == -50.0
    assert context.metric_collector.tables["credit_trace"][-1]["change_reason"] == "recover_toward_zero:credit_update"


def test_credit_increases_while_blocked_by_best_effort() -> None:
    """A queued AVB class should accumulate uncapped credit while BE is transmitting."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    _seed_pending_frame(context, stream_id="stream-a")
    be_frame_id = "stream-be-blocking"
    _seed_transmitting_frame(context, stream_id="stream-be", frame_id=be_frame_id)
    context.clock.advance_to(4.0)

    synchronize_port_credits("link-1", context=context, reason="unit_blocking", related_frame_id="stream-a-frame")

    class_a_queue_id = context.queue_ids_by_port_and_class[("link-1", TrafficClass.CLASS_A)]
    credit_state = context.network_state.ports["link-1"].credits[class_a_queue_id]
    assert credit_state.current_credit == 200.0
    assert context.metric_collector.tables["credit_trace"][-1]["change_reason"] == "blocked_by_best_effort:unit_blocking"
    assert context.metric_collector.tables["credit_trace"][-1]["blocking_frame_id"] == be_frame_id


def test_non_preemptive_behavior_keeps_lower_priority_transmission_running() -> None:
    """A started BE transmission should not be interrupted by a later Class A arrival."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    _seed_pending_frame(context, stream_id="stream-be", frame_id="be-first")

    schedule_next_transmission("link-1", context, reason="unit_start")
    start_event = context.event_queue.pop()
    context.clock.advance_to(start_event.time_us)
    dispatch_event(start_event, context)

    assert context.network_state.ports["link-1"].current_transmission_frame_id == "be-first"

    context.clock.advance_to(1.0)
    _seed_pending_frame(context, stream_id="stream-a", frame_id="a-late")
    schedule_next_transmission("link-1", context, reason="unit_arrival")

    decision = context.metric_collector.tables["scheduler_decision_trace"][-1]
    assert decision["decision_reason"] == "port_busy:unit_arrival"
    assert decision["current_transmission_frame_id"] == "be-first"
    assert context.network_state.ports["link-1"].current_transmission_frame_id == "be-first"


def test_trace_rows_capture_predictable_cbs_decision_sequence() -> None:
    """Scheduler and credit traces should explain a simple blocking-to-recovery scenario."""

    context = build_simulation_context(_build_single_link_case(), SimulationConfig())
    _seed_pending_frame(context, stream_id="stream-a", frame_id="a-head")
    _seed_transmitting_frame(context, stream_id="stream-be", frame_id="be-blocker")
    context.clock.advance_to(2.0)

    synchronize_port_credits("link-1", context=context, reason="trace_test", related_frame_id="a-head")
    schedule_next_transmission("link-1", context, reason="trace_test")

    credit_trace = context.metric_collector.tables["credit_trace"]
    scheduler_trace = context.metric_collector.tables["scheduler_decision_trace"]
    assert credit_trace[-1]["blocking_frame_id"] == "be-blocker"
    assert credit_trace[-1]["traffic_class"] == TrafficClass.CLASS_A.value
    assert scheduler_trace[-1]["decision_reason"] == "port_busy:trace_test"
    assert scheduler_trace[-1]["class_a_head_frame_id"] == "a-head"
