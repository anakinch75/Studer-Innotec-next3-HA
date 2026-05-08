"""Constants for Studer Next3 integration."""
from dataclasses import dataclass
from enum import Enum

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

DOMAIN = "studer_next3"
DEFAULT_HOST = ""
DEFAULT_PORT = 502
DEFAULT_SCAN_INTERVAL = 15


class DataType(str, Enum):
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    UINT16 = "uint16"


@dataclass
class ModbusRegisterDef:
    key: str
    name: str
    slave: int
    address: int
    data_type: DataType
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    scale: float = 1.0


REGISTER_DEFINITIONS: list[ModbusRegisterDef] = [
    # ── AC Source / Grid (slave 7) ───────────────────────────────────────────
    ModbusRegisterDef(
        key="grid_frequency",
        name="Grid Frequency",
        slave=7,
        address=0,
        data_type=DataType.FLOAT32,
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="grid_voltage",
        name="Grid Voltage",
        slave=7,
        address=2,
        data_type=DataType.FLOAT32,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="ac_source_active_power",
        name="AC-Source Active Power",
        slave=7,
        address=8,
        data_type=DataType.FLOAT32,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="ac_source_consumed_energy",
        name="AC-Source Consumed Energy",
        slave=7,
        address=24,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
    ),
    ModbusRegisterDef(
        key="ac_source_produced_energy",
        name="AC-Source Produced Energy",
        slave=7,
        address=36,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
    ),
    # ── AC Loads / System (slave 1) ──────────────────────────────────────────
    ModbusRegisterDef(
        key="ac_loads_active_power",
        name="AC-Loads Active Power",
        slave=1,
        address=3908,
        data_type=DataType.FLOAT32,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="ac_loads_consumed_energy",
        name="AC-Loads Consumed Energy",
        slave=1,
        address=3924,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
    ),
    # ── PV / System (slave 1) ────────────────────────────────────────────────
    ModbusRegisterDef(
        key="pv_power",
        name="PV Power",
        slave=1,
        address=7505,
        data_type=DataType.FLOAT32,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="pv_energy",
        name="PV Energy",
        slave=1,
        address=7519,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
    ),
    # ── Battery / System (slave 1) ───────────────────────────────────────────
    ModbusRegisterDef(
        key="battery_power_raw",
        name="Battery Power (raw)",
        slave=1,
        address=8400,
        data_type=DataType.FLOAT32,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="battery_charging_energy",
        name="Battery Charging Energy",
        slave=1,
        address=8410,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
    ),
    ModbusRegisterDef(
        key="battery_discharging_energy",
        name="Battery Discharging Energy",
        slave=1,
        address=8422,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
    ),
    ModbusRegisterDef(
        key="battery_soc",
        name="Battery SOC",
        slave=1,
        address=8426,
        data_type=DataType.FLOAT32,
        unit="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Battery device (slave 2) ─────────────────────────────────────────────
    ModbusRegisterDef(
        key="battery_voltage",
        name="Battery Voltage",
        slave=2,
        address=318,
        data_type=DataType.FLOAT32,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="battery_current",
        name="Battery Current",
        slave=2,
        address=320,
        data_type=DataType.FLOAT32,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="battery_soh",
        name="Battery State of Health",
        slave=2,
        address=326,
        data_type=DataType.FLOAT32,
        unit="%",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="battery_temperature",
        name="Battery Temperature",
        slave=2,
        address=329,
        data_type=DataType.FLOAT32,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ── Next3 inverter (slave 14) ────────────────────────────────────────────
    ModbusRegisterDef(
        key="inverter_status",
        name="Inverter Status",
        slave=14,
        address=5100,
        data_type=DataType.UINT16,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="inverter_errors",
        name="Inverter Errors",
        slave=14,
        address=5102,
        data_type=DataType.UINT16,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="pv1_voltage",
        name="PV1 Voltage",
        slave=14,
        address=6900,
        data_type=DataType.FLOAT32,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ModbusRegisterDef(
        key="pv1_current",
        name="PV1 Current",
        slave=14,
        address=6902,
        data_type=DataType.FLOAT32,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
]
