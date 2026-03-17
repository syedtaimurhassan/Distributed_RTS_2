"""YAML reader and writer helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from drts_tsn.common.constants import DEFAULT_ENCODING
from drts_tsn.common.dataclass_tools import to_plain_data

try:
    import yaml  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency fallback
    yaml = None


def _parse_scalar(value: str) -> Any:
    """Parse a simple YAML scalar used by the scaffold configs."""

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _clean_yaml_lines(text: str) -> list[tuple[int, str]]:
    """Return indentation-aware YAML lines without comments or blanks."""

    cleaned: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        cleaned.append((indent, stripped))
    return cleaned


def _parse_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    """Parse a minimal YAML mapping/list block."""

    if index >= len(lines):
        return {}, index

    current_indent, current_text = lines[index]
    if current_indent < indent:
        return {}, index

    if current_text == "-" or current_text.startswith("- "):
        items: list[Any] = []
        while index < len(lines):
            line_indent, line_text = lines[index]
            if line_indent != indent or not (line_text == "-" or line_text.startswith("- ")):
                break
            item_text = line_text[1:].strip()
            index += 1
            if item_text:
                items.append(_parse_scalar(item_text))
                continue
            nested, index = _parse_yaml_block(lines, index, indent + 2)
            items.append(nested)
        return items, index

    mapping: dict[str, Any] = {}
    while index < len(lines):
        line_indent, line_text = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError(f"Unexpected indentation in YAML near '{line_text}'.")
        if line_text == "-" or line_text.startswith("- "):
            break
        key, separator, rest = line_text.partition(":")
        if separator != ":":
            raise ValueError(f"Invalid YAML line: '{line_text}'.")
        index += 1
        value_text = rest.strip()
        if value_text:
            mapping[key.strip()] = _parse_scalar(value_text)
            continue
        if index < len(lines) and lines[index][0] > indent:
            nested, index = _parse_yaml_block(lines, index, lines[index][0])
            mapping[key.strip()] = nested
        else:
            mapping[key.strip()] = None
    return mapping, index


def _simple_yaml_load(text: str) -> Any:
    """Parse a small YAML subset used by the scaffold without external dependencies."""

    lines = _clean_yaml_lines(text)
    if not lines:
        return None
    parsed, _ = _parse_yaml_block(lines, 0, lines[0][0])
    return parsed


def _format_scalar(value: Any) -> str:
    """Format a scalar into simple YAML."""

    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def _simple_yaml_dump(data: Any, *, indent: int = 0) -> str:
    """Serialize a small YAML subset used by the scaffold."""

    prefix = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_simple_yaml_dump(value, indent=indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_simple_yaml_dump(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}- {_format_scalar(item)}")
        return "\n".join(lines)
    return f"{prefix}{_format_scalar(data)}"


def read_yaml(path: Path) -> Any:
    """Load YAML from disk."""

    with path.open("r", encoding=DEFAULT_ENCODING) as handle:
        content = handle.read()
    if yaml is not None:
        return yaml.safe_load(content)
    return _simple_yaml_load(content)


def write_yaml(data: Any, path: Path) -> Path:
    """Write structured data as YAML."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=DEFAULT_ENCODING) as handle:
        serialized = to_plain_data(data)
        if yaml is not None:
            yaml.safe_dump(serialized, handle, sort_keys=False)
        else:
            handle.write(_simple_yaml_dump(serialized))
            handle.write("\n")
    return path
