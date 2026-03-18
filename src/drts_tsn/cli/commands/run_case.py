"""CLI handler for the combined case pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from drts_tsn.cli.presenters.console_messages import print_error, print_info
from drts_tsn.cli.presenters.console_tables import render_mapping
from drts_tsn.cli.presenters.exit_codes import ExitCode
from drts_tsn.orchestration.pipeline_run_case import execute
from drts_tsn.validation.errors import CaseReadinessError, CaseValidationError


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the `run-case` subcommand."""

    parser = subparsers.add_parser("run-case", help="Run simulate + analyze + compare for one case.")
    parser.add_argument("case_path", help="Path to the external case directory.")
    parser.add_argument("--simulation-config", type=Path, default=None, help="Simulation config YAML.")
    parser.add_argument("--analysis-config", type=Path, default=None, help="Analysis config YAML.")
    parser.add_argument("--output-config", type=Path, default=None, help="Output config YAML.")
    parser.add_argument("--run-id", default=None, help="Optional explicit run ID.")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    """Execute the combined pipeline command."""

    try:
        _, layout = execute(
            args.case_path,
            simulation_config_path=args.simulation_config,
            analysis_config_path=args.analysis_config,
            output_config_path=args.output_config,
            run_id=args.run_id,
        )
        print_info(render_mapping({"run_id": layout.run_id, "run_dir": layout.run_dir}))
        return ExitCode.SUCCESS
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return ExitCode.VALIDATION_FAILED
    except CaseValidationError as exc:
        print_error(str(exc))
        return ExitCode.VALIDATION_FAILED
    except CaseReadinessError as exc:
        print_error(str(exc))
        return ExitCode.READINESS_FAILED
    except Exception as exc:  # noqa: BLE001
        print_error(str(exc))
        return ExitCode.RUNTIME_ERROR
