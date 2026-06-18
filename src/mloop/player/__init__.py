"""Player module for MLOOP."""

from mloop.config import PlaybackConfig, PlayerConfig
from mloop.player.backend import PlayerBackend, PlayerCapabilities
from mloop.player.cvlc import CvlcPlayer
from mloop.player.mpv import MpvPlayer


def create_player(
    config: PlayerConfig,
    playback_config: PlaybackConfig | None = None,
) -> PlayerBackend:
    """Create a player backend instance from configuration.

    Args:
        config: PlayerConfig instance.

    Returns:
        A PlayerBackend instance matching the configured backend.

    Raises:
        ValueError: If the backend is not supported.
    """
    backend = config.backend
    if backend == "mpv":
        return MpvPlayer(config, playback_config)
    if backend == "cvlc":
        return CvlcPlayer(config, playback_config)
    raise ValueError(f"Unsupported player backend: {backend}")


__all__ = ["PlayerBackend", "PlayerCapabilities", "MpvPlayer", "CvlcPlayer", "create_player"]
