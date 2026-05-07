"""Tests for the DataUpdateCoordinator."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.studer_next3.coordinator import StuderNext3Coordinator
from custom_components.studer_next3.const import REGISTER_DEFINITIONS


@pytest.fixture
def coordinator(hass: HomeAssistant) -> StuderNext3Coordinator:
    return StuderNext3Coordinator(hass, "192.168.1.1", 502, 15)


async def test_battery_power_sign_is_flipped(coordinator):
    """Raw register is positive when discharging; coordinator must negate."""
    async def mock_read(client, reg):
        return 500.0 if reg.key == "battery_power_raw" else 0.0

    with patch.object(coordinator, "_get_client", return_value=AsyncMock()):
        with patch.object(coordinator, "_read_register", side_effect=mock_read):
            data = await coordinator._async_update_data()

    assert data["battery_power"] == -500.0
    assert data["battery_power_raw"] == 500.0


async def test_battery_power_none_when_raw_unavailable(coordinator):
    async def mock_read(client, reg):
        return None

    with patch.object(coordinator, "_get_client", return_value=AsyncMock()):
        with patch.object(coordinator, "_read_register", side_effect=mock_read):
            data = await coordinator._async_update_data()

    assert data["battery_power"] is None


async def test_energy_scale_applied(coordinator):
    """Energy registers (scale=0.001) must return values in kWh, not Wh."""
    energy_reg = next(r for r in REGISTER_DEFINITIONS if r.key == "pv_energy")
    assert energy_reg.scale == pytest.approx(0.001)

    raw_wh = 48_570_299.0
    import struct
    regs = list(struct.unpack(">HHHH", struct.pack(">d", raw_wh)))

    from unittest.mock import AsyncMock as _AM
    from custom_components.studer_next3.modbus_client import ModbusTcpClient

    mock_client = _AM(spec=ModbusTcpClient)
    mock_client.connected = True
    mock_client.read_holding_registers.return_value = regs

    result = await coordinator._read_register(mock_client, energy_reg)
    assert result == pytest.approx(raw_wh * 0.001, rel=1e-6)


async def test_all_register_keys_present(coordinator):
    async def mock_read(client, reg):
        return 42.0

    with patch.object(coordinator, "_get_client", return_value=AsyncMock()):
        with patch.object(coordinator, "_read_register", side_effect=mock_read):
            data = await coordinator._async_update_data()

    expected_keys = {reg.key for reg in REGISTER_DEFINITIONS} | {"battery_power"}
    assert expected_keys.issubset(data.keys())


async def test_connection_failure_raises_update_failed(coordinator):
    with patch.object(coordinator, "_get_client", side_effect=UpdateFailed("no route")):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
