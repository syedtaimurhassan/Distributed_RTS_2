"""Load external case files from disk into raw structured bundles."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from drts_tsn.io.csv_io import read_csv_rows
from drts_tsn.io.json_io import read_json
from drts_tsn.io.manifest import load_manifest

from .parser_expected_wcrts import parse_expected_wcrts_rows
from .parser_routes import parse_routes_payload
from .parser_streams import parse_streams_payload
from .parser_topology import parse_topology_payload
from .schema_checks import infer_case_filenames, missing_optional_files, missing_required_files


@dataclass(slots=True)
class ExternalCaseBundle:
    """Raw external case content loaded from disk."""

    case_directory: Path
    manifest: dict[str, Any] = field(default_factory=dict)
    topology: dict[str, Any] = field(default_factory=dict)
    routes: list[dict[str, Any]] = field(default_factory=list)
    streams: list[dict[str, Any]] = field(default_factory=list)
    expected_wcrts: list[dict[str, Any]] = field(default_factory=list)
    missing_optional_files: list[str] = field(default_factory=list)
    filenames: dict[str, str] = field(default_factory=dict)


def load_external_case(case_directory: Path) -> ExternalCaseBundle:
    """Load an external case directory and perform basic file presence checks."""

    manifest = load_manifest(case_directory)
    filenames = infer_case_filenames(case_directory, manifest=manifest)
    missing = missing_required_files(case_directory, filenames)
    if missing:
        raise FileNotFoundError(
            f"Case directory '{case_directory}' is missing required files: {', '.join(missing)}"
        )

    bundle = ExternalCaseBundle(case_directory=case_directory)
    bundle.manifest = manifest
    bundle.filenames = filenames
    bundle.topology = parse_topology_payload(read_json(case_directory / filenames["topology"]))
    bundle.routes = parse_routes_payload(read_json(case_directory / filenames["routes"]))
    bundle.streams = parse_streams_payload(read_json(case_directory / filenames["streams"]))
    expected_path = case_directory / filenames["expected_wcrts"]
    if expected_path.exists():
        bundle.expected_wcrts = parse_expected_wcrts_rows(
            read_csv_rows(expected_path)
        )
    bundle.missing_optional_files = missing_optional_files(case_directory, filenames)
    return bundle
