"""Trace collection utilities for simulation runs."""

from __future__ import annotations

from dataclasses import asdict

from drts_tsn.domain.trace import TraceRow


class TraceCollector:
    """Collect optional trace rows during simulation."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self._rows: list[TraceRow] = []

    def record(
        self,
        *,
        timestamp_us: float,
        event_type: str,
        description: str,
        attributes: dict[str, object] | None = None,
    ) -> None:
        """Record a trace row when tracing is enabled."""

        if not self.enabled:
            return
        self._rows.append(
            TraceRow(
                timestamp_us=timestamp_us,
                event_type=event_type,
                description=description,
                attributes=attributes or {},
            )
        )

    def rows(self) -> list[dict[str, object]]:
        """Return trace rows as serializable dictionaries."""

        return [asdict(row) for row in self._rows]
