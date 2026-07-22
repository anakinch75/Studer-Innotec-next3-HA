"""DataUpdateCoordinator for Studer Next3 via Modbus TCP."""
from __future__ import annotations

import asyncio
import logging
import struct
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DataType,
    MODEL_DEVICE_DEFINITIONS,
    MODEL_NEXT3,
    NUMBER_DEFINITIONS,
    REGISTER_DEFINITIONS,
    ModbusRegisterDef,
    SWITCH_DEFINITIONS,
)
from .modbus_client import ModbusTcpClient, ModbusTcpError

_REGISTER_COUNTS = {DataType.FLOAT32: 2, DataType.FLOAT64: 4, DataType.UINT16: 2}

_LOGGER = logging.getLogger(__name__)
_CONNECT_TIMEOUT = 10


def _decode_float32(registers: list[int]) -> float:
    raw = struct.pack(">HH", registers[0], registers[1])
    return struct.unpack(">f", raw)[0]


def _decode_float64(registers: list[int]) -> float:
    raw = struct.pack(">HHHH", registers[0], registers[1], registers[2], registers[3])
    return struct.unpack(">d", raw)[0]


def _encode_float32(value: float) -> list[int]:
    raw = struct.pack(">f", value)
    r0, r1 = struct.unpack(">HH", raw)
    return [r0, r1]


class StuderNext3Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls all Modbus registers and exposes the data dict."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        scan_interval: int,
        model: str = MODEL_NEXT3,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._host = host
        self._port = port
        self._model = model
        self._client: ModbusTcpClient | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> ModbusTcpClient:
        """Return a connected client, reconnecting if needed."""
        if self._client is None or not self._client.connected:
            self._client = ModbusTcpClient(self._host, self._port, timeout=_CONNECT_TIMEOUT)
            if not await self._client.connect():
                self._client = None
                raise UpdateFailed(
                    f"Cannot connect to Studer Next3 at {self._host}:{self._port}"
                )
        return self._client

    async def _read_register(
        self, client: ModbusTcpClient, reg: ModbusRegisterDef
    ) -> float | None:
        """Read one register definition. Returns decoded float or None on error."""
        count = _REGISTER_COUNTS[reg.data_type]
        try:
            regs = await client.read_holding_registers(reg.address, count, reg.slave)
        except ModbusTcpError as err:
            _LOGGER.warning("Modbus exception reading %s: %s", reg.key, err)
            return None
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Network error reading %s: %s", reg.key, err)
            self._client = None
            return None
        if len(regs) < count:
            _LOGGER.warning("Short read for %s: expected %d got %d", reg.key, count, len(regs))
            return None
        if reg.data_type is DataType.FLOAT32:
            value = _decode_float32(regs)
        elif reg.data_type is DataType.FLOAT64:
            value = _decode_float64(regs)
        else:
            return int(regs[0])
        return value * reg.scale

    async def _read_float32(
        self, client: ModbusTcpClient, address: int, slave: int
    ) -> float | None:
        """Read a single float32 value from address/slave."""
        try:
            regs = await client.read_holding_registers(address, 2, slave)
        except ModbusTcpError as err:
            _LOGGER.warning("Modbus exception reading %d (slave %d): %s", address, slave, err)
            return None
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Network error reading %d (slave %d): %s", address, slave, err)
            self._client = None
            return None
        if len(regs) < 2:
            return None
        return _decode_float32(regs)

    async def _read_bool(
        self, client: ModbusTcpClient, address: int, slave: int
    ) -> bool | None:
        """Read a single bool value."""
        try:
            regs = await client.read_holding_registers(address, 1, slave)
        except ModbusTcpError as err:
            _LOGGER.warning("Modbus exception reading bool %d (slave %d): %s", address, slave, err)
            return None
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Network error reading bool %d (slave %d): %s", address, slave, err)
            self._client = None
            return None
        if len(regs) < 1:
            return None
        return bool(regs[0])

    async def _async_update_data(self) -> dict[str, Any]:
        async with self._lock:
            try:
                client = await self._get_client()
            except UpdateFailed:
                raise
            except Exception as err:
                raise UpdateFailed(f"Connection error: {err}") from err

            data: dict[str, Any] = {}
            all_regs = REGISTER_DEFINITIONS + MODEL_DEVICE_DEFINITIONS[self._model]
            for reg in all_regs:
                data[reg.key] = await self._read_register(client, reg)

            raw = data.get("battery_power_raw")
            data["battery_power"] = (-raw) if raw is not None else None

            for num in NUMBER_DEFINITIONS:
                data[num.key] = await self._read_float32(client, num.address, num.slave)

            for sw in SWITCH_DEFINITIONS:
                data[sw.key] = await self._read_bool(client, sw.address, sw.slave)

            return data

    async def async_write_float32(self, address: int, value: float, slave: int) -> None:
        """Write a float32 value via FC16."""
        async with self._lock:
            client = await self._get_client()
            await client.write_holding_registers(address, _encode_float32(value), slave)

    async def async_write_bool(self, address: int, value: bool, slave: int) -> None:
        """Write a bool value via FC16."""
        async with self._lock:
            client = await self._get_client()
            await client.write_holding_registers(address, [1 if value else 0], slave)

    async def async_shutdown(self) -> None:
        if self._client:
            self._client.close()
        self._client = None
