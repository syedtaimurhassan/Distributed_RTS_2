"""Derive frame-related canonical parameters for streams."""

from __future__ import annotations

from dataclasses import replace

from drts_tsn.common.constants import CLASS_PRIORITY_ORDER
from drts_tsn.domain.case import Case


def derive_frame_parameters(case: Case) -> Case:
    """Fill baseline stream defaults needed by later stages."""

    return replace(
        case,
        streams=[
            replace(
                stream,
                deadline_us=stream.deadline_us if stream.deadline_us > 0 else stream.period_us,
                route_id=stream.route_id or stream.id,
                priority=stream.priority
                if stream.priority is not None
                else CLASS_PRIORITY_ORDER[stream.traffic_class.value],
            )
            for stream in case.streams
        ],
    )
