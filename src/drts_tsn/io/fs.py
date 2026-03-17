"""Small filesystem helpers shared across the scaffold."""

from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not already exist."""

    path.mkdir(parents=True, exist_ok=True)
    return path


def list_directories(path: Path) -> list[Path]:
    """Return sorted child directories under the provided path."""

    if not path.exists():
        return []
    return sorted([child for child in path.iterdir() if child.is_dir()])
