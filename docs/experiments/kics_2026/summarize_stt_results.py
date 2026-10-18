#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Dict, List

try:
    from .eval_core import utc_now
except ImportError:  # Direct script execution.
    from eval_core import utc_now


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a completed STT evaluation CSV")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("The STT result CSV is empty")

    lines = [
        "# KICS 2026 STT Evaluation Summary",
        "",
        f"Generated at: {utc_now()}",
        "",
        "WER is corpus word error rate: total word edits divided by total reference words.",
        "Command accuracy is reported separately from transcription accuracy.",
        "",
        "| Slice | Rows | Eligible | Corpus WER | Transcript exact | Audio to gold command | Reference command preserved |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, group in _slices(rows):
        eligible = [row for row in group if _as_bool(row["metric_eligible"])]
        lines.append(
            f"| {label} | {len(group)} | {len(eligible)} | {_wer(group)} | "
            f"{_ratio(group, 'transcript_exact')} | {_ratio(eligible, 'audio_gold_exact')} | "
            f"{_ratio(eligible, 'reference_command_preserved')} |"
        )

    stt_latency = [float(row["stt_latency_ms"]) for row in rows]
    planning_latency = [float(row["planning_latency_ms"]) for row in rows]
    lines.extend(
        [
            "",
            "## Software Latency",
            "",
            "These timings exclude browser recording time and physical actuation.",
            "",
            "| Stage | Mean | Median |",
            "| --- | ---: | ---: |",
            f"| faster-whisper transcription | {sum(stt_latency) / len(stt_latency):.3f} ms | {median(stt_latency):.3f} ms |",
            f"| command planning after transcript | {sum(planning_latency) / len(planning_latency):.3f} ms | {median(planning_latency):.3f} ms |",
            "",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(args.output)


def _slices(rows: List[Dict[str, str]]):
    yield "overall", rows
    yield "action_required", [row for row in rows if not _as_bool(row["expected_noop"])]
    yield "no_op", [row for row in rows if _as_bool(row["expected_noop"])]
    by_category = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(row)
    for category in sorted(by_category):
        yield f"category:{category}", by_category[category]


def _wer(rows: List[Dict[str, str]]) -> str:
    words = sum(int(row["reference_words"]) for row in rows)
    errors = sum(int(row["word_errors"]) for row in rows)
    return f"{errors}/{words} ({(errors / words * 100) if words else 0:.1f}%)"


def _ratio(rows: List[Dict[str, str]], field: str) -> str:
    passed = sum(_as_bool(row[field]) for row in rows)
    return f"{passed}/{len(rows)} ({(passed / len(rows) * 100) if rows else 0:.1f}%)"


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


if __name__ == "__main__":
    main()
