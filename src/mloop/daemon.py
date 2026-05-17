"""Main daemon logic for MLOOP."""

from __future__ import annotations

import asyncio
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
from mloop.player.mpv import MpvPlayer
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
        self.player = MpvPlayer(self.config.player)
        self.gesture_machine = GestureStateMachine(self.config.hdmi_gestures)
        self.menu_model = MenuModel()
        self.menu_controller = MenuController(self.menu_model, self.config.menu)
        self._hdmi_watcher: HdmiWatcher | None = None
        self._current_volume = [self.config.playback.volume]
        self._current_rotation = [self.config.display.rotation]
        self._current_audio_idx = [0]

    def run(self) -> None:
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

        self.player.start()

        try:
            self._run_main_loop()
        finally:
            self.stop()

    def _run_main_loop(self) -> None:
        """Run the main event loop."""
        self._load_media()

        while self.service.is_running:
            now_ms = int(time.monotonic() * 1000)
            self.gesture_machine.check_timeouts(now_ms)

            if not self.player.is_running:
                self.logger.warning("mpv exited unexpectedly, restarting")
                self.player.start()

            time.sleep(0.1)

    def stop(self) -> None:
        """Stop the daemon."""
        self.logger.info("MLOOP stopping")
        self.service.stop()

        if self._hdmi_watcher:
            asyncio.get_event_loop().run_until_complete(self._hdmi_watcher.stop())

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
            MenuItem(label="Show network info", action=create_network_info_action()),
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

    def _load_media(self) -> None:
        """Scan and load media files."""
        self.logger.info("Scanning media directories: %s", self.config.playback.media_dirs)
        files = scan_media_dirs(self.config.playback.media_dirs)

        if not files:
            self.logger.warning("No media files found")
            asyncio.get_event_loop().run_until_complete(
                self.player.show_osd("No media files found", 10000)
            )
            return

        playlist = build_playlist(
            files,
            shuffle=self.config.playback.shuffle,
            loop=self.config.playback.loop,
        )

        self.logger.info("Loaded %d files into playlist", len(playlist))
        asyncio.get_event_loop().run_until_complete(self.player.load_playlist(playlist))

    def _on_hdmi_event(self, event: HdmiEvent) -> None:
        """Handle HDMI event.

        Args:
            event: HDMI event.
        """
        self.gesture_machine.handle_event(event)

        if self.menu_model.is_open:
            asyncio.get_event_loop().run_until_complete(
                self.player.show_osd(self.menu_model.render(), self.config.menu.osd_duration_ms)
            )
