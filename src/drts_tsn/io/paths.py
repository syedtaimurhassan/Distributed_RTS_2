"""Filesystem path helpers for project inputs, configs, and outputs."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Return the repository root inferred from the module location."""

    return Path(__file__).resolve().parents[3]


def cases_root() -> Path:
    """Return the top-level case directory."""

    return project_root() / "cases"


def outputs_root() -> Path:
    """Return the default outputs directory."""

    return project_root() / "outputs"


def resolve_case_path(case_path: str | Path) -> Path:
    """Resolve a user-provided case path into an absolute path."""

    path = Path(case_path)
    return path if path.is_absolute() else (project_root() / path).resolve()
