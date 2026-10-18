#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any, Dict, List

from eval_core import (
    DATASET_PATH,
    RESULTS_DIR,
    base_metadata,
    context_for,
    dataset_sha256,
    load_dataset,
    model_metadata,
    require_model_available,
    score_commands,
    selected_cases,
    supported_entities,
    write_csv,
    write_jsonl,
)
from services.parser import parse_command


async def run(args: argparse.Namespace) -> None:
    dataset = load_dataset(args.dataset, expected_case_count=args.expected_cases)
    cases = selected_cases(dataset, args.case, args.limit)
    allowed = supported_entities(dataset)
    model = await model_metadata()
    require_model_available(model)
    rows: List[Dict[str, Any]] = []
    csv_rows: List[Dict[str, Any]] = []

    for repetition in range(1, args.repetitions + 1):
        for case in cases:
            context = context_for(dataset, case)
            final, llm_mode, trace = await parse_command(case["utterance"], allowed, context)
            raw = (
                None
                if trace.get("fallback_used")
                else trace.get("parsed_before_normalization")
            )
            expected = case["expected"]
            raw_score = score_commands(raw, expected, allowed)
            final_score = score_commands(final, expected, allowed)
            metric_eligible = not bool(trace.get("fallback_used"))
            metadata = base_metadata(
                "raw_vs_full", repetition, model, args.repetitions
            )
            row = {
                **metadata,
                "dataset_id": dataset["dataset_id"],
                "dataset_sha256": dataset_sha256(args.dataset),
                "case_id": case["id"],
                "category": case["category"],
                "utterance": case["utterance"],
                "context_id": case["context_id"],
                "expected": expected,
                "raw": raw,
                "final": final,
                "raw_model_output": trace.get("raw_model_output"),
                "llm_mode": llm_mode,
                "normalization_applied": trace.get("normalization_applied"),
                "policy_applied": trace.get("policy_applied"),
                "fallback_used": trace.get("fallback_used"),
                "metric_eligible": metric_eligible,
                "error": trace.get("error"),
                "raw_score": raw_score,
                "final_score": final_score,
            }
            rows.append(row)
            csv_rows.extend(
                [
                    _csv_row(row, "raw", raw_score),
                    _csv_row(row, "full_pipeline", final_score),
                ]
            )
            print(
                f"{case['id']} rep={repetition} raw={raw_score['exact_match']} "
                f"full={final_score['exact_match']} fallback={trace.get('fallback_used')}"
            )

    output_dir: Path = args.output_dir
    write_jsonl(output_dir / "raw_runs.jsonl", rows)
    write_csv(
        output_dir / "command_eval.csv",
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
            "stage",
            "exact_match",
            "ordered_match",
            "extra_command_count",
            "missing_command_count",
            "unsupported_entity_count",
            "unsupported_action_count",
            "expected_noop",
            "noop_correct",
            "intent_match",
            "fallback_used",
            "metric_eligible",
            "error",
        ],
    )


def _csv_row(row: Dict[str, Any], stage: str, score: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **{key: row[key] for key in (
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
        )},
        "stage": stage,
        **score,
        "fallback_used": row["fallback_used"],
        "metric_eligible": row["metric_eligible"],
        "error": row["error"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare raw LLM plans with final commands")
    parser.add_argument("--case", action="append", help="Run only one case id; repeatable")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--expected-cases", type=int, default=40)
    parser.add_argument("--limit", type=int, help="Run only the first N selected cases")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be at least 1")
    try:
        asyncio.run(run(args))
    except RuntimeError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
