"""CSV artifact writers."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from drts_tsn.io.csv_io import write_csv_rows


def write_csv_artifact(
    rows: list[Mapping[str, object]],
    path: Path,
    *,
    fieldnames: list[str] | None = None,
) -> Path:
    """Write a CSV artifact."""

    return write_csv_rows(rows, path, fieldnames=fieldnames)
