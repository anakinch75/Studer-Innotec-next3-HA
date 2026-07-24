"""Studer Next1/Next3 integration for Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_MODEL, DEFAULT_SCAN_INTERVAL, DOMAIN, MODEL_DISPLAY_NAMES, MODEL_NEXT3
from .coordinator import StuderNext3Coordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Studer Next1/Next3 from a config entry."""
    coordinator = StuderNext3Coordinator(
        hass,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        model=entry.data.get(CONF_MODEL, MODEL_NEXT3),
    )

    # Initial data fetch — raises ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Register hub device before platforms so via_device references resolve correctly
    model_key = entry.data.get(CONF_MODEL, MODEL_NEXT3)
    model_name = MODEL_DISPLAY_NAMES[model_key]
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Studer Innotec",
        model=model_name,
        name=f"Studer {model_name}",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and close the Modbus connection."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: StuderNext3Coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok
