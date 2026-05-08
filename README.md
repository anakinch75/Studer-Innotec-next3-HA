# Studer Next3 — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/anakinch75/Studer-Innotec-next3-HA)](https://github.com/anakinch75/Studer-Innotec-next3-HA/releases)
[![Tests](https://github.com/anakinch75/Studer-Innotec-next3-HA/actions/workflows/tests.yml/badge.svg)](https://github.com/anakinch75/Studer-Innotec-next3-HA/actions/workflows/tests.yml)

Custom integration for the **Studer Innotec Next3** hybrid inverter/charger via Modbus TCP.  
No external dependencies — uses a native asyncio Modbus TCP client.

---

## Prerequisites

- Home Assistant **≥ 2024.4**
- The Studer Next3 must be reachable on your local network via **Modbus TCP** (default port **502**)
- Modbus TCP must be enabled on the Next3 (see the Studer configuration portal)

---

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant.
2. Click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/anakinch75/Studer-Innotec-next3-HA` and select category **Integration**.
4. Search for **Studer Next3** and click **Download**.
5. Restart Home Assistant.

### Manual installation

1. Copy the `custom_components/studer_next3/` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Studer Next3**.
3. Fill in the form:

| Field | Default | Description |
|---|---|---|
| IP address | _(empty)_ | IP address of the Next3 on your network |
| Modbus TCP port | `502` | Modbus TCP port (usually 502) |
| Polling interval (s) | `15` | How often data is fetched (5–300 s) |

4. Click **Submit**. The integration tests the connection before saving.

---

## Available sensors

Sensors are organised into **4 sub-devices** under the main **Studer Next3** hub, visible in **Settings → Devices & services → Studer Next3**.

### 🔌 Grid & Loads

| Sensor | Unit | Description |
|---|---|---|
| Grid Frequency | Hz | Grid frequency |
| Grid Voltage | V | Line voltage L1-L2 |
| AC-Source Active Power | W | Positive = import, negative = export |
| AC-Source Consumed Energy | kWh | Cumulative energy imported from grid |
| AC-Source Produced Energy | kWh | Cumulative energy exported to grid |
| AC-Loads Active Power | W | Total AC load consumption |
| AC-Loads Consumed Energy | kWh | Cumulative AC load energy |

### ☀️ Solar PV

| Sensor | Unit | Description |
|---|---|---|
| PV Power | W | Total PV production (system) |
| PV Energy | kWh | Cumulative solar energy |
| PV1 Voltage | V | DC voltage on PV input 1 |
| PV1 Current | A | DC current on PV input 1 |

### 🔋 Battery

| Sensor | Unit | Description |
|---|---|---|
| Battery Power | W | Positive = charging, negative = discharging |
| Battery SOC | % | State of charge |
| Battery Voltage | V | Battery pack voltage |
| Battery Current | A | Positive = charging, negative = discharging |
| Battery Temperature | °C | Battery temperature |
| Battery State of Health | % | Long-term capacity degradation |
| Battery Charging Energy | kWh | Cumulative energy charged |
| Battery Discharging Energy | kWh | Cumulative energy discharged |

### ⚡ Inverter

| Sensor | Unit | Description |
|---|---|---|
| Inverter Status | — | Operating mode (integer code, see note below) |
| Inverter Errors | — | Active error flags (integer bitfield) |

> **Inverter Status codes** are raw integers from the Studer register map. Refer to the [official Studer Modbus documentation](https://technext3.studer-innotec.com/modbus-next) for the meaning of each value.

> **Battery Power sign convention:** the raw Modbus register uses inverter convention (positive = discharging). This integration inverts the sign to match the HA energy dashboard (positive = charging).

> **Battery Power (raw)** is hidden by default. Enable it in **Settings → Devices → Battery** if needed.

---

## Energy dashboard

Go to **Settings → Dashboards → Energy** and configure:

| Dashboard section | Sensor |
|---|---|
| Solar panels | *PV Energy* |
| Grid — from grid | *AC-Source Consumed Energy* |
| Grid — to grid | *AC-Source Produced Energy* |
| Battery — charging | *Battery Charging Energy* |
| Battery — discharging | *Battery Discharging Energy* |
| Home consumption | *AC-Loads Consumed Energy* |

---

## Modbus register mapping

Addresses from the official [Studer next-modbus register map v10.154](https://github.com/studer-innotec/next-modbus).

| Sensor | Slave | Address | Type |
|---|---|---|---|
| Grid Frequency | 7 | 0 | float32 |
| Grid Voltage | 7 | 2 | float32 |
| AC-Source Active Power | 7 | 8 | float32 |
| AC-Source Consumed Energy | 7 | 24 | float64 |
| AC-Source Produced Energy | 7 | 36 | float64 |
| AC-Loads Active Power | 1 | 3908 | float32 |
| AC-Loads Consumed Energy | 1 | 3924 | float64 |
| PV Power | 1 | 7505 | float32 |
| PV Energy | 1 | 7519 | float64 |
| Battery Power (raw) | 1 | 8400 | float32 |
| Battery Charging Energy | 1 | 8410 | float64 |
| Battery Discharging Energy | 1 | 8422 | float64 |
| Battery SOC | 1 | 8426 | float32 |
| Battery Voltage | 2 | 318 | float32 |
| Battery Current | 2 | 320 | float32 |
| Battery State of Health | 2 | 326 | float32 |
| Battery Temperature | 2 | 329 | float32 |
| Inverter Status | 14 | 5100 | uint16 |
| Inverter Errors | 14 | 5102 | uint16 |
| PV1 Voltage | 14 | 6900 | float32 |
| PV1 Current | 14 | 6902 | float32 |

---

## Migrating from an older version

### Energy sensors showing Wh instead of kWh (upgrading from < 0.4.0)

Since v0.4.0, energy sensors report in **kWh**. If you installed the integration before v0.4.0, Home Assistant may have cached the old **Wh** unit and will keep converting values automatically, resulting in values 1 000× too large.

Fix for each of the 6 energy sensors:

1. Go to **Settings → Entities**
2. Search for the sensor (e.g. *PV Energy*)
3. Click on it → ⚙️ → **Unit of measurement** → change `Wh` to `kWh`

Sensors to update:
- PV Energy
- AC-Source Consumed Energy
- AC-Source Produced Energy
- AC-Loads Consumed Energy
- Battery Charging Energy
- Battery Discharging Energy

---

## Troubleshooting

**Cannot connect to device**
- Confirm the Next3 IP is reachable (`ping <ip>` from the HA host).
- Confirm Modbus TCP is enabled on the Next3 and port 502 is not blocked.

**Sensors show `unavailable`**
- The Next3 may have closed the TCP connection. The integration reconnects automatically.
- Check **Settings → System → Logs** and filter by `studer_next3`.

**Sensors on slave 2 or 14 show `unavailable`**
- These registers (battery device, inverter) may not be accessible depending on your firmware version or system configuration.
- The other sensors (slave 1 and 7) will continue to work normally.

**Energy values reset unexpectedly**
- Energy sensors are `total_increasing`. If the Next3 resets its counters (firmware update, power cycle), HA may show a spike. Use the HA **Statistics** editor to correct long-term stats.

---

## License

MIT
