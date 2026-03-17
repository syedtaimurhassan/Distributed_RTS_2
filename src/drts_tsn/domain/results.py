"""Canonical result models shared across subsystem boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import ResultStatus


@dataclass(slots=True, frozen=True)
class ExpectedResult:
    """Expected values provided by the external case format."""

    stream_id: str
    expected_wcrt_us: float


@dataclass(slots=True)
class SimulationStreamResult:
    """Per-stream simulation output."""

    stream_id: str
    max_response_time_us: float | None = None
    frame_count: int = 0
    status: ResultStatus = ResultStatus.STUB
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AnalysisStreamResult:
    """Per-stream analytical output."""

    stream_id: str
    wcrt_us: float | None = None
    status: ResultStatus = ResultStatus.STUB
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ComparisonEntry:
    """Aligned comparison output for a single stream."""

    stream_id: str
    analysis_traffic_class: str | None = None
    simulation_traffic_class: str | None = None
    analysis_route_id: str | None = None
    simulation_route_id: str | None = None
    analysis_hop_count: int | None = None
    simulation_hop_count: int | None = None
    analytical_wcrt_us: float | None = None
    simulated_worst_response_time_us: float | None = None
    expected_wcrt_us: float | None = None
    absolute_difference_us: float | None = None
    analysis_minus_simulation_margin_us: float | None = None
    analysis_to_simulation_ratio: float | None = None
    simulation_exceeded_analysis: bool | None = None
    class_mismatch: bool = False
    path_mismatch: bool = False
    expected_minus_analysis_us: float | None = None
    expected_minus_simulation_us: float | None = None
    discrepancy_flags: list[str] = field(default_factory=list)
    status: ResultStatus = ResultStatus.STUB
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SimulationRunResult:
    """Top-level simulation result container."""

    case_id: str
    run_id: str
    stream_results: list[SimulationStreamResult] = field(default_factory=list)
    detail_rows: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    trace_rows: list[dict[str, Any]] = field(default_factory=list)
    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class AnalysisRunResult:
    """Top-level analysis result container."""

    case_id: str
    run_id: str
    stream_results: list[AnalysisStreamResult] = field(default_factory=list)
    detail_rows: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    trace_rows: list[dict[str, Any]] = field(default_factory=list)
    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ComparisonRunResult:
    """Top-level comparison result container."""

    case_id: str
    run_id: str
    entries: list[ComparisonEntry] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
