"""Tests for the native asyncio Modbus TCP client."""
import struct
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.studer_next3.modbus_client import ModbusTcpClient, ModbusTcpError


def _response(tx_id: int, unit: int, registers: list[int]) -> tuple[bytes, bytes]:
    """Build (mbap, body) for a valid FC03 response."""
    byte_count = len(registers) * 2
    body = bytes([unit, 0x03, byte_count]) + b"".join(
        struct.pack(">H", r) for r in registers
    )
    mbap = struct.pack(">HHH", tx_id, 0x0000, len(body))
    return mbap, body


def _error_response(tx_id: int, unit: int, exc_code: int) -> tuple[bytes, bytes]:
    """Build (mbap, body) for a Modbus exception response."""
    body = bytes([unit, 0x83, exc_code])
    mbap = struct.pack(">HHH", tx_id, 0x0000, len(body))
    return mbap, body


@pytest.fixture
def client_with_mock_socket():
    """ModbusTcpClient with mock reader/writer already connected."""
    client = ModbusTcpClient("192.168.1.1", 502, timeout=1.0)
    writer = MagicMock()
    writer.is_closing.return_value = False
    writer.drain = AsyncMock()
    client._writer = writer
    client._reader = AsyncMock()
    client._transaction_id = 0
    return client


async def test_connect_success():
    with patch("asyncio.open_connection") as mock_open:
        reader, writer = AsyncMock(), MagicMock()
        writer.is_closing.return_value = False
        mock_open.return_value = (reader, writer)

        result = await ModbusTcpClient("192.168.1.1", 502).connect()

    assert result is True


async def test_connect_failure():
    with patch("asyncio.open_connection", side_effect=OSError("refused")):
        result = await ModbusTcpClient("192.168.1.1", 502).connect()

    assert result is False


async def test_read_returns_correct_registers(client_with_mock_socket):
    registers = [0x447A, 0x0000]
    mbap, body = _response(1, 1, registers)
    client_with_mock_socket._reader.readexactly.side_effect = [mbap, body]

    result = await client_with_mock_socket.read_holding_registers(8, 2, 1)

    assert result == registers


async def test_read_float64_four_registers(client_with_mock_socket):
    registers = [0x408F, 0x4000, 0x0000, 0x0000]
    mbap, body = _response(1, 7, registers)
    client_with_mock_socket._reader.readexactly.side_effect = [mbap, body]

    result = await client_with_mock_socket.read_holding_registers(24, 4, 7)

    assert result == registers


async def test_modbus_exception_raises_error(client_with_mock_socket):
    mbap, body = _error_response(1, 1, 3)
    client_with_mock_socket._reader.readexactly.side_effect = [mbap, body]

    with pytest.raises(ModbusTcpError, match="code=3"):
        await client_with_mock_socket.read_holding_registers(8, 2, 1)


async def test_read_not_connected_raises_oserror():
    client = ModbusTcpClient("192.168.1.1", 502)
    with pytest.raises(OSError, match="Not connected"):
        await client.read_holding_registers(8, 2, 1)


async def test_network_error_during_read_raises_oserror(client_with_mock_socket):
    client_with_mock_socket._reader.readexactly.side_effect = OSError("connection reset")

    with pytest.raises(OSError):
        await client_with_mock_socket.read_holding_registers(8, 2, 1)
