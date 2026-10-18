# KICS 2026 macOS Resource Profile Results

Date: 2026-09-23

## Reproducibility Record

- Input revision: `52e769d18d6602f7a97ecc491039d03eb05dece0`
- Host: MacBook Air M1, 8 GB unified memory
- Model: `llama3.2:3b`
- Model digest: `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
- Workload cases: C02, C10, C11, C13, C22, C35
- Model preload: one C02 call
- Loaded-idle baseline: 10 samples
- Sampling interval: 0.5 seconds
- Workload warm-up: 6 calls
- Measured calls: 30
- Workload samples: 196
- Home Assistant and physical actuation: excluded

The initial preload attempt found an empty per-case summary edge case in the existing
latency runner and produced no profile result. The preload was corrected to target
only C02, committed as the input revision above, and the first complete profile was
then preserved without further modification.

## Process Resource Results

| Metric | Result |
| --- | ---: |
| Loaded-idle Ollama RSS median | 2417.852 MB |
| Workload Ollama RSS mean | 2480.331 MB |
| Workload Ollama RSS peak | 2494.422 MB |
| Workload Python RSS mean | 24.504 MB |
| Workload Python RSS peak | 38.000 MB |
| Combined monitored RSS mean | 2504.835 MB |
| Combined monitored RSS peak | 2522.328 MB |
| Combined CPU mean | 18.021% |
| Combined CPU p95 | 55.200% |
| Combined CPU peak | 68.600% |

The process inventory contained two Ollama-related processes and one Python workload
process for all 196 workload samples. CPU percentages use the macOS `ps` convention:
100% represents one fully utilized logical CPU core. The M1 Metal workload is not a
CPU-only computation, and these values do not measure GPU utilization.

## System Memory Pressure

| Metric | Result |
| --- | ---: |
| Loaded-idle `memory_pressure` free median | 20% |
| Workload minimum free percentage | 17% |
| Worst drop from loaded-idle median | 3 percentage points |
| Loaded-idle occupied-memory proxy median | 8072.867 MB |
| Workload occupied-memory proxy peak | 8135.891 MB |
| Proxy peak increase | 63.024 MB |

Apple's `memory_pressure -Q` free percentage is the primary system-wide pressure
indicator. The occupied-memory proxy includes reclaimable cache and unrelated host
activity, so its absolute value must not be interpreted as application memory.

## Concurrent Warm Planning Latency

The nested fixed workload produced:

| Metric | Result |
| --- | ---: |
| Mean | 3007.444 ms |
| Median | 2754.406 ms |
| P95 | 4577.386 ms |

These values are consistent with the earlier warm planning measurement while resource
sampling was active. They exclude STT, Home Assistant context acquisition, network
transit, Matter, IR, and physical device settling.

## Interpretation Boundary

- Summed RSS is a host-visible process proxy, not exact Apple unified-memory
  allocation.
- Shared pages may be counted more than once, while GPU-backed allocations may not be
  represented fully in process RSS.
- CPU percentages do not include an equivalent GPU utilization metric.
- System memory pressure includes all host activity during the run.
- Energy and power were not measured.

The supported conclusion is that the fixed local command-planning workload completed
on the 8 GB M1 host while monitored process RSS peaked near 2.52 GB and the system's
reported free memory pressure did not fall below 17% during this run.

## Local Raw Evidence

| File | SHA-256 |
| --- | --- |
| `resource_samples.csv` | `5bf41db00b1d6ca7f3f6bc96b6e5a6c759bee7d1a4bdf114ab3a50aff6eb6ece` |
| `resource_summary.json` | `47a4f3af4cb3336d2c11ef504fc3be1c235d29071b230a1406360fc331d9bafe` |
| `workload.log` | `31a4b10c0003fff034e750f1030540c1cc57d08f578f7baa5d5afe9ffdf778cf` |
| `workload/latency.csv` | `97204badfc9f0bc3da3e36a3ff8eef9491e62c13ca4fa251fbb37a4725827ec7` |
| `workload/latency_runs.jsonl` | `3025469fd2493c8ad0443e510e6c3350d674f3a7bc725c4006afd5a68a052ddf` |
| `workload/latency_summary.csv` | `d168412897af3802754f65e53601ae6c80c07f529137988798a5f82abfd5836e` |
| `prewarm/latency.csv` | `2c347b36cbec5de5c0815811981c9492012d88f4f0f8593d5262d4ceda40fb58` |
| `prewarm/latency_runs.jsonl` | `b60863fff86473499824929872636599b60a0d3a795452a565c935f88d670cab` |
| `prewarm/latency_summary.csv` | `e1acfa019b2f95f1089ce3b415681fd4bab9491edc2c40ea8999f5155e5abf9c` |
