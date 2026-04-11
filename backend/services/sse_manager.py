"""
SSE Manager — tracks connected clients and broadcasts events.

Each client that hits GET /stream gets its own asyncio.Queue.
When the IoT poller produces a new reading or prediction, it calls
sse_manager.broadcast_*() which puts a message onto every active queue.
The /stream router drains each client's queue and streams it.
"""

import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _default_serialiser(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


class SSEManager:
    def __init__(self) -> None:
        self._clients: set[asyncio.Queue] = set()

    def connect(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._clients.add(q)
        logger.debug("SSE client connected. Total: %d", len(self._clients))
        return q

    def disconnect(self, q: asyncio.Queue) -> None:
        self._clients.discard(q)
        logger.debug("SSE client disconnected. Total: %d", len(self._clients))

    async def _broadcast(self, event: str, data: dict) -> None:
        if not self._clients:
            return
        payload = f"event: {event}\ndata: {json.dumps(data, default=_default_serialiser)}\n\n"
        dead: list[asyncio.Queue] = []
        for q in self._clients:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                # Slow consumer — drop and mark for removal
                dead.append(q)
        for q in dead:
            self._clients.discard(q)
            logger.warning("Dropped slow SSE client (queue full)")

    async def broadcast_reading(self, reading) -> None:
        data = {
            "id": reading.id,
            "recorded_at": reading.recorded_at,
            "machine_type": reading.machine_type,
            "air_temp_k": reading.air_temp_k,
            "process_temp_k": reading.process_temp_k,
            "rpm": reading.rpm,
            "torque_nm": reading.torque_nm,
            "tool_wear_min": reading.tool_wear_min,
            "source": reading.source,
            "assumed_features": (
                [f.strip() for f in reading.assumed_features.split(",")]
                if reading.assumed_features
                else []
            ),
        }
        await self._broadcast("reading", data)

    async def broadcast_prediction(self, prediction) -> None:
        data = {
            "id": prediction.id,
            "reading_id": prediction.reading_id,
            "predicted_at": prediction.predicted_at,
            "failure_type": prediction.failure_type,
            "confidence": prediction.confidence,
            "model_version": prediction.model_version,
        }
        await self._broadcast("prediction", data)

    @property
    def client_count(self) -> int:
        return len(self._clients)


# Module-level singleton
sse_manager = SSEManager()