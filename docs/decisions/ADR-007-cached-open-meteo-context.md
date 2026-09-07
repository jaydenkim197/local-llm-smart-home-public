# ADR-007: Cached Open-Meteo Context

## Status

Accepted and implemented

## Context

Indoor illuminance and astronomical sun position do not describe cloud cover or the amount of outdoor solar energy. Those values can help the local LLM explain ambiguous brightness requests, but a remote dependency must not prevent local curtain control.

## Decision

- Use Open-Meteo's forecast endpoint without an API key.
- Request current temperature, apparent temperature, precipitation probability, cloud cover, wind speed, shortwave radiation, direct radiation, and weather code.
- Use private coordinates from ignored local `.env` values and never include coordinates in normalized output.
- Cache successful responses for ten minutes.
- Return stale cached data or an unavailable marker when refresh fails.
- Keep outdoor values as LLM context only for the MVP; do not make them autonomous actuator triggers.

## Consequences

- The LLM receives richer outdoor context with one remote request at most every ten minutes.
- Local STT, LLM, Home Assistant, and curtain control continue when Open-Meteo is unavailable.
- Forecast and model values are context, not proof of conditions at the exact window.
