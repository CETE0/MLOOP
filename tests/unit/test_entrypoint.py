"""Tests for the daemon entry point."""

import inspect

from mloop import __main__


def test_console_entrypoint_is_synchronous() -> None:
    """Console scripts must call a synchronous function."""
    assert not inspect.iscoroutinefunction(__main__.main)
    assert inspect.iscoroutinefunction(__main__._amain)
