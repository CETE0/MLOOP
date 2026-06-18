"""Platform detection for MLOOP."""

from __future__ import annotations

import logging
import platform
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("mloop.system.platform")


@dataclass
class PlatformInfo:
    """Platform information."""

    machine: str
    system: str
    release: str
    node: str
    python_version: str
    device_model: str | None = None

    @property
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        return self.device_model is not None and "Raspberry Pi" in self.device_model


def _read_pi_model() -> str | None:
    model_path = Path("/proc/device-tree/model")
    try:
        return model_path.read_text(errors="ignore").strip("\x00\n")
    except OSError:
        return None


def get_platform_info() -> PlatformInfo:
    """Get platform information.

    Returns:
        PlatformInfo instance.
    """
    info = PlatformInfo(
        machine=platform.machine(),
        system=platform.system(),
        release=platform.release(),
        node=platform.node(),
        python_version=platform.python_version(),
        device_model=_read_pi_model(),
    )

    logger.info(
        "Platform: %s %s %s Python %s",
        info.system,
        info.machine,
        info.release,
        info.python_version,
    )

    if info.is_raspberry_pi:
        logger.info("Running on Raspberry Pi")
    else:
        logger.warning("Not running on Raspberry Pi, some features may not work")

    return info
