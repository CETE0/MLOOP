"""Tests for configuration loading."""

from pathlib import Path

from mloop.config import (
    AudioConfig,
    Config,
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
    assert "/mpv.sock" in config.player.ipc_socket


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
    assert config.hdmi_gestures.debounce_ms == 500
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
