"""Audio device detection for MLOOP."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger("mloop.audio.devices")

AUDIO_OUTPUTS = {
    "auto": "auto",
    "hdmi": "alsa/hdmi",
    "system-default": "auto",
}


@dataclass
class AudioDevice:
    """Audio device information."""

    name: str
    device_id: str
    description: str


def list_audio_devices() -> list[AudioDevice]:
    """List available audio devices.

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


def get_audio_device_id(output: str) -> str:
    """Get the device ID for an audio output name.

    Args:
        output: Audio output name.

    Returns:
        Device ID string.
    """
    return AUDIO_OUTPUTS.get(output, "auto")
