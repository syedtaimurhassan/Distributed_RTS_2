"""Export simplified report-ready summaries."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.domain.case import Case
from drts_tsn.io.json_io import write_json


def export_case_summary(case: Case, destination: Path) -> Path:
    """Write a concise summary JSON file for reporting use."""

    summary = {
        "case_id": case.metadata.case_id,
        "name": case.metadata.name,
        "stream_count": len(case.streams),
        "route_count": len(case.routes),
        "assumptions": case.assumptions,
    }
    return write_json(summary, destination)
