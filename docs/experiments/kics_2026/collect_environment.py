#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from eval_core import RESULTS_DIR, collect_environment, model_metadata


async def run(output: Path) -> None:
    payload = collect_environment()
    payload["ollama_model"] = await model_metadata()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect reproducible KICS experiment metadata")
    parser.add_argument(
        "--output",
        type=Path,
        default=RESULTS_DIR / "environment.json",
        help="JSON output path (default: ignored results directory)",
    )
    args = parser.parse_args()
    asyncio.run(run(args.output))


if __name__ == "__main__":
    main()
