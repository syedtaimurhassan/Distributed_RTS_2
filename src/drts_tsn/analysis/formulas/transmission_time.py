"""Transmission-time calculator for analytical AVB bounds."""

from __future__ import annotations

from drts_tsn.common.math_utils import serialization_delay_us


def transmission_time_us(frame_size_bytes: int, link_speed_mbps: float) -> float:
    """Return frame serialization time in microseconds."""

    return serialization_delay_us(frame_size_bytes, link_speed_mbps)
