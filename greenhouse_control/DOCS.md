# Home Assistant Community Add-on: GreenhouseControl-io

GreenhouseControl-io provides autonomous climate, VPD, and irrigation management.

## Configuration

In the add-on **Configuration** tab:
1. Specify your target VPD range (e.g. `0.8` to `1.2` kPa).
2. Link your Home Assistant air temperature and relative humidity sensor entity IDs (e.g., `sensor.greenhouse_temperature`, `sensor.greenhouse_humidity`).
3. (Optional) Provide an infrared leaf temperature sensor or use the default offset (-2.0°C).
4. Assign switches/relays for heating, cooling, exhaust, and humidification.
5. Save and restart the add-on.

Open the Web UI in the Home Assistant sidebar to monitor telemetry and manual overrides.
