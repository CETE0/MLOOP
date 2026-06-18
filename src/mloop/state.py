"""Runtime state for MLOOP."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from mloop.config import Config


@dataclass
class RuntimeState:
    volume: int
    rotation: int
    audio_output: str

    @classmethod
    def from_config_and_state(cls, config: Config, data: Mapping[str, object]) -> RuntimeState:
        return cls(
            volume=_int_value(data.get("volume"), config.playback.volume),
            rotation=_rotation_value(data.get("rotation"), config.display.rotation),
            audio_output=_audio_output_value(data.get("audio_output"), config.audio.output),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "volume": self.volume,
            "rotation": self.rotation,
            "audio_output": self.audio_output,
        }


def _int_value(value: object, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100:
        return value
    return default


def _rotation_value(value: object, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value in {0, 90, 180, 270}:
        return value
    return default


def _audio_output_value(value: object, default: str) -> str:
    if isinstance(value, str) and value in {"auto", "hdmi", "system-default"}:
        return value
    return default
