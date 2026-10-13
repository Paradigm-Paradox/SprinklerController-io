import logging
from typing import Dict, Any
from .models import PowerFlowState
from ..config import AppConfig
from ..ha_client import HAClient

logger = logging.getLogger("SolarControl.PowerFlow")

class PowerFlowEngine:
    def __init__(self, config: AppConfig, ha_client: HAClient):
        self.config = config
        self.ha = ha_client

    async def calculate(self) -> PowerFlowState:
        # 1. Fetch Solar PV
        solar_w = 0.0
        if self.config.solar.inverter_power_sensor:
            solar_w = max(0.0, await self.ha.get_numeric_state(self.config.solar.inverter_power_sensor))

        daily_solar_kwh = 0.0
        if self.config.solar.daily_yield_sensor:
            daily_solar_kwh = await self.ha.get_numeric_state(self.config.solar.daily_yield_sensor)

        forecast_kwh = 0.0
        if self.config.solar.forecast_sensor:
            forecast_kwh = await self.ha.get_numeric_state(self.config.solar.forecast_sensor)

        # 2. Fetch Battery
        battery_w = 0.0
        battery_soc = 0.0
        if self.config.battery.enabled:
            if self.config.battery.power_sensor:
                battery_w = await self.ha.get_numeric_state(self.config.battery.power_sensor)
            if self.config.battery.soc_sensor:
                battery_soc = await self.ha.get_numeric_state(self.config.battery.soc_sensor)

        # 3. Fetch Grid
        grid_w = 0.0
        if self.config.grid.meter_power_sensor:
            grid_w = await self.ha.get_numeric_state(self.config.grid.meter_power_sensor)

        # 4. Fetch Diversions & EV Loads
        diverted_w = 0.0
        ev_w = 0.0
        for div in self.config.diversions:
            if div.power_sensor:
                p = max(0.0, await self.ha.get_numeric_state(div.power_sensor))
                if div.type == "evse":
                    ev_w += p
                else:
                    diverted_w += p

        # 5. Compute Home Base Consumption
        # Energy balance: Generation + Net Grid In + Battery Discharge = Consumption
        # P_home = P_pv + P_grid - P_batt - P_ev - P_diverted (where P_batt > 0 is charging, so subtract)
        raw_home = solar_w + grid_w - battery_w - ev_w - diverted_w
        home_w = max(0.0, raw_home)

        # 6. Self-consumption and self-sufficiency percentages
        # Self-consumption: (Solar generated that was used locally: to home, batt, ev, diversions) / total solar
        local_solar_used = max(0.0, solar_w - max(0.0, -grid_w))
        self_consumption_pct = (local_solar_used / solar_w * 100.0) if solar_w > 50.0 else 100.0
        self_consumption_pct = min(100.0, max(0.0, self_consumption_pct))

        # Self-sufficiency: (Total home + ev + div covered by solar + batt) / total consumption
        total_load = home_w + ev_w + diverted_w
        grid_import = max(0.0, grid_w)
        covered_locally = max(0.0, total_load - grid_import)
        self_sufficiency_pct = (covered_locally / total_load * 100.0) if total_load > 50.0 else 100.0
        self_sufficiency_pct = min(100.0, max(0.0, self_sufficiency_pct))

        return PowerFlowState(
            solar_w=round(solar_w, 1),
            battery_w=round(battery_w, 1),
            grid_w=round(grid_w, 1),
            home_w=round(home_w, 1),
            ev_w=round(ev_w, 1),
            diverted_w=round(diverted_w, 1),
            battery_soc=round(battery_soc, 1),
            daily_solar_kwh=round(daily_solar_kwh, 2),
            forecast_today_kwh=round(forecast_kwh, 2),
            self_consumption_pct=round(self_consumption_pct, 1),
            self_sufficiency_pct=round(self_sufficiency_pct, 1),
        )
