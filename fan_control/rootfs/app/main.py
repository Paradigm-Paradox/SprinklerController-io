import os
import json
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FanControl")

app = FastAPI(title="FanControl-io")

# Setup template engine
templates_dir = "/app/templates" if os.path.exists("/app/templates") else os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Initial State
state = {
    "system_name": "Server Rack Cabinet Fan Controller",
    "control_mode": "auto",  # auto, silent, balanced, performance, turbo, manual
    "health_status": "optimal",  # optimal, warning, critical, failsafe
    "thermal": {
        "rack_intake_c": 22.8,
        "rack_exhaust_c": 31.4,
        "delta_t_c": 8.6,
        "cabinet_ambient_c": 26.5,
        "server_cpu_c": 49.2,
        "ble_probe_c": 27.1,
        "target_exhaust_c": 30.0,
        "max_delta_t_c": 8.0,
        "emergency_temp_c": 45.0
    },
    "fans": [
        {
            "id": 1,
            "name": "Rack Top Exhaust Fan 1",
            "type": "4-pin 25kHz PWM",
            "speed_pct": 55,
            "rpm": 1280,
            "max_rpm": 2000,
            "target_rpm": 1300,
            "status": "normal",
            "node_type": "ESP32 (WT32-ETH01 Ethernet)",
            "stall_detected": False
        },
        {
            "id": 2,
            "name": "Rack Top Exhaust Fan 2",
            "type": "4-pin 25kHz PWM",
            "speed_pct": 55,
            "rpm": 1265,
            "max_rpm": 2000,
            "target_rpm": 1300,
            "status": "normal",
            "node_type": "ESP32 (WT32-ETH01 Ethernet)",
            "stall_detected": False
        },
        {
            "id": 3,
            "name": "Front Intake Blower Array",
            "type": "4-pin 25kHz PWM",
            "speed_pct": 40,
            "rpm": 950,
            "max_rpm": 1800,
            "target_rpm": 950,
            "status": "normal",
            "node_type": "ESP32 (Wi-Fi + BLE Gateway)",
            "stall_detected": False
        },
        {
            "id": 4,
            "name": "10G Switch & Patch Panel Fan",
            "type": "4-pin 25kHz PWM",
            "speed_pct": 65,
            "rpm": 1620,
            "max_rpm": 2400,
            "target_rpm": 1600,
            "status": "normal",
            "node_type": "ESP32 (Wi-Fi + BLE Gateway)",
            "stall_detected": False
        }
    ],
    "safety": {
        "stall_detection_enabled": True,
        "min_stall_rpm": 200,
        "failsafe_active": False,
        "emergency_speed_pct": 100
    }
}

class ModeRequest(BaseModel):
    mode: str

class FanSpeedRequest(BaseModel):
    speed_pct: int

class ThermalTargetRequest(BaseModel):
    target_exhaust_c: float
    max_delta_t_c: float
    emergency_temp_c: float

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "state": state})

@app.get("/api/status")
async def get_status():
    return JSONResponse(content=state)

@app.post("/api/mode")
async def set_mode(payload: ModeRequest):
    valid_modes = ["auto", "silent", "balanced", "performance", "turbo", "manual"]
    if payload.mode not in valid_modes:
        return JSONResponse(status_code=400, content={"error": f"Invalid mode. Choose from {valid_modes}"})
    
    state["control_mode"] = payload.mode
    
    # Update fan speeds according to presets if not manual
    if payload.mode == "silent":
        for fan in state["fans"]:
            fan["speed_pct"] = 25
            fan["rpm"] = int(fan["max_rpm"] * 0.3)
    elif payload.mode == "balanced":
        for fan in state["fans"]:
            fan["speed_pct"] = 50
            fan["rpm"] = int(fan["max_rpm"] * 0.55)
    elif payload.mode == "performance":
        for fan in state["fans"]:
            fan["speed_pct"] = 80
            fan["rpm"] = int(fan["max_rpm"] * 0.82)
    elif payload.mode == "turbo":
        for fan in state["fans"]:
            fan["speed_pct"] = 100
            fan["rpm"] = fan["max_rpm"]
    elif payload.mode == "auto":
        # Recalculate auto speed based on Delta-T and exhaust
        exhaust = state["thermal"]["rack_exhaust_c"]
        target = state["thermal"]["target_exhaust_c"]
        delta = max(0, exhaust - target)
        auto_speed = min(100, max(20, int(35 + delta * 12)))
        for fan in state["fans"]:
            fan["speed_pct"] = auto_speed
            fan["rpm"] = int(fan["max_rpm"] * (auto_speed / 100))

    logger.info(f"FanControl mode changed to {payload.mode}")
    return JSONResponse(content={"status": "success", "mode": state["control_mode"], "state": state})

@app.post("/api/fans/{fan_id}/speed")
async def set_fan_speed(fan_id: int, payload: FanSpeedRequest):
    speed = max(0, min(100, payload.speed_pct))
    for fan in state["fans"]:
        if fan["id"] == fan_id:
            fan["speed_pct"] = speed
            fan["rpm"] = int(fan["max_rpm"] * (speed / 100.0))
            if speed > 0 and fan["rpm"] < state["safety"]["min_stall_rpm"]:
                fan["stall_detected"] = True
                fan["status"] = "stalled"
            else:
                fan["stall_detected"] = False
                fan["status"] = "normal"
            state["control_mode"] = "manual"
            return JSONResponse(content={"status": "success", "fan": fan})
            
    return JSONResponse(status_code=404, content={"error": f"Fan ID {fan_id} not found"})

@app.post("/api/thermal/target")
async def set_thermal_targets(payload: ThermalTargetRequest):
    state["thermal"]["target_exhaust_c"] = payload.target_exhaust_c
    state["thermal"]["max_delta_t_c"] = payload.max_delta_t_c
    state["thermal"]["emergency_temp_c"] = payload.emergency_temp_c
    return JSONResponse(content={"status": "success", "thermal": state["thermal"]})

@app.get("/api/esphome/blueprint/{node_type}")
async def get_esphome_blueprint(node_type: str):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    templates_path = os.path.join(base_dir, "templates", "esphome")
    filename = f"{node_type}.yaml"
    filepath = os.path.join(templates_path, filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return PlainTextResponse(content=f.read(), media_type="text/yaml")
    return JSONResponse(status_code=404, content={"error": f"Blueprint {node_type} not found"})
