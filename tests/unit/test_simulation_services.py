"""Unit tests for core discrete-event simulation state transitions."""

from __future__ import annotations

from drts_tsn.domain.case import Case, CaseMetadata
from drts_tsn.domain.credits import CreditParameters
from drts_tsn.domain.enums import NodeType
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.queues import QueueDefinition
from drts_tsn.domain.topology import Link, Node, Topology
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.simulation.config import SimulationConfig
from drts_tsn.simulation.context import build_simulation_context
from drts_tsn.simulation.dispatcher import dispatch_event
from drts_tsn.simulation.event_types import SimulationEventType
from drts_tsn.simulation.services.credit_service import request_credit_update


def test_release_enqueue_and_forward_transition(sample_case_path) -> None:
    """A released frame should enqueue, transmit, and schedule forwarding hop-by-hop."""

    prepared = prepare_case(sample_case_path)
    context = build_simulation_context(
        prepared.normalized_case,
        SimulationConfig(max_releases_per_stream=1),
    )
    context.event_queue.push(0.0, SimulationEventType.RELEASE_FRAME.value, {"stream_id": "stream-a"})

    release_event = context.event_queue.pop()
    context.clock.advance_to(release_event.time_us)
    dispatch_event(release_event, context)

    assert "stream-a-rel-0" in context.network_state.frames
    assert context.metric_collector.tables["frame_release_trace"][0]["frame_id"] == "stream-a-rel-0"

    enqueue_event = context.event_queue.pop()
    context.clock.advance_to(enqueue_event.time_us)
    dispatch_event(enqueue_event, context)

    queue_id = context.queue_ids_by_port_and_class[("link-1", TrafficClass.CLASS_A)]
    port_state = context.network_state.ports["link-1"]
    assert port_state.queues[queue_id].pending_frame_ids == ["stream-a-rel-0"]
    assert context.metric_collector.tables["enqueue_trace"][0]["queue_id"] == queue_id

    transmission_start_event = context.event_queue.pop()
    context.clock.advance_to(transmission_start_event.time_us)
    dispatch_event(transmission_start_event, context)

    assert port_state.current_transmission_frame_id == "stream-a-rel-0"

    transmission_end_event = context.event_queue.pop()
    context.clock.advance_to(transmission_end_event.time_us)
    dispatch_event(transmission_end_event, context)

    assert port_state.current_transmission_frame_id is None
    assert context.metric_collector.tables["transmission_trace"][0]["link_id"] == "link-1"

    forward_event = context.event_queue.pop()
    context.clock.advance_to(forward_event.time_us)
    dispatch_event(forward_event, context)

    frame_state = context.network_state.frames["stream-a-rel-0"]
    assert frame_state.current_hop_index == 1
    assert frame_state.current_link_id == "link-2"

    next_enqueue_event = context.event_queue.pop()
    assert next_enqueue_event.event_name == SimulationEventType.ENQUEUE_FRAME.value
    assert next_enqueue_event.payload["port_id"] == "link-2"


def test_credit_update_lookup_does_not_depend_on_queue_id_delimiter() -> None:
    """Credit updates should resolve queue ownership from state, not queue-id string splitting."""

    case = Case(
        metadata=CaseMetadata(case_id="queue-id-coupling", name="queue-id-coupling"),
        topology=Topology(
            nodes=[
                Node(id="talker", type=NodeType.END_SYSTEM),
                Node(id="listener", type=NodeType.END_SYSTEM),
            ],
            links=[
                Link(id="link:alpha", source_node_id="talker", target_node_id="listener", speed_mbps=100.0),
            ],
        ),
        queues=[
            QueueDefinition(
                traffic_class=TrafficClass.CLASS_A,
                priority=2,
                uses_cbs=True,
                credit_parameters=CreditParameters(idle_slope_mbps=50.0, send_slope_mbps=50.0),
            ),
            QueueDefinition(traffic_class=TrafficClass.CLASS_B, priority=1, uses_cbs=True),
            QueueDefinition(traffic_class=TrafficClass.BEST_EFFORT, priority=0, uses_cbs=False),
        ],
    )
    context = build_simulation_context(case, SimulationConfig())
    queue_id = context.queue_ids_by_port_and_class[("link:alpha", TrafficClass.CLASS_A)]

    request_credit_update(queue_id, time_us=5.0, context=context)
    scheduled = context.event_queue.pop()
    context.clock.advance_to(scheduled.time_us)
    dispatch_event(scheduled, context)

    assert scheduled.event_name == SimulationEventType.CREDIT_UPDATE.value
    assert context.network_state.ports["link:alpha"].queues[queue_id].scheduled_credit_update_time_us is None
