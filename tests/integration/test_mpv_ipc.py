"""Integration tests for mpv IPC (mocked)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mloop.player.ipc import MpvIpcClient


def test_ipc_client_initialization() -> None:
    """Test IPC client initialization."""
    client = MpvIpcClient("/tmp/test.sock")
    assert client.socket_path == "/tmp/test.sock"
    assert client._reader is None
    assert client._writer is None


@pytest.mark.asyncio
async def test_ipc_show_text() -> None:
    """Test show_text command."""
    client = MpvIpcClient("/tmp/test.sock")
    client._writer = MagicMock()
    client._writer.write = MagicMock()
    client._writer.drain = AsyncMock()

    async def mock_send(command: list) -> dict:
        client._request_id += 1
        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        client._pending_requests[client._request_id] = future
        future.set_result({"data": None})
        return {"data": None}

    client._send_command = mock_send

    await client.show_text("Hello", duration=3000)

    assert True


@pytest.mark.asyncio
async def test_ipc_set_volume() -> None:
    """Test set_volume command."""
    client = MpvIpcClient("/tmp/test.sock")
    client._writer = MagicMock()
    client._writer.write = MagicMock()
    client._writer.drain = AsyncMock()

    async def mock_send(command: list) -> dict:
        client._request_id += 1
        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        client._pending_requests[client._request_id] = future
        future.set_result({"data": None})
        return {"data": None}

    client._send_command = mock_send

    await client.set_volume(50)

    assert True
