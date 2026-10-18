# ADR-009: KICS Command Evaluation Protocol

## Status

Accepted. The 40-case gold dataset was reviewed and frozen before model results on
2026-09-17.

## Context

The project has functional regression tests and physical acceptance evidence, but it
does not yet have a fixed quantitative command-planning evaluation. Running the model
before the gold labels are fixed would allow the dataset to be adjusted to observed
outputs and would weaken the validity of the paper results.

## Decision

Use a 40-case English dataset under `docs/experiments/kics_2026/` and compare four
fixed conditions: LLM only, LLM with Home Context, Full Pipeline, and Rules Only.
All conditions use the same deployed curtain and IR AC actuator scope and the same
command scorer. Full Pipeline imports the production parser and policy stages rather
than copying their behavior.

LLM Only and LLM with Home Context use identical model settings, system prompt, and
physical actuator list. Their sole intended difference is whether the synthetic Home
Context is supplied. Full Pipeline adds production normalization, context policy,
entity/action allow-list enforcement, and schema validation. Rules Only replaces the
LLM with the deterministic fallback parser and retains those post-processing stages.

The primary metric is order-insensitive exact command match over entity, action, and
value. Extra, missing, unsupported, no-op, ordered-match, schema-validity, and intent
measures are retained for diagnosis. Raw model output and final commands are scored by
the same implementation.

Because 18 of 40 draft cases are gold no-ops, every condition is reported over the
complete set, the 22 action-required cases, the 18 no-op cases, and each category.
Fallback or transport-failed rows are recorded but excluded from LLM accuracy
denominators; a deterministic fallback must never be presented as an LLM result.

The dataset must be reviewed and committed before full model execution. Generated
results must record the input commit SHA, model name and digest, temperature, UTC
timestamp, condition, and repetition. Software latency is reported separately from
physical actuation latency.

Warm latency rotates through a fixed representative case set, discards warm-up calls,
and is labeled warm software command-planning latency. It excludes STT, live context
collection, network/device calls, and physical settling.

Whole-home ON is treated as an explicit user command, not a context-dependent comfort
request. It therefore does not require the hot-room threshold. In the deployed
physical scope it means opening a closed curtain and sending the AC Cool 24 C scene.
This preserves the system's pre-existing global-command specification; contextual
cooling remains temperature-gated and fails closed without Home Context.

## Consequences

- Existing application tests remain regression evidence and are not reported as model
  accuracy.
- Rules-only dry runs may validate the harness before dataset freeze, but are not paper
  results.
- STT, CPU/RAM, and physical repetition studies follow after command evaluation and
  ablation are complete.
- Changing a gold label after results exist requires a new dataset version and a clear
  reason; previous outputs must not be silently overwritten.
- Production safety defects may be corrected before dataset freeze. After freeze,
  changes made in response to evaluation scores are prohibited for this test set.
