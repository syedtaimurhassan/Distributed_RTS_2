"""Shared pytest fixtures for the scaffold."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest


@pytest.fixture()
def repo_root() -> Path:
    """Return the repository root."""

    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def sample_case_path(repo_root: Path) -> Path:
    """Return the stable one-stream sample case used by automated tests."""

    return repo_root / "tests" / "fixtures" / "sample_case_root" / "test-case-1"


@pytest.fixture()
def invalid_case_path(repo_root: Path) -> Path:
    """Return the invalid fixture case path."""

    return repo_root / "tests" / "fixtures" / "cases" / "invalid_missing_node"


@pytest.fixture()
def invalid_reserved_bandwidth_case_path(repo_root: Path) -> Path:
    """Return the invalid reserved-bandwidth fixture case path."""

    return repo_root / "tests" / "fixtures" / "cases" / "invalid_reserved_bandwidth"


@pytest.fixture()
def assert_csv_contract():
    """Return a helper that asserts a CSV header matches the declared contract."""

    def _assert_csv_contract(path: Path, expected_columns: list[str]) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == expected_columns
            return list(reader)

    return _assert_csv_contract
