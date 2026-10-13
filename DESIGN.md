# SprinklerController-io: Design & Architecture Document

## Overview
**SprinklerController-io** is an edge-native Home Assistant Add-on providing automated multi-zone irrigation, weather adaptation, cycle & soak scheduling, and distributed **ESP32** edge controller integration.

For complete architectural details and ESP32 hardware configurations, see [sprinkler_controller/DESIGN.md](file:///mnt/data/HomeAssitant-Addon/sprinkler_controller/DESIGN.md) and [docs/DESIGN.md](file:///mnt/data/HomeAssitant-Addon/docs/DESIGN.md).

## Core Capabilities
1. **ESP32 Edge Controllers (Wi-Fi, Ethernet, Bluetooth)**:
   - Wired Ethernet (WT32-ETH01, Olimex PoE) for outdoor valve boxes.
   - Wi-Fi 4/8/16-channel 24VAC relay nodes.
   - BLE tracking for wireless soil moisture probes.
2. **Safety & Hardware Watchdogs**:
   - Firmware auto-off countdown timers prevent stuck-open valves.
   - Physical rain sensor cutoffs and freeze lockouts.
3. **Smart Scheduling & Water Budgeting**:
   - Evapotranspiration (ET) and predictive rain delay.
   - Cycle & soak runoff prevention.
4. **Home Assistant Ecosystem Integration**:
   - Ingress UI embedded in Home Assistant sidebar.
   - Direct service calling via Supervisor Core API.
