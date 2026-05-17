"""Gesture event definitions for MLOOP."""

from enum import Enum


class GestureIntent(Enum):
    """Gesture intent emitted by the state machine."""

    ENTER_MENU = "enter_menu"
    NEXT_ITEM = "next_item"
    SELECT_ITEM = "select_item"
    TIMEOUT = "timeout"
