"""FIFO queue policy helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def fifo_select(items: Sequence[T]) -> T | None:
    """Return the first item in FIFO order."""

    return items[0] if items else None
