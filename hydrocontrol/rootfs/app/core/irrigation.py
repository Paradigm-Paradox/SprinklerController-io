import asyncio
import time
import logging
from typing import Dict, Any
from .ha_client import HomeAssistantClient

logger = logging.getLogger("hydrocontrol.irrigation")

class IrrigationController:
    def __init__(self, config: Dict[str, Any], ha_client: HomeAssistantClient):
        self.config = config
        self.ha_client = ha_client
        self.current_state: str = "OFF"
        self.state_since: float = time.time()

    async def update(self):
        irr_cfg = self.config.get("irrigation", {})
        pump_entity = irr_cfg.get("pump_entity", "")
        if not pump_entity:
            return

        mode = irr_cfg.get("mode", "continuous")
        now = time.time()
        elapsed_minutes = (now - self.state_since) / 60.0
        domain = pump_entity.split(".")[0]

        if mode == "continuous":
            if self.current_state != "ON":
                await self.ha_client.call_service(domain, "turn_on", {"entity_id": pump_entity})
                self.current_state = "ON"
                self.state_since = now
                logger.info("Continuous irrigation pump activated.")

        elif mode in ("cycle", "flood_drain"):
            cycle_on = irr_cfg.get("cycle_on_minutes", 15)
            cycle_off = irr_cfg.get("cycle_off_minutes", 45)

            if self.current_state == "ON" and elapsed_minutes >= cycle_on:
                await self.ha_client.call_service(domain, "turn_off", {"entity_id": pump_entity})
                self.current_state = "OFF"
                self.state_since = now
                logger.info("Irrigation cycle: Pump turned OFF after %d mins.", cycle_on)

            elif self.current_state == "OFF" and elapsed_minutes >= cycle_off:
                await self.ha_client.call_service(domain, "turn_on", {"entity_id": pump_entity})
                self.current_state = "ON"
                self.state_since = now
                logger.info("Irrigation cycle: Pump turned ON for next %d min cycle.", cycle_on)
