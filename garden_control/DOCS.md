# Home Assistant Add-on: GardenControl-io

GardenControl-io is an edge-native garden and irrigation orchestration system designed for raised beds, in-ground gardens, and smart homesteads.

## Features
- **Adaptive Evapotranspiration Irrigation**: Waters dynamically based on crop coefficient, weather forecasts, and solar conditions.
- **Cycle & Soak**: Minimizes soil compaction and runoff by pulsing water delivery.
- **Companion Planting Intelligence**: Guides optimal plant groupings and flags antagonistic plant combinations.
- **Home Assistant Ingress Dashboard**: Manage beds, monitor moisture, and control valves directly within your HA sidebar.
- **Cistern & Solar Coordination**: Cooperates with `WaterTankControl-io` and `SolarControl-io` to safeguard water supplies and prioritize solar power.

## Configuration Options
- `weather_entity`: (Optional) The entity ID of your local weather integration (e.g. `weather.home`).
- `cistern_sensor_entity`: (Optional) Entity reporting cistern water level percentage (e.g. `sensor.cistern_level`).
- `cistern_minimum_pct`: Minimum cistern water level before non-essential irrigation is suspended (default: `15.0`).
- `max_concurrent_zones`: Maximum number of valve circuits active at the exact same moment (default: `1`).
- `solar_coordination_enabled`: Prioritize running booster pumps during peak solar production.
- `zones`: Array of zone definitions with valve entities, moisture sensors, and cycle/soak durations.

## Troubleshooting & Support
Check the Home Assistant Add-on log tab for real-time engine logs, watchdog events, and cycle transitions.
