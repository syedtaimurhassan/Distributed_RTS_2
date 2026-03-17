"""CLI handler for batch execution over multiple case directories."""

from __future__ import annotations

import argparse
from pathlib import Path

from drts_tsn.cli.presenters.console_messages import print_error, print_info
from drts_tsn.cli.presenters.console_tables import render_mapping
from drts_tsn.orchestration.batch_manager import run_batch


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the `batch-run` subcommand."""

    parser = subparsers.add_parser("batch-run", help="Run a selected pipeline over case directories.")
    parser.add_argument("cases_root", type=Path, help="Root directory containing case subdirectories.")
    parser.add_argument(
        "--operation",
        choices=("simulate", "analyze", "run-case"),
        default="run-case",
        help="Pipeline operation to execute per case.",
    )
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    """Execute the batch command."""

    try:
        outcomes = run_batch(args.cases_root, operation=args.operation)
        print_info(render_mapping({"operation": args.operation, "case_count": len(outcomes)}))
        for outcome in outcomes:
            print_info(render_mapping(outcome))
        return 0
    except Exception as exc:  # noqa: BLE001
        print_error(str(exc))
        return 4
