"""Transmission-selection helpers for the baseline simulator."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.domain.enums import TrafficClass
from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.model.port_state import PortState

from .cbs import can_transmit_with_credit
from .fifo import fifo_select


@dataclass(slots=True, frozen=True)
class TransmissionCandidate:
    """One selected transmission candidate for a port."""

    port_id: str
    queue_id: str
    frame_id: str
    traffic_class: TrafficClass


@dataclass(slots=True, frozen=True)
class QueueSnapshot:
    """Current scheduler-relevant state for one queue."""

    queue_id: str
    traffic_class: TrafficClass
    head_frame_id: str | None
    queue_depth: int
    credit: float | None


@dataclass(slots=True, frozen=True)
class SchedulerDecision:
    """One deterministic scheduler decision for a port at a point in time."""

    candidate: TransmissionCandidate | None
    reason: str
    snapshots: dict[TrafficClass, QueueSnapshot]


def build_scheduler_decision(
    port_state: PortState,
    context: SimulationContext,
) -> SchedulerDecision:
    """Select the next transmission candidate and explain the decision."""

    snapshots: dict[TrafficClass, QueueSnapshot] = {}
    higher_ineligible = False
    queue_definitions = sorted(
        context.case.queues,
        key=lambda queue: queue.priority,
        reverse=True,
    )
    for queue_definition in queue_definitions:
        queue_id = context.queue_ids_by_port_and_class[(port_state.port_id, queue_definition.traffic_class)]
        queue_state = port_state.queues[queue_id]
        credit_state = port_state.credits.get(queue_id)
        snapshots[queue_definition.traffic_class] = QueueSnapshot(
            queue_id=queue_id,
            traffic_class=queue_definition.traffic_class,
            head_frame_id=fifo_select(queue_state.pending_frame_ids),
            queue_depth=len(queue_state.pending_frame_ids),
            credit=credit_state.current_credit if credit_state is not None else None,
        )

    if port_state.current_transmission_frame_id is not None:
        return SchedulerDecision(
            candidate=None,
            reason="port_busy",
            snapshots=snapshots,
        )

    for queue_definition in queue_definitions:
        snapshot = snapshots[queue_definition.traffic_class]
        if snapshot.head_frame_id is None:
            continue
        if queue_definition.uses_cbs:
            credit = snapshot.credit if snapshot.credit is not None else 0.0
            if not can_transmit_with_credit(credit):
                higher_ineligible = True
                continue
        if queue_definition.traffic_class is TrafficClass.BEST_EFFORT:
            reason = "selected_best_effort_fallback" if higher_ineligible else "selected_best_effort"
        elif higher_ineligible:
            reason = f"selected_{queue_definition.traffic_class.value}_after_higher_ineligible"
        else:
            reason = f"selected_{queue_definition.traffic_class.value}"
        return SchedulerDecision(
            candidate=TransmissionCandidate(
                port_id=port_state.port_id,
                queue_id=snapshot.queue_id,
                frame_id=snapshot.head_frame_id,
                traffic_class=queue_definition.traffic_class,
            ),
            reason=reason,
            snapshots=snapshots,
        )

    if any(
        snapshot.head_frame_id is not None and snapshot.credit is not None and not can_transmit_with_credit(snapshot.credit)
        for snapshot in snapshots.values()
    ):
        return SchedulerDecision(
            candidate=None,
            reason="waiting_for_credit_recovery",
            snapshots=snapshots,
        )
    return SchedulerDecision(
        candidate=None,
        reason="no_frames_available",
        snapshots=snapshots,
    )


def select_transmission_candidate(
    port_state: PortState,
    context: SimulationContext,
) -> TransmissionCandidate | None:
    """Return the selected candidate without scheduler-decision metadata."""

    return build_scheduler_decision(port_state, context).candidate
