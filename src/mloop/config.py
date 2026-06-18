"""Configuration loading and management for MLOOP."""

from __future__ import annotations

import dataclasses
import json
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import TypeVar, cast

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
    debounce_ms: int = 100
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


class ConfigError(ValueError):
    """Invalid MLOOP configuration."""


def _parse_section(data: Mapping[str, object], cls: type[T]) -> T:
    """Parse a configuration section from TOML data."""
    if not is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")

    defaults_dict: dict[str, object] = {}
    for f in fields(cls):
        if f.default_factory is not dataclasses.MISSING:
            defaults_dict[f.name] = f.default_factory()
        elif f.default is not dataclasses.MISSING:
            defaults_dict[f.name] = f.default
    merged = {**defaults_dict, **{k: v for k, v in data.items() if k in defaults_dict}}
    return cls(**merged)


def _get_section(data: Mapping[str, object], name: str) -> Mapping[str, object]:
    value = data.get(name, {})
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    raise ConfigError(f"{name} must be a table")


def _validate_int_range(name: str, value: object, min_value: int, max_value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{name} must be an integer")
    if not min_value <= value <= max_value:
        raise ConfigError(f"{name} must be between {min_value} and {max_value}")
    return value


def _validate_positive_int(name: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"{name} must be an integer")
    if value <= 0:
        raise ConfigError(f"{name} must be greater than 0")
    return value


def _validate_choice(name: str, value: object, choices: set[str]) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{name} must be a string")
    if value not in choices:
        options = ", ".join(sorted(choices))
        raise ConfigError(f"{name} must be one of {options}")
    return value


def _validate_string(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{name} must be a string")
    if not value:
        raise ConfigError(f"{name} must not be empty")
    return value


def _validate_bool(name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{name} must be true or false")
    return value


def _validate_string_list(name: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{name} must be a list of strings")
    if not value:
        raise ConfigError(f"{name} must not be empty")
    return value


def validate_config(config: Config) -> None:
    """Validate configuration values."""
    _validate_string_list("playback.media_dirs", config.playback.media_dirs)
    _validate_bool("playback.shuffle", config.playback.shuffle)
    _validate_bool("playback.loop", config.playback.loop)
    _validate_choice("player.backend", config.player.backend, {"mpv", "cvlc"})
    _validate_string("player.mpv_path", config.player.mpv_path)
    _validate_string("player.cvlc_path", config.player.cvlc_path)
    _validate_string("player.ipc_socket", config.player.ipc_socket)
    _validate_int_range("playback.volume", config.playback.volume, 0, 100)
    _validate_positive_int(
        "playback.image_duration_seconds", config.playback.image_duration_seconds
    )
    _validate_string("display.connector", config.display.connector)
    _validate_string("display.mode", config.display.mode)
    if config.display.mode != "auto":
        raise ConfigError("display.mode runtime mode setting is not implemented")
    _validate_int_range("display.rotation", config.display.rotation, 0, 270)
    if config.display.rotation not in {0, 90, 180, 270}:
        raise ConfigError("display.rotation must be one of 0, 90, 180, 270")
    _validate_choice("audio.output", config.audio.output, {"auto", "hdmi", "system-default"})

    gestures = config.hdmi_gestures
    _validate_bool("hdmi_gestures.enabled", gestures.enabled)
    _validate_positive_int(
        "hdmi_gestures.enter_min_disconnect_ms", gestures.enter_min_disconnect_ms
    )
    _validate_positive_int(
        "hdmi_gestures.enter_max_disconnect_ms", gestures.enter_max_disconnect_ms
    )
    _validate_positive_int(
        "hdmi_gestures.cycle_min_disconnect_ms", gestures.cycle_min_disconnect_ms
    )
    _validate_positive_int(
        "hdmi_gestures.cycle_max_disconnect_ms", gestures.cycle_max_disconnect_ms
    )
    _validate_positive_int("hdmi_gestures.debounce_ms", gestures.debounce_ms)
    _validate_positive_int(
        "hdmi_gestures.select_after_connected_ms", gestures.select_after_connected_ms
    )
    _validate_positive_int("hdmi_gestures.menu_timeout_ms", gestures.menu_timeout_ms)

    if gestures.debounce_ms >= gestures.cycle_min_disconnect_ms:
        raise ConfigError("hdmi_gestures.debounce_ms must be less than cycle_min_disconnect_ms")
    if gestures.cycle_min_disconnect_ms > gestures.cycle_max_disconnect_ms:
        raise ConfigError("cycle_min_disconnect_ms must be <= cycle_max_disconnect_ms")
    if gestures.enter_min_disconnect_ms > gestures.enter_max_disconnect_ms:
        raise ConfigError("enter_min_disconnect_ms must be <= enter_max_disconnect_ms")

    _validate_positive_int("menu.osd_duration_ms", config.menu.osd_duration_ms)
    _validate_bool("menu.confirm_dangerous_actions", config.menu.confirm_dangerous_actions)

    _validate_bool("web.enabled", config.web.enabled)
    _validate_string("web.host", config.web.host)
    _validate_int_range("web.port", config.web.port, 1, 65535)
    if config.web.enabled:
        raise ConfigError("web.enabled is not implemented")


def load_config(path: Path | None = None) -> Config:
    """Load configuration from a TOML file.

    Args:
        path: Path to configuration file. Uses default if not provided.

    Returns:
        Config object with merged defaults and file values.
    """
    config_path = path or DEFAULT_CONFIG_PATH

    data: Mapping[str, object] = {}
    if config_path.exists():
        with open(config_path, "rb") as f:
            data = cast(Mapping[str, object], tomllib.load(f))

    playback = _parse_section(_get_section(data, "playback"), PlaybackConfig)
    player = _parse_section(_get_section(data, "player"), PlayerConfig)
    display = _parse_section(_get_section(data, "display"), DisplayConfig)
    audio = _parse_section(_get_section(data, "audio"), AudioConfig)
    hdmi_gestures = _parse_section(_get_section(data, "hdmi_gestures"), HdmiGesturesConfig)
    menu = _parse_section(_get_section(data, "menu"), MenuConfig)
    web = _parse_section(_get_section(data, "web"), WebConfig)

    config = Config(
        playback=playback,
        player=player,
        display=display,
        audio=audio,
        hdmi_gestures=hdmi_gestures,
        menu=menu,
        web=web,
    )
    validate_config(config)
    return config


def load_state(path: Path | None = None) -> dict[str, object]:
    """Load runtime state from TOML file.

    Args:
        path: Path to state file. Uses default if not provided.

    Returns:
        Dictionary of state values.
    """
    state_path = path or DEFAULT_STATE_PATH
    if state_path.exists():
        with open(state_path, "rb") as f:
            return cast(dict[str, object], tomllib.load(f))
    return {}


def save_state(state: dict[str, object], path: Path | None = None) -> None:
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
            lines.append(f"{key} = {json.dumps(value)}")
        else:
            raise TypeError(f"Unsupported state value for {key}: {type(value).__name__}")

    with open(state_path, "w") as f:
        f.write("\n".join(lines) + "\n")
