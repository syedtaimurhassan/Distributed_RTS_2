"""Golden/reference regression tests for the baseline analysis artifacts."""

from __future__ import annotations

from drts_tsn.analysis.outputs.analysis_result_builder import ANALYSIS_SCHEMA_VERSION, ANALYSIS_TABLE_FIELDS
from drts_tsn.io.json_io import read_json
from drts_tsn.orchestration.pipeline_analyze import execute


def test_reference_case_analysis_outputs_match_golden_invariants(
    sample_case_path,
    tmp_path,
    assert_csv_contract,
) -> None:
    """The bundled example case should keep its load-bearing analysis outputs stable."""

    result, layout = execute(sample_case_path, output_root=tmp_path, run_id="golden-analysis")

    stream_rows = assert_csv_contract(
        layout.analysis_results_dir / "stream_wcrt_summary.csv",
        ANALYSIS_TABLE_FIELDS["stream_wcrt_summary"],
    )
    assert stream_rows == [
        {
            "stream_id": "stream-a",
            "route_id": "route-stream-a",
            "traffic_class": "class_a",
            "hop_count": "2",
            "deadline_us": "1000.0",
            "end_to_end_wcrt_us": "40.96",
            "meets_deadline": "True",
            "expected_wcrt_us": "0.0",
            "analyzed": "True",
            "status": "ok",
        }
    ]

    per_link_rows = assert_csv_contract(
        layout.analysis_results_dir / "per_link_wcrt_summary.csv",
        ANALYSIS_TABLE_FIELDS["per_link_wcrt_summary"],
    )
    assert per_link_rows == [
        {
            "stream_id": "stream-a",
            "route_id": "route-stream-a",
            "link_id": "link-1",
            "hop_index": "0",
            "traffic_class": "class_a",
            "transmission_time_us": "20.48",
            "same_priority_interference_us": "0",
            "lower_priority_interference_us": "0.0",
            "higher_priority_interference_us": "0.0",
            "per_link_wcrt_us": "20.48",
            "reserved_share": "0.5",
            "reserved_share_up_to_class": "0.5",
        },
        {
            "stream_id": "stream-a",
            "route_id": "route-stream-a",
            "link_id": "link-2",
            "hop_index": "1",
            "traffic_class": "class_a",
            "transmission_time_us": "20.48",
            "same_priority_interference_us": "0",
            "lower_priority_interference_us": "0.0",
            "higher_priority_interference_us": "0.0",
            "per_link_wcrt_us": "20.48",
            "reserved_share": "0.5",
            "reserved_share_up_to_class": "0.5",
        },
    ]

    formula_rows = assert_csv_contract(
        layout.analysis_traces_dir / "per_link_formula_trace.csv",
        ANALYSIS_TABLE_FIELDS["per_link_formula_trace"],
    )
    assert [row["term_name"] for row in formula_rows] == [
        "Ci",
        "SPI",
        "LPI",
        "HPI",
        "W_link",
        "Ci",
        "SPI",
        "LPI",
        "HPI",
        "W_link",
    ]
    assert formula_rows[-1]["term_value_us"] == "20.48"

    result_json = read_json(layout.analysis_results_dir / "analysis_result.json")
    assert result_json["summary"] == {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "engine_status": "ok",
        "stream_count": 1,
        "analyzed_stream_count": 1,
        "detail_row_count": 2,
        "precondition_failure_count": 0,
        "precondition_failures": [],
    }
    assert result.tables["stream_wcrt_summary"][0]["expected_wcrt_us"] == 0.0
