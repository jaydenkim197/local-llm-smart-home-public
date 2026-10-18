#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

try:
    from .eval_core import RESULTS_DIR, schema_is_valid, utc_now
except ImportError:  # Direct script execution.
    from eval_core import RESULTS_DIR, schema_is_valid, utc_now


CONDITION_ORDER = ("llm_only", "llm_context", "rules_only", "full_pipeline")
EXPECTED_CASES = 40
EXPECTED_REPETITIONS = 5


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize five-run paired KICS command stability results"
    )
    parser.add_argument(
        "--paired",
        type=Path,
        default=RESULTS_DIR / "stability_5runs" / "paired" / "raw_runs.jsonl",
    )
    parser.add_argument(
        "--baselines",
        type=Path,
        default=RESULTS_DIR / "stability_5runs" / "baselines" / "ablation_runs.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RESULTS_DIR / "stability_5runs" / "stability-summary.md",
    )
    parser.add_argument(
        "--case-csv",
        type=Path,
        default=RESULTS_DIR / "stability_5runs" / "case-success-counts.csv",
    )
    args = parser.parse_args()

    rows = normalize_rows(_read_jsonl(args.paired), _read_jsonl(args.baselines))
    validate_stability_rows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(rows), encoding="utf-8")
    write_case_counts(args.case_csv, rows)
    print(args.output)
    print(args.case_csv)


def normalize_rows(
    paired_rows: Sequence[Dict[str, Any]],
    baseline_rows: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for row in paired_rows:
        common = _common(row)
        eligible = bool(row.get("metric_eligible"))
        normalized.append(
            {
                **common,
                "condition": "llm_context",
                "eligible": eligible,
                "schema_valid": schema_is_valid(row.get("raw")),
                **_score_fields(row["raw_score"]),
            }
        )
        normalized.append(
            {
                **common,
                "condition": "full_pipeline",
                "eligible": eligible,
                "schema_valid": schema_is_valid(row.get("final")),
                **_score_fields(row["final_score"]),
            }
        )

    for row in baseline_rows:
        if row.get("condition") not in {"llm_only", "rules_only"}:
            continue
        normalized.append(
            {
                **_common(row),
                "condition": row["condition"],
                "eligible": bool(row.get("metric_eligible")),
                "schema_valid": bool(row.get("schema_valid")),
                **_score_fields(row["score"]),
            }
        )
    return normalized


def validate_stability_rows(rows: Sequence[Dict[str, Any]]) -> None:
    conditions = {row["condition"] for row in rows}
    if conditions != set(CONDITION_ORDER):
        raise ValueError(f"Expected conditions {CONDITION_ORDER}, found {sorted(conditions)}")

    hashes = {row["dataset_sha256"] for row in rows}
    if len(hashes) != 1:
        raise ValueError("Stability inputs use different dataset hashes")

    seen = set()
    for row in rows:
        key = (row["condition"], row["repetition_index"], row["case_id"])
        if key in seen:
            raise ValueError(f"Duplicate stability row: {key}")
        seen.add(key)

    for condition in CONDITION_ORDER:
        condition_rows = [row for row in rows if row["condition"] == condition]
        repetitions = {row["repetition_index"] for row in condition_rows}
        if repetitions != set(range(1, EXPECTED_REPETITIONS + 1)):
            raise ValueError(f"{condition}: expected repetitions 1..5, found {repetitions}")
        for repetition in repetitions:
            run_rows = [
                row for row in condition_rows if row["repetition_index"] == repetition
            ]
            if len(run_rows) != EXPECTED_CASES:
                raise ValueError(
                    f"{condition} repetition {repetition}: expected 40 cases, "
                    f"found {len(run_rows)}"
                )


def render_markdown(rows: Sequence[Dict[str, Any]]) -> str:
    first = rows[0]
    lines = [
        "# KICS 2026 Five-Run Stability Summary",
        "",
        f"Generated at: {utc_now()}",
        "",
        f"- Dataset SHA-256: `{first['dataset_sha256']}`",
        f"- Model: `{first['model']}`",
        f"- Model digest: `{first['model_digest']}`",
        f"- Temperature: `{first['temperature']}`",
        "- Repetitions: 5 complete 40-case runs per condition",
        "- `llm_context` and `full_pipeline` are paired stages of the same inference.",
        "",
        "## Per-Run Results",
        "",
        "| Condition | Run | Overall | Action required | No-op | Schema failures | Excluded | Fallback |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in CONDITION_ORDER:
        for repetition in range(1, EXPECTED_REPETITIONS + 1):
            run_rows = _run_rows(rows, condition, repetition)
            lines.append(
                "| {condition} | {repetition} | {overall} | {action} | {noop} | "
                "{schema} | {excluded} | {fallback} |".format(
                    condition=condition,
                    repetition=repetition,
                    overall=_fraction(run_rows),
                    action=_fraction(
                        [row for row in run_rows if not row["expected_noop"]]
                    ),
                    noop=_fraction([row for row in run_rows if row["expected_noop"]]),
                    schema=sum(not row["schema_valid"] for row in run_rows),
                    excluded=sum(not row["eligible"] for row in run_rows),
                    fallback=sum(bool(row["fallback_used"]) for row in run_rows),
                )
            )

    lines.extend(
        [
            "",
            "## Aggregate Stability",
            "",
            "Mean and sample standard deviation are calculated over the five per-run percentages.",
            "",
            "| Condition | Overall mean +/- SD | Action mean +/- SD | No-op mean +/- SD | Always success | Variable | Always failure |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for condition in CONDITION_ORDER:
        condition_rows = [row for row in rows if row["condition"] == condition]
        counts = case_success_counts(condition_rows)
        classes = [classify_success_count(value) for value in counts.values()]
        lines.append(
            "| {condition} | {overall} | {action} | {noop} | {always} | {variable} | {never} |".format(
                condition=condition,
                overall=_mean_sd(rows, condition),
                action=_mean_sd(rows, condition, expected_noop=False),
                noop=_mean_sd(rows, condition, expected_noop=True),
                always=classes.count("always_success"),
                variable=classes.count("variable"),
                never=classes.count("always_failure"),
            )
        )

    lines.extend(["", "## Variable And Always-Failing Cases", ""])
    for condition in CONDITION_ORDER:
        counts = case_success_counts(
            [row for row in rows if row["condition"] == condition]
        )
        noteworthy = [
            f"{case_id} {count}/5"
            for case_id, count in sorted(counts.items())
            if count < EXPECTED_REPETITIONS
        ]
        lines.append(f"- `{condition}`: " + (", ".join(noteworthy) or "none"))
    lines.append("")
    return "\n".join(lines)


def case_success_counts(rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    case_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        case_rows[row["case_id"]].append(row)
    return {
        case_id: sum(row["eligible"] and row["exact_match"] for row in values)
        for case_id, values in case_rows.items()
    }


def classify_success_count(count: int) -> str:
    if count == EXPECTED_REPETITIONS:
        return "always_success"
    if count == 0:
        return "always_failure"
    return "variable"


def write_case_counts(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_condition = {
        condition: case_success_counts(
            [row for row in rows if row["condition"] == condition]
        )
        for condition in CONDITION_ORDER
    }
    case_ids = sorted(next(iter(by_condition.values())).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case_id", *CONDITION_ORDER])
        for case_id in case_ids:
            writer.writerow(
                [case_id, *(by_condition[condition][case_id] for condition in CONDITION_ORDER)]
            )


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _common(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "timestamp_utc",
            "git_commit",
            "model",
            "model_digest",
            "temperature",
            "dataset_sha256",
            "case_id",
            "category",
            "repetition_index",
            "fallback_used",
            "error",
        )
    }


def _score_fields(score: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "exact_match": bool(score["exact_match"]),
        "expected_noop": bool(score["expected_noop"]),
    }


def _run_rows(
    rows: Sequence[Dict[str, Any]], condition: str, repetition: int
) -> List[Dict[str, Any]]:
    return [
        row
        for row in rows
        if row["condition"] == condition and row["repetition_index"] == repetition
    ]


def _fraction(rows: Sequence[Dict[str, Any]]) -> str:
    eligible = [row for row in rows if row["eligible"]]
    passed = sum(row["exact_match"] for row in eligible)
    percent = (passed / len(eligible) * 100) if eligible else 0.0
    return f"{passed}/{len(eligible)} ({percent:.1f}%)"


def _mean_sd(
    rows: Sequence[Dict[str, Any]],
    condition: str,
    expected_noop: bool | None = None,
) -> str:
    percentages = []
    for repetition in range(1, EXPECTED_REPETITIONS + 1):
        run_rows = _run_rows(rows, condition, repetition)
        if expected_noop is not None:
            run_rows = [
                row for row in run_rows if row["expected_noop"] is expected_noop
            ]
        eligible = [row for row in run_rows if row["eligible"]]
        percentages.append(sum(row["exact_match"] for row in eligible) / len(eligible) * 100)
    return f"{statistics.fmean(percentages):.1f} +/- {statistics.stdev(percentages):.1f}%"


if __name__ == "__main__":
    main()
