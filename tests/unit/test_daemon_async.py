"""Tests for daemon background task supervision."""

import asyncio
import logging

import pytest

from mloop.config import Config
from mloop.daemon import Daemon


@pytest.mark.asyncio
async def test_background_task_exception_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    daemon = Daemon(Config())

    async def fail() -> None:
        raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR):
        daemon._spawn_background(fail(), "failing-task")
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    assert "Background task failed: failing-task" in caplog.text
    assert not daemon._background_tasks
