from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from app.config import (
    HOME_LATITUDE,
    HOME_LONGITUDE,
    OPEN_METEO_CACHE_SECONDS,
    OPEN_METEO_TIMEOUT,
    OPEN_METEO_URL,
)


CURRENT_FIELDS = (
    "temperature_2m",
    "apparent_temperature",
    "precipitation_probability",
    "cloud_cover",
    "wind_speed_10m",
    "shortwave_radiation",
    "direct_radiation",
    "weather_code",
)


class OutdoorContextProvider:
    def __init__(
        self,
        transport: Optional[httpx.AsyncBaseTransport] = None,
        cache_seconds: int = OPEN_METEO_CACHE_SECONDS,
    ) -> None:
        self._transport = transport
        self._cache_seconds = cache_seconds
        self._cached: Dict[str, Any] | None = None
        self._cached_at = 0.0

    @property
    def configured(self) -> bool:
        return HOME_LATITUDE is not None and HOME_LONGITUDE is not None

    async def get_context(self) -> Dict[str, Any]:
        now = time.monotonic()
        if self._cached and now - self._cached_at < self._cache_seconds:
            return self._cached
        if not self.configured:
            return {"source": "unavailable", "reason": "Home coordinates are not configured"}

        params = {
            "latitude": HOME_LATITUDE,
            "longitude": HOME_LONGITUDE,
            "current": ",".join(CURRENT_FIELDS),
            "wind_speed_unit": "ms",
            "timezone": "auto",
        }
        try:
            async with httpx.AsyncClient(
                timeout=OPEN_METEO_TIMEOUT, transport=self._transport
            ) as client:
                response = await client.get(OPEN_METEO_URL, params=params)
                response.raise_for_status()
                payload = response.json()
            context = _normalize(payload)
            self._cached = context
            self._cached_at = now
            return context
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            if self._cached:
                return {**self._cached, "stale": True, "refresh_error": str(exc)}
            return {"source": "unavailable", "reason": str(exc)}


def _normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
    current = payload["current"]
    return {
        "source": "open_meteo",
        "observed_at": current.get("time"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "precipitation_probability_percent": current.get("precipitation_probability"),
        "cloud_cover_percent": current.get("cloud_cover"),
        "wind_speed_mps": current.get("wind_speed_10m"),
        "shortwave_radiation_wm2": current.get("shortwave_radiation"),
        "direct_radiation_wm2": current.get("direct_radiation"),
        "weather_code": current.get("weather_code"),
        "stale": False,
    }
