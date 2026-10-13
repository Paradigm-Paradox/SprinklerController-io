import logging
from typing import Optional
from .models import PowerFlowState
from ..config import AppConfig
from ..ha_client import HAClient

logger = logging.getLogger("SolarControl.BatteryManager")

class BatteryManager:
    def __init__(self, config: AppConfig, ha_client: HAClient):
        self.config = config
        self.ha = ha_client

    async def evaluate(self, pf: PowerFlowState, mode: str) -> Optional[str]:
        if not self.config.battery.enabled:
            return "Battery storage disabled in configuration"

        soc = pf.battery_soc
        min_reserve = self.config.battery.min_soc_reserve
        max_limit = self.config.battery.max_soc_limit

        # Safety Check: Reserve Violations
        if soc <= min_reserve and pf.battery_w < 0:
            logger.info(f"Battery SoC ({soc}%) reached min reserve ({min_reserve}%). Halting discharge.")
            if self.config.battery.discharge_rate_entity:
                await self.ha.call_service("number", "set_value", {
                    "entity_id": self.config.battery.discharge_rate_entity,
                    "value": 0
                })
            return f"Battery at reserve limit ({soc}%). Discharge halted."

        # Safety Check: Max SoC Limit
        if soc >= max_limit and pf.battery_w > 0:
            logger.info(f"Battery SoC ({soc}%) reached max limit ({max_limit}%). Halting charge.")
            if self.config.battery.charge_rate_entity:
                await self.ha.call_service("number", "set_value", {
                    "entity_id": self.config.battery.charge_rate_entity,
                    "value": 0
                })
            return f"Battery at upper limit ({soc}%). Charging paused."

        # Operating Modes
        if mode == "backup_reserve":
            # Force grid/solar charging to 100%
            if self.config.battery.charge_rate_entity:
                await self.ha.call_service("number", "set_value", {
                    "entity_id": self.config.battery.charge_rate_entity,
                    "value": self.config.battery.max_charge_power_w
                })
            return "Backup Reserve Active: Maximizing battery charge"

        elif mode == "self_consumption" or mode == "auto":
            # Normal self-consumption: allow full inverter charging/discharging within limits
            if self.config.battery.charge_rate_entity:
                await self.ha.call_service("number", "set_value", {
                    "entity_id": self.config.battery.charge_rate_entity,
                    "value": self.config.battery.max_charge_power_w
                })
            if self.config.battery.discharge_rate_entity:
                await self.ha.call_service("number", "set_value", {
                    "entity_id": self.config.battery.discharge_rate_entity,
                    "value": self.config.battery.max_discharge_power_w
                })
            return "Self-Consumption Mode: Zeroing grid exchange"

        elif mode == "manual":
            return "Manual Mode: Autonomous control bypassed"

        return "Battery state nominal"
