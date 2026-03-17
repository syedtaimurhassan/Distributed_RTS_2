"""Unit tests for the analytical baseline."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from drts_tsn.analysis.engine import AnalysisEngine
from drts_tsn.domain.enums import TrafficClass
from drts_tsn.domain.routes import Route
from drts_tsn.orchestration.run_manager import prepare_case


def test_analysis_engine_computes_baseline_wcrt(sample_case_path) -> None:
    """The baseline analysis should compute a deterministic AVB WCRT."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    result = AnalysisEngine().run(prepared.normalized_case)

    assert len(result.stream_results) == 1
    assert result.stream_results[0].wcrt_us == pytest.approx(40.96)
    assert result.summary["engine_status"] == "ok"
    assert len(result.detail_rows) == 2
    assert {row["link_id"] for row in result.detail_rows} == {"link-1", "link-2"}


def test_analysis_run_summary_matches_engine_status(sample_case_path) -> None:
    """Run-summary CSV rows should stay aligned with the JSON summary status."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    result = AnalysisEngine().run(prepared.normalized_case)

    assert result.tables["run_summary"][0]["status"] == result.summary["engine_status"]


def test_end_to_end_wcrt_equals_sum_of_per_link_contributions(sample_case_path) -> None:
    """End-to-end WCRT should equal the sum of per-link WCRT contributions."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    result = AnalysisEngine().run(prepared.normalized_case)

    per_link_total = sum(float(row["per_link_wcrt_us"]) for row in result.tables["per_link_wcrt_summary"])

    assert result.tables["stream_wcrt_summary"][0]["end_to_end_wcrt_us"] == pytest.approx(per_link_total)
    assert result.tables["end_to_end_accumulation_trace"][-1]["cumulative_wcrt_us"] == pytest.approx(
        per_link_total
    )


def test_stream_wcrt_summary_excludes_best_effort_rows(sample_case_path) -> None:
    """The analytical stream summary CSV should report only AVB streams."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    case_with_be = deepcopy(prepared.normalized_case)
    case_with_be.streams.append(
        replace(
            case_with_be.streams[0],
            id="stream-be",
            name="BE stream",
            traffic_class=TrafficClass.BEST_EFFORT,
            route_id="route-stream-be",
            priority=0,
        )
    )
    case_with_be.routes.append(
        Route(
            stream_id="stream-be",
            route_id="route-stream-be",
            hops=deepcopy(case_with_be.routes[0].hops),
        )
    )

    result = AnalysisEngine().run(case_with_be)

    assert any(stream.stream_id == "stream-be" and stream.wcrt_us is None for stream in result.stream_results)
    assert [row["stream_id"] for row in result.tables["stream_wcrt_summary"]] == ["stream-a"]


def test_analysis_result_summary_exposes_schema_version(sample_case_path) -> None:
    """The JSON summary should expose a stable schema/version marker."""

    prepared = prepare_case(sample_case_path, include_analysis_checks=True)
    result = AnalysisEngine().run(prepared.normalized_case)

    assert result.summary["schema_version"] == "analysis.v1"
    assert result.summary["precondition_failures"] == []
