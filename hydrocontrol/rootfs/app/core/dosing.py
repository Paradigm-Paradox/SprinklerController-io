import asyncio
import time
import logging
from typing import Dict, Any, Optional
from .ha_client import HomeAssistantClient

logger = logging.getLogger("hydrocontrol.dosing")

class DosingController:
    def __init__(self, config: Dict[str, Any], ha_client: HomeAssistantClient):
        self.config = config
        self.ha_client = ha_client
        self.last_dose_time: float = 0.0
        self.daily_dosed_ml: float = 0.0
        self.daily_reset_timestamp: float = time.time()
        self.status: str = "Idle"
        self.recent_events = []

    def log_event(self, message: str, level: str = "info"):
        entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "message": message, "level": level}
        self.recent_events.append(entry)
        if len(self.recent_events) > 50:
            self.recent_events.pop(0)
        getattr(logger, level, logger.info)(message)

    def _check_daily_reset(self):
        # Reset 24hr counter every 86400 seconds
        if time.time() - self.daily_reset_timestamp >= 86400:
            self.daily_dosed_ml = 0.0
            self.daily_reset_timestamp = time.time()
            self.log_event("Daily dosing safety counter reset to 0 mL.")

    async def execute_dose(self, pump_entity: str, volume_ml: float, reason: str) -> bool:
        if not pump_entity:
            self.log_event(f"Cannot dose: No pump entity configured for {reason}", "warning")
            return False

        dosing_cfg = self.config.get("dosing", {})
        flow_rate = dosing_cfg.get("pump_flow_rate_ml_min", 60.0) # mL/min
        max_dose = dosing_cfg.get("max_single_dose_ml", 10.0)
        daily_cap = dosing_cfg.get("daily_safety_cap_ml", 100.0)

        # Cap volume
        volume_to_dose = min(volume_ml, max_dose)
        self._check_daily_reset()

        if self.daily_dosed_ml + volume_to_dose > daily_cap:
            self.log_event(
                f"SAFETY INTERLOCK: Dose of {volume_to_dose:.1f}mL for {reason} exceeds daily cap ({daily_cap}mL). Dosing aborted!",
                "error"
            )
            self.status = "Daily Cap Safety Lockout"
            return False

        duration_sec = (volume_to_dose / flow_rate) * 60.0
        self.log_event(f"Activating {pump_entity} for {duration_sec:.1f}s (~{volume_to_dose:.1f}mL) - {reason}")
        self.status = f"Dosing {volume_to_dose:.1f}mL ({reason})"

        # Turn pump ON
        domain = pump_entity.split(".")[0]
        on_success = await self.ha_client.call_service(domain, "turn_on", {"entity_id": pump_entity})
        if not on_success:
            self.log_event(f"Failed to turn on pump {pump_entity}", "error")
            self.status = "Pump Activation Failed"
            return False

        await asyncio.sleep(duration_sec)

        # Turn pump OFF
        await self.ha_client.call_service(domain, "turn_off", {"entity_id": pump_entity})

        self.last_dose_time = time.time()
        self.daily_dosed_ml += volume_to_dose
        self.status = "Mixing & Stabilizing"
        self.log_event(f"Completed dose. Total today: {self.daily_dosed_ml:.1f}mL. Entering mixing delay.")
        return True

    async def evaluate_and_dose(self, current_ph: Optional[float], current_ec: Optional[float]):
        dosing_cfg = self.config.get("dosing", {})
        if not dosing_cfg.get("enabled", False):
            self.status = "Dosing Disabled (Manual/Safe Mode)"
            return

        mixing_delay = dosing_cfg.get("dose_mixing_delay_sec", 900)
        time_since_last = time.time() - self.last_dose_time
        if time_since_last < mixing_delay:
            remaining = int(mixing_delay - time_since_last)
            self.status = f"Mixing Delay ({remaining}s remaining)"
            return

        targets = self.config.get("targets", {})
        target_ph = targets.get("target_ph", 6.0)
        ph_tol = targets.get("ph_tolerance", 0.2)

        target_ec = targets.get("target_ec_ms", 1.8)
        ec_tol = targets.get("ec_tolerance", 0.1)

        # 1. pH Evaluation (pH takes precedence)
        if current_ph is not None:
            if current_ph > target_ph + ph_tol:
                # pH is too high -> Dose pH Down
                diff = current_ph - target_ph
                dose_volume = min(diff * 5.0, dosing_cfg.get("max_single_dose_ml", 10.0))
                await self.execute_dose(dosing_cfg.get("ph_down_pump_entity", ""), dose_volume, f"pH high ({current_ph:.2f} > {target_ph:.2f})")
                return
            elif current_ph < target_ph - ph_tol:
                # pH is too low -> Dose pH Up
                diff = target_ph - current_ph
                dose_volume = min(diff * 5.0, dosing_cfg.get("max_single_dose_ml", 10.0))
                await self.execute_dose(dosing_cfg.get("ph_up_pump_entity", ""), dose_volume, f"pH low ({current_ph:.2f} < {target_ph:.2f})")
                return

        # 2. EC Evaluation
        if current_ec is not None:
            if current_ec < target_ec - ec_tol:
                # EC too low -> Dose nutrients
                diff = target_ec - current_ec
                dose_volume = min(diff * 8.0, dosing_cfg.get("max_single_dose_ml", 10.0))
                
                # Alternate or split between A and B
                pump_a = dosing_cfg.get("nutrient_a_pump_entity", "")
                pump_b = dosing_cfg.get("nutrient_b_pump_entity", "")
                if pump_a:
                    await self.execute_dose(pump_a, dose_volume / 2.0, f"EC low ({current_ec:.2f} mS) Part A")
                if pump_b:
                    await asyncio.sleep(5) # Stagger A and B to prevent lockout precipitation
                    await self.execute_dose(pump_b, dose_volume / 2.0, f"EC low ({current_ec:.2f} mS) Part B")
                return

        self.status = "All Parameters in Target Range"
