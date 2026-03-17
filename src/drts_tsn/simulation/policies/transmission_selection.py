"""Transmission-selection helpers for the baseline simulator."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.domain.enums import TrafficClass
from drts_tsn.simulation.context import SimulationContext
from drts_tsn.simulation.model.port_state import PortState

from .cbs import can_transmit_with_credit
from .fifo import fifo_select
from .strict_priority import select_highest_priority


@dataclass(slots=True, frozen=True)
class TransmissionCandidate:
    """One selected transmission candidate for a port."""

    port_id: str
    queue_id: str
    frame_id: str
    traffic_class: TrafficClass


def select_transmission_candidate(
    port_state: PortState,
    context: SimulationContext,
) -> TransmissionCandidate | None:
    """Select the next eligible frame for transmission on a port."""

    eligible_candidates: list[TransmissionCandidate] = []
    queue_definitions = sorted(
        context.case.queues,
        key=lambda queue: queue.priority,
        reverse=True,
    )
    for queue_definition in queue_definitions:
        queue_id = context.queue_ids_by_port_and_class[(port_state.port_id, queue_definition.traffic_class)]
        queue_state = port_state.queues[queue_id]
        frame_id = fifo_select(queue_state.pending_frame_ids)
        if frame_id is None:
            continue
        if queue_definition.uses_cbs:
            credit_state = port_state.credits[queue_id]
            if not can_transmit_with_credit(credit_state, now_us=context.clock.current_time_us):
                continue
        eligible_candidates.append(
            TransmissionCandidate(
                port_id=port_state.port_id,
                queue_id=queue_id,
                frame_id=frame_id,
                traffic_class=queue_definition.traffic_class,
            )
        )
    return select_highest_priority(eligible_candidates)
