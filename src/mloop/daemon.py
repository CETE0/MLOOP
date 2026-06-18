"""Main daemon logic for MLOOP."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time

from mloop.config import Config, load_config
from mloop.display.drm import discover_connectors
from mloop.display.hdmi_watcher import HdmiEvent, HdmiWatcher
from mloop.gestures.state_machine import GestureStateMachine
from mloop.logging import setup_logging
from mloop.media import build_playlist, scan_media_dirs
from mloop.menu.actions import (
    create_audio_output_action,
    create_network_info_action,
    create_reboot_action,
    create_rescan_action,
    create_resume_action,
    create_rotation_action,
    create_shutdown_action,
    create_volume_action,
)
from mloop.menu.controller import MenuController
from mloop.menu.model import MenuItem, MenuModel
from mloop.player import create_player
from mloop.state import RuntimeState
from mloop.system.platform import get_platform_info
from mloop.system.service import ServiceManager

logger = logging.getLogger("mloop.daemon")


class Daemon:
    """MLOOP main daemon."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the daemon.

        Args:
            config: Configuration object. Loads from default path if not provided.
        """
        self.config = config or load_config()
        self.logger = setup_logging()
        self.service = ServiceManager()
        self.player = create_player(self.config.player, self.config.playback)
        self.state = RuntimeState(
            volume=self.config.playback.volume,
            rotation=self.config.display.rotation,
            audio_output=self.config.audio.output,
        )
        self.gesture_machine = GestureStateMachine(self.config.hdmi_gestures)
        self.menu_model = MenuModel()
        self.menu_controller = MenuController(self.menu_model, self.config.menu)
        self._hdmi_watcher: HdmiWatcher | None = None
        self._watcher_task: asyncio.Task[None] | None = None
        self._player_restart_backoff_seconds = 0.0
        self._current_volume = [self.state.volume]
        self._current_rotation = [self.state.rotation]
        self._current_audio_idx = [0]

    async def run(self) -> None:
        """Run the daemon."""
        self.logger.info("MLOOP starting")

        get_platform_info()
        self.logger.info("Config loaded from defaults")

        self.service.setup_signal_handlers()
        self.service.start()

        self._setup_gesture_handlers()
        self._build_menu()

        connectors = discover_connectors(self.config.display.connector)
        if connectors:
            self._hdmi_watcher = HdmiWatcher(
                connectors=connectors,
                debounce_ms=self.config.hdmi_gestures.debounce_ms,
            )
            self._hdmi_watcher.on_event(self._on_hdmi_event)
            self._watcher_task = asyncio.create_task(self._hdmi_watcher.start())

        self.player.start()
        await self._load_media()
        await self._apply_player_state()

        try:
            await self._run_main_loop()
        finally:
            await self.stop()

    async def _run_main_loop(self) -> None:
        """Run the main event loop."""
        while self.service.is_running:
            now_ms = int(time.monotonic() * 1000)
            self.gesture_machine.check_timeouts(now_ms)

            if not self.player.is_running:
                await self._recover_player()

            await asyncio.sleep(0.1)

    async def _recover_player(self) -> None:
        """Restart the player after an unexpected process exit."""
        self.logger.warning("%s exited unexpectedly, restarting", type(self.player).__name__)

        await self.player.reset_after_exit()

        delay = self._player_restart_backoff_seconds
        if delay > 0:
            await asyncio.sleep(delay)

        try:
            self.player.start()
            await self._load_media()
            await self._apply_player_state()
        except Exception:
            self._player_restart_backoff_seconds = min(
                max(1.0, self._player_restart_backoff_seconds * 2),
                60.0,
            )
            self.logger.exception(
                "Player restart failed; next retry in %.1fs",
                self._player_restart_backoff_seconds,
            )
            return

        self._player_restart_backoff_seconds = 0.0

    async def _apply_player_state(self) -> None:
        """Apply configured runtime player state."""
        await self.player.set_volume(self.state.volume)
        await self.player.set_rotation(self.state.rotation)
        await self.player.set_audio_output(self.state.audio_output)

    async def stop(self) -> None:
        """Stop the daemon."""
        self.logger.info("MLOOP stopping")
        self.service.stop()

        if self._hdmi_watcher:
            await self._hdmi_watcher.stop()

        if self._watcher_task and not self._watcher_task.done():
            try:
                await asyncio.wait_for(self._watcher_task, timeout=1.0)
            except TimeoutError:
                self._watcher_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._watcher_task

        self.player.stop()

    def _setup_gesture_handlers(self) -> None:
        """Setup gesture and menu handlers."""
        self.gesture_machine.on_intent(self.menu_controller.handle_intent)

    def _build_menu(self) -> None:
        """Build the menu items."""
        items = [
            MenuItem(label="Resume playback", action=create_resume_action()),
            MenuItem(
                label="Volume",
                action=create_volume_action(self.player, self._current_volume),
            ),
            MenuItem(
                label="Audio output",
                action=create_audio_output_action(
                    self.player, ["auto", "hdmi"], self._current_audio_idx
                ),
            ),
            MenuItem(
                label="Rotate video",
                action=create_rotation_action(self.player, self._current_rotation),
            ),
            MenuItem(
                label="Rescan media",
                action=create_rescan_action(self._load_media),
            ),
            MenuItem(
                label="Show network info",
                action=create_network_info_action(self.player, self.config.menu.osd_duration_ms),
            ),
            MenuItem(
                label="Reboot",
                action=create_reboot_action(),
                is_dangerous=True,
            ),
            MenuItem(
                label="Shutdown",
                action=create_shutdown_action(),
                is_dangerous=True,
            ),
        ]

        self.menu_model = MenuModel(items)
        self.menu_controller = MenuController(self.menu_model, self.config.menu)
        self.gesture_machine.on_intent(self.menu_controller.handle_intent)

    async def _load_media(self) -> None:
        """Scan and load media files."""
        self.logger.info("Scanning media directories: %s", self.config.playback.media_dirs)
        files = scan_media_dirs(self.config.playback.media_dirs)

        if not files:
            self.logger.warning("No media files found")
            await self.player.show_osd("No media files found", 10000)
            return

        playlist = build_playlist(
            files,
            shuffle=self.config.playback.shuffle,
        )

        self.logger.info("Loaded %d files into playlist", len(playlist))
        await self.player.load_playlist(playlist)

    def _on_hdmi_event(self, event: HdmiEvent) -> None:
        """Handle HDMI event.

        Args:
            event: HDMI event.
        """
        self.gesture_machine.handle_event(event)

        if self.menu_model.is_open:
            asyncio.create_task(
                self.player.show_osd(self.menu_model.render(), self.config.menu.osd_duration_ms)
            )
