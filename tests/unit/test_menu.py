"""Tests for menu model and controller."""

import pytest

from mloop.config import MenuConfig
from mloop.gestures.events import GestureIntent
from mloop.menu.controller import MenuController
from mloop.menu.model import MenuItem, MenuModel


@pytest.fixture
def menu_model() -> MenuModel:
    """Create a menu model with test items."""
    items = [
        MenuItem(label="Item 1", action=lambda: None),
        MenuItem(label="Item 2", action=lambda: None),
        MenuItem(label="Item 3", action=lambda: None),
    ]
    return MenuModel(items)


@pytest.fixture
def controller(menu_model: MenuModel) -> MenuController:
    """Create a menu controller."""
    config = MenuConfig(confirm_dangerous_actions=True)
    return MenuController(menu_model, config)


def test_menu_initially_closed(menu_model: MenuModel) -> None:
    """Test that menu is initially closed."""
    assert menu_model.is_open is False
    assert menu_model.cursor == 0


def test_open_menu(menu_model: MenuModel) -> None:
    """Test opening the menu."""
    menu_model.open()
    assert menu_model.is_open is True
    assert menu_model.cursor == 0


def test_close_menu(menu_model: MenuModel) -> None:
    """Test closing the menu."""
    menu_model.open()
    menu_model.close()
    assert menu_model.is_open is False
    assert menu_model.cursor == 0


def test_next_item(menu_model: MenuModel) -> None:
    """Test moving to next item."""
    menu_model.open()
    assert menu_model.cursor == 0

    menu_model.next_item()
    assert menu_model.cursor == 1

    menu_model.next_item()
    assert menu_model.cursor == 2


def test_next_item_wraps(menu_model: MenuModel) -> None:
    """Test that next item wraps around."""
    menu_model.open()
    menu_model.cursor = 2

    menu_model.next_item()
    assert menu_model.cursor == 0


def test_selected_item(menu_model: MenuModel) -> None:
    """Test getting selected item."""
    menu_model.open()
    assert menu_model.selected_item is not None
    assert menu_model.selected_item.label == "Item 1"

    menu_model.next_item()
    assert menu_model.selected_item.label == "Item 2"


def test_render_menu(menu_model: MenuModel) -> None:
    """Test menu rendering."""
    menu_model.open()
    rendered = menu_model.render()

    assert "MLOOP Menu" in rendered
    assert "Item 1" in rendered
    assert "> 1." in rendered


def test_controller_handle_enter_menu(controller: MenuController) -> None:
    """Test controller handles enter menu intent."""
    controller.handle_intent(GestureIntent.ENTER_MENU)
    assert controller.model.is_open is True


def test_controller_handle_next_item(controller: MenuController) -> None:
    """Test controller handles next item intent."""
    controller.handle_intent(GestureIntent.ENTER_MENU)
    controller.handle_intent(GestureIntent.NEXT_ITEM)
    assert controller.model.cursor == 1


def test_controller_handle_timeout(controller: MenuController) -> None:
    """Test controller handles timeout intent."""
    controller.handle_intent(GestureIntent.ENTER_MENU)
    controller.handle_intent(GestureIntent.TIMEOUT)
    assert controller.model.is_open is False


def test_dangerous_item_requires_confirmation() -> None:
    """Test that dangerous items require confirmation."""
    executed = []
    items = [
        MenuItem(label="Dangerous", action=lambda: executed.append(True), is_dangerous=True),
    ]
    model = MenuModel(items)
    config = MenuConfig(confirm_dangerous_actions=True)
    controller = MenuController(model, config)

    controller.handle_intent(GestureIntent.ENTER_MENU)
    controller.handle_intent(GestureIntent.SELECT_ITEM)

    assert len(executed) == 0

    controller.handle_intent(GestureIntent.SELECT_ITEM)
    assert len(executed) == 1
