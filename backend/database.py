from collections.abc import AsyncGenerator
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

if _is_sqlite:
    from sqlalchemy.pool import StaticPool
    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
else:
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
    """Create tables on startup. TimescaleDB is used when available (self-hosted
    PostgreSQL), and silently skipped on managed databases like Neon that don't
    support it. Plain PostgreSQL works fine for typical sensor ingestion volumes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        if not _is_sqlite:
            try:
                await conn.execute(
                    text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
                )
                await conn.execute(
                    text(
                        "SELECT create_hypertable('sensor_readings', 'recorded_at', "
                        "if_not_exists => TRUE);"
                    )
                )
                logger.info("TimescaleDB hypertable enabled for sensor_readings.")
            except Exception as exc:
                # TimescaleDB not available (e.g. Neon, standard RDS) —
                # plain PostgreSQL indexes are sufficient for this workload.
                logger.info(
                    "TimescaleDB not available (%s). "
                    "Continuing with standard PostgreSQL.",
                    exc,
                )

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
        logger.info("Database tables and indexes ready.")