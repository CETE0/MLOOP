"""Tests for gesture state machine."""

import pytest

from mloop.config import HdmiGesturesConfig
from mloop.display.hdmi_watcher import HdmiEvent
from mloop.gestures.events import GestureIntent
from mloop.gestures.state_machine import GestureState, GestureStateMachine


@pytest.fixture
def config() -> HdmiGesturesConfig:
    """Create test gesture configuration."""
    return HdmiGesturesConfig(
        enabled=True,
        enter_min_disconnect_ms=800,
        enter_max_disconnect_ms=8000,
        cycle_min_disconnect_ms=300,
        cycle_max_disconnect_ms=5000,
        debounce_ms=500,
        select_after_connected_ms=5000,
        menu_timeout_ms=30000,
    )


@pytest.fixture
def machine(config: HdmiGesturesConfig) -> GestureStateMachine:
    """Create gesture state machine."""
    return GestureStateMachine(config)


def create_event(state: str, time_ms: int) -> HdmiEvent:
    """Create an HDMI event.

    Args:
        state: HDMI state.
        time_ms: Event time in milliseconds.

    Returns:
        HDMI event.
    """
    return HdmiEvent(connector="HDMI-A-1", state=state, monotonic_ms=time_ms)


def test_initial_state(machine: GestureStateMachine) -> None:
    """Test that machine starts in idle state."""
    assert machine.state == GestureState.IDLE
    assert machine.is_menu_open is False


def test_disabled_machine() -> None:
    """Test that disabled machine ignores events."""
    config = HdmiGesturesConfig(enabled=False)
    machine = GestureStateMachine(config)
    machine.handle_event(create_event("disconnected", 1000))
    assert machine.state == GestureState.IDLE


def test_enter_menu_short_disconnect(machine: GestureStateMachine) -> None:
    """Test that short disconnect does not enter menu."""
    intents: list[GestureIntent] = []
    machine.on_intent(lambda i: intents.append(i))

    machine.handle_event(create_event("disconnected", 1000))
    machine.handle_event(create_event("connected", 1400))

    assert GestureIntent.ENTER_MENU not in intents


def test_enter_menu_valid_disconnect(machine: GestureStateMachine) -> None:
    """Test that valid disconnect enters menu."""
    intents: list[GestureIntent] = []
    machine.on_intent(lambda i: intents.append(i))

    machine.handle_event(create_event("disconnected", 1000))
    machine.handle_event(create_event("connected", 3000))

    assert GestureIntent.ENTER_MENU in intents
    assert machine.is_menu_open is True


def test_enter_menu_too_long_disconnect(machine: GestureStateMachine) -> None:
    """Test that too long disconnect does not enter menu."""
    intents: list[GestureIntent] = []
    machine.on_intent(lambda i: intents.append(i))

    machine.handle_event(create_event("disconnected", 1000))
    machine.handle_event(create_event("connected", 10000))

    assert GestureIntent.ENTER_MENU not in intents


def test_menu_navigation(machine: GestureStateMachine) -> None:
    """Test menu navigation gesture."""
    intents: list[GestureIntent] = []
    machine.on_intent(lambda i: intents.append(i))

    machine.handle_event(create_event("disconnected", 1000))
    machine.handle_event(create_event("connected", 3000))

    assert machine.is_menu_open is True

    machine.handle_event(create_event("disconnected", 4000))
    machine.handle_event(create_event("connected", 4500))

    assert GestureIntent.NEXT_ITEM in intents


def test_menu_timeout(machine: GestureStateMachine) -> None:
    """Test menu timeout."""
    intents: list[GestureIntent] = []
    machine.on_intent(lambda i: intents.append(i))

    machine.handle_event(create_event("disconnected", 1000))
    machine.handle_event(create_event("connected", 3000))

    assert machine.is_menu_open is True

    machine.check_timeouts(3000 + 30000)

    assert GestureIntent.TIMEOUT in intents
    assert machine.is_menu_open is False


def test_select_timeout(machine: GestureStateMachine) -> None:
    """Test select after connected timeout."""
    intents: list[GestureIntent] = []
    machine.on_intent(lambda i: intents.append(i))

    machine.handle_event(create_event("disconnected", 1000))
    machine.handle_event(create_event("connected", 3000))

    machine.check_timeouts(3000 + 5000)

    assert GestureIntent.SELECT_ITEM in intents


def test_reset(machine: GestureStateMachine) -> None:
    """Test state machine reset."""
    machine.handle_event(create_event("disconnected", 1000))
    machine.handle_event(create_event("connected", 3000))

    assert machine.is_menu_open is True

    machine.reset()

    assert machine.state == GestureState.IDLE
    assert machine.is_menu_open is False
