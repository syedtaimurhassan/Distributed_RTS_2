"""Parser for external stream payloads."""

from __future__ import annotations

from typing import Any


def parse_streams_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract stream rows from the external payload."""

    rows = list(payload) if isinstance(payload, list) else list(payload.get("streams", []))
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Stream at index {index} must be an object.")
        required_any = {
            "frame_size": ("max_frame_size_bytes", "size_bytes", "frame_size_bytes"),
            "period": ("period_us", "period"),
            "traffic_class": ("traffic_class", "class", "priority_class"),
        }
        for field_name in ("id", "source", "destination"):
            if field_name not in row:
                raise ValueError(f"Stream at index {index} is missing required field '{field_name}'.")
        for field_label, aliases in required_any.items():
            if not any(alias in row for alias in aliases):
                raise ValueError(
                    f"Stream at index {index} is missing required {field_label} field. "
                    f"Accepted keys: {', '.join(aliases)}."
                )
    return rows
