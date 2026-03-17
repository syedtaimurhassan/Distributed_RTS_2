"""CLI handler for case inspection."""

from __future__ import annotations

import argparse

from drts_tsn.cli.presenters.console_messages import print_error, print_info
from drts_tsn.cli.presenters.console_tables import render_case_inspection
from drts_tsn.cli.presenters.exit_codes import ExitCode
from drts_tsn.orchestration.run_manager import inspect_prepared_case_detailed, prepare_case


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the `inspect-case` subcommand."""

    parser = subparsers.add_parser("inspect-case", help="Inspect a case summary.")
    parser.add_argument("case_path", help="Path to the external case directory.")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    """Execute the inspection command."""

    try:
        prepared = prepare_case(args.case_path)
        print_info(render_case_inspection(inspect_prepared_case_detailed(prepared)))
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return ExitCode.VALIDATION_FAILED
    except Exception as exc:  # noqa: BLE001
        print_error(str(exc))
        return ExitCode.RUNTIME_ERROR
