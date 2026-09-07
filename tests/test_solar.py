import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from services.solar import _angular_difference, build_solar_context
from services.parser import _normalize_parsed_command


class SolarContextTests(unittest.TestCase):
    @patch("services.solar.HOME_LONGITUDE", 125.0)
    @patch("services.solar.HOME_LATITUDE", 35.0)
    @patch("services.solar.HOME_WINDOW_AZIMUTH_DEG", None)
    def test_solar_context_contains_local_sunrise_and_sunset(self):
        now = datetime(2026, 9, 6, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))

        context = build_solar_context(now)

        self.assertEqual(context["source"], "local_astral")
        self.assertTrue(context["is_daylight"])
        self.assertTrue(context["sunrise"].startswith("2026-09-06T"))
        self.assertTrue(context["sunset"].startswith("2026-09-06T"))
        self.assertEqual(context["next_event"], "sunset")
        self.assertIsNone(context["direct_sun_possible"])

    def test_angular_difference_wraps_at_north(self):
        self.assertEqual(_angular_difference(350, 10), 20)

    @patch("services.solar.HOME_LONGITUDE", 125.0)
    @patch("services.solar.HOME_LATITUDE", 35.0)
    @patch("services.solar.HOME_WINDOW_AZIMUTH_DEG", 180.0)
    def test_window_alignment_uses_local_azimuth(self):
        now = datetime(2026, 9, 6, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))

        context = build_solar_context(now)

        self.assertEqual(context["living_room_window_azimuth_deg"], 180.0)
        self.assertIsNotNone(context["sun_to_window_angle_deg"])
        self.assertIsInstance(context["direct_sun_possible"], bool)

    @patch("services.solar.HOME_LONGITUDE", 125.0)
    @patch("services.solar.HOME_LATITUDE", 35.0)
    def test_sunset_question_uses_calculated_context_value(self):
        now = datetime(2026, 9, 6, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))
        context = {"solar": build_solar_context(now)}
        incorrect_model_output = {
            "intent": None,
            "commands": [],
            "response": "Sunset is at 06:01.",
        }

        result = _normalize_parsed_command(
            "What time is sunset today?", incorrect_model_output, context
        )

        self.assertEqual(result["intent"], "solar_information")
        expected_sunset = context["solar"]["sunset"][11:16]
        self.assertIn(expected_sunset, result["response"])
