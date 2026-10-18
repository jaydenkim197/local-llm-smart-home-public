#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

try:
    from .eval_core import (
        DATASET_PATH,
        base_metadata,
        context_for,
        dataset_sha256,
        git_commit,
        load_dataset,
        model_metadata,
        require_model_available,
        score_commands,
        supported_entities,
        utc_now,
        write_jsonl,
    )
    from .stt_eval_core import (
        DEFAULT_AUDIO_DIR,
        STT_DATASET_PATH,
        audio_path,
        expanded_cases,
        file_sha256,
        load_stt_dataset,
        word_error_stats,
    )
except ImportError:  # Direct script execution.
    from eval_core import (
        DATASET_PATH,
        base_metadata,
        context_for,
        dataset_sha256,
        git_commit,
        load_dataset,
        model_metadata,
        require_model_available,
        score_commands,
        supported_entities,
        utc_now,
        write_jsonl,
    )
    from stt_eval_core import (
        DEFAULT_AUDIO_DIR,
        STT_DATASET_PATH,
        audio_path,
        expanded_cases,
        file_sha256,
        load_stt_dataset,
        word_error_stats,
    )

from app.config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL
from services.parser import parse_command
from services.stt import _transcribe_with_faster_whisper


async def run(args: argparse.Namespace) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", args.speaker_id):
        raise ValueError(
            "Speaker id may contain only letters, digits, underscore, and hyphen"
        )
    stt_dataset = load_stt_dataset(args.dataset)
    command_dataset = load_dataset(DATASET_PATH, expected_case_count=40)
    cases = expanded_cases(stt_dataset)
    allowed = supported_entities(command_dataset)
    _require_complete_audio_set(args.audio_dir, args.speaker_id, cases, stt_dataset)
    _require_empty_output_dir(args.output_dir)
    model = await model_metadata()
    require_model_available(model)

    reference_rows: List[Dict[str, Any]] = []
    audio_rows: List[Dict[str, Any]] = []
    csv_rows: List[Dict[str, Any]] = []

    for case in cases:
        source = case["source"]
        context = context_for(command_dataset, source)
        reference_parsed, reference_mode, reference_trace = await parse_command(
            source["utterance"], allowed, context
        )
        reference_score = score_commands(reference_parsed, source["expected"], allowed)
        reference_fallback_used = reference_trace.get("fallback_used", False)
        reference_error = reference_trace.get("error")
        reference_row = {
            **base_metadata("stt_reference_text", 1, model),
            "stt_dataset_id": stt_dataset["dataset_id"],
            "stt_dataset_sha256": dataset_sha256(args.dataset),
            "command_dataset_sha256": dataset_sha256(DATASET_PATH),
            "stt_case_id": case["id"],
            "source_case_id": source["id"],
            "reference_text": source["utterance"],
            "parsed": reference_parsed,
            "score": reference_score,
            "llm_mode": reference_mode,
            "fallback_used": reference_fallback_used,
            "error": reference_error,
        }
        reference_rows.append(reference_row)

        for take in range(1, stt_dataset["takes_per_case"] + 1):
            path = audio_path(args.audio_dir, args.speaker_id, case["id"], take)
            stt_started = perf_counter()
            transcript = _transcribe_with_faster_whisper(str(path))
            stt_latency_ms = round((perf_counter() - stt_started) * 1000, 3)
            word_score = word_error_stats(source["utterance"], transcript)

            planning_started = perf_counter()
            parsed, llm_mode, trace = await parse_command(transcript, allowed, context)
            planning_latency_ms = round((perf_counter() - planning_started) * 1000, 3)
            gold_score = score_commands(parsed, source["expected"], allowed)
            preservation_score = score_commands(parsed, reference_parsed, allowed)
            fallback_used = trace.get("fallback_used", False)
            error = trace.get("error")
            metric_eligible = (
                not fallback_used
                and error is None
                and llm_mode.startswith("ollama:")
                and not reference_fallback_used
                and reference_error is None
                and reference_mode.startswith("ollama:")
            )

            row = {
                **base_metadata("stt_full_pipeline", take, model, stt_dataset["takes_per_case"]),
                "stt_dataset_id": stt_dataset["dataset_id"],
                "stt_dataset_sha256": dataset_sha256(args.dataset),
                "command_dataset_sha256": dataset_sha256(DATASET_PATH),
                "speaker_id": args.speaker_id,
                "stt_case_id": case["id"],
                "source_case_id": source["id"],
                "category": source["category"],
                "context_id": source["context_id"],
                "take": take,
                "audio_file": str(path.relative_to(args.audio_dir)),
                "audio_sha256": file_sha256(path),
                "reference_text": source["utterance"],
                "transcript": transcript,
                "word_score": word_score,
                "expected": source["expected"],
                "reference_text_parsed": reference_parsed,
                "reference_text_gold_score": reference_score,
                "reference_text_fallback_used": reference_fallback_used,
                "reference_text_error": reference_error,
                "parsed": parsed,
                "gold_score": gold_score,
                "reference_preservation_score": preservation_score,
                "stt_model": WHISPER_MODEL,
                "stt_device": WHISPER_DEVICE,
                "stt_compute_type": WHISPER_COMPUTE_TYPE,
                "stt_latency_ms": stt_latency_ms,
                "planning_latency_ms": planning_latency_ms,
                "llm_mode": llm_mode,
                "fallback_used": fallback_used,
                "error": error,
                "metric_eligible": metric_eligible,
            }
            audio_rows.append(row)
            csv_rows.append(_csv_row(row))
            print(
                f"{case['id']} take={take} wer={word_score['wer']:.3f} "
                f"gold={gold_score['exact_match']} preserved={preservation_score['exact_match']} "
                f"fallback={fallback_used}"
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "reference_text_runs.jsonl", reference_rows)
    write_jsonl(args.output_dir / "audio_runs.jsonl", audio_rows)
    _write_csv(args.output_dir / "stt_eval.csv", csv_rows)
    manifest = {
        "created_at_utc": utc_now(),
        "git_commit": git_commit(),
        "stt_dataset_sha256": dataset_sha256(args.dataset),
        "command_dataset_sha256": dataset_sha256(DATASET_PATH),
        "speaker_id": args.speaker_id,
        "recordings": len(audio_rows),
        "stt_model": WHISPER_MODEL,
        "stt_device": WHISPER_DEVICE,
        "stt_compute_type": WHISPER_COMPUTE_TYPE,
        "llm_model": model.get("model"),
        "llm_model_digest": model.get("digest"),
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _require_complete_audio_set(
    audio_dir: Path,
    speaker_id: str,
    cases: List[Dict[str, Any]],
    dataset: Dict[str, Any],
) -> None:
    missing = []
    for case in cases:
        for take in range(1, dataset["takes_per_case"] + 1):
            path = audio_path(audio_dir, speaker_id, case["id"], take)
            if not path.is_file() or path.stat().st_size == 0:
                missing.append(str(path))
    if missing:
        preview = "\n".join(missing[:5])
        raise FileNotFoundError(
            f"Missing {len(missing)} required audio recordings. First missing files:\n{preview}"
        )


def _require_empty_output_dir(output_dir: Path) -> None:
    protected = ("reference_text_runs.jsonl", "audio_runs.jsonl", "stt_eval.csv", "run_manifest.json")
    existing = [str(output_dir / name) for name in protected if (output_dir / name).exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite an existing STT result: " + ", ".join(existing)
        )


def _csv_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "git_commit": row["git_commit"],
        "stt_dataset_sha256": row["stt_dataset_sha256"],
        "command_dataset_sha256": row["command_dataset_sha256"],
        "speaker_id": row["speaker_id"],
        "stt_case_id": row["stt_case_id"],
        "source_case_id": row["source_case_id"],
        "category": row["category"],
        "take": row["take"],
        "reference_text": row["reference_text"],
        "transcript": row["transcript"],
        "reference_words": row["word_score"]["reference_words"],
        "word_errors": row["word_score"]["word_errors"],
        "wer": row["word_score"]["wer"],
        "transcript_exact": row["word_score"]["transcript_exact"],
        "reference_text_gold_exact": row["reference_text_gold_score"]["exact_match"],
        "reference_text_fallback_used": row["reference_text_fallback_used"],
        "audio_gold_exact": row["gold_score"]["exact_match"],
        "reference_command_preserved": row["reference_preservation_score"]["exact_match"],
        "expected_noop": row["gold_score"]["expected_noop"],
        "stt_latency_ms": row["stt_latency_ms"],
        "planning_latency_ms": row["planning_latency_ms"],
        "fallback_used": row["fallback_used"],
        "metric_eligible": row["metric_eligible"],
    }


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("No STT result rows were produced")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate fixed audio through STT and command planning")
    parser.add_argument("--dataset", type=Path, default=STT_DATASET_PATH)
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--speaker-id", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results" / "stt_v1",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except (FileNotFoundError, FileExistsError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
