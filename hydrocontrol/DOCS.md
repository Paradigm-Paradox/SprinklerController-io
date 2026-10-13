# Home Assistant Add-on: HydroControl-io

HydroControl-io provides closed-loop control and intelligent automation for indoor and greenhouse hydroponic systems.

## Hardware & Entity Prerequisites

Before activating automatic dosing, ensure you have configured:
- **pH Sensor:** An ESPHome, Zigbee, or analog probe publishing pH value (e.g. `sensor.reservoir_ph`).
- **EC Sensor:** An electrical conductivity sensor (e.g. `sensor.reservoir_ec`).
- **Water Temperature Sensor:** DS18B20 or similar probe (e.g. `sensor.reservoir_temp`).
- **Peristaltic Dosing Pumps:** Smart switches or ESPHome relays controlling 12V dosing pumps (e.g. `switch.pump_ph_down`, `switch.pump_nutrient_a`).
- **Main Circulation / Irrigation Pump:** Smart relay or smart plug (e.g. `switch.water_pump`).

## Configuration Options

### Section: `targets`
- `target_ph`: The ideal pH level (e.g. 5.8 - 6.2 for most hydroponic crops).
- `ph_tolerance`: Allowed drift above/below target before triggering a dose (default: 0.2).
- `target_ec_ms`: Target nutrient concentration in mS/cm.
- `ec_tolerance`: Allowed drift in mS/cm before nutrient dosing.

### Section: `dosing`
- `enabled`: Master safety switch for dosing pumps. Keep `false` until testing flow rates.
- `pump_flow_rate_ml_min`: Flow rate of your peristaltic pumps (typically 60-100 mL/min).
- `max_single_dose_ml`: Maximum volume dispensed in a single pulse.
- `dose_mixing_delay_sec`: Minimum dwell time (seconds) to allow circulation and mixing before taking a new reading (default: 900s / 15m).
- `daily_safety_cap_ml`: Hard cap on cumulative chemical dispensed per 24-hour window to protect root health.

## Ingress Web Interface

Access the live dashboard directly from the Home Assistant sidebar to:
- Monitor live pH, EC, and temperature trends
- Run calibration sequences for pH 4.01, 7.00, and 10.01 buffer solutions
- Manually prime or test dosing pumps
- View event logs and safety alerts
