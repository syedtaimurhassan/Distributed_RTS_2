"""JSON reader and writer helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from drts_tsn.common.constants import DEFAULT_ENCODING
from drts_tsn.common.dataclass_tools import to_plain_data


def read_json(path: Path) -> Any:
    """Load JSON from disk."""

    with path.open("r", encoding=DEFAULT_ENCODING) as handle:
        return json.load(handle)


def write_json(data: Any, path: Path, *, indent: int = 2) -> Path:
    """Write structured data as JSON, creating parent directories as needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=DEFAULT_ENCODING) as handle:
        json.dump(to_plain_data(data), handle, indent=indent, sort_keys=True)
        handle.write("\n")
    return path
