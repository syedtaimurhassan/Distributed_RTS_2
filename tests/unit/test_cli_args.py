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
