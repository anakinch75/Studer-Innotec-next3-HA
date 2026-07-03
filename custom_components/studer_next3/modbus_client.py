"""Minimal async Modbus TCP client — no external dependencies."""
from __future__ import annotations

import asyncio
import logging
import struct

_LOGGER = logging.getLogger(__name__)

_MODBUS_PROTOCOL_ID = 0x0000
_FC_READ_HOLDING = 0x03
_FC_WRITE_MULTIPLE = 0x10


class ModbusTcpError(Exception):
    """Raised when the device returns a Modbus exception response."""


class ModbusTcpClient:
    """Bare-bones async Modbus TCP client using raw asyncio sockets."""

    def __init__(self, host: str, port: int, timeout: float = 10.0) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._transaction_id = 0

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> bool:
        """Open the TCP connection. Returns True on success."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._timeout,
            )
            return True
        except Exception as err:
            _LOGGER.debug("Modbus connect failed: %s", err)
            self._reader = None
            self._writer = None
            return False

    def close(self) -> None:
        """Close the TCP connection."""
        if self._writer:
            try:
                self._writer.close()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    async def read_holding_registers(
        self, address: int, count: int, slave: int
    ) -> list[int]:
        """Read `count` holding registers starting at `address` from `slave`.

        Returns a list of register values (uint16).
        Raises ModbusTcpError on Modbus exception response.
        Raises OSError / asyncio.TimeoutError on network errors.
        """
        if not self.connected:
            raise OSError("Not connected")

        self._transaction_id = (self._transaction_id + 1) & 0xFFFF

        # PDU: Function code + starting address + quantity
        pdu = struct.pack(">BHH", _FC_READ_HOLDING, address, count)

        # MBAP header: transaction ID, protocol ID, length (unit + PDU), unit ID
        mbap = struct.pack(
            ">HHHB",
            self._transaction_id,
            _MODBUS_PROTOCOL_ID,
            len(pdu) + 1,  # +1 for unit ID byte
            slave,
        )

        try:
            if self._writer is None or self._reader is None:
                raise OSError("Not connected")

            self._writer.write(mbap + pdu)
            await self._writer.drain()

            # Response MBAP: 6 bytes
            resp_mbap = await asyncio.wait_for(
                self._reader.readexactly(6), timeout=self._timeout
            )
            _, _, resp_length = struct.unpack(">HHH", resp_mbap)

            # Response body: unit_id (1) + func_code (1) + payload
            resp_body = await asyncio.wait_for(
                self._reader.readexactly(resp_length), timeout=self._timeout
            )

            func_code = resp_body[1]

            if func_code & 0x80:
                exception_code = resp_body[2] if len(resp_body) > 2 else 0
                raise ModbusTcpError(
                    f"Modbus exception FC={func_code:#x} code={exception_code}"
                )

            byte_count = resp_body[2]
            registers: list[int] = []
            for i in range(byte_count // 2):
                (val,) = struct.unpack_from(">H", resp_body, 3 + i * 2)
                registers.append(val)

            return registers

        except (ModbusTcpError, asyncio.TimeoutError, OSError):
            raise
        except Exception as err:
            self.close()
            raise OSError(f"Unexpected Modbus TCP error: {err}") from err

    async def write_holding_registers(
        self, address: int, values: list[int], slave: int
    ) -> None:
        """Write `values` (list of uint16) to holding registers starting at `address` on `slave`.

        Uses FC16 (Write Multiple Registers).
        Raises ModbusTcpError on Modbus exception response.
        Raises OSError / asyncio.TimeoutError on network errors.
        """
        if not self.connected:
            raise OSError("Not connected")

        self._transaction_id = (self._transaction_id + 1) & 0xFFFF

        byte_count = len(values) * 2
        # PDU: FC + starting address + quantity + byte count + register data
        pdu = struct.pack(">BHHB", _FC_WRITE_MULTIPLE, address, len(values), byte_count)
        pdu += struct.pack(f">{len(values)}H", *values)

        mbap = struct.pack(
            ">HHHB",
            self._transaction_id,
            _MODBUS_PROTOCOL_ID,
            len(pdu) + 1,
            slave,
        )

        try:
            if self._writer is None or self._reader is None:
                raise OSError("Not connected")

            self._writer.write(mbap + pdu)
            await self._writer.drain()

            resp_mbap = await asyncio.wait_for(
                self._reader.readexactly(6), timeout=self._timeout
            )
            _, _, resp_length = struct.unpack(">HHH", resp_mbap)

            resp_body = await asyncio.wait_for(
                self._reader.readexactly(resp_length), timeout=self._timeout
            )

            if len(resp_body) < 2:
                raise ModbusTcpError(f"Truncated FC16 response: {len(resp_body)} bytes")
            func_code = resp_body[1]
            if func_code & 0x80:
                exception_code = resp_body[2] if len(resp_body) > 2 else 0
                raise ModbusTcpError(
                    f"Modbus exception FC={func_code:#x} code={exception_code}"
                )

        except (ModbusTcpError, asyncio.TimeoutError, OSError):
            raise
        except Exception as err:
            self.close()
            raise OSError(f"Unexpected Modbus TCP error: {err}") from err
