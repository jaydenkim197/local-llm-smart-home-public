import unittest

from docs.experiments.kics_2026.analyze_component_ablation import replay
from docs.experiments.kics_2026.eval_core import load_dataset, schema_is_valid


class ComponentReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset = load_dataset()
        cls.context = dataset["contexts"]["neutral_open"]
        cls.allowed = set(dataset["supported_entities"])

    def test_normalization_and_allowlist_are_independently_switchable(self):
        raw = {
            "intent": "movie_mode",
            "commands": [{"entity_id": "media_player.smart_tv", "action": "turn_on"}],
            "response": "TV on.",
        }
        full, error = replay(raw, "Close the living room curtain.", self.context, self.allowed)
        self.assertIsNone(error)
        self.assertEqual(
            full["commands"],
            [{"entity_id": "cover.living_room_curtain", "action": "close_cover"}],
        )
        without_normalization, error = replay(
            raw, "Close the living room curtain.", self.context, self.allowed,
            frozenset({"normalization"}),
        )
        self.assertIsNone(error)
        self.assertEqual(without_normalization["commands"], [])
        without_allowlist, error = replay(
            raw, "Unmapped request.", self.context, self.allowed,
            frozenset({"physical_allowlist"}),
        )
        self.assertIsNone(error)
        self.assertEqual(without_allowlist["commands"], raw["commands"])

    def test_schema_omission_keeps_invalidity_visible(self):
        raw = {"intent": None, "commands": [], "response": 3}
        full, error = replay(raw, "Unknown request.", self.context, self.allowed)
        self.assertIsNone(full)
        self.assertIsNotNone(error)
        without_schema, error = replay(
            raw, "Unknown request.", self.context, self.allowed,
            frozenset({"schema_validation"}),
        )
        self.assertIsNone(error)
        self.assertFalse(schema_is_valid(without_schema))

    def test_unknown_stage_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown disabled stages"):
            replay({}, "x", self.context, self.allowed, frozenset({"unknown"}))


if __name__ == "__main__":
    unittest.main()
