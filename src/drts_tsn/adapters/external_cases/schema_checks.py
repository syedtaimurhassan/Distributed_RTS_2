"""Schema and filename checks for external case directories."""

from __future__ import annotations

from pathlib import Path

DEFAULT_REQUIRED_CASE_FILES = {
    "topology": "topology.json",
    "routes": "routes.json",
    "streams": "streams.json",
}
DEFAULT_OPTIONAL_CASE_FILES = {
    "expected_wcrts": "expected_wcrts.csv",
}
MANIFEST_FILE = "manifest.yaml"

INFERRED_REQUIRED_PATTERNS = {
    "topology": "*-topology.json",
    "routes": "*-routes.json",
    "streams": "*-streams.json",
}
INFERRED_OPTIONAL_PATTERNS = {
    "expected_wcrts": "*-WCRTs.csv",
}


def resolve_case_filenames(manifest: dict[str, object]) -> dict[str, str]:
    """Resolve case filenames from the manifest with stable defaults."""

    filenames = dict(DEFAULT_REQUIRED_CASE_FILES)
    filenames.update(DEFAULT_OPTIONAL_CASE_FILES)
    for key in tuple(filenames):
        raw_value = manifest.get(key)
        if raw_value is not None:
            filenames[key] = str(raw_value)
    return filenames


def infer_case_filenames(
    case_directory: Path,
    *,
    manifest: dict[str, object] | None = None,
) -> dict[str, str]:
    """Resolve filenames from defaults, manifest values, or the provided case-folder format."""

    resolved = resolve_case_filenames(manifest or {})
    if all((case_directory / filename).exists() for filename in DEFAULT_REQUIRED_CASE_FILES.values()):
        return resolved
    if manifest:
        return resolved

    inferred = dict(resolved)
    for key, pattern in INFERRED_REQUIRED_PATTERNS.items():
        matches = sorted(case_directory.glob(pattern))
        if len(matches) == 1:
            inferred[key] = matches[0].name
    for key, pattern in INFERRED_OPTIONAL_PATTERNS.items():
        matches = sorted(case_directory.glob(pattern))
        if len(matches) == 1:
            inferred[key] = matches[0].name
    return inferred


def missing_required_files(case_directory: Path, filenames: dict[str, str] | None = None) -> list[str]:
    """Return required filenames missing from the case directory."""

    resolved = filenames or resolve_case_filenames({})
    return [
        filename
        for key, filename in resolved.items()
        if key in DEFAULT_REQUIRED_CASE_FILES and not (case_directory / filename).exists()
    ]


def missing_optional_files(case_directory: Path, filenames: dict[str, str] | None = None) -> list[str]:
    """Return optional filenames absent from the case directory."""

    resolved = filenames or resolve_case_filenames({})
    return [
        filename
        for key, filename in resolved.items()
        if key in DEFAULT_OPTIONAL_CASE_FILES and not (case_directory / filename).exists()
    ]
