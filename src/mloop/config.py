"""Configuration loading and management for MLOOP."""

from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

DEFAULT_CONFIG_PATH = Path("/etc/mloop/config.toml")
DEFAULT_STATE_PATH = Path("/var/lib/mloop/state.toml")
DEFAULT_IPC_SOCKET = Path("/run/mloop/mpv.sock")

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".mp4",
        ".mov",
        ".mkv",
        ".webm",
        ".m4v",
        ".mp3",
        ".wav",
        ".flac",
        ".jpg",
        ".jpeg",
        ".png",
    }
)

T = TypeVar("T")


@dataclass
class PlaybackConfig:
    """Playback configuration."""

    media_dirs: list[str] = field(default_factory=lambda: ["/home/mloop/media"])
    shuffle: bool = False
    loop: bool = True
    volume: int = 80
    image_duration_seconds: int = 10


@dataclass
class PlayerConfig:
    """Player configuration."""

    backend: str = "mpv"
    mpv_path: str = "/usr/bin/mpv"
    cvlc_path: str = "/usr/bin/cvlc"
    ipc_socket: str = str(DEFAULT_IPC_SOCKET)


@dataclass
class DisplayConfig:
    """Display configuration."""

    connector: str = "auto"
    rotation: int = 0
    mode: str = "auto"


@dataclass
class AudioConfig:
    """Audio configuration."""

    output: str = "auto"


@dataclass
class HdmiGesturesConfig:
    """HDMI gestures configuration."""

    enabled: bool = True
    enter_min_disconnect_ms: int = 800
    enter_max_disconnect_ms: int = 8000
    cycle_min_disconnect_ms: int = 300
    cycle_max_disconnect_ms: int = 5000
    debounce_ms: int = 500
    select_after_connected_ms: int = 5000
    menu_timeout_ms: int = 30000


@dataclass
class MenuConfig:
    """Menu configuration."""

    osd_duration_ms: int = 5000
    confirm_dangerous_actions: bool = True


@dataclass
class WebConfig:
    """Web interface configuration."""

    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass
class Config:
    """Main configuration container."""

    playback: PlaybackConfig = field(default_factory=PlaybackConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    hdmi_gestures: HdmiGesturesConfig = field(default_factory=HdmiGesturesConfig)
    menu: MenuConfig = field(default_factory=MenuConfig)
    web: WebConfig = field(default_factory=WebConfig)


def _parse_section(data: dict[str, Any], cls: type[T]) -> T:
    """Parse a configuration section from TOML data."""
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")

    defaults_dict: dict[str, Any] = {}
    for f in fields(cls):
        if f.default_factory is not dataclasses.MISSING:
            defaults_dict[f.name] = f.default_factory()
        elif f.default is not dataclasses.MISSING:
            defaults_dict[f.name] = f.default
    merged = {**defaults_dict, **{k: v for k, v in data.items() if k in defaults_dict}}
    return cls(**merged)


def load_config(path: Path | None = None) -> Config:
    """Load configuration from a TOML file.

    Args:
        path: Path to configuration file. Uses default if not provided.

    Returns:
        Config object with merged defaults and file values.
    """
    config_path = path or DEFAULT_CONFIG_PATH

    data: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

    playback = _parse_section(data.get("playback", {}), PlaybackConfig)
    player = _parse_section(data.get("player", {}), PlayerConfig)
    display = _parse_section(data.get("display", {}), DisplayConfig)
    audio = _parse_section(data.get("audio", {}), AudioConfig)
    hdmi_gestures = _parse_section(data.get("hdmi_gestures", {}), HdmiGesturesConfig)
    menu = _parse_section(data.get("menu", {}), MenuConfig)
    web = _parse_section(data.get("web", {}), WebConfig)

    return Config(
        playback=playback,
        player=player,
        display=display,
        audio=audio,
        hdmi_gestures=hdmi_gestures,
        menu=menu,
        web=web,
    )


def load_state(path: Path | None = None) -> dict[str, Any]:
    """Load runtime state from TOML file.

    Args:
        path: Path to state file. Uses default if not provided.

    Returns:
        Dictionary of state values.
    """
    state_path = path or DEFAULT_STATE_PATH
    if state_path.exists():
        with open(state_path, "rb") as f:
            return tomllib.load(f)
    return {}


def save_state(state: dict[str, Any], path: Path | None = None) -> None:
    """Save runtime state to TOML file.

    Args:
        state: State dictionary to save.
        path: Path to state file. Uses default if not provided.
    """
    state_path = path or DEFAULT_STATE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for key, value in state.items():
        if isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, int):
            lines.append(f"{key} = {value}")
        elif isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        else:
            lines.append(f"{key} = {value!r}")

    with open(state_path, "w") as f:
        f.write("\n".join(lines) + "\n")
