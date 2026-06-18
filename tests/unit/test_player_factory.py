"""Tests for player backend factory and abstraction."""

import pytest

from mloop.config import PlayerConfig
from mloop.player import CvlcPlayer, MpvPlayer, PlayerBackend, create_player
from mloop.player.backend import PlayerBackend as PlayerBackendDirect


def test_create_player_mpv() -> None:
    """Factory returns MpvPlayer when backend is 'mpv'."""
    config = PlayerConfig(backend="mpv")
    player = create_player(config)
    assert isinstance(player, MpvPlayer)
    assert isinstance(player, PlayerBackend)


def test_create_player_cvlc() -> None:
    """Factory returns CvlcPlayer when backend is 'cvlc'."""
    config = PlayerConfig(backend="cvlc")
    player = create_player(config)
    assert isinstance(player, CvlcPlayer)
    assert isinstance(player, PlayerBackend)


def test_create_player_unknown_backend() -> None:
    """Factory raises ValueError for unknown backend."""
    config = PlayerConfig(backend="omxplayer")
    with pytest.raises(ValueError, match="Unsupported player backend"):
        create_player(config)


def test_mpv_player_is_backend() -> None:
    """MpvPlayer is a PlayerBackend."""
    config = PlayerConfig(backend="mpv")
    player = MpvPlayer(config)
    assert isinstance(player, PlayerBackend)
    assert isinstance(player, PlayerBackendDirect)
    assert player.capabilities.osd is True
    assert player.capabilities.runtime_volume is True


def test_cvlc_player_is_backend() -> None:
    """CvlcPlayer is a PlayerBackend."""
    config = PlayerConfig(backend="cvlc")
    player = CvlcPlayer(config)
    assert isinstance(player, PlayerBackend)
    assert isinstance(player, PlayerBackendDirect)
    assert player.capabilities.osd is False
    assert player.capabilities.runtime_volume is False


def test_player_backend_abstract_methods() -> None:
    """PlayerBackend defines required abstract methods."""
    required = {
        "start",
        "stop",
        "load_playlist",
        "set_volume",
        "set_rotation",
        "set_audio_output",
        "show_osd",
        "reset_after_exit",
    }
    for method_name in required:
        assert hasattr(PlayerBackend, method_name), f"Missing abstract method: {method_name}"
        method = getattr(PlayerBackend, method_name)
        assert getattr(method, "__isabstractmethod__", False), f"{method_name} is not abstract"


def test_player_backend_properties() -> None:
    """PlayerBackend defines required abstract properties."""
    for prop_name in ("capabilities", "is_running", "pid"):
        assert hasattr(PlayerBackend, prop_name), f"Missing property: {prop_name}"
