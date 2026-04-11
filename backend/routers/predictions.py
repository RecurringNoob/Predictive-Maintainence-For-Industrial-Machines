from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Prediction, SensorReading
from schemas.prediction import PredictResponse, PredictionListResponse, PredictionResponse
from schemas.sensor import SensorReadingCreate, SensorReadingResponse
from services.ml_service import get_ml_service

router = APIRouter(tags=["predictions"])


@router.get("/predictions", response_model=PredictionListResponse)
async def list_predictions(
    from_dt: datetime | None = Query(None, alias="from"),
    to_dt: datetime | None = Query(None, alias="to"),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Prediction).order_by(Prediction.predicted_at.desc())
    if from_dt:
        stmt = stmt.where(Prediction.predicted_at >= from_dt)
    if to_dt:
        stmt = stmt.where(Prediction.predicted_at <= to_dt)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    return PredictionListResponse(
        data=[PredictionResponse.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/predictions/latest", response_model=PredictionResponse)
async def get_latest_prediction(db: AsyncSession = Depends(get_db)):
    stmt = select(Prediction).order_by(Prediction.predicted_at.desc()).limit(1)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No predictions found")
    return PredictionResponse.model_validate(row)


@router.post("/predict", response_model=PredictResponse)
async def predict(
    payload: SensorReadingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept sensor readings, persist them, run ML inference, persist the prediction,
    and return both. All 6 features must be supplied — no defaults are injected here.
    """
    ml = get_ml_service()
    result = ml.predict(payload)

    db_reading = SensorReading(
        machine_type=payload.machine_type,
        air_temp_k=payload.air_temp_k,
        process_temp_k=payload.process_temp_k,
        rpm=payload.rpm,
        torque_nm=payload.torque_nm,
        tool_wear_min=payload.tool_wear_min,
        source=payload.source,
        assumed_features=None,  # manual submissions have no assumed features
    )
    db.add(db_reading)
    await db.flush()

    db_prediction = Prediction(
        reading_id=db_reading.id,
        failure_type=result.failure_type,
        confidence=result.confidence,
        model_version=result.model_version,
    )
    db.add(db_prediction)
    await db.flush()
    await db.refresh(db_reading)
    await db.refresh(db_prediction)

    return PredictResponse(
        reading=SensorReadingResponse.model_validate(db_reading),
        prediction=PredictionResponse.model_validate(db_prediction),
    )