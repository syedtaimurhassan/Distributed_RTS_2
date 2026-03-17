"""Alignment helpers for stable analysis and simulation output tables."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class AlignedStreamRow:
    """One stream-level alignment between analysis and simulation summaries."""

    stream_id: str
    analysis_row: dict[str, object] | None = None
    simulation_row: dict[str, object] | None = None


@dataclass(slots=True)
class AlignmentResult:
    """Aligned rows plus machine-readable diagnostics about the inputs."""

    aligned_rows: list[AlignedStreamRow] = field(default_factory=list)
    diagnostics: list[dict[str, object]] = field(default_factory=list)


def _index_rows(
    rows: list[dict[str, object]],
    *,
    source_name: str,
) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    """Index rows by canonical stream ID and report duplicate identifiers."""

    counts = Counter(str(row["stream_id"]) for row in rows)
    indexed: dict[str, dict[str, object]] = {}
    diagnostics: list[dict[str, object]] = []
    for row in rows:
        stream_id = str(row["stream_id"])
        if stream_id not in indexed:
            indexed[stream_id] = row
    for stream_id, count in sorted(counts.items()):
        if count > 1:
            diagnostics.append(
                {
                    "diagnostic_code": f"comparison.duplicate.{source_name}_stream_id",
                    "severity": "error",
                    "stream_id": stream_id,
                    "source": source_name,
                    "message": (
                        f"{source_name.capitalize()} results contain {count} rows for stream "
                        f"'{stream_id}'. The first row is used for comparison."
                    ),
                }
            )
    return indexed, diagnostics


def align_stream_rows(
    *,
    analysis_rows: list[dict[str, object]],
    simulation_rows: list[dict[str, object]],
) -> AlignmentResult:
    """Align stream summary rows by canonical stream ID."""

    indexed_analysis, diagnostics = _index_rows(analysis_rows, source_name="analysis")
    indexed_simulation, simulation_diagnostics = _index_rows(
        simulation_rows,
        source_name="simulation",
    )
    diagnostics.extend(simulation_diagnostics)
    stream_ids = sorted(set(indexed_analysis) | set(indexed_simulation))
    return AlignmentResult(
        aligned_rows=[
            AlignedStreamRow(
                stream_id=stream_id,
                analysis_row=indexed_analysis.get(stream_id),
                simulation_row=indexed_simulation.get(stream_id),
            )
            for stream_id in stream_ids
        ],
        diagnostics=diagnostics,
    )
