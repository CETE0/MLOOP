"""mpv playback backend for MLOOP."""

from __future__ import annotations

import contextlib
import logging
import os
import signal
import subprocess
from pathlib import Path

from mloop.audio.devices import get_audio_device_id
from mloop.config import PlaybackConfig, PlayerConfig
from mloop.player.backend import PlayerBackend, PlayerCapabilities
from mloop.player.ipc import MpvIpcClient

logger = logging.getLogger("mloop.player.mpv")


class MpvPlayer(PlayerBackend):
    """mpv playback controller."""

    def __init__(self, config: PlayerConfig, playback_config: PlaybackConfig | None = None) -> None:
        """Initialize the mpv player.

        Args:
            config: Player configuration.
        """
        self.config = config
        self.playback_config = playback_config or PlaybackConfig()
        self._process: subprocess.Popen | None = None
        self._ipc: MpvIpcClient | None = None
        self._running = False

    @property
    def capabilities(self) -> PlayerCapabilities:
        """Return mpv runtime capabilities."""
        return PlayerCapabilities(
            osd=True,
            runtime_volume=True,
            runtime_rotation=True,
            runtime_audio_output=True,
        )

    def start(self) -> None:
        """Start the mpv process."""
        socket_path = self.config.ipc_socket
        socket_dir = Path(socket_path).parent
        socket_dir.mkdir(parents=True, exist_ok=True)

        if Path(socket_path).exists():
            Path(socket_path).unlink()

        args = [
            self.config.mpv_path,
            "--fullscreen",
            "--idle=yes",
            f"--loop-playlist={'inf' if self.playback_config.loop else 'no'}",
            f"--image-display-duration={self.playback_config.image_duration_seconds}",
            f"--input-ipc-server={socket_path}",
            "--osd-level=1",
            "--no-terminal",
        ]

        logger.info("Starting mpv: %s", " ".join(args))

        self._process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self._running = True

    def stop(self) -> None:
        """Stop the mpv process."""
        if self._process:
            logger.info("Stopping mpv (PID: %d)", self._process.pid)
            try:
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("mpv did not exit after SIGTERM; sending SIGKILL")
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
                    self._process.wait(timeout=5)
            except ProcessLookupError:
                pass
            self._process = None
            self._running = False

    async def reset_after_exit(self) -> None:
        """Clear transient state after the mpv process exits unexpectedly."""
        if self._ipc is not None:
            await self._ipc.disconnect()
            self._ipc = None
        self._process = None
        self._running = False

    async def connect_ipc(self) -> MpvIpcClient:
        """Connect to mpv IPC socket.

        Returns:
            Connected IPC client.
        """
        if self._ipc is None:
            self._ipc = MpvIpcClient(self.config.ipc_socket)
            await self._ipc.connect()
        return self._ipc

    async def disconnect_ipc(self) -> None:
        """Disconnect from mpv IPC socket."""
        if self._ipc:
            await self._ipc.disconnect()
            self._ipc = None

    async def load_playlist(self, files: list[Path]) -> None:
        """Load a playlist of files.

        Args:
            files: List of media files.
        """
        ipc = await self.connect_ipc()
        await ipc.playlist_clear()

        for i, file_path in enumerate(files):
            mode = "append" if i > 0 else "replace"
            await ipc.loadfile(str(file_path), mode)

        logger.info("Loaded %d files into playlist", len(files))

    async def set_volume(self, volume: int) -> None:
        """Set playback volume.

        Args:
            volume: Volume level (0-100).
        """
        ipc = await self.connect_ipc()
        await ipc.set_volume(volume)
        logger.info("Volume set to %d", volume)

    async def set_rotation(self, degrees: int) -> None:
        """Set video rotation.

        Args:
            degrees: Rotation in degrees (0, 90, 180, 270).
        """
        ipc = await self.connect_ipc()
        await ipc.set_property("video-rotate", degrees)
        logger.info("Rotation set to %d degrees", degrees)

    async def set_audio_output(self, output: str) -> None:
        """Set audio output device.

        Args:
            output: Audio output device name.
        """
        ipc = await self.connect_ipc()
        await ipc.set_property("audio-device", get_audio_device_id(output))
        logger.info("Audio output set to %s", output)

    async def show_osd(self, text: str, duration: int = 5000) -> None:
        """Show text on OSD.

        Args:
            text: Text to display.
            duration: Display duration in milliseconds.
        """
        ipc = await self.connect_ipc()
        await ipc.show_text(text, duration)

    @property
    def is_running(self) -> bool:
        """Check if mpv is running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    @property
    def pid(self) -> int | None:
        """Get mpv process PID."""
        if self._process:
            return self._process.pid
        return None
