from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    CONTROL_BACKEND,
    HOME_ASSISTANT_TIMEOUT,
    HOME_ASSISTANT_AC_COOL_ENTITY,
    HOME_ASSISTANT_AC_OFF_ENTITY,
    HOME_ASSISTANT_AC_SCENE_RESET_DELAY,
    HOME_ASSISTANT_TOKEN,
    HOME_ASSISTANT_URL,
    OLLAMA_MODEL,
    OLLAMA_URL,
    WHISPER_MODEL,
)
from app.devices import DeviceStore
from app.models import AudioCommandResponse, CommandResponse, TextCommandRequest
from services.home_assistant import HomeAssistantAdapter
from services.home_context import build_simulation_home_context
from services.outdoor_context import OutdoorContextProvider
from services.parser import parse_command
from services.stt import transcribe_audio

app = FastAPI(title="Context-Aware Local LLM-Based IoT Control System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = DeviceStore()
adapter = HomeAssistantAdapter(
    HOME_ASSISTANT_URL,
    HOME_ASSISTANT_TOKEN,
    HOME_ASSISTANT_TIMEOUT,
    ac_cool_scene_entity=HOME_ASSISTANT_AC_COOL_ENTITY,
    ac_off_scene_entity=HOME_ASSISTANT_AC_OFF_ENTITY,
    ac_scene_reset_delay=HOME_ASSISTANT_AC_SCENE_RESET_DELAY,
)
outdoor_context = OutdoorContextProvider()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health() -> dict:
    home_assistant_reachable, ollama_reachable = await asyncio.gather(
        adapter.is_available(), _ollama_available()
    )
    return {
        "status": "ok",
        "control_backend": CONTROL_BACKEND,
        "home_assistant_configured": adapter.configured,
        "home_assistant_reachable": home_assistant_reachable,
        "air_conditioner_scene_control_configured": adapter.ac_scene_configured,
        "outdoor_context_configured": outdoor_context.configured,
        "llm_model": OLLAMA_MODEL,
        "ollama_reachable": ollama_reachable,
        "stt_model": WHISPER_MODEL,
        "stt_configured": bool(WHISPER_MODEL),
    }


@app.get("/api/devices")
async def devices() -> dict:
    return {"devices": await _current_devices()}


@app.get("/api/context")
async def context() -> dict:
    return {"home_context": await _home_context()}


@app.post("/api/devices/reset")
async def reset_devices() -> dict:
    return {"devices": await _current_devices(store.reset())}


@app.post("/api/command/text", response_model=CommandResponse)
async def command_text(request: TextCommandRequest) -> CommandResponse:
    home_context = await _home_context()
    parsed, llm_mode, llm_trace = await parse_command(request.text, _supported_entities(), home_context)
    result = await _apply(parsed.get("commands", []))
    return CommandResponse(
        input_text=request.text,
        parsed=parsed,
        result=result,
        devices=await _current_devices(),
        llm_mode=llm_mode,
        llm_trace=llm_trace,
        home_context=home_context,
    )


@app.post("/api/command/audio", response_model=AudioCommandResponse)
async def command_audio(file: UploadFile = File(...)) -> AudioCommandResponse:
    transcript, stt_mode = await transcribe_audio(file)
    home_context = await _home_context()
    parsed, llm_mode, llm_trace = await parse_command(transcript, _supported_entities(), home_context)
    result = await _apply(parsed.get("commands", []))
    return AudioCommandResponse(
        input_text=transcript,
        transcript=transcript,
        parsed=parsed,
        result=result,
        devices=await _current_devices(),
        llm_mode=llm_mode,
        llm_trace=llm_trace,
        home_context=home_context,
        stt_mode=stt_mode,
    )


def _supported_entities() -> set[str] | None:
    if CONTROL_BACKEND == "home_assistant":
        return adapter.supported_entities
    return store.controllable_entities()


async def _apply(commands: list[dict]) -> dict:
    if CONTROL_BACKEND == "home_assistant":
        return await adapter.apply(commands)
    return store.apply(commands)


async def _current_devices(devices: dict | None = None) -> dict:
    current = devices or store.all()
    if CONTROL_BACKEND == "home_assistant":
        return await adapter.overlay_states(current)
    return current


async def _home_context() -> dict:
    if CONTROL_BACKEND == "home_assistant":
        current = await adapter.get_home_context()
    else:
        current = build_simulation_home_context(store.all())
    current["outdoor"] = await outdoor_context.get_context()
    return current


async def _ollama_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
        return True
    except httpx.HTTPError:
        return False
