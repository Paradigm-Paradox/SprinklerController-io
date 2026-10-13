# Home Assistant Community Add-on: FanControl-io

FanControl-io provides intelligent thermal orchestration and variable fan speed control for server racks, network enclosures, and custom cooling projects using low-cost ESP32 microcontrollers.

## Features

- **Multi-Protocol ESP32 Integration**: Supports Wi-Fi, 10/100 Wired Ethernet (WT32-ETH01, Olimex PoE), and Bluetooth Low Energy (BLE).
- **Intelligent Thermal Regulation**: Dynamically calculates exhaust vs. intake Delta-T to eliminate server rack heat pockets while preserving silence.
- **Tachometer Monitoring & Stall Alerts**: Real-time RPM pulse counting with automatic stall detection to warn of seized fans or dust buildup.
- **Edge-Level Thermal Failsafe**: Microcontrollers run autonomous watchdogs; if the network goes down, the fans automatically ramp to safety speeds.
- **Integrated Ingress Dashboard**: Full-featured control panel embedded seamlessly in Home Assistant.

## Hardware Wiring Guide (4-Pin PWM Fans)

Standard 4-pin computer cooling fans (Noctua, Arctic, Delta, etc.) connect as follows:

| Fan Wire Pin | Function | ESP32 Connection | Notes |
|---|---|---|---|
| Pin 1 (Black) | GND | Common Ground | Tie to ESP32 GND and 12V PSU GND |
| Pin 2 (Yellow) | +12V VCC | 12V Power Supply | Powered directly from 12V DC power source |
| Pin 3 (Green) | Tachometer (Sense) | GPIO (e.g. GPIO18, 36) | Requires 10kΩ pull-up resistor to 3.3V |
| Pin 4 (Blue) | PWM Control | GPIO (e.g. GPIO22, 14) | Direct 3.3V connection to ESP32 LEDC pin |

## Quick Start

1. Install this add-on from your Home Assistant Add-on Store repository.
2. Flash your ESP32 board using one of the included ESPHome templates:
   - Wi-Fi + BLE: `esp32_rack_fan_wifi_ble.yaml`
   - Wired Ethernet: `wt32_eth01_rack_fan_ethernet.yaml`
3. Configure your sensor entities and fan channels in the add-on configuration tab.
4. Launch the Ingress dashboard from the Home Assistant sidebar!
