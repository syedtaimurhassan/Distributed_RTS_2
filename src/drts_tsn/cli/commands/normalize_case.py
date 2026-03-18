"""CLI handler for case normalization."""

from __future__ import annotations

import argparse
from pathlib import Path

from drts_tsn.cli.presenters.console_messages import print_error, print_info
from drts_tsn.cli.presenters.console_tables import render_mapping
from drts_tsn.cli.presenters.exit_codes import ExitCode
from drts_tsn.io.paths import project_root
from drts_tsn.orchestration.run_manager import (
    assert_case_readiness,
    export_prepared_case_bundle,
    prepare_case,
)
from drts_tsn.validation.errors import CaseReadinessError, CaseValidationError


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the `normalize-case` subcommand."""

    parser = subparsers.add_parser("normalize-case", help="Normalize an external case directory.")
    parser.add_argument("case_path", help="Path to the external case directory.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for normalized JSON and CSV artifacts.",
    )
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    """Execute the normalization command."""

    try:
        prepared = prepare_case(args.case_path)
        assert_case_readiness(prepared, stage="normalization")
        destination_directory = args.output_dir or (
            project_root() / "cases" / "normalized" / prepared.normalized_case.metadata.case_id
        )
        artifacts = export_prepared_case_bundle(prepared, destination_directory)
        print_info(
            render_mapping(
                {
                    "output_dir": destination_directory,
                    "artifact_count": len(artifacts),
                    "normalized_case_json": artifacts["normalized_case.json"],
                }
        )
        )
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return ExitCode.VALIDATION_FAILED
    except CaseValidationError as exc:
        print_error(str(exc))
        print_info(render_mapping({"validation_issue_count": len(exc.report.issues)}))
        return ExitCode.VALIDATION_FAILED
    except CaseReadinessError as exc:
        print_error(str(exc))
        return ExitCode.VALIDATION_FAILED
    except Exception as exc:  # noqa: BLE001
        print_error(str(exc))
        return ExitCode.RUNTIME_ERROR
