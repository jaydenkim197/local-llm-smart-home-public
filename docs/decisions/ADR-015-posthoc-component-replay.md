# ADR-015: Post-hoc Replay for Component Attribution

Date: 2026-10-02

## Context

The submitted KICS evaluation compared four complete conditions, but did not
separately attribute the contribution of each deterministic post-processing
stage. The original full-pipeline LLM outputs and final plans for the frozen
40-case and prospective 20-case sets are preserved locally.

## Decision

Use the preserved first-run LLM output as the fixed input for a separate,
post-submission analysis. Replay the production normalization, context policy,
physical allow-list, and schema validation functions in order, then repeat with
one function omitted. Require exact reproduction of every preserved final plan
and score before accepting any component result. Keep raw files private and
Git-ignored; publish only the method, aggregate, source hashes, and analysis code.

Report schema validity separately from command exact match. A schema check is a
gate, not a command transformation, and an invalid plan is not operationally
successful even when its command multiset happens to match gold.

## Alternatives

- Re-run the LLM under new prompts or model settings: rejected for this analysis
  because it would change the model proposal and confound post-processing effects.
  It could be a separate, versioned experiment.
- Treat the saved trace's final score as proof of each component's contribution:
  rejected because the intermediate counterfactual outputs were not saved.

## Consequences

- No new LLM calls, simulated device calls, or physical actuation are required.
- Stage effects are conditional on the full-pipeline prompt, contexts, and fixed
  model outputs. The analysis cannot estimate the effect of omitting context from
  the LLM prompt or claim a new prospective result.
- The analysis is explicitly post-hoc and cannot be described as part of the
  previously submitted experiment without identifying its later provenance.
