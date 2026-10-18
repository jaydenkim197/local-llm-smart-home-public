#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    from .eval_core import RESULTS_DIR, utc_now
except ImportError:  # Direct script execution.
    from eval_core import RESULTS_DIR, utc_now


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize measured command-evaluation CSV files")
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        default=[RESULTS_DIR / "command_eval.csv", RESULTS_DIR / "ablation.csv"],
    )
    parser.add_argument("--output", type=Path, default=RESULTS_DIR / "summary.md")
    args = parser.parse_args()

    rows = []
    for path in args.inputs:
        if not path.exists():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                row["_source"] = path.stem
                rows.append(row)
    if not rows:
        raise SystemExit("No measured result CSV files were found")

    groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        condition = row.get("stage") or row.get("condition") or "unknown"
        groups[f"{row['_source']}:{condition}"].append(row)

    lines = [
        "# KICS 2026 Experiment Summary",
        "",
        f"Generated at: {utc_now()}",
        "",
        "Fallback or transport-failed LLM rows are excluded from accuracy denominators",
        "and reported separately. Rules-only rows remain eligible without a model.",
        "",
        "| Condition / Stage | Slice | Rows | Eligible | Excluded / failed | Exact match | Schema valid | No-op correct | Extra | Missing | Unsupported entity | Unsupported action |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, group in sorted(groups.items()):
        for slice_name, sliced_rows in _slices(group):
            eligible = [row for row in sliced_rows if _is_eligible(row)]
            lines.append(
                "| {label} | {slice_name} | {rows} | {eligible} | {failed} | {exact} | {schema} | {noop} | {extra} | {missing} | {unsupported_entity} | {unsupported_action} |".format(
                    label=label,
                    slice_name=slice_name,
                    rows=len(sliced_rows),
                    eligible=len(eligible),
                    failed=len(sliced_rows) - len(eligible),
                    exact=_ratio(eligible, "exact_match"),
                    schema=_ratio(eligible, "schema_valid"),
                    noop=_ratio(eligible, "noop_correct"),
                    extra=_sum(eligible, "extra_command_count"),
                    missing=_sum(eligible, "missing_command_count"),
                    unsupported_entity=_sum(eligible, "unsupported_entity_count"),
                    unsupported_action=_sum(eligible, "unsupported_action_count"),
                )
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)


def _slices(rows: List[Dict[str, str]]) -> List[Tuple[str, List[Dict[str, str]]]]:
    slices = [
        ("overall", rows),
        ("action_required", [row for row in rows if _as_bool(row.get("expected_noop")) is False]),
        ("no_op", [row for row in rows if _as_bool(row.get("expected_noop")) is True]),
    ]
    categories = sorted({row.get("category", "") for row in rows if row.get("category")})
    slices.extend(
        (
            f"category:{category}",
            [row for row in rows if row.get("category") == category],
        )
        for category in categories
    )
    return [(name, values) for name, values in slices if values]


def _is_eligible(row: Dict[str, str]) -> bool:
    value = row.get("metric_eligible", "")
    return True if value == "" else _as_bool(value) is True


def _as_bool(value: object) -> object:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def _ratio(rows: Iterable[Dict[str, str]], field: str) -> str:
    values = [_as_bool(row.get(field)) for row in rows]
    measured = [value for value in values if isinstance(value, bool)]
    if not measured:
        return "n/a"
    passed = sum(value is True for value in measured)
    return f"{passed}/{len(measured)}"


def _sum(rows: Iterable[Dict[str, str]], field: str) -> str:
    values = []
    for row in rows:
        value = row.get(field, "")
        if value not in {"", None}:
            values.append(int(value))
    return str(sum(values)) if values else "n/a"


if __name__ == "__main__":
    main()
