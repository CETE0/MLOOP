"""Tests for daemon player recovery."""

from pathlib import Path

import pytest

from mloop.config import Config
from mloop.daemon import Daemon


class _FakePlayer:
    def __init__(self, calls: list[str]) -> None:
        self.calls = calls
        self._running = False

    def start(self) -> None:
        self.calls.append("start")
        self._running = True

    def stop(self) -> None:
        self.calls.append("stop")
        self._running = False

    async def reset_after_exit(self) -> None:
        self.calls.append("reset")

    async def load_playlist(self, files: list[Path]) -> None:
        self.calls.append(f"load_playlist:{len(files)}")

    async def set_volume(self, volume: int) -> None:
        self.calls.append(f"volume:{volume}")

    async def set_rotation(self, degrees: int) -> None:
        self.calls.append(f"rotation:{degrees}")

    async def set_audio_output(self, output: str) -> None:
        self.calls.append(f"audio:{output}")

    async def show_osd(self, text: str, duration: int = 5000) -> None:
        self.calls.append(f"osd:{duration}:{text}")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def pid(self) -> int | None:
        return 123


@pytest.mark.asyncio
async def test_player_crash_reloads_media_and_state(tmp_path: Path) -> None:
    media_file = tmp_path / "a.mp4"
    media_file.write_text("")
    config = Config()
    config.playback.media_dirs = [str(tmp_path)]
    config.playback.volume = 70
    config.display.rotation = 90
    config.audio.output = "hdmi"
    daemon = Daemon(config, state_path=tmp_path / "state.toml")
    calls: list[str] = []
    daemon.player = _FakePlayer(calls)

    await daemon._recover_player()

    assert calls == [
        "reset",
        "start",
        "load_playlist:1",
        "volume:70",
        "rotation:90",
        "audio:hdmi",
    ]
    assert daemon._player_restart_backoff_seconds == 0.0


@pytest.mark.asyncio
async def test_player_recovery_increases_backoff_on_failure(tmp_path: Path) -> None:
    config = Config()
    config.playback.media_dirs = [str(tmp_path)]
    daemon = Daemon(config, state_path=tmp_path / "state.toml")
    calls: list[str] = []
    player = _FakePlayer(calls)

    def fail_start() -> None:
        calls.append("start")
        raise RuntimeError("failed")

    player.start = fail_start
    daemon.player = player

    await daemon._recover_player()

    assert calls == ["reset", "start"]
    assert daemon._player_restart_backoff_seconds == 1.0
