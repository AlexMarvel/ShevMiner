# ShevMiner — Home Assistant Integration

HACS custom integration for controlling Antminer / Vnish mining devices via the xminer-api.

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
| Hashrate Realtime | GH/s | Instant hashrate |
| Hashrate Average | GH/s | Average hashrate |
| Hashrate Nominal | GH/s | Nominal/target hashrate |
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

The integration polls the miner every 10 seconds by default.

## Requirements

- Home Assistant 2024.1.0 or newer
- HACS (for one-click install)
- Miner running Vnish/Anthill firmware with accessible API
