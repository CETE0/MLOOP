"""HDMI state watcher for MLOOP."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from mloop.display.drm import DrmConnector

logger = logging.getLogger("mloop.display.hdmi_watcher")


@dataclass
class HdmiEvent:
    """Normalized HDMI state event."""

    connector: str
    state: str
    monotonic_ms: int


class HdmiWatcher:
    """Watches HDMI connector state changes."""

    def __init__(
        self,
        connectors: list[DrmConnector],
        debounce_ms: int = 500,
        poll_interval_ms: int = 200,
    ) -> None:
        """Initialize the HDMI watcher.

        Args:
            connectors: List of DRM connectors to watch.
            debounce_ms: Debounce time in milliseconds.
            poll_interval_ms: Polling interval in milliseconds.
        """
        self.connectors = connectors
        self.debounce_ms = debounce_ms
        self.poll_interval_ms = poll_interval_ms
        self._running = False
        self._last_state: dict[str, str] = {}
        self._last_change_ms: dict[str, int] = {}
        self._callbacks: list[Callable[[HdmiEvent], None]] = []

    def on_event(self, callback: Callable[[HdmiEvent], None]) -> None:
        """Register an event callback.

        Args:
            callback: Function to call on HDMI events.
        """
        self._callbacks.append(callback)

    async def start(self) -> None:
        """Start watching HDMI state changes."""
        self._running = True

        for connector in self.connectors:
            self._last_state[connector.name] = connector.read_status()
            self._last_change_ms[connector.name] = self._now_ms()

        logger.info("HDMI watcher started for %d connectors", len(self.connectors))

        while self._running:
            await self._poll()
            await asyncio.sleep(self.poll_interval_ms / 1000.0)

    async def stop(self) -> None:
        """Stop watching HDMI state changes."""
        self._running = False
        logger.info("HDMI watcher stopped")

    async def _poll(self) -> None:
        """Poll connector states and emit events."""
        now = self._now_ms()

        for connector in self.connectors:
            current_status = connector.read_status()
            last_status = self._last_state.get(connector.name)

            if current_status != last_status:
                last_change = self._last_change_ms.get(connector.name, 0)

                if now - last_change >= self.debounce_ms:
                    event = HdmiEvent(
                        connector=connector.name,
                        state=current_status,
                        monotonic_ms=now,
                    )
                    logger.info(
                        "HDMI event connector=%s state=%s source=poll",
                        event.connector,
                        event.state,
                    )
                    self._emit(event)

                    self._last_state[connector.name] = current_status
                    self._last_change_ms[connector.name] = now

    def _emit(self, event: HdmiEvent) -> None:
        """Emit an HDMI event to all callbacks.

        Args:
            event: HDMI event to emit.
        """
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error("Error in HDMI event callback: %s", e)

    @staticmethod
    def _now_ms() -> int:
        """Get current monotonic time in milliseconds.

        Returns:
            Current time in milliseconds.
        """
        return int(time.monotonic() * 1000)
