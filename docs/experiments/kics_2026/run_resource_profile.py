#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

try:
    from .eval_core import ROOT, git_commit, model_metadata, require_model_available, utc_now
except ImportError:  # Direct script execution.
    from eval_core import ROOT, git_commit, model_metadata, require_model_available, utc_now


FIELDS = (
    "timestamp_utc",
    "elapsed_seconds",
    "phase",
    "ollama_process_count",
    "ollama_rss_mb",
    "ollama_cpu_percent",
    "workload_process_count",
    "workload_rss_mb",
    "workload_cpu_percent",
    "monitored_rss_mb",
    "monitored_cpu_percent",
    "system_occupied_proxy_mb",
    "system_occupied_proxy_percent",
    "memory_pressure_free_percent",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile CPU and RSS during the fixed warm command-planning workload"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results" / "resource_v1",
    )
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--baseline-samples", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=6)
    parser.add_argument("--repetitions", type=int, default=30)
    args = parser.parse_args()
    if args.interval <= 0 or args.baseline_samples < 1:
        parser.error("interval must be > 0 and baseline-samples must be >= 1")
    if args.warmup < 0 or args.repetitions < 1:
        parser.error("warmup must be >= 0 and repetitions must be >= 1")
    try:
        run(args)
    except (FileExistsError, RuntimeError) as exc:
        parser.error(str(exc))


def run(args: argparse.Namespace) -> None:
    _require_empty_output(args.output_dir)
    model = asyncio.run(model_metadata())
    require_model_available(model)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _run_latency_subprocess(
        output_dir=args.output_dir / "prewarm",
        warmup=0,
        repetitions=1,
        case_id="C02",
    )

    started = time.perf_counter()
    samples: List[Dict[str, Any]] = []
    for _ in range(args.baseline_samples):
        samples.append(_sample("loaded_idle_baseline", started, workload_root_pid=None))
        time.sleep(args.interval)

    workload_dir = args.output_dir / "workload"
    command = _latency_command(workload_dir, args.warmup, args.repetitions)
    workload = subprocess.Popen(
        command,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    while workload.poll() is None:
        samples.append(_sample("workload", started, workload_root_pid=workload.pid))
        time.sleep(args.interval)
    output, _ = workload.communicate()
    (args.output_dir / "workload.log").write_text(output, encoding="utf-8")
    if workload.returncode:
        raise RuntimeError(
            f"Resource workload failed with exit code {workload.returncode}; "
            f"see {args.output_dir / 'workload.log'}"
        )
    samples.append(_sample("post_workload", started, workload_root_pid=None))

    summary = summarize_samples(samples)
    summary.update(
        {
            "created_at_utc": utc_now(),
            "git_commit": git_commit(),
            "model": model.get("model"),
            "model_digest": model.get("digest"),
            "sample_interval_seconds": args.interval,
            "baseline_samples_requested": args.baseline_samples,
            "warmup_calls": args.warmup,
            "measured_calls": args.repetitions,
            "memory_semantics": (
                "Process RSS is a host-visible proxy and may omit or double-count shared "
                "CPU/GPU unified-memory pages. memory_pressure free percentage is the "
                "primary system-wide pressure indicator. System occupied proxy is total "
                "physical memory minus free and speculative pages and includes cache."
            ),
            "cpu_semantics": "100 percent represents one fully utilized logical CPU core.",
            "physical_actuation_included": False,
            "home_assistant_included": False,
        }
    )
    _write_csv(args.output_dir / "resource_samples.csv", samples)
    (args.output_dir / "resource_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


def summarize_samples(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    baseline = [sample for sample in samples if sample["phase"] == "loaded_idle_baseline"]
    workload = [sample for sample in samples if sample["phase"] == "workload"]
    if not baseline or not workload:
        raise ValueError("Both baseline and workload samples are required")
    baseline_system = statistics.median(
        sample["system_occupied_proxy_mb"] for sample in baseline
    )
    peak_system = max(sample["system_occupied_proxy_mb"] for sample in workload)
    return {
        "baseline_sample_count": len(baseline),
        "workload_sample_count": len(workload),
        "loaded_idle_ollama_rss_median_mb": _median(baseline, "ollama_rss_mb"),
        "workload_ollama_rss_mean_mb": _mean(workload, "ollama_rss_mb"),
        "workload_ollama_rss_peak_mb": _max(workload, "ollama_rss_mb"),
        "workload_python_rss_mean_mb": _mean(workload, "workload_rss_mb"),
        "workload_python_rss_peak_mb": _max(workload, "workload_rss_mb"),
        "workload_monitored_rss_mean_mb": _mean(workload, "monitored_rss_mb"),
        "workload_monitored_rss_peak_mb": _max(workload, "monitored_rss_mb"),
        "workload_monitored_cpu_mean_percent": _mean(workload, "monitored_cpu_percent"),
        "workload_monitored_cpu_p95_percent": _percentile(
            [sample["monitored_cpu_percent"] for sample in workload], 0.95
        ),
        "workload_monitored_cpu_peak_percent": _max(workload, "monitored_cpu_percent"),
        "loaded_idle_system_occupied_proxy_median_mb": round(baseline_system, 3),
        "workload_system_occupied_proxy_peak_mb": round(peak_system, 3),
        "workload_system_occupied_proxy_peak_delta_mb": round(
            peak_system - baseline_system, 3
        ),
        "loaded_idle_memory_pressure_free_median_percent": _median(
            baseline, "memory_pressure_free_percent"
        ),
        "workload_memory_pressure_free_min_percent": round(
            min(sample["memory_pressure_free_percent"] for sample in workload), 3
        ),
        "workload_memory_pressure_free_drop_percentage_points": round(
            _median(baseline, "memory_pressure_free_percent")
            - min(sample["memory_pressure_free_percent"] for sample in workload),
            3,
        ),
    }


def parse_process_rows(output: str) -> List[Dict[str, Any]]:
    rows = []
    for line in output.splitlines():
        parts = line.strip().split(None, 4)
        if len(parts) != 5:
            continue
        try:
            rows.append(
                {
                    "pid": int(parts[0]),
                    "ppid": int(parts[1]),
                    "rss_kb": int(parts[2]),
                    "cpu_percent": float(parts[3]),
                    "command": parts[4],
                }
            )
        except ValueError:
            continue
    return rows


def descendant_pids(rows: List[Dict[str, Any]], root_pid: int) -> Set[int]:
    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for row in rows:
            if row["ppid"] in descendants and row["pid"] not in descendants:
                descendants.add(row["pid"])
                changed = True
    return descendants


def _sample(
    phase: str, started: float, workload_root_pid: int | None
) -> Dict[str, Any]:
    process_output = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,rss=,%cpu=,command="],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    rows = parse_process_rows(process_output)
    ollama = [
        row
        for row in rows
        if "ollama serve" in row["command"] or "llama-server" in row["command"]
    ]
    workload_ids = (
        descendant_pids(rows, workload_root_pid) if workload_root_pid is not None else set()
    )
    workload = [row for row in rows if row["pid"] in workload_ids]
    memory = _system_memory_snapshot()
    ollama_rss = _rss_mb(ollama)
    workload_rss = _rss_mb(workload)
    ollama_cpu = _cpu(ollama)
    workload_cpu = _cpu(workload)
    return {
        "timestamp_utc": utc_now(),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "phase": phase,
        "ollama_process_count": len(ollama),
        "ollama_rss_mb": ollama_rss,
        "ollama_cpu_percent": ollama_cpu,
        "workload_process_count": len(workload),
        "workload_rss_mb": workload_rss,
        "workload_cpu_percent": workload_cpu,
        "monitored_rss_mb": round(ollama_rss + workload_rss, 3),
        "monitored_cpu_percent": round(ollama_cpu + workload_cpu, 3),
        **memory,
    }


def _system_memory_snapshot() -> Dict[str, float]:
    total_bytes = int(
        subprocess.run(
            ["sysctl", "-n", "hw.memsize"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    output = subprocess.run(
        ["vm_stat"], capture_output=True, text=True, check=True
    ).stdout
    page_match = re.search(r"page size of (\d+) bytes", output)
    if not page_match:
        raise RuntimeError("Could not determine vm_stat page size")
    page_size = int(page_match.group(1))
    values = {}
    for line in output.splitlines()[1:]:
        match = re.match(r"([^:]+):\s+([0-9.]+)", line)
        if match:
            values[match.group(1)] = int(match.group(2).replace(".", ""))
    free_pages = values.get("Pages free", 0)
    speculative_pages = values.get("Pages speculative", 0)
    occupied_bytes = max(
        0, total_bytes - (free_pages + speculative_pages) * page_size
    )
    pressure_output = subprocess.run(
        ["memory_pressure", "-Q"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    pressure_match = re.search(
        r"System-wide memory free percentage:\s*([0-9.]+)%", pressure_output
    )
    if not pressure_match:
        raise RuntimeError("Could not parse memory_pressure free percentage")
    return {
        "system_occupied_proxy_mb": round(occupied_bytes / 1024 / 1024, 3),
        "system_occupied_proxy_percent": round(occupied_bytes / total_bytes * 100, 3),
        "memory_pressure_free_percent": float(pressure_match.group(1)),
    }


def _latency_command(
    output_dir: Path,
    warmup: int,
    repetitions: int,
    case_id: str | None = None,
) -> List[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve().parent / "run_latency.py"),
        "--warmup",
        str(warmup),
        "--repetitions",
        str(repetitions),
        "--output-dir",
        str(output_dir),
    ]
    if case_id:
        command.extend(["--case", case_id])
    return command


def _run_latency_subprocess(
    output_dir: Path,
    warmup: int,
    repetitions: int,
    case_id: str | None = None,
) -> None:
    completed = subprocess.run(
        _latency_command(output_dir, warmup, repetitions, case_id=case_id),
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"Prewarm failed with exit code {completed.returncode}:\n"
            f"{completed.stdout}{completed.stderr}"
        )


def _require_empty_output(output_dir: Path) -> None:
    protected = (
        output_dir / "resource_samples.csv",
        output_dir / "resource_summary.json",
        output_dir / "workload.log",
        output_dir / "workload" / "latency.csv",
    )
    existing = [str(path) for path in protected if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite an existing resource profile: " + ", ".join(existing)
        )


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _rss_mb(rows: Iterable[Dict[str, Any]]) -> float:
    return round(sum(row["rss_kb"] for row in rows) / 1024, 3)


def _cpu(rows: Iterable[Dict[str, Any]]) -> float:
    return round(sum(row["cpu_percent"] for row in rows), 3)


def _mean(rows: List[Dict[str, Any]], field: str) -> float:
    return round(statistics.fmean(row[field] for row in rows), 3)


def _median(rows: List[Dict[str, Any]], field: str) -> float:
    return round(statistics.median(row[field] for row in rows), 3)


def _max(rows: List[Dict[str, Any]], field: str) -> float:
    return round(max(row[field] for row in rows), 3)


def _percentile(values: List[float], quantile: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * quantile + 0.999999)))
    return round(ordered[index], 3)


if __name__ == "__main__":
    main()
