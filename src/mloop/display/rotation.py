"""Video rotation utilities for MLOOP."""

from __future__ import annotations

VALID_ROTATIONS = (0, 90, 180, 270)


def normalize_rotation(degrees: int) -> int:
    """Normalize rotation to valid values.

    Args:
        degrees: Rotation in degrees.

    Returns:
        Normalized rotation (0, 90, 180, or 270).
    """
    degrees = degrees % 360
    if degrees not in VALID_ROTATIONS:
        return 0
    return degrees


def next_rotation(current: int) -> int:
    """Get the next rotation value in sequence.

    Args:
        current: Current rotation value.

    Returns:
        Next rotation value (0 -> 90 -> 180 -> 270 -> 0).
    """
    rotations = [0, 90, 180, 270]
    current = normalize_rotation(current)
    idx = rotations.index(current)
    return rotations[(idx + 1) % len(rotations)]
