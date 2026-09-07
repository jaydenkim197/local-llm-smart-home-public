# ADR-001: Local AI Runtime

## Status

Accepted

## Context

The project needs English voice and text commands to work on a MacBook Air M1 with 8 GB memory. The first development stage also needed to run without smart-home hardware.

## Decision

Use the following local runtime during development:

- LLM: Ollama with `llama3.2:3b`
- STT: `faster-whisper` with `tiny.en`
- API server: FastAPI
- Command format: validated JSON
- Initial device target: virtual device simulator

## Rationale

- The model sizes are practical for the available development machine.
- Local execution keeps voice and control requests on the device during prototyping.
- JSON separates natural-language interpretation from device-specific hardware control.
- The virtual simulator allows command logic and UI work to be verified before device delivery and pairing.

## Consequences

- The project must handle Ollama or STT startup failures and expose them clearly in the UI.
- Model output needs schema validation and deterministic normalization for critical routines.
- Hardware adapters can be added without changing the LLM prompt or command schema where existing actions are sufficient.

## Alternatives Considered

### Cloud LLM and cloud STT

Not selected for the prototype because the project goal is local AI execution and its operation would depend on external network services.

### Larger local models

Not selected as the default because latency and memory use are less suitable for an M1 MacBook Air with 8 GB memory.
