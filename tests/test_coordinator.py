"""Tests for the DataUpdateCoordinator."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.studer_next3.coordinator import StuderNext3Coordinator
from custom_components.studer_next3.const import (
    REGISTER_DEFINITIONS,
    NEXT3_DEVICE_DEFINITIONS,
    NUMBER_DEFINITIONS,
    SWITCH_DEFINITIONS,
    MODEL_SELECT_DEFINITIONS,
    MODEL_NEXT1,
    MODEL_NEXT3,
    DataType,
)


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


async def test_uint32_reads_two_registers_and_combines(coordinator):
    """UINT32 (Studer ENUM) reads 2 registers and combines them as a 32-bit value."""
    from custom_components.studer_next3.modbus_client import ModbusTcpClient
    from unittest.mock import AsyncMock as _AM
    uint32_reg = next(r for r in NEXT3_DEVICE_DEFINITIONS if r.key == "inverter_status")
    assert uint32_reg.data_type is DataType.UINT32

    mock_client = _AM(spec=ModbusTcpClient)
    mock_client.connected = True
    mock_client.read_holding_registers.return_value = [0, 3]  # high=0, low=3 → value=3

    result = await coordinator._read_register(mock_client, uint32_reg)

    mock_client.read_holding_registers.assert_called_once_with(5100, 2, 14)
    assert result == 3
    assert isinstance(result, int)


async def test_uint16_reads_single_register(coordinator):
    """UINT16 reads exactly 1 register."""
    from custom_components.studer_next3.modbus_client import ModbusTcpClient
    from unittest.mock import AsyncMock as _AM
    from custom_components.studer_next3.const import ModbusRegisterDef, GROUP_INVERTER
    uint16_reg = ModbusRegisterDef(
        key="test_uint16", name="Test", slave=1, address=100,
        data_type=DataType.UINT16, group=GROUP_INVERTER,
    )

    mock_client = _AM(spec=ModbusTcpClient)
    mock_client.connected = True
    mock_client.read_holding_registers.return_value = [42]

    result = await coordinator._read_register(mock_client, uint16_reg)

    mock_client.read_holding_registers.assert_called_once_with(100, 1, 1)
    assert result == 42


async def test_all_register_keys_present(coordinator):
    async def mock_read(client, reg):
        return 42.0

    async def mock_read_float32(client, address, slave):
        return 42.0

    async def mock_read_bool(client, address, slave):
        return True

    async def mock_read_uint32(client, address, slave):
        return 1

    with patch.object(coordinator, "_get_client", return_value=AsyncMock()):
        with patch.object(coordinator, "_read_register", side_effect=mock_read):
            with patch.object(coordinator, "_read_float32", side_effect=mock_read_float32):
                with patch.object(coordinator, "_read_bool", side_effect=mock_read_bool):
                    with patch.object(coordinator, "_read_uint32_val", side_effect=mock_read_uint32):
                        data = await coordinator._async_update_data()

    expected_keys = (
        {reg.key for reg in REGISTER_DEFINITIONS}
        | {reg.key for reg in NEXT3_DEVICE_DEFINITIONS}
        | {reg.key for reg in NUMBER_DEFINITIONS}
        | {reg.key for reg in SWITCH_DEFINITIONS}
        | {reg.key for reg in MODEL_SELECT_DEFINITIONS[MODEL_NEXT3]}
        | {"battery_power"}
    )
    assert expected_keys.issubset(data.keys())


async def test_all_register_keys_present_next1(hass):
    coordinator = StuderNext3Coordinator(hass, "192.168.1.1", 502, 15, model=MODEL_NEXT1)

    async def mock_read(client, reg):
        return 42.0

    async def mock_read_float32(client, address, slave):
        return 42.0

    async def mock_read_bool(client, address, slave):
        return True

    async def mock_read_uint32(client, address, slave):
        return 1

    with patch.object(coordinator, "_get_client", return_value=AsyncMock()):
        with patch.object(coordinator, "_read_register", side_effect=mock_read):
            with patch.object(coordinator, "_read_float32", side_effect=mock_read_float32):
                with patch.object(coordinator, "_read_bool", side_effect=mock_read_bool):
                    with patch.object(coordinator, "_read_uint32_val", side_effect=mock_read_uint32):
                        data = await coordinator._async_update_data()

    expected_keys = (
        {reg.key for reg in REGISTER_DEFINITIONS}
        | {reg.key for reg in MODEL_SELECT_DEFINITIONS[MODEL_NEXT1]}
        | {reg.key for reg in NUMBER_DEFINITIONS}
        | {reg.key for reg in SWITCH_DEFINITIONS}
        | {"battery_power"}
    )
    assert expected_keys.issubset(data.keys())


async def test_connection_failure_raises_update_failed(coordinator):
    with patch.object(coordinator, "_get_client", side_effect=UpdateFailed("no route")):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
