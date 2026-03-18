"""Canonical credit-based shaper parameter models."""

from __future__ import annotations

from dataclasses import dataclass

from drts_tsn.common.constants import DEFAULT_LINK_SPEED_MBPS


@dataclass(slots=True, frozen=True)
class SlopeValue:
    """A resolved slope value with explicit unit semantics."""

    share: float
    rate_mbps: float
    source: str

@dataclass(slots=True, frozen=True)
class CreditParameters:
    """CBS parameters for AVB classes with explicit share/rate semantics."""

    idle_slope_mbps: float
    send_slope_mbps: float | None = None
    idle_slope_share: float | None = None
    send_slope_share: float | None = None
    slope_reference_speed_mbps: float | None = None
    hi_credit_bytes: float | None = None
    lo_credit_bytes: float | None = None


def _reference_speed_mbps(parameters: CreditParameters) -> float:
    """Return the reference link speed used for share/rate conversion."""

    return float(parameters.slope_reference_speed_mbps or DEFAULT_LINK_SPEED_MBPS)


def _share_from_rate(rate_mbps: float, *, reference_speed_mbps: float) -> float:
    """Convert an absolute slope rate into a normalized slope share."""

    if reference_speed_mbps <= 0:
        raise ValueError("CBS slope reference speed must be positive.")
    return rate_mbps / reference_speed_mbps


def _resolve_idle_slope(parameters: CreditParameters) -> SlopeValue:
    """Return the idle slope in both share and Mbps using canonical semantics."""

    if parameters.idle_slope_share is not None:
        share = float(parameters.idle_slope_share)
        return SlopeValue(
            share=share,
            rate_mbps=share * _reference_speed_mbps(parameters),
            source="share",
        )
    rate_mbps = float(parameters.idle_slope_mbps)
    return SlopeValue(
        share=_share_from_rate(rate_mbps, reference_speed_mbps=_reference_speed_mbps(parameters)),
        rate_mbps=rate_mbps,
        source="mbps",
    )


def _resolve_send_slope(parameters: CreditParameters) -> SlopeValue:
    """Return the send slope in both share and Mbps using canonical semantics."""

    if parameters.send_slope_share is not None:
        share = float(parameters.send_slope_share)
        return SlopeValue(
            share=share,
            rate_mbps=share * _reference_speed_mbps(parameters),
            source="share",
        )
    rate_mbps = float(parameters.send_slope_mbps or parameters.idle_slope_mbps)
    return SlopeValue(
        share=_share_from_rate(rate_mbps, reference_speed_mbps=_reference_speed_mbps(parameters)),
        rate_mbps=rate_mbps,
        source="mbps",
    )


def idle_slope_share(parameters: CreditParameters) -> float:
    """Return the normalized idle-slope share."""

    return _resolve_idle_slope(parameters).share


def send_slope_share(parameters: CreditParameters) -> float:
    """Return the normalized send-slope share."""

    return _resolve_send_slope(parameters).share


def effective_idle_slope_mbps(parameters: CreditParameters, *, link_speed_mbps: float) -> float:
    """Return the idle slope converted to an effective per-link Mbps value."""

    if link_speed_mbps <= 0:
        raise ValueError("Link speed must be positive for CBS slope conversion.")
    return idle_slope_share(parameters) * link_speed_mbps


def effective_send_slope_mbps(parameters: CreditParameters, *, link_speed_mbps: float) -> float:
    """Return the send slope converted to an effective per-link Mbps value."""

    if link_speed_mbps <= 0:
        raise ValueError("Link speed must be positive for CBS slope conversion.")
    return send_slope_share(parameters) * link_speed_mbps


def validate_credit_parameter_consistency(parameters: CreditParameters) -> list[str]:
    """Return consistency errors for mixed-unit CBS slope definitions."""

    issues: list[str] = []
    idle = _resolve_idle_slope(parameters)
    send = _resolve_send_slope(parameters)
    if idle.share <= 0:
        issues.append("idle slope share must be positive.")
    if send.share <= 0:
        issues.append("send slope share must be positive.")
    if parameters.idle_slope_mbps <= 0:
        issues.append("idle slope Mbps must be positive.")
    if (parameters.send_slope_mbps or parameters.idle_slope_mbps) <= 0:
        issues.append("send slope Mbps must be positive.")

    tolerance = 1e-9
    reference_speed_mbps = _reference_speed_mbps(parameters)
    expected_idle_mbps = idle.share * reference_speed_mbps
    expected_send_mbps = send.share * reference_speed_mbps
    configured_send_mbps = float(parameters.send_slope_mbps or parameters.idle_slope_mbps)
    if abs(float(parameters.idle_slope_mbps) - expected_idle_mbps) > tolerance:
        issues.append(
            "idle slope share/Mbps are inconsistent for the configured reference speed."
        )
    if abs(configured_send_mbps - expected_send_mbps) > tolerance:
        issues.append(
            "send slope share/Mbps are inconsistent for the configured reference speed."
        )
    return issues


def slope_semantics_summary(parameters: CreditParameters) -> str:
    """Return a concise summary of slope source units for diagnostics."""

    idle = _resolve_idle_slope(parameters)
    send = _resolve_send_slope(parameters)
    return (
        f"idle(source={idle.source}, share={idle.share:.6f}, rate_mbps={idle.rate_mbps:.6f}); "
        f"send(source={send.source}, share={send.share:.6f}, rate_mbps={send.rate_mbps:.6f})"
    )
