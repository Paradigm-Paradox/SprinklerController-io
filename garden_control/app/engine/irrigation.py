import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, List
import aiosqlite

from app.config import AppConfig
from app.engine.ha_client import HomeAssistantClient

logger = logging.getLogger("gardencontrol.irrigation")

class ActiveRun:
    def __init__(
        self,
        run_id: str,
        zone_id: str,
        total_duration_sec: int,
        cycle_sec: int,
        soak_sec: int,
        flow_rate_lpm: float,
        valve_entity: Optional[str]
    ):
        self.run_id = run_id
        self.zone_id = zone_id
        self.total_duration_sec = total_duration_sec
        self.cycle_sec = cycle_sec
        self.soak_sec = soak_sec
        self.flow_rate_lpm = flow_rate_lpm
        self.valve_entity = valve_entity
        self.start_time = datetime.utcnow()
        self.phase: str = "starting" # starting, watering, soaking, completed, aborted
        self.elapsed_watering_sec: int = 0
        self.current_pulse: int = 1
        self.total_pulses: int = max(1, (total_duration_sec + cycle_sec - 1) // cycle_sec) if cycle_sec > 0 else 1
        self.task: Optional[asyncio.Task] = None

class IrrigationDispatcher:
    def __init__(self, config: AppConfig, ha_client: HomeAssistantClient):
        self.config = config
        self.ha = ha_client
        self.active_runs: Dict[str, ActiveRun] = {}
        self._lock = asyncio.Lock()

    async def get_active_runs_summary(self) -> List[dict]:
        """Return snapshot of currently running irrigation tasks."""
        async with self._lock:
            runs = []
            for r in self.active_runs.values():
                runs.append({
                    "run_id": r.run_id,
                    "zone_id": r.zone_id,
                    "phase": r.phase,
                    "elapsed_watering_sec": r.elapsed_watering_sec,
                    "total_duration_sec": r.total_duration_sec,
                    "current_pulse": r.current_pulse,
                    "total_pulses": r.total_pulses,
                    "estimated_liters": round((r.elapsed_watering_sec / 60.0) * r.flow_rate_lpm, 2)
                })
            return runs

    async def trigger_zone(
        self,
        zone_id: str,
        duration_minutes: Optional[int] = None,
        use_cycle_and_soak: bool = True
    ) -> ActiveRun:
        """Initiate an irrigation event with optional cycle-and-soak."""
        async with self._lock:
            # Check if zone is already running
            if zone_id in self.active_runs:
                raise ValueError(f"Zone {zone_id} is already actively irrigating")

            # Check concurrency limits
            active_watering_count = sum(1 for r in self.active_runs.values() if r.phase == "watering")
            if active_watering_count >= self.config.max_concurrent_zones:
                raise ValueError(f"Max concurrent active zones ({self.config.max_concurrent_zones}) reached")

            # Find zone config
            zc = next((z for z in self.config.zones if z.id == zone_id), None)
            duration_min = duration_minutes or (zc.max_duration_minutes if zc else 20)
            cycle_min = zc.cycle_minutes if (zc and use_cycle_and_soak) else duration_min
            soak_min = zc.soak_minutes if (zc and use_cycle_and_soak) else 0
            flow_lpm = zc.flow_rate_lpm if zc else 12.0
            valve_ent = zc.valve_entity if zc else None

            # Verify cistern level interlock if configured
            if self.config.cistern_sensor_entity:
                state = await self.ha.get_entity_state(self.config.cistern_sensor_entity)
                if state and state.get("state"):
                    try:
                        level = float(state["state"])
                        if level < self.config.cistern_minimum_pct:
                            raise ValueError(
                                f"Cistern water level ({level}%) is below minimum threshold ({self.config.cistern_minimum_pct}%)"
                            )
                    except ValueError:
                        pass

            run_id = str(uuid.uuid4())[:8]
            run = ActiveRun(
                run_id=run_id,
                zone_id=zone_id,
                total_duration_sec=duration_min * 60,
                cycle_sec=cycle_min * 60,
                soak_sec=soak_min * 60,
                flow_rate_lpm=flow_lpm,
                valve_entity=valve_ent
            )
            self.active_runs[zone_id] = run
            run.task = asyncio.create_task(self._execute_run(run))
            logger.info("Triggered irrigation for zone %s (Run %s, %d min)", zone_id, run_id, duration_min)
            return run

    async def stop_zone(self, zone_id: str, reason: str = "manual_stop"):
        """Emergency or manual halt for an active irrigation zone."""
        run = self.active_runs.get(zone_id)
        if run:
            logger.warning("Stopping zone %s (Run %s) due to: %s", zone_id, run.run_id, reason)
            if run.task and not run.task.done():
                run.task.cancel()
            if run.valve_entity:
                await self.ha.set_switch(run.valve_entity, False)
            run.phase = "aborted"
            await self._record_run_completion(run, status=f"aborted_{reason}")
            async with self._lock:
                self.active_runs.pop(zone_id, None)

    async def _execute_run(self, run: ActiveRun):
        """Asynchronous execution loop for cycle-and-soak watering."""
        try:
            remaining_sec = run.total_duration_sec
            pulse_idx = 1

            while remaining_sec > 0:
                run.current_pulse = pulse_idx
                pulse_duration = min(remaining_sec, run.cycle_sec)

                # WATERING PHASE
                run.phase = "watering"
                if run.valve_entity:
                    await self.ha.set_switch(run.valve_entity, True)
                logger.info("Zone %s: pulse %d watering for %ds", run.zone_id, pulse_idx, pulse_duration)

                # Sleep in 1-second ticks to monitor cancellations & track elapsed time
                for _ in range(pulse_duration):
                    await asyncio.sleep(1)
                    run.elapsed_watering_sec += 1
                    remaining_sec -= 1

                # Turn valve off after pulse
                if run.valve_entity:
                    await self.ha.set_switch(run.valve_entity, False)

                # SOAK PHASE (if water remains)
                if remaining_sec > 0 and run.soak_sec > 0:
                    run.phase = "soaking"
                    logger.info("Zone %s: soaking for %ds", run.zone_id, run.soak_sec)
                    await asyncio.sleep(run.soak_sec)

                pulse_idx += 1

            run.phase = "completed"
            await self._record_run_completion(run, status="completed")
            logger.info("Zone %s irrigation run %s completed successfully", run.zone_id, run.run_id)

        except asyncio.CancelledError:
            logger.info("Zone %s irrigation task was cancelled", run.zone_id)
            if run.valve_entity:
                await self.ha.set_switch(run.valve_entity, False)
            raise
        except Exception as e:
            logger.error("Error during zone %s execution: %s", run.zone_id, e)
            if run.valve_entity:
                await self.ha.set_switch(run.valve_entity, False)
            await self._record_run_completion(run, status="error")
        finally:
            async with self._lock:
                self.active_runs.pop(run.zone_id, None)

    async def _record_run_completion(self, run: ActiveRun, status: str):
        """Persist finished run to database."""
        try:
            liters = (run.elapsed_watering_sec / 60.0) * run.flow_rate_lpm
            async with aiosqlite.connect(self.config.database_path) as db:
                await db.execute(
                    """
                    INSERT INTO irrigation_runs (
                        id, zone_id, trigger_source, start_time, end_time,
                        duration_seconds, estimated_liters, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run.run_id,
                        run.zone_id,
                        "manual",
                        run.start_time.isoformat(),
                        datetime.utcnow().isoformat(),
                        run.elapsed_watering_sec,
                        round(liters, 2),
                        status
                    )
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed recording irrigation run to DB: %s", e)
