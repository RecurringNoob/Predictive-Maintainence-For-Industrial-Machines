from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        CheckConstraint("machine_type IN ('L', 'M', 'H')", name="ck_machine_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    machine_type: Mapped[str] = mapped_column(String(1), nullable=False)
    air_temp_k: Mapped[float] = mapped_column(Float, nullable=False)
    process_temp_k: Mapped[float] = mapped_column(Float, nullable=False)
    rpm: Mapped[float] = mapped_column(Float, nullable=False)
    torque_nm: Mapped[float] = mapped_column(Float, nullable=False)
    tool_wear_min: Mapped[float] = mapped_column(Float, nullable=False)
    # 'iot' | 'manual'
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="iot")
    # Comma-separated names of features that were assumed (not from real sensor)
    assumed_features: Mapped[str | None] = mapped_column(String(255), nullable=True)

    predictions: Mapped[list["Prediction"]] = relationship(  # noqa: F821
        back_populates="reading", cascade="all, delete-orphan"
    )