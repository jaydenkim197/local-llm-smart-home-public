#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from eval_core import DATASET_PATH, load_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a KICS command dataset")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--expected-cases", type=int, default=40)
    args = parser.parse_args()
    dataset = load_dataset(args.dataset, expected_case_count=args.expected_cases)
    categories = Counter(case["category"] for case in dataset["cases"])
    noops = sum(not case["expected"]["commands"] for case in dataset["cases"])
    print(f"dataset: {dataset['dataset_id']}")
    print(f"path: {args.dataset}")
    print(f"status: {dataset['status']}")
    print(f"cases: {len(dataset['cases'])}")
    print(f"no-op gold cases: {noops}")
    print("categories:")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
