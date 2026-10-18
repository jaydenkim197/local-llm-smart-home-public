#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, sleep
from typing import Any, Dict, Iterable, List

import httpx


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = Path(__file__).resolve().parent
DATASET_PATH = EXPERIMENT_DIR / "physical_e2e_cases.json"
DEFAULT_AUDIO_DIR = ROOT / "data" / "kics_2026_stt"
DEFAULT_OUTPUT_DIR = EXPERIMENT_DIR / "results" / "physical_e2e_v1" / "curtain"
CURTAIN_ID = "cover.living_room_curtain"
AC_ID = "climate.air_conditioner"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def load_physical_dataset(path: Path = DATASET_PATH) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        dataset = json.load(handle)
    validate_physical_dataset(dataset)
    return dataset


def validate_physical_dataset(dataset: Dict[str, Any]) -> None:
    if not dataset.get("frozen") or dataset.get("status") != "frozen_before_execution":
        raise ValueError("Physical dataset must be frozen before execution")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        raise ValueError("Physical dataset must contain exactly four cases")
    seen = set()
    for case in cases:
        case_id = case.get("id")
        if not case_id or case_id in seen:
            raise ValueError(f"Duplicate or missing physical case id: {case_id!r}")
        seen.add(case_id)
        if not str(case.get("audio_file", "")).endswith(".webm"):
            raise ValueError(f"{case_id}: audio_file must be a WebM recording")
        commands = case.get("expected_commands")
        if not isinstance(commands, list) or len(commands) != 1:
            raise ValueError(f"{case_id}: exactly one expected command is required")
        entity_id = commands[0].get("entity_id")
        if entity_id not in {CURTAIN_ID, AC_ID}:
            raise ValueError(f"{case_id}: unsupported physical entity {entity_id!r}")
        verifier = case.get("verification", {}).get("type")
        if verifier not in {"ha_cover_state", "operator_ir_observation"}:
            raise ValueError(f"{case_id}: unsupported verification type {verifier!r}")


def canonical_commands(commands: Iterable[Dict[str, Any]]) -> List[tuple[str, str, str]]:
    return sorted(
        (
            str(command.get("entity_id", "")),
            str(command.get("action", "")),
            json.dumps(command.get("value"), sort_keys=True, separators=(",", ":")),
        )
        for command in commands
        if isinstance(command, dict)
    )


def commands_exact(actual: Iterable[Dict[str, Any]], expected: Iterable[Dict[str, Any]]) -> bool:
    return canonical_commands(actual) == canonical_commands(expected)


def curtain_snapshot(devices_payload: Dict[str, Any]) -> Dict[str, Any]:
    curtain = devices_payload.get("devices", {}).get(CURTAIN_ID, {})
    return {"state": curtain.get("state"), "position": curtain.get("position")}


def wait_for_curtain_state(
    client: httpx.Client,
    expected_state: str,
    request_started: float,
    timeout_seconds: float = 30.0,
    interval_seconds: float = 0.5,
) -> tuple[Dict[str, Any], float | None]:
    deadline = perf_counter() + timeout_seconds
    last = curtain_snapshot(client.get("/api/devices").json())
    while True:
        if last.get("state") == expected_state:
            return last, round((perf_counter() - request_started) * 1000, 3)
        if perf_counter() >= deadline:
            return last, None
        sleep(interval_seconds)
        last = curtain_snapshot(client.get("/api/devices").json())


def selected_cases(dataset: Dict[str, Any], case_ids: List[str] | None, include_ac: bool) -> List[Dict[str, Any]]:
    cases = list(dataset["cases"])
    if case_ids:
        wanted = set(case_ids)
        cases = [case for case in cases if case["id"] in wanted]
        missing = wanted - {case["id"] for case in cases}
        if missing:
            raise ValueError(f"Unknown physical case ids: {sorted(missing)}")
    if not include_ac:
        cases = [
            case
            for case in cases
            if case["expected_commands"][0]["entity_id"] != AC_ID
        ]
    return cases


def require_empty_output(output_dir: Path) -> None:
    protected = ("physical_runs.jsonl", "physical_summary.json")
    existing = [output_dir / name for name in protected if (output_dir / name).exists()]
    if existing:
        raise FileExistsError(
            "Physical result files already exist and will not be overwritten: "
            + ", ".join(str(path) for path in existing)
        )


def health_preflight(client: httpx.Client, include_ac: bool) -> Dict[str, Any]:
    response = client.get("/api/health")
    response.raise_for_status()
    health = response.json()
    required = {
        "control_backend": health.get("control_backend") == "home_assistant",
        "home_assistant_reachable": health.get("home_assistant_reachable") is True,
        "ollama_reachable": health.get("ollama_reachable") is True,
        "stt_configured": health.get("stt_configured") is True,
    }
    if include_ac:
        required["air_conditioner_scene_control_configured"] = (
            health.get("air_conditioner_scene_control_configured") is True
        )
    failed = [name for name, passed in required.items() if not passed]
    if failed:
        raise RuntimeError(f"Physical preflight failed: {', '.join(failed)}")
    return health


def operator_observation(case: Dict[str, Any]) -> str:
    prompt = (
        f"{case['id']} physical IR result observed? "
        "Enter y=yes, n=no, u=unclear: "
    )
    while True:
        value = input(prompt).strip().lower()
        if value in {"y", "yes"}:
            return "observed_success"
        if value in {"n", "no"}:
            return "observed_failure"
        if value in {"u", "unclear", ""}:
            return "unclear"


def physical_row_passed(row: Dict[str, Any], observe_ac: bool) -> bool:
    if not row.get("metric_eligible") or not row.get("command_accepted"):
        return False
    if row.get("verification_type") == "ha_cover_state":
        return row.get("state_verified") is True
    if observe_ac:
        return row.get("operator_observation") == "observed_success"
    return True


def persist_results(
    output_dir: Path,
    rows: List[Dict[str, Any]],
    dataset: Dict[str, Any],
    args: argparse.Namespace,
    health: Dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    runs_path = output_dir / "physical_runs.jsonl"
    with runs_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary = summarize(rows, dataset, args, health)
    (output_dir / "physical_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run(args: argparse.Namespace) -> None:
    if not args.allow_actuation:
        raise RuntimeError("Refusing physical execution without --allow-actuation")
    dataset = load_physical_dataset(args.dataset)
    cases = selected_cases(dataset, args.case, args.include_ac)
    if not cases:
        raise ValueError("No physical cases selected")
    require_empty_output(args.output_dir)
    for case in cases:
        audio = args.audio_dir / case["audio_file"]
        if not audio.is_file() or audio.stat().st_size == 0:
            raise FileNotFoundError(f"Missing physical input recording: {audio}")

    timeout = httpx.Timeout(args.timeout)
    rows: List[Dict[str, Any]] = []
    with httpx.Client(base_url=args.server_url, timeout=timeout) as client:
        health = health_preflight(client, args.include_ac)
        for repetition in range(1, args.repetitions + 1):
            for case in cases:
                before = curtain_snapshot(client.get("/api/devices").json())
                required_state = case.get("precondition", {}).get("curtain_state")
                precondition_met = required_state is None or before["state"] == required_state
                row: Dict[str, Any] = {
                    "created_at_utc": utc_now(),
                    "git_commit": git_commit(),
                    "dataset_id": dataset["dataset_id"],
                    "dataset_sha256": sha256(args.dataset),
                    "case_id": case["id"],
                    "repetition": repetition,
                    "repetitions": args.repetitions,
                    "audio_file": case["audio_file"],
                    "audio_sha256": sha256(args.audio_dir / case["audio_file"]),
                    "reference_text": case["reference_text"],
                    "expected_commands": case["expected_commands"],
                    "verification_type": case["verification"]["type"],
                    "before": before,
                    "precondition_met": precondition_met,
                    "metric_eligible": precondition_met,
                }
                if not precondition_met:
                    row.update({"error": "physical_precondition_not_met"})
                    rows.append(row)
                    persist_results(args.output_dir, rows, dataset, args, health)
                    print(f"{case['id']} rep={repetition} SKIP precondition={before}")
                    if not args.continue_on_failure:
                        return
                    continue

                audio_path = args.audio_dir / case["audio_file"]
                started = perf_counter()
                with audio_path.open("rb") as handle:
                    response = client.post(
                        "/api/command/audio",
                        files={"file": (audio_path.name, handle, "audio/webm")},
                    )
                wall_latency_ms = round((perf_counter() - started) * 1000, 3)
                response.raise_for_status()
                payload = response.json()
                after = curtain_snapshot(client.get("/api/devices").json())
                actual_commands = payload.get("parsed", {}).get("commands", [])
                exact = commands_exact(actual_commands, case["expected_commands"])
                applied = payload.get("result", {}).get("applied", [])
                apply_success = payload.get("result", {}).get("success") is True
                command_accepted = exact and apply_success and bool(applied)

                state_verified = None
                physical_settle_latency_ms = None
                adapter_settled = None
                if case["verification"]["type"] == "ha_cover_state":
                    expected_state = case["verification"]["expected_state"]
                    after, physical_settle_latency_ms = wait_for_curtain_state(
                        client, expected_state, started
                    )
                    adapter_settled = any(
                        item.get("entity_id") == CURTAIN_ID
                        and item.get("settled") is True
                        for item in applied
                    )
                    state_verified = (
                        command_accepted
                        and after["state"] == expected_state
                    )

                observation = "not_applicable"
                if case["verification"]["type"] == "operator_ir_observation":
                    observation = (
                        operator_observation(case) if args.observe_ac else "not_observed"
                    )

                row.update(
                    {
                        "transcript": payload.get("transcript"),
                        "stt_mode": payload.get("stt_mode"),
                        "llm_mode": payload.get("llm_mode"),
                        "actual_commands": actual_commands,
                        "command_exact_match": exact,
                        "apply_success": apply_success,
                        "command_accepted": command_accepted,
                        "adapter_settled_within_response": adapter_settled,
                        "state_verified": state_verified,
                        "physical_settle_latency_ms": physical_settle_latency_ms,
                        "operator_observation": observation,
                        "after": after,
                        "wall_latency_ms": wall_latency_ms,
                        "fallback_used": payload.get("llm_trace", {}).get(
                            "fallback_used", False
                        ),
                        "error": payload.get("llm_trace", {}).get("error"),
                    }
                )
                rows.append(row)
                persist_results(args.output_dir, rows, dataset, args, health)
                print(
                    f"{case['id']} rep={repetition} exact={exact} "
                    f"accepted={command_accepted} state_verified={state_verified} "
                    f"wall_ms={wall_latency_ms:.3f}"
                )
                if not physical_row_passed(row, args.observe_ac) and not args.continue_on_failure:
                    print("Stopping after failed physical verification; evidence was preserved.")
                    return

    persist_results(args.output_dir, rows, dataset, args, health)


def summarize(
    rows: List[Dict[str, Any]],
    dataset: Dict[str, Any],
    args: argparse.Namespace,
    health: Dict[str, Any],
) -> Dict[str, Any]:
    eligible = [row for row in rows if row.get("metric_eligible")]
    latencies = [float(row["wall_latency_ms"]) for row in eligible if "wall_latency_ms" in row]
    settle_latencies = [
        float(row["physical_settle_latency_ms"])
        for row in eligible
        if row.get("physical_settle_latency_ms") is not None
    ]
    curtain = [row for row in eligible if row.get("verification_type") == "ha_cover_state"]
    ac = [row for row in eligible if row.get("verification_type") == "operator_ir_observation"]
    observed_ac = [row for row in ac if row.get("operator_observation") != "not_observed"]
    return {
        "created_at_utc": utc_now(),
        "git_commit": git_commit(),
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": sha256(args.dataset),
        "server_url": args.server_url,
        "llm_model": health.get("llm_model"),
        "stt_model": health.get("stt_model"),
        "rows": len(rows),
        "eligible_rows": len(eligible),
        "command_exact_successes": sum(bool(row.get("command_exact_match")) for row in eligible),
        "command_accepted_successes": sum(bool(row.get("command_accepted")) for row in eligible),
        "curtain_state_verified_successes": sum(bool(row.get("state_verified")) for row in curtain),
        "curtain_rows": len(curtain),
        "ac_command_accepted_successes": sum(bool(row.get("command_accepted")) for row in ac),
        "ac_rows": len(ac),
        "ac_operator_observed_successes": sum(
            row.get("operator_observation") == "observed_success" for row in observed_ac
        ),
        "ac_operator_observed_rows": len(observed_ac),
        "wall_latency_ms": {
            "mean": round(statistics.mean(latencies), 3) if latencies else None,
            "median": round(statistics.median(latencies), 3) if latencies else None,
            "minimum": round(min(latencies), 3) if latencies else None,
            "maximum": round(max(latencies), 3) if latencies else None,
            "first_observation": round(latencies[0], 3) if latencies else None,
        },
        "curtain_physical_settle_latency_ms": {
            "mean": round(statistics.mean(settle_latencies), 3) if settle_latencies else None,
            "median": round(statistics.median(settle_latencies), 3) if settle_latencies else None,
            "minimum": round(min(settle_latencies), 3) if settle_latencies else None,
            "maximum": round(max(settle_latencies), 3) if settle_latencies else None,
            "first_observation": round(settle_latencies[0], 3) if settle_latencies else None,
        },
        "interpretation": (
            "Wall time starts before fixed WebM upload and ends after the API response. "
            "Curtain physical settle time continues polling Home Assistant after the "
            "response when needed. Both exclude browser capture and speaking time. AC "
            "physical state is counted only when separately observed by an operator."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run guarded physical end-to-end trials")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--server-url", default="http://127.0.0.1:8000")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--case", action="append")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--allow-actuation", action="store_true")
    parser.add_argument("--include-ac", action="store_true")
    parser.add_argument("--observe-ac", action="store_true")
    parser.add_argument("--continue-on-failure", action="store_true")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    if args.observe_ac and not args.include_ac:
        parser.error("--observe-ac requires --include-ac")
    return args


if __name__ == "__main__":
    run(parse_args())
