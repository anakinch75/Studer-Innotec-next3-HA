"""Sensor platform for Studer Next3."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTER_DEFINITIONS, ModbusRegisterDef
from .coordinator import StuderNext3Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up all sensor entities from a config entry."""
    coordinator: StuderNext3Coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # One entity per register definition
    for reg in REGISTER_DEFINITIONS:
        entities.append(StuderNext3Sensor(coordinator, entry, reg))

    # One extra derived entity for the sign-corrected battery power
    entities.append(StuderNext3BatteryPowerSensor(coordinator, entry))

    async_add_entities(entities)


class StuderNext3Sensor(CoordinatorEntity[StuderNext3Coordinator], SensorEntity):
    """A sensor entity backed by a single Modbus register."""

    def __init__(
        self,
        coordinator: StuderNext3Coordinator,
        entry: ConfigEntry,
        reg: ModbusRegisterDef,
    ) -> None:
        super().__init__(coordinator)
        self._reg = reg
        self._attr_unique_id = f"next3_{reg.key}"
        self._attr_name = reg.name
        self._attr_native_unit_of_measurement = reg.unit
        self._attr_device_class = reg.device_class
        self._attr_state_class = reg.state_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Studer Next3",
            manufacturer="Studer Innotec",
            model="Next3",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value from the coordinator data."""
        return self.coordinator.data.get(self._reg.key)


class StuderNext3BatteryPowerSensor(
    CoordinatorEntity[StuderNext3Coordinator], SensorEntity
):
    """Derived sensor: battery power with correct sign convention.

    The raw register returns positive values when discharging (inverter convention).
    We flip the sign so that charging = positive, discharging = negative,
    which matches the HA energy dashboard expectation.
    """

    def __init__(
        self,
        coordinator: StuderNext3Coordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
        from homeassistant.const import UnitOfPower

        self._attr_unique_id = "next3_battery_power"
        self._attr_name = "Battery Power"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Studer Next3",
            manufacturer="Studer Innotec",
            model="Next3",
        )

    @property
    def native_value(self) -> float | None:
        """Return sign-corrected battery power."""
        return self.coordinator.data.get("battery_power")
