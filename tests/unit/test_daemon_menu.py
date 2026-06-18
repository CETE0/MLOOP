"""Tests for daemon menu wiring."""

from mloop.config import Config
from mloop.daemon import Daemon


def test_daemon_registers_one_menu_controller() -> None:
    daemon = Daemon(Config())

    daemon._build_menu()
    daemon._setup_gesture_handlers()
    daemon._setup_gesture_handlers()

    assert len(daemon.gesture_machine._callbacks) == 1


def test_cvlc_menu_hides_unsupported_runtime_controls(tmp_path) -> None:
    config = Config()
    config.player.backend = "cvlc"
    daemon = Daemon(config, state_path=tmp_path / "state.toml")

    daemon._build_menu()

    assert daemon.menu_model is not None
    labels = [item.label for item in daemon.menu_model.items]
    assert "Volume" not in labels
    assert "Audio output" not in labels
    assert "Rotate video" not in labels
    assert "Show network info" not in labels
    assert "Rescan media" in labels


def test_cvlc_menu_registration_is_disabled_without_osd(tmp_path, caplog) -> None:
    config = Config()
    config.player.backend = "cvlc"
    daemon = Daemon(config, state_path=tmp_path / "state.toml")

    daemon._build_menu()
    daemon._setup_gesture_handlers()

    assert len(daemon.gesture_machine._callbacks) == 0
    assert "does not support it" in caplog.text
