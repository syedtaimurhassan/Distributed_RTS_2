"""Development namespace shim for local `python -m drts_tsn...` execution."""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "drts_tsn"
if SRC_PACKAGE.is_dir():
    __path__.append(str(SRC_PACKAGE))

from .version import __version__

__all__ = ["__version__"]
