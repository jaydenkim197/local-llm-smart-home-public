from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TextCommandRequest(BaseModel):
    text: str = Field(..., min_length=1)


class DeviceCommand(BaseModel):
    entity_id: str
    action: str
    value: Optional[Any] = None


class ParsedCommand(BaseModel):
    intent: Optional[str] = None
    commands: List[DeviceCommand]
    response: Optional[str] = None


class CommandResponse(BaseModel):
    input_text: str
    parsed: Dict[str, Any]
    result: Dict[str, Any]
    devices: Dict[str, Any]
    llm_mode: str
    llm_trace: Dict[str, Any]
    home_context: Dict[str, Any]


class AudioCommandResponse(CommandResponse):
    transcript: str
    stt_mode: str
