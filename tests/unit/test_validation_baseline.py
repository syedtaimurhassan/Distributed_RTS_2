"""Unit tests for stricter baseline validation."""

from __future__ import annotations

from copy import deepcopy

from drts_tsn.domain.topology import Link, Node
from drts_tsn.domain.enums import NodeType
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.validation.case_validator import validate_case


def test_validation_rejects_branching_line_topology(sample_case_path) -> None:
    """A directed line topology must not branch in the baseline model."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    invalid_case = deepcopy(prepared.normalized_case)
    invalid_case.topology.nodes.append(Node(id="branch", type=NodeType.END_SYSTEM))
    invalid_case.topology.links.append(
        Link(
            id="link-branch",
            source_node_id="talker",
            target_node_id="branch",
            speed_mbps=100.0,
        )
    )

    report = validate_case(invalid_case, include_analysis_checks=True)

    assert not report.is_valid
    assert any(issue.code == "assumptions.line-topology.directionality" for issue in report.issues)
