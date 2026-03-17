"""Artifact index helpers for generated run outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .json_writers import write_json_artifact


@dataclass(slots=True)
class ArtifactRecord:
    """One artifact entry in a run index."""

    name: str
    path: str
    kind: str


def write_artifact_index(records: list[ArtifactRecord], path: Path) -> Path:
    """Write the artifact index JSON file."""

    return write_json_artifact([asdict(record) for record in records], path)
