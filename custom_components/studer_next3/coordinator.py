"""DataUpdateCoordinator for Studer Next3 via Modbus TCP."""
from __future__ import annotations

import asyncio
import logging
import struct
from datetime import timedelta
from typing import Any

_CONNECT_TIMEOUT = 10  # seconds

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, REGISTER_DEFINITIONS, ModbusRegisterDef

_LOGGER = logging.getLogger(__name__)


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
    """Call read_holding_registers with pymodbus 2.x/3.x API compatibility.

    Different pymodbus versions use different signatures:
      - 3.x keyword: slave=
      - 2.x keyword: unit=
      - some versions: address only, count/slave via kwargs
    Try each variant until one works.
    """
    for kwargs in (
        {"count": count, "slave": slave},  # pymodbus 3.x
        {"count": count, "unit": slave},   # pymodbus 2.x
        {"count": count},                  # no slave arg
    ):
        try:
            return await client.read_holding_registers(address, **kwargs)
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

    async def _read_two_registers(
        self, client: AsyncModbusTcpClient, address: int, slave: int
    ) -> list[int] | None:
        """Read 2 holding registers and return the register list, or None on error."""
        try:
            result = await _compat_read_holding_registers(client, address, 2, slave)
        except ModbusException as err:
            _LOGGER.warning("Modbus error at address %s: %s", address, err)
            return None
        if result.isError():
            _LOGGER.warning("Error response at address %s", address)
            return None
        if len(result.registers) < 2:
            _LOGGER.warning("Short read at address %s: got %d", address, len(result.registers))
            return None
        return list(result.registers)

    async def _read_register(
        self, client: AsyncModbusTcpClient, reg: ModbusRegisterDef
    ) -> float | None:
        """Read a single register definition and return its decoded value."""
        regs = await self._read_two_registers(client, reg.address, reg.slave)
        if regs is None:
            return None

        if reg.data_type == "float32":
            return _decode_float32(regs)

        # float64: read the second pair of registers (address + 2)
        regs2 = await self._read_two_registers(client, reg.address + 2, reg.slave)
        if regs2 is None:
            return None
        return _decode_float64(regs + regs2)

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

            # Derived sensor: battery power sign is inverted in the raw register
            raw = data.get("battery_power_raw")
            data["battery_power"] = (-raw) if raw is not None else None

            return data

    async def async_shutdown(self) -> None:
        """Close the Modbus connection on unload."""
        if self._client and self._client.connected:
            self._client.close()
        self._client = None
