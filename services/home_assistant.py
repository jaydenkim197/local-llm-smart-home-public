from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any, Dict, List, Optional

import httpx

from services.home_context import STATE_ENTITY_MAP, build_home_context, unavailable_home_context


# Logical IDs keep LLM prompts independent from Home Assistant entity names.
CURTAIN_ENTITY_MAP = {
    "cover.living_room_curtain": "cover.aqara_curtain_controller",
}

DISPLAY_ENTITY_MAP = {
    "cover.living_room_curtain": STATE_ENTITY_MAP["curtain"],
    "sensor.temperature": STATE_ENTITY_MAP["temperature_c"],
    "sensor.humidity": STATE_ENTITY_MAP["humidity_percent"],
    "sensor.illuminance": STATE_ENTITY_MAP["illuminance_lux"],
}

CURTAIN_ACTION_MAP = {
    "open_cover": ("cover", "open_cover"),
    "close_cover": ("cover", "close_cover"),
    "stop_cover": ("cover", "stop_cover"),
}


class HomeAssistantAdapter:
    def __init__(
        self,
        url: str,
        token: str,
        timeout: float,
        ac_cool_scene_entity: str = "",
        ac_off_scene_entity: str = "",
        ac_scene_reset_delay: float = 2.0,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._ac_cool_scene_entity = ac_cool_scene_entity
        self._ac_off_scene_entity = ac_off_scene_entity
        self._ac_scene_reset_delay = ac_scene_reset_delay
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self._url and self._token)

    @property
    def supported_entities(self) -> set[str]:
        entities = set(CURTAIN_ENTITY_MAP)
        if self.ac_scene_configured:
            entities.add("climate.air_conditioner")
        return entities

    @property
    def ac_scene_configured(self) -> bool:
        return bool(self._ac_cool_scene_entity and self._ac_off_scene_entity)

    async def is_available(self) -> bool:
        if not self.configured:
            return False
        try:
            async with self._client() as client:
                response = await client.get("/api/")
                response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False

    async def apply(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.configured:
            return {
                "applied": [],
                "errors": [{"error": "Home Assistant is not configured. Set HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN."}],
                "success": False,
            }

        applied = []
        errors = []
        async with self._client() as client:
            for command in commands:
                logical_id = command.get("entity_id")
                action = command.get("action")
                actual_id, service, metadata = await self._physical_target(client, logical_id, action)
                if not actual_id:
                    errors.append({"entity_id": logical_id, "action": action, "error": "Entity is not mapped to physical hardware"})
                    continue
                if not service:
                    errors.append({"entity_id": logical_id, "action": action, "error": "Action is not supported by physical hardware"})
                    continue

                domain, service_name = service
                try:
                    if metadata.pop("momentary_trigger", False):
                        prelude_entity_id = metadata.pop("prelude_entity_id", None)
                        if prelude_entity_id:
                            await self._wait_for_scene_ready(
                                client, prelude_entity_id
                            )
                            await self._activate_scene(client, prelude_entity_id)
                            await asyncio.sleep(self._ac_scene_reset_delay)
                        await self._wait_for_scene_ready(client, actual_id)
                        await self._activate_scene(client, actual_id)
                        service_label = (
                            "AC Off scene -> AC Cool 24 scene"
                            if prelude_entity_id
                            else "AC Off scene"
                        )
                    else:
                        response = await client.post(
                            f"/api/services/{domain}/{service_name}",
                            json={"entity_id": actual_id},
                        )
                        response.raise_for_status()
                        service_label = f"{domain}.{service_name}"
                    applied.append(
                        {
                            "entity_id": logical_id,
                            "home_assistant_entity_id": actual_id,
                            "action": action,
                            "service": service_label,
                        }
                    )
                    applied[-1].update(metadata)
                    if logical_id == "cover.living_room_curtain":
                        applied[-1].update(
                            await self._wait_for_cover_state(client, actual_id, action)
                        )
                except (httpx.HTTPError, ValueError) as exc:
                    errors.append({"entity_id": logical_id, "action": action, "error": str(exc)})

        return {"applied": applied, "errors": errors, "success": not errors}

    async def _activate_scene(
        self, client: httpx.AsyncClient, entity_id: str
    ) -> None:
        trigger = await client.post(
            "/api/services/switch/turn_on", json={"entity_id": entity_id}
        )
        trigger.raise_for_status()

    async def _wait_for_scene_ready(
        self, client: httpx.AsyncClient, entity_id: str
    ) -> None:
        if not entity_id.startswith("switch."):
            raise ValueError(f"Scene trigger is not a switch: {entity_id}")
        for attempt in range(11):
            response = await client.get(f"/api/states/{entity_id}")
            response.raise_for_status()
            state = response.json().get("state")
            if state == "off":
                return
            if state in {"unknown", "unavailable"}:
                raise ValueError(f"Scene trigger is unavailable: {entity_id}")
            if state != "on":
                raise ValueError(f"Scene trigger is not ready: {entity_id} ({state})")
            if attempt < 10:
                await asyncio.sleep(0.5)
        raise ValueError(f"Scene trigger did not return to off: {entity_id}")

    async def _physical_target(
        self, client: httpx.AsyncClient, logical_id: Any, action: Any
    ) -> tuple[str | None, tuple[str, str] | None, Dict[str, Any]]:
        actual_id = CURTAIN_ENTITY_MAP.get(logical_id)
        service = CURTAIN_ACTION_MAP.get(action)
        if actual_id:
            return actual_id, service, {"state_verified": True}

        if logical_id != "climate.air_conditioner" or not self.ac_scene_configured:
            return None, None, {}
        actual_id = {
            "turn_on": self._ac_cool_scene_entity,
            "turn_off": self._ac_off_scene_entity,
        }.get(action)
        if not actual_id:
            return self._ac_cool_scene_entity, None, {}

        preset = "Cool 24 C" if action == "turn_on" else "Off"
        return actual_id, ("switch", "turn_on"), {
            "momentary_trigger": True,
            "prelude_entity_id": (
                self._ac_off_scene_entity if action == "turn_on" else None
            ),
            "state_verified": False,
            "verification": "ir_scene_command_accepted_not_physical_ac_state",
            "preset": preset,
        }

    async def _wait_for_cover_state(
        self, client: httpx.AsyncClient, entity_id: str, action: str
    ) -> Dict[str, Any]:
        expected = {"open_cover": "open", "close_cover": "closed"}.get(action)
        if expected is None:
            return {"settled": True}

        last_state = None
        last_position = None
        for attempt in range(21):
            if attempt:
                await asyncio.sleep(0.75)
            try:
                response = await client.get(f"/api/states/{entity_id}")
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPError:
                break
            last_state = payload.get("state")
            last_position = payload.get("attributes", {}).get("current_position")
            if last_state == expected:
                return {
                    "settled": True,
                    "final_state": last_state,
                    "final_position": last_position,
                }
        return {
            "settled": False,
            "final_state": last_state,
            "final_position": last_position,
        }

    async def overlay_states(self, devices: Dict[str, Any]) -> Dict[str, Any]:
        result = deepcopy(devices)
        if not self.configured:
            return result

        async with self._client() as client:
            for logical_id, actual_id in DISPLAY_ENTITY_MAP.items():
                try:
                    response = await client.get(f"/api/states/{actual_id}")
                    response.raise_for_status()
                    state = response.json()
                except httpx.HTTPError:
                    continue

                attributes = state.get("attributes", {})
                device = result.get(logical_id, {})
                if logical_id == "cover.living_room_curtain":
                    device.update({"state": state.get("state", "unknown"), "position": attributes.get("current_position")})
                else:
                    device.update({"value": _number_or_text(state.get("state"))})
                device.update({"source": "home_assistant", "home_assistant_entity_id": actual_id})
                result[logical_id] = device
        return result

    async def get_home_context(self) -> Dict[str, Any]:
        if not self.configured:
            return unavailable_home_context("Home Assistant is not configured")

        try:
            async with self._client() as client:
                response = await client.get("/api/states")
                response.raise_for_status()
                context = build_home_context(response.json())
                if self.ac_scene_configured:
                    context["living_room"]["air_conditioner"] = {
                        "control": "aqara_m3_ir_scene",
                        "state": "unknown",
                        "preset_on": "Cool 24 C",
                        "feedback": "command_only_not_sensor_verified",
                    }
                return context
        except (httpx.HTTPError, ValueError) as exc:
            return unavailable_home_context(str(exc))

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._url,
            timeout=self._timeout,
            headers={"Authorization": f"Bearer {self._token}"},
            transport=self._transport,
        )


def _number_or_text(value: Any) -> Any:
    try:
        return float(value)
    except (TypeError, ValueError):
        return value
