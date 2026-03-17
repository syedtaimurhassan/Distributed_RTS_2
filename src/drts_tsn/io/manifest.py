"""Helpers for loading and storing case manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .yaml_io import read_yaml, write_yaml


DEFAULT_MANIFEST_NAME = "manifest.yaml"


def load_manifest(case_directory: Path) -> dict[str, Any]:
    """Load a case manifest when it exists, otherwise return an empty mapping."""

    manifest_path = case_directory / DEFAULT_MANIFEST_NAME
    if not manifest_path.exists():
        return {}
    return dict(read_yaml(manifest_path) or {})


def write_manifest(data: dict[str, Any], case_directory: Path) -> Path:
    """Write a manifest into the target case directory."""

    return write_yaml(data, case_directory / DEFAULT_MANIFEST_NAME)
