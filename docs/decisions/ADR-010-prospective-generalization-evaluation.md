# ADR-010: Prospective Generalization Evaluation

## Status

Accepted on 2026-09-20 before the first held-out model execution.

## Context

The original 40-case dataset was frozen before model execution, but some production
policies were finalized during its pre-freeze review. Its result is valid as a
requirements-based system evaluation but should not be presented as a historically
untouched generalization benchmark.

## Decision

Use a new 20-case prospective set with production behavior locked to revision
`d281c9e95af9880474e18a15a079fdc955a920a7`. Review and freeze all utterances,
synthetic contexts, intents, and physical command plans before the first model call.
Do not modify production code, prompts, policies, or gold labels in response to its
result.

H04, "Switch on cooling," is a direct actuator request. In the deployed scope, the AC
is the only cooling actuator, so its logical command is `climate.air_conditioner`
`turn_on` and does not require a hot-temperature threshold. The current adapter maps
that logical action to the Aqara Cool 24 C IR scene. This implementation mapping does
not permanently define the natural-language meaning of cooling as a 24 C setpoint;
future adapters may expose richer mode and target-temperature capabilities.

H17, "Bring every supported device online," is accepted as an explicit whole-home-on
request under the reviewed project policy. Within the physical allow-list it opens
the curtain and sends the AC on command.

Evaluate the same four conditions as the original set. Use one inference to score the
paired LLM + Context and Full Pipeline stages, and separate calls for LLM Only. Rules
Only remains deterministic. Preserve the first result files without overwrite.

## Consequences

- The new result is a prospective generalization check for the unchanged system, not
  a claim about arbitrary homes, devices, speakers, or languages.
- Current Cool 24 C scene behavior remains an adapter capability constraint.
- A poor result is reported as measured; it cannot justify post-result tuning on this
  dataset.
- STT and physical-device validation remain separate evaluation stages.
