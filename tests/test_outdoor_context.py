import unittest
from unittest.mock import patch

import httpx

from services.outdoor_context import OutdoorContextProvider


class OutdoorContextTests(unittest.IsolatedAsyncioTestCase):
    @patch("services.outdoor_context.HOME_LONGITUDE", 125.0)
    @patch("services.outdoor_context.HOME_LATITUDE", 35.0)
    async def test_normalizes_and_caches_open_meteo_current_weather(self):
        requests = []

        async def handler(request):
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "current": {
                        "time": "2026-09-06T12:00",
                        "temperature_2m": 30.1,
                        "apparent_temperature": 33.2,
                        "precipitation_probability": 20,
                        "cloud_cover": 15,
                        "wind_speed_10m": 2.8,
                        "shortwave_radiation": 720,
                        "direct_radiation": 610,
                        "weather_code": 1,
                    }
                },
            )

        provider = OutdoorContextProvider(httpx.MockTransport(handler), cache_seconds=600)
        first = await provider.get_context()
        second = await provider.get_context()

        self.assertEqual(first["source"], "open_meteo")
        self.assertEqual(first["direct_radiation_wm2"], 610)
        self.assertEqual(first["wind_speed_mps"], 2.8)
        self.assertEqual(second, first)
        self.assertEqual(len(requests), 1)
