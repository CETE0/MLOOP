"""Gesture state machine for MLOOP."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import Enum

from mloop.config import HdmiGesturesConfig
from mloop.display.hdmi_watcher import HdmiEvent
from mloop.gestures.events import GestureIntent

logger = logging.getLogger("mloop.gestures.state_machine")


class GestureState(Enum):
    """States for the gesture state machine."""

    IDLE = "idle"
    MENU_OPEN = "menu_open"
    SELECTING = "selecting"
    CONFIRMING = "confirming"


class GestureStateMachine:
    """Converts HDMI events into gesture intents."""

    def __init__(self, config: HdmiGesturesConfig) -> None:
        """Initialize the gesture state machine.

        Args:
            config: HDMI gestures configuration.
        """
        self.config = config
        self._state = GestureState.IDLE
        self._disconnect_start_ms: int | None = None
        self._connect_time_ms: int | None = None
        self._menu_entered_ms: int | None = None
        self._callbacks: list[Callable[[GestureIntent], None]] = []

    def on_intent(self, callback: Callable[[GestureIntent], None]) -> None:
        """Register an intent callback.

        Args:
            callback: Function to call on gesture intents.
        """
        self._callbacks.append(callback)

    def clear_intent_callbacks(self) -> None:
        """Clear registered intent callbacks."""
        self._callbacks.clear()

    def handle_event(self, event: HdmiEvent) -> None:
        """Process an HDMI event.

        Args:
            event: HDMI event to process.
        """
        if not self.config.enabled:
            return

        now = event.monotonic_ms

        if event.state == "disconnected":
            self._on_disconnect(now)
        elif event.state == "connected":
            self._on_connect(now)

    def _on_disconnect(self, now_ms: int) -> None:
        """Handle HDMI disconnect.

        Args:
            now_ms: Current time in milliseconds.
        """
        self._disconnect_start_ms = now_ms
        self._connect_time_ms = None

        if self._state == GestureState.SELECTING:
            self._state = GestureState.MENU_OPEN
            logger.info("Gesture intent=NEXT_ITEM (navigation gesture)")
            self._emit(GestureIntent.NEXT_ITEM)

    def _on_connect(self, now_ms: int) -> None:
        """Handle HDMI connect.

        Args:
            now_ms: Current time in milliseconds.
        """
        if self._disconnect_start_ms is None:
            return

        disconnect_duration = now_ms - self._disconnect_start_ms
        self._connect_time_ms = now_ms

        logger.info(
            "HDMI reconnect disconnect_duration_ms=%d state=%s",
            disconnect_duration,
            self._state.value,
        )

        if self._state == GestureState.IDLE:
            self._handle_enter_menu(disconnect_duration, now_ms)
        elif self._state == GestureState.MENU_OPEN:
            self._handle_menu_navigation(disconnect_duration, now_ms)
        elif self._state == GestureState.SELECTING:
            self._handle_selection(disconnect_duration, now_ms)

    def _handle_enter_menu(self, duration_ms: int, now_ms: int) -> None:
        """Check if gesture should enter menu.

        Args:
            duration_ms: Disconnect duration in milliseconds.
            now_ms: Current time in milliseconds.
        """
        if (
            self.config.enter_min_disconnect_ms
            <= duration_ms
            <= self.config.enter_max_disconnect_ms
        ):
            self._state = GestureState.MENU_OPEN
            self._menu_entered_ms = now_ms
            logger.info(
                "Gesture intent=ENTER_MENU disconnect_duration_ms=%d",
                duration_ms,
            )
            self._emit(GestureIntent.ENTER_MENU)
        else:
            logger.debug(
                "Disconnect duration %dms not in enter menu range [%d, %d]",
                duration_ms,
                self.config.enter_min_disconnect_ms,
                self.config.enter_max_disconnect_ms,
            )

    def _handle_menu_navigation(self, duration_ms: int, now_ms: int) -> None:
        """Handle menu navigation gesture.

        Args:
            duration_ms: Disconnect duration in milliseconds.
            now_ms: Current time in milliseconds.
        """
        if (
            self.config.cycle_min_disconnect_ms
            <= duration_ms
            <= self.config.cycle_max_disconnect_ms
        ):
            self._state = GestureState.MENU_OPEN
            self._menu_entered_ms = now_ms
            logger.info(
                "Gesture intent=NEXT_ITEM disconnect_duration_ms=%d",
                duration_ms,
            )
            self._emit(GestureIntent.NEXT_ITEM)

    def _handle_selection(self, duration_ms: int, now_ms: int) -> None:
        """Handle selection gesture.

        Args:
            duration_ms: Disconnect duration in milliseconds.
            now_ms: Current time in milliseconds.
        """
        self._state = GestureState.MENU_OPEN
        self._menu_entered_ms = now_ms

    def check_timeouts(self, now_ms: int | None = None) -> None:
        """Check for timeout conditions.

        Args:
            now_ms: Current time in milliseconds. Uses current time if not provided.
        """
        if now_ms is None:
            now_ms = int(time.monotonic() * 1000)

        if self._state == GestureState.MENU_OPEN and self._menu_entered_ms is not None:
            elapsed = now_ms - self._menu_entered_ms

            if elapsed >= self.config.menu_timeout_ms:
                logger.info("Gesture intent=TIMEOUT (menu timeout)")
                self._state = GestureState.IDLE
                self._emit(GestureIntent.TIMEOUT)
                return

            if (
                self._connect_time_ms is not None
                and now_ms - self._connect_time_ms >= self.config.select_after_connected_ms
            ):
                self._state = GestureState.SELECTING
                logger.info("Gesture intent=SELECT_ITEM (select timeout)")
                self._emit(GestureIntent.SELECT_ITEM)

    def reset(self) -> None:
        """Reset the state machine to idle."""
        self._state = GestureState.IDLE
        self._disconnect_start_ms = None
        self._connect_time_ms = None
        self._menu_entered_ms = None
        logger.info("Gesture state machine reset to IDLE")

    @property
    def state(self) -> GestureState:
        """Get current state."""
        return self._state

    @property
    def is_menu_open(self) -> bool:
        """Check if menu is open."""
        return self._state in (GestureState.MENU_OPEN, GestureState.SELECTING)

    def _emit(self, intent: GestureIntent) -> None:
        """Emit a gesture intent.

        Args:
            intent: Gesture intent to emit.
        """
        for callback in self._callbacks:
            try:
                callback(intent)
            except Exception as e:
                logger.error("Error in gesture intent callback: %s", e)
