"""DataUpdateCoordinator for Studer Next3 via Modbus TCP."""
from __future__ import annotations

import asyncio
import logging
import struct
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, REGISTER_DEFINITIONS, ModbusRegisterDef
from .modbus_client import ModbusTcpClient, ModbusTcpError

_LOGGER = logging.getLogger(__name__)
_CONNECT_TIMEOUT = 10


def _decode_float32(registers: list[int]) -> float:
    raw = struct.pack(">HH", registers[0], registers[1])
    return struct.unpack(">f", raw)[0]


def _decode_float64(registers: list[int]) -> float:
    raw = struct.pack(">HHHH", registers[0], registers[1], registers[2], registers[3])
    return struct.unpack(">d", raw)[0]


class StuderNext3Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls all Modbus registers and exposes the data dict."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._host = host
        self._port = port
        self._client: ModbusTcpClient | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> ModbusTcpClient:
        """Return a connected client, reconnecting if needed."""
        if self._client is None or not self._client.connected:
            self._client = ModbusTcpClient(self._host, self._port, timeout=_CONNECT_TIMEOUT)
            ok = await asyncio.wait_for(self._client.connect(), timeout=_CONNECT_TIMEOUT)
            if not ok:
                self._client = None
                raise UpdateFailed(
                    f"Cannot connect to Studer Next3 at {self._host}:{self._port}"
                )
        return self._client

    async def _read_n(
        self, client: ModbusTcpClient, address: int, count: int, slave: int, key: str
    ) -> list[int] | None:
        """Read `count` holding registers. Returns list or None on error."""
        try:
            regs = await client.read_holding_registers(address, count, slave)
        except ModbusTcpError as err:
            _LOGGER.warning(
                "Modbus exception reading %s (addr=%s count=%s slave=%s): %s",
                key, address, count, slave, err,
            )
            return None
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Network error reading %s: %s", key, err)
            self._client = None
            return None
        if len(regs) < count:
            _LOGGER.warning(
                "Short read for %s (addr=%s count=%s): got %d", key, address, count, len(regs)
            )
            return None
        _LOGGER.debug("Read %s addr=%s slave=%s: %s", key, address, slave, regs)
        return regs

    async def _read_register(
        self, client: ModbusTcpClient, reg: ModbusRegisterDef
    ) -> float | None:
        """Read one register definition. Returns decoded float or None on error."""
        count = 2 if reg.data_type == "float32" else 4
        regs = await self._read_n(client, reg.address, count, reg.slave, reg.key)
        if regs is None:
            return None
        if reg.data_type == "float32":
            return _decode_float32(regs)
        return _decode_float64(regs)

    async def _async_update_data(self) -> dict[str, Any]:
        async with self._lock:
            try:
                client = await self._get_client()
            except UpdateFailed:
                raise
            except Exception as err:
                raise UpdateFailed(f"Connection error: {err}") from err

            data: dict[str, Any] = {}
            for reg in REGISTER_DEFINITIONS:
                data[reg.key] = await self._read_register(client, reg)

            raw = data.get("battery_power_raw")
            data["battery_power"] = (-raw) if raw is not None else None

            return data

    async def async_shutdown(self) -> None:
        if self._client:
            self._client.close()
        self._client = None
