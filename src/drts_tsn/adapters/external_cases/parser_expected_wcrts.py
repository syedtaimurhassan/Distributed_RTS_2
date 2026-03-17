"""Parser for externally provided expected WCRT values."""

from __future__ import annotations

from typing import Any


def parse_expected_wcrts_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return expected WCRT rows in a stable list-of-dicts shape."""

    for index, row in enumerate(rows):
        if "stream_id" not in row or "expected_wcrt_us" not in row:
            raise ValueError(
                f"Expected-WCRT CSV row {index} must contain 'stream_id' and 'expected_wcrt_us'."
            )
    return [dict(row) for row in rows]
