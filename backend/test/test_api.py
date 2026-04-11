"""
Integration tests for REST API endpoints.

Uses the async_client fixture from conftest.py which wires up a real FastAPI
app with an in-memory SQLite DB and stub ML model.
"""

import pytest


pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health_ok(self, async_client):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestReadingsEndpoints:
    async def test_list_readings_empty(self, async_client):
        resp = await async_client.get("/v1/readings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["total"] == 0

    async def test_latest_reading_404_when_empty(self, async_client):
        resp = await async_client.get("/v1/readings/latest")
        assert resp.status_code == 404

    async def test_create_reading(self, async_client):
        payload = {
            "machine_type": "M",
            "air_temp_k": 300.0,
            "process_temp_k": 310.0,
            "rpm": 1500.0,
            "torque_nm": 40.0,
            "tool_wear_min": 100.0,
            "source": "manual",
        }
        resp = await async_client.post("/v1/readings", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["machine_type"] == "M"
        assert body["air_temp_k"] == 300.0
        assert body["source"] == "manual"
        assert isinstance(body["id"], int)

    async def test_latest_reading_after_insert(self, async_client):
        payload = {
            "machine_type": "H",
            "air_temp_k": 305.0,
            "process_temp_k": 315.0,
            "rpm": 1800.0,
            "torque_nm": 45.0,
            "tool_wear_min": 50.0,
            "source": "manual",
        }
        await async_client.post("/v1/readings", json=payload)
        resp = await async_client.get("/v1/readings/latest")
        assert resp.status_code == 200
        assert resp.json()["machine_type"] == "H"

    async def test_list_readings_after_insert(self, async_client):
        for _ in range(3):
            await async_client.post(
                "/v1/readings",
                json={
                    "machine_type": "L",
                    "air_temp_k": 298.0,
                    "process_temp_k": 308.0,
                    "rpm": 1200.0,
                    "torque_nm": 35.0,
                    "tool_wear_min": 20.0,
                    "source": "manual",
                },
            )
        resp = await async_client.get("/v1/readings")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 3

    async def test_invalid_reading_rejected(self, async_client):
        resp = await async_client.post(
            "/v1/readings",
            json={
                "machine_type": "Z",   # invalid
                "air_temp_k": 300.0,
                "process_temp_k": 310.0,
                "rpm": 1500.0,
                "torque_nm": 40.0,
                "tool_wear_min": 100.0,
            },
        )
        assert resp.status_code == 422


class TestPredictEndpoint:
    async def test_predict_returns_reading_and_prediction(self, async_client):
        payload = {
            "machine_type": "M",
            "air_temp_k": 300.0,
            "process_temp_k": 310.0,
            "rpm": 1500.0,
            "torque_nm": 40.0,
            "tool_wear_min": 100.0,
            "source": "manual",
        }
        resp = await async_client.post("/v1/predict", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "reading" in body
        assert "prediction" in body
        assert body["prediction"]["failure_type"] == "No Failure"
        assert body["prediction"]["confidence"] is not None
        assert body["reading"]["id"] == body["prediction"]["reading_id"]

    async def test_predict_persists_prediction(self, async_client):
        payload = {
            "machine_type": "L",
            "air_temp_k": 295.0,
            "process_temp_k": 305.0,
            "rpm": 1300.0,
            "torque_nm": 38.0,
            "tool_wear_min": 80.0,
            "source": "manual",
        }
        await async_client.post("/v1/predict", json=payload)
        resp = await async_client.get("/v1/predictions/latest")
        assert resp.status_code == 200
        assert resp.json()["failure_type"] == "No Failure"

    async def test_predict_process_temp_below_air_temp_fails(self, async_client):
        resp = await async_client.post(
            "/v1/predict",
            json={
                "machine_type": "M",
                "air_temp_k": 310.0,
                "process_temp_k": 300.0,   # below air_temp — should fail
                "rpm": 1500.0,
                "torque_nm": 40.0,
                "tool_wear_min": 100.0,
                "source": "manual",
            },
        )
        assert resp.status_code == 422


class TestPredictionsEndpoints:
    async def test_list_predictions_empty(self, async_client):
        resp = await async_client.get("/v1/predictions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["total"] == 0

    async def test_latest_prediction_404_when_empty(self, async_client):
        resp = await async_client.get("/v1/predictions/latest")
        assert resp.status_code == 404