"""Context object shared by analytical services."""

from __future__ import annotations

from dataclasses import dataclass, field

from drts_tsn.domain.case import Case

from .config import AnalysisConfig


@dataclass(slots=True)
class AnalysisContext:
    """Runtime context for analytical processing."""

    case: Case
    config: AnalysisConfig
    explanations: list[dict[str, object]] = field(default_factory=list)
