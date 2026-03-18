"""Canonical route entities for end-to-end stream paths."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class RouteHop:
    """One hop in a route."""

    node_id: str
    link_id: str | None = None
    transmission_time_us: float | None = None
    egress_port_id: str | None = None


@dataclass(slots=True)
class Route:
    """The canonical route for a stream."""

    stream_id: str
    route_id: str | None = None
    hops: list[RouteHop] = field(default_factory=list)


def route_link_ids(route: Route) -> list[str]:
    """Return resolved link identifiers from a normalized route."""

    return [hop.link_id for hop in route.hops[:-1] if hop.link_id is not None]


def route_link_ids_by_stream(routes: Iterable[Route]) -> dict[str, list[str]]:
    """Return per-stream directed link paths resolved from normalized routes."""

    return {route.stream_id: route_link_ids(route) for route in routes}


def active_route_link_ids(routes: Iterable[Route]) -> set[str]:
    """Return the set of directed link identifiers actively used by routes."""

    active_link_ids: set[str] = set()
    for route in routes:
        active_link_ids.update(route_link_ids(route))
    return active_link_ids
