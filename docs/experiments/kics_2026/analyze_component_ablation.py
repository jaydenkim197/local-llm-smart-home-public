#!/usr/bin/env python3
"""Replay frozen LLM outputs through selectable production post-processing stages."""

from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from docs.experiments.kics_2026.eval_core import (
    DATASET_PATH,
    HELDOUT_DATASET_PATH,
    context_for,
    dataset_sha256,
    git_commit,
    load_dataset,
    schema_is_valid,
    score_commands,
)
from services.parser import (
    _apply_context_policy,
    _normalize_parsed_command,
    _restrict_to_supported_entities,
    _validate_or_raise,
)


EXPERIMENT_DIR = Path(__file__).resolve().parent
INPUTS = (
    (DATASET_PATH, EXPERIMENT_DIR / "results/raw_runs.jsonl", 40),
    (
        HELDOUT_DATASET_PATH,
        EXPERIMENT_DIR / "results/heldout_v1/paired/raw_runs.jsonl",
        20,
    ),
)
STAGES = ("normalization", "context_policy", "physical_allowlist", "schema_validation")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(
    raw: dict[str, Any],
    utterance: str,
    context: dict[str, Any],
    allowed: set[str],
    disabled: frozenset[str] = frozenset(),
) -> tuple[dict[str, Any] | None, str | None]:
    if not disabled.issubset(STAGES):
        raise ValueError(f"Unknown disabled stages: {sorted(disabled - set(STAGES))}")
    parsed = deepcopy(raw)
    try:
        if "normalization" not in disabled:
            parsed = _normalize_parsed_command(utterance, parsed, context, allowed)
        if "context_policy" not in disabled:
            parsed = _apply_context_policy(parsed, context)
        if "physical_allowlist" not in disabled:
            parsed = _restrict_to_supported_entities(parsed, allowed)
        if "schema_validation" not in disabled:
            _validate_or_raise(parsed)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return parsed, None


def load_preserved_rows(
    dataset_path: Path, raw_path: Path, expected_count: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dataset = load_dataset(dataset_path, expected_case_count=expected_count)
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    cases = {case["id"]: case for case in dataset["cases"]}
    if len(rows) != expected_count or {row["case_id"] for row in rows} != set(cases):
        raise ValueError(f"{raw_path}: expected one row per frozen case")
    for row in rows:
        case = cases[row["case_id"]]
        if (
            row["dataset_sha256"] != dataset_sha256(dataset_path)
            or row["expected"] != case["expected"]
            or row["utterance"] != case["utterance"]
            or row["context_id"] != case["context_id"]
            or not row["metric_eligible"]
            or row["fallback_used"]
            or not isinstance(row["raw"], dict)
        ):
            raise ValueError(f"{raw_path}: ineligible or mismatched row {row['case_id']}")
    return dataset, rows


def analyze_dataset(
    dataset_path: Path, raw_path: Path, expected_count: int
) -> dict[str, Any]:
    dataset, rows = load_preserved_rows(dataset_path, raw_path, expected_count)
    cases = {case["id"]: case for case in dataset["cases"]}
    allowed = set(dataset["supported_entities"])
    variants: dict[str, list[dict[str, Any]]] = {"raw": []}
    variants.update({f"through_{stage}": [] for stage in STAGES})
    variants.update({f"without_{stage}": [] for stage in STAGES})

    for row in rows:
        case = cases[row["case_id"]]
        context = context_for(dataset, case)
        predicted = row["raw"]
        for name, candidate, error in [("raw", predicted, None)]:
            variants[name].append(_result(row, candidate, error, allowed))

        for index, stage in enumerate(STAGES):
            disabled = frozenset(STAGES[index + 1 :])
            candidate, error = replay(predicted, row["utterance"], context, allowed, disabled)
            variants[f"through_{stage}"].append(_result(row, candidate, error, allowed))

        full, error = replay(predicted, row["utterance"], context, allowed)
        if error or full != row["final"]:
            raise ValueError(f"Full-pipeline replay differs from preserved {row['case_id']}: {error}")
        if score_commands(full, case["expected"], allowed) != row["final_score"]:
            raise ValueError(f"Preserved score differs for {row['case_id']}")

        for stage in STAGES:
            candidate, error = replay(
                predicted, row["utterance"], context, allowed, frozenset({stage})
            )
            variants[f"without_{stage}"].append(_result(row, candidate, error, allowed))

    full_rows = variants["through_schema_validation"]
    sequence = ["raw", *(f"through_{stage}" for stage in STAGES)]
    transitions = {}
    for before, after in zip(sequence, sequence[1:]):
        prior = {row["case_id"]: row for row in variants[before]}
        current = {row["case_id"]: row for row in variants[after]}
        transitions[after] = {
            "fixed_cases": [
                case_id for case_id in prior
                if not prior[case_id]["operational_match"] and current[case_id]["operational_match"]
            ],
            "broken_cases": [
                case_id for case_id in prior
                if prior[case_id]["operational_match"] and not current[case_id]["operational_match"]
            ],
        }
    return {
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": dataset_sha256(dataset_path),
        "raw_file_sha256": sha256(raw_path),
        "original_run_commit": sorted({row["git_commit"] for row in rows}),
        "model_digest": sorted({row["model_digest"] for row in rows}),
        "count": len(rows),
        "variants": {
            name: _summarize(results, full_rows) for name, results in variants.items()
        },
        "sequential_transitions": transitions,
    }


def _result(
    row: dict[str, Any], candidate: dict[str, Any] | None, error: str | None, allowed: set[str]
) -> dict[str, Any]:
    score = score_commands(candidate, row["expected"], allowed)
    valid = schema_is_valid(candidate)
    return {
        "case_id": row["case_id"],
        "expected_noop": score["expected_noop"],
        "exact_match": score["exact_match"] if error is None else False,
        "schema_valid": valid,
        "operational_match": score["exact_match"] and valid and error is None,
        "extra_command_count": score["extra_command_count"],
        "missing_command_count": score["missing_command_count"],
        "unsupported_entity_count": score["unsupported_entity_count"],
        "unsupported_action_count": score["unsupported_action_count"],
        "error": error,
    }


def _summarize(rows: list[dict[str, Any]], full: list[dict[str, Any]]) -> dict[str, Any]:
    full_by_id = {row["case_id"]: row for row in full}
    return {
        "exact_match": sum(row["exact_match"] for row in rows),
        "action_required_match": sum(
            row["exact_match"] for row in rows if not row["expected_noop"]
        ),
        "no_op_match": sum(row["exact_match"] for row in rows if row["expected_noop"]),
        "schema_valid": sum(row["schema_valid"] for row in rows),
        "operational_match": sum(row["operational_match"] for row in rows),
        "extra_commands": sum(row["extra_command_count"] for row in rows),
        "missing_commands": sum(row["missing_command_count"] for row in rows),
        "unsupported_entities": sum(row["unsupported_entity_count"] for row in rows),
        "unsupported_actions": sum(row["unsupported_action_count"] for row in rows),
        "error_count": sum(row["error"] is not None for row in rows),
        "better_than_full": [
            row["case_id"]
            for row in rows
            if row["operational_match"] and not full_by_id[row["case_id"]]["operational_match"]
        ],
        "worse_than_full": [
            row["case_id"]
            for row in rows
            if not row["operational_match"] and full_by_id[row["case_id"]]["operational_match"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=EXPERIMENT_DIR / "results/component_ablation_v1.json",
    )
    args = parser.parse_args()
    result = {
        "analysis": "posthoc_fixed_llm_output_replay",
        "analysis_commit": git_commit(),
        "parser_sha256": sha256(EXPERIMENT_DIR.parents[2] / "services/parser.py"),
        "datasets": [analyze_dataset(*inputs) for inputs in INPUTS],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Saved verified replay to {args.output}")


if __name__ == "__main__":
    main()
