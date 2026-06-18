"""Tests for configuration loading."""

from pathlib import Path

import pytest

from mloop.config import (
    AudioConfig,
    Config,
    ConfigError,
    DisplayConfig,
    HdmiGesturesConfig,
    MenuConfig,
    PlaybackConfig,
    PlayerConfig,
    WebConfig,
    load_config,
)


def test_default_config() -> None:
    """Test that default config has expected values."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert isinstance(config, Config)
    assert isinstance(config.playback, PlaybackConfig)
    assert isinstance(config.player, PlayerConfig)
    assert isinstance(config.display, DisplayConfig)
    assert isinstance(config.audio, AudioConfig)
    assert isinstance(config.hdmi_gestures, HdmiGesturesConfig)
    assert isinstance(config.menu, MenuConfig)
    assert isinstance(config.web, WebConfig)


def test_default_playback_values() -> None:
    """Test default playback configuration."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert config.playback.media_dirs == ["/home/mloop/media"]
    assert config.playback.shuffle is False
    assert config.playback.loop is True
    assert config.playback.volume == 80
    assert config.playback.image_duration_seconds == 10


def test_default_player_values() -> None:
    """Test default player configuration."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert config.player.backend == "mpv"
    assert config.player.mpv_path == "/usr/bin/mpv"
    assert config.player.cvlc_path == "/usr/bin/cvlc"
    assert "/mpv.sock" in config.player.ipc_socket


def test_player_config_backend_mpv() -> None:
    """Test PlayerConfig with mpv backend."""
    cfg = PlayerConfig(backend="mpv")
    assert cfg.backend == "mpv"


def test_player_config_backend_cvlc() -> None:
    """Test PlayerConfig with cvlc backend."""
    cfg = PlayerConfig(backend="cvlc")
    assert cfg.backend == "cvlc"


def test_default_display_values() -> None:
    """Test default display configuration."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert config.display.connector == "auto"
    assert config.display.rotation == 0
    assert config.display.mode == "auto"


def test_default_audio_values() -> None:
    """Test default audio configuration."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert config.audio.output == "auto"


def test_default_gesture_values() -> None:
    """Test default HDMI gestures configuration."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert config.hdmi_gestures.enabled is True
    assert config.hdmi_gestures.enter_min_disconnect_ms == 800
    assert config.hdmi_gestures.enter_max_disconnect_ms == 8000
    assert config.hdmi_gestures.cycle_min_disconnect_ms == 300
    assert config.hdmi_gestures.cycle_max_disconnect_ms == 5000
    assert config.hdmi_gestures.debounce_ms == 100
    assert config.hdmi_gestures.select_after_connected_ms == 5000
    assert config.hdmi_gestures.menu_timeout_ms == 30000


def test_default_menu_values() -> None:
    """Test default menu configuration."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert config.menu.osd_duration_ms == 5000
    assert config.menu.confirm_dangerous_actions is True


def test_default_web_values() -> None:
    """Test default web configuration."""
    config = load_config(Path("/nonexistent/config.toml"))

    assert config.web.enabled is False
    assert config.web.host == "127.0.0.1"
    assert config.web.port == 8080


@pytest.mark.parametrize("backend", ["omxplayer", "vlc"])
def test_invalid_backend_rejected(tmp_path: Path, backend: str) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'[player]\nbackend = "{backend}"\n')

    with pytest.raises(ConfigError, match="player.backend"):
        load_config(path)


@pytest.mark.parametrize("volume", [-1, 101])
def test_invalid_volume_rejected(tmp_path: Path, volume: int) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f"[playback]\nvolume = {volume}\n")

    with pytest.raises(ConfigError, match="playback.volume"):
        load_config(path)


@pytest.mark.parametrize("rotation", [45, -90, 360])
def test_invalid_rotation_rejected(tmp_path: Path, rotation: int) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f"[display]\nrotation = {rotation}\n")

    with pytest.raises(ConfigError, match="display.rotation"):
        load_config(path)


def test_invalid_audio_output_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[audio]\noutput = "bluetooth"\n')

    with pytest.raises(ConfigError, match="audio.output"):
        load_config(path)


def test_invalid_gesture_debounce_rejected(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[hdmi_gestures]\ndebounce_ms = 300\ncycle_min_disconnect_ms = 300\n")

    with pytest.raises(ConfigError, match="debounce_ms"):
        load_config(path)
