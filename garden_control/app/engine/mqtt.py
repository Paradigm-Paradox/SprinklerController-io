import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("gardencontrol.mqtt")

class MQTTManager:
    """Manages Home Assistant MQTT Discovery for garden zones, moisture, and controls."""

    def __init__(self, host: str = "core-mosquitto", port: int = 1883, prefix: str = "homeassistant"):
        self.host = os.environ.get("MQTT_HOST", host)
        self.port = int(os.environ.get("MQTT_PORT", port))
        self.username = os.environ.get("MQTT_USER", "")
        self.password = os.environ.get("MQTT_PASSWORD", "")
        self.prefix = prefix
        self.is_connected = False

    def build_discovery_payloads(self, zone_id: str, zone_name: str) -> Dict[str, Any]:
        """Generate Home Assistant MQTT discovery topics and configs for a zone."""
        device_info = {
            "identifiers": [f"gardencontrol_{zone_id}"],
            "name": f"Garden Zone: {zone_name}",
            "manufacturer": "Paradigm Paradox",
            "model": "GardenControl-io Node",
            "sw_version": "0.1.0"
        }

        # Valve / Switch entity
        valve_config = {
            "name": f"{zone_name} Irrigation",
            "unique_id": f"gardencontrol_{zone_id}_valve",
            "command_topic": f"gardencontrol/{zone_id}/set",
            "state_topic": f"gardencontrol/{zone_id}/state",
            "payload_on": "ON",
            "payload_off": "OFF",
            "icon": "mdi:sprinkler-variant",
            "device": device_info
        }

        # Daily Water Consumption sensor
        water_sensor_config = {
            "name": f"{zone_name} Water Applied Today",
            "unique_id": f"gardencontrol_{zone_id}_water_today",
            "state_topic": f"gardencontrol/{zone_id}/telemetry",
            "value_template": "{{ value_json.liters_today }}",
            "unit_of_measurement": "L",
            "device_class": "water",
            "state_class": "total_increasing",
            "icon": "mdi:water",
            "device": device_info
        }

        return {
            f"{self.prefix}/switch/gardencontrol_{zone_id}/config": valve_config,
            f"{self.prefix}/sensor/gardencontrol_{zone_id}_water/config": water_sensor_config
        }
