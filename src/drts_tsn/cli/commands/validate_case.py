"""CLI handler for case validation."""

from __future__ import annotations

import argparse

from drts_tsn.cli.presenters.console_messages import print_error, print_info
from drts_tsn.cli.presenters.console_tables import render_validation_report
from drts_tsn.cli.presenters.exit_codes import ExitCode
from drts_tsn.orchestration.run_manager import prepare_case


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the `validate-case` subcommand."""

    parser = subparsers.add_parser("validate-case", help="Validate an external case directory.")
    parser.add_argument("case_path", help="Path to the external case directory.")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    """Execute the validation command."""

    try:
        prepared = prepare_case(args.case_path)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return ExitCode.VALIDATION_FAILED
    except Exception as exc:  # noqa: BLE001
        print_error(str(exc))
        return ExitCode.RUNTIME_ERROR
    print_info(render_validation_report(prepared.validation_report))
    return ExitCode.SUCCESS if prepared.validation_report.is_valid else ExitCode.VALIDATION_FAILED
