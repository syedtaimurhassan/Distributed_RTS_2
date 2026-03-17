"""Parser wiring tests for the CLI."""

from __future__ import annotations

from drts_tsn.cli.args import build_parser


def test_parser_registers_validate_case_command() -> None:
    """The parser should wire Milestone 1 command arguments and handler."""

    parser = build_parser()
    args = parser.parse_args(["validate-case", "cases/external/test-case-1"])
    assert args.command == "validate-case"
    assert args.case_path == "cases/external/test-case-1"
    assert callable(args.handler)


def test_parser_registers_analyze_command() -> None:
    """The parser should wire the Milestone 2 analyze command."""

    parser = build_parser()
    args = parser.parse_args(["analyze", "cases/external/test-case-1"])
    assert args.command == "analyze"
    assert args.case_path == "cases/external/test-case-1"
    assert callable(args.handler)


def test_parser_registers_simulate_command() -> None:
    """The parser should wire the baseline simulation command."""

    parser = build_parser()
    args = parser.parse_args(["simulate", "cases/external/test-case-1"])
    assert args.command == "simulate"
    assert args.case_path == "cases/external/test-case-1"
    assert callable(args.handler)


def test_parser_registers_compare_command() -> None:
    """The parser should wire the comparison command."""

    parser = build_parser()
    args = parser.parse_args(
        [
            "compare",
            "--simulation-result",
            "outputs/runs/sim/simulation/results/simulation_result.json",
            "--analysis-result",
            "outputs/runs/ana/analysis/results/analysis_result.json",
        ]
    )
    assert args.command == "compare"
    assert callable(args.handler)


def test_parser_registers_run_case_command() -> None:
    """The parser should wire the end-to-end run-case command."""

    parser = build_parser()
    args = parser.parse_args(["run-case", "cases/external/test-case-1"])
    assert args.command == "run-case"
    assert args.case_path == "cases/external/test-case-1"
    assert callable(args.handler)


def test_parser_registers_batch_run_command() -> None:
    """The parser should wire the batch-run command."""

    parser = build_parser()
    args = parser.parse_args(["batch-run", "cases/external", "--operation", "run-case"])
    assert args.command == "batch-run"
    assert str(args.cases_root) == "cases/external"
    assert args.operation == "run-case"
    assert callable(args.handler)
