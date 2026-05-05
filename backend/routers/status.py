"""
routers/status.py — Machine health status endpoint.

GET /v1/status
  Returns the current machine status derived from the latest prediction.
  Falls back gracefully if no data exists yet.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Prediction

logger = logging.getLogger(__name__)
router = APIRouter(tags=["status"])

# Map failure types → human-readable machine status
_FAILURE_STATUS_MAP: dict[str, str] = {
    "No Failure": "Healthy",
    "Heat Dissipation Failure": "Warning",
    "Power Failure": "Warning",
    "Overstrain Failure": "Attention Required",
    "Tool Wear Failure": "Attention Required",
    "Random Failures": "Warning",
}


class StatusResponse(BaseModel):
    status: str
    failure_type: str | None = None
    confidence: float | None = None


@router.get("/status", response_model=StatusResponse)
async def get_status(db: AsyncSession = Depends(get_db)):
    """
    Derives machine status from the most recent ML prediction.

    - Healthy           → No Failure
    - Warning           → Heat Dissipation / Power / Random Failures
    - Attention Required→ Overstrain / Tool Wear Failure
    - Unknown           → No predictions in DB yet
    """
    stmt = select(Prediction).order_by(Prediction.predicted_at.desc()).limit(1)
    row = (await db.execute(stmt)).scalar_one_or_none()

    if row is None:
        return StatusResponse(status="Unknown")

    status = _FAILURE_STATUS_MAP.get(row.failure_type, "Unknown")
    return StatusResponse(
        status=status,
        failure_type=row.failure_type,
        confidence=row.confidence,
    )