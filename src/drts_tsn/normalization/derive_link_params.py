"""Derive or fill link-related canonical parameters."""

from __future__ import annotations

from dataclasses import replace

from drts_tsn.common.constants import DEFAULT_LINK_SPEED_MBPS
from drts_tsn.domain.case import Case
from drts_tsn.domain.topology import Topology


def derive_link_parameters(case: Case) -> Case:
    """Fill default link speeds when the external case omits them."""

    default_speed = float(case.parameters.get("link_speed_mbps", DEFAULT_LINK_SPEED_MBPS))
    topology = Topology(
        nodes=case.topology.nodes,
        links=[
            replace(link, speed_mbps=link.speed_mbps or default_speed)
            for link in case.topology.links
        ],
        ports=case.topology.ports,
    )
    return replace(case, topology=topology)
