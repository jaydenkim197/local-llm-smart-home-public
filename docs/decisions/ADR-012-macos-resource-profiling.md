# ADR-012: macOS Resource Profiling Semantics

## Status

Accepted on 2026-09-23 before the first resource-profile run.

## Context

The deployed experiment host is an 8 GB Apple M1 MacBook Air. CPU and GPU share
unified physical memory, while the local command path spans a Python process, the
Ollama daemon, and a separate llama-server process. A single Python RSS value would
therefore omit the model process, while summed RSS is not identical to total unified
memory because shared and GPU-backed pages may be counted differently.

## Decision

Profile the existing fixed warm command-planning workload with six warm-up calls and
30 measured calls. Preload the model, collect ten loaded-idle baseline samples, then
sample every 0.5 seconds throughout the workload.

Record the following separately:

- summed RSS and CPU percentage for Ollama plus llama-server;
- summed RSS and CPU percentage for the Python workload process tree;
- combined monitored-process RSS and CPU percentage;
- a system occupied-memory proxy derived from physical memory minus free and
  speculative VM pages;
- the system-wide free percentage reported by Apple's `memory_pressure -Q`.

Use memory-pressure free percentage as the primary system-wide pressure indicator;
the occupied-memory proxy is supporting evidence because macOS aggressively uses
reclaimable cache. Interpret 100 percent CPU as one fully utilized logical CPU core.
Describe RSS as a host-visible process proxy, not as exact model unified-memory
allocation. Do not use
the result to claim GPU-only memory, energy consumption, or physical actuation cost.

## Consequences

- The measurements are reproducible without administrator privileges.
- The system memory delta includes unrelated host activity and is supporting evidence
  only.
- Process RSS may omit GPU allocations or double-count shared pages.
- Energy and hardware power require a separately authorized tool such as
  `powermetrics` and remain outside this experiment.
