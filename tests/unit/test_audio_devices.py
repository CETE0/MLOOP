"""Tests for audio device resolution and output mapping."""

import asyncio

import pytest

from mloop.audio.devices import resolve_audio_outputs
from mloop.menu.actions import create_audio_output_action


class FakeMpvPlayer:
    """Fake player that records audio-device changes."""

    def __init__(self) -> None:
        self.last_device: str | None = None

    async def set_audio_output(self, device_id: str) -> None:
        self.last_device = device_id


def test_resolve_none_returns_default() -> None:
    """None / no devices returns only the auto fallback."""
    result = resolve_audio_outputs(None)
    assert result == [("Auto", "auto")]


def test_resolve_empty_returns_default() -> None:
    """Empty list returns only the auto fallback."""
    result = resolve_audio_outputs([])
    assert result == [("Auto", "auto")]


def test_resolve_hdmi_device() -> None:
    """HDMI keyword in description maps to HDMI label."""
    devices = [
        {"name": "auto", "description": "Default"},
        {"name": "alsa/hdmi:CARD=vc4hdmi,DEV=0", "description": "vc4-hdmi-hifi, HDMI/DP"},
    ]
    result = resolve_audio_outputs(devices)
    assert result[0] == ("Auto", "auto")
    assert ("HDMI", "alsa/hdmi:CARD=vc4hdmi,DEV=0") in result


def test_resolve_analog_device() -> None:
    """Analogue/headphone keywords map to Analog label."""
    devices = [
        {"name": "auto", "description": "Default"},
        {
            "name": "alsa/analog:CARD=Headphones,DEV=0",
            "description": "bcm2835-headphones, Headphones",
        },
    ]
    result = resolve_audio_outputs(devices)
    assert result[0] == ("Auto", "auto")
    assert ("Analog", "alsa/analog:CARD=Headphones,DEV=0") in result


def test_resolve_multiple_devices() -> None:
    """Multiple devices are all mapped."""
    devices = [
        {"name": "auto", "description": "Default"},
        {"name": "alsa/hdmi:CARD=vc4hdmi,DEV=0", "description": "HDMI/DP"},
        {"name": "alsa/hdmi:CARD=vc4hdmi,DEV=1", "description": "HDMI/DP #2"},
        {"name": "alsa/headphones", "description": "Headphones"},
    ]
    result = resolve_audio_outputs(devices)
    assert result[0] == ("Auto", "auto")
    assert len(result) == 4
    assert result[1] == ("HDMI", "alsa/hdmi:CARD=vc4hdmi,DEV=0")
    assert result[2] == ("HDMI", "alsa/hdmi:CARD=vc4hdmi,DEV=1")
    assert result[3] == ("Analog", "alsa/headphones")


def test_resolve_displayport_keyword() -> None:
    """DisplayPort keyword is treated like HDMI."""
    devices = [
        {"name": "auto", "description": "Default"},
        {"name": "alsa/dp:CARD=GPU,DEV=0", "description": "GPU, DisplayPort"},
    ]
    result = resolve_audio_outputs(devices)
    assert ("HDMI", "alsa/dp:CARD=GPU,DEV=0") in result


def test_resolve_speaker_keyword() -> None:
    """Speaker keyword maps to Analog."""
    devices = [
        {"name": "auto", "description": "Default"},
        {"name": "alsa/speaker", "description": "Built-in Speaker"},
    ]
    result = resolve_audio_outputs(devices)
    assert ("Analog", "alsa/speaker") in result


def test_resolve_case_insensitive() -> None:
    """Keyword matching is case-insensitive."""
    devices = [
        {"name": "auto", "description": "Default"},
        {"name": "alsa/HDMI", "description": "HDMI Output"},
    ]
    result = resolve_audio_outputs(devices)
    assert ("HDMI", "alsa/HDMI") in result


def test_resolve_unknown_device_skipped() -> None:
    """Devices with no recognisable keywords are omitted."""
    devices = [
        {"name": "auto", "description": "Default"},
        {"name": "alsa/unknown", "description": "Mystery sink"},
    ]
    result = resolve_audio_outputs(devices)
    assert len(result) == 1
    assert result == [("Auto", "auto")]


def test_resolve_no_auto_in_list() -> None:
    """Auto is always prepended even when not in the device list."""
    devices = [
        {"name": "alsa/hdmi", "description": "HDMI"},
    ]
    result = resolve_audio_outputs(devices)
    assert result[0] == ("Auto", "auto")


@pytest.mark.asyncio
async def test_audio_output_action_cycles() -> None:
    """create_audio_output_action cycles through (label, device_id) and sends ids."""
    player = FakeMpvPlayer()
    outputs: list[tuple[str, str]] = [
        ("Auto", "auto"),
        ("HDMI", "alsa/hdmi:CARD=vc4hdmi"),
    ]
    current = [0]
    action = create_audio_output_action(player, outputs, current)

    action()
    await asyncio.sleep(0)
    assert current[0] == 1
    assert player.last_device == "alsa/hdmi:CARD=vc4hdmi"

    action()
    await asyncio.sleep(0)
    assert current[0] == 0
    assert player.last_device == "auto"


def test_audio_output_action_empty_handled() -> None:
    """Action does nothing when outputs list is empty."""
    player = FakeMpvPlayer()
    current = [0]
    action = create_audio_output_action(player, [], current)

    action()
    assert current[0] == 0
    assert player.last_device is None
