"""Menu data model for MLOOP."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

Action = Callable[[], None]


@dataclass
class MenuItem:
    """A single menu item."""

    label: str
    action: Action
    is_dangerous: bool = False
    submenu: list[MenuItem] | None = None

    def __str__(self) -> str:
        """String representation of menu item."""
        prefix = "!" if self.is_dangerous else " "
        return f"{prefix} {self.label}"


class MenuModel:
    """Menu state model."""

    def __init__(self, items: list[MenuItem] | None = None) -> None:
        """Initialize the menu model.

        Args:
            items: List of menu items.
        """
        self.items = items or []
        self._cursor = 0
        self._open = False

    @property
    def cursor(self) -> int:
        """Get current cursor position."""
        return self._cursor

    @cursor.setter
    def cursor(self, value: int) -> None:
        """Set cursor position.

        Args:
            value: New cursor position.
        """
        if self.items:
            self._cursor = value % len(self.items)

    @property
    def is_open(self) -> bool:
        """Check if menu is open."""
        return self._open

    def open(self) -> None:
        """Open the menu."""
        self._open = True
        self._cursor = 0

    def close(self) -> None:
        """Close the menu."""
        self._open = False
        self._cursor = 0

    def next_item(self) -> None:
        """Move cursor to next item."""
        if self.items:
            self._cursor = (self._cursor + 1) % len(self.items)

    @property
    def selected_item(self) -> MenuItem | None:
        """Get the currently selected item."""
        if self.items and 0 <= self._cursor < len(self.items):
            return self.items[self._cursor]
        return None

    def render(self) -> str:
        """Render the menu as a string for OSD display.

        Returns:
            Formatted menu string.
        """
        if not self.items:
            return "No menu items"

        lines = ["=== MLOOP Menu ===", ""]
        for i, item in enumerate(self.items):
            marker = ">" if i == self._cursor else " "
            prefix = "!" if item.is_dangerous else " "
            lines.append(f"{marker} {i + 1}. {prefix}{item.label}")

        lines.extend(["", "Unplug/replug: navigate", "Wait: select"])
        return "\n".join(lines)
