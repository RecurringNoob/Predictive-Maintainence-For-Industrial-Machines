"""
IoT Poller — runs on a fixed interval via APScheduler.

Each tick:
  1. Fetch latest reading from ThingSpeak
  2. Persist SensorReading to DB
  3. Run ML inference
  4. Persist Prediction to DB
  5. Broadcast both via SSE to all connected clients
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import get_settings
from database import AsyncSessionLocal
from models import Prediction, SensorReading
from schemas.sensor import SensorReadingCreate
from services.ml_service import get_ml_service
from services.thingspeak import fetch_latest
from services.sse_manager import sse_manager

logger = logging.getLogger(__name__)
settings = get_settings()

# Stateful tool wear counter — resets to 0 at 250 min (simulates a tool change)
_tool_wear_min: float = 0.0
_TOOL_WEAR_RESET_THRESHOLD: float = 250.0
_TOOL_WEAR_INCREMENT: float = 1.0  # 1 minute of wear per poll cycle


async def _poll_once() -> None:
    global _tool_wear_min

    reading_raw = await fetch_latest()
    if reading_raw is None:
        return

    # Increment simulated tool wear
    _tool_wear_min = (_tool_wear_min + _TOOL_WEAR_INCREMENT) % _TOOL_WEAR_RESET_THRESHOLD
    reading_raw.tool_wear_min = _tool_wear_min

    create_schema = SensorReadingCreate(
        machine_type="M",               # assumed medium-grade until configurable
        air_temp_k=reading_raw.air_temp_k,
        process_temp_k=reading_raw.process_temp_k,
        rpm=reading_raw.rpm,
        torque_nm=reading_raw.torque_nm,
        tool_wear_min=reading_raw.tool_wear_min,
        source="iot",
    )

    ml = get_ml_service()
    result = ml.predict(create_schema)

    async with AsyncSessionLocal() as session:
        # Persist reading
        db_reading = SensorReading(
            machine_type=create_schema.machine_type,
            air_temp_k=create_schema.air_temp_k,
            process_temp_k=create_schema.process_temp_k,
            rpm=create_schema.rpm,
            torque_nm=create_schema.torque_nm,
            tool_wear_min=create_schema.tool_wear_min,
            source="iot",
            assumed_features=",".join(reading_raw.assumed_features),
        )
        session.add(db_reading)
        await session.flush()  # populate db_reading.id

        # Persist prediction
        db_prediction = Prediction(
            reading_id=db_reading.id,
            failure_type=result.failure_type,
            confidence=result.confidence,
            model_version=result.model_version,
        )
        session.add(db_prediction)
        await session.commit()
        await session.refresh(db_reading)
        await session.refresh(db_prediction)

    logger.info(
        "Poll complete | air=%.1fK | wear=%.0f min | → %s (%.2f)",
        create_schema.air_temp_k,
        create_schema.tool_wear_min,
        result.failure_type,
        result.confidence,
    )

    # Broadcast via SSE
    await sse_manager.broadcast_reading(db_reading)
    await sse_manager.broadcast_prediction(db_prediction)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll_once,
        trigger="interval",
        seconds=settings.poll_interval_seconds,
        id="iot_poll",
        max_instances=1,        # prevent overlap if a poll takes too long
        coalesce=True,
    )
    return scheduler