"""Canonical queue definitions used by the simplified TSN baseline."""

from __future__ import annotations

from dataclasses import dataclass

from .credits import CreditParameters
from .enums import TrafficClass


@dataclass(slots=True, frozen=True)
class QueueDefinition:
    """A queue definition associated with a traffic class."""

    traffic_class: TrafficClass
    priority: int
    uses_cbs: bool
    credit_parameters: CreditParameters | None = None
