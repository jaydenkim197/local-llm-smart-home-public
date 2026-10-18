from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from app.config import HOME_BRIGHT_LUX_THRESHOLD, HOME_DARK_LUX_THRESHOLD
from services.solar import build_solar_context


STATE_ENTITY_MAP = {
    "temperature_c": "sensor.aqara_temp_humidity_sensor_t1_temperature",
    "humidity_percent": "sensor.aqara_temp_humidity_sensor_t1_humidity",
    "illuminance_lux": "sensor.aqara_light_detection_sensor_t1_illuminance",
    "curtain": "cover.aqara_curtain_controller",
}

DARK_LUX_THRESHOLD = HOME_DARK_LUX_THRESHOLD
BRIGHT_LUX_THRESHOLD = HOME_BRIGHT_LUX_THRESHOLD
HOT_C_THRESHOLD = 28.0
HUMID_PERCENT_THRESHOLD = 65.0


def build_home_context(states: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    by_entity_id = {state.get("entity_id"): state for state in states}
    temperature = _numeric_state(by_entity_id.get(STATE_ENTITY_MAP["temperature_c"]))
    humidity = _numeric_state(by_entity_id.get(STATE_ENTITY_MAP["humidity_percent"]))
    illuminance = _numeric_state(by_entity_id.get(STATE_ENTITY_MAP["illuminance_lux"]))
    curtain_state = by_entity_id.get(STATE_ENTITY_MAP["curtain"])

    curtain = {
        "state": curtain_state.get("state", "unknown") if curtain_state else "unknown",
        "position": (curtain_state.get("attributes") or {}).get("current_position") if curtain_state else None,
    }

    return {
        "source": "home_assistant",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "living_room": {
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "illuminance_lux": illuminance,
            "curtain": curtain,
        },
        "derived": {
            "is_dark": _compare(illuminance, "lt", DARK_LUX_THRESHOLD),
            "is_bright": _compare(illuminance, "gt", BRIGHT_LUX_THRESHOLD),
            "is_hot": _compare(temperature, "gt", HOT_C_THRESHOLD),
            "is_humid": _compare(humidity, "gt", HUMID_PERCENT_THRESHOLD),
        },
        "solar": build_solar_context(),
    }


def build_simulation_home_context(devices: Dict[str, Any]) -> Dict[str, Any]:
    curtain = devices.get("cover.living_room_curtain", {})
    temperature = devices.get("sensor.temperature", {}).get("value")
    humidity = devices.get("sensor.humidity", {}).get("value")
    illuminance = devices.get("sensor.illuminance", {}).get("value")
    return {
        "source": "simulation",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "living_room": {
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "illuminance_lux": illuminance,
            "curtain": {
                "state": curtain.get("state", "unknown"),
                "position": curtain.get("position"),
            },
        },
        "derived": {
            "is_dark": _compare(illuminance, "lt", DARK_LUX_THRESHOLD),
            "is_bright": _compare(illuminance, "gt", BRIGHT_LUX_THRESHOLD),
            "is_hot": _compare(temperature, "gt", HOT_C_THRESHOLD),
            "is_humid": _compare(humidity, "gt", HUMID_PERCENT_THRESHOLD),
        },
        "solar": build_solar_context(),
    }


def unavailable_home_context(error: str) -> Dict[str, Any]:
    return {
        "source": "unavailable",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "living_room": {},
        "derived": {},
        "error": error,
    }


def _numeric_state(state: Dict[str, Any] | None) -> float | None:
    if not state or state.get("state") in {None, "unknown", "unavailable"}:
        return None
    try:
        return float(state["state"])
    except (TypeError, ValueError):
        return None


def _compare(value: float | None, operation: str, threshold: float) -> bool | None:
    if value is None:
        return None
    if operation == "lt":
        return value < threshold
    return value > threshold
