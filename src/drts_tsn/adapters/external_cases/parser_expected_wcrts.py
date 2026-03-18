"""Parser for externally provided expected WCRT values."""

from __future__ import annotations

from typing import Any


def _canonical_stream_id(raw_value: object) -> str:
    """Return a canonical external stream identifier."""

    if isinstance(raw_value, int):
        return f"stream-{raw_value}"
    raw_text = str(raw_value).strip()
    return raw_text if not raw_text.isdigit() else f"stream-{raw_text}"


def _parse_float(raw_value: object) -> float:
    """Parse numeric values, accepting comma decimals used by the assignment CSV."""

    return float(str(raw_value).strip().replace(",", "."))


def parse_expected_wcrts_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return expected WCRT rows in a stable list-of-dicts shape."""

    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if "stream_id" in row and "expected_wcrt_us" in row:
            normalized_rows.append(
                {
                    "stream_id": _canonical_stream_id(row["stream_id"]),
                    "expected_wcrt_us": _parse_float(row["expected_wcrt_us"]),
                }
            )
            continue
        if "ID" in row and "WCRT" in row:
            normalized_rows.append(
                {
                    "stream_id": _canonical_stream_id(row["ID"]),
                    "expected_wcrt_us": _parse_float(row["WCRT"]),
                }
            )
            continue
        raise ValueError(
            "Expected-WCRT CSV row "
            f"{index} must contain either 'stream_id'/'expected_wcrt_us' or 'ID'/'WCRT'."
        )
    return normalized_rows
