import unittest

import httpx

from services.home_assistant import HomeAssistantAdapter
from services.home_context import build_home_context
from services.parser import _apply_context_policy, _normalize_parsed_command, _restrict_to_supported_entities


def sample_states(curtain_state="closed", position=0, illuminance="35"):
    return [
        {"entity_id": "sensor.aqara_temp_humidity_sensor_t1_temperature", "state": "29.5", "attributes": {}},
        {"entity_id": "sensor.aqara_temp_humidity_sensor_t1_humidity", "state": "48", "attributes": {}},
        {"entity_id": "sensor.aqara_light_detection_sensor_t1_illuminance", "state": illuminance, "attributes": {}},
        {
            "entity_id": "cover.aqara_curtain_controller",
            "state": curtain_state,
            "attributes": {"current_position": position},
        },
    ]


class HomeAssistantAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_close_cover_calls_mapped_home_assistant_service(self):
        requests = []

        async def handler(request):
            requests.append(request)
            if request.method == "GET":
                return httpx.Response(
                    200,
                    json={"state": "closed", "attributes": {"current_position": 0}},
                )
            return httpx.Response(200, json=[])

        adapter = HomeAssistantAdapter(
            "http://ha.local",
            "token",
            5,
            transport=httpx.MockTransport(handler),
        )

        result = await adapter.apply(
            [{"entity_id": "cover.living_room_curtain", "action": "close_cover"}]
        )

        self.assertTrue(result["success"])
        self.assertEqual(requests[0].url.path, "/api/services/cover/close_cover")
        self.assertEqual(
            requests[0].content,
            b'{"entity_id":"cover.aqara_curtain_controller"}',
        )
        self.assertTrue(result["applied"][0]["settled"])

    async def test_overlay_uses_live_cover_state(self):
        async def handler(request):
            return httpx.Response(
                200,
                json={
                    "state": "closed",
                    "attributes": {"current_position": 0},
                },
            )

        adapter = HomeAssistantAdapter(
            "http://ha.local",
            "token",
            5,
            transport=httpx.MockTransport(handler),
        )
        devices = {
            "cover.living_room_curtain": {"name": "Living Room Curtain", "state": "open"}
        }

        result = await adapter.overlay_states(devices)

        self.assertEqual(result["cover.living_room_curtain"]["state"], "closed")
        self.assertEqual(result["cover.living_room_curtain"]["position"], 0)
        self.assertEqual(result["cover.living_room_curtain"]["source"], "home_assistant")

    async def test_get_home_context_uses_one_state_snapshot(self):
        requests = []

        async def handler(request):
            requests.append(request)
            return httpx.Response(200, json=sample_states())

        adapter = HomeAssistantAdapter(
            "http://ha.local",
            "token",
            5,
            transport=httpx.MockTransport(handler),
        )

        context = await adapter.get_home_context()

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].url.path, "/api/states")
        self.assertEqual(context["living_room"]["temperature_c"], 29.5)
        self.assertTrue(context["derived"]["is_dark"])
        self.assertNotIn("motion", context["living_room"])

    async def test_ac_scene_turn_on_uses_cool_preset_without_claiming_ac_state(self):
        requests = []

        async def handler(request):
            requests.append(request)
            if request.method == "GET":
                return httpx.Response(200, json={"state": "off", "attributes": {}})
            return httpx.Response(200, json=[])

        adapter = HomeAssistantAdapter(
            "http://ha.local",
            "token",
            5,
            ac_cool_scene_entity="switch.ac_cool_24",
            ac_off_scene_entity="switch.ac_off",
            ac_scene_reset_delay=0,
            transport=httpx.MockTransport(handler),
        )

        result = await adapter.apply(
            [{"entity_id": "climate.air_conditioner", "action": "turn_on"}]
        )

        self.assertTrue(result["success"])
        self.assertIn("climate.air_conditioner", adapter.supported_entities)
        self.assertEqual(requests[0].url.path, "/api/states/switch.ac_cool_24")
        self.assertEqual(requests[1].url.path, "/api/states/switch.ac_off")
        self.assertEqual(requests[2].url.path, "/api/services/switch/turn_off")
        self.assertEqual(requests[2].content, b'{"entity_id":"switch.ac_off"}')
        self.assertEqual(requests[3].url.path, "/api/services/switch/turn_on")
        self.assertEqual(requests[3].content, b'{"entity_id":"switch.ac_off"}')
        self.assertEqual(requests[4].url.path, "/api/services/switch/turn_off")
        self.assertEqual(requests[4].content, b'{"entity_id":"switch.ac_cool_24"}')
        self.assertEqual(requests[5].url.path, "/api/services/switch/turn_on")
        self.assertEqual(requests[5].content, b'{"entity_id":"switch.ac_cool_24"}')
        self.assertEqual(
            result["applied"][0]["service"],
            "AC Off scene -> AC Cool 24 scene",
        )
        self.assertFalse(result["applied"][0]["state_verified"])
        self.assertEqual(
            result["applied"][0]["verification"],
            "ir_scene_command_accepted_not_physical_ac_state",
        )

    async def test_ac_scene_turn_off_triggers_only_off_preset(self):
        requests = []

        async def handler(request):
            requests.append(request)
            if request.method == "GET":
                return httpx.Response(200, json={"state": "off", "attributes": {}})
            return httpx.Response(200, json=[])

        adapter = HomeAssistantAdapter(
            "http://ha.local",
            "token",
            5,
            ac_cool_scene_entity="switch.ac_cool_24",
            ac_off_scene_entity="switch.ac_off",
            ac_scene_reset_delay=0,
            transport=httpx.MockTransport(handler),
        )

        result = await adapter.apply(
            [{"entity_id": "climate.air_conditioner", "action": "turn_off"}]
        )

        self.assertTrue(result["success"])
        self.assertEqual(requests[0].url.path, "/api/states/switch.ac_off")
        self.assertEqual(requests[1].content, b'{"entity_id":"switch.ac_off"}')
        self.assertEqual(requests[2].content, b'{"entity_id":"switch.ac_off"}')
        self.assertEqual(result["applied"][0]["preset"], "Off")


class HardwareCommandRestrictionTests(unittest.TestCase):
    def test_explicit_close_curtain_overrides_incorrect_model_action(self):
        incorrect_model_output = {
            "intent": None,
            "commands": [{"entity_id": "cover.living_room_curtain", "action": "open_cover"}],
            "response": "The curtain is closed.",
        }

        result = _normalize_parsed_command("Close the living room curtain.", incorrect_model_output)

        self.assertEqual(result["commands"][0]["action"], "close_cover")

    def test_dark_room_with_closed_curtain_opens_curtain(self):
        context = build_home_context(sample_states())

        result = _normalize_parsed_command(
            "It's dark in here.",
            {"intent": None, "commands": [], "response": None},
            context,
        )

        self.assertEqual(result["intent"], "increase_natural_light")
        self.assertEqual(result["commands"][0]["action"], "open_cover")

    def test_redundant_close_is_removed_by_context_policy(self):
        context = build_home_context(sample_states())
        parsed = {
            "intent": "curtain_control",
            "commands": [{"entity_id": "cover.living_room_curtain", "action": "close_cover"}],
            "response": "Closing.",
        }

        result = _apply_context_policy(parsed, context)

        self.assertEqual(result["commands"], [])
        self.assertIn("already", result["response"])

    def test_bright_request_prefers_closed_curtain_no_op_over_threshold(self):
        context = build_home_context(sample_states(illuminance="777"))

        result = _normalize_parsed_command(
            "It's too bright here.",
            {"intent": None, "commands": [], "response": None},
            context,
        )

        self.assertEqual(result["commands"], [])
        self.assertEqual(result["response"], "The curtain is already closed.")

    def test_hot_room_uses_curtain_and_ac_scene_when_physically_configured(self):
        context = build_home_context(sample_states(curtain_state="open", position=100))

        result = _normalize_parsed_command(
            "It's too hot in the living room. Make it comfortable.",
            {"intent": None, "commands": [], "response": None},
            context,
            {"cover.living_room_curtain", "climate.air_conditioner"},
        )

        self.assertEqual(result["intent"], "reduce_heat")
        self.assertEqual(
            result["commands"],
            [
                {"entity_id": "cover.living_room_curtain", "action": "close_cover"},
                {"entity_id": "climate.air_conditioner", "action": "turn_on"},
            ],
        )

    def test_hot_request_is_suppressed_when_sensor_is_not_hot(self):
        states = sample_states()
        states[0]["state"] = "24"
        context = build_home_context(states)

        result = _normalize_parsed_command(
            "It's too hot in the living room.",
            {"intent": None, "commands": [], "response": None},
            context,
            {"cover.living_room_curtain", "climate.air_conditioner"},
        )

        self.assertEqual(result["commands"], [])
        self.assertIn("does not indicate", result["response"])

    def test_cooling_transcription_variants_use_hot_context(self):
        context = build_home_context(sample_states())
        variants = [
            "It's too hot in the living room.",
            "It's hot in here.",
            "The living room is really hot.",
            "Make it cooler in here.",
            "Make the room comfortable.",
            "IT'S HOT IN HERE",
            "It is hot in here, make it comfortable.",
            "It's hot here.",
        ]

        for transcript in variants:
            with self.subTest(transcript=transcript):
                result = _normalize_parsed_command(
                    transcript,
                    {"intent": None, "commands": [], "response": None},
                    context,
                    {"cover.living_room_curtain", "climate.air_conditioner"},
                )
                self.assertEqual(result["intent"], "reduce_heat")
                self.assertIn(
                    {"entity_id": "climate.air_conditioner", "action": "turn_on"},
                    result["commands"],
                )

    def test_explicit_ac_off_reports_command_sent_not_physical_state(self):
        result = _normalize_parsed_command(
            "Turn off the air conditioner.",
            {"intent": None, "commands": [], "response": "The AC is off."},
            build_home_context(sample_states()),
            {"cover.living_room_curtain", "climate.air_conditioner"},
        )

        self.assertEqual(result["commands"][0]["action"], "turn_off")
        self.assertEqual(result["response"], "I sent the Off IR preset.")

    def test_empty_no_action_survives_physical_restriction(self):
        parsed = {"intent": "context_no_action", "commands": [], "response": "No action needed."}

        result = _restrict_to_supported_entities(parsed, {"cover.living_room_curtain"})

        self.assertEqual(result, parsed)

    def test_restriction_drops_unmapped_commands(self):
        parsed = {
            "intent": "movie_mode",
            "commands": [
                {"entity_id": "cover.living_room_curtain", "action": "close_cover"},
                {"entity_id": "media_player.smart_tv", "action": "turn_on"},
            ],
            "response": "Movie mode is ready.",
        }

        result = _restrict_to_supported_entities(parsed, {"cover.living_room_curtain"})

        self.assertEqual(result["commands"], [parsed["commands"][0]])
