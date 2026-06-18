"""Runtime state for MLOOP."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeState:
    volume: int
    rotation: int
    audio_output: str
