"""
ThingSpeak REST client.

Field mapping (current hardware):
  field1 → air temperature (°C)
  field2 → humidity (%) — used only as a raw reading; NOT fed to the ML model
"""

import logging
from dataclasses import dataclass, field

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Features the model needs that the DHT11 cannot supply.
# Extend this list as sensors are added to the ESP32.
ASSUMED_FEATURE_DEFAULTS: dict[str, float] = {
    "process_temp_k": 0.0,     # calculated at parse time as air_temp_k + 10
    "rpm": 1500.0,
    "torque_nm": 40.0,
    "tool_wear_min": 0.0,       # incremented by poller, not hardcoded here
}


@dataclass
class ThingSpeakReading:
    """Raw parsed reading from ThingSpeak, before DB persistence."""
    air_temp_celsius: float
    humidity_pct: float
    timestamp_utc: str
    # Derived / assumed fields populated by the poller
    air_temp_k: float = 0.0
    process_temp_k: float = 0.0
    rpm: float = ASSUMED_FEATURE_DEFAULTS["rpm"]
    torque_nm: float = ASSUMED_FEATURE_DEFAULTS["torque_nm"]
    tool_wear_min: float = 0.0
    assumed_features: list[str] = field(default_factory=list)


async def fetch_latest() -> ThingSpeakReading | None:
    """
    Fetch the single most recent feed entry from ThingSpeak.
    Returns None if the channel has no data or if the request fails.
    """
    url = settings.thingspeak_url
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("ThingSpeak request failed: %s", exc)
        return None

    feeds = body.get("feeds", [])
    if not feeds:
        logger.warning("ThingSpeak returned 0 feeds for channel %s", settings.thingspeak_channel_id)
        return None

    feed = feeds[0]
    try:
        air_c = float(feed["field1"])
        humidity = float(feed["field2"])
    except (KeyError, TypeError, ValueError) as exc:
        logger.error("Could not parse ThingSpeak feed fields: %s | raw: %s", exc, feed)
        return None

    air_k = air_c + 273.15

    reading = ThingSpeakReading(
        air_temp_celsius=air_c,
        humidity_pct=humidity,
        timestamp_utc=feed.get("created_at", ""),
        air_temp_k=air_k,
        # process_temp is approximated — thermocouple sensor not yet wired
        process_temp_k=air_k + 10.0,
        rpm=ASSUMED_FEATURE_DEFAULTS["rpm"],
        torque_nm=ASSUMED_FEATURE_DEFAULTS["torque_nm"],
        # tool_wear_min injected by the poller (stateful increment)
        tool_wear_min=0.0,
        assumed_features=["process_temp_k", "rpm", "torque_nm", "tool_wear_min"],
    )
    return reading