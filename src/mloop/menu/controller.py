"""Menu controller for MLOOP."""

from __future__ import annotations

import logging

from mloop.config import MenuConfig
from mloop.gestures.events import GestureIntent
from mloop.menu.model import MenuModel

logger = logging.getLogger("mloop.menu.controller")


class MenuController:
    """Controls menu state and actions."""

    def __init__(self, model: MenuModel, config: MenuConfig) -> None:
        """Initialize the menu controller.

        Args:
            model: Menu model.
            config: Menu configuration.
        """
        self.model = model
        self.config = config
        self._pending_action = False

    def handle_intent(self, intent: GestureIntent) -> None:
        """Handle a gesture intent.

        Args:
            intent: Gesture intent.
        """
        if intent == GestureIntent.ENTER_MENU:
            self._open_menu()
        elif intent == GestureIntent.NEXT_ITEM:
            self._next_item()
        elif intent == GestureIntent.SELECT_ITEM:
            self._select_item()
        elif intent == GestureIntent.TIMEOUT:
            self._close_menu()

    def _open_menu(self) -> None:
        """Open the menu."""
        self.model.open()
        logger.info("Menu opened")

    def _next_item(self) -> None:
        """Move to next menu item."""
        if self.model.is_open:
            self.model.next_item()
            logger.info("Menu cursor moved to: %s", self.model.selected_item)

    def _select_item(self) -> None:
        """Select the current menu item."""
        if not self.model.is_open:
            return

        item = self.model.selected_item
        if item is None:
            return

        if item.is_dangerous and self.config.confirm_dangerous_actions:
            if self._pending_action:
                self._execute_action(item)
                self._pending_action = False
            else:
                logger.info("Confirmation required for: %s", item.label)
                self._pending_action = True
        else:
            self._execute_action(item)

    def _execute_action(self, item) -> None:
        """Execute a menu item action.

        Args:
            item: Menu item to execute.
        """
        logger.info("Executing menu action: %s", item.label)
        try:
            item.action()
        except Exception as e:
            logger.error("Error executing action %s: %s", item.label, e)

    def _close_menu(self) -> None:
        """Close the menu."""
        self.model.close()
        self._pending_action = False
        logger.info("Menu closed")
