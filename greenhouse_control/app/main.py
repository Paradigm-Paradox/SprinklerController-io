import asyncio
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import load_config, AppConfig
from .ha_client import HomeAssistantClient
from .engine.climate import ClimateEngine
from .engine.irrigation import IrrigationEngine

app_config: AppConfig = load_config()
ha_client = HomeAssistantClient()

climate_engine = ClimateEngine("Main Zone", app_config.zones[0].target_vpd_min, app_config.zones[0].target_vpd_max)
irrigation_engine = IrrigationEngine("Main Zone", app_config.zones[0].soil_moisture_target)

latest_state = {
    "ha_connected": ha_client.is_connected,
    "climate": {
        "air_temp": 24.5,
        "humidity": 65.0,
    },
    "vpd": {
        "air_vpd_kpa": 1.08,
        "leaf_vpd_kpa": 0.95,
        "effective_leaf_temp_c": 22.5,
        "dew_point_c": 17.4
    },
    "irrigation": {
        "soil_moisture": 48.0,
        "valve_open": False,
        "status": "Adequate"
    },
    "actions": {
        "exhaust_fan": False,
        "humidifier": False,
        "heater": False,
        "status": "Optimal Target Zone"
    }
}

async def background_loop():
    while True:
        try:
            zone = app_config.zones[0]
            air_temp = 24.5
            humidity = 65.0
            leaf_temp = None

            if ha_client.is_connected:
                if zone.temp_sensor:
                    state = await ha_client.get_entity_state(zone.temp_sensor)
                    if state and state.get("state") not in (None, "unknown", "unavailable"):
                        try:
                            air_temp = float(state["state"])
                        except ValueError:
                            pass

                if zone.humidity_sensor:
                    state = await ha_client.get_entity_state(zone.humidity_sensor)
                    if state and state.get("state") not in (None, "unknown", "unavailable"):
                        try:
                            humidity = float(state["state"])
                        except ValueError:
                            pass

                if zone.leaf_temp_sensor:
                    state = await ha_client.get_entity_state(zone.leaf_temp_sensor)
                    if state and state.get("state") not in (None, "unknown", "unavailable"):
                        try:
                            leaf_temp = float(state["state"])
                        except ValueError:
                            pass

            eval_res = climate_engine.evaluate(air_temp, humidity, leaf_temp, zone.leaf_temp_offset)
            irrig_res = irrigation_engine.evaluate(latest_state["irrigation"]["soil_moisture"])

            latest_state["ha_connected"] = ha_client.is_connected
            latest_state["climate"] = {"air_temp": air_temp, "humidity": humidity}
            latest_state["vpd"] = eval_res["vpd"]
            latest_state["actions"] = eval_res["actions"]
            latest_state["irrigation"]["valve_open"] = irrig_res["valve_open"]
            latest_state["irrigation"]["status"] = irrig_res["status"]

            if ha_client.is_connected:
                if zone.exhaust_fan_switch:
                    service = "turn_on" if eval_res["actions"]["exhaust_fan"] else "turn_off"
                    await ha_client.call_service("switch", service, {"entity_id": zone.exhaust_fan_switch})
                if zone.humidifier_switch:
                    service = "turn_on" if eval_res["actions"]["humidifier"] else "turn_off"
                    await ha_client.call_service("switch", service, {"entity_id": zone.humidifier_switch})
                if zone.heater_switch:
                    service = "turn_on" if eval_res["actions"]["heater"] else "turn_off"
                    await ha_client.call_service("switch", service, {"entity_id": zone.heater_switch})
                if zone.irrigation_valve:
                    service = "turn_on" if irrig_res["valve_open"] else "turn_off"
                    await ha_client.call_service("switch", service, {"entity_id": zone.irrigation_valve})

        except Exception as e:
            print(f"Error in automation loop: {e}")

        await asyncio.sleep(app_config.refresh_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_loop())
    yield
    task.cancel()

app = FastAPI(title="GreenhouseControl-io", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)

@app.get("/styles.css")
async def get_styles():
    return FileResponse(STATIC_DIR / "styles.css")

@app.get("/app.js")
async def get_app_js():
    return FileResponse(STATIC_DIR / "app.js")

@app.get("/api/status")
async def get_status():
    return latest_state

@app.get("/api/config")
async def get_app_config():
    return app_config.model_dump()
