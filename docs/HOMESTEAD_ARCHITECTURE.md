# MyHomeStead.io: Local-First Architecture & Design Specification

> **A sovereign, resilient, local-first automation ecosystem for Home Assistant and distributed ESP32 microcontrollers.**  
> *Governing all 26 `*-io` specialized homestead subsystems.*

<p align="center">
  <img src="assets/myhomestead_logo.png" alt="MyHomeStead.io Master Architecture Logo" width="300" style="border-radius: 20px;">
</p>

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

## 🗺️ 2. The 26 Subsystems of MyHomeStead.io

```
                                  +-------------------------------------------------------------+
                                  |                       MyHomeStead.io                        |
                                  |              (Master Sovereign Homestead Node)              |
                                  |                                                             |
                                  |  +-------------------------------------------------------+  |
                                  |  |                   Control-io Master                   |  |
                                  |  |        (System Supervisor & Cross-Domain Logic)       |  |
                                  |  +---------------------------+---------------------------+  |
                                  |                              |                              |
                                  |  +---------------------------v---------------------------+  |
                                  |  |                   DataHub-io Engine                   |  |
                                  |  |  (Local InfluxDB/TimescaleDB/SQLite • Long-Term Store)|  |
                                  |  +---------------------------+---------------------------+  |
                                  +------------------------------+------------------------------+
                                                                 |
                                      Local LAN Only (ESPHome Native API / Local Mosquitto MQTT)
                                                                 |
            +--------------------+-------------------------------+--------------------+--------------------+
            |                    |                               |                    |                    |
            v                    v                               v                    v                    v
     [ ⚡ ENERGY & POWER ] [ 💧 WATER LIFELINE ]         [ 🌱 AGRI & LIVING ] [ 🌬️ CLIMATE & AIR ] [ 🏡 HOMESTEAD & LOGS ]
     - SolarControl       - WellPumpControl               - GreenhouseControl  - ClimateControl     - LivestockCare
     - BatteryBankControl - RainHarvest                   - HydroControl       - AirQuality         - CompostControl
     - BackupPower        - WaterTankControl              - SoilSense          - FanControl         - PantryControl
     - LoadBalancer       - FiltrationControl             - GardenControl                           - WorkshopControl
                          - SprinklerController                                                     - WasteControl
                                                                                                    - TransportControl
                                                                                                    - SecurityControl
                                                                                                    - LightingControl
```

---

## ⚡ 3. Domain Subsystems & Hardware Profiles

### Domain 1: Energy & Power
| Subsystem | ESP32 Hardware Profile | Key Sensors & Actuators | Local Home Assistant Entities |
| :--- | :--- | :--- | :--- |
| **SolarControl-io** | WT32-ETH01 / ESP32 + MAX485 | Inverter Modbus RTU, SSR zero-cross PWM | `sensor.solar_inverter_pv_power`<br>`sensor.solar_excess_power_diverted`<br>`switch.solar_diverter_immersion_ssr` |
| **BatteryBankControl-io** | ESP32-S3 + SN65HVD230 CAN | TWAI/CAN bus (Pylontech), BLE BMS client | `sensor.battery_bank_total_soc`<br>`sensor.battery_bank_bus_voltage`<br>`sensor.battery_bank_min_cell_voltage` |
| **BackupPower-io** | ESP32 + Optocoupler AC Sense | Grid loss detector, ATS feedback, 2-wire auto-start | `binary_sensor.backup_grid_presence`<br>`binary_sensor.backup_ats_position`<br>`switch.backup_generator_autostart` |
| **LoadBalancer-io** | ESP32 + Multi-channel ADC | Split-core CT clamps (SCT-013), EVSE pilot PWM | `sensor.load_balancer_main_amperage`<br>`sensor.load_balancer_evse_allowed_amps`<br>`switch.load_balancer_shed_secondary_hvac` |

### Domain 2: Water Lifeline & Management
| Subsystem | ESP32 Hardware Profile | Key Sensors & Actuators | Local Home Assistant Entities |
| :--- | :--- | :--- | :--- |
| **WellPumpControl-io** | WT32-ETH01 PoE + Snubber Relay | 4-20mA hydrostatic depth sensor, 0-100 PSI pressure | `sensor.well_casing_water_depth_ft`<br>`sensor.well_system_pressure_psi`<br>`switch.well_pump_contactor` |
| **RainHarvest-io** | ESP32 Solar Deep Sleep | Tipping bucket rain gauge, first-flush diverters | `sensor.rain_harvest_daily_volume_gal`<br>`sensor.rain_harvest_precipitation_rate_in_hr`<br>`switch.rain_first_flush_purge_valve` |
| **WaterTankControl-io**| ESP32 + Waterproof Ultrasonic | Non-contact ultrasonic (JSN-SR04T), high/low floats | `sensor.water_tank_storage_level_percent`<br>`sensor.water_tank_total_gallons`<br>`switch.water_tank_transfer_pump` |
| **FiltrationControl-io**| ESP32 + Dual Pressure Sensors | Differential pressure ($\Delta P$), UV ballast current | `sensor.filtration_filter_delta_pressure_psi`<br>`sensor.filtration_uv_sterilizer_intensity`<br>`switch.filtration_backwash_cycle_valve` |
| **SprinklerController-io**| WT32-ETH01 / NodeMCU-32S | 8/16-channel 24VAC relays, Hall flow meter (GPM) | `sensor.sprinkler_flow_rate_gpm`<br>`switch.sprinkler_lawn_zone_1_valve`<br>`binary_sensor.sprinkler_freeze_lockout` |
| **GardenControl-io** | ESP32 LiFePO4 Solar Node | Soil moisture, latching valves, $ET_0$ calculation | `sensor.garden_bed_1_soil_moisture`<br>`sensor.garden_daily_et0_loss_inches`<br>`switch.garden_manifold_zone_raised_beds` |

### Domain 3: Agriculture, Greenhouse & Living Systems
| Subsystem | ESP32 Hardware Profile | Key Sensors & Actuators | Local Home Assistant Entities |
| :--- | :--- | :--- | :--- |
| **GreenhouseControl-io**| ESP32-WROOM / PoE | SHT31, MLX90614 (Leaf IR), PAR/DLI sensor, ridge vents | `sensor.greenhouse_canopy_leaf_vpd`<br>`sensor.greenhouse_daily_light_integral_dli`<br>`switch.greenhouse_exhaust_fan_relay` |
| **HydroControl-io** | ESP32 + Galvanic Isolators | Isolated analog/UART pH & EC, peristaltic stepper pumps | `sensor.hydro_dwc_reservoir_ph`<br>`sensor.hydro_dwc_reservoir_ec`<br>`switch.hydro_doser_ph_down_pump` |
| **SoilSense-io** | ESP32 + RS485 Modbus | 7-in-1 Modbus probe (Moisture, Temp, EC, pH, N, P, K) | `sensor.soil_field_alpha_nitrogen`<br>`sensor.soil_field_alpha_moisture`<br>`sensor.soil_field_alpha_ph` |
| **CompostControl-io** | ESP32 + 1-Wire Bus (DS18B20) | Multi-depth stainless probe array, aerated blower | `sensor.compost_pile_core_temp_c`<br>`sensor.compost_pile_ambient_delta`<br>`switch.compost_aeration_blower` |

### Domain 4: Animal Care & Homestead Infrastructure
| Subsystem | ESP32 Hardware Profile | Key Sensors & Actuators | Local Home Assistant Entities |
| :--- | :--- | :--- | :--- |
| **LivestockCare-io** | WT32-ETH01 + Waterproof Temp | Heated trough relay, float switch, automated feeder | `sensor.livestock_trough_water_temp_c`<br>`binary_sensor.livestock_trough_low_water`<br>`switch.livestock_trough_heater_relay` |
| **PantryControl-io** | ESP32 + HX711 Load Cell ADC | Bulk weight scales (grain/flour), root cellar SHT31 | `sensor.pantry_bulk_flour_weight_lbs`<br>`sensor.pantry_root_cellar_temp`<br>`sensor.pantry_root_cellar_humidity` |
| **WorkshopControl-io** | ESP32 + Current Transformers | Tool power sense, automatic blast gate servos | `switch.workshop_blast_gate_table_saw`<br>`switch.workshop_dust_collector_main`<br>`binary_sensor.workshop_air_compressor_running` |
| **WasteControl-io** | ESP32 Deep Sleep + BLE | Ultrasonic fill level (JSN-SR04T), BLE beacon presence | `sensor.waste_trash_fill_percent`<br>`sensor.waste_compost_fill_percent`<br>`binary_sensor.waste_bin_curbside_placed` |
| **TransportControl-io** | ESP32 BLE / mmWave | Vehicle BLE presence, garage ultrasonic parking guide | `device_tracker.transport_truck_ble`<br>`device_tracker.transport_tractor_ble`<br>`sensor.transport_garage_bay_distance_in` |
| **SecurityControl-io** | ESP32 + 24GHz mmWave radar | LD2410 radar, perimeter IR beams, gate lockout | `binary_sensor.security_perimeter_alarm`<br>`binary_sensor.security_north_beam_break`<br>`switch.security_gate_lockout` |
| **LightingControl-io** | ESP32 + PCA9685 / DALI | Low-voltage 12V/24V constant-voltage PWM, DALI bus | `light.lighting_perimeter_security_led`<br>`light.lighting_greenhouse_supplemental_led`<br>`light.lighting_barn_high_bay` |

### Domain 5: Atmosphere & Climate
| Subsystem | ESP32 Hardware Profile | Key Sensors & Actuators | Local Home Assistant Entities |
| :--- | :--- | :--- | :--- |
| **ClimateControl-io** | ESP32 + Thermostat Relays | Multi-stage HVAC, radiant heating, wood stove flue temp | `climate.homestead_main_hvac`<br>`sensor.climate_woodstove_flue_temp`<br>`switch.climate_fresh_air_damper` |
| **AirQuality-io** | ESP32 + I2C Bus | Sensirion SPS30 (PM2.5/10), SCD40 (NDIR CO2), VOC | `sensor.air_quality_indoor_pm2_5`<br>`sensor.air_quality_indoor_co2_ppm`<br>`switch.air_quality_scrubber_hvac` |
| **FanControl.io** | ESP32 (LEDC Timer) | 25kHz Intel 4-wire PWM driver, RPM tachometer | `fan.fan_rack_exhaust_pwm`<br>`sensor.fan_rack_exhaust_rpm`<br>`fan.fan_greenhouse_circulation_pwm` |

### Domain 6: Master Control & Data Engine
| Subsystem | Core Role | Local Home Assistant Entities |
| :--- | :--- | :--- |
| **Control-io** | Master supervisor coordinating cross-domain priority rules | `switch.homestead_master_irrigation_enable`<br>`switch.homestead_master_solar_priority`<br>`switch.homestead_grid_island_mode` |
| **DataHub-io** | Local-first time-series telemetry aggregator & storage | `sensor.datahub_local_db_size_mb`<br>`sensor.datahub_nvme_storage_free_gb`<br>`button.datahub_trigger_local_export` |

---

## 🛠️ 4. ESP32 Electrical Safety & Pin Assignment Matrix

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

## 🔄 5. Cross-Subsystem Interlocks Orchestrated by Control-io

```
+---------------------------------------------------------------------------------+
|                                 CONTROL-IO MATRIX                               |
+------------------------------------+--------------------------------------------+
| TRIGGER CONDITION                  | AUTONOMOUS EDGE ACTION                     |
+------------------------------------+--------------------------------------------+
| Battery SoC < 25%                  | LoadBalancer sheds secondary HVAC; locks   |
|                                    | out WellPump non-essential irrigation.     |
+------------------------------------+--------------------------------------------+
| Solar Excess > 1,500W              | SolarControl diverts to hot water SSR;     |
|                                    | WaterTankControl tops off storage cisterns.|
+------------------------------------+--------------------------------------------+
| RainHarvest registers > 0.5"       | SprinklerController & GardenControl engage |
| precipitation                      | 48-hour rain delay lockout.                |
+------------------------------------+--------------------------------------------+
| Ambient Temp < 2°C (35.6°F)        | LivestockCare activates heated trough SSR; |
|                                    | SprinklerController drains exposed lines.  |
+------------------------------------+--------------------------------------------+
| Greenhouse VPD > 1.6 kPa           | FanControl ramps circulation fans to 80%;  |
|                                    | HydroControl initiates low-volume misting. |
+------------------------------------+--------------------------------------------+
| Filter Differential Press > 15 PSI | FiltrationControl triggers backwash cycle  |
|                                    | and notifies operator via Home Assistant.  |
+------------------------------------+--------------------------------------------+
```
