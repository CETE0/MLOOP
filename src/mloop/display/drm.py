"""DRM connector discovery and management for MLOOP."""

from __future__ import annotations

import glob
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("mloop.display.drm")

DRM_BASE = Path("/sys/class/drm")


@dataclass
class DrmConnector:
    """DRM connector information."""

    name: str
    sysfs_path: Path
    status: str

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self.status == "connected"

    @property
    def has_edid(self) -> bool:
        """Check if EDID is available."""
        edid_path = self.sysfs_path / "edid"
        try:
            return edid_path.exists() and edid_path.stat().st_size > 0
        except OSError:
            return False

    def read_status(self) -> str:
        """Read current connector status from sysfs.

        Returns:
            Current status: 'connected', 'disconnected', or 'unknown'.
        """
        status_path = self.sysfs_path / "status"
        try:
            return status_path.read_text().strip()
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", status_path, e)
            return "unknown"

    def read_modes(self) -> list[str]:
        """Read available display modes.

        Returns:
            List of mode strings.
        """
        modes_path = self.sysfs_path / "modes"
        try:
            content = modes_path.read_text().strip()
            if content:
                return content.split("\n")
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", modes_path, e)
        return []


def discover_connectors(
    connector_override: str | None = None,
    sysfs_root: Path | None = None,
) -> list[DrmConnector]:
    """Discover DRM HDMI connectors.

    Args:
        connector_override: Specific connector name to use.
        sysfs_root: Alternative sysfs root for testing.

    Returns:
        List of discovered HDMI connectors.
    """
    base = sysfs_root or DRM_BASE
    connectors: list[DrmConnector] = []

    pattern = str(base / "card*-HDMI-A-*")
    paths = sorted(glob.glob(pattern))

    for path_str in paths:
        path = Path(path_str)
        name = path.name
        status = "unknown" if sysfs_root else path.joinpath("status").read_text().strip()
        connector = DrmConnector(
            name=name,
            sysfs_path=path,
            status=status,
        )
        connectors.append(connector)
        logger.info(
            "Found connector: %s status=%s edid=%s",
            connector.name,
            connector.status,
            connector.has_edid,
        )

    if connector_override and connector_override != "auto":
        filtered = [c for c in connectors if c.name == connector_override]
        if filtered:
            logger.info("Using connector override: %s", connector_override)
            return filtered
        logger.warning("Connector override %s not found, using all", connector_override)

    return connectors


def get_kmsprint_connectors() -> list[str]:
    """Get connector information from kmsprint.

    Returns:
        List of connector lines from kmsprint.
    """
    try:
        result = subprocess.run(
            ["kmsprint", "--grep", "Connector"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip().split("\n")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return []
