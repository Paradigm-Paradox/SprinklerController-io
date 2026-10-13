import json
import logging
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
from ..config import AppConfig, StreamConfig
from .bin_tracker import BinState

logger = logging.getLogger("WasteControl.MQTT")

class MQTTManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = None
        self.connected = False

    def start(self):
        if not self.config.mqtt.enabled:
            logger.info("MQTT is disabled in configuration.")
            return

        try:
            self.client = mqtt.Client(
                client_id="wastecontrol_io",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            if self.config.mqtt.username:
                self.client.username_pw_set(
                    self.config.mqtt.username,
                    self.config.mqtt.password
                )
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            logger.info(f"Connecting to MQTT broker at {self.config.mqtt.host}:{self.config.mqtt.port}")
            self.client.connect_async(self.config.mqtt.host, self.config.mqtt.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.warning(f"Could not connect to MQTT broker: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Connected to MQTT broker successfully.")
            self.connected = True
            self.publish_discovery()
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        logger.warning(f"Disconnected from MQTT broker (rc: {rc})")
        self.connected = False

    def publish_discovery(self):
        """Publish Home Assistant MQTT Auto-Discovery topics for all streams."""
        if not self.connected or not self.client:
            return

        device_info = {
            "identifiers": ["wastecontrol_io"],
            "name": "WasteControl-io",
            "model": "Waste & Bin Automation Hub",
            "manufacturer": "Paradigm-Paradox",
            "sw_version": "0.1.0"
        }

        prefix = self.config.mqtt.topic_prefix

        for stream in self.config.streams:
            base_topic = f"{prefix}/{stream.id}"
            
            # Days remaining sensor
            self.client.publish(
                f"homeassistant/sensor/wastecontrol/{stream.id}_days/config",
                json.dumps({
                    "name": f"{stream.name} Days Remaining",
                    "unique_id": f"wastecontrol_{stream.id}_days_remaining",
                    "state_topic": f"{base_topic}/state",
                    "value_template": "{{ value_json.days_remaining }}",
                    "unit_of_measurement": "days",
                    "icon": "mdi:calendar-clock",
                    "device": device_info
                }),
                retain=True
            )

            # Next pickup date sensor
            self.client.publish(
                f"homeassistant/sensor/wastecontrol/{stream.id}_date/config",
                json.dumps({
                    "name": f"{stream.name} Next Pickup",
                    "unique_id": f"wastecontrol_{stream.id}_next_date",
                    "state_topic": f"{base_topic}/state",
                    "value_template": "{{ value_json.next_date }}",
                    "icon": "mdi:truck-cargo-container",
                    "device": device_info
                }),
                retain=True
            )

            if stream.bin_monitor:
                # Bin Fill Level
                self.client.publish(
                    f"homeassistant/sensor/wastecontrol/{stream.id}_fill/config",
                    json.dumps({
                        "name": f"{stream.name} Bin Fill Level",
                        "unique_id": f"wastecontrol_{stream.id}_fill_level",
                        "state_topic": f"{base_topic}/bin",
                        "value_template": "{{ value_json.fill_level_percent }}",
                        "unit_of_measurement": "%",
                        "icon": "mdi:trash-can",
                        "device": device_info
                    }),
                    retain=True
                )

                # Bin Location
                self.client.publish(
                    f"homeassistant/sensor/wastecontrol/{stream.id}_loc/config",
                    json.dumps({
                        "name": f"{stream.name} Bin Location",
                        "unique_id": f"wastecontrol_{stream.id}_location",
                        "state_topic": f"{base_topic}/bin",
                        "value_template": "{{ value_json.location }}",
                        "icon": "mdi:map-marker-radius",
                        "device": device_info
                    }),
                    retain=True
                )

    def publish_state(self, stream_id: str, schedule_data: Dict[str, Any], bin_data: Optional[BinState]):
        if not self.connected or not self.client:
            return

        prefix = self.config.mqtt.topic_prefix
        base_topic = f"{prefix}/{stream_id}"

        self.client.publish(f"{base_topic}/state", json.dumps(schedule_data), retain=True)

        if bin_data:
            self.client.publish(f"{base_topic}/bin", json.dumps(bin_data.to_dict()), retain=True)
