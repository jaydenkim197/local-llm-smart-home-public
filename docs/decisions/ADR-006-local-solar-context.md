# ADR-006: Local Solar Context

## Status

Accepted and implemented

## Context

Context-aware curtain decisions can benefit from sunrise, sunset, daylight state, and current sun position. Home Assistant already exposes `sun.sun`, but its configured location was observed to still use a default city coordinate rather than the actual home location. A remote sunrise API would add an unnecessary network dependency, while committing the exact home coordinates would expose private location data in the public repository.

Map inspection also showed that the apartment building has a multi-wing layout. The building address alone cannot establish the direction of a particular living-room window.

## Decision

- Use Astral 3.2 to calculate solar data locally from latitude, longitude, elevation, date, and timezone.
- Store actual coordinates only in ignored local `.env` values.
- Include sunrise, sunset, daylight state, current azimuth/elevation, next event, and minutes to that event in `HomeContext`.
- Store the user-measured southwest living-room window azimuth only in local `.env`.
- Calculate the sun-to-window angular difference and a simple `direct_sun_possible` context flag, without making it an autonomous trigger.
- Deterministically answer direct sunrise/sunset time questions from calculated context instead of trusting a small model to copy the correct field.

## Consequences

- Solar context works without internet access or an API key.
- Seasonal changes are recalculated automatically.
- Local horizon obstructions, neighboring buildings, terrain, and curtains are not modeled.
- The angle calculation does not account for neighboring buildings, curtains, glazing, or local horizon obstructions.
- Home Assistant's global location remains unchanged by this decision.
