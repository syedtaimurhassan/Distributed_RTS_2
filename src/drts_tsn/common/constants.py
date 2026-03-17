"""Shared constants for the TSN scaffold."""

DEFAULT_ENCODING = "utf-8"
DEFAULT_LINK_SPEED_MBPS = 100.0
DEFAULT_CBS_SLOPE_SHARE = 0.5
DEFAULT_QUEUE_ORDER = ("class_a", "class_b", "best_effort")

CLASS_PRIORITY_ORDER = {
    "class_a": 2,
    "class_b": 1,
    "best_effort": 0,
}
