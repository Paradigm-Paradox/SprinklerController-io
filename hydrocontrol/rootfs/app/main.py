import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from config import load_options
from core.ha_client import HomeAssistantClient
from core.dosing import DosingController
from core.irrigation import IrrigationController

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hydrocontrol.main")

config = load_options()
ha_client = HomeAssistantClient()
dosing_ctrl = DosingController(config, ha_client)
irrigation_ctrl = IrrigationController(config, ha_client)

current_metrics = {
    "ph": None,
    "ec": None,
    "water_temp": None,
    "water_level": None,
}

background_task: Optional[asyncio.Task] = None

async def poll_sensors_and_control_loop():
    logger.info("Starting HydroControl background telemetry & control loop...")
    while True:
        try:
            sensors = config.get("sensors", {})
            ph_entity = sensors.get("ph_sensor_entity")
            ec_entity = sensors.get("ec_sensor_entity")
            temp_entity = sensors.get("water_temp_entity")

            # 1. Fetch sensor states
            if ph_entity:
                state = await ha_client.get_state(ph_entity)
                if state and "state" in state:
                    try:
                        current_metrics["ph"] = float(state["state"])
                    except ValueError:
                        pass

            if ec_entity:
                state = await ha_client.get_state(ec_entity)
                if state and "state" in state:
                    try:
                        current_metrics["ec"] = float(state["state"])
                    except ValueError:
                        pass

            if temp_entity:
                state = await ha_client.get_state(temp_entity)
                if state and "state" in state:
                    try:
                        current_metrics["water_temp"] = float(state["state"])
                    except ValueError:
                        pass

            # 2. Evaluate Dosing
            await dosing_ctrl.evaluate_and_dose(current_metrics["ph"], current_metrics["ec"])

            # 3. Evaluate Irrigation
            await irrigation_ctrl.update()

        except Exception as err:
            logger.error("Error in background loop iteration: %s", err, exc_info=True)

        await asyncio.sleep(15)  # Cycle interval

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_task
    background_task = asyncio.create_task(poll_sensors_and_control_loop())
    yield
    if background_task:
        background_task.cancel()
    await ha_client.close()

app = FastAPI(title="HydroControl-io", lifespan=lifespan)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

class ManualDoseRequest(BaseModel):
    pump: str
    volume_ml: float

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    targets = config.get("targets", {})
    irrigation_cfg = config.get("irrigation", {})
    dosing_cfg = config.get("dosing", {})

    context = {
        "request": request,
        "system_name": config.get("system_name", "Hydroponics Main"),
        "current_ph": current_metrics["ph"],
        "target_ph": targets.get("target_ph", 6.0),
        "ph_tolerance": targets.get("ph_tolerance", 0.2),
        "current_ec": current_metrics["ec"],
        "target_ec_ms": targets.get("target_ec_ms", 1.8),
        "ec_tolerance": targets.get("ec_tolerance", 0.1),
        "current_temp": current_metrics["water_temp"],
        "target_water_temp_c": targets.get("target_water_temp_c", 20.0),
        "irrigation_state": irrigation_ctrl.current_state,
        "irrigation_mode": irrigation_cfg.get("mode", "continuous").capitalize(),
        "daily_dosed_ml": dosing_ctrl.daily_dosed_ml,
        "daily_safety_cap_ml": dosing_cfg.get("daily_safety_cap_ml", 100.0),
        "dosing_status": dosing_ctrl.status,
        "events": reversed(dosing_ctrl.recent_events),
    }
    return templates.TemplateResponse("index.html", context)

@app.get("/api/telemetry")
async def get_telemetry():
    return JSONResponse({
        "metrics": current_metrics,
        "dosing_status": dosing_ctrl.status,
        "irrigation_state": irrigation_ctrl.current_state,
        "daily_dosed_ml": dosing_ctrl.daily_dosed_ml,
    })

@app.post("/api/manual-dose")
async def manual_dose(req: ManualDoseRequest):
    dosing_cfg = config.get("dosing", {})
    pump_map = {
        "ph_down": dosing_cfg.get("ph_down_pump_entity"),
        "ph_up": dosing_cfg.get("ph_up_pump_entity"),
        "nutrient_a": dosing_cfg.get("nutrient_a_pump_entity"),
        "nutrient_b": dosing_cfg.get("nutrient_b_pump_entity"),
    }
    entity_id = pump_map.get(req.pump)
    if not entity_id:
        return JSONResponse({"success": False, "message": f"Entity not configured for {req.pump}"}, status_code=400)

    success = await dosing_ctrl.execute_dose(entity_id, req.volume_ml, f"Manual trigger for {req.pump}")
    return JSONResponse({"success": success, "message": f"Dose dispatched: {req.volume_ml}mL for {req.pump}"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
