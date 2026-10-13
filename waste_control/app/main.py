import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional

from .config import load_config, AppConfig
from .ha_client import HAClient
from .engine.scheduler import calculate_next_pickup
from .engine.bin_tracker import BinManager
from .engine.mqtt_publisher import MQTTManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WasteControl.App")

app = FastAPI(title="WasteControl-io", version="0.1.0")

config: AppConfig = load_config()
ha_client = HAClient()
bin_manager = BinManager()
mqtt_manager = MQTTManager(config)

class LocationPayload(BaseModel):
    location: str

class ReadingPayload(BaseModel):
    distance_cm: float

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing WasteControl-io Engine...")
    mqtt_manager.start()
    asyncio.create_task(sync_loop())

async def sync_loop():
    """Periodically recalculate collection schedules and sync states."""
    while True:
        try:
            for stream in config.streams:
                sched = calculate_next_pickup(stream)
                bin_state = bin_manager.get_bin(stream.id) if stream.bin_monitor else None
                mqtt_manager.publish_state(stream.id, sched, bin_state)
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
        await asyncio.sleep(config.refresh_interval)

@app.get("/api/status")
async def get_status():
    streams_out = []
    for stream in config.streams:
        sched = calculate_next_pickup(stream)
        bin_state = bin_manager.get_bin(stream.id).to_dict() if stream.bin_monitor else None
        streams_out.append({
            "id": stream.id,
            "name": stream.name,
            "color": stream.color,
            "schedule_type": stream.schedule_type,
            "pickup_day": stream.pickup_day,
            "holiday_delay": stream.holiday_delay,
            "bin_monitor": stream.bin_monitor,
            "schedule": sched,
            "bin": bin_state
        })
    return {
        "status": "ok",
        "mqtt_connected": mqtt_manager.connected,
        "streams": streams_out
    }

@app.post("/api/bin/{stream_id}/location")
async def set_location(stream_id: str, payload: LocationPayload):
    bin_state = bin_manager.set_location(stream_id, payload.location)
    stream = next((s for s in config.streams if s.id == stream_id), None)
    if stream:
        sched = calculate_next_pickup(stream)
        mqtt_manager.publish_state(stream_id, sched, bin_state)
    return {"status": "ok", "bin": bin_state.to_dict()}

@app.post("/api/bin/{stream_id}/reading")
async def update_reading(stream_id: str, payload: ReadingPayload):
    stream = next((s for s in config.streams if s.id == stream_id), None)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
        
    bin_state = bin_manager.update_sensor_reading(
        stream_id,
        payload.distance_cm,
        stream.empty_depth_cm,
        stream.full_depth_cm
    )
    sched = calculate_next_pickup(stream)
    mqtt_manager.publish_state(stream_id, sched, bin_state)
    return {"status": "ok", "bin": bin_state.to_dict()}

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    return "<h1>WasteControl-io</h1>"

@app.get("/icon.png")
async def serve_icon():
    icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/logo.png")
async def serve_logo():
    logo_path = os.path.join(os.path.dirname(__file__), "..", "logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path)
    raise HTTPException(status_code=404, detail="Logo not found")
