"""JSON artifact writers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from drts_tsn.io.json_io import write_json


def write_json_artifact(data: Any, path: Path) -> Path:
    """Write a JSON artifact."""

    return write_json(data, path)
