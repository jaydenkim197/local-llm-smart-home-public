from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import OLLAMA_MODEL, OLLAMA_URL
from services.parser import (
    PHYSICAL_ACTIONS_BY_ENTITY,
    _apply_context_policy,
    _build_llm_user_content,
    _fallback_parse,
    _normalize_parsed_command,
    _parse_with_ollama,
    _restrict_to_supported_entities,
    _validate_or_raise,
    parse_command,
)
from services.home_context import (
    BRIGHT_LUX_THRESHOLD,
    DARK_LUX_THRESHOLD,
    HOT_C_THRESHOLD,
    HUMID_PERCENT_THRESHOLD,
)


EXPERIMENT_DIR = Path(__file__).resolve().parent
DATASET_PATH = EXPERIMENT_DIR / "cases.json"
HELDOUT_DATASET_PATH = EXPERIMENT_DIR / "heldout_cases.json"
RESULTS_DIR = EXPERIMENT_DIR / "results"
TEMPERATURE = 0.0

CONDITIONS = (
    "llm_only",
    "llm_context",
    "full_pipeline",
    "rules_only",
)

PACKAGE_NAMES = (
    "fastapi",
    "uvicorn",
    "httpx",
    "jsonschema",
    "faster-whisper",
    "ctranslate2",
    "astral",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dataset(
    path: Path = DATASET_PATH, expected_case_count: int = 40
) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        dataset = json.load(handle)
    validate_dataset(dataset, expected_case_count=expected_case_count)
    return dataset


def validate_dataset(dataset: Dict[str, Any], expected_case_count: int = 40) -> None:
    cases = dataset.get("cases")
    contexts = dataset.get("contexts")
    supported = set(dataset.get("supported_entities", []))
    if not isinstance(cases, list) or len(cases) != expected_case_count:
        raise ValueError(
            f"The command dataset must contain exactly {expected_case_count} cases"
        )
    if not isinstance(contexts, dict) or not contexts:
        raise ValueError("Dataset contexts must be a non-empty object")
    if not supported:
        raise ValueError("Dataset must define supported_entities")

    seen_ids = set()
    for case in cases:
        case_id = case.get("id")
        if not case_id or case_id in seen_ids:
            raise ValueError(f"Duplicate or missing case id: {case_id!r}")
        seen_ids.add(case_id)
        if case.get("context_id") not in contexts:
            raise ValueError(f"{case_id}: unknown context_id")
        if not str(case.get("utterance", "")).strip():
            raise ValueError(f"{case_id}: utterance is empty")
        expected = case.get("expected", {})
        commands = expected.get("commands")
        if not isinstance(commands, list):
            raise ValueError(f"{case_id}: expected.commands must be a list")
        for command in commands:
            if command.get("entity_id") not in supported:
                raise ValueError(
                    f"{case_id}: gold command targets unsupported entity "
                    f"{command.get('entity_id')!r}"
                )
            if not command.get("action"):
                raise ValueError(f"{case_id}: gold command action is missing")
            allowed_actions = PHYSICAL_ACTIONS_BY_ENTITY.get(command["entity_id"])
            if allowed_actions is not None and command["action"] not in allowed_actions:
                raise ValueError(
                    f"{case_id}: gold command action {command['action']!r} is not "
                    f"physically supported for {command['entity_id']!r}"
                )
        try:
            _validate_or_raise(expected)
        except Exception as exc:
            raise ValueError(f"{case_id}: invalid gold command schema: {exc}") from exc

    for context_id, context in contexts.items():
        if context.get("source") == "unavailable":
            continue
        room = context.get("living_room", {})
        derived = context.get("derived", {})
        expected_derived = {
            "is_dark": room.get("illuminance_lux") < DARK_LUX_THRESHOLD,
            "is_bright": room.get("illuminance_lux") > BRIGHT_LUX_THRESHOLD,
            "is_hot": room.get("temperature_c") > HOT_C_THRESHOLD,
            "is_humid": room.get("humidity_percent") > HUMID_PERCENT_THRESHOLD,
        }
        if derived != expected_derived:
            raise ValueError(
                f"{context_id}: derived flags do not match production thresholds"
            )


def selected_cases(
    dataset: Dict[str, Any], case_ids: Optional[Sequence[str]] = None, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    cases = list(dataset["cases"])
    if case_ids:
        wanted = set(case_ids)
        cases = [case for case in cases if case["id"] in wanted]
        missing = wanted - {case["id"] for case in cases}
        if missing:
            raise ValueError(f"Unknown case ids: {sorted(missing)}")
    if limit is not None:
        cases = cases[:limit]
    return cases


def context_for(dataset: Dict[str, Any], case: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(dataset["contexts"][case["context_id"]]))


def supported_entities(dataset: Dict[str, Any]) -> set[str]:
    return set(dataset["supported_entities"])


def dataset_sha256(path: Path = DATASET_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_command(command: Dict[str, Any]) -> Tuple[str, str, str]:
    value = command.get("value", None)
    return (
        str(command.get("entity_id", "")),
        str(command.get("action", "")),
        json.dumps(value, sort_keys=True, separators=(",", ":")),
    )


def score_commands(
    predicted: Optional[Dict[str, Any]],
    expected: Dict[str, Any],
    allowed_entities: Iterable[str],
) -> Dict[str, Any]:
    predicted_commands = [] if not isinstance(predicted, dict) else predicted.get("commands", [])
    if not isinstance(predicted_commands, list):
        predicted_commands = []
    expected_commands = expected.get("commands", [])

    predicted_counter = Counter(canonical_command(item) for item in predicted_commands if isinstance(item, dict))
    expected_counter = Counter(canonical_command(item) for item in expected_commands if isinstance(item, dict))
    extra = predicted_counter - expected_counter
    missing = expected_counter - predicted_counter
    allowed = set(allowed_entities)
    unsupported = sum(
        1
        for command in predicted_commands
        if not isinstance(command, dict) or command.get("entity_id") not in allowed
    )
    unsupported_actions = sum(
        1
        for command in predicted_commands
        if isinstance(command, dict)
        and command.get("entity_id") in allowed
        and PHYSICAL_ACTIONS_BY_ENTITY.get(command.get("entity_id")) is not None
        and command.get("action")
        not in PHYSICAL_ACTIONS_BY_ENTITY[command.get("entity_id")]
    )
    expected_noop = not expected_commands
    predicted_noop = not predicted_commands
    return {
        "exact_match": predicted_counter == expected_counter,
        "ordered_match": [canonical_command(item) for item in predicted_commands if isinstance(item, dict)]
        == [canonical_command(item) for item in expected_commands if isinstance(item, dict)],
        "extra_command_count": sum(extra.values()),
        "missing_command_count": sum(missing.values()),
        "unsupported_entity_count": unsupported,
        "unsupported_action_count": unsupported_actions,
        "expected_noop": expected_noop,
        "noop_correct": predicted_noop if expected_noop else None,
        "intent_match": (
            predicted.get("intent") == expected.get("intent")
            if isinstance(predicted, dict) and "intent" in expected
            else None
        ),
    }


def schema_is_valid(parsed: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(parsed, dict):
        return False
    try:
        _validate_or_raise(parsed)
    except Exception:
        return False
    return True


async def run_condition(
    condition: str,
    text: str,
    context: Dict[str, Any],
    allowed_entities: set[str],
) -> Dict[str, Any]:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")

    started = perf_counter()
    trace: Dict[str, Any] = {}
    error = None
    parsed: Optional[Dict[str, Any]] = None
    raw_output = None

    try:
        if condition in {"llm_only", "llm_context"}:
            supplied_context = context if condition == "llm_context" else None
            user_content = _build_llm_user_content(text, allowed_entities, supplied_context)
            parsed, raw_output = await _parse_with_ollama(user_content)
        elif condition == "full_pipeline":
            parsed, _, trace = await parse_command(text, allowed_entities, context)
            raw_output = trace.get("raw_model_output")
        else:
            parsed = _fallback_parse(text)
            parsed = _normalize_parsed_command(text, parsed, context, allowed_entities)
            parsed = _apply_context_policy(parsed, context)
            parsed = _restrict_to_supported_entities(parsed, allowed_entities)
            _validate_or_raise(parsed)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    return {
        "condition": condition,
        "parsed": parsed,
        "raw_model_output": raw_output,
        "trace": trace,
        "schema_valid": schema_is_valid(parsed),
        "error": error,
        "latency_ms": round((perf_counter() - started) * 1000, 3),
    }


async def run_full_pipeline_timed(
    text: str, context: Dict[str, Any], allowed_entities: set[str]
) -> Dict[str, Any]:
    user_content = _build_llm_user_content(text, allowed_entities, context)
    total_started = perf_counter()
    llm_started = perf_counter()
    parsed, raw_output = await _parse_with_ollama(user_content)
    llm_ms = (perf_counter() - llm_started) * 1000

    post_started = perf_counter()
    normalized = _normalize_parsed_command(text, parsed, context, allowed_entities)
    policy_output = _apply_context_policy(normalized, context)
    final = _restrict_to_supported_entities(policy_output, allowed_entities)
    _validate_or_raise(final)
    post_ms = (perf_counter() - post_started) * 1000
    total_ms = (perf_counter() - total_started) * 1000
    return {
        "parsed": final,
        "raw_model_output": raw_output,
        "llm_ms": round(llm_ms, 3),
        "postprocess_ms": round(post_ms, 3),
        "planning_total_ms": round(total_ms, 3),
    }


async def model_metadata() -> Dict[str, Any]:
    result = {"model": OLLAMA_MODEL, "digest": None, "ollama_url": OLLAMA_URL}
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            for model in response.json().get("models", []):
                names = {model.get("name"), model.get("model")}
                if OLLAMA_MODEL in names:
                    result["digest"] = model.get("digest")
                    break
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def git_commit() -> str:
    return _run([_git_binary(), "rev-parse", "HEAD"], cwd=ROOT).strip()


def base_metadata(
    condition: str,
    repetition: int,
    model: Dict[str, Any],
    repetition_count: int = 1,
) -> Dict[str, Any]:
    return {
        "timestamp_utc": utc_now(),
        "git_commit": git_commit(),
        "model": model.get("model"),
        "model_digest": model.get("digest"),
        "model_used": condition != "rules_only",
        "temperature": TEMPERATURE,
        "condition": condition,
        "repetition_index": repetition,
        "repetition_count": repetition_count,
    }


def require_model_available(model: Dict[str, Any]) -> None:
    if model.get("digest"):
        return
    detail = model.get("error") or "configured model was not returned by /api/tags"
    raise RuntimeError(
        f"Ollama model {OLLAMA_MODEL!r} is not ready: {detail}. "
        "Start Ollama and verify the model before an LLM experiment."
    )


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def collect_environment() -> Dict[str, Any]:
    packages = {}
    for name in PACKAGE_NAMES:
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None

    hardware = _mac_hardware()
    return {
        "collected_at_utc": utc_now(),
        "git_commit": git_commit(),
        "platform": platform.platform(),
        "macos_version": _run(["sw_vers", "-productVersion"]).strip(),
        "python_version": platform.python_version(),
        "python_executable_name": Path(sys.executable).name,
        "hardware": hardware,
        "ollama_client": _run(["ollama", "--version"], allow_error=True).strip(),
        "model": OLLAMA_MODEL,
        "temperature": TEMPERATURE,
        "packages": packages,
        "pip_freeze": _run_package_freeze(),
    }


def _mac_hardware() -> Dict[str, Any]:
    output = _run(["system_profiler", "SPHardwareDataType", "-json"], allow_error=True)
    try:
        payload = json.loads(output)
        item = payload.get("SPHardwareDataType", [{}])[0]
    except (json.JSONDecodeError, IndexError, TypeError):
        return {"error": "hardware profile unavailable"}
    return {
        "model_name": item.get("machine_name"),
        "model_identifier": item.get("machine_model"),
        "chip": item.get("chip_type"),
        "memory": item.get("physical_memory"),
    }


def _run_package_freeze() -> List[str]:
    output = _run(
        [sys.executable, "-m", "pip", "freeze"],
        allow_error=True,
    )
    return [line for line in output.splitlines() if line.strip()]


def _git_binary() -> str:
    candidate = Path("/Applications/Xcode.app/Contents/Developer/usr/bin/git")
    return str(candidate) if candidate.exists() else "git"


def _run(
    command: Sequence[str], cwd: Optional[Path] = None, allow_error: bool = False
) -> str:
    completed = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout or completed.stderr
    if completed.returncode and not allow_error:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}\n{output}")
    return output
