from datetime import datetime

from pydantic import BaseModel

from schemas.sensor import SensorReadingResponse


class PredictionResponse(BaseModel):
    id: int
    reading_id: int
    predicted_at: datetime
    failure_type: str
    confidence: float | None
    model_version: str

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class PredictionListResponse(BaseModel):
    data: list[PredictionResponse]
    total: int


class PredictResponse(BaseModel):
    """Response for POST /predict — bundles both the stored reading and prediction."""
    reading: SensorReadingResponse
    prediction: PredictionResponse