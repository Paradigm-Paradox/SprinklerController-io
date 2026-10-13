# FanControl-io: Design & Architecture Document

## 1. Overview
**FanControl-io** is an intelligent thermal management and variable speed fan orchestration system built as a Home Assistant Add-on. It links Home Assistant's environmental sensors and automation engine to distributed **ESP32** edge microcontrollers over **Wi-Fi**, **Ethernet**, and **Bluetooth Low Energy (BLE)** to provide whisper-quiet, precision cooling for server racks, AV enclosures, networking cabinets, and greenhouse/grow setups.

---

## 2. ESP32 Microcontroller Architecture

The ESP32 family (Espressif Systems) provides dedicated hardware timers and multi-protocol connectivity:

```
+-----------------------------------------------------------------------------------+
|                           Home Assistant Core / Supervisor                        |
|                                                                                   |
|    +-------------------------------------------------------------------------+    |
|    |                        FanControl-io Add-on                             |    |
|    |  - Delta-T Thermal Engine (Exhaust vs Intake differential cooling)      |    |
|    |  - Curve Optimizer (Silent, Balanced, Performance, Turbo profiles)     |    |
|    |  - Tachometer RPM Telemetry & Stall Alert Monitor                       |    |
|    |  - Ingress Web UI & ESPHome Blueprint Distributor                      |    |
|    +-----------------------------------+-------------------------------------+    |
+----------------------------------------|------------------------------------------+
                                         | (Native HA API / MQTT / WebSockets)
           +-----------------------------+-----------------------------+
           |                                                           |
+----------v-----------------------------+       +---------------------v--------------------+
|  ESP32 Edge Node: Ethernet / PoE       |       |  ESP32 Edge Node: Wi-Fi + BLE Gateway    |
|  (e.g., WT32-ETH01 / Olimex POE)       |       |  (e.g., ESP32-WROOM-32 / ESP32-S3)       |
|                                        |       |                                          |
|  Hardware Features:                    |       |  Hardware Features:                      |
|  - 10/100 Mbps RJ45 Wired Ethernet     |       |  - 2.4 GHz 802.11 b/g/n Wi-Fi            |
|  - Metal rack Faraday immunity         |       |  - Active BLE Tracker (Xiaomi, Inkbird)  |
|  - 4x 25 kHz Hardware LEDC PWM outputs |       |  - 2-4x Hardware PWM fan outputs         |
|  - 4x Tachometer pulse counter inputs  |       |  - 1-Wire DS18B20 temp probe bus         |
|  - Hardware watchdog auto-failsafe     |       |  - Autonomous failsafe watchdog          |
+----------------------------------------+       +------------------------------------------+
```

### 2.1 Hardware Profiles
1. **Wired Ethernet & PoE Boards** *(Ideal for metallic server rack enclosures)*:
   - **WT32-ETH01**: Low-cost ESP32 with LAN8720 PHY Ethernet. Bypasses RF shielding inside enclosed steel server racks.
   - **Olimex ESP32-POE / ESP32-POE-ISO**: Power-over-Ethernet simplifies wiring to a single CAT6 run.
2. **Wi-Fi + BLE Gateway Boards**:
   - ESP32-WROOM-32 / ESP32-S3.
   - Uses the ESP32's onboard BLE radio to scan wireless temperature & humidity beacons (e.g. Xiaomi Mijia LYWSD03MMC, Inkbird IBS-TH1/TH2, RuuviTag) positioned throughout the rack without extra wiring.
3. **Fan Wiring & Signal Interfacing**:
   - **4-Pin PWM Fans (Noctua, Arctic, Delta, San Ace)**:
     - Pin 1: GND (Common Ground).
     - Pin 2: +12V (or +24V / +5V depending on fan voltage).
     - Pin 3: Tachometer (Open-collector/drain pulse output, requires 10k pull-up to 3.3V).
     - Pin 4: PWM Control Input (25 kHz target frequency, 3.3V logic level directly driven by ESP32 LEDC pin).
   - **3-Pin Voltage Controlled Fans**:
     - Controlled via external logic-level N-channel MOSFET (e.g., IRLZ44N) or buck regulator module with flyback diode protection.
   - **0-10V EC Fans**:
     - Driven via an active op-amp or I2C DAC (MCP4725) module.

---

## 3. Thermal Regulation Strategies

### 3.1 Delta-T (Differential Temperature) Control
Server racks require airflow proportional to the heat produced, not simply ambient temperature. FanControl-io calculates:
$$\Delta T = T_{\text{exhaust}} - T_{\text{intake}}$$
- If $\Delta T \le 4^\circ\text{C}$: Fans stay at ultra-quiet idle (15-25%).
- If $\Delta T > 8^\circ\text{C}$: Fan speed ramps aggressively to exhaust accumulated thermal load.
- If $T_{\text{exhaust}} \ge T_{\text{emergency}}$ ($45^\circ\text{C}$): Emergency Override engages, forcing 100% PWM regardless of mode.

### 3.2 Edge Safety & Stall Detection
- **Fan Stall Alarm**: If PWM duty cycle is $> 20\%$ but measured RPM remains below 200 RPM for $> 5$ seconds, the controller raises an immediate stall alarm (protecting equipment from seized bearing failures).
- **Offline Failsafe**: If network connection or Home Assistant disconnects, the ESP32 edge firmware automatically sets fan duty cycles to a safe 70% or 100% default.

---

## 4. REST API & Integration Matrix

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Current system status, thermal telemetry, and fan speeds |
| `/api/mode` | POST | Switch profile (`auto`, `silent`, `balanced`, `performance`, `turbo`, `manual`) |
| `/api/fans/{id}/speed` | POST | Set manual PWM duty cycle (0-100%) |
| `/api/thermal/target` | POST | Update target exhaust and Delta-T limits |
| `/api/esphome/blueprint/{type}` | GET | Download pre-configured ESPHome YAML firmware |
