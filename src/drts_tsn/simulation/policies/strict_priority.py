"""Strict-priority scheduling helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def select_highest_priority(items: Iterable[T]) -> T | None:
    """Return the first item in already-prioritized order."""

    for item in items:
        return item
    return None
