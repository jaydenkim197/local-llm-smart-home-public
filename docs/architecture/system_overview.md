# System Overview

## Purpose

The project combines an English text or voice request with the current home state, then produces validated smart-home commands. It retains a simulator and controls the Aqara curtain and M3 IR air conditioner scenes through Home Assistant.

## Current Control Flow

```text
English voice or text
        |
        +-- voice input --> faster-whisper (`tiny.en`)
        |
        v
FastAPI control server
        |
        +-- request-time Home Assistant state snapshot
        |       |
        |       v
        |   normalized HomeContext
        |   (indoor sensors, curtain, sun position, outdoor weather/radiation)
        |       |
        +-------+
        |
        v
Ollama local LLM (`llama3.2:3b`)
        |
        v
Validated JSON command
        |
        v
Command router
        |
        +-- Simulation: virtual device store and web dashboard
        +-- Physical: Home Assistant REST adapter
                         |
                         v
              Matter Server -> Aqara Hub M3 -> Aqara Zigbee devices
                                        -> Aqara IR AC scenes
```

## Current Software Components

| Component | Responsibility | Current implementation |
| --- | --- | --- |
| Web client | Text input, microphone recording, device state and trace display | `static/` |
| API server | Receives text/audio commands and selects the simulation or HA control backend | `app/main.py` |
| STT | Converts English audio to text | `services/stt.py`, faster-whisper `tiny.en` |
| LLM parser | Converts requests into validated command JSON | `services/parser.py`, Ollama `llama3.2:3b` |
| Device store | Simulates state changes and validates supported actions | `app/devices.py` |
| HA adapter | Maps approved logical commands to Home Assistant REST services and refreshes entity state | `services/home_assistant.py` |
| Home context | Normalizes vendor entity states and derives bounded conditions such as dark, bright, hot, and humid | `services/home_context.py` |
| Solar context | Calculates local sunrise, sunset, solar azimuth/elevation, and next event from private local coordinates | `services/solar.py`, Astral 3.2 |
| Outdoor context | Fetches and caches current weather, cloud cover, precipitation probability, wind, and radiation | `services/outdoor_context.py`, Open-Meteo |

## Virtual Devices Implemented

- Living room simulation: dimmable main light, two smart bulbs, curtain, temperature, humidity, illuminance, air purifier, robot cleaner, smart TV, air conditioner
- Bedrooms 1-4: one controllable main light per room

## Hardware Integration Principle

The LLM and command schema remain independent of a specific vendor or transport protocol. Physical integration is added after the command router through device-specific adapters. Each adapter translates a validated command into the device's actual control method and reports the resulting state or error.

## Current Boundary

Physical mappings are deliberately bounded. `cover.living_room_curtain` maps to `cover.aqara_curtain_controller` and allows only open, close, and stop actions. When both ignored local Scene Sync entity settings are present, `climate.air_conditioner` maps to Aqara's `AC Cool 24` and `AC Off` Matter switches. A logical AC-on request triggers the Off Scene first and the Cool 24 Scene second; AC-off triggers only the Off Scene. For each Scene, the adapter resets its virtual switch to off, waits two seconds, and turns it on to create the rising edge that runs the scene. These are one-way IR command scenes, so the adapter reports command acceptance rather than an AC state. Sensor mappings are read-only context. `CONTROL_BACKEND=simulation` remains the default and exposes only non-sensor virtual entities to the same parser and policy boundary. Setting `CONTROL_BACKEND=home_assistant` requires a Home Assistant long-lived access token and rejects commands targeting unmapped virtual devices. `scripts/run.sh` accepts `simulation` or `home_assistant` as an explicit backend argument after loading local configuration.

The current context implementation reads `/api/states` once per user request. The LLM receives only normalized logical fields and the physical actuator allow-list, not vendor-specific sensor entity IDs. A deterministic policy removes redundant curtain commands and resolves the initial dark/bright curtain use cases. Continuous WebSocket caching and autonomous control are explicitly deferred.

Solar values are calculated locally on every context build. The measured southwest living-room window azimuth is configured locally. Exact home coordinates and the measured azimuth are not committed. Outdoor context is fetched from Open-Meteo with a ten-minute cache and degrades to unavailable or stale data without blocking local control. The motion sensor is excluded from the current MVP and its entity is not sent to the LLM or displayed in the physical demo UI.

For hot-room requests, a deterministic policy requires a live indoor temperature above the hot threshold and physical AC-scene availability. It closes an open curtain first and then sends the Cool 24 C command. The policy deliberately avoids autonomously changing HVAC settings outside those fixed scenes.

Additional physical device models, communication protocols, credentials, and wiring details must be added to [Hardware Inventory](../hardware/inventory.md) before each device is integrated.
