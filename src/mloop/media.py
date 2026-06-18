"""Media scanning and playlist generation for MLOOP."""

from __future__ import annotations

import random
from pathlib import Path

from mloop.config import SUPPORTED_EXTENSIONS


def scan_media_dirs(directories: list[str]) -> list[Path]:
    """Scan directories for media files.

    Args:
        directories: List of directory paths to scan.

    Returns:
        Sorted list of media file paths.
    """
    files: list[Path] = []

    for directory in directories:
        path = Path(directory)
        if not path.is_dir():
            continue

        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(file_path)

    files.sort(key=lambda p: p.name.lower())
    return files


def build_playlist(
    files: list[Path],
    shuffle: bool = False,
) -> list[Path]:
    """Build a playlist from media files.

    Args:
        files: List of media file paths.
        shuffle: Whether to shuffle the playlist.

    Returns:
        Playlist as a list of file paths.
    """
    if not files:
        return []

    playlist = list(files)

    if shuffle:
        random.shuffle(playlist)

    return playlist


def is_media_file(path: Path) -> bool:
    """Check if a file is a supported media file.

    Args:
        path: File path to check.

    Returns:
        True if the file has a supported extension.
    """
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def get_media_type(path: Path) -> str:
    """Get the media type for a file.

    Args:
        path: File path.

    Returns:
        One of 'video', 'audio', 'image', or 'unknown'.
    """
    suffix = path.suffix.lower()
    video_extensions = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
    audio_extensions = {".mp3", ".wav", ".flac"}
    image_extensions = {".jpg", ".jpeg", ".png"}

    if suffix in video_extensions:
        return "video"
    if suffix in audio_extensions:
        return "audio"
    if suffix in image_extensions:
        return "image"
    return "unknown"
