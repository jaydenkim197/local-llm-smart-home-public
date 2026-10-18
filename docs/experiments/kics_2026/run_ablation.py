#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any, Dict, List

from eval_core import (
    CONDITIONS,
    DATASET_PATH,
    RESULTS_DIR,
    base_metadata,
    context_for,
    dataset_sha256,
    load_dataset,
    model_metadata,
    require_model_available,
    run_condition,
    score_commands,
    selected_cases,
    supported_entities,
    write_csv,
    write_jsonl,
)


async def run(args: argparse.Namespace) -> None:
    dataset = load_dataset(args.dataset, expected_case_count=args.expected_cases)
    cases = selected_cases(dataset, args.case, args.limit)
    allowed = supported_entities(dataset)
    model = await model_metadata()
    if any(condition != "rules_only" for condition in args.condition):
        require_model_available(model)
    rows: List[Dict[str, Any]] = []
    csv_rows: List[Dict[str, Any]] = []

    for repetition in range(1, args.repetitions + 1):
        for condition in args.condition:
            for case in cases:
                context = context_for(dataset, case)
                result = await run_condition(
                    condition, case["utterance"], context, allowed
                )
                score = score_commands(result["parsed"], case["expected"], allowed)
                fallback_used = result["trace"].get("fallback_used", False)
                metric_eligible = condition == "rules_only" or (
                    result["error"] is None and not fallback_used
                )
                metadata = base_metadata(
                    condition, repetition, model, args.repetitions
                )
                row = {
                    **metadata,
                    "dataset_id": dataset["dataset_id"],
                    "dataset_sha256": dataset_sha256(args.dataset),
                    "case_id": case["id"],
                    "category": case["category"],
                    "utterance": case["utterance"],
                    "context_id": case["context_id"],
                    "expected": case["expected"],
                    "predicted": result["parsed"],
                    "raw_model_output": result["raw_model_output"],
                    "schema_valid": result["schema_valid"],
                    "fallback_used": fallback_used,
                    "metric_eligible": metric_eligible,
                    "latency_ms": result["latency_ms"],
                    "error": result["error"],
                    "score": score,
                }
                rows.append(row)
                csv_rows.append(
                    {
                        **metadata,
                        "dataset_sha256": dataset_sha256(args.dataset),
                        "case_id": case["id"],
                        "category": case["category"],
                        "schema_valid": result["schema_valid"],
                        "fallback_used": fallback_used,
                        "metric_eligible": metric_eligible,
                        "latency_ms": result["latency_ms"],
                        "error": result["error"],
                        **score,
                    }
                )
                print(
                    f"{condition} {case['id']} rep={repetition} "
                    f"exact={score['exact_match']} error={bool(result['error'])}"
                )

    output_dir: Path = args.output_dir
    write_jsonl(output_dir / "ablation_runs.jsonl", rows)
    write_csv(
        output_dir / "ablation.csv",
        csv_rows,
        [
            "timestamp_utc",
            "git_commit",
            "model",
            "model_digest",
            "model_used",
            "temperature",
            "condition",
            "repetition_index",
            "repetition_count",
            "dataset_sha256",
            "case_id",
            "category",
            "schema_valid",
            "fallback_used",
            "metric_eligible",
            "exact_match",
            "ordered_match",
            "extra_command_count",
            "missing_command_count",
            "unsupported_entity_count",
            "unsupported_action_count",
            "expected_noop",
            "noop_correct",
            "intent_match",
            "latency_ms",
            "error",
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run four-condition KICS ablation")
    parser.add_argument(
        "--condition",
        action="append",
        choices=CONDITIONS,
        help="Condition to run; repeatable (default: all four)",
    )
    parser.add_argument("--case", action="append", help="Run only one case id; repeatable")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--expected-cases", type=int, default=40)
    parser.add_argument("--limit", type=int, help="Run only the first N selected cases")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    args.condition = args.condition or list(CONDITIONS)
    if args.repetitions < 1:
        parser.error("--repetitions must be at least 1")
    try:
        asyncio.run(run(args))
    except RuntimeError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
