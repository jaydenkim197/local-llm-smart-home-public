import copy
import unittest

from docs.experiments.kics_2026.run_physical_e2e import (
    commands_exact,
    curtain_snapshot,
    load_physical_dataset,
    physical_row_passed,
    selected_cases,
    validate_physical_dataset,
)


class PhysicalEndToEndFrameworkTests(unittest.TestCase):
    def test_frozen_dataset_is_valid(self):
        dataset = load_physical_dataset()

        self.assertTrue(dataset["frozen"])
        self.assertEqual(len(dataset["cases"]), 4)

    def test_default_selection_excludes_ir_cases(self):
        dataset = load_physical_dataset()

        cases = selected_cases(dataset, None, include_ac=False)

        self.assertEqual([case["id"] for case in cases], ["P01", "P02"])

    def test_explicit_ac_selection_requires_include_flag(self):
        dataset = load_physical_dataset()

        excluded = selected_cases(dataset, ["P03"], include_ac=False)
        included = selected_cases(dataset, ["P03"], include_ac=True)

        self.assertEqual(excluded, [])
        self.assertEqual([case["id"] for case in included], ["P03"])

    def test_command_comparison_is_order_insensitive_and_value_aware(self):
        expected = [
            {"entity_id": "cover.living_room_curtain", "action": "close_cover"},
            {"entity_id": "climate.air_conditioner", "action": "turn_on"},
        ]

        self.assertTrue(commands_exact(list(reversed(expected)), expected))
        changed = copy.deepcopy(expected)
        changed[1]["value"] = 20
        self.assertFalse(commands_exact(changed, expected))

    def test_curtain_snapshot_uses_logical_device(self):
        payload = {
            "devices": {
                "cover.living_room_curtain": {"state": "open", "position": 100}
            }
        }

        self.assertEqual(
            curtain_snapshot(payload), {"state": "open", "position": 100}
        )

    def test_validator_rejects_unfrozen_dataset(self):
        dataset = load_physical_dataset()
        dataset["frozen"] = False

        with self.assertRaisesRegex(ValueError, "frozen"):
            validate_physical_dataset(dataset)

    def test_physical_failure_stops_on_unverified_curtain(self):
        row = {
            "metric_eligible": True,
            "command_accepted": True,
            "verification_type": "ha_cover_state",
            "state_verified": False,
        }

        self.assertFalse(physical_row_passed(row, observe_ac=False))

    def test_ac_requires_observation_only_when_requested(self):
        row = {
            "metric_eligible": True,
            "command_accepted": True,
            "verification_type": "operator_ir_observation",
            "operator_observation": "not_observed",
        }

        self.assertTrue(physical_row_passed(row, observe_ac=False))
        self.assertFalse(physical_row_passed(row, observe_ac=True))


if __name__ == "__main__":
    unittest.main()
