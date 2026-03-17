"""Credit-based shaper helpers for the baseline simulator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CreditComputation:
    """One CBS credit-state update over a time interval."""

    credit_before: float
    credit_after: float
    reason: str
    slope_mbps: float
    elapsed_time_us: float
    capped_at_zero: bool = False


def can_transmit_with_credit(current_credit: float) -> bool:
    """Return whether a queue is CBS-eligible to transmit."""

    return current_credit >= -1e-9


def credit_recovery_completion_time_us(
    *,
    current_credit: float,
    idle_slope_mbps: float,
    now_us: float,
) -> float | None:
    """Return the time when a negative credit reaches zero under idle-slope recovery."""

    if current_credit >= 0:
        return now_us
    if idle_slope_mbps <= 0:
        return None
    return now_us + ((-current_credit) / idle_slope_mbps)


def integrate_credit(
    *,
    current_credit: float,
    elapsed_time_us: float,
    idle_slope_mbps: float,
    send_slope_mbps: float,
    transmitting_this_class: bool,
    blocked_by_best_effort: bool,
) -> CreditComputation:
    """Integrate one queue's credit over a fixed interval under simplified CBS rules."""

    if elapsed_time_us < 0:
        raise ValueError("CBS credit integration cannot move backwards in time.")
    if elapsed_time_us == 0:
        return CreditComputation(
            credit_before=current_credit,
            credit_after=current_credit,
            reason="no_time_elapsed",
            slope_mbps=0.0,
            elapsed_time_us=0.0,
        )
    if transmitting_this_class:
        if send_slope_mbps <= 0:
            raise ValueError("CBS send slope must be positive.")
        return CreditComputation(
            credit_before=current_credit,
            credit_after=current_credit - (send_slope_mbps * elapsed_time_us),
            reason="transmit",
            slope_mbps=-send_slope_mbps,
            elapsed_time_us=elapsed_time_us,
        )
    if blocked_by_best_effort:
        if idle_slope_mbps <= 0:
            raise ValueError("CBS idle slope must be positive.")
        return CreditComputation(
            credit_before=current_credit,
            credit_after=current_credit + (idle_slope_mbps * elapsed_time_us),
            reason="blocked_by_best_effort",
            slope_mbps=idle_slope_mbps,
            elapsed_time_us=elapsed_time_us,
        )
    if current_credit < 0:
        if idle_slope_mbps <= 0:
            raise ValueError("CBS idle slope must be positive.")
        recovered_credit = current_credit + (idle_slope_mbps * elapsed_time_us)
        credit_after = min(recovered_credit, 0.0)
        return CreditComputation(
            credit_before=current_credit,
            credit_after=credit_after,
            reason="recover_toward_zero",
            slope_mbps=idle_slope_mbps,
            elapsed_time_us=elapsed_time_us,
            capped_at_zero=recovered_credit > 0.0,
        )
    return CreditComputation(
        credit_before=current_credit,
        credit_after=current_credit,
        reason="hold",
        slope_mbps=0.0,
        elapsed_time_us=elapsed_time_us,
    )
