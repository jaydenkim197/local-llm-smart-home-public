import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app import main


class SimulationApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        main.store.reset()
        self.backend_patch = patch("app.main.CONTROL_BACKEND", "simulation")
        self.ollama_patch = patch(
            "services.parser._parse_with_ollama",
            new=AsyncMock(side_effect=httpx.ConnectError("Ollama unavailable in test")),
        )
        self.outdoor_patch = patch.object(
            main.outdoor_context,
            "get_context",
            new=AsyncMock(return_value={"source": "unavailable", "error": "offline test"}),
        )
        self.backend_patch.start()
        self.ollama_patch.start()
        self.outdoor_patch.start()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app),
            base_url="http://test",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.outdoor_patch.stop()
        self.ollama_patch.stop()
        self.backend_patch.stop()
        main.store.reset()

    async def test_movie_mode_applies_to_simulated_devices(self):
        response = await self.client.post(
            "/api/command/text",
            json={"text": "I am going to watch a movie from now on."},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["llm_mode"], "fallback")
        self.assertEqual(body["parsed"]["intent"], "movie_mode")
        self.assertTrue(body["result"]["success"])
        self.assertEqual(body["devices"]["media_player.smart_tv"]["state"], "on")
        self.assertEqual(body["devices"]["cover.living_room_curtain"]["state"], "closed")
        self.assertEqual(body["devices"]["vacuum.robot_cleaner"]["state"], "stopped")

    async def test_global_on_excludes_robot_cleaner(self):
        response = await self.client.post(
            "/api/command/text",
            json={"text": "Turn everything on."},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["parsed"]["intent"], "whole_home_on")
        self.assertEqual(body["devices"]["light.living_room_main"]["state"], "on")
        self.assertEqual(body["devices"]["media_player.smart_tv"]["state"], "on")
        self.assertEqual(body["devices"]["climate.air_conditioner"]["state"], "on")
        self.assertEqual(body["devices"]["vacuum.robot_cleaner"]["state"], "docked")

    async def test_contextual_cooling_is_safely_suppressed_when_simulated_room_is_not_hot(self):
        response = await self.client.post(
            "/api/command/text",
            json={"text": "It's hot in here. Make the room comfortable."},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["home_context"]["source"], "simulation")
        self.assertFalse(body["home_context"]["derived"]["is_hot"])
        self.assertEqual(body["parsed"]["intent"], "context_no_action")
        self.assertEqual(body["parsed"]["commands"], [])
        self.assertEqual(body["result"]["applied"], [])

    async def test_reset_restores_initial_state(self):
        await self.client.post(
            "/api/command/text",
            json={"text": "Turn on the living room light."},
        )

        response = await self.client.post("/api/devices/reset")

        self.assertEqual(response.status_code, 200)
        devices = response.json()["devices"]
        self.assertEqual(devices["light.living_room_main"]["state"], "off")
        self.assertEqual(devices["light.living_room_main"]["brightness"], 0)
        self.assertEqual(devices["cover.living_room_curtain"]["state"], "open")


if __name__ == "__main__":
    unittest.main()
