#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable

try:
    from .eval_core import DATASET_PATH, EXPERIMENT_DIR, context_for, load_dataset
except ImportError:  # Direct script execution.
    from eval_core import DATASET_PATH, EXPERIMENT_DIR, context_for, load_dataset


REVIEW_FOCUS = {
    "C10": (
        "The deployed IR integration supports only Cool 24 C and Off. An arbitrary "
        "setpoint is therefore a no-op with the unsupported intent."
    ),
    "C15": (
        "The utterance is intentionally ambiguous. The hot synthetic context makes "
        "curtain close plus the fixed cooling preset the expected plan."
    ),
    "C29": (
        "Movie mode is projected onto the deployed physical scope. TV and light "
        "commands are excluded, leaving only curtain close."
    ),
    "C30": (
        "Away mode is projected onto the deployed physical scope: close the curtain "
        "and send the one-way AC Off scene."
    ),
    "C31": (
        "Whole-home on is projected onto the two deployed actuators: open the curtain "
        "and send the Cool 24 C scene. It is an explicit global command, so the cooling "
        "action does not require a hot-room context. The synthetic curtain is closed, "
        "so open_cover is not redundant."
    ),
    "C32": (
        "Whole-home off is projected onto the two deployed actuators: close the curtain "
        "and send the AC Off scene."
    ),
    "C39": (
        "The request depends on current temperature. With context unavailable, the "
        "fail-closed policy emits no command and uses context_unavailable."
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the draft gold dataset for human review")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--expected-cases", type=int, default=40)
    parser.add_argument(
        "--output",
        type=Path,
        default=EXPERIMENT_DIR / "case-review.md",
    )
    args = parser.parse_args()

    dataset = load_dataset(args.dataset, expected_case_count=args.expected_cases)
    cases = dataset["cases"]
    action_count = sum(bool(case["expected"]["commands"]) for case in cases)
    noop_count = len(cases) - action_count
    lines = [
        "# KICS 2026 Gold Dataset Review",
        "",
        "> Dataset-only rendering. No model inference or experiment result is included.",
        "",
        f"- Status: `{dataset['status']}`",
        f"- Frozen: `{str(dataset['frozen']).lower()}`",
        f"- Cases: {len(cases)}",
        f"- Action required: {action_count}",
        f"- No-op: {noop_count}",
        "",
        f"The source of truth is `{args.dataset.name}`. Context values below are synthetic evaluation inputs.",
        "",
        "| ID | Category | Utterance | Synthetic Home Context | Expected intent | Expected commands |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        context = context_for(dataset, case)
        lines.append(
            "| {id} | {category} | {utterance} | {context} | `{intent}` | {commands} |".format(
                id=case["id"],
                category=_escape(case["category"]),
                utterance=_escape(case["utterance"]),
                context=_escape(_format_context(case["context_id"], context)),
                intent=_escape(case["expected"]["intent"]),
                commands=_format_commands(case["expected"]["commands"]),
            )
        )

    by_id = {case["id"]: case for case in cases}
    focus_ids = [case_id for case_id in REVIEW_FOCUS if case_id in by_id]
    if focus_ids:
        lines.extend(["", "## Focus Cases", ""])
    for case_id in focus_ids:
        case = by_id[case_id]
        context = context_for(dataset, case)
        lines.extend(
            [
                f"### {case_id}",
                "",
                f"- Utterance: {case['utterance']}",
                f"- Context: {_format_context(case['context_id'], context)}",
                f"- Expected intent: `{case['expected']['intent']}`",
                f"- Expected commands: {_format_commands(case['expected']['commands'])}",
                f"- Dataset rationale: {case['rationale']}",
                f"- Review focus: {REVIEW_FOCUS[case_id]}",
                "",
            ]
        )

    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(args.output)


def _format_context(context_id: str, context: Dict[str, Any]) -> str:
    if context.get("source") == "unavailable":
        return f"{context_id}: unavailable"
    room = context["living_room"]
    curtain = room["curtain"]
    derived = ", ".join(
        name for name, enabled in context.get("derived", {}).items() if enabled
    ) or "none"
    return (
        f"{context_id}: {room['temperature_c']} C, {room['humidity_percent']}% RH, "
        f"{room['illuminance_lux']} lux, curtain {curtain['state']} "
        f"({curtain['position']}%), derived={derived}"
    )


def _format_commands(commands: Iterable[Dict[str, Any]]) -> str:
    values = []
    for command in commands:
        value = f"={command['value']}" if "value" in command else ""
        values.append(f"`{command['entity_id']}:{command['action']}{value}`")
    return "<none>" if not values else "<br>".join(values)


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
