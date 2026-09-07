from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


INITIAL_DEVICES: Dict[str, Dict[str, Any]] = {
    "light.living_room_main": {
        "name": "Living Room Main Light",
        "room": "living_room",
        "type": "dimmable_light",
        "state": "off",
        "brightness": 0,
        "ir_capable": True,
    },
    "light.living_room_bulb_1": {
        "name": "Living Room Smart Bulb 1",
        "room": "living_room",
        "type": "smart_bulb",
        "state": "off",
        "brightness": 0,
    },
    "light.living_room_bulb_2": {
        "name": "Living Room Smart Bulb 2",
        "room": "living_room",
        "type": "smart_bulb",
        "state": "off",
        "brightness": 0,
    },
    "cover.living_room_curtain": {
        "name": "Living Room Curtain",
        "room": "living_room",
        "type": "cover",
        "state": "open",
        "position": 100,
    },
    "light.bedroom_1": {"name": "Bedroom 1 Main Light", "room": "bedroom_1", "type": "light", "state": "off"},
    "light.bedroom_2": {"name": "Bedroom 2 Main Light", "room": "bedroom_2", "type": "light", "state": "off"},
    "light.bedroom_3": {"name": "Bedroom 3 Main Light", "room": "bedroom_3", "type": "light", "state": "off"},
    "light.bedroom_4": {"name": "Bedroom 4 Main Light", "room": "bedroom_4", "type": "light", "state": "off"},
    "sensor.temperature": {"name": "Temperature Sensor", "room": "living_room", "type": "sensor", "value": 27.5, "unit": "C"},
    "sensor.humidity": {"name": "Humidity Sensor", "room": "living_room", "type": "sensor", "value": 48.0, "unit": "%"},
    "sensor.illuminance": {"name": "Illuminance Sensor", "room": "living_room", "type": "sensor", "value": 180, "unit": "lux"},
    "fan.air_purifier": {
        "name": "Air Purifier",
        "room": "living_room",
        "type": "fan",
        "state": "off",
        "speed": "auto",
    },
    "vacuum.robot_cleaner": {
        "name": "Robot Cleaner",
        "room": "home",
        "type": "vacuum",
        "state": "docked",
    },
    "media_player.smart_tv": {
        "name": "Smart TV",
        "room": "living_room",
        "type": "media_player",
        "state": "off",
    },
    "climate.air_conditioner": {
        "name": "Air Conditioner",
        "room": "living_room",
        "type": "climate",
        "state": "off",
        "temperature": 26,
        "mode": "cool",
    },
}


class DeviceStore:
    def __init__(self) -> None:
        self._devices = deepcopy(INITIAL_DEVICES)

    def all(self) -> Dict[str, Any]:
        return deepcopy(self._devices)

    def reset(self) -> Dict[str, Any]:
        self._devices = deepcopy(INITIAL_DEVICES)
        return self.all()

    def controllable_entities(self) -> set[str]:
        return {
            entity_id
            for entity_id, device in self._devices.items()
            if device.get("type") != "sensor"
        }

    def apply(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        applied = []
        errors = []
        for command in commands:
            entity_id = command.get("entity_id")
            action = command.get("action")
            value = command.get("value")
            device = self._devices.get(entity_id)
            if not device:
                errors.append({"entity_id": entity_id, "error": "Unknown entity"})
                continue

            try:
                self._apply_one(device, action, value)
                applied.append({"entity_id": entity_id, "action": action, "value": value})
            except ValueError as exc:
                errors.append({"entity_id": entity_id, "action": action, "error": str(exc)})

        return {"applied": applied, "errors": errors, "success": not errors}

    def _apply_one(self, device: Dict[str, Any], action: str, value: Any) -> None:
        if action == "turn_on":
            device["state"] = "on"
            if "brightness" in device and device.get("brightness", 0) == 0:
                device["brightness"] = 80
            return
        if action == "turn_off":
            device["state"] = "off"
            if "brightness" in device:
                device["brightness"] = 0
            return
        if action == "set_brightness":
            if "brightness" not in device:
                raise ValueError("Device does not support brightness")
            brightness = int(value)
            if brightness < 0 or brightness > 100:
                raise ValueError("Brightness must be 0..100")
            device["state"] = "on" if brightness > 0 else "off"
            device["brightness"] = brightness
            return
        if action == "set_temperature":
            if "temperature" not in device:
                raise ValueError("Device does not support temperature")
            device["state"] = "on"
            device["temperature"] = int(value)
            return
        if action == "set_mode":
            if "mode" not in device:
                raise ValueError("Device does not support mode")
            device["mode"] = str(value)
            return
        if action == "set_speed":
            if "speed" not in device:
                raise ValueError("Device does not support speed")
            device["state"] = "on"
            device["speed"] = str(value)
            return
        if action == "start_cleaning":
            if device.get("type") != "vacuum":
                raise ValueError("Device is not a vacuum")
            device["state"] = "cleaning"
            return
        if action == "stop_cleaning":
            if device.get("type") != "vacuum":
                raise ValueError("Device is not a vacuum")
            device["state"] = "stopped"
            return
        if action == "return_to_dock":
            if device.get("type") != "vacuum":
                raise ValueError("Device is not a vacuum")
            device["state"] = "docked"
            return
        if action == "open_cover":
            if device.get("type") != "cover":
                raise ValueError("Device is not a cover")
            device["state"] = "open"
            device["position"] = 100
            return
        if action == "close_cover":
            if device.get("type") != "cover":
                raise ValueError("Device is not a cover")
            device["state"] = "closed"
            device["position"] = 0
            return
        if action == "stop_cover":
            if device.get("type") != "cover":
                raise ValueError("Device is not a cover")
            device["state"] = "stopped"
            return
        raise ValueError(f"Unsupported action: {action}")
