"""Per-queue CBS credit state for the baseline simulator."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.domain.enums import TrafficClass


@dataclass(slots=True)
class CreditState:
    """Mutable CBS eligibility state for one AVB queue."""

    traffic_class: TrafficClass
    current_credit: float = 0.0
    last_update_time_us: float = 0.0
    next_eligible_time_us: float = 0.0
