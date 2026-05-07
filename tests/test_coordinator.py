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
