# Paradigm-Paradox Smart Homestead: Local-First Architecture & Design Specification

> **A sovereign, resilient, local-first automation ecosystem for Home Assistant and distributed ESP32 microcontrollers.**

---

## 🏛️ 1. Core Architectural Pillars

### 1.1 Local-First & Data Sovereignty
* **100% Local Execution**: Every calculation, schedule, decision loop, and sensor reading operates within the physical boundary of the homestead local area network (LAN).
* **Zero Cloud Dependencies**: The system functions identically whether WAN internet is connected, degraded, or completely severed. No proprietary clouds, vendor subscriptions, or third-party brokers.
* **User Data Ownership**: Historical time-series telemetry, crop records, water usage logs, and power production data are stored directly on the local Home Assistant host (SSD/NVMe storage) via **DataHub-io** and the Home Assistant recorder.

### 1.2 Edge Autonomy & Fail-Safe Hardware
* **Distributed Microcontrollers (ESP32)**: Dedicated ESP32 nodes manage physical I/O (relays, valves, PWM, sensors) close to the hardware.
* **Firmware-Level Watchdogs**: Actuators (water valves, well pumps, immersion heaters) execute strict auto-off countdown timers in ESP32 firmware (`delayed_off`). If Home Assistant reboots or Wi-Fi drops mid-cycle, the hardware turns itself off safely.
* **Physical Hardware Interlocks**: Critical equipment (e.g. well pump dry-run pressure switches, ATS grid isolation switches, battery thermal cutoffs) feature hardwired electro-mechanical backups independent of software.

---

## 📡 2. Unified Communication & Protocol Standards

All 21 modules communicate locally using two standardized transport layers:

### 2.1 ESPHome Native API (Preferred for ESP32 Nodes)
* **Port**: `6053` (TCP)
* **Encryption**: Pre-shared Noise encryption key (`noise_psk`).
* **Zero Configuration**: Entities are auto-discovered into Home Assistant with native types, units, and update rates up to 50 Hz without MQTT overhead.

### 2.2 Local MQTT with Home Assistant Auto-Discovery
* **Broker**: Local Home Assistant Mosquitto add-on (`core-mosquitto`).
* **Topic Convention**:
  ```text
  paradigm_homestead/<subsystem>/<device_id>/state
  paradigm_homestead/<subsystem>/<device_id>/command
  ```
* **Discovery Topic**:
  ```text
  homeassistant/<component>/paradigm_<subsystem>_<device_id>/<object_id>/config
  ```

---

## 🏷️ 3. Standardized Entity Taxonomy

To ensure a seamless, homogeneous experience across all 21 modules in Home Assistant dashboards and automations:

```text
<domain>.<subsystem>_<location>_<metric_or_action>
```

| Subsystem | Example Entity ID | Friendly Name | Device Class |
| :--- | :--- | :--- | :--- |
| **SolarControl** | `sensor.solar_inverter_pv_power` | Solar Inverter PV Generation | `power` (W) |
| **BatteryBankControl** | `sensor.battery_bank_total_soc` | Battery Storage State of Charge | `battery` (%) |
| **BackupPower** | `binary_sensor.backup_grid_presence` | Main Grid Power Utility Line | `power` |
| **LoadBalancer** | `sensor.load_balancer_main_amperage` | Main Panel Total Current | `current` (A) |
| **WellPumpControl** | `sensor.well_casing_water_depth_ft` | Well Borehole Water Depth | `distance` (ft) |
| **SprinklerController**| `switch.sprinkler_lawn_zone_1_valve` | Sprinkler Zone 1 (Front Lawn) | `switch` |
| **HydroControl** | `sensor.hydro_dwc_reservoir_ph` | DWC Hydro Reservoir pH | `ph` |
| **GardenControl** | `sensor.garden_bed_1_soil_moisture` | Raised Bed 1 Volumetric Moisture | `moisture` (%) |
| **GreenhouseControl** | `sensor.greenhouse_canopy_leaf_vpd` | Canopy Leaf Vapor Pressure Deficit | `pressure` (kPa) |
| **ClimateControl** | `climate.homestead_main_hvac` | Main Homestead HVAC Unit | `climate` |
| **AirQuality** | `sensor.air_quality_indoor_pm2_5` | Indoor PM2.5 Fine Particulate | `pm25` (µg/m³) |
| **SoilSense** | `sensor.soil_field_alpha_nitrogen` | Field Alpha Nitrogen (N) Level | `nitrogen` (mg/kg) |
| **FanControl** | `fan.fan_rack_exhaust_pwm` | Server Rack Exhaust Fan | `fan` |
| **WasteControl** | `sensor.waste_compost_fill_percent` | Main Compost Bin Fill Level | `battery` (%) |
| **PantryControl** | `sensor.pantry_bulk_flour_weight_lbs`| Bulk Flour Bin Net Weight | `weight` (lbs) |
| **WorkshopControl** | `switch.workshop_blast_gate_table_saw`| Table Saw Dust Blast Gate | `switch` |
| **TransportControl** | `device_tracker.transport_truck_ble` | Homestead Farm Truck | `device_tracker` |
| **SecurityControl** | `binary_sensor.security_north_beam_break`| North Perimeter Infrared Beam | `motion` |
| **LightingControl** | `light.lighting_perimeter_security_led` | Perimeter Night Floods | `light` |
| **Control-io** | `switch.homestead_master_irrigation_enable`| Master Irrigation Subsystem Lock | `switch` |
| **DataHub-io** | `sensor.datahub_local_db_size_mb` | Local Telemetry Database Size | `data_size` (MB) |

---

## 🛠️ 4. ESP32 Hardware Guidelines & Electrical Design

When designing and deploying ESP32 nodes for the 21 modules, strict adherence to these hardware rules prevents field instability:

```
+-----------------------------------------------------------------------------------+
|                            ESP32 PIN SAFETY MATRIX                                |
+------------------+-----------------+----------------------------------------------+
| PIN RANGE        | USABLE FUNCTIONS| CRITICAL HARDWARE RULES                      |
+------------------+-----------------+----------------------------------------------+
| GPIO 34, 35,     | Analog In (ADC) | INPUT ONLY. No internal pull-up/pull-down.   |
| GPIO 36, 39      | Sensors         | Perfect for 4-20mA, pressure, thermistors.   |
+------------------+-----------------+----------------------------------------------+
| GPIO 0, 2, 5,    | Boot Strapping  | DO NOT attach pull-ups, relays, or switches  |
| GPIO 12, 15      | Pins            | that hold pins high/low at boot.             |
+------------------+-----------------+----------------------------------------------+
| ADC2             | DO NOT USE WITH | Conflicted with Wi-Fi RF radio! When Wi-Fi   |
| (GPIO 0,2,4,     | ACTIVE WI-FI    | is active, ADC2 reads return corrupt values. |
|  12-15, 25-27)   |                 | Always place analog sensors on ADC1 (32-39). |
+------------------+-----------------+----------------------------------------------+
| GPIO 21, 22      | I2C Bus         | Standard I2C SDA (21) / SCL (22).            |
|                  |                 | Always include 4.7kΩ pull-up to 3.3V.        |
+------------------+-----------------+----------------------------------------------+
| GPIO 16, 17      | Hardware UART   | Standard UART2 for RS485 Modbus transceivers |
|                  |                 | (MAX485/SP3485) and NDIR CO2 sensors.        |
+------------------+-----------------+----------------------------------------------+
| GPIO 4, 5        | TWAI / CAN Bus  | ESP32 CAN controller connected to 3.3V CAN   |
|                  |                 | transceiver (SN65HVD230) for Battery BMS.    |
+------------------+-----------------+----------------------------------------------+
```

---

## ⚡ 5. Cross-Subsystem Interlocks (Control-io Master Logic)

The true power of this ecosystem lies in **autonomous local coordination**:

```
+-----------------------------+
|    SolarControl-io /        |
|  BatteryBankControl-io      |
+--------------+--------------+
               |
               | (Telemetry: Battery SoC, Solar Excess Watts)
               v
+-----------------------------+
|       Control-io Master     |
|   (Local Coordination Hub)  |
+--------------+--------------+
               |
               +---------------------------------------+
               |                                       |
    [ Excess Solar Available ]              [ Low Battery (< 25%) ]
               |                                       |
               v                                       v
+-----------------------------+         +-----------------------------+
|     SolarControl Diverter   |         |      LoadBalancer-io        |
|  - Hot water immersion SSR  |         |  - Lock out WellPump        |
|  - EV charging trickle      |         |  - Shed secondary HVAC      |
+-----------------------------+         |  - Turn off non-essentials  |
                                        +-----------------------------+
```

1. **Water Source Interlock**: `WellPumpControl-io` monitors borehole recharge rate. If static depth drops below safety minimum, `SprinklerController-io` and `GardenControl-io` are paused automatically.
2. **Solar Pumping Interlock**: When `SolarControl-io` detects > 1,500W of excess solar and `WellPumpControl-io` detects a full pressure tank, water is diverted to pump into bulk agricultural cisterns instead of clipping solar production.
3. **Greenhouse Climate Sync**: When `GreenhouseControl-io` detects high VPD, it requests ventilation boost from `FanControl.io` and low-rate misting from `HydroControl-io`.
