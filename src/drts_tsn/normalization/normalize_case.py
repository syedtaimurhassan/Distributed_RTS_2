"""Top-level normalization pipeline for canonical cases."""

from __future__ import annotations

from drts_tsn.domain.case import Case

from .canonicalize_ids import canonicalize_case_identifiers
from .derive_frame_params import derive_frame_parameters
from .derive_link_params import derive_link_parameters
from .derive_paths import derive_paths
from .derive_priority_classes import derive_priority_classes


def normalize_case(case: Case) -> Case:
    """Run the explicit normalization pipeline in a stable order."""

    normalized = canonicalize_case_identifiers(case)
    normalized = derive_link_parameters(normalized)
    normalized = derive_frame_parameters(normalized)
    normalized = derive_priority_classes(normalized)
    normalized = derive_paths(normalized)
    return normalized
