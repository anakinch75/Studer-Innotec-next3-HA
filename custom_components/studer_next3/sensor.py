"""Sensor platform for Studer Next1/Next3."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_MODEL,
    DOMAIN,
    GROUP_BATTERY,
    GROUP_NAMES,
    MODEL_DEVICE_DEFINITIONS,
    MODEL_NEXT3,
    REGISTER_DEFINITIONS,
    ModbusRegisterDef,
)
from .coordinator import StuderNext3Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all sensor entities from a config entry."""
    coordinator: StuderNext3Coordinator = hass.data[DOMAIN][entry.entry_id]
    model = entry.data.get(CONF_MODEL, MODEL_NEXT3)
    all_regs = REGISTER_DEFINITIONS + MODEL_DEVICE_DEFINITIONS[model]
    entities: list[SensorEntity] = [
        StuderNext3Sensor(coordinator, entry, reg) for reg in all_regs
    ]
    entities.append(StuderNext3BatteryPowerSensor(coordinator, entry))
    async_add_entities(entities)


def _group_device_info(entry: ConfigEntry, group: str, model_name: str) -> DeviceInfo:
    """Sub-device for a sensor group, linked to the hub via via_device."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{group}")},
        name=GROUP_NAMES[group],
        manufacturer="Studer Innotec",
        model=model_name,
        via_device=(DOMAIN, entry.entry_id),
    )


class StuderNext3Sensor(CoordinatorEntity[StuderNext3Coordinator], SensorEntity):
    """A sensor entity backed by a single Modbus register."""

    def __init__(
        self,
        coordinator: StuderNext3Coordinator,
        entry: ConfigEntry,
        reg: ModbusRegisterDef,
    ) -> None:
        super().__init__(coordinator)
        model = entry.data.get(CONF_MODEL, MODEL_NEXT3)
        model_name = "Next3" if model == MODEL_NEXT3 else "Next1"
        self._reg = reg
        self._attr_unique_id = f"next3_{reg.key}"
        self._attr_name = reg.name
        self._attr_entity_registry_enabled_default = reg.key != "battery_power_raw"
        self._attr_native_unit_of_measurement = reg.unit
        self._attr_device_class = reg.device_class
        self._attr_state_class = reg.state_class
        self._attr_suggested_display_precision = reg.suggested_display_precision
        self._attr_device_info = _group_device_info(entry, reg.group, model_name)

    @property
    def native_value(self) -> float | int | None:
        return self.coordinator.data.get(self._reg.key)


class StuderNext3BatteryPowerSensor(
    CoordinatorEntity[StuderNext3Coordinator], SensorEntity
):
    """Battery power with sign convention: charging = positive, discharging = negative."""

    def __init__(
        self,
        coordinator: StuderNext3Coordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        model = entry.data.get(CONF_MODEL, MODEL_NEXT3)
        model_name = "Next3" if model == MODEL_NEXT3 else "Next1"
        self._attr_unique_id = "next3_battery_power"
        self._attr_name = "Battery Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_suggested_display_precision = 0
        self._attr_device_info = _group_device_info(entry, GROUP_BATTERY, model_name)

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("battery_power")
