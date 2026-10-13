import json
import logging
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("gardencontrol.config")

OPTIONS_PATH = Path("/data/options.json")
LOCAL_FALLBACK_OPTIONS = Path("./options.json")

class ZoneConfig(BaseModel):
    id: str = "zone_1"
    name: str = "Main Vegetable Beds"
    valve_entity: Optional[str] = ""
    moisture_sensor_entity: Optional[str] = ""
    cycle_minutes: int = 8
    soak_minutes: int = 15
    max_duration_minutes: int = 45
    flow_rate_lpm: float = 12.0

class AppConfig(BaseModel):
    log_level: str = "info"
    weather_entity: Optional[str] = ""
    cistern_sensor_entity: Optional[str] = ""
    cistern_minimum_pct: float = 15.0
    max_concurrent_zones: int = 1
    solar_coordination_enabled: bool = False
    solar_power_entity: Optional[str] = ""
    cycle_and_soak_default: bool = True
    database_path: str = "/data/gardencontrol.db"
    zones: List[ZoneConfig] = Field(default_factory=lambda: [ZoneConfig()])

def load_config() -> AppConfig:
    """Load configuration from Home Assistant /data/options.json or local development fallback."""
    config_file = None
    if OPTIONS_PATH.is_file():
        config_file = OPTIONS_PATH
    elif LOCAL_FALLBACK_OPTIONS.is_file():
        config_file = LOCAL_FALLBACK_OPTIONS

    if config_file:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception as e:
            logger.warning("Failed to parse config from %s: %s", config_file, e)

    # In dev mode, fall back to SQLite in local directory if /data does not exist
    default_cfg = AppConfig()
    if not os.path.exists("/data") and not os.access("/", os.W_OK):
        default_cfg.database_path = "./gardencontrol.db"
    return default_cfg
