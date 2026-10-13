from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Zone(BaseModel):
    id: str
    name: str
    valve_entity: Optional[str] = ""
    moisture_sensor_entity: Optional[str] = ""
    cycle_minutes: int = 8
    soak_minutes: int = 15
    max_duration_minutes: int = 45
    flow_rate_lpm: float = 12.0
    is_enabled: bool = True

class ZoneCreate(BaseModel):
    id: str
    name: str
    valve_entity: Optional[str] = ""
    moisture_sensor_entity: Optional[str] = ""
    cycle_minutes: int = 8
    soak_minutes: int = 15
    max_duration_minutes: int = 45
    flow_rate_lpm: float = 12.0

class Bed(BaseModel):
    id: str
    zone_id: Optional[str] = None
    name: str
    bed_type: str = "raised_bed"
    width_cm: float = 120.0
    length_cm: float = 240.0
    depth_cm: float = 30.0
    soil_type: str = "loam"
    soil_sensor_entity: Optional[str] = None
    moisture_target_pct: float = 45.0

class BedCreate(BaseModel):
    id: str
    zone_id: Optional[str] = None
    name: str
    bed_type: str = "raised_bed"
    width_cm: float = 120.0
    length_cm: float = 240.0
    depth_cm: float = 30.0
    soil_type: str = "loam"
    moisture_target_pct: float = 45.0

class CropCatalogItem(BaseModel):
    id: str
    common_name: str
    botanical_name: Optional[str] = None
    category: str = "vegetable"
    days_to_germinate: Optional[int] = None
    days_to_maturity: Optional[int] = None
    sun_exposure: str = "full_sun"
    water_demand: str = "medium"
    kc_initial: float = 0.5
    kc_mid: float = 1.0
    kc_late: float = 0.8
    root_depth_cm: float = 30.0
    spacing_cm: float = 30.0
    beneficial_companions: Optional[str] = ""
    antagonist_plants: Optional[str] = ""

class Planting(BaseModel):
    id: str
    bed_id: str
    crop_id: str
    common_name: Optional[str] = None
    category: Optional[str] = None
    x_cm: float = 0.0
    y_cm: float = 0.0
    quantity: int = 1
    planted_at: date
    current_stage: str = "vegetative"
    expected_harvest: Optional[date] = None
    notes: Optional[str] = None

class PlantingCreate(BaseModel):
    bed_id: str
    crop_id: str
    x_cm: float = 0.0
    y_cm: float = 0.0
    quantity: int = 1
    planted_at: date = Field(default_factory=date.today)
    current_stage: str = "vegetative"
    notes: Optional[str] = None

class IrrigationTriggerRequest(BaseModel):
    duration_minutes: Optional[int] = None
    use_cycle_and_soak: bool = True

class SystemStatus(BaseModel):
    version: str
    uptime_seconds: float
    active_runs: List[dict]
    cistern_level_pct: Optional[float]
    solar_power_watts: Optional[float]
    daily_et0_mm: float
    water_used_today_liters: float
    weather_delay_active: bool
