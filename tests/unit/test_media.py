"""Tests for media scanning and playlist generation."""

from pathlib import Path

from mloop.config import SUPPORTED_EXTENSIONS
from mloop.media import build_playlist, get_media_type, is_media_file


def test_supported_extensions() -> None:
    """Test that supported extensions are defined."""
    assert ".mp4" in SUPPORTED_EXTENSIONS
    assert ".mov" in SUPPORTED_EXTENSIONS
    assert ".mkv" in SUPPORTED_EXTENSIONS
    assert ".mp3" in SUPPORTED_EXTENSIONS
    assert ".jpg" in SUPPORTED_EXTENSIONS


def test_is_media_file() -> None:
    """Test media file detection."""
    assert is_media_file(Path("video.mp4")) is True
    assert is_media_file(Path("audio.mp3")) is True
    assert is_media_file(Path("image.jpg")) is True
    assert is_media_file(Path("document.pdf")) is False
    assert is_media_file(Path("script.py")) is False


def test_get_media_type() -> None:
    """Test media type detection."""
    assert get_media_type(Path("video.mp4")) == "video"
    assert get_media_type(Path("audio.mp3")) == "audio"
    assert get_media_type(Path("image.jpg")) == "image"
    assert get_media_type(Path("document.pdf")) == "unknown"


def test_build_playlist_empty() -> None:
    """Test building empty playlist."""
    assert build_playlist([]) == []


def test_build_playlist_no_shuffle() -> None:
    """Test building playlist without shuffle."""
    files = [Path("b.mp4"), Path("a.mp4"), Path("c.mp4")]
    playlist = build_playlist(files, shuffle=False)
    assert playlist == files


def test_build_playlist_does_not_duplicate_for_loop() -> None:
    """Test that looping is handled by player backends."""
    files = [Path("a.mp4"), Path("b.mp4")]
    playlist = build_playlist(files, shuffle=False)
    assert playlist == files


def test_build_playlist_shuffle() -> None:
    """Test building shuffled playlist."""
    files = [Path(f"video{i}.mp4") for i in range(10)]
    playlist = build_playlist(files, shuffle=True)
    assert len(playlist) == len(files)
    assert set(playlist) == set(files)
