from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create tables and TimescaleDB hypertable on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Enable TimescaleDB extension (no-op if already enabled)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))

        # Create hypertable — idempotent: if_not_exists=true
        await conn.execute(
            text(
                "SELECT create_hypertable('sensor_readings', 'recorded_at', "
                "if_not_exists => TRUE);"
            )
        )

        # Indexes
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_sensor_readings_recorded_at "
                "ON sensor_readings (recorded_at DESC);"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_predictions_predicted_at "
                "ON predictions (predicted_at DESC);"
            )
        )