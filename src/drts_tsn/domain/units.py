"""Typed unit aliases used across the canonical domain."""

from __future__ import annotations

from typing import NewType

Bytes = NewType("Bytes", int)
Microseconds = NewType("Microseconds", float)
MegabitsPerSecond = NewType("MegabitsPerSecond", float)
