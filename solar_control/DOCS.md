# SolarControl-io Add-on Documentation

## Quick Start Guide

### 1. Configuration
Navigate to the **Configuration** tab in the Home Assistant Add-on panel:

- **operating_mode**:
  - `auto`: Full intelligent dispatch combining self-consumption, TOU arbitrage, and dynamic excess solar routing.
  - `self_consumption`: Keeps battery charging when solar > load, discharges when load > solar to zero grid import.
  - `tou_arbitrage`: Follows strict Time-of-Use windows to minimize cost.
  - `backup_reserve`: Holds or charges battery to 100% in preparation for grid loss.
  - `manual`: Passthrough monitoring only; no automatic controls asserted.

- **solar**:
  - `inverter_power_sensor`: Instantaneous solar generation in Watts (`sensor.*`).
  - `daily_yield_sensor`: Cumulative daily solar yield in kWh (`sensor.*`).
  - `forecast_sensor`: Solar forecast for today in kWh (`sensor.*`).

- **battery**:
  - `enabled`: Set to `true` if you have a home battery (BESS).
  - `power_sensor`: Battery power in Watts (Positive = Charging, Negative = Discharging).
  - `soc_sensor`: Battery State of Charge in % (`sensor.*`).
  - `min_soc_reserve`: Lowest allowable SoC floor before grid import is forced.
  - `max_soc_limit`: Maximum SoC limit for battery longevity (typically 90-100%).

- **grid**:
  - `meter_power_sensor`: Utility meter power in Watts (Positive = Import, Negative = Export).
  - `zero_export`: Disallow any power export to the grid.
  - `max_export_power_w`: Export ceiling for grid compliance.

- **tariff**:
  - `dynamic_pricing_enabled`: Enable real-time wholesale pricing responses.
  - `price_sensor`: Current import electricity price (e.g. from Tibber, Nord Pool, Amber Electric).
  - `export_price_sensor`: Current feed-in tariff / export price.
  - `negative_price_curtailment`: Curtail export or divert excess solar when export price < 0.

- **diversions**:
  - Add your smart appliances, EVSE, or water heaters with their respective priority levels.

### 2. Ingress Dashboard
Open the add-on from your Home Assistant sidebar to view:
- Live animated Power Flow diagram.
- Real-time battery status, solar generation, grid interaction, and home loads.
- Mode selectors and manual overrides.
