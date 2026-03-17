"""Canonical credit-based shaper parameter models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CreditParameters:
    """CBS parameters reserved for AVB classes."""

    idle_slope_mbps: float
    send_slope_mbps: float | None = None
    hi_credit_bytes: float | None = None
    lo_credit_bytes: float | None = None
