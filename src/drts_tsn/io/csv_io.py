"""CSV reader and writer helpers for detailed logs and summaries."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping

from drts_tsn.common.constants import DEFAULT_ENCODING


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of dictionaries."""

    with path.open("r", encoding=DEFAULT_ENCODING, newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(
    rows: Iterable[Mapping[str, object]],
    path: Path,
    *,
    fieldnames: list[str] | None = None,
) -> Path:
    """Write rows to CSV with optional explicit fieldnames."""

    row_list = [dict(row) for row in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    derived_fieldnames = fieldnames or (list(row_list[0].keys()) if row_list else [])
    with path.open("w", encoding=DEFAULT_ENCODING, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=derived_fieldnames)
        writer.writeheader()
        for row in row_list:
            writer.writerow(row)
    return path
