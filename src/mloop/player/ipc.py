"""mpv JSON IPC client for MLOOP."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any

logger = logging.getLogger("mloop.player.ipc")


class MpvIpcClient:
    """Client for communicating with mpv over JSON IPC."""

    def __init__(self, socket_path: str) -> None:
        """Initialize the IPC client.

        Args:
            socket_path: Path to the mpv IPC Unix socket.
        """
        self.socket_path = socket_path
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}

    async def connect(self) -> None:
        """Connect to the mpv IPC socket."""
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)
                logger.info("Connected to mpv IPC socket")
                asyncio.create_task(self._read_loop())
                return
            except (ConnectionRefusedError, FileNotFoundError):
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
                else:
                    raise

        raise ConnectionError(f"Could not connect to mpv IPC socket: {self.socket_path}")

    async def disconnect(self) -> None:
        """Disconnect from the mpv IPC socket."""
        if self._writer:
            self._writer.close()
            with contextlib.suppress(Exception):
                await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def _read_loop(self) -> None:
        """Read responses from mpv."""
        if not self._reader:
            return

        try:
            while True:
                line = await self._reader.readline()
                if not line:
                    break

                try:
                    data = json.loads(line.decode("utf-8"))
                    request_id = data.get("request_id")
                    if request_id and request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        future.set_result(data)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning("Failed to parse IPC message: %s", e)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("IPC read error: %s", e)

    async def _send_command(self, command: list[Any]) -> dict[str, Any]:
        """Send a command to mpv and wait for response.

        Args:
            command: Command list to send.

        Returns:
            Response dictionary from mpv.
        """
        if not self._writer:
            raise ConnectionError("Not connected to mpv IPC")

        self._request_id += 1
        request_id = self._request_id

        message = {
            "command": command,
            "request_id": request_id,
        }

        future: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        data = json.dumps(message) + "\n"
        self._writer.write(data.encode("utf-8"))
        await self._writer.drain()

        try:
            return await asyncio.wait_for(future, timeout=5.0)
        except TimeoutError as e:
            self._pending_requests.pop(request_id, None)
            raise TimeoutError("mpv IPC request timed out") from e

    async def command(self, *args: Any) -> dict[str, Any]:
        """Send a command to mpv.

        Args:
            *args: Command arguments.

        Returns:
            Response dictionary from mpv.
        """
        return await self._send_command(list(args))

    async def set_property(self, name: str, value: Any) -> dict[str, Any]:
        """Set an mpv property.

        Args:
            name: Property name.
            value: Property value.

        Returns:
            Response dictionary.
        """
        return await self.command("set_property", name, value)

    async def get_property(self, name: str) -> Any:
        """Get an mpv property.

        Args:
            name: Property name.

        Returns:
            Property value.
        """
        response = await self.command("get_property", name)
        return response.get("data")

    async def show_text(self, text: str, duration: int = 3000, level: int = 1) -> dict[str, Any]:
        """Show text on the OSD.

        Args:
            text: Text to display.
            duration: Display duration in milliseconds.
            level: OSD level.

        Returns:
            Response dictionary.
        """
        return await self.command("show_text", text, duration, level)

    async def loadfile(
        self,
        path: str,
        mode: str = "replace",
    ) -> dict[str, Any]:
        """Load a file for playback.

        Args:
            path: File path.
            mode: Load mode (replace, append, append-play).

        Returns:
            Response dictionary.
        """
        return await self.command("loadfile", path, mode)

    async def playlist_clear(self) -> dict[str, Any]:
        """Clear the playlist."""
        return await self.command("playlist_clear")

    async def playlist_next(self) -> dict[str, Any]:
        """Go to next item in playlist."""
        return await self.command("playlist_next")

    async def set_volume(self, volume: int) -> dict[str, Any]:
        """Set playback volume.

        Args:
            volume: Volume level (0-100).

        Returns:
            Response dictionary.
        """
        return await self.set_property("volume", volume)

    async def set_af(self, audio_filter: str) -> dict[str, Any]:
        """Set audio filter.

        Args:
            audio_filter: Audio filter string.

        Returns:
            Response dictionary.
        """
        return await self.set_property("af", audio_filter)

    async def set_vf(self, video_filter: str) -> dict[str, Any]:
        """Set video filter.

        Args:
            video_filter: Video filter string.

        Returns:
            Response dictionary.
        """
        return await self.set_property("vf", video_filter)
