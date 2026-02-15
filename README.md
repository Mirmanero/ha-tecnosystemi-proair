# Tecnosystemi ProAir for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Mirmanero&repository=ha-tecnosystemi-proair&category=integration)

Unofficial custom integration for [Home Assistant](https://www.home-assistant.io/) to control **Tecnosystemi ProAir** climate systems over the local network (TCP).

> **Note:** This is an independent project, not affiliated with or supported by Tecnosystemi. Use at your own risk.
>
> **Tested only with ProAir Polaris 3x.** If you successfully use this integration with a different ProAir model, please [open an issue](https://github.com/Mirmanero/ha-tecnosystemi-proair/issues) to let me know — I'd love to update the compatibility list.

## Features

- Local communication via TCP (no cloud)
- Climate control per zone (temperature, HVAC mode, fan speed)
- Temperature and humidity sensors per zone
- Canal temperature sensor
- Control unit power switch
- Operating mode selection (heating, cooling, dehumidification, ventilation)
- Config Flow UI setup
- Italian and English translations

## Installation

### HACS (recommended)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Mirmanero&repository=ha-tecnosystemi-proair&category=integration)

Click the button above, or add manually:

1. Open HACS in Home Assistant
2. Click the three dots menu (top right) → **Custom repositories**
3. Add `https://github.com/Mirmanero/ha-tecnosystemi-proair` with category **Integration**
4. Search for **Tecnosystemi ProAir** and install it
5. Restart Home Assistant

### Manual

1. Download or clone this repository
2. Copy the `custom_components/proair` folder into your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Tecnosystemi ProAir**
3. Enter:
   - **Host**: IP address of your ProAir system
   - **Port**: TCP port (default: `1235`)
   - **PIN**: Access PIN (default: `0000`)

## Entities

### Control Unit (parent device)

| Entity | Type | Description |
|--------|------|-------------|
| Power | Switch | Turn the control unit on/off |
| Operating mode | Select | Heating / Cooling / Dehumidification / Ventilation |
| Canal temperature | Sensor | Air duct temperature (°C) |

### Per Zone (child devices)

| Entity | Type | Description |
|--------|------|-------------|
| Climate | Climate | HVAC mode, target temperature, fan mode |
| Temperature | Sensor | Current zone temperature (°C) |
| Humidity | Sensor | Current zone humidity (%) |

### Climate entity details

- **HVAC modes**: Off, Heat, Cool, Dry, Fan Only
- **Fan modes**: Auto, Low, Medium, High (mapped to damper opening)
- **Temperature range**: 10–35 °C (0.5° step)

## How it works

The integration communicates directly with the ProAir control unit over TCP on your local network. It polls the status every 30 seconds. All commands (temperature changes, mode switches, on/off) are sent immediately.

No internet connection or cloud service is required.
