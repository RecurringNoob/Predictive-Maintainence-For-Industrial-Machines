"""
Shared pytest fixtures.

Uses an in-memory SQLite database (via aiosqlite) so tests run without
a real PostgreSQL instance. TimescaleDB-specific DDL (create_hypertable)
is skipped automatically because SQLite doesn't support it.
"""

import pickle
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base, get_db

# ── Patch settings before importing the app ───────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def mock_settings(tmp_path_factory):
    """Return a Settings-like object pointing at test model stubs."""
    tmp = tmp_path_factory.mktemp("ml")

    # Minimal stub model that always predicts "No Failure"
    stub_model = MagicMock()
    stub_model.predict.return_value = np.array(["No Failure"])
    stub_model.predict_proba.return_value = np.array([[0.95, 0.01, 0.01, 0.01, 0.01, 0.01]])

    model_path = tmp / "predictive_maintenance.pkl"
    scaler_path = tmp / "scaler.pkl"

    stub_scaler = MagicMock()
    stub_scaler.transform.return_value = np.zeros((1, 5))

    with open(model_path, "wb") as f:
        pickle.dump(stub_model, f)
    with open(scaler_path, "wb") as f:
        pickle.dump(stub_scaler, f)

    return {
        "model_path": str(model_path),
        "scaler_path": str(scaler_path),
        "model_version": "test-v1",
        "database_url": TEST_DB_URL,
        "thingspeak_channel_id": "TEST",
        "thingspeak_read_api_key": "TEST",
        "poll_interval_seconds": 999,
        "cors_origins": ["http://localhost:5173"],
    }


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session, mock_settings):
    """
    Async HTTP client wired up to the FastAPI app with DB and settings overridden.
    The IoT scheduler is not started.
    """
    with (
        patch("config.get_settings", return_value=MagicMock(**mock_settings)),
        patch("services.iot_poller.create_scheduler", return_value=MagicMock()),
    ):
        from main import app

        app.dependency_overrides[get_db] = lambda: db_session

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client

        app.dependency_overrides.clear()