"""Credit-recovery helpers used by the baseline AVB formulas."""

from __future__ import annotations


def credit_recovery_us(transmission_time_us: float, reserved_share: float) -> float:
    """Return the recovery term for one eligible interval under a reserved share."""

    if reserved_share <= 0:
        raise ValueError("Reserved share must be positive.")
    return max((transmission_time_us / reserved_share) - transmission_time_us, 0.0)


def blocking_credit_recovery_us(
    blocking_time_us: float,
    *,
    idle_slope_share: float,
    send_slope_share: float,
) -> float:
    """Return recovery caused by credit accumulated during lower-priority blocking."""

    if blocking_time_us <= 0:
        return 0.0
    if idle_slope_share <= 0 or send_slope_share <= 0:
        raise ValueError("Idle and send slope shares must be positive.")
    return blocking_time_us * (idle_slope_share / send_slope_share)
