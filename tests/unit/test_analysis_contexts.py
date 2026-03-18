"""Unit tests for per-link analytical traffic context construction."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from drts_tsn.analysis.link_model import build_link_traffic_contexts
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.routes import Route
from drts_tsn.orchestration.run_manager import prepare_case


def test_same_priority_set_construction_on_a_link(sample_case_path) -> None:
    """Contexts should expose same-priority competitors that share the same directed links."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    case_with_peer = deepcopy(prepared.normalized_case)
    case_with_peer.streams.append(
        replace(
            case_with_peer.streams[0],
            id="stream-a-peer",
            name="AVB A peer stream",
            route_id="route-stream-a-peer",
        )
    )
    case_with_peer.routes.append(
        Route(
            stream_id="stream-a-peer",
            route_id="route-stream-a-peer",
            hops=deepcopy(case_with_peer.routes[0].hops),
        )
    )

    contexts = build_link_traffic_contexts(case_with_peer)
    analyzed_contexts = [context for context in contexts if context.stream_id == "stream-a"]

    assert len(analyzed_contexts) == 2
    assert [flow.stream_id for flow in analyzed_contexts[0].same_priority_flows] == ["stream-a-peer"]
    assert analyzed_contexts[0].higher_priority_flows == ()
    assert analyzed_contexts[0].lower_priority_flows == ()


def test_best_effort_streams_are_excluded_from_analysis_contexts(sample_case_path) -> None:
    """Best-effort streams should not produce AVB analytical link contexts."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    case_with_be = deepcopy(prepared.normalized_case)
    case_with_be.streams.append(
        replace(
            case_with_be.streams[0],
            id="stream-be",
            name="BE stream",
            traffic_class=TrafficClass.BEST_EFFORT,
            route_id="route-stream-be",
            priority=0,
        )
    )
    case_with_be.routes.append(
        Route(
            stream_id="stream-be",
            route_id="route-stream-be",
            hops=deepcopy(case_with_be.routes[0].hops),
        )
    )

    contexts = build_link_traffic_contexts(case_with_be)

    assert {context.stream_id for context in contexts} == {"stream-a"}


def test_reserved_share_up_to_class_uses_queue_reservations_even_without_higher_priority_flows(
    sample_case_path,
) -> None:
    """Class B contexts should include Class A reservation even when no Class A stream is present."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    case_only_b = deepcopy(prepared.normalized_case)
    case_only_b.streams = [
        replace(
            case_only_b.streams[0],
            id="stream-b-only",
            name="B-only stream",
            traffic_class=TrafficClass.CLASS_B,
            route_id="route-stream-b-only",
            priority=1,
        )
    ]
    case_only_b.routes = [
        Route(
            stream_id="stream-b-only",
            route_id="route-stream-b-only",
            hops=deepcopy(prepared.normalized_case.routes[0].hops),
        )
    ]

    contexts = build_link_traffic_contexts(case_only_b)

    assert contexts
    assert all(context.traffic_class == TrafficClass.CLASS_B for context in contexts)
    assert all(context.reserved_share == 0.5 for context in contexts)
    assert all(context.reserved_share_up_to_class == 1.0 for context in contexts)
