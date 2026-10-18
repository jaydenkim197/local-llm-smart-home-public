# KICS 2026 Initial Measured Results

Date: 2026-09-20

## Reproducibility Record

- Input revision: `d281c9e95af9880474e18a15a079fdc955a920a7`
- Dataset: `kics_2026_command_eval_v1`
- Dataset SHA-256: `80bc08ce34a6e280eecd60ecca0c2da354793013f8f53bca27f29f49e3dd6f86`
- Model: `llama3.2:3b`
- Model digest: `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
- Quantization: Q4_K_M
- Temperature: `0.0`
- Runtime: Ollama 0.31.1
- Host: MacBook Air M1, 8 GB memory, macOS 26.6.2
- Python: 3.9.6
- Cases: 40 total, 22 action-required, 18 no-op
- Repetitions: one command-evaluation pass per condition
- Fallback or transport failures: 0

The gold dataset was reviewed, frozen, committed, and pushed before these model calls.

## Command Planning Accuracy

Exact match compares the complete order-insensitive set of `(entity_id, action,
value)` commands against the frozen gold plan.

| Condition | Overall | Action required | No-op | Schema valid |
| --- | ---: | ---: | ---: | ---: |
| LLM Only | 8/40 (20.0%) | 5/22 (22.7%) | 3/18 (16.7%) | 39/40 (97.5%) |
| LLM + Context | 8/40 (20.0%) | 6/22 (27.3%) | 2/18 (11.1%) | 39/40 (97.5%) |
| Rules Only | 31/40 (77.5%) | 13/22 (59.1%) | 18/18 (100.0%) | 40/40 (100.0%) |
| Full Pipeline | 37/40 (92.5%) | 20/22 (90.9%) | 17/18 (94.4%) | 40/40 (100.0%) |

Adding Home Context to the raw 3B model improved one action-required case but did not
improve overall exact match. The large gain appeared only when context was combined
with deterministic normalization, context policy, schema validation, and the physical
entity/action allow-list. Rules Only was conservative and perfect on no-op cases, but
missed nine requested actions or scenes.

## Full Pipeline Errors

| Case | Frozen expectation | Measured final output | Interpretation |
| --- | --- | --- | --- |
| C03 | Stop the curtain | No-op | The model interpreted "freeze" as keeping the curtain open; redundant-state policy then removed the incorrect open command. |
| C09 | AC `turn_on` with no value | AC `turn_on` with value `Cool 24 C` | The physical action was correct, but exact match failed because the model added a value field not present in the canonical command. |
| C34 | Unsupported/no-op bedtime request | AC off plus curtain close | The model invented an undefined bedtime scene using valid physical actions. |

No production code or gold label was changed after observing these failures.

## Category Result For Full Pipeline

| Category | Exact match |
| --- | ---: |
| Context cooling | 8/8 |
| Context light | 6/6 |
| Context light boundary | 4/4 |
| Direct AC | 3/4 |
| Direct curtain | 5/6 |
| Scene and global | 5/6 |
| Unsupported and safety | 6/6 |

## Warm Software Command-Planning Latency

The latency run discarded six round-robin warm-up calls and measured 30 calls across
C02, C10, C11, C13, C22, and C35.

| Metric | Result |
| --- | ---: |
| Mean | 3215.826 ms |
| Median | 2923.703 ms |
| P95 | 4967.947 ms |

Per-case mean planning latency ranged from 2682.814 ms for C10 to 4910.226 ms for
C22. Deterministic post-processing generally took 5-14 ms; local LLM inference
dominated total planning time.

This is warm software command-planning latency only. It excludes STT, live Home
Assistant context acquisition, network transit, Matter, IR transmission, and physical
device settling.

## Local Raw Evidence

Raw outputs remain ignored by Git and are stored locally under `results/`. Their
SHA-256 hashes are recorded so the measured files can be checked without publishing
raw model traces by default.

| File | SHA-256 |
| --- | --- |
| `environment.json` | `9df02acb37694cbc697b81178ca4050b681c6c92d89313cb9e20e45e1c309aab` |
| `command_eval.csv` | `a6763b91a1f8bcab759f075e068e8f314ad6a38309ef5957aa090fe1ad22c5fd` |
| `raw_runs.jsonl` | `ba6e1e487b730644107290dee0b12bf2bd54c3dba1878c135502897cd45bad5a` |
| `ablation.csv` | `b8f045e1b5ae87cb55bc3cc50db6c7e07b0aabdd7720a0e1fec66c57b005c46d` |
| `ablation_runs.jsonl` | `49b3ebc90f33ad2e1a43f2a39065f0507a96c168c99d43d0efebcdeb9db8537a` |
| `latency.csv` | `a8a60b4b58cc3a1144c15dd888486a0da578769e012814e52cc291527f0c1f60` |
| `latency_summary.csv` | `875d9eac6ece8b6d2a053a709a1264c86b5a97ed1c92c56d65599e9903bde35a` |
| `latency_runs.jsonl` | `2c1cdbb5d926152698286d5535f4d674f9bba6dbfcc405db57526cc1e23268c1` |

## Limitations And Next Measurements

- Each accuracy condition currently has one measured pass. Repeated runs are needed
  before making a statistical stability claim.
- STT transcription accuracy and end-to-end voice-command success are not included.
- CPU and unified-memory use were not measured.
- Physical device latency is intentionally separate from this software measurement.
