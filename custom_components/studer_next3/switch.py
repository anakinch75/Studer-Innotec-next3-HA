"""Switch entities for Studer Next1/Next3 — writable boolean settings."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN, MODEL_DISPLAY_NAMES, MODEL_NEXT3, MODEL_SWITCH_DEFINITIONS, SWITCH_DEFINITIONS, SwitchRegisterDef
from .coordinator import StuderNext3Coordinator
from .sensor import _group_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StuderNext3Coordinator = hass.data[DOMAIN][entry.entry_id]
    model = entry.data.get(CONF_MODEL, MODEL_NEXT3)
    all_switches = SWITCH_DEFINITIONS + MODEL_SWITCH_DEFINITIONS[model]
    async_add_entities(
        StuderNext3Switch(coordinator, entry, reg) for reg in all_switches
    )


class StuderNext3Switch(CoordinatorEntity[StuderNext3Coordinator], SwitchEntity):
    """A writable switch entity backed by a Modbus bool register."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StuderNext3Coordinator,
        entry: ConfigEntry,
        reg: SwitchRegisterDef,
    ) -> None:
        super().__init__(coordinator)
        self._reg = reg
        self._attr_unique_id = f"{entry.entry_id}_{reg.key}"
        self._attr_name = reg.name
        model = entry.data.get(CONF_MODEL, MODEL_NEXT3)
        model_name = MODEL_DISPLAY_NAMES[model]
        self._attr_device_info = _group_device_info(entry, reg.group, model_name)

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._reg.key)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_bool(self._reg.address, True, self._reg.slave)
        self.coordinator.data[self._reg.key] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_bool(self._reg.address, False, self._reg.slave)
        self.coordinator.data[self._reg.key] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
