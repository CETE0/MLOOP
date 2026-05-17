"""Integration tests for HDMI watcher with fake sysfs."""

import asyncio
import contextlib
from pathlib import Path

import pytest

from mloop.display.drm import DrmConnector, discover_connectors
from mloop.display.hdmi_watcher import HdmiEvent, HdmiWatcher

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_discover_connectors_connected() -> None:
    """Test connector discovery with connected fixture."""
    sysfs_root = FIXTURES_DIR / "sysfs_connected"
    connectors = discover_connectors(sysfs_root=sysfs_root)

    assert len(connectors) == 1
    assert connectors[0].name == "card1-HDMI-A-1"


def test_discover_connectors_disconnected() -> None:
    """Test connector discovery with disconnected fixture."""
    sysfs_root = FIXTURES_DIR / "sysfs_disconnected"
    connectors = discover_connectors(sysfs_root=sysfs_root)

    assert len(connectors) == 1
    assert connectors[0].name == "card1-HDMI-A-1"


def test_connector_read_status_connected() -> None:
    """Test reading connector status from connected fixture."""
    sysfs_root = FIXTURES_DIR / "sysfs_connected"
    connector_path = sysfs_root / "card1-HDMI-A-1"
    connector = DrmConnector(
        name="card1-HDMI-A-1",
        sysfs_path=connector_path,
        status="unknown",
    )

    status = connector.read_status()
    assert status == "connected"


def test_connector_read_status_disconnected() -> None:
    """Test reading connector status from disconnected fixture."""
    sysfs_root = FIXTURES_DIR / "sysfs_disconnected"
    connector_path = sysfs_root / "card1-HDMI-A-1"
    connector = DrmConnector(
        name="card1-HDMI-A-1",
        sysfs_path=connector_path,
        status="unknown",
    )

    status = connector.read_status()
    assert status == "disconnected"


@pytest.mark.asyncio
async def test_hdmi_watcher_emits_events(tmp_path: Path) -> None:
    """Test that HDMI watcher emits events on state change."""
    connector_path = tmp_path / "card1-HDMI-A-1"
    connector_path.mkdir(parents=True)
    status_file = connector_path / "status"
    status_file.write_text("connected\n")

    connector = DrmConnector(
        name="card1-HDMI-A-1",
        sysfs_path=connector_path,
        status="connected",
    )

    events: list[HdmiEvent] = []

    def capture_event(event: HdmiEvent) -> None:
        events.append(event)

    watcher = HdmiWatcher(
        connectors=[connector],
        debounce_ms=100,
        poll_interval_ms=50,
    )
    watcher.on_event(capture_event)

    async def change_state() -> None:
        await asyncio.sleep(0.2)
        status_file.write_text("disconnected\n")
        await asyncio.sleep(0.3)

    task = asyncio.create_task(watcher.start())
    await change_state()
    await watcher.stop()
    task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert len(events) >= 1
    assert events[0].state == "disconnected"
