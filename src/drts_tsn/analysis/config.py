"""Analysis configuration models and loaders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drts_tsn.io.paths import project_root
from drts_tsn.io.yaml_io import read_yaml


@dataclass(slots=True)
class AnalysisConfig:
    """Configuration values consumed by the analysis scaffold."""

    strict_validation: bool = True
    emit_explanations: bool = True
    fixed_point_limit: int = 100
    response_time_limit_us: float = 1_000_000.0


def load_analysis_config(path: Path | None = None) -> AnalysisConfig:
    """Load analysis configuration from YAML or return defaults."""

    config_path = path or (project_root() / "configs" / "analysis" / "default.yaml")
    data = dict(read_yaml(config_path) or {})
    return AnalysisConfig(
        strict_validation=bool(data.get("strict_validation", True)),
        emit_explanations=bool(data.get("emit_explanations", True)),
        fixed_point_limit=int(data.get("fixed_point_limit", 100)),
        response_time_limit_us=float(data.get("response_time_limit_us", 1_000_000.0)),
    )
