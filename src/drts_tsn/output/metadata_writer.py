"""Writers for run-level metadata files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_writers import write_json_artifact


def write_run_metadata(metadata: dict[str, Any], path: Path) -> Path:
    """Write run metadata as JSON."""

    return write_json_artifact(metadata, path)
