from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from app.config import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL
from app.schema import COMMAND_SCHEMA


SYSTEM_PROMPT = """
You convert English smart-home requests into JSON only.
Do not explain. Do not use markdown. Return one JSON object.

Available entities:
- light.living_room_main: dimmable living room main light, IR capable
- light.living_room_bulb_1: living room smart bulb
- light.living_room_bulb_2: living room smart bulb
- cover.living_room_curtain: living room curtain
- light.bedroom_1: bedroom 1 main light
- light.bedroom_2: bedroom 2 main light
- light.bedroom_3: bedroom 3 main light
- light.bedroom_4: bedroom 4 main light
- fan.air_purifier: air purifier
- vacuum.robot_cleaner: robot cleaner
- media_player.smart_tv: smart TV
- climate.air_conditioner: air conditioner

Allowed actions:
turn_on, turn_off, set_brightness, set_temperature, set_mode, set_speed,
start_cleaning, stop_cleaning, return_to_dock, open_cover, close_cover, stop_cover.

JSON shape:
{
  "intent": "optional_intent_or_null",
  "commands": [
    {"entity_id": "entity", "action": "action", "value": "optional_value"}
  ],
  "response": "short English confirmation"
}

Rules:
- Use the supplied current home context for context-dependent requests.
- Only propose commands for the supplied available physical actuators.
- Return an empty commands array when the requested state is already satisfied.
- Sensor values are read-only context and never command targets.
- If the user says both living room bulbs, control light.living_room_bulb_1 and light.living_room_bulb_2.
- If the user says living room lights, include the main light and both smart bulbs.
- If the user says curtain, drape, shade, or blind, use cover.living_room_curtain.
- "Everything", "all devices", or "the whole house" means all controllable non-sensor devices, except do not start the robot cleaner unless cleaning or vacuuming is explicitly requested.
- For "turn everything on", turn on all lights, open the living room curtain, turn on the TV, air purifier, and air conditioner.
- For "turn everything off", turn off all lights, close the living room curtain, turn off the TV, air purifier, and air conditioner, and stop_cleaning the robot cleaner.
- If brightness is requested, use set_brightness with an integer 0..100.
- When air conditioning is available physically, it supports only two IR scene presets: turn_on means Cool 24 C and turn_off means Off. Never use set_temperature or set_mode for it.
- Movie mode: TV on, living room curtain closed, all living room lights off, robot cleaner stop_cleaning, air purifier off.
- Away mode: all lights off, living room curtain closed, TV off, air conditioner off, air purifier off, robot cleaner return_to_dock.
- Cleaning mode: robot cleaner start_cleaning and air purifier turn_on.
- Unknown or unsafe requests must return {"intent":"unsupported","commands":[],"response":"I cannot map that request to supported devices."}
"""


PHYSICAL_ACTIONS_BY_ENTITY = {
    "cover.living_room_curtain": {"open_cover", "close_cover", "stop_cover"},
    "climate.air_conditioner": {"turn_on", "turn_off"},
}


async def parse_command(
    text: str,
    supported_entities: Optional[set[str]] = None,
    home_context: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
    llm_user_content = _build_llm_user_content(text, supported_entities, home_context)
    trace: Dict[str, Any] = {
        "input_text": text,
        "model": OLLAMA_MODEL,
        "ollama_url": OLLAMA_URL,
        "system_prompt": SYSTEM_PROMPT.strip(),
        "user_message": text,
        "llm_user_content": llm_user_content,
        "home_context": home_context,
        "raw_model_output": None,
        "parsed_before_normalization": None,
        "parsed_after_normalization": None,
        "normalization_applied": False,
        "policy_applied": False,
        "parsed_after_policy": None,
        "supported_entities": sorted(supported_entities) if supported_entities else None,
        "fallback_used": False,
        "error": None,
    }
    try:
        parsed, raw_model_output = await _parse_with_ollama(llm_user_content)
        trace["raw_model_output"] = raw_model_output
        trace["parsed_before_normalization"] = parsed
        normalized_parsed = _normalize_parsed_command(text, parsed, home_context, supported_entities)
        trace["normalization_applied"] = normalized_parsed != parsed
        parsed = normalized_parsed
        trace["parsed_after_normalization"] = parsed
        policy_parsed = _apply_context_policy(parsed, home_context)
        trace["policy_applied"] = policy_parsed != parsed
        trace["parsed_after_policy"] = policy_parsed
        parsed = policy_parsed
        parsed = _restrict_to_supported_entities(parsed, supported_entities)
        _validate_or_raise(parsed)
        return parsed, f"ollama:{OLLAMA_MODEL}", trace
    except Exception as exc:
        trace["fallback_used"] = True
        trace["error"] = str(exc)
        parsed = _fallback_parse(text)
        trace["parsed_before_normalization"] = parsed
        normalized_parsed = _normalize_parsed_command(text, parsed, home_context, supported_entities)
        trace["normalization_applied"] = normalized_parsed != parsed
        parsed = normalized_parsed
        trace["parsed_after_normalization"] = parsed
        policy_parsed = _apply_context_policy(parsed, home_context)
        trace["policy_applied"] = policy_parsed != parsed
        trace["parsed_after_policy"] = policy_parsed
        parsed = policy_parsed
        parsed = _restrict_to_supported_entities(parsed, supported_entities)
        _validate_or_raise(parsed)
        return parsed, "fallback", trace


async def _parse_with_ollama(user_content: str) -> Tuple[Dict[str, Any], str]:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "format": "json",
        "options": {"temperature": 0.0},
    }
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return json.loads(content), content


def _validate_or_raise(parsed: Dict[str, Any]) -> None:
    try:
        validate(instance=parsed, schema=COMMAND_SCHEMA)
    except ValidationError as exc:
        raise ValueError(f"Invalid command JSON: {exc.message}") from exc


def _restrict_to_supported_entities(
    parsed: Dict[str, Any], supported_entities: Optional[set[str]]
) -> Dict[str, Any]:
    if supported_entities is None:
        return parsed

    commands = parsed.get("commands", [])
    if not commands:
        return parsed

    filtered_commands = []
    for command in commands:
        entity_id = command.get("entity_id")
        if entity_id not in supported_entities:
            continue
        allowed_actions = PHYSICAL_ACTIONS_BY_ENTITY.get(entity_id)
        if allowed_actions is not None and command.get("action") not in allowed_actions:
            continue
        filtered_commands.append(command)
    if filtered_commands:
        return {**parsed, "commands": filtered_commands}
    return {
        "intent": "unsupported",
        "commands": [],
        "response": "That request is not supported by a configured physical device.",
    }


def _normalize_parsed_command(
    text: str,
    parsed: Dict[str, Any],
    home_context: Optional[Dict[str, Any]] = None,
    supported_entities: Optional[set[str]] = None,
) -> Dict[str, Any]:
    normalized = text.lower().strip()
    solar_information = _solar_information_response(normalized, home_context)
    if solar_information:
        return solar_information

    unsupported_environment_command = _unsupported_environment_command(
        normalized, supported_entities
    )
    if unsupported_environment_command:
        return unsupported_environment_command

    explicit_ac_command = _explicit_ac_command(normalized, supported_entities)
    if explicit_ac_command:
        return explicit_ac_command

    explicit_cover_command = _explicit_cover_command(normalized)
    if explicit_cover_command:
        return explicit_cover_command

    contextual_cooling_command = _contextual_cooling_command(
        normalized, home_context, supported_entities
    )
    if contextual_cooling_command:
        return contextual_cooling_command

    contextual_command = _contextual_curtain_command(normalized, home_context)
    if contextual_command:
        return contextual_command

    if not _is_global_request(normalized):
        return parsed

    action = _action_for_text(normalized)
    if action == "turn_on":
        return {
            "intent": "whole_home_on",
            "commands": _whole_home_on_commands(),
            "response": "All controllable devices are on.",
        }
    if action == "turn_off":
        return {
            "intent": "whole_home_off",
            "commands": _whole_home_off_commands(),
            "response": "All controllable devices are off.",
        }
    return parsed


def _solar_information_response(
    text: str, home_context: Optional[Dict[str, Any]]
) -> Dict[str, Any] | None:
    event = None
    if "sunrise" in text:
        event = "sunrise"
    elif "sunset" in text:
        event = "sunset"
    if not event or not home_context:
        return None

    solar = home_context.get("solar", {})
    event_at = solar.get(event)
    if not event_at:
        return None
    try:
        local_time = datetime.fromisoformat(event_at).strftime("%H:%M")
    except (TypeError, ValueError):
        return None

    return {
        "intent": "solar_information",
        "commands": [],
        "response": f"Today's {event} is at {local_time} {solar.get('timezone', '')}.".strip(),
    }


def _build_llm_user_content(
    text: str,
    supported_entities: Optional[set[str]],
    home_context: Optional[Dict[str, Any]],
) -> str:
    actuator_list = sorted(supported_entities) if supported_entities is not None else "all listed entities in simulation"
    context = home_context or {"source": "unavailable"}
    return (
        "Current home context:\n"
        f"{json.dumps(context, ensure_ascii=True, separators=(',', ':'))}\n\n"
        "Available physical actuators:\n"
        f"{json.dumps(actuator_list, ensure_ascii=True)}\n\n"
        "User request:\n"
        f"{text}"
    )


def _contextual_curtain_command(
    text: str, home_context: Optional[Dict[str, Any]]
) -> Dict[str, Any] | None:
    request_kind = _contextual_light_request_kind(text)
    if request_kind is None:
        return None

    if not home_context or home_context.get("source") == "unavailable":
        return _context_unavailable_response()

    derived = home_context.get("derived", {})
    curtain = home_context.get("living_room", {}).get("curtain", {})
    curtain_state = curtain.get("state")

    if request_kind == "increase":
        if derived.get("is_dark") is not True:
            return {
                "intent": "context_no_action",
                "commands": [],
                "response": "The illuminance sensor does not indicate that the room is dark.",
            }
        if curtain_state == "open":
            return {
                "intent": "context_no_action",
                "commands": [],
                "response": "The curtain is already open.",
            }
        return {
            "intent": "increase_natural_light",
            "commands": [{"entity_id": "cover.living_room_curtain", "action": "open_cover"}],
            "response": "I will open the curtain to let in more natural light.",
        }

    if request_kind == "reduce":
        if curtain_state == "closed":
            return {
                "intent": "context_no_action",
                "commands": [],
                "response": "The curtain is already closed.",
            }
        if derived.get("is_bright") is not True:
            return {
                "intent": "context_no_action",
                "commands": [],
                "response": "The illuminance sensor does not indicate excessive brightness.",
            }
        return {
            "intent": "reduce_natural_light",
            "commands": [{"entity_id": "cover.living_room_curtain", "action": "close_cover"}],
            "response": "I will close the curtain to reduce the light.",
        }

    return None


def _contextual_cooling_command(
    text: str,
    home_context: Optional[Dict[str, Any]],
    supported_entities: Optional[set[str]],
) -> Dict[str, Any] | None:
    if not supported_entities or "climate.air_conditioner" not in supported_entities:
        return None
    if not _is_cooling_request(text):
        return None

    if not home_context or home_context.get("source") == "unavailable":
        return _context_unavailable_response()

    if home_context.get("derived", {}).get("is_hot") is not True:
        return {
            "intent": "context_no_action",
            "commands": [],
            "response": "The temperature sensor does not indicate excessive heat.",
        }

    commands = []
    curtain_state = home_context.get("living_room", {}).get("curtain", {}).get("state")
    if curtain_state != "closed" and "cover.living_room_curtain" in supported_entities:
        commands.append({"entity_id": "cover.living_room_curtain", "action": "close_cover"})
    commands.append({"entity_id": "climate.air_conditioner", "action": "turn_on"})
    response = (
        "I will close the curtain and send the Cool 24 C IR preset."
        if len(commands) == 2
        else "I will send the Cool 24 C IR preset."
    )
    return {"intent": "reduce_heat", "commands": commands, "response": response}


def _is_cooling_request(text: str) -> bool:
    if _is_heating_request(text):
        return False

    room_reference = bool(
        re.search(r"\b(living room|room|in here|here|inside|home)\b", text)
    )
    heat_description = bool(
        re.search(r"\b(hot|warm|overheated|stifling|sweltering)\b", text)
    )
    cooling_request = bool(
        re.search(r"\b(cool down|cooler|cool the (?:living )?room|start cooling)\b", text)
    )
    comfort_request = bool(
        re.search(
            r"\b(make|get) (?:it|the (?:living )?room|this room) comfortable\b",
            text,
        )
    )
    comfort_request = comfort_request or bool(
        room_reference
        and re.search(r"\b(make|bring|get|keep)\b", text)
        and re.search(r"\b(comfortable|comfort|pleasant)\b", text)
    )
    discomfort = "uncomfortable" in text and room_reference
    return (heat_description and room_reference) or cooling_request or comfort_request or discomfort


def _is_heating_request(text: str) -> bool:
    return any(
        phrase in text
        for phrase in ["warm up", "warmer", "heating", "turn on the heat", "too cold"]
    )


def _unsupported_environment_command(
    text: str, supported_entities: Optional[set[str]]
) -> Dict[str, Any] | None:
    if not supported_entities or "climate.air_conditioner" not in supported_entities:
        return None

    ac_reference = bool(
        "air conditioner" in text
        or re.search(r"\bac\b", text)
        or "thermostat" in text
    )
    unsupported_ac_capability = ac_reference and bool(
        re.search(r"\b(degree|degrees|temperature|thermostat|fan speed|hvac mode)\b", text)
    )
    if not _is_heating_request(text) and not unsupported_ac_capability:
        return None
    return {
        "intent": "unsupported",
        "commands": [],
        "response": "The configured air conditioner supports only Cool 24 C and Off presets.",
    }


def _contextual_light_request_kind(text: str) -> str | None:
    increase_phrases = [
        "dark",
        "not enough light",
        "not enough natural light",
        "need more light",
        "more daylight",
        "more natural light",
        "feels dim",
        "feel dim",
        "room is dim",
    ]
    reduce_phrases = ["too bright", "very bright", "excessively bright", "glare"]
    if any(phrase in text for phrase in increase_phrases):
        return "increase"
    if any(phrase in text for phrase in reduce_phrases):
        return "reduce"
    return None


def _context_unavailable_response() -> Dict[str, Any]:
    return {
        "intent": "context_unavailable",
        "commands": [],
        "response": "Current sensor context is unavailable, so no contextual action was sent.",
    }


def _apply_context_policy(
    parsed: Dict[str, Any], home_context: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    if not home_context or home_context.get("source") == "unavailable":
        return parsed

    curtain = home_context.get("living_room", {}).get("curtain", {})
    curtain_state = curtain.get("state")
    redundant_actions = set()
    if curtain_state == "open":
        redundant_actions.add("open_cover")
    if curtain_state == "closed":
        redundant_actions.add("close_cover")

    commands = parsed.get("commands", [])
    filtered = [
        command
        for command in commands
        if not (
            command.get("entity_id") == "cover.living_room_curtain"
            and command.get("action") in redundant_actions
        )
    ]
    if len(filtered) == len(commands):
        return parsed
    if filtered:
        return {**parsed, "commands": filtered}
    return {
        "intent": parsed.get("intent") or "context_no_action",
        "commands": [],
        "response": "The curtain is already in the requested state.",
    }


def _explicit_cover_command(text: str) -> Dict[str, Any] | None:
    """Make a single, explicit curtain direction independent of model wording."""
    if not any(
        word in text
        for word in ["curtain", "curtains", "drape", "drapes", "shade", "shades", "blind", "blinds"]
    ):
        return None

    action = _action_for_text(text)
    if action not in {"open_cover", "close_cover", "stop_cover"}:
        return None

    response = {
        "open_cover": "The living room curtain is opening.",
        "close_cover": "The living room curtain is closing.",
        "stop_cover": "The living room curtain is stopping.",
    }[action]
    return {
        "intent": "curtain_control",
        "commands": [{"entity_id": "cover.living_room_curtain", "action": action}],
        "response": response,
    }


def _explicit_ac_command(
    text: str, supported_entities: Optional[set[str]]
) -> Dict[str, Any] | None:
    if not (
        "air conditioner" in text
        or re.search(r"\bac\b", text)
    ):
        return None
    if supported_entities is not None and "climate.air_conditioner" not in supported_entities:
        return None

    action = _action_for_text(text)
    if action not in {"turn_on", "turn_off"}:
        return None
    preset = "Cool 24 C" if action == "turn_on" else "Off"
    return {
        "intent": "air_conditioner_scene_control",
        "commands": [{"entity_id": "climate.air_conditioner", "action": action}],
        "response": f"I sent the {preset} IR preset.",
    }


def _fallback_parse(text: str) -> Dict[str, Any]:
    normalized = text.lower().strip()
    commands: List[Dict[str, Any]] = []
    intent = None

    if any(phrase in normalized for phrase in ["movie", "cinema", "watch a film"]):
        return {
            "intent": "movie_mode",
            "commands": [
                {"entity_id": "media_player.smart_tv", "action": "turn_on"},
                {"entity_id": "cover.living_room_curtain", "action": "close_cover"},
                {"entity_id": "light.living_room_main", "action": "turn_off"},
                {"entity_id": "light.living_room_bulb_1", "action": "turn_off"},
                {"entity_id": "light.living_room_bulb_2", "action": "turn_off"},
                {"entity_id": "vacuum.robot_cleaner", "action": "stop_cleaning"},
                {"entity_id": "fan.air_purifier", "action": "turn_off"},
            ],
            "response": "Movie mode is ready.",
        }

    if any(phrase in normalized for phrase in ["leaving", "away", "out for", "vacation"]):
        return {
            "intent": "away_mode",
            "commands": [
                {"entity_id": "light.living_room_main", "action": "turn_off"},
                {"entity_id": "light.living_room_bulb_1", "action": "turn_off"},
                {"entity_id": "light.living_room_bulb_2", "action": "turn_off"},
                {"entity_id": "light.bedroom_1", "action": "turn_off"},
                {"entity_id": "light.bedroom_2", "action": "turn_off"},
                {"entity_id": "light.bedroom_3", "action": "turn_off"},
                {"entity_id": "light.bedroom_4", "action": "turn_off"},
                {"entity_id": "cover.living_room_curtain", "action": "close_cover"},
                {"entity_id": "media_player.smart_tv", "action": "turn_off"},
                {"entity_id": "climate.air_conditioner", "action": "turn_off"},
                {"entity_id": "fan.air_purifier", "action": "turn_off"},
                {"entity_id": "vacuum.robot_cleaner", "action": "return_to_dock"},
            ],
            "response": "Away mode is active.",
        }

    if any(phrase in normalized for phrase in ["clean", "vacuum"]):
        return {
            "intent": "cleaning_mode",
            "commands": [
                {"entity_id": "vacuum.robot_cleaner", "action": "start_cleaning"},
                {"entity_id": "fan.air_purifier", "action": "turn_on"},
            ],
            "response": "Cleaning has started.",
        }

    if any(phrase in normalized for phrase in ["cooler", "too hot", "cool down"]):
        return {
            "intent": "cooling",
            "commands": [
                {"entity_id": "climate.air_conditioner", "action": "turn_on"},
                {"entity_id": "climate.air_conditioner", "action": "set_temperature", "value": 24},
            ],
            "response": "Cooling is on.",
        }

    if _is_global_request(normalized):
        global_action = _action_for_text(normalized)
        if global_action == "turn_on":
            return {
                "intent": "whole_home_on",
                "commands": _whole_home_on_commands(),
                "response": "All controllable devices are on.",
            }
        if global_action == "turn_off":
            return {
                "intent": "whole_home_off",
                "commands": _whole_home_off_commands(),
                "response": "All controllable devices are off.",
            }

    target_entities = _targets_for_text(normalized)
    action = _action_for_text(normalized)
    brightness = _brightness_for_text(normalized)

    if brightness is not None:
        for entity_id in target_entities or ["light.living_room_main"]:
            if entity_id.startswith("light."):
                commands.append({"entity_id": entity_id, "action": "set_brightness", "value": brightness})
    elif action:
        for entity_id in target_entities:
            commands.append({"entity_id": entity_id, "action": action})

    if commands:
        return {"intent": intent, "commands": commands, "response": "Done."}

    return {
        "intent": "unsupported",
        "commands": [],
        "response": "I cannot map that request to supported devices.",
    }


def _targets_for_text(text: str) -> List[str]:
    if any(word in text for word in ["curtain", "curtains", "drape", "drapes", "shade", "shades", "blind", "blinds"]):
        return ["cover.living_room_curtain"]
    if "living room" in text and ("all" in text or "lights" in text):
        return ["light.living_room_main", "light.living_room_bulb_1", "light.living_room_bulb_2"]
    if "both" in text and ("bulb" in text or "smart bulb" in text):
        return ["light.living_room_bulb_1", "light.living_room_bulb_2"]
    if "bulb 1" in text or "first bulb" in text:
        return ["light.living_room_bulb_1"]
    if "bulb 2" in text or "second bulb" in text:
        return ["light.living_room_bulb_2"]
    if "bulb" in text:
        return ["light.living_room_bulb_1", "light.living_room_bulb_2"]
    if "living room" in text and ("light" in text or "lamp" in text):
        return ["light.living_room_main"]
    for number in range(1, 5):
        if f"bedroom {number}" in text or f"room {number}" in text:
            return [f"light.bedroom_{number}"]
    if "tv" in text:
        return ["media_player.smart_tv"]
    if "air purifier" in text or "purifier" in text:
        return ["fan.air_purifier"]
    if "air conditioner" in text or "ac" in text:
        return ["climate.air_conditioner"]
    return []


def _is_global_request(text: str) -> bool:
    return any(phrase in text for phrase in ["everything", "all devices", "whole house", "entire house", "all controllable"])


def _whole_home_on_commands() -> List[Dict[str, Any]]:
    return [
        {"entity_id": "light.living_room_main", "action": "turn_on"},
        {"entity_id": "light.living_room_bulb_1", "action": "turn_on"},
        {"entity_id": "light.living_room_bulb_2", "action": "turn_on"},
        {"entity_id": "light.bedroom_1", "action": "turn_on"},
        {"entity_id": "light.bedroom_2", "action": "turn_on"},
        {"entity_id": "light.bedroom_3", "action": "turn_on"},
        {"entity_id": "light.bedroom_4", "action": "turn_on"},
        {"entity_id": "cover.living_room_curtain", "action": "open_cover"},
        {"entity_id": "media_player.smart_tv", "action": "turn_on"},
        {"entity_id": "fan.air_purifier", "action": "turn_on"},
        {"entity_id": "climate.air_conditioner", "action": "turn_on"},
    ]


def _whole_home_off_commands() -> List[Dict[str, Any]]:
    return [
        {"entity_id": "light.living_room_main", "action": "turn_off"},
        {"entity_id": "light.living_room_bulb_1", "action": "turn_off"},
        {"entity_id": "light.living_room_bulb_2", "action": "turn_off"},
        {"entity_id": "light.bedroom_1", "action": "turn_off"},
        {"entity_id": "light.bedroom_2", "action": "turn_off"},
        {"entity_id": "light.bedroom_3", "action": "turn_off"},
        {"entity_id": "light.bedroom_4", "action": "turn_off"},
        {"entity_id": "cover.living_room_curtain", "action": "close_cover"},
        {"entity_id": "media_player.smart_tv", "action": "turn_off"},
        {"entity_id": "fan.air_purifier", "action": "turn_off"},
        {"entity_id": "climate.air_conditioner", "action": "turn_off"},
        {"entity_id": "vacuum.robot_cleaner", "action": "stop_cleaning"},
    ]


def _action_for_text(text: str) -> str:
    if any(word in text for word in ["open", "raise"]):
        return "open_cover" if any(cover in text for cover in ["curtain", "curtains", "drape", "drapes", "shade", "shades", "blind", "blinds"]) else "turn_on"
    if any(word in text for word in ["close", "lower", "shut"]):
        return "close_cover" if any(cover in text for cover in ["curtain", "curtains", "drape", "drapes", "shade", "shades", "blind", "blinds"]) else "turn_off"
    if "stop" in text and any(cover in text for cover in ["curtain", "curtains", "drape", "drapes", "shade", "shades", "blind", "blinds"]):
        return "stop_cover"
    if re.search(r"\bturn\b.+\bon\b", text) or re.search(r"\bswitch\b.+\bon\b", text):
        return "turn_on"
    if re.search(r"\bturn\b.+\boff\b", text) or re.search(r"\bswitch\b.+\boff\b", text):
        return "turn_off"
    if any(word in text for word in ["turn off", "switch off", "shut off", "disable"]):
        return "turn_off"
    if any(word in text for word in ["turn on", "switch on", "enable", "start"]):
        return "turn_on"
    return ""


def _brightness_for_text(text: str) -> int | None:
    match = re.search(r"(\d{1,3})\s*(%|percent)", text)
    if match:
        return max(0, min(100, int(match.group(1))))
    if "dim" in text:
        return 25
    if "bright" in text:
        return 90
    return None
