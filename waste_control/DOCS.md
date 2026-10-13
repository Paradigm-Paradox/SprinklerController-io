# WasteControl-io: User Documentation

## Configuration Reference

### MQTT Broker
Configure connection parameters to your Home Assistant MQTT broker (e.g., Mosquitto add-on):
- `enabled`: Enable/disable MQTT publishing and auto-discovery.
- `host`: Broker hostname (default `core-mosquitto`).
- `port`: Broker port (default `1883`).
- `topic_prefix`: Root MQTT topic (default `wastecontrol`).

### Waste Streams
Define each collection stream active on your property:
- `id`: Unique identifier (e.g. `trash`, `recycling`, `organics`).
- `name`: Display name in Home Assistant.
- `color`: Hex color used in dashboards and badge cards.
- `schedule_type`:
  - `weekly`: Every week on `pickup_day`.
  - `biweekly_even`: Alternating weeks (even ISO week numbers).
  - `biweekly_odd`: Alternating weeks (odd ISO week numbers).
  - `monthly`: First occurrence of `pickup_day` in each month.
- `pickup_day`: Day of week (`Monday` - `Sunday`).
- `holiday_delay`: Automatically shifts pickup by +1 day when a municipal holiday occurs earlier in the week.
- `bin_monitor`: Enables fill level and location tracking for physical carts.
- `empty_depth_cm`: Total internal depth of the can in centimeters (default: 95 cm).
- `full_depth_cm`: Distance below lid when bin is considered 100% full (default: 15 cm).

## REST API Endpoints

- `GET /api/status`: Returns current status of all streams, next pickup dates, and bin telemetry.
- `POST /api/bin/{stream_id}/location`: Sets bin location (`{"location": "storage" | "curb" | "transit"}`).
- `POST /api/bin/{stream_id}/reading`: Posts raw sensor distance (`{"distance_cm": 42.5}`).
