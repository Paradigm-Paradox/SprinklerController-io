import time
from typing import Dict, Any

class IrrigationEngine:
    def __init__(
        self,
        zone_name: str,
        moisture_target: float = 45.0,
        max_run_seconds: int = 120,
        min_cooldown_seconds: int = 600
    ):
        self.zone_name = zone_name
        self.moisture_target = moisture_target
        self.max_run_seconds = max_run_seconds
        self.min_cooldown_seconds = min_cooldown_seconds
        
        self.last_irrigation_start = 0.0
        self.last_irrigation_end = 0.0
        self.is_running = False

    def evaluate(self, current_moisture: float) -> Dict[str, Any]:
        now = time.time()
        
        if self.is_running:
            elapsed = now - self.last_irrigation_start
            if elapsed >= self.max_run_seconds:
                self.is_running = False
                self.last_irrigation_end = now
                return {
                    "valve_open": False,
                    "status": "Watchdog: Max run-time reached. Shutting off.",
                    "alert": True
                }
            return {
                "valve_open": True,
                "status": f"Irrigating ({int(elapsed)}s elapsed)",
                "alert": False
            }

        cooldown_remaining = self.min_cooldown_seconds - (now - self.last_irrigation_end)
        if cooldown_remaining > 0:
            return {
                "valve_open": False,
                "status": f"Cooldown active ({int(cooldown_remaining)}s remaining)",
                "alert": False
            }

        if current_moisture < self.moisture_target:
            self.is_running = True
            self.last_irrigation_start = now
            return {
                "valve_open": True,
                "status": "Target moisture breached. Starting irrigation cycle.",
                "alert": False
            }

        return {
            "valve_open": False,
            "status": "Moisture adequate",
            "alert": False
        }
