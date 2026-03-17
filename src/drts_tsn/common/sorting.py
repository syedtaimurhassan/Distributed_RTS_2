"""Stable sorting helpers used by writers and reports."""

from __future__ import annotations

from typing import Iterable, Protocol, TypeVar


class HasIdentifier(Protocol):
    """Protocol for objects that expose an `id` attribute."""

    id: str


T = TypeVar("T", bound=HasIdentifier)


def sort_by_id(values: Iterable[T]) -> list[T]:
    """Return a list sorted by the object's `id` attribute."""

    return sorted(values, key=lambda item: item.id)
