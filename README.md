# Studer Next3 — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/anakinch75/Studer-Innotec-next3-HA)](https://github.com/anakinch75/Studer-Innotec-next3-HA/releases)

Custom integration for the **Studer Innotec Next3** hybrid inverter/charger via Modbus TCP.

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

4. Click **Submit**. The integration tests the connection before saving. If the device is unreachable you will see an error — check IP address and network access.

> The integration prevents duplicate entries: you cannot add the same IP:port twice.

---

## Available sensors

All sensors are grouped under a single device called **Studer Next3**.

| Entity | Unit | Description |
|---|---|---|
| Next3 AC-Source Active Power | W | Grid power — positive = import, negative = export |
| Next3 AC-Source Consumed Energy | Wh | Cumulative energy consumed from the grid |
| Next3 AC-Source Produced Energy | Wh | Cumulative energy exported to the grid |
| Next3 AC-Loads Active Power | W | Total AC load consumption |
| Next3 AC-Loads Consumed Energy | Wh | Cumulative AC loads energy |
| Next3 PV Power | W | Solar PV production |
| Next3 PV Energy | Wh | Cumulative solar energy produced |
| Next3 Battery Power | W | Battery power — positive = charging, negative = discharging |
| Next3 Battery Charging Energy | Wh | Cumulative energy charged into battery |
| Next3 Battery Discharging Energy | Wh | Cumulative energy discharged from battery |
| Next3 Battery SOC | % | Battery state of charge |

> **Note on Battery Power sign convention:** the raw Modbus register from the Next3 uses inverter convention (positive = discharging). This integration inverts the sign so that it matches the Home Assistant energy dashboard convention (positive = charging).

---

## Energy dashboard integration

The energy sensors are compatible with the HA **Energy** dashboard:

- Go to **Settings → Dashboards → Energy**.
- **Solar panels** → add *Next3 PV Energy*
- **Grid consumption** → add *Next3 AC-Source Consumed Energy* (from grid) and *Next3 AC-Source Produced Energy* (to grid)
- **Battery** → add *Next3 Battery Charging Energy* and *Next3 Battery Discharging Energy*

---

## Modbus register mapping

For reference, the registers read by this integration:

| Key | Slave | Address | Type | Description |
|---|---|---|---|---|
| AC-Source Active Power | 7 | 8 | float32 | |
| AC-Source Consumed Energy | 7 | 24 | float64 | |
| AC-Source Produced Energy | 7 | 36 | float64 | |
| AC-Loads Active Power | 1 | 3908 | float32 | |
| AC-Loads Consumed Energy | 1 | 3924 | float64 | |
| PV Power | 1 | 7505 | float32 | |
| PV Energy | 1 | 7519 | float64 | |
| Battery Power (raw) | 1 | 8400 | float32 | Sign inverted in HA |
| Battery Charging Energy | 1 | 8410 | float64 | |
| Battery Discharging Energy | 1 | 8422 | float64 | |
| Battery SOC | 1 | 8426 | float32 | |

---

## Troubleshooting

**Cannot connect to device**
- Confirm the Next3 IP address is correct and reachable (`ping <ip>` from the HA host).
- Confirm Modbus TCP is enabled on the Next3 and port 502 is not blocked by a firewall.

**Sensors show `unavailable`**
- The Next3 may have closed the TCP connection. The integration reconnects automatically on the next polling cycle.
- Check the Home Assistant logs (**Settings → System → Logs**) and filter by `studer_next3`.

**Wrong values on energy sensors**
- Energy sensors are `total_increasing`: HA expects them to only go up. If the Next3 resets its counters (firmware update, power cycle), HA may show a spike. Use the HA **Statistics** editor to fix the long-term stats if needed.

---

## License

MIT
