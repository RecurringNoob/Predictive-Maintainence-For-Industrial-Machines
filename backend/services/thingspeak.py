"""
ThingSpeak REST client.

Field mapping (current hardware):
  field1 → air temperature (°C)
  field2 → humidity (%) — used only as a raw reading; NOT fed to the ML model

Stub mode activates automatically when:
  - THINGSPEAK_CHANNEL_ID / THINGSPEAK_READ_API_KEY are not set, OR
  - the HTTP request fails (network down, channel unreachable)

Set USE_THINGSPEAK_STUB=true in .env to force stub mode regardless.
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ASSUMED_FEATURE_DEFAULTS: dict[str, float] = {
    "process_temp_k": 0.0,     # calculated at parse time as air_temp_k + 10
    "rpm": 1500.0,
    "torque_nm": 40.0,
    "tool_wear_min": 0.0,
}


@dataclass
class ThingSpeakReading:
    """Raw parsed reading from ThingSpeak, before DB persistence."""
    air_temp_celsius: float
    humidity_pct: float
    timestamp_utc: str
    air_temp_k: float = 0.0
    process_temp_k: float = 0.0
    rpm: float = ASSUMED_FEATURE_DEFAULTS["rpm"]
    torque_nm: float = ASSUMED_FEATURE_DEFAULTS["torque_nm"]
    tool_wear_min: float = 0.0
    assumed_features: list[str] = field(default_factory=list)
    is_stub: bool = False   # surfaced in API responses / frontend warning badge


# ---------------------------------------------------------------------------
# Stub
# ---------------------------------------------------------------------------

class _ThingSpeakStub:
    """
    Generates plausible sensor readings so the full pipeline stays exercisable
    (poller → ML → SSE → dashboard) without a live ThingSpeak channel.

    Values oscillate around typical operating points with Gaussian noise so
    the Random Forest sees realistic feature distributions.
    """

    # Sinusoidal cycle length (seconds) — makes the live chart visually dynamic
    _CYCLE_S: float = 60.0

    _BASE_AIR_C: float = 27.0       # ≈ 300 K
    _BASE_HUMIDITY: float = 55.0

    def get_reading(self) -> ThingSpeakReading:
        t = time.monotonic()
        phase = (t % self._CYCLE_S) / self._CYCLE_S * 2 * math.pi

        air_c = self._BASE_AIR_C + 2.0 * math.sin(phase) + random.gauss(0, 0.3)
        humidity = self._BASE_HUMIDITY + 3.0 * math.sin(phase * 0.7) + random.gauss(0, 0.5)
        air_k = air_c + 273.15

        return ThingSpeakReading(
            air_temp_celsius=round(air_c, 2),
            humidity_pct=round(max(0.0, min(100.0, humidity)), 2),
            timestamp_utc=_utc_now_iso(),
            air_temp_k=round(air_k, 3),
            process_temp_k=round(air_k + 10.0, 3),
            rpm=ASSUMED_FEATURE_DEFAULTS["rpm"],
            torque_nm=ASSUMED_FEATURE_DEFAULTS["torque_nm"],
            tool_wear_min=0.0,   # poller owns this counter
            assumed_features=["process_temp_k", "rpm", "torque_nm", "tool_wear_min"],
            is_stub=True,
        )


_stub = _ThingSpeakStub()   # module-level singleton (stateless here; poller owns tool_wear)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _credentials_configured() -> bool:
    return bool(settings.thingspeak_channel_id and settings.thingspeak_read_api_key)


# ---------------------------------------------------------------------------
# Public API  (iot_poller imports only this)
# ---------------------------------------------------------------------------

async def fetch_latest() -> ThingSpeakReading | None:
    """
    Fetch the single most recent feed entry from ThingSpeak.

    Returns a stub reading (is_stub=True) instead of None when the channel
    is unreachable, so the poller pipeline keeps running during outages.
    Returns None only when the response payload is structurally invalid
    (a bug we should not silently paper over with fake data).
    """
    # ── Fast-path: no credentials → stub immediately ──────────────────────
    if not _credentials_configured():
        logger.warning(
            "ThingSpeak credentials not configured "
            "(THINGSPEAK_CHANNEL_ID / THINGSPEAK_READ_API_KEY). "
            "Returning stub reading."
        )
        return _stub.get_reading()

    # ── Network call ──────────────────────────────────────────────────────
    url = settings.thingspeak_url
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.warning(
            "ThingSpeak unreachable (%s). Returning stub reading so the "
            "pipeline keeps running.",
            exc,
        )
        return _stub.get_reading()

    # ── Parse ─────────────────────────────────────────────────────────────
    feeds = body.get("feeds", [])
    if not feeds:
        logger.warning(
            "ThingSpeak returned 0 feeds for channel %s. Returning stub reading.",
            settings.thingspeak_channel_id,
        )
        return _stub.get_reading()

    feed = feeds[0]
    try:
        air_c = float(feed["field1"])
        humidity = float(feed["field2"])
    except (KeyError, TypeError, ValueError) as exc:
        # Malformed payload — don't silently substitute fake data; let the
        # poller skip this cycle (returns None, same as before).
        logger.error(
            "Could not parse ThingSpeak feed fields: %s | raw: %s", exc, feed
        )
        return None

    air_k = air_c + 273.15

    return ThingSpeakReading(
        air_temp_celsius=air_c,
        humidity_pct=humidity,
        timestamp_utc=feed.get("created_at", ""),
        air_temp_k=air_k,
        process_temp_k=air_k + 10.0,
        rpm=ASSUMED_FEATURE_DEFAULTS["rpm"],
        torque_nm=ASSUMED_FEATURE_DEFAULTS["torque_nm"],
        tool_wear_min=0.0,
        assumed_features=["process_temp_k", "rpm", "torque_nm", "tool_wear_min"],
        is_stub=False,
    )