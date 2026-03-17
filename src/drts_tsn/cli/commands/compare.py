"""CLI handler for result comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

from drts_tsn.cli.presenters.console_messages import print_error, print_info
from drts_tsn.cli.presenters.console_tables import render_mapping
from drts_tsn.orchestration.pipeline_compare import execute


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the `compare` subcommand."""

    parser = subparsers.add_parser("compare", help="Compare simulation and analytical outputs.")
    parser.add_argument("--simulation-result", type=Path, required=True, help="Simulation result JSON path.")
    parser.add_argument("--analysis-result", type=Path, required=True, help="Analysis result JSON path.")
    parser.add_argument("--output-config", type=Path, default=None, help="Output config YAML.")
    parser.add_argument("--run-id", default=None, help="Optional explicit run ID.")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    """Execute the comparison command."""

    try:
        result, layout = execute(
            simulation_result_path=args.simulation_result,
            analysis_result_path=args.analysis_result,
            output_config_path=args.output_config,
            run_id=args.run_id,
        )
        print_info(render_mapping({"case_id": result.case_id, "run_id": layout.run_id, "run_dir": layout.run_dir}))
        return 0
    except Exception as exc:  # noqa: BLE001
        print_error(str(exc))
        return 4
