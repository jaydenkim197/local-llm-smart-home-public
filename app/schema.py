COMMAND_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {"type": ["string", "null"]},
        "response": {"type": ["string", "null"]},
        "commands": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["entity_id", "action"],
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "enum": [
                            "light.living_room_main",
                            "light.living_room_bulb_1",
                            "light.living_room_bulb_2",
                            "cover.living_room_curtain",
                            "light.bedroom_1",
                            "light.bedroom_2",
                            "light.bedroom_3",
                            "light.bedroom_4",
                            "fan.air_purifier",
                            "vacuum.robot_cleaner",
                            "media_player.smart_tv",
                            "climate.air_conditioner",
                        ],
                    },
                    "action": {
                        "type": "string",
                        "enum": [
                            "turn_on",
                            "turn_off",
                            "set_brightness",
                            "set_temperature",
                            "set_mode",
                            "set_speed",
                            "start_cleaning",
                            "stop_cleaning",
                            "return_to_dock",
                            "open_cover",
                            "close_cover",
                            "stop_cover",
                        ],
                    },
                    "value": {},
                },
            },
        },
    },
    "required": ["commands"],
}
