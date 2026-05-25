"""Audio device detection for MLOOP."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger("mloop.audio.devices")


@dataclass
class AudioDevice:
    """Audio device information."""

    name: str
    device_id: str
    description: str


def list_audio_devices() -> list[AudioDevice]:
    """List available audio devices via ALSA (fallback).

    Returns:
        List of available audio devices.
    """
    devices: list[AudioDevice] = []

    try:
        result = subprocess.run(
            ["aplay", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith("card"):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        card_info = parts[0].split()
                        if len(card_info) >= 2:
                            card_num = card_info[1].rstrip(",")
                            description = parts[1].strip()
                            devices.append(
                                AudioDevice(
                                    name=f"card {card_num}",
                                    device_id=f"hw:{card_num}",
                                    description=description,
                                )
                            )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning("Could not list audio devices: %s", e)

    return devices


_HDMI_KEYWORDS = {"hdmi", "displayport", "digital", "/dp", "/dp:"}
_ANALOG_KEYWORDS = {"analog", "headphone", "headset", "jack", "speaker", "line-out", "lineout"}


def _matches_keywords(text: str, keywords: set[str]) -> bool:
    """Check whether *text* contains any of the given keywords (case-insensitive)."""
    lower = text.lower()
    return any(kw in lower for kw in keywords)


def resolve_audio_outputs(
    devices: list[dict[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """Resolve audio output options from mpv ``audio-device-list``.

    Each returned tuple is ``(friendly_label, mpv_device_name)``.
    The friendly label is shown in the menu; the device name is the value
    passed to mpv's ``audio-device`` property.

    Mapping rules:
    - The special ``auto`` device is always labelled ``Auto`` and placed first.
    - Devices whose description (or name) contains ``hdmi`` or similar digital
      keywords are mapped to ``HDMI``.
    - Devices matching ``analog`` / ``headphone`` / ``jack`` are mapped to
      ``Analog``.
    - Devices that don't match any known category are skipped.

    If *devices* is ``None`` or empty, returns ``[("Auto", "auto")]``.

    Args:
        devices: Device-list payload from mpv (list of dicts with ``name``
                 and ``description``).  May be ``None``.

    Returns:
        Ordered list of ``(label, device_id)`` tuples.
    """
    outputs: list[tuple[str, str]] = []

    if not devices:
        return [("Auto", "auto")]

    for device in devices:
        name = device.get("name", "")
        desc = device.get("description", "") or ""

        if name == "auto":
            continue

        if _matches_keywords(desc, _HDMI_KEYWORDS) or _matches_keywords(
            name, _HDMI_KEYWORDS
        ):
            outputs.append(("HDMI", name))
        elif _matches_keywords(desc, _ANALOG_KEYWORDS) or _matches_keywords(
            name, _ANALOG_KEYWORDS
        ):
            outputs.append(("Analog", name))

    result: list[tuple[str, str]] = [("Auto", "auto")]
    result.extend(outputs)
    return result
