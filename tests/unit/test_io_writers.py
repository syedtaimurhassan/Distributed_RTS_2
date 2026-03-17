"""Tests for basic JSON, CSV, and YAML helpers."""

from __future__ import annotations

from drts_tsn.io.csv_io import read_csv_rows, write_csv_rows
from drts_tsn.io.json_io import read_json, write_json
from drts_tsn.io.yaml_io import read_yaml, write_yaml


def test_json_csv_yaml_helpers_round_trip(tmp_path) -> None:
    """The basic serialization helpers should round-trip scaffold data."""

    json_path = tmp_path / "data.json"
    csv_path = tmp_path / "data.csv"
    yaml_path = tmp_path / "data.yaml"

    write_json({"alpha": 1}, json_path)
    write_csv_rows([{"alpha": 1, "beta": "x"}], csv_path)
    write_yaml({"alpha": 1}, yaml_path)

    assert read_json(json_path) == {"alpha": 1}
    assert read_csv_rows(csv_path) == [{"alpha": "1", "beta": "x"}]
    assert read_yaml(yaml_path) == {"alpha": 1}
