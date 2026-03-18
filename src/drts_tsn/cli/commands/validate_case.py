"""CLI handler for case validation."""

from __future__ import annotations

import argparse

from drts_tsn.cli.presenters.console_messages import print_error, print_info
from drts_tsn.cli.presenters.console_tables import render_mapping, render_validation_report
from drts_tsn.cli.presenters.exit_codes import ExitCode
from drts_tsn.orchestration.run_manager import prepare_case
from drts_tsn.validation.readiness import READINESS_STAGES


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the `validate-case` subcommand."""

    parser = subparsers.add_parser("validate-case", help="Validate an external case directory.")
    parser.add_argument("case_path", help="Path to the external case directory.")
    parser.add_argument(
        "--stage",
        choices=READINESS_STAGES,
        default="normalization",
        help=(
            "Readiness stage to validate: schema, normalization, baseline, simulation, "
            "analysis, or all."
        ),
    )
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
    readiness = prepared.readiness_report
    selected_stage = str(args.stage)
    selected_report = readiness.report_for_stage(selected_stage)
    selected_status = readiness.status_for_stage(selected_stage)
    summary = {
        "selected_stage": selected_stage,
        "selected_stage_valid": selected_status,
        **readiness.status_mapping(),
    }
    print_info(render_mapping(summary))
    if selected_stage != "schema":
        print_info(render_validation_report(selected_report))
    if selected_status:
        return ExitCode.SUCCESS
    if selected_stage in {"baseline", "simulation", "analysis", "all"}:
        return ExitCode.READINESS_FAILED
    return ExitCode.VALIDATION_FAILED
