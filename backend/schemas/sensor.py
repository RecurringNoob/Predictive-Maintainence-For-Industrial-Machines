from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


MachineType = Literal["L", "M", "H"]

VALID_FAILURE_TYPES = {
    "No Failure",
    "Heat Dissipation Failure",
    "Power Failure",
    "Overstrain Failure",
    "Tool Wear Failure",
    "Random Failures",
}


class SensorReadingCreate(BaseModel):
    machine_type: MachineType
    air_temp_k: float = Field(..., gt=200, lt=500, description="Air temperature in Kelvin")
    process_temp_k: float = Field(..., gt=200, lt=500, description="Process temperature in Kelvin")
    rpm: float = Field(..., gt=0, lt=5000, description="Rotational speed in RPM")
    torque_nm: float = Field(..., ge=0, lt=200, description="Torque in Newton-metres")
    tool_wear_min: float = Field(..., ge=0, lt=300, description="Tool wear in minutes")
    source: Literal["iot", "manual"] = "manual"

    @field_validator("process_temp_k")
    @classmethod
    def process_temp_must_exceed_air(cls, v: float, info) -> float:
        air = info.data.get("air_temp_k")
        if air is not None and v < air:
            raise ValueError("process_temp_k must be >= air_temp_k")
        return v


class SensorReadingResponse(BaseModel):
    id: int
    recorded_at: datetime
    machine_type: str
    air_temp_k: float
    process_temp_k: float
    rpm: float
    torque_nm: float
    tool_wear_min: float
    source: str
    assumed_features: list[str]

    @field_validator("assumed_features", mode="before")
    @classmethod
    def parse_assumed_features(cls, v) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [f.strip() for f in v.split(",") if f.strip()]
        return v

    model_config = {"from_attributes": True}


class SensorReadingListResponse(BaseModel):
    data: list[SensorReadingResponse]
    total: int