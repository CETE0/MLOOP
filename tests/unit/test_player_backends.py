"""Tests for concrete player backends."""

import signal
import subprocess
from pathlib import Path

import pytest

from mloop.config import PlaybackConfig, PlayerConfig
from mloop.player.cvlc import CvlcPlayer
from mloop.player.ipc import JsonObject
from mloop.player.mpv import MpvPlayer


class _SlowProcess:
    pid = 123

    def __init__(self) -> None:
        self.waits = 0

    def wait(self, timeout: float) -> None:
        self.waits += 1
        if self.waits == 1:
            raise subprocess.TimeoutExpired("player", timeout)

    def poll(self) -> None:
        return None


class _StartedProcess:
    pid = 123

    def wait(self, timeout: float) -> None:
        return None

    def poll(self) -> None:
        return None


def test_mpv_stop_timeout_sends_sigkill(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _SlowProcess()
    player = MpvPlayer(PlayerConfig())
    player._process = process
    kill_signals: list[int] = []

    monkeypatch.setattr("mloop.player.mpv.os.getpgid", lambda pid: pid)
    monkeypatch.setattr("mloop.player.mpv.os.killpg", lambda _pgid, sig: kill_signals.append(sig))

    player.stop()

    assert kill_signals == [signal.SIGTERM, signal.SIGKILL]
    assert process.waits == 2
    assert player._process is None


def test_cvlc_stop_timeout_sends_sigkill(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _SlowProcess()
    player = CvlcPlayer(PlayerConfig())
    player._process = process
    kill_signals: list[int] = []

    monkeypatch.setattr("mloop.player.cvlc.os.getpgid", lambda pid: pid)
    monkeypatch.setattr("mloop.player.cvlc.os.killpg", lambda _pgid, sig: kill_signals.append(sig))

    player.stop()

    assert kill_signals == [signal.SIGTERM, signal.SIGKILL]
    assert process.waits == 2
    assert player._process is None


def test_mpv_start_uses_loop_and_image_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_args: list[str] = []
    playback = PlaybackConfig(loop=False, image_duration_seconds=17)
    player = MpvPlayer(PlayerConfig(ipc_socket="/tmp/mloop-test.sock"), playback)

    def fake_popen(
        args: list[str],
        stdout: object,
        stderr: object,
        start_new_session: bool,
    ) -> _StartedProcess:
        captured_args.extend(args)
        return _StartedProcess()

    monkeypatch.setattr("mloop.player.mpv.subprocess.Popen", fake_popen)
    monkeypatch.setattr(Path, "exists", lambda _path: False)

    player.start()

    assert "--loop-playlist=no" in captured_args
    assert "--image-display-duration=17" in captured_args


@pytest.mark.asyncio
async def test_mpv_load_playlist_uses_loadlist(tmp_path: Path) -> None:
    player = MpvPlayer(PlayerConfig(ipc_socket=str(tmp_path / "mpv.sock")))
    commands: list[tuple[str, str, str]] = []

    class _FakeIpc:
        async def command(self, command: str, path: str, mode: str) -> JsonObject:
            commands.append((command, path, mode))
            return {}

    async def connect_ipc() -> _FakeIpc:
        return _FakeIpc()

    player.connect_ipc = connect_ipc
    files = [tmp_path / "a.mp4", tmp_path / "b.mp4"]

    await player.load_playlist(files)

    playlist_path = tmp_path / "mpv.m3u"
    assert commands == [("loadlist", str(playlist_path), "replace")]
    assert playlist_path.read_text() == f"{files[0]}\n{files[1]}\n"


def test_cvlc_start_omits_loop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_args: list[str] = []
    player = CvlcPlayer(PlayerConfig(), PlaybackConfig(loop=False))

    def fake_popen(
        args: list[str],
        stdout: object,
        stderr: object,
        start_new_session: bool,
    ) -> _StartedProcess:
        captured_args.extend(args)
        return _StartedProcess()

    monkeypatch.setattr("mloop.player.cvlc.subprocess.Popen", fake_popen)

    player.start()

    assert "--loop" not in captured_args
