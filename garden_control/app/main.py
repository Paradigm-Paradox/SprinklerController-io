import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import load_config
from app.database import init_db
from app.engine.ha_client import HomeAssistantClient
from app.engine.irrigation import IrrigationDispatcher
from app.routers import zones, beds, crops, system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("gardencontrol")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Starting GardenControl-io Edge Engine...")
    cfg = load_config()
    app.state.config = cfg

    # Initialize SQLite database
    await init_db(cfg.database_path)

    # Initialize HA connector & irrigation dispatcher
    ha_client = HomeAssistantClient()
    app.state.ha = ha_client
    app.state.irrigation = IrrigationDispatcher(config=cfg, ha_client=ha_client)

    yield

    # Teardown sequence
    logger.info("Shutting down GardenControl-io...")
    await ha_client.close()

app = FastAPI(
    title="GardenControl-io",
    description="Adaptive Irrigation & Crop Management for Home Assistant",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(zones.router)
app.include_router(beds.router)
app.include_router(crops.router)
app.include_router(system.router)

# Mount Static Ingress Assets
STATIC_DIR = Path(__file__).parent / "static"

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
