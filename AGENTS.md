# Project Working Rules

## Documentation

Document every meaningful development task as part of the task.

1. Add or update a dated record in `docs/development/` after implementation.
2. Record the objective, work completed, modified files, test evidence, unresolved issues, and next step.
3. Record only tests that were actually run and measurements that were actually observed.
4. When a technical or architectural choice is made, add or update an ADR in `docs/decisions/`.
5. When the current system structure changes, update `docs/architecture/`.
6. For hardware work, update `docs/hardware/` with the device model, connection method, configuration, and verification result.
7. Keep reusable failure symptoms and fixes in `docs/troubleshooting/`.
8. Keep experiment inputs, environment, metrics, and results in `docs/experiments/`.

## Source of Truth

- `docs/architecture/` describes the current implemented system.
- `docs/development/` preserves the chronological development record.
- `docs/decisions/` explains important choices and their alternatives.
