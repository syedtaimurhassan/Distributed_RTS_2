"""Exit codes used by the CLI."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Stable process exit codes for scaffold commands."""

    SUCCESS = 0
    VALIDATION_FAILED = 2
    CONFIG_ERROR = 3
    RUNTIME_ERROR = 4
    READINESS_FAILED = 5
