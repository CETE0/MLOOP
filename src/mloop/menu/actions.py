"""Menu actions for MLOOP."""

from __future__ import annotations

import asyncio
import logging
import socket
import subprocess
from typing import Any

logger = logging.getLogger("mloop.menu.actions")


def create_resume_action() -> Any:
    """Create an action to resume playback."""

    def action() -> None:
        logger.info("Resuming playback")

    return action


def create_volume_action(player: Any, current_volume: list[int]) -> Any:
    """Create an action to adjust volume.

    Args:
        player: MpvPlayer instance.
        current_volume: Mutable list containing current volume.
    """

    def action() -> None:
        current_volume[0] = (current_volume[0] + 10) % 110
        if current_volume[0] == 0:
            current_volume[0] = 10

        asyncio.create_task(player.set_volume(current_volume[0]))
        logger.info("Volume changed to %d", current_volume[0])

    return action


def create_audio_output_action(
    player: Any, outputs: list[tuple[str, str]], current: list[int]
) -> Any:
    """Create an action to cycle audio outputs.

    Args:
        player: MpvPlayer instance.
        outputs: List of ``(label, device_id)`` tuples resolved from mpv.
        current: Mutable list containing current index.
    """

    def action() -> None:
        if not outputs:
            return

        current[0] = (current[0] + 1) % len(outputs)
        label, device_id = outputs[current[0]]

        asyncio.create_task(player.set_audio_output(device_id))
        logger.info("Audio output changed to %s (%s)", label, device_id)

    return action


def create_rotation_action(player: Any, current_rotation: list[int]) -> Any:
    """Create an action to cycle video rotation.

    Args:
        player: MpvPlayer instance.
        current_rotation: Mutable list containing current rotation.
    """

    def action() -> None:
        rotations = [0, 90, 180, 270]
        idx = rotations.index(current_rotation[0])
        current_rotation[0] = rotations[(idx + 1) % len(rotations)]

        asyncio.create_task(player.set_rotation(current_rotation[0]))
        logger.info("Rotation changed to %d", current_rotation[0])

    return action


def create_rescan_action(media_scanner: Any) -> Any:
    """Create an action to rescan media.

    Args:
        media_scanner: Media scanner callable (sync or async).
    """

    def action() -> None:
        logger.info("Rescanning media")
        if asyncio.iscoroutinefunction(media_scanner):
            asyncio.create_task(media_scanner())
        else:
            media_scanner()

    return action


def create_network_info_action() -> Any:
    """Create an action to show network info."""

    def action() -> None:
        info = get_network_info()
        logger.info("Network info: %s", info)

    return action


def get_network_info() -> str:
    """Get network information.

    Returns:
        String with network information.
    """
    lines = ["=== Network Info ===", ""]

    try:
        hostname = socket.gethostname()
        lines.append(f"Hostname: {hostname}")
    except Exception:
        lines.append("Hostname: unknown")

    try:
        result = subprocess.run(
            ["ip", "-4", "addr", "show"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "inet " in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        lines.append(f"IP: {parts[1]}")
    except Exception:
        pass

    return "\n".join(lines)


def create_reboot_action() -> Any:
    """Create an action to reboot the system."""

    def action() -> None:
        logger.info("Rebooting system")
        subprocess.run(["sudo", "reboot"], check=False)

    return action


def create_shutdown_action() -> Any:
    """Create an action to shutdown the system."""

    def action() -> None:
        logger.info("Shutting down system")
        subprocess.run(["sudo", "shutdown", "now"], check=False)

    return action
