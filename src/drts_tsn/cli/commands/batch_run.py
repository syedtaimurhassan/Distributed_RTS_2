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
    parser.add_argument("--simulation-config", type=Path, default=None, help="Simulation config YAML.")
    parser.add_argument("--analysis-config", type=Path, default=None, help="Analysis config YAML.")
    parser.add_argument("--output-config", type=Path, default=None, help="Output config YAML.")
    parser.add_argument("--output-root", type=Path, default=None, help="Override the outputs root directory.")
    parser.add_argument("--batch-id", default=None, help="Optional explicit batch ID.")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    """Execute the batch command."""

    try:
        outcomes, layout = run_batch(
            args.cases_root,
            operation=args.operation,
            simulation_config_path=args.simulation_config,
            analysis_config_path=args.analysis_config,
            output_config_path=args.output_config,
            output_root=args.output_root,
            batch_id=args.batch_id,
        )
        success_count = sum(1 for outcome in outcomes if outcome["status"] == "success")
        failure_count = len(outcomes) - success_count
        print_info(
            render_mapping(
                {
                    "batch_id": layout.batch_id,
                    "batch_dir": layout.batch_dir,
                    "operation": args.operation,
                    "case_count": len(outcomes),
                    "success_count": success_count,
                    "failure_count": failure_count,
                }
            )
        )
        for outcome in outcomes:
            print_info(
                render_mapping(
                    {
                        "case_name": outcome["case_name"],
                        "status": outcome["status"],
                        "run_id": outcome["run_id"],
                        "run_dir": outcome["run_dir"],
                        "error_message": outcome["error_message"],
                    }
                )
            )
        return 0 if failure_count == 0 else 4
    except Exception as exc:  # noqa: BLE001
        print_error(str(exc))
        return 4
