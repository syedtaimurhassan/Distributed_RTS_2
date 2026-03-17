"""Run-finalization event payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FinalizeRunEvent:
    """Finalize the current simulation run."""

    time_us: float
    reason: str
