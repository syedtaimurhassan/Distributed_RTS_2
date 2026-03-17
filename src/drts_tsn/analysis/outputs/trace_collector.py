"""Trace collection for analytical explanations."""

from __future__ import annotations


class AnalysisTraceCollector:
    """Collect explanation rows for analytical processing."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._rows: list[dict[str, object]] = []

    def record(
        self,
        *,
        step: str,
        description: str,
        details: dict[str, object] | None = None,
    ) -> None:
        """Record an explanation row when enabled."""

        if not self.enabled:
            return
        self._rows.append(
            {
                "step": step,
                "description": description,
                "details": details or {},
            }
        )

    def rows(self) -> list[dict[str, object]]:
        """Return collected explanation rows."""

        return list(self._rows)
