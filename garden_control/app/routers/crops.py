import aiosqlite
from fastapi import APIRouter, Request
from typing import List
from app.models import CropCatalogItem

router = APIRouter(prefix="/api/crops", tags=["crops"])

@router.get("", response_model=List[CropCatalogItem])
async def list_crops(request: Request):
    """Retrieve full catalog of crops with biological requirements and companion guidelines."""
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM crop_catalog ORDER BY common_name ASC") as cursor:
            rows = await cursor.fetchall()
            return [CropCatalogItem(**dict(row)) for row in rows]

@router.get("/{crop_id}/companions")
async def get_companion_advice(crop_id: str, request: Request):
    """Get beneficial and antagonistic companion recommendations for a crop."""
    db_path = request.app.state.config.database_path
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM crop_catalog WHERE id = ?", (crop_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"error": "Crop not found"}
            beneficial = [c.strip() for c in (row["beneficial_companions"] or "").split(",") if c.strip()]
            antagonists = [c.strip() for c in (row["antagonist_plants"] or "").split(",") if c.strip()]
            return {
                "crop_id": crop_id,
                "common_name": row["common_name"],
                "beneficial_companions": beneficial,
                "antagonist_plants": antagonists
            }
