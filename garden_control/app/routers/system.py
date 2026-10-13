import time
import aiosqlite
from datetime import date
from fastapi import APIRouter, Request
from app.models import SystemStatus
from app.engine.et_calculator import ETCalculator

router = APIRouter(prefix="/api/system", tags=["system"])

START_TIME = time.time()

@router.get("/status", response_model=SystemStatus)
async def get_system_status(request: Request):
    """Retrieve full system status, active irrigation runs, and environmental parameters."""
    cfg = request.app.state.config
    ha = request.app.state.ha
    dispatcher = request.app.state.irrigation

    active_runs = await dispatcher.get_active_runs_summary()

    # Query cistern level if entity configured
    cistern_pct = None
    if cfg.cistern_sensor_entity:
        state = await ha.get_entity_state(cfg.cistern_sensor_entity)
        if state and state.get("state"):
            try:
                cistern_pct = float(state["state"])
            except ValueError:
                pass

    # Query solar power if entity configured
    solar_watts = None
    if cfg.solar_power_entity:
        state = await ha.get_entity_state(cfg.solar_power_entity)
        if state and state.get("state"):
            try:
                solar_watts = float(state["state"])
            except ValueError:
                pass

    # Calculate current baseline ET0 (Puerto Rico standard day estimate if weather sensor not yet bound)
    # Defaulting to tropical baseline 24C min, 31C max
    daily_et0 = ETCalculator.calculate_daily_et0(t_min_c=24.0, t_max_c=31.0, current_date=date.today())

    # Calculate water used today from DB
    water_today = 0.0
    try:
        async with aiosqlite.connect(cfg.database_path) as db:
            query = """
                SELECT COALESCE(SUM(estimated_liters), 0.0) 
                FROM irrigation_runs 
                WHERE date(start_time) = date('now')
            """
            async with db.execute(query) as cursor:
                water_today = (await cursor.fetchone())[0]
    except Exception:
        pass

    return SystemStatus(
        version="0.1.0",
        uptime_seconds=round(time.time() - START_TIME, 1),
        active_runs=active_runs,
        cistern_level_pct=cistern_pct if cistern_pct is not None else 85.0, # default resilient mockup if unlinked
        solar_power_watts=solar_watts if solar_watts is not None else 1850.0,
        daily_et0_mm=daily_et0,
        water_used_today_liters=round(water_today, 2),
        weather_delay_active=False
    )
