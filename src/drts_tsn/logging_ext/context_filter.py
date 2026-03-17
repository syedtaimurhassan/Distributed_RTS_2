"""Logging filter that injects static context."""

from __future__ import annotations

import logging


class ContextFilter(logging.Filter):
    """Attach fixed context fields to log records."""

    def __init__(self, **context: object) -> None:
        super().__init__()
        self._context = context

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply stored context to the log record."""

        for key, value in self._context.items():
            setattr(record, key, value)
        return True
