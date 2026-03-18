"""Identifier normalization helpers."""

from __future__ import annotations

import re


def slugify_identifier(value: object) -> str:
    """Normalize identifiers into a lowercase slug used internally."""

    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", str(value).strip().lower()).strip("-")
    return cleaned or "unnamed"


def compose_identifier(*parts: str) -> str:
    """Compose a stable identifier from multiple parts."""

    return "-".join(slugify_identifier(part) for part in parts if part)
