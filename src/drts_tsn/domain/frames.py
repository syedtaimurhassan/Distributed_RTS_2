"""Frame-level canonical models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class FrameSpec:
    """A frame size description for a stream."""

    payload_size_bytes: int
    overhead_size_bytes: int = 0

    @property
    def total_size_bytes(self) -> int:
        """Return payload plus overhead."""

        return self.payload_size_bytes + self.overhead_size_bytes
