"""Unit tests for external case loading and parsing."""

from __future__ import annotations

from pathlib import Path

from drts_tsn.adapters.external_cases.loader import load_external_case
from drts_tsn.adapters.external_cases.mapper import map_external_case
from drts_tsn.adapters.exports.normalized_case_exporter import export_normalized_case_bundle
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.io.csv_io import read_csv_rows
from drts_tsn.io.json_io import read_json, write_json
from drts_tsn.io.manifest import write_manifest
from drts_tsn.orchestration.run_manager import prepare_case


def test_loader_respects_manifest_selected_filenames(tmp_path: Path) -> None:
    """The loader should use filenames declared in the manifest."""

    case_dir = tmp_path / "case"
    case_dir.mkdir()
    write_manifest(
        {
            "case_id": "custom-case",
            "topology": "topo.json",
            "routes": "route-data.json",
            "streams": "stream-data.json",
        },
        case_dir,
    )
    write_json(
        {
            "nodes": [{"id": "n1", "type": "end_system"}],
            "links": [],
        },
        case_dir / "topo.json",
    )
    write_json(
        {
            "routes": [
                {"id": "r1", "stream_id": "s1", "hops": [{"node_id": "n1"}]},
            ]
        },
        case_dir / "route-data.json",
    )
    write_json(
        {
            "streams": [
                {
                    "id": "s1",
                    "source": "n1",
                    "destination": "n1",
                    "traffic_class": "BE",
                    "period_us": 1000,
                    "deadline_us": 1000,
                    "max_frame_size_bytes": 64,
                }
            ]
        },
        case_dir / "stream-data.json",
    )

    bundle = load_external_case(case_dir)

    assert bundle.filenames["topology"] == "topo.json"
    assert bundle.filenames["routes"] == "route-data.json"
    assert bundle.filenames["streams"] == "stream-data.json"


def test_mapper_accepts_baseline_traffic_class_aliases(sample_case_path: Path) -> None:
    """Alias traffic-class labels should normalize into the canonical enum."""

    bundle = load_external_case(sample_case_path)
    case = map_external_case(bundle)

    assert case.streams[0].traffic_class == TrafficClass.CLASS_A
    assert case.streams[0].deadline_us == 1000.0
    assert case.streams[0].route_id == "route-stream-a"


def test_loader_infers_provided_course_case_filenames(tmp_path: Path) -> None:
    """Course-style prefixed filenames should load even without a manifest."""

    case_dir = tmp_path / "provided-course-case"
    case_dir.mkdir()
    write_json(
        {
            "topology": {
                "switches": [{"id": "sw1", "ports": 2}],
                "end_systems": [{"id": "es0"}, {"id": "es1"}],
                "links": [
                    {
                        "id": "Link0",
                        "source": "es0",
                        "destination": "sw1",
                        "sourcePort": 0,
                        "destinationPort": 0,
                        "bandwidth_mbps": 100,
                    },
                    {
                        "id": "Link1",
                        "source": "sw1",
                        "destination": "es1",
                        "sourcePort": 1,
                        "destinationPort": 0,
                        "bandwidth_mbps": 100,
                    },
                ],
            }
        },
        case_dir / "provided-course-case-topology.json",
    )
    write_json(
        {
            "routes": [
                {
                    "flow_id": 0,
                    "paths": [[{"node": "es0", "port": 0}, {"node": "sw1", "port": 1}, {"node": "es1", "port": 0}]],
                }
            ]
        },
        case_dir / "provided-course-case-routes.json",
    )
    write_json(
        {
            "streams": [
                {
                    "id": 0,
                    "name": "Stream0",
                    "source": "es0",
                    "destinations": [{"id": "es1", "deadline": 1000}],
                    "PCP": 2,
                    "size": 256,
                    "period": 1000,
                }
            ]
        },
        case_dir / "provided-course-case-streams.json",
    )
    (case_dir / "provided-course-case-WCRTs.csv").write_text(
        "stream_id,expected_wcrt_us\nstream-0,0.0\n",
        encoding="utf-8",
    )

    bundle = load_external_case(case_dir)

    assert bundle.filenames["topology"] == "provided-course-case-topology.json"
    assert bundle.filenames["routes"] == "provided-course-case-routes.json"
    assert bundle.filenames["streams"] == "provided-course-case-streams.json"
    assert bundle.filenames["expected_wcrts"] == "provided-course-case-WCRTs.csv"


def test_loader_uses_original_assignment_case_files_when_manifest_declares_them(repo_root: Path) -> None:
    """The bundled external sample should resolve to the original assignment file set."""

    bundle = load_external_case(repo_root / "cases" / "external" / "test-case-1")

    assert bundle.filenames["topology"] == "test-case-1-topology.json"
    assert bundle.filenames["routes"] == "test-case-1-routes.json"
    assert bundle.filenames["streams"] == "test-case-1-streams.json"
    assert bundle.filenames["expected_wcrts"] == "test-case-1-WCRTs.csv"
    assert len(bundle.streams) == 10
    assert len(bundle.routes) == 10
    assert len(bundle.expected_wcrts) == 8
    assert bundle.expected_wcrts[0]["stream_id"] == "stream-0"
    assert bundle.expected_wcrts[0]["expected_wcrt_us"] == 603.2


def test_normalized_export_bundle_writes_core_artifacts(sample_case_path: Path, tmp_path: Path) -> None:
    """Normalized export should emit JSON and the required CSV bundle."""

    prepared = prepare_case(sample_case_path)
    artifacts = export_normalized_case_bundle(prepared.normalized_case, tmp_path)

    assert set(artifacts) == {
        "normalized_case.json",
        "nodes.csv",
        "links.csv",
        "routes.csv",
        "streams.csv",
        "link_stream_map.csv",
        "artifact_index.json",
    }
    for path in artifacts.values():
        assert path.exists()

    route_rows = read_csv_rows(artifacts["routes.csv"])
    link_stream_rows = read_csv_rows(artifacts["link_stream_map.csv"])

    assert list(route_rows[0]) == [
        "route_id",
        "stream_id",
        "hop_index",
        "node_id",
        "link_id",
        "transmission_time_us",
    ]
    assert list(link_stream_rows[0]) == [
        "stream_id",
        "route_id",
        "link_id",
        "hop_index",
        "transmission_time_us",
    ]
    artifact_index = read_json(artifacts["artifact_index.json"])
    assert artifact_index["schema_version"] == "normalized-bundle-index.v1"
    assert artifact_index["case_id"] == prepared.normalized_case.metadata.case_id
    assert {entry["name"] for entry in artifact_index["artifacts"]} == {
        "normalized_case.json",
        "nodes.csv",
        "links.csv",
        "routes.csv",
        "streams.csv",
        "link_stream_map.csv",
    }
