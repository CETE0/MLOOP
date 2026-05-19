"""cvlc (VLC CLI) playback backend for MLOOP."""

from __future__ import annotations

import contextlib
import logging
import os
import signal
import subprocess
from pathlib import Path

from mloop.config import PlayerConfig
from mloop.player.backend import PlayerBackend

logger = logging.getLogger("mloop.player.cvlc")


class CvlcPlayer(PlayerBackend):
    """cvlc playback controller.

    Uses VLC's command-line interface (cvlc) for playback.
    Unlike mpv, cvlc does not have a JSON IPC interface, so
    some interactive controls are limited to process-level management.
    """

    def __init__(self, config: PlayerConfig) -> None:
        """Initialize the cvlc player.

        Args:
            config: Player configuration.
        """
        self.config = config
        self._process: subprocess.Popen | None = None
        self._running = False

    def start(self) -> None:
        """Start the cvlc process."""
        args = [
            self.config.cvlc_path,
            "--fullscreen",
            "--loop",
            "--no-osd",
            "--intf=dummy",
            "--no-video-title-show",
        ]

        logger.info("Starting cvlc: %s", " ".join(args))

        self._process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self._running = True

    def stop(self) -> None:
        """Stop the cvlc process."""
        if self._process:
            logger.info("Stopping cvlc (PID: %d)", self._process.pid)
            try:
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                self._process.wait(timeout=5)
            except (ProcessLookupError, TimeoutError):
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
            self._process = None
            self._running = False

    async def load_playlist(self, files: list[Path]) -> None:
        """Load a playlist of files by restarting cvlc with file arguments.

        Args:
            files: List of media file paths.
        """
        self.stop()

        args = [
            self.config.cvlc_path,
            "--fullscreen",
            "--loop",
            "--no-osd",
            "--intf=dummy",
            "--no-video-title-show",
        ]
        args.extend(str(f) for f in files)

        logger.info("Starting cvlc with %d files", len(files))

        self._process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self._running = True

    async def set_volume(self, volume: int) -> None:
        """Set playback volume.

        cvlc does not support runtime volume control without a
        control interface. This is a stub.

        Args:
            volume: Volume level (0-100).
        """
        logger.debug("cvlc set_volume stub called with %d (not supported at runtime)", volume)

    async def set_rotation(self, degrees: int) -> None:
        """Set video rotation.

        cvlc does not support runtime rotation without a
        control interface. This is a stub.

        Args:
            degrees: Rotation in degrees (0, 90, 180, 270).
        """
        logger.debug("cvlc set_rotation stub called with %d (not supported at runtime)", degrees)

    async def set_audio_output(self, output: str) -> None:
        """Set audio output device.

        cvlc does not support runtime audio device switching without a
        control interface. This is a stub.

        Args:
            output: Audio output device name.
        """
        logger.debug("cvlc set_audio_output stub called with %s (not supported at runtime)", output)

    async def show_osd(self, text: str, duration: int = 5000) -> None:
        """Show text on OSD.

        cvlc OSD is limited. This is a stub.

        Args:
            text: Text to display.
            duration: Display duration in milliseconds.
        """
        logger.debug("cvlc show_osd stub called with text=%r duration=%d", text, duration)

    @property
    def is_running(self) -> bool:
        """Check if cvlc is running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def pid(self) -> int | None:
        """Get cvlc process PID."""
        if self._process:
            return self._process.pid
        return None
