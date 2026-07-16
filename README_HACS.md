# ShevMiner — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

Monitoring and control of Antminer mining devices running **VNISH firmware** through Home Assistant.
The integration allows tracking hashrate, temperature, power consumption, controlling mining operations, and automating miner behavior through Home Assistant automations.

## Compatibility

- **Firmware:** VNISH (AnthillOS)
- **Tested versions:** 1.3.3, 1.3.5
- **Tested devices:** Antminer S19j Pro, Antminer S19
- **Languages:** English, Ukrainian

> Need support for a new miner model? Please [create an issue](https://github.com/AlexMarvel/miner-api/issues) with your device model and firmware version.

## Features

- Hashrate monitoring (realtime, average, nominal) in TH/s
- Chip and PCB temperature monitoring
- Power consumption and power efficiency tracking
- Fan RPM and duty cycle monitoring
- Pool statistics (accepted / rejected / stale shares)
- Mining control (start / stop / pause / resume / restart)
- Autotune preset selection
- Miner reboot capability
- Full Home Assistant automation support

## Installation

### Via HACS

1. Add this repository as a custom repository in HACS (type: **Integration**)
2. Click **Install** on "ShevMiner"
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration**
5. Search for "ShevMiner" and follow the config flow

### Manual

1. Copy the `custom_components/shevminer/` folder to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration**
4. Search for "ShevMiner"

## Configuration

The integration is configured via the UI (config flow). You will need:

- **Host / IP** — the miner's IP address (e.g. `192.168.1.147`)
- **Port** — usually `80`
- **Password** — web UI password for the miner (Vnish firmware)
- **API Key** — alternative to password (32-character key); leave empty if using password

## Entities

### Sensors

| Sensor | Unit | Description |
|--------|------|-------------|
| Hashrate Realtime | TH/s | Instant hashrate |
| Hashrate Average | TH/s | Average hashrate |
| Hashrate Nominal | TH/s | Nominal/target hashrate |
| Power Consumption | W | Power draw |
| Power Efficiency | J/TH | Joules per terahash |
| Hardware Errors | count | Total HW errors |
| HW Errors Percent | % | Error percentage |
| Chip Temperature | °C | Max chip temperature |
| PCB Temperature | °C | Max PCB temperature |
| Fan Duty | % | Fan duty cycle |
| Restart Count | count | Total restarts |
| Miner State | — | Current state (mining/stopped/...) |
| Fan N RPM | RPM | Per-fan RPM |
| Pool N Accepted/Rejected/Stale/Status | — | Per-pool statistics |

### Switch

- **Mining** — Start / Stop mining

### Select

- **Autotune Preset** — Select and apply an autotune preset

### Buttons

- **Restart Mining** — Restart the mining process
- **Pause Mining** — Pause mining
- **Resume Mining** — Resume mining
- **Reboot Miner** — Reboot the miner device

## Data Update

The integration polls the miner every 10 seconds.

## Requirements

- Home Assistant 2024.1.0 or newer
- HACS (for one-click install)
- Miner running VNISH firmware with accessible API
