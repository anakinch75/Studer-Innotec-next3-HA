"""Constants for Studer Next1/Next3 integration."""
from dataclasses import dataclass, field
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

CONF_MODEL = "model"
MODEL_NEXT3 = "next3"
MODEL_NEXT1 = "next1"

# Device groups — each becomes a sub-device under the main "Studer Next1/Next3" hub
GROUP_GRID = "grid"
GROUP_PV = "pv"
GROUP_BATTERY = "battery"
GROUP_INVERTER = "inverter"

GROUP_NAMES: dict[str, str] = {
    GROUP_GRID: "Grid & Loads",
    GROUP_PV: "Solar PV",
    GROUP_BATTERY: "Battery",
    GROUP_INVERTER: "Inverter",
}


class DataType(str, Enum):
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    UINT16 = "uint16"
    UINT32 = "uint32"


@dataclass
class ModbusRegisterDef:
    key: str
    name: str
    slave: int
    address: int
    data_type: DataType
    group: str = GROUP_GRID
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    scale: float = 1.0
    suggested_display_precision: int | None = None


@dataclass
class NumberRegisterDef:
    key: str
    name: str
    slave: int
    address: int
    group: str
    unit: str
    min_value: float
    max_value: float
    step: float = 1.0
    suggested_display_precision: int = 1


NUMBER_DEFINITIONS: list[NumberRegisterDef] = [
    NumberRegisterDef(
        key="soc_for_backup",
        name="SOC for Backup",
        slave=2,
        address=346,
        group=GROUP_BATTERY,
        unit="%",
        min_value=0,
        max_value=100,
        step=1,
    ),
    NumberRegisterDef(
        key="soc_for_end_of_charge",
        name="SOC for End of Charge",
        slave=2,
        address=342,
        group=GROUP_BATTERY,
        unit="%",
        min_value=0,
        max_value=100,
        step=1,
    ),
    NumberRegisterDef(
        key="soc_for_grid_feeding",
        name="SOC for Grid Feeding",
        slave=2,
        address=344,
        group=GROUP_BATTERY,
        unit="%",
        min_value=0,
        max_value=100,
        step=1,
    ),
]


@dataclass
class SwitchRegisterDef:
    key: str
    name: str
    slave: int
    address: int
    group: str


SWITCH_DEFINITIONS: list[SwitchRegisterDef] = [
    SwitchRegisterDef(
        key="grid_feeding_allowed",
        name="Grid-Feeding Allowed",
        slave=7,
        address=1815,
        group=GROUP_GRID,
    ),
]

NEXT3_SWITCH_DEFINITIONS: list[SwitchRegisterDef] = [
    SwitchRegisterDef(key="aux1_relay", name="AUX1 Relay", slave=14, address=8100, group=GROUP_INVERTER),
    SwitchRegisterDef(key="aux2_relay", name="AUX2 Relay", slave=14, address=8400, group=GROUP_INVERTER),
]

NEXT1_SWITCH_DEFINITIONS: list[SwitchRegisterDef] = [
    SwitchRegisterDef(key="aux1_relay", name="AUX1 Relay", slave=29, address=3000, group=GROUP_INVERTER),
    SwitchRegisterDef(key="aux2_relay", name="AUX2 Relay", slave=29, address=3300, group=GROUP_INVERTER),
]

MODEL_SWITCH_DEFINITIONS: dict[str, list[SwitchRegisterDef]] = {
    MODEL_NEXT3: NEXT3_SWITCH_DEFINITIONS,
    MODEL_NEXT1: NEXT1_SWITCH_DEFINITIONS,
}


REGISTER_DEFINITIONS: list[ModbusRegisterDef] = [
    # ── AC Source / Grid (slave 7) ───────────────────────────────────────────
    ModbusRegisterDef(
        key="grid_frequency",
        name="Grid Frequency",
        slave=7,
        address=0,
        data_type=DataType.FLOAT32,
        group=GROUP_GRID,
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    ModbusRegisterDef(
        key="grid_voltage",
        name="Grid Voltage",
        slave=7,
        address=2,
        data_type=DataType.FLOAT32,
        group=GROUP_GRID,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    ModbusRegisterDef(
        key="ac_source_active_power",
        name="AC-Source Active Power",
        slave=7,
        address=8,
        data_type=DataType.FLOAT32,
        group=GROUP_GRID,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    ModbusRegisterDef(
        key="ac_source_consumed_energy",
        name="AC-Source Consumed Energy",
        slave=7,
        address=24,
        data_type=DataType.FLOAT64,
        group=GROUP_GRID,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        suggested_display_precision=2,
    ),
    ModbusRegisterDef(
        key="ac_source_produced_energy",
        name="AC-Source Produced Energy",
        slave=7,
        address=36,
        data_type=DataType.FLOAT64,
        group=GROUP_GRID,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        suggested_display_precision=2,
    ),
    # ── AC Loads / System (slave 1) ──────────────────────────────────────────
    ModbusRegisterDef(
        key="ac_loads_active_power",
        name="AC-Loads Active Power",
        slave=1,
        address=3908,
        data_type=DataType.FLOAT32,
        group=GROUP_GRID,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    ModbusRegisterDef(
        key="ac_loads_consumed_energy",
        name="AC-Loads Consumed Energy",
        slave=1,
        address=3924,
        data_type=DataType.FLOAT64,
        group=GROUP_GRID,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        suggested_display_precision=2,
    ),
    # ── PV / System (slave 1) ────────────────────────────────────────────────
    ModbusRegisterDef(
        key="pv_power",
        name="PV Power",
        slave=1,
        address=7505,
        data_type=DataType.FLOAT32,
        group=GROUP_PV,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    ModbusRegisterDef(
        key="pv_energy",
        name="PV Energy",
        slave=1,
        address=7519,
        data_type=DataType.FLOAT64,
        group=GROUP_PV,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        suggested_display_precision=2,
    ),
    # ── Battery / System (slave 1) ───────────────────────────────────────────
    ModbusRegisterDef(
        key="battery_power_raw",
        name="Battery Power (raw)",
        slave=1,
        address=8400,
        data_type=DataType.FLOAT32,
        group=GROUP_BATTERY,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    ModbusRegisterDef(
        key="battery_charging_energy",
        name="Battery Charging Energy",
        slave=1,
        address=8410,
        data_type=DataType.FLOAT64,
        group=GROUP_BATTERY,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        suggested_display_precision=2,
    ),
    ModbusRegisterDef(
        key="battery_discharging_energy",
        name="Battery Discharging Energy",
        slave=1,
        address=8422,
        data_type=DataType.FLOAT64,
        group=GROUP_BATTERY,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.001,
        suggested_display_precision=2,
    ),
    ModbusRegisterDef(
        key="battery_soc",
        name="Battery SOC",
        slave=1,
        address=8426,
        data_type=DataType.FLOAT32,
        group=GROUP_BATTERY,
        unit="%",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    # ── Battery device (slave 2) ─────────────────────────────────────────────
    ModbusRegisterDef(
        key="battery_voltage",
        name="Battery Voltage",
        slave=2,
        address=318,
        data_type=DataType.FLOAT32,
        group=GROUP_BATTERY,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    ModbusRegisterDef(
        key="battery_current",
        name="Battery Current",
        slave=2,
        address=320,
        data_type=DataType.FLOAT32,
        group=GROUP_BATTERY,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    ModbusRegisterDef(
        key="battery_soh",
        name="Battery State of Health",
        slave=2,
        address=326,
        data_type=DataType.FLOAT32,
        group=GROUP_BATTERY,
        unit="%",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    ModbusRegisterDef(
        key="battery_temperature",
        name="Battery Temperature",
        slave=2,
        address=329,
        data_type=DataType.FLOAT32,
        group=GROUP_BATTERY,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
]

# ── Device-specific registers (model-dependent) ──────────────────────────────

NEXT3_DEVICE_DEFINITIONS: list[ModbusRegisterDef] = [
    ModbusRegisterDef(
        key="inverter_status",
        name="Inverter Status",
        slave=14,
        address=5100,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="inverter_errors",
        name="Inverter Errors",
        slave=14,
        address=5102,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="aux1_relay_position",
        name="AUX1 Relay Position",
        slave=14,
        address=8101,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="aux2_relay_position",
        name="AUX2 Relay Position",
        slave=14,
        address=8401,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
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
        group=GROUP_PV,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    ModbusRegisterDef(
        key="pv1_current",
        name="PV1 Current",
        slave=14,
        address=6902,
        data_type=DataType.FLOAT32,
        group=GROUP_PV,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
]

NEXT1_DEVICE_DEFINITIONS: list[ModbusRegisterDef] = [
    ModbusRegisterDef(
        key="inverter_status",
        name="Inverter Status",
        slave=29,
        address=2700,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="inverter_errors",
        name="Inverter Errors",
        slave=29,
        address=2702,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="aux1_relay_position",
        name="AUX1 Relay Position",
        slave=29,
        address=3001,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
        unit=None,
        device_class=None,
        state_class=None,
    ),
    ModbusRegisterDef(
        key="aux2_relay_position",
        name="AUX2 Relay Position",
        slave=29,
        address=3301,
        data_type=DataType.UINT32,
        group=GROUP_INVERTER,
        unit=None,
        device_class=None,
        state_class=None,
    ),
]

MODEL_DEVICE_DEFINITIONS: dict[str, list[ModbusRegisterDef]] = {
    MODEL_NEXT3: NEXT3_DEVICE_DEFINITIONS,
    MODEL_NEXT1: NEXT1_DEVICE_DEFINITIONS,
}
