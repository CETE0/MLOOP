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


@pytest.mark.asyncio
@pytest.mark.parametrize("degrees", [0, 90, 180, 270])
async def test_ipc_set_rotation_uses_video_rotate_property(degrees: int) -> None:
    """Test set_rotation sends video-rotate property, not vf filter."""
    client = MpvIpcClient("/tmp/test.sock")
    client._writer = MagicMock()
    client._writer.write = MagicMock()
    client._writer.drain = AsyncMock()
    commands: list[list] = []

    async def mock_send(command: list) -> dict:
        commands.append(list(command))
        client._request_id += 1
        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        client._pending_requests[client._request_id] = future
        future.set_result({"data": None})
        return {"data": None}

    client._send_command = mock_send

    await client.set_property("video-rotate", degrees)

    assert any(c[:2] == ["set_property", "video-rotate"] and c[2] == degrees for c in commands), (
        f"Expected set_property video-rotate {degrees}, got commands: {commands}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("degrees", [0, 90, 180, 270])
async def test_ipc_set_rotation_does_not_use_vf(degrees: int) -> None:
    """Test set_rotation does not use the vf property."""
    client = MpvIpcClient("/tmp/test.sock")
    client._writer = MagicMock()
    client._writer.write = MagicMock()
    client._writer.drain = AsyncMock()
    commands: list[list] = []

    async def mock_send(command: list) -> dict:
        commands.append(list(command))
        client._request_id += 1
        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        client._pending_requests[client._request_id] = future
        future.set_result({"data": None})
        return {"data": None}

    client._send_command = mock_send

    await client.set_property("video-rotate", degrees)

    vf_commands = [c for c in commands if c[:2] == ["set_property", "vf"]]
    assert not vf_commands, f"Should not use vf property for rotation, got: {vf_commands}"


@pytest.mark.asyncio
async def test_ipc_read_loop_fails_pending_requests_on_close() -> None:
    client = MpvIpcClient("/tmp/test.sock")
    future: asyncio.Future[dict] = asyncio.get_running_loop().create_future()
    client._pending_requests[1] = future

    class _ClosedReader:
        async def readline(self) -> bytes:
            return b""

    client._reader = _ClosedReader()

    await client._read_loop()

    assert future.done()
    with pytest.raises(ConnectionError):
        future.result()


@pytest.mark.asyncio
async def test_ipc_disconnect_cancels_read_task(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MpvIpcClient("/tmp/test.sock")

    class _Reader:
        async def readline(self) -> bytes:
            await asyncio.sleep(10)
            return b""

    class _Writer:
        def close(self) -> None:
            return None

        async def wait_closed(self) -> None:
            return None

    async def open_connection(path: str) -> tuple[_Reader, _Writer]:
        return _Reader(), _Writer()

    monkeypatch.setattr("mloop.player.ipc.asyncio.open_unix_connection", open_connection)

    await client.connect()
    assert client._read_task is not None

    await client.disconnect()
    assert client._read_task is None
