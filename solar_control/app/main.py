import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .config import load_config, AppConfig
from .ha_client import HAClient
from .engine import (
    PowerFlowEngine,
    BatteryManager,
    LoadDiverter,
    TariffOptimizer,
    EnergySystemState,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SolarControl.Main")

# Global state
config: AppConfig = load_config()
ha_client = HAClient()
power_flow_engine = PowerFlowEngine(config, ha_client)
battery_manager = BatteryManager(config, ha_client)
load_diverter = LoadDiverter(config, ha_client)
tariff_optimizer = TariffOptimizer(config, ha_client)

system_state = EnergySystemState(operating_mode=config.operating_mode)
background_task: asyncio.Task = None

async def control_loop():
    logger.info("Starting SolarControl background dispatch loop...")
    while True:
        try:
            # 1. Update Power Flow telemetry
            pf = await power_flow_engine.calculate()
            system_state.power_flow = pf

            # 2. Evaluate Dynamic Tariffs
            tariff_st = await tariff_optimizer.evaluate(pf)
            system_state.tariff = tariff_st

            # 3. Evaluate Battery Dispatch
            status_msg = await battery_manager.evaluate(pf, system_state.operating_mode)
            if status_msg:
                system_state.status_message = status_msg

            # 4. Evaluate Excess Solar Diversions
            diversion_results = await load_diverter.evaluate(pf)
            system_state.diversions = diversion_results

        except Exception as e:
            logger.error(f"Error in control loop: {e}", exc_info=True)

        await asyncio.sleep(config.refresh_interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_task
    background_task = asyncio.create_task(control_loop())
    yield
    if background_task:
        background_task.cancel()
    await ha_client.close()

app = FastAPI(title="SolarControl-io", lifespan=lifespan)

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

class ModeRequest(BaseModel):
    mode: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/state")
async def get_state() -> Dict[str, Any]:
    return {
        "operating_mode": system_state.operating_mode,
        "status_message": system_state.status_message,
        "power_flow": {
            "solar_w": system_state.power_flow.solar_w,
            "battery_w": system_state.power_flow.battery_w,
            "grid_w": system_state.power_flow.grid_w,
            "home_w": system_state.power_flow.home_w,
            "ev_w": system_state.power_flow.ev_w,
            "diverted_w": system_state.power_flow.diverted_w,
            "battery_soc": system_state.power_flow.battery_soc,
            "daily_solar_kwh": system_state.power_flow.daily_solar_kwh,
            "forecast_today_kwh": system_state.power_flow.forecast_today_kwh,
            "self_consumption_pct": system_state.power_flow.self_consumption_pct,
            "self_sufficiency_pct": system_state.power_flow.self_sufficiency_pct,
        },
        "tariff": {
            "enabled": system_state.tariff.enabled,
            "import_price": system_state.tariff.import_price,
            "export_price": system_state.tariff.export_price,
            "is_negative_export": system_state.tariff.is_negative_export,
        },
        "diversions": [
            {
                "name": d.name,
                "type": d.type,
                "entity_id": d.entity_id,
                "priority": d.priority,
                "is_active": d.is_active,
                "current_power_w": d.current_power_w,
                "allocated_power_w": d.allocated_power_w,
            }
            for d in system_state.diversions
        ],
    }

@app.post("/api/mode")
async def update_mode(req: ModeRequest):
    allowed_modes = ["auto", "self_consumption", "tou_arbitrage", "backup_reserve", "manual"]
    if req.mode in allowed_modes:
        system_state.operating_mode = req.mode
        logger.info(f"Operating mode set to: {req.mode}")
        return {"status": "ok", "mode": system_state.operating_mode}
    return {"status": "error", "message": "Invalid mode"}
