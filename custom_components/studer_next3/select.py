"""Select entities for Studer Next1/Next3 — writable ENUM settings."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN, MODEL_DISPLAY_NAMES, MODEL_NEXT3, MODEL_SELECT_DEFINITIONS, SelectRegisterDef
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
    async_add_entities(
        StuderNext3Select(coordinator, entry, reg)
        for reg in MODEL_SELECT_DEFINITIONS[model]
    )


class StuderNext3Select(CoordinatorEntity[StuderNext3Coordinator], SelectEntity):
    """A writable select entity backed by a Modbus UINT32 ENUM register."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StuderNext3Coordinator,
        entry: ConfigEntry,
        reg: SelectRegisterDef,
    ) -> None:
        super().__init__(coordinator)
        self._reg = reg
        self._attr_unique_id = f"{entry.entry_id}_{reg.key}"
        self._attr_name = reg.name
        self._attr_options = list(reg.options.values())
        model_name = MODEL_DISPLAY_NAMES[entry.data.get(CONF_MODEL, MODEL_NEXT3)]
        self._attr_device_info = _group_device_info(entry, reg.group, model_name)

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get(self._reg.key)
        if raw is None:
            return None
        return self._reg.options.get(int(raw))

    async def async_select_option(self, option: str) -> None:
        value = next(k for k, v in self._reg.options.items() if v == option)
        await self.coordinator.async_write_uint32(self._reg.address, value, self._reg.slave)
        self.coordinator.data[self._reg.key] = value
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
