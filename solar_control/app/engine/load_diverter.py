import logging
import time
from typing import List, Dict
from .models import PowerFlowState, DiversionLoadState
from ..config import AppConfig, DiversionConfig
from ..ha_client import HAClient

logger = logging.getLogger("SolarControl.LoadDiverter")

class LoadDiverter:
    def __init__(self, config: AppConfig, ha_client: HAClient):
        self.config = config
        self.ha = ha_client
        self._last_state_change: Dict[str, float] = {}
        self.min_cycle_time_s = 60 # Prevent rapid on/off toggling

    async def evaluate(self, pf: PowerFlowState) -> List[DiversionLoadState]:
        # Grid export is negative grid_w. Available surplus:
        surplus_w = max(0.0, -pf.grid_w)
        now = time.time()

        results: List[DiversionLoadState] = []
        # Sort diversions by configured priority (1 is highest)
        sorted_diversions = sorted(self.config.diversions, key=lambda x: x.priority)

        remaining_surplus = surplus_w

        for div in sorted_diversions:
            load_state = DiversionLoadState(
                name=div.name,
                type=div.type,
                entity_id=div.entity_id,
                priority=div.priority,
                min_power_w=float(div.min_power_w),
                max_power_w=float(div.max_power_w)
            )

            # Check current entity state
            entity_data = await self.ha.get_state(div.entity_id)
            current_state = entity_data.get("state") if entity_data else "off"
            is_currently_on = current_state in ("on", "charging", "active")
            load_state.is_active = is_currently_on

            if div.power_sensor:
                load_state.current_power_w = await self.ha.get_numeric_state(div.power_sensor)

            last_change = self._last_state_change.get(div.entity_id, 0.0)
            can_toggle = (now - last_change) >= self.min_cycle_time_s

            if div.type == "switch":
                # Standard on/off relay
                if not is_currently_on and remaining_surplus >= div.min_power_w and can_toggle:
                    logger.info(f"Turning ON diversion '{div.name}' with surplus {remaining_surplus}W")
                    await self.ha.call_service("switch", "turn_on", {"entity_id": div.entity_id})
                    self._last_state_change[div.entity_id] = now
                    load_state.is_active = True
                    remaining_surplus -= div.min_power_w
                elif is_currently_on and pf.grid_w > 200 and can_toggle:
                    # Drawing more than 200W from grid; shut down non-critical diversion
                    logger.info(f"Turning OFF diversion '{div.name}' due to grid import {pf.grid_w}W")
                    await self.ha.call_service("switch", "turn_off", {"entity_id": div.entity_id})
                    self._last_state_change[div.entity_id] = now
                    load_state.is_active = False

            elif div.type == "evse":
                # Proportional EV charger modulating current (6A - 32A @ 230V)
                if remaining_surplus >= 1380: # 6A minimum single phase
                    target_amps = int(min(32, max(6, remaining_surplus / 230)))
                    await self.ha.call_service("number", "set_value", {
                        "entity_id": div.entity_id,
                        "value": target_amps
                    })
                    load_state.allocated_power_w = target_amps * 230
                    remaining_surplus = max(0.0, remaining_surplus - load_state.allocated_power_w)

            results.append(load_state)

        return results
