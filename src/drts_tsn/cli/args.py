"""Argument parser construction for the baseline `drts` CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from .commands import analyze, inspect_case, normalize_case, simulate, validate_case


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser and register subcommands."""

    parser = argparse.ArgumentParser(
        prog="drts",
        description="TSN case ingestion, normalization, inspection, baseline AVB analysis, and simulation.",
    )
    parser.add_argument(
        "--logging-config",
        type=Path,
        default=None,
        help="Optional logging config YAML.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_case.register(subparsers)
    normalize_case.register(subparsers)
    inspect_case.register(subparsers)
    analyze.register(subparsers)
    simulate.register(subparsers)
    return parser
