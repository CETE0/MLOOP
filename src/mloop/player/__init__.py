"""Player module for MLOOP."""

from mloop.player.backend import PlayerBackend
from mloop.player.cvlc import CvlcPlayer
from mloop.player.mpv import MpvPlayer


def create_player(config) -> PlayerBackend:
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
        return MpvPlayer(config)
    if backend == "cvlc":
        return CvlcPlayer(config)
    raise ValueError(f"Unsupported player backend: {backend}")


__all__ = ["PlayerBackend", "MpvPlayer", "CvlcPlayer", "create_player"]
