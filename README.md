# Studer Next3 — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Custom integration for the **Studer Next3** hybrid inverter/charger via Modbus TCP.

## Sensors

| Entity | Unit | Description |
|---|---|---|
| Next3 AC-Source Active Power | W | Grid power (import/export) |
| Next3 AC-Source Consumed Energy | Wh | Total energy consumed from grid |
| Next3 AC-Source Produced Energy | Wh | Total energy exported to grid |
| Next3 AC-Loads Active Power | W | AC load consumption |
| Next3 AC-Loads Consumed Energy | Wh | Total AC loads energy |
| Next3 PV Power | W | Solar PV production |
| Next3 PV Energy | Wh | Total solar energy produced |
| Next3 Battery Power | W | Battery power (+ = charging, − = discharging) |
| Next3 Battery Charging Energy | Wh | Total energy charged into battery |
| Next3 Battery Discharging Energy | Wh | Total energy discharged from battery |
| Next3 Battery SOC | % | State of charge |

## Installation via HACS

1. In HACS, click **Custom repositories** → add `https://github.com/anakinch75/Studer-Innotec-next3-HA` as **Integration**.
2. Search for *Studer Next3* and install.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and search for *Studer Next3*.
5. Enter the IP address and Modbus TCP port (default `502`).

## Manual installation

Copy the `custom_components/studer_next3/` folder into your HA `config/custom_components/` directory and restart.

## Requirements

- Studer Next3 reachable on your local network via Modbus TCP (port 502).
- `pymodbus` is bundled with Home Assistant — no extra pip install needed.

## Notes

- The **Battery Power** sensor inverts the raw register sign to match HA energy dashboard convention (positive = charging).
- Registers are read with a configurable polling interval (default 15 s for power, 60 s for energy counters). The integration uses the shorter interval globally and skips redundant fast reads for slow registers internally.

## License

MIT
