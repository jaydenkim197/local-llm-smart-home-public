#!/usr/bin/env python3
"""Run frozen live-context checks against the deployed physical backend."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, sleep
from typing import Any, Dict, Iterable, List

import httpx


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = Path(__file__).resolve().parent
DATASET_PATH = EXPERIMENT_DIR / "live_context_cases.json"
DEFAULT_OUTPUT_DIR = EXPERIMENT_DIR / "results" / "live_context_v1" / "run"
CURTAIN_ID = "cover.living_room_curtain"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


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


def load_dataset(path: Path = DATASET_PATH) -> Dict[str, Any]:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset: Dict[str, Any]) -> None:
    if dataset.get("status") != "frozen_before_execution" or dataset.get("frozen") is not True:
        raise ValueError("Live-context dataset must be frozen before execution")
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Live-context dataset must contain at least one case")
    ids = set()
    for case in cases:
        case_id = case.get("id")
        if not case_id or case_id in ids:
            raise ValueError(f"Duplicate or missing case id: {case_id!r}")
        ids.add(case_id)
        if not isinstance(case.get("utterance"), str) or not case["utterance"].strip():
            raise ValueError(f"{case_id}: utterance is required")
        if not isinstance(case.get("expected_commands"), list):
            raise ValueError(f"{case_id}: expected_commands must be a list")
        if case.get("verification", {}).get("type") not in {"ha_cover_state", "no_actuation"}:
            raise ValueError(f"{case_id}: unsupported verification type")


def require_empty_output(output_dir: Path) -> None:
    paths = [output_dir / "live_context_runs.jsonl", output_dir / "live_context_summary.json"]
    existing = [path for path in paths if path.exists()]
    if existing:
        raise FileExistsError("Refusing to overwrite: " + ", ".join(str(path) for path in existing))


def curtain_from_context(context: Dict[str, Any]) -> Dict[str, Any]:
    return context.get("living_room", {}).get("curtain", {})


def live_snapshot(client: httpx.Client) -> Dict[str, Any]:
    response = client.get("/api/context")
    response.raise_for_status()
    payload = response.json()
    context = payload.get("home_context", payload)
    living_room = context.get("living_room", {})
    return {
        "context": context,
        "illuminance_lux": living_room.get("illuminance_lux"),
        "curtain": {
            "state": curtain_from_context(context).get("state"),
            "position": curtain_from_context(context).get("position"),
        },
        "derived": context.get("derived", {}),
    }


def precondition_met(case: Dict[str, Any], snapshot: Dict[str, Any]) -> tuple[bool, List[str]]:
    precondition = case.get("precondition", {})
    failures: List[str] = []
    illuminance = snapshot.get("illuminance_lux")
    if "illuminance_min_lux" in precondition and (
        not isinstance(illuminance, (int, float)) or illuminance < precondition["illuminance_min_lux"]
    ):
        failures.append("illuminance_below_minimum")
    if "illuminance_max_lux" in precondition and (
        not isinstance(illuminance, (int, float)) or illuminance > precondition["illuminance_max_lux"]
    ):
        failures.append("illuminance_above_maximum")
    expected_state = precondition.get("curtain_state")
    if expected_state and snapshot["curtain"].get("state") != expected_state:
        failures.append("curtain_state_mismatch")
    return not failures, failures


def wait_for_curtain_state(
    client: httpx.Client, expected_state: str, started: float, timeout_seconds: float = 35.0
) -> tuple[Dict[str, Any], float | None]:
    deadline = perf_counter() + timeout_seconds
    last = live_snapshot(client)
    while True:
        if last["curtain"].get("state") == expected_state:
            return last, round((perf_counter() - started) * 1000, 3)
        if perf_counter() >= deadline:
            return last, None
        sleep(0.5)
        last = live_snapshot(client)


def run_case(
    client: httpx.Client, case: Dict[str, Any], dataset: Dict[str, Any], dataset_path: Path
) -> Dict[str, Any]:
    before = live_snapshot(client)
    met, failures = precondition_met(case, before)
    row: Dict[str, Any] = {
        "created_at_utc": utc_now(),
        "git_commit": git_commit(),
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": sha256(dataset_path),
        "case_id": case["id"],
        "utterance": case["utterance"],
        "expected_intent": case["expected_intent"],
        "expected_commands": case["expected_commands"],
        "verification": case["verification"],
        "before": before,
        "precondition_met": met,
        "precondition_failures": failures,
        "metric_eligible": met,
    }
    if not met:
        row["error"] = "live_precondition_not_met"
        return row

    started = perf_counter()
    response = client.post("/api/command/text", json={"text": case["utterance"]})
    row["api_wall_latency_ms"] = round((perf_counter() - started) * 1000, 3)
    response.raise_for_status()
    payload = response.json()
    parsed = payload.get("parsed", {})
    result = payload.get("result", {})
    actual_commands = parsed.get("commands", [])
    row.update(
        {
            "after_response": live_snapshot(client),
            "actual_intent": parsed.get("intent"),
            "actual_commands": actual_commands,
            "command_exact": commands_exact(actual_commands, case["expected_commands"]),
            "result": result,
            "result_applied": result.get("applied", []),
            "result_errors": result.get("errors", []),
        }
    )

    verification = case["verification"]
    if verification["type"] == "ha_cover_state":
        after, settle_ms = wait_for_curtain_state(client, verification["expected_state"], started)
        row["after_verification"] = after
        row["curtain_settle_latency_ms"] = settle_ms
        row["state_verified"] = settle_ms is not None
    else:
        after = live_snapshot(client)
        row["after_verification"] = after
        expected_state = verification.get("expected_state")
        row["state_verified"] = (
            expected_state is None or after["curtain"].get("state") == expected_state
        )
        row["no_actuation_verified"] = not actual_commands and not row["result_applied"]
    return row


def row_passed(row: Dict[str, Any]) -> bool:
    if not row.get("metric_eligible") or not row.get("command_exact"):
        return False
    if row.get("actual_intent") != row.get("expected_intent"):
        return False
    if row["verification"]["type"] == "ha_cover_state":
        return row.get("state_verified") is True and not row.get("result_errors")
    return row.get("state_verified") is True and row.get("no_actuation_verified") is True


def persist(
    output_dir: Path, rows: List[Dict[str, Any]], dataset: Dict[str, Any], dataset_path: Path
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    runs_path = output_dir / "live_context_runs.jsonl"
    runs_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    eligible = [row for row in rows if row.get("metric_eligible")]
    passed = [row for row in eligible if row_passed(row)]
    summary = {
        "dataset_id": dataset["dataset_id"],
        "dataset_sha256": sha256(dataset_path),
        "git_commit": git_commit(),
        "completed_rows": len(rows),
        "eligible_rows": len(eligible),
        "passed_rows": len(passed),
        "failed_or_ineligible_rows": len(rows) - len(passed),
        "case_status": {row["case_id"]: "pass" if row_passed(row) else "not_passed" for row in rows},
    }
    (output_dir / "live_context_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-url", default="http://127.0.0.1:8000")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--case", action="append", help="Run only the named frozen case; repeatable")
    parser.add_argument("--allow-actuation", action="store_true")
    args = parser.parse_args()
    if not args.allow_actuation:
        raise RuntimeError("Refusing physical execution without --allow-actuation")
    dataset = load_dataset(args.dataset)
    cases = dataset["cases"]
    if args.case:
        requested = set(args.case)
        cases = [case for case in cases if case["id"] in requested]
        missing = requested - {case["id"] for case in cases}
        if missing:
            raise ValueError(f"Unknown case ids: {sorted(missing)}")
    require_empty_output(args.output_dir)
    rows: List[Dict[str, Any]] = []
    with httpx.Client(base_url=args.server_url, timeout=httpx.Timeout(90.0)) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        if health.json().get("control_backend") != "home_assistant":
            raise RuntimeError("Physical Home Assistant backend is required")
        for case in cases:
            row = run_case(client, case, dataset, args.dataset)
            rows.append(row)
            persist(args.output_dir, rows, dataset, args.dataset)
            print(f"{case['id']}: {'PASS' if row_passed(row) else 'NOT PASSED'}")
            if not row.get("precondition_met"):
                break


if __name__ == "__main__":
    main()
