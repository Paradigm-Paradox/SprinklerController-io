import os
import logging
import aiosqlite
from typing import Optional

logger = logging.getLogger("gardencontrol.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS zones (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    valve_entity TEXT,
    moisture_sensor_entity TEXT,
    cycle_minutes INTEGER DEFAULT 8,
    soak_minutes INTEGER DEFAULT 15,
    max_duration_minutes INTEGER DEFAULT 45,
    flow_rate_lpm REAL DEFAULT 12.0,
    is_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS beds (
    id TEXT PRIMARY KEY,
    zone_id TEXT REFERENCES zones(id),
    name TEXT NOT NULL,
    bed_type TEXT DEFAULT 'raised_bed',
    width_cm REAL DEFAULT 120.0,
    length_cm REAL DEFAULT 240.0,
    depth_cm REAL DEFAULT 30.0,
    soil_type TEXT DEFAULT 'loam',
    soil_sensor_entity TEXT,
    moisture_target_pct REAL DEFAULT 45.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crop_catalog (
    id TEXT PRIMARY KEY,
    common_name TEXT NOT NULL,
    botanical_name TEXT,
    category TEXT DEFAULT 'vegetable',
    days_to_germinate INTEGER,
    days_to_maturity INTEGER,
    sun_exposure TEXT DEFAULT 'full_sun',
    water_demand TEXT DEFAULT 'medium',
    kc_initial REAL DEFAULT 0.5,
    kc_mid REAL DEFAULT 1.0,
    kc_late REAL DEFAULT 0.8,
    root_depth_cm REAL DEFAULT 30.0,
    spacing_cm REAL DEFAULT 30.0,
    beneficial_companions TEXT,
    antagonist_plants TEXT
);

CREATE TABLE IF NOT EXISTS plantings (
    id TEXT PRIMARY KEY,
    bed_id TEXT NOT NULL REFERENCES beds(id),
    crop_id TEXT NOT NULL REFERENCES crop_catalog(id),
    x_cm REAL DEFAULT 0.0,
    y_cm REAL DEFAULT 0.0,
    quantity INTEGER DEFAULT 1,
    planted_at DATE NOT NULL,
    current_stage TEXT DEFAULT 'vegetative',
    expected_harvest DATE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS irrigation_runs (
    id TEXT PRIMARY KEY,
    zone_id TEXT NOT NULL REFERENCES zones(id),
    trigger_source TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    estimated_liters REAL,
    status TEXT DEFAULT 'completed'
);
"""

DEFAULT_CROPS = [
    (
        "tomato", "Roma Tomato", "Solanum lycopersicum", "vegetable",
        7, 75, "full_sun", "high", 0.6, 1.15, 0.8, 45.0, 45.0,
        "basil,marigold,carrot,onion", "fennel,cabbage,potato"
    ),
    (
        "basil", "Genovese Basil", "Ocimum basilicum", "herb",
        5, 60, "full_sun", "medium", 0.5, 0.9, 0.7, 20.0, 20.0,
        "tomato,pepper,oregano", "rue,sage"
    ),
    (
        "bell_pepper", "Bell Pepper", "Capsicum annuum", "vegetable",
        10, 80, "full_sun", "medium", 0.6, 1.05, 0.85, 35.0, 40.0,
        "basil,onion,spinach", "fennel,kohlrabi"
    ),
    (
        "lettuce", "Butterhead Lettuce", "Lactuca sativa", "vegetable",
        4, 50, "partial_shade", "high", 0.5, 1.0, 0.9, 20.0, 25.0,
        "carrot,radish,cucumber,strawberry", "cabbage,celery"
    ),
    (
        "carrot", "Nantes Carrot", "Daucus carota", "vegetable",
        12, 70, "full_sun", "medium", 0.45, 1.0, 0.75, 30.0, 10.0,
        "tomato,rosemary,lettuce,onion", "fennel,dill,parsnip"
    ),
    (
        "marigold", "French Marigold", "Tagetes patula", "flower",
        5, 45, "full_sun", "low", 0.4, 0.8, 0.6, 20.0, 20.0,
        "tomato,cucumber,eggplant,squash", "beans,cabbage"
    ),
    (
        "cucumber", "Marketmore Cucumber", "Cucumis sativus", "vegetable",
        6, 60, "full_sun", "high", 0.5, 1.0, 0.8, 35.0, 30.0,
        "marigold,beans,lettuce,radish", "sage,potato,aromatic_herbs"
    ),
    (
        "bush_bean", "Green Bush Bean", "Phaseolus vulgaris", "vegetable",
        8, 55, "full_sun", "medium", 0.4, 1.15, 0.85, 25.0, 15.0,
        "cucumber,corn,carrot,strawberry", "onion,garlic,fennel"
    )
]

async def init_db(db_path: str):
    """Initialize database and seed baseline catalog and default zone/bed if empty."""
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA_SQL)
        
        # Seed crop catalog if empty
        async with db.execute("SELECT COUNT(*) FROM crop_catalog") as cursor:
            count = (await cursor.fetchone())[0]
            if count == 0:
                logger.info("Seeding default crop catalog...")
                await db.executemany(
                    """
                    INSERT INTO crop_catalog (
                        id, common_name, botanical_name, category,
                        days_to_germinate, days_to_maturity, sun_exposure, water_demand,
                        kc_initial, kc_mid, kc_late, root_depth_cm, spacing_cm,
                        beneficial_companions, antagonist_plants
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    DEFAULT_CROPS
                )

        # Seed initial sample zone & bed if empty
        async with db.execute("SELECT COUNT(*) FROM zones") as cursor:
            zone_count = (await cursor.fetchone())[0]
            if zone_count == 0:
                await db.execute(
                    """
                    INSERT INTO zones (id, name, valve_entity, flow_rate_lpm, cycle_minutes, soak_minutes, max_duration_minutes)
                    VALUES ('zone_1', 'Main Vegetable Beds', 'switch.garden_valve_1', 12.0, 8, 15, 45)
                    """
                )
                await db.execute(
                    """
                    INSERT INTO beds (id, zone_id, name, bed_type, width_cm, length_cm, depth_cm, soil_type, moisture_target_pct)
                    VALUES ('bed_1', 'zone_1', 'Raised Bed #1 (Heritage Heirloom)', 'raised_bed', 120.0, 240.0, 30.0, 'loam', 50.0)
                    """
                )
                await db.execute(
                    """
                    INSERT INTO plantings (id, bed_id, crop_id, x_cm, y_cm, quantity, planted_at, current_stage, expected_harvest, notes)
                    VALUES ('plant_1', 'bed_1', 'tomato', 30.0, 30.0, 2, date('now', '-20 days'), 'vegetative', date('now', '+55 days'), 'Vigorous early growth')
                    """
                )
                await db.execute(
                    """
                    INSERT INTO plantings (id, bed_id, crop_id, x_cm, y_cm, quantity, planted_at, current_stage, expected_harvest, notes)
                    VALUES ('plant_2', 'bed_1', 'basil', 30.0, 75.0, 4, date('now', '-15 days'), 'vegetative', date('now', '+45 days'), 'Companion to tomatoes')
                    """
                )

        await db.commit()
        logger.info("Database initialized successfully at %s", db_path)
