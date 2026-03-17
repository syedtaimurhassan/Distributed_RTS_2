"""Canonical case model assembled from normalized external inputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .queues import QueueDefinition
from .results import ExpectedResult
from .routes import Route
from .streams import Stream
from .topology import Topology


@dataclass(slots=True)
class CaseMetadata:
    """Metadata that identifies and describes a case."""

    case_id: str
    name: str
    description: str = ""
    source_directory: Path | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Case:
    """A fully mapped canonical case used by all subsystems."""

    metadata: CaseMetadata
    topology: Topology
    streams: list[Stream] = field(default_factory=list)
    routes: list[Route] = field(default_factory=list)
    queues: list[QueueDefinition] = field(default_factory=list)
    expected_results: list[ExpectedResult] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    parameters: dict[str, object] = field(default_factory=dict)
