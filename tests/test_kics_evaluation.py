import unittest
from copy import deepcopy
from pathlib import Path

from docs.experiments.kics_2026.eval_core import (
    CONDITIONS,
    HELDOUT_DATASET_PATH,
    base_metadata,
    context_for,
    dataset_sha256,
    load_dataset,
    run_condition,
    score_commands,
    supported_entities,
    validate_dataset,
)
from docs.experiments.kics_2026.run_latency import DEFAULT_CASES
from docs.experiments.kics_2026.run_resource_profile import (
    _latency_command,
    descendant_pids,
    parse_process_rows,
    summarize_samples,
)
from docs.experiments.kics_2026.summarize_results import _is_eligible, _slices
from docs.experiments.kics_2026.summarize_stability import (
    case_success_counts,
    classify_success_count,
)
from docs.experiments.kics_2026.stt_eval_core import (
    expanded_cases,
    load_stt_dataset,
    normalize_transcript,
    word_error_stats,
)


class KicsDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset()

    def test_dataset_has_40_unique_cases(self):
        case_ids = [case["id"] for case in self.dataset["cases"]]
        self.assertEqual(len(case_ids), 40)
        self.assertEqual(len(set(case_ids)), 40)

    def test_dataset_is_frozen_before_model_results(self):
        self.assertEqual(self.dataset["status"], "frozen_before_results")
        self.assertTrue(self.dataset["frozen"])
        self.assertEqual(self.dataset["frozen_on"], "2026-09-17")

    def test_all_gold_commands_are_physically_supported(self):
        allowed = supported_entities(self.dataset)
        for case in self.dataset["cases"]:
            for command in case["expected"]["commands"]:
                self.assertIn(command["entity_id"], allowed, case["id"])

    def test_validator_rejects_physically_unsupported_gold_action(self):
        changed = deepcopy(self.dataset)
        changed["cases"][6]["expected"]["commands"][0]["action"] = "set_temperature"
        with self.assertRaisesRegex(ValueError, "not physically supported"):
            validate_dataset(changed)

    def test_validator_rejects_case_count_change(self):
        changed = deepcopy(self.dataset)
        changed["cases"] = changed["cases"][:-1]
        with self.assertRaisesRegex(ValueError, "exactly 40"):
            validate_dataset(changed)

    def test_validator_rejects_derived_context_mismatch(self):
        changed = deepcopy(self.dataset)
        changed["contexts"]["temp_28_open"]["derived"]["is_hot"] = True
        with self.assertRaisesRegex(ValueError, "production thresholds"):
            validate_dataset(changed)

    def test_dataset_hash_and_repetition_metadata_are_recorded(self):
        self.assertEqual(len(dataset_sha256()), 64)
        metadata = base_metadata(
            "rules_only",
            repetition=2,
            model={"model": "none", "digest": None},
            repetition_count=5,
        )
        self.assertEqual(metadata["repetition_index"], 2)
        self.assertEqual(metadata["repetition_count"], 5)
        self.assertFalse(metadata["model_used"])

    def test_four_ablation_conditions_are_fixed(self):
        self.assertEqual(
            CONDITIONS,
            ("llm_only", "llm_context", "full_pipeline", "rules_only"),
        )

    def test_prospective_heldout_dataset_is_frozen_and_disjoint(self):
        heldout = load_dataset(HELDOUT_DATASET_PATH, expected_case_count=20)
        self.assertEqual(heldout["status"], "frozen_before_results")
        self.assertTrue(heldout["frozen"])
        self.assertEqual(heldout["frozen_on"], "2026-09-20")
        self.assertTrue(heldout["authored_after_initial_results"])
        original_utterances = {case["utterance"] for case in self.dataset["cases"]}
        heldout_utterances = {case["utterance"] for case in heldout["cases"]}
        self.assertEqual(len(heldout["cases"]), 20)
        self.assertEqual(len(heldout_utterances), 18)
        self.assertTrue(original_utterances.isdisjoint(heldout_utterances))


class KicsSttDatasetTests(unittest.TestCase):
    def test_stt_set_is_frozen_and_uses_twelve_unique_source_cases(self):
        dataset = load_stt_dataset()
        cases = expanded_cases(dataset)
        self.assertEqual(dataset["status"], "frozen_before_recording")
        self.assertTrue(dataset["frozen"])
        self.assertEqual(dataset["takes_per_case"], 3)
        self.assertEqual(len(cases), 12)
        self.assertEqual(len({case["source_case_id"] for case in cases}), 12)

    def test_transcript_normalization_ignores_case_and_punctuation(self):
        reference = "It's hot in here."
        hypothesis = "IT'S HOT IN HERE!"
        self.assertEqual(normalize_transcript(reference), normalize_transcript(hypothesis))
        self.assertTrue(word_error_stats(reference, hypothesis)["transcript_exact"])

    def test_word_error_stats_use_word_level_edit_distance(self):
        score = word_error_stats("close the living room curtain", "close living curtain")
        self.assertEqual(score["reference_words"], 5)
        self.assertEqual(score["word_errors"], 2)
        self.assertAlmostEqual(score["wer"], 0.4)


class KicsResourceProfileTests(unittest.TestCase):
    def test_single_call_prewarm_targets_one_explicit_case(self):
        command = _latency_command(
            output_dir=Path("/tmp/resource-prewarm"),
            warmup=0,
            repetitions=1,
            case_id="C02",
        )
        self.assertEqual(command[-2:], ["--case", "C02"])

    def test_process_parser_and_descendant_selection(self):
        rows = parse_process_rows(
            "100 1 1024 5.0 python runner.py\n"
            "101 100 2048 20.0 child worker\n"
            "102 101 512 10.0 grandchild\n"
            "200 1 4096 1.0 unrelated\n"
        )
        self.assertEqual(descendant_pids(rows, 100), {100, 101, 102})
        self.assertEqual(rows[1]["rss_kb"], 2048)

    def test_resource_summary_separates_loaded_idle_and_workload(self):
        samples = [
            {
                "phase": "loaded_idle_baseline",
                "ollama_rss_mb": 2000.0,
                "workload_rss_mb": 0.0,
                "monitored_rss_mb": 2000.0,
                "monitored_cpu_percent": 1.0,
                "system_occupied_proxy_mb": 5000.0,
                "memory_pressure_free_percent": 70.0,
            },
            {
                "phase": "workload",
                "ollama_rss_mb": 2200.0,
                "workload_rss_mb": 100.0,
                "monitored_rss_mb": 2300.0,
                "monitored_cpu_percent": 250.0,
                "system_occupied_proxy_mb": 5400.0,
                "memory_pressure_free_percent": 60.0,
            },
            {
                "phase": "workload",
                "ollama_rss_mb": 2400.0,
                "workload_rss_mb": 120.0,
                "monitored_rss_mb": 2520.0,
                "monitored_cpu_percent": 300.0,
                "system_occupied_proxy_mb": 5600.0,
                "memory_pressure_free_percent": 55.0,
            },
        ]
        summary = summarize_samples(samples)
        self.assertEqual(summary["workload_monitored_rss_peak_mb"], 2520.0)
        self.assertEqual(summary["workload_monitored_cpu_mean_percent"], 275.0)
        self.assertEqual(summary["workload_system_occupied_proxy_peak_delta_mb"], 600.0)
        self.assertEqual(summary["workload_memory_pressure_free_min_percent"], 55.0)
        self.assertEqual(
            summary["workload_memory_pressure_free_drop_percentage_points"], 15.0
        )


class KicsScoringTests(unittest.TestCase):
    def setUp(self):
        self.allowed = {
            "cover.living_room_curtain",
            "climate.air_conditioner",
        }

    def test_exact_match_is_order_insensitive_but_order_is_recorded(self):
        expected = {
            "commands": [
                {"entity_id": "cover.living_room_curtain", "action": "close_cover"},
                {"entity_id": "climate.air_conditioner", "action": "turn_on"},
            ]
        }
        predicted = {"commands": list(reversed(expected["commands"]))}
        score = score_commands(predicted, expected, self.allowed)
        self.assertTrue(score["exact_match"])
        self.assertFalse(score["ordered_match"])

    def test_extra_missing_and_unsupported_are_counted(self):
        expected = {
            "commands": [
                {"entity_id": "cover.living_room_curtain", "action": "close_cover"}
            ]
        }
        predicted = {
            "commands": [
                {"entity_id": "light.kitchen", "action": "turn_on"}
            ]
        }
        score = score_commands(predicted, expected, self.allowed)
        self.assertFalse(score["exact_match"])
        self.assertEqual(score["extra_command_count"], 1)
        self.assertEqual(score["missing_command_count"], 1)
        self.assertEqual(score["unsupported_entity_count"], 1)

    def test_noop_accuracy_is_only_defined_for_gold_noop(self):
        noop = score_commands({"commands": []}, {"commands": []}, self.allowed)
        action = score_commands(
            {"commands": []},
            {
                "commands": [
                    {"entity_id": "cover.living_room_curtain", "action": "close_cover"}
                ]
            },
            self.allowed,
        )
        self.assertTrue(noop["noop_correct"])
        self.assertIsNone(action["noop_correct"])

    def test_unsupported_action_is_counted_separately_from_entity(self):
        score = score_commands(
            {
                "commands": [
                    {
                        "entity_id": "climate.air_conditioner",
                        "action": "set_temperature",
                        "value": 19,
                    }
                ]
            },
            {"commands": []},
            self.allowed,
        )
        self.assertEqual(score["unsupported_entity_count"], 0)
        self.assertEqual(score["unsupported_action_count"], 1)


class KicsReportingTests(unittest.TestCase):
    def test_summary_separates_action_noop_and_category_slices(self):
        rows = [
            {"case_id": "C01", "category": "direct", "expected_noop": "False"},
            {"case_id": "C02", "category": "safety", "expected_noop": "True"},
        ]
        slices = dict(_slices(rows))
        self.assertEqual(len(slices["overall"]), 2)
        self.assertEqual([row["case_id"] for row in slices["action_required"]], ["C01"])
        self.assertEqual([row["case_id"] for row in slices["no_op"]], ["C02"])
        self.assertIn("category:direct", slices)
        self.assertIn("category:safety", slices)

    def test_fallback_or_failed_llm_row_is_not_metric_eligible(self):
        self.assertFalse(_is_eligible({"metric_eligible": "False"}))
        self.assertTrue(_is_eligible({"metric_eligible": "True"}))

    def test_latency_default_uses_mixed_representative_cases(self):
        self.assertGreater(len(DEFAULT_CASES), 1)
        self.assertEqual(len(DEFAULT_CASES), len(set(DEFAULT_CASES)))

    def test_stability_classifies_case_success_frequency(self):
        rows = [
            {"case_id": "C01", "eligible": True, "exact_match": True},
            {"case_id": "C01", "eligible": True, "exact_match": False},
            {"case_id": "C02", "eligible": True, "exact_match": True},
        ]
        self.assertEqual(case_success_counts(rows), {"C01": 1, "C02": 1})
        self.assertEqual(classify_success_count(5), "always_success")
        self.assertEqual(classify_success_count(3), "variable")
        self.assertEqual(classify_success_count(0), "always_failure")


class KicsRulesOnlyDryRunTests(unittest.IsolatedAsyncioTestCase):
    async def test_rules_only_uses_production_stages_without_ollama(self):
        dataset = load_dataset()
        case = next(case for case in dataset["cases"] if case["id"] == "C02")
        result = await run_condition(
            "rules_only",
            case["utterance"],
            context_for(dataset, case),
            supported_entities(dataset),
        )
        score = score_commands(
            result["parsed"], case["expected"], supported_entities(dataset)
        )
        self.assertIsNone(result["error"])
        self.assertTrue(result["schema_valid"])
        self.assertTrue(score["exact_match"])


if __name__ == "__main__":
    unittest.main()
