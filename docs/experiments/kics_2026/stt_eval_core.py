from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from .eval_core import DATASET_PATH, dataset_sha256, load_dataset
except ImportError:  # Direct script execution.
    from eval_core import DATASET_PATH, dataset_sha256, load_dataset


EXPERIMENT_DIR = Path(__file__).resolve().parent
STT_DATASET_PATH = EXPERIMENT_DIR / "stt_cases.json"
DEFAULT_AUDIO_DIR = EXPERIMENT_DIR.parents[2] / "data" / "kics_2026_stt"
AUDIO_EXTENSION = ".webm"
SUPPORTED_AUDIO_EXTENSIONS = (".webm", ".m4a")


def load_stt_dataset(path: Path = STT_DATASET_PATH) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        dataset = json.load(handle)
    validate_stt_dataset(dataset)
    return dataset


def validate_stt_dataset(dataset: Dict[str, Any]) -> None:
    if dataset.get("status") != "frozen_before_recording" or dataset.get("frozen") is not True:
        raise ValueError("STT dataset must be frozen before recording")
    if dataset.get("language") != "en":
        raise ValueError("STT evaluation language must be English")
    if dataset.get("takes_per_case") != 3:
        raise ValueError("STT evaluation requires exactly three takes per case")

    source = load_dataset(DATASET_PATH, expected_case_count=40)
    if dataset.get("source_dataset") != source.get("dataset_id"):
        raise ValueError("STT source dataset id does not match cases.json")
    if dataset.get("source_dataset_sha256") != dataset_sha256(DATASET_PATH):
        raise ValueError("STT source dataset hash does not match cases.json")

    cases = dataset.get("cases")
    if not isinstance(cases, list) or len(cases) != 12:
        raise ValueError("STT dataset must contain exactly 12 cases")
    source_by_id = {case["id"]: case for case in source["cases"]}
    ids = [case.get("id") for case in cases]
    source_ids = [case.get("source_case_id") for case in cases]
    if len(set(ids)) != len(ids) or any(not value for value in ids):
        raise ValueError("STT case ids must be unique and non-empty")
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("STT source cases must be unique")
    missing = [case_id for case_id in source_ids if case_id not in source_by_id]
    if missing:
        raise ValueError(f"Unknown source case ids: {missing}")


def expanded_cases(dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    source = load_dataset(DATASET_PATH, expected_case_count=40)
    source_by_id = {case["id"]: case for case in source["cases"]}
    return [
        {**entry, "source": source_by_id[entry["source_case_id"]]}
        for entry in dataset["cases"]
    ]


def audio_path(audio_dir: Path, speaker_id: str, case_id: str, take: int) -> Path:
    base = audio_dir / speaker_id / f"{case_id}_take{take:02d}"
    existing = [Path(f"{base}{extension}") for extension in SUPPORTED_AUDIO_EXTENSIONS
                if Path(f"{base}{extension}").is_file()]
    if len(existing) > 1:
        raise ValueError(f"Multiple audio formats for {base.name}; keep one take")
    return existing[0] if existing else Path(f"{base}{AUDIO_EXTENSION}")


def normalize_transcript(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.lower())


def word_error_stats(reference: str, hypothesis: str) -> Dict[str, Any]:
    ref = normalize_transcript(reference)
    hyp = normalize_transcript(hypothesis)
    distance = _edit_distance(ref, hyp)
    return {
        "reference_words": len(ref),
        "word_errors": distance,
        "wer": distance / len(ref) if ref else 0.0,
        "transcript_exact": ref == hyp,
    }


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _edit_distance(reference: List[str], hypothesis: List[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for ref_index, ref_word in enumerate(reference, start=1):
        current = [ref_index]
        for hyp_index, hyp_word in enumerate(hypothesis, start=1):
            substitution = previous[hyp_index - 1] + (ref_word != hyp_word)
            insertion = current[hyp_index - 1] + 1
            deletion = previous[hyp_index] + 1
            current.append(min(substitution, insertion, deletion))
        previous = current
    return previous[-1]
