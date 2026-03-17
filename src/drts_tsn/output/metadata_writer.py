"""Helpers for stable run-level metadata and manifest files."""

from __future__ import annotations

import subprocess
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from drts_tsn.common.dataclass_tools import to_plain_data
from drts_tsn.io.paths import project_root
from drts_tsn.version import __version__

from .artifact_index import ArtifactRecord
from .json_writers import write_json_artifact


RUN_MANIFEST_SCHEMA_VERSION = "run-manifest.v1"
BATCH_MANIFEST_SCHEMA_VERSION = "batch-manifest.v1"


def write_run_metadata(metadata: dict[str, Any], path: Path) -> Path:
    """Write run metadata as JSON."""

    return write_json_artifact(metadata, path)


def _utc_now_iso() -> str:
    """Return the current UTC time in a stable ISO 8601 form."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_git_commit_hash() -> str | None:
    """Return the current git commit hash when available."""

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root(),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit_hash = completed.stdout.strip()
    return commit_hash or None


def snapshot_config(*, config: Any, source_path: Path | None) -> dict[str, Any]:
    """Return a stable config snapshot entry."""

    if is_dataclass(config):
        values = asdict(config)
    else:
        values = to_plain_data(config)
    return {
        "source_path": str(source_path) if source_path is not None else None,
        "values": values,
    }


def build_run_manifest(
    *,
    pipeline: str,
    run_id: str,
    run_dir: Path,
    status: str,
    artifact_records: list[ArtifactRecord],
    command_invoked: str,
    pipeline_status: str | None = None,
    case_id: str | None = None,
    case_name: str | None = None,
    case_path: Path | None = None,
    config_snapshot: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a stable manifest payload for one pipeline run."""

    manifest = {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "pipeline": pipeline,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "status": status,
        "pipeline_status": pipeline_status,
        "command_invoked": command_invoked,
        "package_version": __version__,
        "git_commit_hash": read_git_commit_hash(),
        "case": {
            "case_id": case_id,
            "case_name": case_name,
            "case_path": str(case_path) if case_path is not None else None,
        },
        "config_snapshot": to_plain_data(config_snapshot or {}),
        "artifacts": [asdict(record) for record in artifact_records],
    }
    if extra:
        manifest.update(to_plain_data(extra))
    return manifest


def build_batch_manifest(
    *,
    batch_id: str,
    batch_dir: Path,
    cases_root: Path,
    operation: str,
    status: str,
    success_count: int,
    failure_count: int,
    command_invoked: str,
    artifact_records: list[ArtifactRecord],
    config_snapshot: dict[str, Any] | None = None,
    outcomes: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a stable manifest payload for one batch execution."""

    manifest = {
        "schema_version": BATCH_MANIFEST_SCHEMA_VERSION,
        "generated_at_utc": _utc_now_iso(),
        "batch_id": batch_id,
        "batch_dir": str(batch_dir),
        "cases_root": str(cases_root),
        "operation": operation,
        "status": status,
        "success_count": success_count,
        "failure_count": failure_count,
        "command_invoked": command_invoked,
        "package_version": __version__,
        "git_commit_hash": read_git_commit_hash(),
        "config_snapshot": to_plain_data(config_snapshot or {}),
        "artifacts": [asdict(record) for record in artifact_records],
        "outcomes": to_plain_data(outcomes or []),
    }
    if extra:
        manifest.update(to_plain_data(extra))
    return manifest


def write_run_manifest_bundle(
    manifest: dict[str, Any],
    *,
    metadata_dir: Path,
) -> dict[str, Path]:
    """Write the canonical run manifest and compatibility metadata file."""

    run_manifest_path = write_json_artifact(manifest, metadata_dir / "run_manifest.json")
    run_metadata_path = write_json_artifact(manifest, metadata_dir / "run_metadata.json")
    return {
        "run_manifest": run_manifest_path,
        "run_metadata": run_metadata_path,
    }
