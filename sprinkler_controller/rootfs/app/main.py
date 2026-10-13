import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiohttp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SprinklerController")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="SprinklerController-io")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load Options from Home Assistant Supervisor
OPTIONS_PATH = Path("/data/options.json")
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
SUPERVISOR_URL = "http://supervisor/core/api"

def load_options() -> Dict[str, Any]:
    if OPTIONS_PATH.exists():
        try:
            with open(OPTIONS_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read {OPTIONS_PATH}: {e}")
    return {}

ha_options = load_options()

# Initial System State
state: Dict[str, Any] = {
    "system_name": ha_options.get("system_name", "SprinklerController-io"),
    "status": "idle",  # idle, watering, rain_delay, freeze_lockout
    "weather": {
        "temperature_c": 21.5,
        "rain_detected": False,
        "rain_delay_active": False,
        "freeze_lockout_active": False,
        "et_rate_mm_day": 4.2
    },
    "safety": {
        "freeze_lockout_temp_c": ha_options.get("safety", {}).get("freeze_lockout_temp_c", 3.0),
        "rain_delay_hours": ha_options.get("safety", {}).get("rain_delay_hours", 24),
        "max_zone_runtime_minutes": ha_options.get("safety", {}).get("max_zone_runtime_minutes", 60),
        "concurrent_zone_limit": ha_options.get("safety", {}).get("concurrent_zone_limit", 1),
    },
    "zones": [],
    "flow": {
        "current_gpm": 0.0,
        "daily_gallons": 142.0,
        "leak_detected": False
    }
}

# Populate default zones if not configured
configured_zones = ha_options.get("zones", [])
if configured_zones:
    for idx, z in enumerate(configured_zones, start=1):
        state["zones"].append({
            "id": idx,
            "name": z.get("name", f"Zone {idx}"),
            "switch_entity": z.get("switch_entity", ""),
            "state": "idle",
            "remaining_seconds": 0,
            "default_duration_min": z.get("default_duration_minutes", 15),
            "cycle_count": z.get("cycle_count", 2),
            "soak_minutes": z.get("soak_minutes", 10),
            "flow_rate_gpm": z.get("flow_rate_gpm", 4.0),
            "node_type": "ESP32",
            "soil_moisture_pct": 40.0
        })
else:
    state["zones"] = [
        {
            "id": 1,
            "name": "Front Lawn",
            "switch_entity": "switch.zone_1_front_lawn",
            "state": "idle",
            "remaining_seconds": 0,
            "default_duration_min": 15,
            "cycle_count": 2,
            "soak_minutes": 10,
            "flow_rate_gpm": 4.5,
            "node_type": "ESP32 (WT32-ETH01 Ethernet)",
            "soil_moisture_pct": 38.0
        },
        {
            "id": 2,
            "name": "Back Lawn",
            "switch_entity": "switch.zone_2_back_lawn",
            "state": "idle",
            "remaining_seconds": 0,
            "default_duration_min": 20,
            "cycle_count": 2,
            "soak_minutes": 15,
            "flow_rate_gpm": 5.0,
            "node_type": "ESP32 (Wi-Fi 8-Relay)",
            "soil_moisture_pct": 42.0
        },
        {
            "id": 3,
            "name": "Garden Beds",
            "switch_entity": "switch.zone_3_garden_beds",
            "state": "idle",
            "remaining_seconds": 0,
            "default_duration_min": 10,
            "cycle_count": 1,
            "soak_minutes": 0,
            "flow_rate_gpm": 2.0,
            "node_type": "ESP32 (Wi-Fi + BLE Gateway)",
            "soil_moisture_pct": 55.0
        },
        {
            "id": 4,
            "name": "Shrubs & Planters",
            "switch_entity": "switch.zone_4_shrubs",
            "state": "idle",
            "remaining_seconds": 0,
            "default_duration_min": 12,
            "cycle_count": 1,
            "soak_minutes": 0,
            "flow_rate_gpm": 2.2,
            "node_type": "ESP32 (Wi-Fi 8-Relay)",
            "soil_moisture_pct": 49.0
        }
    ]

async def call_ha_service(domain: str, service: str, service_data: Dict[str, Any]):
    """Calls Home Assistant Core API service if running under Supervisor."""
    if not SUPERVISOR_TOKEN:
        logger.debug(f"[Simulated HA Service] {domain}.{service} with {service_data}")
        return True
    
    headers = {
        "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{SUPERVISOR_URL}/services/{domain}/{service}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=service_data, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status in (200, 201):
                    logger.info(f"Successfully called HA service {domain}.{service} for {service_data.get('entity_id')}")
                    return True
                logger.warning(f"HA service {domain}.{service} returned {resp.status}")
    except Exception as e:
        logger.error(f"Error calling HA service {domain}.{service}: {e}")
    return False

# Background Zone Countdown Watchdog
async def zone_countdown_ticker():
    while True:
        try:
            await asyncio.sleep(1)
            any_active = False
            for zone in state["zones"]:
                if zone["state"] == "watering":
                    if zone["remaining_seconds"] > 0:
                        zone["remaining_seconds"] -= 1
                        any_active = True
                    else:
                        # Timer finished
                        zone["state"] = "idle"
                        zone["remaining_seconds"] = 0
                        logger.info(f"Zone {zone['name']} timer elapsed. Shutting off valve.")
                        if zone.get("switch_entity"):
                            asyncio.create_task(call_ha_service("switch", "turn_off", {"entity_id": zone["switch_entity"]}))
            
            if not any_active and state["status"] == "watering":
                state["status"] = "idle"
                state["flow"]["current_gpm"] = 0.0
        except Exception as e:
            logger.error(f"Countdown ticker error: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(zone_countdown_ticker())
    logger.info("SprinklerController-io started successfully")

class ZoneAction(BaseModel):
    duration_minutes: Optional[int] = 10

def get_ingress_root(request: Request) -> str:
    """Calculates ingress root path for Home Assistant Ingress embedding."""
    ingress_path = request.headers.get("X-Ingress-Path", "")
    if ingress_path:
        return ingress_path.rstrip("/")
    scope_root = request.scope.get("root_path", "")
    return scope_root.rstrip("/")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    root_path = get_ingress_root(request)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "state": state, "root_path": root_path}
    )

@app.get("/api/state")
async def get_state():
    return state

@app.post("/api/zones/{zone_id}/run")
async def run_zone(zone_id: int, action: ZoneAction):
    duration = action.duration_minutes or 10
    max_duration = state["safety"]["max_zone_runtime_minutes"]
    if duration > max_duration:
        duration = max_duration

    for zone in state["zones"]:
        if zone["id"] == zone_id:
            zone["state"] = "watering"
            zone["remaining_seconds"] = duration * 60
            state["status"] = "watering"
            state["flow"]["current_gpm"] = zone["flow_rate_gpm"]
            
            logger.info(f"Started watering {zone['name']} for {duration}m ({zone['remaining_seconds']}s)")
            
            if zone.get("switch_entity"):
                asyncio.create_task(call_ha_service("switch", "turn_on", {"entity_id": zone["switch_entity"]}))
                
            return {"status": "ok", "zone": zone}
            
    raise HTTPException(status_code=404, detail="Zone not found")

@app.post("/api/zones/{zone_id}/stop")
async def stop_zone(zone_id: int):
    for zone in state["zones"]:
        if zone["id"] == zone_id:
            zone["state"] = "idle"
            zone["remaining_seconds"] = 0
            logger.info(f"Stopped watering zone {zone['name']}")
            if zone.get("switch_entity"):
                asyncio.create_task(call_ha_service("switch", "turn_off", {"entity_id": zone["switch_entity"]}))
    
    if not any(z["state"] == "watering" for z in state["zones"]):
        state["status"] = "idle"
        state["flow"]["current_gpm"] = 0.0
        
    return {"status": "ok"}

@app.post("/api/system/stop_all")
async def stop_all():
    for zone in state["zones"]:
        if zone["state"] == "watering" and zone.get("switch_entity"):
            asyncio.create_task(call_ha_service("switch", "turn_off", {"entity_id": zone["switch_entity"]}))
        zone["state"] = "idle"
        zone["remaining_seconds"] = 0
        
    state["status"] = "idle"
    state["flow"]["current_gpm"] = 0.0
    logger.info("Emergency Stop triggered: all zones shut off")
    return {"status": "ok", "message": "All zones shut off"}
