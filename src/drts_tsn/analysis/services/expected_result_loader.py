"""Helpers for expected WCRT data exposed with external cases."""

from __future__ import annotations

from drts_tsn.domain.case import Case


def load_expected_results(case: Case) -> dict[str, float]:
    """Return expected results keyed by stream ID."""

    return {result.stream_id: result.expected_wcrt_us for result in case.expected_results}
