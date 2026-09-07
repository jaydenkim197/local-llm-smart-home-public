from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from zoneinfo import ZoneInfo

from astral import Observer
from astral.sun import azimuth, elevation, sun

from app.config import (
    HOME_ELEVATION_M,
    HOME_LATITUDE,
    HOME_LONGITUDE,
    HOME_TIMEZONE,
    HOME_WINDOW_AZIMUTH_DEG,
)


def build_solar_context(now: datetime | None = None) -> Dict[str, Any]:
    if HOME_LATITUDE is None or HOME_LONGITUDE is None:
        return {"source": "unavailable", "reason": "Home coordinates are not configured"}

    local_zone = ZoneInfo(HOME_TIMEZONE)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    local_now = current.astimezone(local_zone)
    observer = Observer(HOME_LATITUDE, HOME_LONGITUDE, HOME_ELEVATION_M)
    today = sun(observer, date=local_now.date(), tzinfo=local_zone)

    if local_now < today["sunrise"]:
        next_event = "sunrise"
        next_event_at = today["sunrise"]
    elif local_now < today["sunset"]:
        next_event = "sunset"
        next_event_at = today["sunset"]
    else:
        tomorrow = sun(observer, date=local_now.date() + timedelta(days=1), tzinfo=local_zone)
        next_event = "sunrise"
        next_event_at = tomorrow["sunrise"]

    solar_azimuth = round(azimuth(observer, local_now), 2)
    solar_elevation = round(elevation(observer, local_now), 2)
    window_delta = _angular_difference(solar_azimuth, HOME_WINDOW_AZIMUTH_DEG)
    direct_sun_possible = None
    if window_delta is not None:
        direct_sun_possible = solar_elevation > 0 and window_delta <= 60

    return {
        "source": "local_astral",
        "timezone": HOME_TIMEZONE,
        "local_time": local_now.isoformat(),
        "sunrise": today["sunrise"].isoformat(),
        "sunset": today["sunset"].isoformat(),
        "is_daylight": today["sunrise"] <= local_now < today["sunset"],
        "azimuth_deg": solar_azimuth,
        "elevation_deg": solar_elevation,
        "next_event": next_event,
        "next_event_at": next_event_at.isoformat(),
        "minutes_until_next_event": max(0, round((next_event_at - local_now).total_seconds() / 60)),
        "living_room_window_azimuth_deg": HOME_WINDOW_AZIMUTH_DEG,
        "sun_to_window_angle_deg": window_delta,
        "direct_sun_possible": direct_sun_possible,
    }


def _angular_difference(first: float, second: float | None) -> float | None:
    if second is None:
        return None
    return round(abs((first - second + 180) % 360 - 180), 2)
