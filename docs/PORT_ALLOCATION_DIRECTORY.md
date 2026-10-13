# MyHomeStead.io: Dedicated Port Allocation Directory

> **Safe, non-conflicting port allocation map for all 26 services in the MyHomeStead.io ecosystem.**  
> Sorted in priority order by **services most prevalent on a farm, homestead, or villa**.

---

## 🛡️ Why the `8700–8726` Range?

Common ports to **avoid** in IoT and Home Assistant environments:
* `80`, `443`: Standard HTTP/HTTPS
* `1883`, `8883`: MQTT / MQTTS (Mosquitto)
* `53`, `5353`: DNS (Pi-hole/AdGuard) and mDNS / Avahi
* `5432`, `3306`, `6379`, `8086`: Default database ports (Postgres, MariaDB, Redis, InfluxDB)
* `6053`: ESPHome Native API (Noise Protocol)
* `8080`, `8443`: Unifi Controller, general reverse proxies
* `8123`: Home Assistant Core Web Interface
* `9000`: Portainer / Docker management

The **`8700–8799` block** is a clean, unassigned user port range according to IANA guidelines. It provides 100% collision-free operation across local LANs, Docker bridges, and Home Assistant Ingress.

---

## 📋 Master Homestead Port Allocation Map

| Port | Service Subsystem | Farm / Homestead / Villa Function | Protocol | Default Ingress Path |
| :---: | :--- | :--- | :---: | :--- |
| **8700** | **Control-io** | **Master Sovereign Hub & Cross-System Orchestrator** | HTTP / WS | `/` (Supervisor Ingress) |
| **8701** | **SolarControl-io** | Solar PV Inverters & Excess Immersion Diversion | HTTP / REST | `/` (Solar Dashboard) |
| **8702** | **BatteryBankControl-io**| Stationary LiFePO4 Battery Storage & BMS Bridge | HTTP / REST | `/` (BMS Manager) |
| **8703** | **BackupPower-io** | Grid Outage Sensing, ATS & Generator Auto-Start | HTTP / REST | `/` (Power Islanding) |
| **8704** | **LoadBalancer-io** | Service Entrance Current Balancing & EVSE Pilot | HTTP / REST | `/` (Panel Balancer) |
| **8705** | **WellPumpControl-io** | Submersible Borehole Depth & Pressure Management | HTTP / REST | `/` (Well Telemetry) |
| **8706** | **WaterTankControl-io** | Bulk Cistern Storage & Automated Transfer Pumps | HTTP / REST | `/` (Cistern Monitor) |
| **8707** | **FiltrationControl-io**| Potable Water Treatment, UV & Auto-Backwash | HTTP / REST | `/` (Filtration UI) |
| **8708** | **SprinklerController-io**| Multi-Zone 24VAC Lawn & Turf Irrigation | HTTP / REST | `/` (Zone Sequencer) |
| **8709** | **GardenControl-io** | Raised-Bed Drip Lines & $ET_0$ Water Budgets | HTTP / REST | `/` (Garden Planner) |
| **8710** | **RainHarvest-io** | Roof Catchment, First-Flush Purge & Rain Gauges | HTTP / REST | `/` (Rain Analytics) |
| **8711** | **ClimateControl-io** | Multi-Zone HVAC, Hydronic Floors & Woodstove Flue | HTTP / REST | `/` (Climate Hub) |
| **8712** | **AirQuality-io** | Particulate (PM2.5), True NDIR CO2 & Scrubbers | HTTP / REST | `/` (Air Station) |
| **8713** | **SecurityControl-io** | Perimeter Radar, IR Beams, Gates & Sirens | HTTP / REST | `/` (Security Console) |
| **8714** | **LightingControl-io** | Circadian Biological Lighting & Security Floods | HTTP / REST | `/` (Lighting Matrix) |
| **8715** | **WasteControl-io** | Trash, Recycling, Compost Fill & Curbside BLE | HTTP / REST | `/` (Bin Logistics) |
| **8716** | **TransportControl-io** | Farm Truck, Tractor & Fleet Equipment Presence | HTTP / REST | `/` (Fleet Monitor) |
| **8717** | **WorkshopControl-io** | Machine Safety, Auto Blast Gates & Compressors | HTTP / REST | `/` (Shop Console) |
| **8718** | **PantryControl-io** | Bulk Grain/Flour Load Cells & Root Cellar Temp | HTTP / REST | `/` (Pantry Inventory) |
| **8719** | **LivestockCare-io** | Heated Water Troughs & Predator-Proof Coops | HTTP / REST | `/` (Livestock Hub) |
| **8720** | **CompostControl-io** | Core Temperature Probes & Aerated Static Piles | HTTP / REST | `/` (Compost Monitor) |
| **8721** | **SoilSense-io** | RS485 Modbus 7-in-1 Soil NPK Telemetry Array | HTTP / REST | `/` (Soil Analytics) |
| **8722** | **GreenhouseControl-io**| Canopy VPD, Leaf IR, PAR/DLI & Ridge Vents | HTTP / REST | `/` (Greenhouse Console)|
| **8723** | **HydroControl-io** | Closed-Loop Hydroponics, pH & Nutrient Dosing | HTTP / REST | `/` (Dosing Controller)|
| **8724** | **FanControl.io** | 25kHz Intel PWM Server Rack & Shed Ventilation | HTTP / REST | `/` (Fan Tachometer) |
| **8725** | **DataHub-io** | Local Sovereign Telemetry Explorer & Export API | HTTP / REST | `/` (DataHub UI) |
| **8726** | **DataHub-io (Ingest)**| Direct High-Throughput TCP Telemetry Socket | TCP / Stream| `tcp://localhost:8726` |

---

## ⚙️ Configuration Standard in Add-on `config.yaml`

To ensure uniform deployments, every add-on in the suite declares its dedicated port under `ingress_port` and optional direct host binding:

```yaml
ingress: true
ingress_port: 8708
panel_icon: "mdi:sprinkler-variant"
panel_title: "Sprinklers"
network:
  8708/tcp: 8708
```
