"""Menu actions for MLOOP."""

from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Awaitable, Callable

from mloop.player.backend import PlayerBackend
from mloop.state import RuntimeState

logger = logging.getLogger("mloop.menu.actions")

Action = Callable[[], None]
SpawnFunc = Callable[[Awaitable[object], str], None]
SaveStateFunc = Callable[[], None]


def create_resume_action() -> Action:
    def action() -> None:
        logger.info("Resuming playback")

    return action


def create_volume_action(
    player: PlayerBackend,
    state: RuntimeState,
    spawn: SpawnFunc,
    save_state: SaveStateFunc,
) -> Action:
    def action() -> None:
        state.volume += 10
        if state.volume > 100:
            state.volume = 10

        save_state()
        spawn(player.set_volume(state.volume), "set-volume")
        logger.info("Volume changed to %d", state.volume)

    return action


def create_audio_output_action(
    player: PlayerBackend,
    outputs: list[str],
    state: RuntimeState,
    spawn: SpawnFunc,
    save_state: SaveStateFunc,
) -> Action:
    def action() -> None:
        try:
            current_index = outputs.index(state.audio_output)
        except ValueError:
            current_index = 0
        state.audio_output = outputs[(current_index + 1) % len(outputs)]

        save_state()
        spawn(player.set_audio_output(state.audio_output), "set-audio-output")
        logger.info("Audio output changed to %s", state.audio_output)

    return action


def create_rotation_action(
    player: PlayerBackend,
    state: RuntimeState,
    spawn: SpawnFunc,
    save_state: SaveStateFunc,
) -> Action:
    def action() -> None:
        state.rotation = next_rotation(state.rotation)

        save_state()
        spawn(player.set_rotation(state.rotation), "set-rotation")
        logger.info("Rotation changed to %d", state.rotation)

    return action


def next_rotation(current: int) -> int:
    rotations = [0, 90, 180, 270]
    try:
        current_index = rotations.index(current)
    except ValueError:
        current_index = 0
    return rotations[(current_index + 1) % len(rotations)]


def create_rescan_action(
    media_scanner: Callable[[], Awaitable[object]], spawn: SpawnFunc
) -> Action:
    def action() -> None:
        logger.info("Rescanning media")
        spawn(media_scanner(), "rescan-media")

    return action


def create_network_info_action(
    player: PlayerBackend,
    osd_duration_ms: int,
    spawn: SpawnFunc,
) -> Action:
    async def run() -> None:
        info = await get_network_info_async()
        logger.info("Network info: %s", info)
        await player.show_osd(info, osd_duration_ms)

    def action() -> None:
        spawn(run(), "network-info")

    return action


async def get_network_info_async() -> str:
    lines = ["=== Network Info ===", ""]
    lines.append(f"Hostname: {socket.gethostname()}")

    try:
        proc = await asyncio.create_subprocess_exec(
            "ip",
            "-4",
            "addr",
            "show",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
    except (OSError, TimeoutError) as exc:
        logger.debug("Could not get network info: %s", exc)
        return "\n".join(lines)

    if proc.returncode == 0:
        for line in stdout.decode().splitlines():
            if "inet " in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    lines.append(f"IP: {parts[1]}")

    return "\n".join(lines)


async def run_system_command(*args: str) -> None:
    proc = await asyncio.create_subprocess_exec(*args)
    await proc.wait()


def create_reboot_action(spawn: SpawnFunc) -> Action:
    def action() -> None:
        logger.info("Rebooting system")
        spawn(run_system_command("sudo", "reboot"), "reboot")

    return action


def create_shutdown_action(spawn: SpawnFunc) -> Action:
    def action() -> None:
        logger.info("Shutting down system")
        spawn(run_system_command("sudo", "shutdown", "now"), "shutdown")

    return action
