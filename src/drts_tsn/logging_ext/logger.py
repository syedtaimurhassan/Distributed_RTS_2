"""Logging configuration helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from drts_tsn.io.paths import project_root
from drts_tsn.io.yaml_io import read_yaml


def configure_logging(config_path: Path | None = None) -> None:
    """Configure standard library logging from a YAML file."""

    resolved = config_path or (project_root() / "configs" / "logging" / "default.yaml")
    data = dict(read_yaml(resolved) or {})
    logging.basicConfig(
        level=getattr(logging, str(data.get("level", "INFO")).upper(), logging.INFO),
        format=str(data.get("format", "%(levelname)s | %(message)s")),
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger."""

    return logging.getLogger(name)
