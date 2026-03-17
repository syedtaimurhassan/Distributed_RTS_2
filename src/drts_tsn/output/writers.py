"""Shared output configuration and writing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drts_tsn.io.paths import project_root
from drts_tsn.io.yaml_io import read_yaml


@dataclass(slots=True)
class OutputConfig:
    """Configurable output behavior for orchestration pipelines."""

    write_json: bool = True
    write_csv: bool = True
    write_metadata: bool = True
    write_trace_csv: bool = False
    symlink_latest: bool = True


def load_output_config(path: Path | None = None) -> OutputConfig:
    """Load output configuration from YAML or return defaults."""

    config_path = path or (project_root() / "configs" / "output" / "default.yaml")
    data = dict(read_yaml(config_path) or {})
    return OutputConfig(
        write_json=bool(data.get("write_json", True)),
        write_csv=bool(data.get("write_csv", True)),
        write_metadata=bool(data.get("write_metadata", True)),
        write_trace_csv=bool(data.get("write_trace_csv", False)),
        symlink_latest=bool(data.get("symlink_latest", True)),
    )
