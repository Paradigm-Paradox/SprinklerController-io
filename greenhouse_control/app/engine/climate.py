from typing import Dict, Any
from .vpd import calculate_vpd

class ClimateEngine:
    def __init__(self, zone_name: str, target_vpd_min: float = 0.8, target_vpd_max: float = 1.2):
        self.zone_name = zone_name
        self.target_vpd_min = target_vpd_min
        self.target_vpd_max = target_vpd_max
        self.max_temp_c = 32.0
        self.min_temp_c = 15.0

    def evaluate(
        self,
        air_temp: float,
        humidity: float,
        leaf_temp: float = None,
        leaf_offset: float = -2.0
    ) -> Dict[str, Any]:
        vpd_metrics = calculate_vpd(air_temp, humidity, leaf_temp, leaf_offset)
        leaf_vpd = vpd_metrics["leaf_vpd_kpa"]

        actions = {
            "heater": False,
            "cooler": False,
            "exhaust_fan": False,
            "humidifier": False,
            "status": "Optimal",
        }

        # Temperature Safety Guardrails first
        if air_temp > self.max_temp_c:
            actions["cooler"] = True
            actions["exhaust_fan"] = True
            actions["status"] = "High Temperature Protection"
            return {"vpd": vpd_metrics, "actions": actions}

        if air_temp < self.min_temp_c:
            actions["heater"] = True
            actions["status"] = "Freeze / Low Temperature Protection"
            return {"vpd": vpd_metrics, "actions": actions}

        # VPD Optimization Loop
        if leaf_vpd < self.target_vpd_min:
            actions["status"] = "Low VPD (Excess Humidity)"
            actions["exhaust_fan"] = True
        elif leaf_vpd > self.target_vpd_max:
            actions["status"] = "High VPD (Air Too Dry)"
            actions["humidifier"] = True
        else:
            actions["status"] = "Optimal Target Zone"

        return {
            "vpd": vpd_metrics,
            "actions": actions
        }
