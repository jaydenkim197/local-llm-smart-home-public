from __future__ import annotations

import os


def _optional_float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    return float(value) if value else None


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "45"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny.en")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

CONTROL_BACKEND = os.getenv("CONTROL_BACKEND", "simulation").strip().lower()
HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "").rstrip("/")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")
HOME_ASSISTANT_TIMEOUT = float(os.getenv("HOME_ASSISTANT_TIMEOUT", "10"))
HOME_ASSISTANT_AC_COOL_ENTITY = os.getenv("HOME_ASSISTANT_AC_COOL_ENTITY", "").strip()
HOME_ASSISTANT_AC_OFF_ENTITY = os.getenv("HOME_ASSISTANT_AC_OFF_ENTITY", "").strip()
HOME_ASSISTANT_AC_SCENE_RESET_DELAY = float(
    os.getenv("HOME_ASSISTANT_AC_SCENE_RESET_DELAY", "2.0")
)

HOME_LATITUDE = _optional_float("HOME_LATITUDE")
HOME_LONGITUDE = _optional_float("HOME_LONGITUDE")
HOME_ELEVATION_M = float(os.getenv("HOME_ELEVATION_M", "0"))
HOME_TIMEZONE = os.getenv("HOME_TIMEZONE", "Asia/Seoul")
HOME_WINDOW_AZIMUTH_DEG = _optional_float("HOME_WINDOW_AZIMUTH_DEG")

OPEN_METEO_URL = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast").rstrip("/")
OPEN_METEO_TIMEOUT = float(os.getenv("OPEN_METEO_TIMEOUT", "4"))
OPEN_METEO_CACHE_SECONDS = int(os.getenv("OPEN_METEO_CACHE_SECONDS", "600"))
