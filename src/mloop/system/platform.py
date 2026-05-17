"""Platform detection for MLOOP."""

from __future__ import annotations

import logging
import platform
from dataclasses import dataclass

logger = logging.getLogger("mloop.system.platform")


@dataclass
class PlatformInfo:
    """Platform information."""

    machine: str
    system: str
    release: str
    node: str
    python_version: str

    @property
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        return "aarch64" in self.machine or "arm" in self.machine


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
