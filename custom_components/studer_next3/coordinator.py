"""DataUpdateCoordinator for Studer Next3 via Modbus TCP."""
from __future__ import annotations

import asyncio
import logging
import struct
from datetime import timedelta
from typing import Any

import pymodbus
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, REGISTER_DEFINITIONS, ModbusRegisterDef

_LOGGER = logging.getLogger(__name__)
_CONNECT_TIMEOUT = 10  # seconds

_LOGGER.warning("studer_next3: pymodbus version = %s", pymodbus.__version__)

# Cached kwarg name for slave ID ("slave", "unit", or "" = not supported)
_SLAVE_KWARG: str | None = None  # None = not yet detected


def _decode_float32(registers: list[int]) -> float:
    """Decode two 16-bit Modbus registers into an IEEE 754 float32."""
    raw = struct.pack(">HH", registers[0], registers[1])
    return struct.unpack(">f", raw)[0]


def _decode_float64(registers: list[int]) -> float:
    """Decode four 16-bit Modbus registers into an IEEE 754 float64."""
    raw = struct.pack(">HHHH", registers[0], registers[1], registers[2], registers[3])
    return struct.unpack(">d", raw)[0]


async def _compat_read_holding_registers(
    client: AsyncModbusTcpClient, address: int, count: int, slave: int
):
    """Call read_holding_registers with automatic pymodbus version detection.

    Tries slave= (3.x), unit= (2.x), then no slave kwarg in order.
    Caches the first working variant for subsequent calls.
    """
    global _SLAVE_KWARG

    candidates = [
        ("slave", {"count": count, "slave": slave}),
        ("unit",  {"count": count, "unit": slave}),
        ("",      {"count": count}),
    ]

    if _SLAVE_KWARG is not None:
        # Use cached variant
        kwargs = {"count": count}
        if _SLAVE_KWARG:
            kwargs[_SLAVE_KWARG] = slave
        return await client.read_holding_registers(address, **kwargs)

    # Discovery: find which variant works
    for key, kwargs in candidates:
        try:
            result = await client.read_holding_registers(address, **kwargs)
            _SLAVE_KWARG = key
            if key:
                _LOGGER.warning("studer_next3: slave kwarg = '%s'", key)
            else:
                _LOGGER.warning(
                    "studer_next3: no slave kwarg supported — slave ID cannot be set. "
                    "Registers on non-default slaves (e.g. slave 7) may return wrong data."
                )
            return result
        except TypeError:
            continue

    raise ModbusException("Incompatible pymodbus API — no working signature found")


class StuderNext3Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls all Modbus registers and exposes the data dict."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        scan_interval: int,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._host = host
        self._port = port
        self._client: AsyncModbusTcpClient | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> AsyncModbusTcpClient:
        """Return a connected Modbus client, creating one if needed."""
        if self._client is None or not self._client.connected:
            try:
                self._client = AsyncModbusTcpClient(self._host, port=self._port)
                await asyncio.wait_for(self._client.connect(), timeout=_CONNECT_TIMEOUT)
            except (OSError, TimeoutError, asyncio.TimeoutError) as err:
                self._client = None
                raise UpdateFailed(
                    f"Cannot connect to Studer Next3 at {self._host}:{self._port}: {err}"
                ) from err
            if not self._client.connected:
                self._client = None
                raise UpdateFailed(
                    f"Cannot connect to Studer Next3 at {self._host}:{self._port}"
                )
        return self._client

    async def _read_n_registers(
        self, client: AsyncModbusTcpClient, address: int, count: int, slave: int, key: str
    ) -> list[int] | None:
        """Read `count` holding registers. Returns list or None on any error."""
        try:
            result = await _compat_read_holding_registers(client, address, count, slave)
        except ModbusException as err:
            _LOGGER.warning("Modbus error reading %s (addr=%s count=%s): %s", key, address, count, err)
            return None
        if result.isError():
            _LOGGER.warning("Error response for %s (slave=%s addr=%s count=%s): %s", key, slave, address, count, result)
            return None
        regs = list(result.registers)
        if len(regs) < count:
            _LOGGER.warning("Short read for %s: expected %d, got %d", key, count, len(regs))
            return None
        return regs

    async def _read_register(
        self, client: AsyncModbusTcpClient, reg: ModbusRegisterDef
    ) -> float | None:
        """Read a single register definition and return its decoded value."""
        if reg.data_type == "float32":
            regs = await self._read_n_registers(client, reg.address, 2, reg.slave, reg.key)
            if regs is None:
                return None
            return _decode_float32(regs)

        # float64: try single 4-register read first
        regs = await self._read_n_registers(client, reg.address, 4, reg.slave, reg.key)
        if regs is not None:
            return _decode_float64(regs)

        # Fallback: two consecutive 2-register reads
        _LOGGER.warning("float64 single-read failed for %s — trying split read", reg.key)
        regs1 = await self._read_n_registers(client, reg.address, 2, reg.slave, reg.key)
        regs2 = await self._read_n_registers(client, reg.address + 2, 2, reg.slave, reg.key)
        if regs1 is None or regs2 is None:
            return None
        return _decode_float64(regs1 + regs2)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Studer Next3 — called by HA on each interval."""
        async with self._lock:
            try:
                client = await self._get_client()
            except UpdateFailed:
                raise
            except Exception as err:
                raise UpdateFailed(f"Connection error: {err}") from err

            data: dict[str, Any] = {}
            for reg in REGISTER_DEFINITIONS:
                value = await self._read_register(client, reg)
                data[reg.key] = value

            raw = data.get("battery_power_raw")
            data["battery_power"] = (-raw) if raw is not None else None

            return data

    async def async_shutdown(self) -> None:
        """Close the Modbus connection on unload."""
        if self._client and self._client.connected:
            self._client.close()
        self._client = None
