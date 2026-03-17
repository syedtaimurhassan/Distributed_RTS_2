"""Basic import smoke tests for the scaffold."""

from __future__ import annotations


def test_package_imports() -> None:
    """The top-level package should be importable."""

    import drts_tsn
    import drts_tsn.cli.main
    import drts_tsn.orchestration.run_manager

    assert drts_tsn.__version__
