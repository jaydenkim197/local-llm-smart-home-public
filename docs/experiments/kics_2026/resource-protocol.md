# KICS 2026 macOS Resource Profile Protocol

## Scope

This experiment profiles the local command-planning workload on the deployed
MacBook Air M1 with 8 GB unified memory. It measures software resource use only and
does not contact Home Assistant or actuate devices.

## Fixed Workload

- Model: `llama3.2:3b`
- Cases: C02, C10, C11, C13, C22, C35
- Model preload: one call before baseline sampling
- Loaded-idle baseline: 10 samples
- Sampling interval: 0.5 seconds
- Workload warm-up: 6 calls
- Measured workload: 30 round-robin calls

## Metrics

- Ollama/llama-server RSS mean and peak
- Python workload RSS mean and peak
- Combined monitored RSS mean and peak
- Combined monitored CPU mean, p95, and peak
- Loaded-idle and workload `memory_pressure` free percentage
- Loaded-idle and workload system occupied-memory proxy as supporting evidence
- Warm command-planning latency from the nested latency run

On macOS, summed process RSS is not exact unified-memory allocation. Shared pages and
GPU-backed pages may be omitted or counted differently. The system occupied-memory
proxy is physical memory minus free and speculative VM pages; it can include unrelated
host activity and reclaimable cache. Apple's `memory_pressure -Q` free percentage is
the primary system-wide pressure indicator. All are reported with these limitations.

## Execution

Commit and push this protocol before the first run. Then start Ollama and execute:

```bash
.venv/bin/python docs/experiments/kics_2026/run_resource_profile.py \
  --output-dir docs/experiments/kics_2026/results/resource_v1
```

The profiler refuses to overwrite an existing result. Preserve the first CSV, JSON,
workload log, and nested latency files by hash.
