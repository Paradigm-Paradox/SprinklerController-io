import json
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

OPTIONS_PATH = Path("/data/options.json")

class ZoneConfig(BaseModel):
    name: str = "Main Zone"
    target_vpd_min: float = 0.8
    target_vpd_max: float = 1.2
    temp_sensor: Optional[str] = ""
    humidity_sensor: Optional[str] = ""
    leaf_temp_sensor: Optional[str] = ""
    leaf_temp_offset: float = -2.0
    heater_switch: Optional[str] = ""
    cooler_switch: Optional[str] = ""
    exhaust_fan_switch: Optional[str] = ""
    humidifier_switch: Optional[str] = ""
    irrigation_valve: Optional[str] = ""
    soil_moisture_sensor: Optional[str] = ""
    soil_moisture_target: float = 45.0

class AppConfig(BaseModel):
    log_level: str = "info"
    refresh_interval: int = 30
    zones: List[ZoneConfig] = Field(default_factory=lambda: [ZoneConfig()])

def load_config() -> AppConfig:
    if OPTIONS_PATH.is_file():
        try:
            with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception as e:
            print(f"Warning: Failed to parse /data/options.json: {e}")
    
    # Default fallback
    return AppConfig()
