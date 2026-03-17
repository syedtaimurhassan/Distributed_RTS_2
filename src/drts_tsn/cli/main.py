"""Entrypoint for the `drts` CLI."""

from __future__ import annotations

import sys
from typing import Sequence

from drts_tsn.logging_ext.logger import configure_logging

from .args import build_parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and dispatch to the selected command handler."""

    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.logging_config)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
