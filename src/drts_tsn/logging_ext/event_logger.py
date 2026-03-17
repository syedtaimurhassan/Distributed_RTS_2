"""Structured event logging helper."""

from __future__ import annotations

from typing import Any

from .logger import get_logger


def log_event(name: str, **fields: Any) -> None:
    """Emit a lightweight structured event message."""

    logger = get_logger("drts.event")
    logger.debug("event=%s fields=%s", name, fields)
