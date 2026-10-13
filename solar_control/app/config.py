import json
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

OPTIONS_PATH = Path("/data/options.json")

class SolarConfig(BaseModel):
    inverter_power_sensor: Optional[str] = ""
    daily_yield_sensor: Optional[str] = ""
    forecast_sensor: Optional[str] = ""

class BatteryConfig(BaseModel):
    enabled: bool = False
    power_sensor: Optional[str] = ""
    soc_sensor: Optional[str] = ""
    min_soc_reserve: int = 20
    max_soc_limit: int = 95
    max_charge_power_w: int = 5000
    max_discharge_power_w: int = 5000
    charge_rate_entity: Optional[str] = ""
    discharge_rate_entity: Optional[str] = ""

class GridConfig(BaseModel):
    meter_power_sensor: Optional[str] = ""
    zero_export: bool = False
    max_export_power_w: int = 10000

class TariffConfig(BaseModel):
    dynamic_pricing_enabled: bool = False
    price_sensor: Optional[str] = ""
    export_price_sensor: Optional[str] = ""
    negative_price_curtailment: bool = True

class DiversionConfig(BaseModel):
    name: str
    type: str = "switch" # switch | pwm_diverter | evse | climate
    entity_id: str
    power_sensor: Optional[str] = ""
    priority: int = 1
    min_power_w: int = 0
    max_power_w: int = 3000

class AppConfig(BaseModel):
    log_level: str = "info"
    refresh_interval: int = 5
    operating_mode: str = "auto"
    solar: SolarConfig = Field(default_factory=SolarConfig)
    battery: BatteryConfig = Field(default_factory=BatteryConfig)
    grid: GridConfig = Field(default_factory=GridConfig)
    tariff: TariffConfig = Field(default_factory=TariffConfig)
    diversions: List[DiversionConfig] = Field(default_factory=list)

def load_config() -> AppConfig:
    if OPTIONS_PATH.is_file():
        try:
            with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception as e:
            print(f"Warning: Failed to parse {OPTIONS_PATH}: {e}")
    return AppConfig()
