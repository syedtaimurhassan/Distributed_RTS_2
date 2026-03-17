"""Minimal simulation clock implementation."""

from __future__ import annotations


class SimulationClock:
    """Track current simulation time in microseconds."""

    def __init__(self) -> None:
        self.current_time_us: float = 0.0

    def advance_to(self, time_us: float) -> None:
        """Advance monotonically to the requested time."""

        if time_us < self.current_time_us:
            raise ValueError("Simulation clock cannot move backwards.")
        self.current_time_us = time_us
