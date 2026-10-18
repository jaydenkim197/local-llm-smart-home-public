from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "docs" / "experiments" / "kics_2026" / "run_live_context_e2e.py"
SPEC = importlib.util.spec_from_file_location("run_live_context_e2e", MODULE_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class LiveContextE2ETest(unittest.TestCase):
    def test_frozen_dataset_is_valid(self) -> None:
        dataset = RUNNER.load_dataset()
        self.assertEqual(dataset["dataset_id"], "kics_2026_live_context_v1")
        self.assertEqual([case["id"] for case in dataset["cases"]], ["L01", "L02", "L03", "L04", "L05", "L06"])

    def test_calibrated_dataset_is_valid_and_separate(self) -> None:
        calibrated = RUNNER.load_dataset(
            ROOT / "docs" / "experiments" / "kics_2026" / "live_context_calibrated_v2_cases.json"
        )
        self.assertEqual(calibrated["policy_profile"]["dark_lux_threshold"], 300.0)
        self.assertEqual([case["id"] for case in calibrated["cases"]], ["LC01", "LC02"])

    def test_bright_precondition_requires_live_lux_and_curtain_state(self) -> None:
        case = RUNNER.load_dataset()["cases"][0]
        matched, failures = RUNNER.precondition_met(
            case, {"illuminance_lux": 1168.0, "curtain": {"state": "open"}}
        )
        self.assertTrue(matched)
        self.assertEqual(failures, [])
        matched, failures = RUNNER.precondition_met(
            case, {"illuminance_lux": 799.0, "curtain": {"state": "closed"}}
        )
        self.assertFalse(matched)
        self.assertEqual(failures, ["illuminance_below_minimum", "curtain_state_mismatch"])

    def test_no_action_requires_no_commands_or_apply_results(self) -> None:
        row = {
            "metric_eligible": True,
            "command_exact": True,
            "actual_intent": "unsupported",
            "expected_intent": "unsupported",
            "verification": {"type": "no_actuation"},
            "state_verified": True,
            "no_actuation_verified": True,
        }
        self.assertTrue(RUNNER.row_passed(row))
        row["no_actuation_verified"] = False
        self.assertFalse(RUNNER.row_passed(row))

    def test_context_wrapper_is_unwrapped_for_live_values(self) -> None:
        class Response:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict:
                return {
                    "home_context": {
                        "living_room": {
                            "illuminance_lux": 1168.0,
                            "curtain": {"state": "closed", "position": 0},
                        },
                        "derived": {"is_bright": True},
                    }
                }

        class Client:
            def get(self, path: str) -> Response:
                self.path = path
                return Response()

        snapshot = RUNNER.live_snapshot(Client())
        self.assertEqual(snapshot["illuminance_lux"], 1168.0)
        self.assertEqual(snapshot["curtain"]["state"], "closed")
        self.assertTrue(snapshot["derived"]["is_bright"])
