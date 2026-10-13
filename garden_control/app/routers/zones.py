import aiosqlite
from fastapi import APIRouter, HTTPException, Request
from typing import List
from app.models import Zone, ZoneCreate, IrrigationTriggerRequest

router = APIRouter(prefix="/api/zones", tags=["zones"])

@router.get("", response_model=List[Zone])
async def list_zones(request: Request):
    """List all registered irrigation zones."""
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM zones") as cursor:
            rows = await cursor.fetchall()
            return [Zone(**dict(row)) for row in rows]

@router.post("", response_model=Zone)
async def create_zone(zone: ZoneCreate, request: Request):
    """Create a new irrigation zone."""
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO zones (id, name, valve_entity, moisture_sensor_entity, cycle_minutes, soak_minutes, max_duration_minutes, flow_rate_lpm)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (zone.id, zone.name, zone.valve_entity, zone.moisture_sensor_entity, zone.cycle_minutes, zone.soak_minutes, zone.max_duration_minutes, zone.flow_rate_lpm)
        )
        await db.commit()
    return Zone(**zone.model_dump(), is_enabled=True)

@router.post("/{zone_id}/run")
async def trigger_zone_run(zone_id: str, payload: IrrigationTriggerRequest, request: Request):
    """Trigger manual or cycle-and-soak irrigation for a specific zone."""
    dispatcher = request.app.state.irrigation
    try:
        run = await dispatcher.trigger_zone(
            zone_id=zone_id,
            duration_minutes=payload.duration_minutes,
            use_cycle_and_soak=payload.use_cycle_and_soak
        )
        return {
            "status": "started",
            "run_id": run.run_id,
            "zone_id": zone_id,
            "total_duration_sec": run.total_duration_sec,
            "pulses": run.total_pulses
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{zone_id}/stop")
async def stop_zone_run(zone_id: str, request: Request):
    """Stop active irrigation run for a zone."""
    dispatcher = request.app.state.irrigation
    await dispatcher.stop_zone(zone_id, reason="user_stop")
    return {"status": "stopped", "zone_id": zone_id}
