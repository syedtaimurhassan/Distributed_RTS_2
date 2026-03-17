"""Console message helpers."""

from __future__ import annotations

import sys


def print_info(message: str) -> None:
    """Print an informational message."""

    print(message)


def print_error(message: str) -> None:
    """Print an error message."""

    print(message, file=sys.stderr)
