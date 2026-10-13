import aiosqlite
import uuid
from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from app.models import Bed, BedCreate, Planting, PlantingCreate

router = APIRouter(prefix="/api/beds", tags=["beds"])

@router.get("", response_model=List[Bed])
async def list_beds(request: Request):
    """List all physical garden beds."""
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM beds") as cursor:
            rows = await cursor.fetchall()
            return [Bed(**dict(row)) for row in rows]

@router.post("", response_model=Bed)
async def create_bed(bed: BedCreate, request: Request):
    """Create a new physical garden bed."""
    bed_id = f"bed_{uuid.uuid4().hex[:6]}"
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO beds (id, zone_id, name, bed_type, width_cm, length_cm, depth_cm, soil_type, moisture_target_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (bed_id, bed.zone_id, bed.name, bed.bed_type, bed.width_cm, bed.length_cm, bed.depth_cm, bed.soil_type, bed.moisture_target_pct)
        )
        await db.commit()
    return Bed(id=bed_id, **bed.model_dump())

@router.get("/{bed_id}/plantings", response_model=List[Planting])
async def list_bed_plantings(bed_id: str, request: Request):
    """List all crops actively planted in a given bed with catalog metadata."""
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT p.*, c.common_name, c.category
            FROM plantings p
            JOIN crop_catalog c ON p.crop_id = c.id
            WHERE p.bed_id = ?
        """
        async with db.execute(query, (bed_id,)) as cursor:
            rows = await cursor.fetchall()
            return [Planting(**dict(row)) for row in rows]

@router.post("/{bed_id}/plantings", response_model=Planting)
async def add_planting(bed_id: str, planting: PlantingCreate, request: Request):
    """Add a new crop planting to a garden bed and analyze companion affinity."""
    planting_id = f"plant_{uuid.uuid4().hex[:6]}"
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        # Fetch crop days to maturity
        async with db.execute("SELECT * FROM crop_catalog WHERE id = ?", (planting.crop_id,)) as cursor:
            crop = await cursor.fetchone()
            if not crop:
                raise HTTPException(status_code=404, detail="Crop not found in catalog")

        await db.execute(
            """
            INSERT INTO plantings (id, bed_id, crop_id, x_cm, y_cm, quantity, planted_at, current_stage, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (planting_id, bed_id, planting.crop_id, planting.x_cm, planting.y_cm, planting.quantity, planting.planted_at.isoformat(), planting.current_stage, planting.notes)
        )
        await db.commit()

    return Planting(
        id=planting_id,
        bed_id=bed_id,
        crop_id=planting.crop_id,
        common_name=crop["common_name"],
        category=crop["category"],
        x_cm=planting.x_cm,
        y_cm=planting.y_cm,
        quantity=planting.quantity,
        planted_at=planting.planted_at,
        current_stage=planting.current_stage,
        notes=planting.notes
    )
