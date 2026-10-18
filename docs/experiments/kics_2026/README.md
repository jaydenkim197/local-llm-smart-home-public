# KICS 2026 Evaluation Artifact

This public directory packages the reference datasets, evaluation code, and
reviewed results supporting the [KICS submission manuscript](../../papers/README.md).
It does not contain the private raw recordings or raw model-output archive.
See [source provenance and exclusions](../../public-release.md).

## Command Planning

| Condition | Requirements, 40 cases | Prospective expressions, 20 cases |
| --- | ---: | ---: |
| LLM Only | 8/40 (20.0%) | 6/20 (30.0%) |
| LLM + Context | 8/40 (20.0%) | 5/20 (25.0%) |
| Rules Only | 31/40 (77.5%) | 10/20 (50.0%) |
| Full Pipeline | 37/40 (92.5%) | 13/20 (65.0%) |

- [40-case frozen dataset](cases.json) and [gold review](case-review.md).
- [20-case frozen prospective dataset](heldout_cases.json) and [gold review](heldout-review.md).
- [Initial experiment and warm planning results](measured-results-2026-09-20.md).
- [Five-run repeatability results](stability-results-2026-09-20.md).
- [Prospective results and failure cases](heldout-results-2026-09-20.md).
- [Original evaluation decision](../../decisions/ADR-009-kics-command-evaluation-protocol.md).
- [Prospective freeze decision](../../decisions/ADR-010-prospective-generalization-evaluation.md).

Cases contain a user request, a fixed synthetic Home Context, and a frozen gold
command list. Exact match compares the duplicate-preserving multiset of
`(entity_id, action, value)` without regard to command order.
Both sets were developer-authored; the prospective set is not an independent
external benchmark. All five repeated runs reused the same 40 cases.

The raw LLM conditions share a model and physical actuator description but differ
in whether context is provided. Rules Only uses the fallback parser and the same
post-processing as Full Pipeline. Full Pipeline applies normalization, state
policy, device/action allow-list, and schema validation to context-informed LLM
output. See `eval_core.py` for the executable scoring and condition definitions.

If inference/parsing fails, fallback outputs are retained diagnostically and must
not be reported as successful LLM inference. Inspect failed/excluded row counts
as well as the eligible-row denominator before interpreting a new run.

## Voice, Field, and Resource Evidence

- [Frozen 12-prompt voice manifest](stt_cases.json), [protocol](stt-protocol.md),
  and [original one-speaker results](stt-results-2026-09-23.md).
- [Separate three-speaker results](multispeaker-stt-results-2026-09-26.md) and
  [recording audit](four-speaker-stt-audit-2026-09-26.md). The collection portal and
  private participants' recordings/mappings are intentionally omitted.
- [Physical trial manifest](physical_e2e_cases.json),
  [protocol](physical-e2e-protocol.md), and
  [results](physical-e2e-results-2026-09-25.md).
- [Live-context protocol](live-context-protocol.md) and
  [results](live-context-results-2026-09-25.md), distinguishing the original
  100-lux default from the separate 300-lux field profile.
- [Resource protocol](resource-protocol.md) and
  [resource results](resource-results-2026-09-23.md). Process RSS is not an exact
  measurement of Apple unified-memory allocation.
- [Consolidated Korean results and claim boundaries](paper-results-2026-09-23.ko.md).

The original 1-speaker and subsequent 3-speaker cohorts remain separate. Do not
infer a noise/microphone effect from the uncontrolled collection environments.
The curtain's 6/6 result concerns final Home Assistant state; IR reactions are
operator observations without authoritative bidirectional state feedback.

## Post-hoc Component Replay

[Analysis and interpretation limits](component-ablation-posthoc-2026-10-02.ko.md)
describe replaying the same stored LLM candidates through selected post-processing
stages. The analysis reproduced 40/40 and 20/20 preserved final plans and their
37/40 and 13/20 gold scores. These are different comparisons.

`analyze_component_ablation.py` requires two original raw JSONL files that are not
public. The code and reported hashes are provided, but the public repository alone
cannot reproduce this fixed-output analysis. It used no new LLM inference and
does not isolate independent causal component effects.

## Running Checks

From the repository root, with the application dependencies installed:

```bash
python -m unittest discover -s tests -v
python docs/experiments/kics_2026/validate_cases.py
python docs/experiments/kics_2026/validate_stt_cases.py
```

An offline rule-only harness check, not a paper result:

```bash
python docs/experiments/kics_2026/run_ablation.py --condition rules_only --case C02 --output-dir docs/experiments/kics_2026/results/public_smoke
```

Fresh command experiments require local Ollama and the intended model:

```bash
python docs/experiments/kics_2026/run_command_eval.py
python docs/experiments/kics_2026/run_ablation.py
python docs/experiments/kics_2026/run_latency.py --warmup 6 --repetitions 30
```

Review options with `--help` before running. The command-planning harness does not
apply commands to Home Assistant. In contrast, `run_physical_e2e.py` and
`run_live_context_e2e.py` can control configured devices and require their documented
explicit opt-in flags; they are not part of the offline checks above.
Voice evaluation requires private recordings and the STT model. Resource profiling
uses macOS process tools and is not a cross-platform memory benchmark.

Generated files belong under the ignored `results/` directory. A new run is a new
measurement, not permission to rewrite frozen labels or the historical reports.
