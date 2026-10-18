#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import statistics
from pathlib import Path
from typing import Any, Dict, List

try:
    from .eval_core import (
        RESULTS_DIR,
        base_metadata,
        context_for,
        dataset_sha256,
        load_dataset,
        model_metadata,
        require_model_available,
        run_full_pipeline_timed,
        selected_cases,
        supported_entities,
        write_csv,
        write_jsonl,
    )
except ImportError:  # Direct script execution.
    from eval_core import (
        RESULTS_DIR,
        base_metadata,
        context_for,
        dataset_sha256,
        load_dataset,
        model_metadata,
        require_model_available,
        run_full_pipeline_timed,
        selected_cases,
        supported_entities,
        write_csv,
        write_jsonl,
    )


DEFAULT_CASES = ("C02", "C10", "C11", "C13", "C22", "C35")


async def run(args: argparse.Namespace) -> None:
    dataset = load_dataset()
    case_ids = args.case or list(DEFAULT_CASES)
    cases = selected_cases(dataset, case_ids)
    by_id = {case["id"]: case for case in cases}
    cases = [by_id[case_id] for case_id in case_ids]
    allowed = supported_entities(dataset)
    model = await model_metadata()
    require_model_available(model)

    for index in range(args.warmup):
        case = cases[index % len(cases)]
        await run_full_pipeline_timed(
            case["utterance"], context_for(dataset, case), allowed
        )

    rows: List[Dict[str, Any]] = []
    for repetition in range(1, args.repetitions + 1):
        case = cases[(repetition - 1) % len(cases)]
        result = await run_full_pipeline_timed(
            case["utterance"], context_for(dataset, case), allowed
        )
        row = {
            **base_metadata(
                "full_pipeline_warm_latency",
                repetition,
                model,
                args.repetitions,
            ),
            "dataset_id": dataset["dataset_id"],
            "dataset_sha256": dataset_sha256(),
            "case_id": case["id"],
            "category": case["category"],
            "physical_actuation_included": False,
            "context_acquisition_included": False,
            **result,
        }
        rows.append(row)
        print(
            f"rep={repetition} case={case['id']} llm_ms={result['llm_ms']} "
            f"post_ms={result['postprocess_ms']} total_ms={result['planning_total_ms']}"
        )

    summaries = [
        _summary("overall", "mixed", rows, args.warmup, model, dataset["dataset_id"])
    ]
    for case in cases:
        case_rows = [row for row in rows if row["case_id"] == case["id"]]
        summaries.append(
            _summary(
                "case",
                case["id"],
                case_rows,
                args.warmup,
                model,
                dataset["dataset_id"],
            )
        )

    output_dir: Path = args.output_dir
    write_jsonl(output_dir / "latency_runs.jsonl", rows + summaries)
    write_csv(
        output_dir / "latency.csv",
        [
            {
                key: value
                for key, value in row.items()
                if key not in {"parsed", "raw_model_output"}
            }
            for row in rows
        ],
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
            "dataset_id",
            "dataset_sha256",
            "case_id",
            "category",
            "physical_actuation_included",
            "context_acquisition_included",
            "llm_ms",
            "postprocess_ms",
            "planning_total_ms",
        ],
    )
    write_csv(
        output_dir / "latency_summary.csv",
        summaries,
        [
            "timestamp_utc",
            "git_commit",
            "model",
            "model_digest",
            "model_used",
            "temperature",
            "condition",
            "summary_scope",
            "case_id",
            "dataset_id",
            "dataset_sha256",
            "warmup_runs_total",
            "measured_runs",
            "physical_actuation_included",
            "context_acquisition_included",
            "mean_ms",
            "median_ms",
            "p95_ms",
        ],
    )
    for summary in summaries:
        print(summary)


def _summary(
    scope: str,
    case_id: str,
    rows: List[Dict[str, Any]],
    warmup_runs: int,
    model: Dict[str, Any],
    dataset_id: str,
) -> Dict[str, Any]:
    totals = [row["planning_total_ms"] for row in rows]
    return {
        **base_metadata(
            "full_pipeline_warm_latency_summary",
            len(rows),
            model,
            len(rows),
        ),
        "summary_scope": scope,
        "dataset_id": dataset_id,
        "dataset_sha256": dataset_sha256(),
        "case_id": case_id,
        "warmup_runs_total": warmup_runs,
        "measured_runs": len(rows),
        "physical_actuation_included": False,
        "context_acquisition_included": False,
        "mean_ms": round(statistics.fmean(totals), 3),
        "median_ms": round(statistics.median(totals), 3),
        "p95_ms": round(_percentile(totals, 0.95), 3),
    }


def _percentile(values: List[float], quantile: float) -> float:
    ordered = sorted(values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            int((len(ordered) - 1) * quantile + 0.999999),
        ),
    )
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure warm full-pipeline command-planning latency"
    )
    parser.add_argument(
        "--case",
        action="append",
        help=(
            "Representative case id; repeatable. Defaults to "
            + ", ".join(DEFAULT_CASES)
        ),
    )
    parser.add_argument("--warmup", type=int, default=6)
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    if args.warmup < 0 or args.repetitions < 1:
        parser.error("warmup must be >= 0 and repetitions must be >= 1")
    try:
        asyncio.run(run(args))
    except RuntimeError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
