from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Prediction, SensorReading
from schemas.prediction import PredictResponse, PredictionResponse
from schemas.sensor import (
    SensorReadingCreate,
    SensorReadingListResponse,
    SensorReadingResponse,
)
from services.ml_service import get_ml_service

router = APIRouter(prefix="/readings", tags=["readings"])


@router.get("", response_model=SensorReadingListResponse)
async def list_readings(
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SensorReading).order_by(SensorReading.recorded_at.desc())
    if from_dt:
        stmt = stmt.where(SensorReading.recorded_at >= from_dt)
    if to_dt:
        stmt = stmt.where(SensorReading.recorded_at <= to_dt)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    return SensorReadingListResponse(
        data=[SensorReadingResponse.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/latest", response_model=SensorReadingResponse)
async def get_latest_reading(db: AsyncSession = Depends(get_db)):
    stmt = select(SensorReading).order_by(SensorReading.recorded_at.desc()).limit(1)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No readings found")
    return SensorReadingResponse.model_validate(row)


@router.post("", response_model=SensorReadingResponse, status_code=201)
async def create_reading(
    payload: SensorReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    """Persist a reading without running a prediction (used by firmware bridge)."""
    db_reading = SensorReading(
        machine_type=payload.machine_type,
        air_temp_k=payload.air_temp_k,
        process_temp_k=payload.process_temp_k,
        rpm=payload.rpm,
        torque_nm=payload.torque_nm,
        tool_wear_min=payload.tool_wear_min,
        source=payload.source,
        assumed_features=None,
    )
    db.add(db_reading)
    await db.flush()
    await db.refresh(db_reading)
    return SensorReadingResponse.model_validate(db_reading)