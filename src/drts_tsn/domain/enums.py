"""Enums shared by canonical TSN domain models."""

from __future__ import annotations

from enum import Enum


class TrafficClass(str, Enum):
    """Supported traffic classes for the simplified TSN baseline."""

    CLASS_A = "class_a"
    CLASS_B = "class_b"
    BEST_EFFORT = "best_effort"

    @classmethod
    def from_external(cls, value: str) -> "TrafficClass":
        """Normalize supported external traffic-class spellings into the canonical enum."""

        normalized = value.strip().lower().replace("-", "_")
        aliases = {
            "class_a": cls.CLASS_A,
            "avb_a": cls.CLASS_A,
            "a": cls.CLASS_A,
            "class_b": cls.CLASS_B,
            "avb_b": cls.CLASS_B,
            "b": cls.CLASS_B,
            "best_effort": cls.BEST_EFFORT,
            "be": cls.BEST_EFFORT,
            "besteffort": cls.BEST_EFFORT,
        }
        if normalized not in aliases:
            raise ValueError(
                "Unsupported traffic class "
                f"'{value}'. Baseline mode accepts only AVB_A, AVB_B, or BE."
            )
        return aliases[normalized]

    @property
    def display_name(self) -> str:
        """Return the baseline display label."""

        return {
            TrafficClass.CLASS_A: "AVB_A",
            TrafficClass.CLASS_B: "AVB_B",
            TrafficClass.BEST_EFFORT: "BE",
        }[self]


class NodeType(str, Enum):
    """Node roles supported by the baseline topology model."""

    END_SYSTEM = "end_system"
    SWITCH = "switch"

    @classmethod
    def from_external(cls, value: str) -> "NodeType":
        """Normalize supported external node-type spellings."""

        normalized = value.strip().lower().replace("-", "_")
        aliases = {
            "end_system": cls.END_SYSTEM,
            "endsystem": cls.END_SYSTEM,
            "host": cls.END_SYSTEM,
            "talker": cls.END_SYSTEM,
            "listener": cls.END_SYSTEM,
            "switch": cls.SWITCH,
            "bridge": cls.SWITCH,
        }
        if normalized not in aliases:
            raise ValueError(
                f"Unsupported node type '{value}'. Baseline mode accepts only end_system or switch."
            )
        return aliases[normalized]


class ResultStatus(str, Enum):
    """Status labels used by scaffold result objects."""

    STUB = "stub"
    OK = "ok"
    ERROR = "error"
