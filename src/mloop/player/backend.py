"""Player backend abstraction for MLOOP."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class PlayerBackend(ABC):
    """Abstract base class for player backends (mpv, cvlc, etc.)."""

    @abstractmethod
    def start(self) -> None:
        """Start the player process."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the player process."""
        ...

    @abstractmethod
    async def reset_after_exit(self) -> None:
        """Clear transient state after the player process exits unexpectedly."""
        ...

    @abstractmethod
    async def load_playlist(self, files: list[Path]) -> None:
        """Load a playlist of media files.

        Args:
            files: List of media file paths.
        """
        ...

    @abstractmethod
    async def set_volume(self, volume: int) -> None:
        """Set playback volume.

        Args:
            volume: Volume level (0-100).
        """
        ...

    @abstractmethod
    async def set_rotation(self, degrees: int) -> None:
        """Set video rotation.

        Args:
            degrees: Rotation in degrees (0, 90, 180, 270).
        """
        ...

    @abstractmethod
    async def set_audio_output(self, output: str) -> None:
        """Set audio output device.

        Args:
            output: Audio output device name.
        """
        ...

    @abstractmethod
    async def show_osd(self, text: str, duration: int = 5000) -> None:
        """Show text on the OSD.

        Args:
            text: Text to display.
            duration: Display duration in milliseconds.
        """
        ...

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the player process is running."""
        ...

    @property
    @abstractmethod
    def pid(self) -> int | None:
        """Get the player process PID."""
        ...
