from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class PowerFlowState:
    solar_w: float = 0.0
    battery_w: float = 0.0       # Positive = Charging, Negative = Discharging
    grid_w: float = 0.0          # Positive = Import, Negative = Export
    home_w: float = 0.0          # Domestic consumption
    ev_w: float = 0.0            # EV Charging consumption
    diverted_w: float = 0.0      # Active excess diversion consumption
    battery_soc: float = 0.0     # 0 - 100 %
    daily_solar_kwh: float = 0.0
    forecast_today_kwh: float = 0.0
    self_consumption_pct: float = 0.0
    self_sufficiency_pct: float = 0.0

@dataclass
class DiversionLoadState:
    name: str
    type: str
    entity_id: str
    priority: int
    is_active: bool = False
    current_power_w: float = 0.0
    allocated_power_w: float = 0.0
    min_power_w: float = 0.0
    max_power_w: float = 3000.0

@dataclass
class TariffState:
    enabled: bool = False
    import_price: float = 0.0
    export_price: float = 0.0
    is_negative_export: bool = False
    current_window: str = "standard" # off_peak | standard | peak | critical_peak

@dataclass
class EnergySystemState:
    operating_mode: str = "auto"
    status_message: str = "Optimal Dispatch Active"
    power_flow: PowerFlowState = field(default_factory=PowerFlowState)
    tariff: TariffState = field(default_factory=TariffState)
    diversions: List[DiversionLoadState] = field(default_factory=list)
