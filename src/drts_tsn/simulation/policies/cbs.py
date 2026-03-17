"""Credit-based shaper helpers for the baseline simulator."""

from __future__ import annotations

from drts_tsn.simulation.model.credit_state import CreditState


def refresh_credit_state(credit_state: CreditState, *, now_us: float) -> None:
    """Refresh simplified credit state to the current simulation time."""

    if now_us < credit_state.last_update_time_us:
        raise ValueError("Credit state cannot be refreshed backwards in time.")
    if now_us >= credit_state.next_eligible_time_us:
        credit_state.current_credit = 0.0
    else:
        credit_state.current_credit = now_us - credit_state.next_eligible_time_us
    credit_state.last_update_time_us = now_us


def can_transmit_with_credit(credit_state: CreditState, *, now_us: float) -> bool:
    """Return whether a queue is eligible to transmit under simplified CBS logic."""

    refresh_credit_state(credit_state, now_us=now_us)
    return credit_state.current_credit >= 0.0


def apply_transmission_credit(
    credit_state: CreditState,
    *,
    transmission_time_us: float,
    reserved_share: float,
    end_time_us: float,
) -> tuple[float, float]:
    """Consume credit for one AVB transmission and return before/after credit."""

    if reserved_share <= 0:
        raise ValueError("Reserved share must be positive for CBS queues.")
    refresh_credit_state(credit_state, now_us=end_time_us - transmission_time_us)
    credit_before = credit_state.current_credit
    recovery_time_us = max((transmission_time_us / reserved_share) - transmission_time_us, 0.0)
    credit_state.current_credit = -recovery_time_us
    credit_state.last_update_time_us = end_time_us
    credit_state.next_eligible_time_us = end_time_us + recovery_time_us
    return credit_before, credit_state.current_credit
