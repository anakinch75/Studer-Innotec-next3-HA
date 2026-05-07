"""Constants for Studer Next3 integration."""
from dataclasses import dataclass
from enum import Enum

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower

DOMAIN = "studer_next3"
DEFAULT_HOST = ""
DEFAULT_PORT = 502
DEFAULT_SCAN_INTERVAL = 15


class DataType(str, Enum):
    FLOAT32 = "float32"
    FLOAT64 = "float64"


@dataclass
class ModbusRegisterDef:
    key: str
    name: str
    slave: int
    address: int
    data_type: DataType
    unit: str
    device_class: str
    state_class: str
    scale: float = 1.0


REGISTER_DEFINITIONS: list[ModbusRegisterDef] = [
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
        scale=0.001,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ModbusRegisterDef(
        key="ac_source_produced_energy",
        name="AC-Source Produced Energy",
        slave=7,
        address=36,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        scale=0.001,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
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
        scale=0.001,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
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
        scale=0.001,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
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
        scale=0.001,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ModbusRegisterDef(
        key="battery_discharging_energy",
        name="Battery Discharging Energy",
        slave=1,
        address=8422,
        data_type=DataType.FLOAT64,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        scale=0.001,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
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
]
