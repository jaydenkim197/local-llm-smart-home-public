#!/usr/bin/env python3
from __future__ import annotations

try:
    from .stt_eval_core import expanded_cases, load_stt_dataset
except ImportError:  # Direct script execution.
    from stt_eval_core import expanded_cases, load_stt_dataset


def main() -> None:
    dataset = load_stt_dataset()
    cases = expanded_cases(dataset)
    action_count = sum(bool(case["source"]["expected"]["commands"]) for case in cases)
    print(f"dataset: {dataset['dataset_id']}")
    print(f"status: {dataset['status']}")
    print(f"cases: {len(cases)}")
    print(f"takes per case: {dataset['takes_per_case']}")
    print(f"expected recordings: {len(cases) * dataset['takes_per_case']}")
    print(f"action-required source cases: {action_count}")
    print(f"no-op source cases: {len(cases) - action_count}")


if __name__ == "__main__":
    main()
