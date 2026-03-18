"""Unit tests for stricter baseline validation."""

from __future__ import annotations

from copy import deepcopy

from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.routes import Route, RouteHop
from drts_tsn.domain.streams import Stream
from drts_tsn.domain.topology import Link, Node
from drts_tsn.domain.enums import NodeType
from drts_tsn.normalization.normalize_case import normalize_case
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.validation.case_validator import validate_case


def _new_stream(stream_id: str, source: str, destination: str, route_id: str) -> Stream:
    """Build a baseline-compatible synthetic stream for assumption tests."""

    return Stream(
        id=stream_id,
        name=stream_id,
        source_node_id=source,
        destination_node_id=destination,
        traffic_class=TrafficClass.CLASS_A,
        period_us=1000.0,
        deadline_us=1000.0,
        max_frame_size_bytes=1024,
        route_id=route_id,
        priority=2,
    )


def test_validation_accepts_full_duplex_topology_when_active_routes_are_one_direction(sample_case_path) -> None:
    """Unused reverse links should not break baseline line/single-direction assumptions."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    case_with_unused_reverse_links = deepcopy(prepared.normalized_case)
    case_with_unused_reverse_links.topology.links.extend(
        [
            Link(id="link-1-reverse", source_node_id="sw1", target_node_id="talker", speed_mbps=100.0),
            Link(id="link-2-reverse", source_node_id="listener", target_node_id="sw1", speed_mbps=100.0),
        ]
    )

    report = validate_case(case_with_unused_reverse_links, include_analysis_checks=True)

    assert report.is_valid


def test_validation_rejects_non_line_behavior_when_active_routes_branch(sample_case_path) -> None:
    """Branching in active directed routes must be rejected under line-topology assumptions."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    invalid_case = deepcopy(prepared.normalized_case)
    invalid_case.topology.nodes.append(Node(id="branch", type=NodeType.END_SYSTEM))
    invalid_case.topology.links.append(
        Link(
            id="link-branch",
            source_node_id="sw1",
            target_node_id="branch",
            speed_mbps=100.0,
        )
    )
    invalid_case.streams.append(_new_stream("stream-branch", "talker", "branch", "route-stream-branch"))
    invalid_case.routes.append(
        Route(
            route_id="route-stream-branch",
            stream_id="stream-branch",
            hops=[RouteHop(node_id="talker"), RouteHop(node_id="sw1"), RouteHop(node_id="branch")],
        )
    )

    report = validate_case(normalize_case(invalid_case), include_analysis_checks=True)

    assert not report.is_valid
    assert any(issue.code == "assumptions.line-topology.branching" for issue in report.issues)


def test_validation_rejects_mixed_active_route_directions_under_single_direction_assumption(sample_case_path) -> None:
    """Active routes that use opposite directions should fail the one-direction baseline check."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    invalid_case = deepcopy(prepared.normalized_case)
    invalid_case.topology.links.extend(
        [
            Link(id="link-1-reverse", source_node_id="sw1", target_node_id="talker", speed_mbps=100.0),
            Link(id="link-2-reverse", source_node_id="listener", target_node_id="sw1", speed_mbps=100.0),
        ]
    )
    invalid_case.streams.append(_new_stream("stream-reverse", "listener", "talker", "route-stream-reverse"))
    invalid_case.routes.append(
        Route(
            route_id="route-stream-reverse",
            stream_id="stream-reverse",
            hops=[RouteHop(node_id="listener"), RouteHop(node_id="sw1"), RouteHop(node_id="talker")],
        )
    )

    report = validate_case(normalize_case(invalid_case), include_analysis_checks=True)

    assert not report.is_valid
    assert any(issue.code == "assumptions.single-direction.directionality" for issue in report.issues)
