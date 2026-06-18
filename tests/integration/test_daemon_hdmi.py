"""Integration tests for daemon HDMI watcher lifecycle."""

import asyncio

import pytest

from mloop.config import Config
from mloop.daemon import Daemon
from mloop.display.drm import DrmConnector


class _FakeProcess:
    """Fake subprocess for MpvPlayer.is_running."""

    pid = 12345

    @staticmethod
    def poll():
        return None


def _fake_discover(connectors):
    def _discover(*args, **kwargs):
        return list(connectors)

    return _discover


def _patch_daemon_player(daemon, monkeypatch):
    """Patch daemon player to avoid needing real mpv on the system."""
    monkeypatch.setattr(daemon.player, "_process", _FakeProcess())
    monkeypatch.setattr(daemon.player, "start", lambda: None)
    monkeypatch.setattr(daemon.player, "stop", lambda: None)
    monkeypatch.setattr(daemon.player, "show_osd", lambda *a, **kw: asyncio.sleep(0))
    monkeypatch.setattr(daemon.player, "load_playlist", lambda *a, **kw: asyncio.sleep(0))
    monkeypatch.setattr(daemon.player, "set_volume", lambda *a, **kw: asyncio.sleep(0))
    monkeypatch.setattr(daemon.player, "set_rotation", lambda *a, **kw: asyncio.sleep(0))
    monkeypatch.setattr(daemon.player, "set_audio_output", lambda *a, **kw: asyncio.sleep(0))


@pytest.mark.asyncio
async def test_daemon_starts_watcher_as_task(tmp_path, monkeypatch):
    """Daemon creates HdmiWatcher and starts it as an asyncio task."""
    connector_path = tmp_path / "card1-HDMI-A-1"
    connector_path.mkdir()
    (connector_path / "status").write_text("connected")

    connector = DrmConnector(
        name="card1-HDMI-A-1",
        sysfs_path=connector_path,
        status="connected",
    )

    monkeypatch.setattr(
        "mloop.daemon.discover_connectors",
        _fake_discover([connector]),
    )

    config = Config()
    daemon = Daemon(config)

    _patch_daemon_player(daemon, monkeypatch)
    monkeypatch.setattr(daemon.service, "setup_signal_handlers", lambda: None)
    monkeypatch.setattr("mloop.daemon.scan_media_dirs", lambda _: [])

    daemon_task = asyncio.create_task(daemon.run())
    await asyncio.sleep(0.2)

    assert daemon._hdmi_watcher is not None, "HdmiWatcher was not created"
    assert daemon._watcher_task is not None, "Watcher task was not created"
    assert daemon._hdmi_watcher._running is True, "Watcher was not started"

    daemon.service.stop()
    await asyncio.wait_for(daemon_task, timeout=2.0)

    assert daemon._hdmi_watcher._running is False, "Watcher was not stopped"


@pytest.mark.asyncio
async def test_daemon_hdmi_events_reach_gesture_machine(tmp_path, monkeypatch):
    """HDMI state changes from sysfs reach the gesture state machine and open the menu."""
    connector_path = tmp_path / "card1-HDMI-A-1"
    connector_path.mkdir()
    (connector_path / "status").write_text("connected")

    connector = DrmConnector(
        name="card1-HDMI-A-1",
        sysfs_path=connector_path,
        status="connected",
    )

    monkeypatch.setattr(
        "mloop.daemon.discover_connectors",
        _fake_discover([connector]),
    )

    config = Config()
    config.hdmi_gestures.debounce_ms = 50
    config.hdmi_gestures.enter_min_disconnect_ms = 100
    config.hdmi_gestures.enter_max_disconnect_ms = 10000

    daemon = Daemon(config)

    _patch_daemon_player(daemon, monkeypatch)
    monkeypatch.setattr(daemon.service, "setup_signal_handlers", lambda: None)
    monkeypatch.setattr("mloop.daemon.scan_media_dirs", lambda _: [])

    daemon_task = asyncio.create_task(daemon.run())
    await asyncio.sleep(0.2)

    assert daemon._hdmi_watcher is not None
    assert daemon._watcher_task is not None

    # Simulate HDMI disconnect
    (connector_path / "status").write_text("disconnected")
    await asyncio.sleep(0.5)

    assert daemon.gesture_machine._disconnect_start_ms is not None, (
        "Disconnect not detected by gesture machine"
    )

    # Simulate HDMI reconnect after a delay within enter-menu range
    await asyncio.sleep(0.8)
    (connector_path / "status").write_text("connected")
    await asyncio.sleep(0.5)

    assert daemon.menu_model.is_open, "Menu did not open after valid disconnect/connect sequence"

    daemon.service.stop()
    await asyncio.wait_for(daemon_task, timeout=2.0)


@pytest.mark.asyncio
async def test_daemon_clean_shutdown_stops_watcher(tmp_path, monkeypatch):
    """Daemon clean shutdown stops the HdmiWatcher."""
    connector_path = tmp_path / "card1-HDMI-A-1"
    connector_path.mkdir()
    (connector_path / "status").write_text("connected")

    connector = DrmConnector(
        name="card1-HDMI-A-1",
        sysfs_path=connector_path,
        status="connected",
    )

    monkeypatch.setattr(
        "mloop.daemon.discover_connectors",
        _fake_discover([connector]),
    )

    config = Config()
    daemon = Daemon(config)

    _patch_daemon_player(daemon, monkeypatch)
    monkeypatch.setattr(daemon.service, "setup_signal_handlers", lambda: None)
    monkeypatch.setattr("mloop.daemon.scan_media_dirs", lambda _: [])

    daemon_task = asyncio.create_task(daemon.run())
    await asyncio.sleep(0.2)

    assert daemon._hdmi_watcher._running is True

    daemon.service.stop()
    await asyncio.wait_for(daemon_task, timeout=2.0)

    assert daemon._hdmi_watcher._running is False, "Watcher was not stopped cleanly"
