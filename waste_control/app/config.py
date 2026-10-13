import os
import json
import logging
from typing import List, Optional

logger = logging.getLogger("WasteControl.Config")

class StreamConfig:
    def __init__(
        self,
        id: str,
        name: str,
        color: str = "#2E7D32",
        schedule_type: str = "weekly",
        pickup_day: str = "Tuesday",
        holiday_delay: bool = True,
        bin_monitor: bool = True,
        empty_depth_cm: float = 95.0,
        full_depth_cm: float = 15.0
    ):
        self.id = id
        self.name = name
        self.color = color
        self.schedule_type = schedule_type
        self.pickup_day = pickup_day
        self.holiday_delay = holiday_delay
        self.bin_monitor = bin_monitor
        self.empty_depth_cm = float(empty_depth_cm)
        self.full_depth_cm = float(full_depth_cm)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "schedule_type": self.schedule_type,
            "pickup_day": self.pickup_day,
            "holiday_delay": self.holiday_delay,
            "bin_monitor": self.bin_monitor,
            "empty_depth_cm": self.empty_depth_cm,
            "full_depth_cm": self.full_depth_cm
        }

class MQTTConfig:
    def __init__(
        self,
        enabled: bool = True,
        host: str = "core-mosquitto",
        port: int = 1883,
        username: str = "",
        password: str = "",
        topic_prefix: str = "wastecontrol"
    ):
        self.enabled = enabled
        self.host = host
        self.port = int(port)
        self.username = username or ""
        self.password = password or ""
        self.topic_prefix = topic_prefix

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "topic_prefix": self.topic_prefix
        }

class AppConfig:
    def __init__(self, log_level: str = "info", refresh_interval: int = 60, mqtt: Optional[MQTTConfig] = None, streams: Optional[List[StreamConfig]] = None):
        self.log_level = log_level
        self.refresh_interval = int(refresh_interval)
        self.mqtt = mqtt or MQTTConfig()
        self.streams = streams or []

    def to_dict(self):
        return {
            "log_level": self.log_level,
            "refresh_interval": self.refresh_interval,
            "mqtt": self.mqtt.to_dict(),
            "streams": [s.to_dict() for s in self.streams]
        }

def load_config() -> AppConfig:
    options_file = "/data/options.json"
    if os.path.exists(options_file):
        try:
            with open(options_file, "r") as f:
                data = json.load(f)
                
            mqtt_data = data.get("mqtt", {})
            mqtt_cfg = MQTTConfig(
                enabled=mqtt_data.get("enabled", True),
                host=mqtt_data.get("host", "core-mosquitto"),
                port=mqtt_data.get("port", 1883),
                username=mqtt_data.get("username", ""),
                password=mqtt_data.get("password", ""),
                topic_prefix=mqtt_data.get("topic_prefix", "wastecontrol")
            )
            
            streams_list = []
            for s in data.get("streams", []):
                streams_list.append(StreamConfig(
                    id=s.get("id", "stream"),
                    name=s.get("name", "Stream"),
                    color=s.get("color", "#2E7D32"),
                    schedule_type=s.get("schedule_type", "weekly"),
                    pickup_day=s.get("pickup_day", "Tuesday"),
                    holiday_delay=s.get("holiday_delay", True),
                    bin_monitor=s.get("bin_monitor", True),
                    empty_depth_cm=s.get("empty_depth_cm", 95.0),
                    full_depth_cm=s.get("full_depth_cm", 15.0)
                ))
                
            return AppConfig(
                log_level=data.get("log_level", "info"),
                refresh_interval=data.get("refresh_interval", 60),
                mqtt=mqtt_cfg,
                streams=streams_list
            )
        except Exception as e:
            logger.error(f"Error loading options.json: {e}")

    # Fallback default configuration
    return AppConfig(
        log_level="info",
        refresh_interval=60,
        mqtt=MQTTConfig(),
        streams=[
            StreamConfig(
                id="trash",
                name="Household Trash",
                color="#2E7D32",
                schedule_type="weekly",
                pickup_day="Tuesday",
                holiday_delay=True,
                bin_monitor=True
            ),
            StreamConfig(
                id="recycling",
                name="Recycling",
                color="#1565C0",
                schedule_type="biweekly_even",
                pickup_day="Tuesday",
                holiday_delay=True,
                bin_monitor=True
            ),
            StreamConfig(
                id="yard_waste",
                name="Yard Waste",
                color="#8D6E63",
                schedule_type="weekly",
                pickup_day="Wednesday",
                holiday_delay=True,
                bin_monitor=False
            )
        ]
    )
