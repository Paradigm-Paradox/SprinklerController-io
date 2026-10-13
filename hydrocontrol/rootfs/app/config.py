import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("hydrocontrol.config")

DEFAULT_CONFIG: Dict[str, Any] = {
    "log_level": "info",
    "system_name": "Hydroponics Main",
    "reservoir_capacity_liters": 50.0,
    "sensors": {
        "ph_sensor_entity": "",
        "ec_sensor_entity": "",
        "water_temp_entity": "",
        "water_level_entity": ""
    },
    "targets": {
        "target_ph": 6.0,
        "ph_tolerance": 0.2,
        "target_ec_ms": 1.8,
        "ec_tolerance": 0.1,
        "target_water_temp_c": 20.0
    },
    "dosing": {
        "enabled": False,
        "ph_down_pump_entity": "",
        "ph_up_pump_entity": "",
        "nutrient_a_pump_entity": "",
        "nutrient_b_pump_entity": "",
        "pump_flow_rate_ml_min": 60.0,
        "max_single_dose_ml": 10.0,
        "dose_mixing_delay_sec": 900,
        "daily_safety_cap_ml": 100.0
    },
    "irrigation": {
        "pump_entity": "",
        "mode": "continuous",
        "cycle_on_minutes": 15,
        "cycle_off_minutes": 45
    }
}

def load_options() -> Dict[str, Any]:
    options_path = "/data/options.json"
    if os.path.exists(options_path):
        try:
            with open(options_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                logger.info("Loaded configuration options from %s", options_path)
                return config
        except Exception as err:
            logger.error("Failed to parse options.json: %s. Using defaults.", err)
    else:
        logger.info("No options.json found at %s. Using default configuration.", options_path)
    return DEFAULT_CONFIG
