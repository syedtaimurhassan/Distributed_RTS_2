"""Parser for external stream payloads."""

from __future__ import annotations

from typing import Any


def _canonical_stream_id(raw_value: object) -> str:
    """Return a canonical external stream identifier."""

    if isinstance(raw_value, int):
        return f"stream-{raw_value}"
    raw_text = str(raw_value)
    return raw_text if not raw_text.isdigit() else f"stream-{raw_text}"


def _pcp_to_traffic_class(pcp_value: object) -> str:
    """Map a baseline PCP value into the supported traffic classes."""

    pcp = int(pcp_value)
    if pcp >= 2:
        return "AVB_A"
    if pcp == 1:
        return "AVB_B"
    return "BE"


def parse_streams_payload(payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract stream rows from the external payload."""

    rows = list(payload) if isinstance(payload, list) else list(payload.get("streams", []))
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Stream at index {index} must be an object.")
        normalized_row = dict(row)
        if "destination" not in normalized_row and "destinations" in normalized_row:
            destinations = normalized_row.get("destinations", [])
            if isinstance(destinations, list) and destinations:
                first_destination = destinations[0]
                if isinstance(first_destination, dict):
                    normalized_row["destination"] = first_destination.get("id")
                    if "deadline_us" not in normalized_row and "deadline" in first_destination:
                        normalized_row["deadline_us"] = first_destination["deadline"]
        if "traffic_class" not in normalized_row and normalized_row.get("PCP") is not None:
            normalized_row["traffic_class"] = _pcp_to_traffic_class(normalized_row["PCP"])
        if "max_frame_size_bytes" not in normalized_row and normalized_row.get("size") is not None:
            normalized_row["max_frame_size_bytes"] = normalized_row["size"]
        if "period_us" not in normalized_row and normalized_row.get("period") is not None:
            normalized_row["period_us"] = normalized_row["period"]
        normalized_row["id"] = _canonical_stream_id(normalized_row.get("id"))
        if normalized_row.get("route_id") is None:
            normalized_row["route_id"] = f"route-{normalized_row['id']}"
        required_any = {
            "frame_size": ("max_frame_size_bytes", "size_bytes", "frame_size_bytes"),
            "period": ("period_us", "period"),
            "traffic_class": ("traffic_class", "class", "priority_class"),
        }
        for field_name in ("id", "source", "destination"):
            if field_name not in normalized_row:
                raise ValueError(f"Stream at index {index} is missing required field '{field_name}'.")
        for field_label, aliases in required_any.items():
            if not any(alias in normalized_row for alias in aliases):
                raise ValueError(
                    f"Stream at index {index} is missing required {field_label} field. "
                    f"Accepted keys: {', '.join(aliases)}."
                )
        normalized_rows.append(normalized_row)
    return normalized_rows
