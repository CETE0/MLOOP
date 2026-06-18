"""Tests for daemon menu wiring."""

from mloop.config import Config
from mloop.daemon import Daemon


def test_daemon_registers_one_menu_controller() -> None:
    daemon = Daemon(Config())

    daemon._build_menu()
    daemon._setup_gesture_handlers()
    daemon._setup_gesture_handlers()

    assert len(daemon.gesture_machine._callbacks) == 1
