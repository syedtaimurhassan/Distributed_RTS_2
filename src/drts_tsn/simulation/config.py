"""Simulation configuration models and loaders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drts_tsn.io.paths import project_root
from drts_tsn.io.yaml_io import read_yaml


@dataclass(slots=True)
class SimulationConfig:
    """Configuration values consumed by the simulation scaffold."""

    trace_enabled: bool = False
    max_events: int = 100_000
    time_limit_us: float | None = None
    max_releases_per_stream: int | None = 1
    max_deliveries_total: int | None = None
    stop_when_all_streams_observed: bool = True
    max_hyperperiod_us: int = 100_000


def load_simulation_config(path: Path | None = None) -> SimulationConfig:
    """Load simulation configuration from YAML or return defaults."""

    config_path = path or (project_root() / "configs" / "simulation" / "default.yaml")
    data = dict(read_yaml(config_path) or {})
    max_releases_per_stream = data.get("max_releases_per_stream", 1)
    max_deliveries_total = data.get("max_deliveries_total")
    return SimulationConfig(
        trace_enabled=bool(data.get("trace_enabled", False)),
        max_events=int(data.get("max_events", 100_000)),
        time_limit_us=float(data["time_limit_us"]) if data.get("time_limit_us") is not None else None,
        max_releases_per_stream=(
            int(max_releases_per_stream) if max_releases_per_stream is not None else None
        ),
        max_deliveries_total=int(max_deliveries_total) if max_deliveries_total is not None else None,
        stop_when_all_streams_observed=bool(data.get("stop_when_all_streams_observed", True)),
        max_hyperperiod_us=int(data.get("max_hyperperiod_us", 100_000)),
    )
