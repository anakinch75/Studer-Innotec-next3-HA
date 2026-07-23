"""Number entities for Studer Next1/Next3 — writable settings."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN, MODEL_NEXT3, NUMBER_DEFINITIONS, NumberRegisterDef
from .coordinator import StuderNext3Coordinator
from .sensor import _group_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StuderNext3Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StuderNext3Number(coordinator, entry, reg) for reg in NUMBER_DEFINITIONS
    )


class StuderNext3Number(CoordinatorEntity[StuderNext3Coordinator], NumberEntity):
    """A writable number entity backed by a Modbus float32 register."""

    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: StuderNext3Coordinator,
        entry: ConfigEntry,
        reg: NumberRegisterDef,
    ) -> None:
        super().__init__(coordinator)
        self._reg = reg
        self._attr_unique_id = f"{entry.entry_id}_{reg.key}"
        self._attr_name = reg.name
        self._attr_native_unit_of_measurement = reg.unit
        self._attr_native_min_value = reg.min_value
        self._attr_native_max_value = reg.max_value
        self._attr_native_step = reg.step
        self._attr_suggested_display_precision = reg.suggested_display_precision
        model = entry.data.get(CONF_MODEL, MODEL_NEXT3)
        model_name = "Next3" if model == MODEL_NEXT3 else "Next1"
        self._attr_device_info = _group_device_info(entry, reg.group, model_name)

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self._reg.key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_float32(
            self._reg.address, value, self._reg.slave
        )
        # Optimistically update local state then schedule a refresh
        self.coordinator.data[self._reg.key] = value
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
