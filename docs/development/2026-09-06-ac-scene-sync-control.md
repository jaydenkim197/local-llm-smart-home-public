# Aqara IR AC Scene Sync Control

## Objective

Expose the existing Aqara Hub M3 IR air-conditioner control to the local LLM without pretending that a one-way IR command is a verified HVAC state.

## Work Completed

- Confirmed that Aqara Advanced Matter Bridging Scene Sync created two M3 child devices in Home Assistant: `AC Cool 24` and `AC Off`.
- Confirmed their HA entities are Matter outlet switches and are available for `switch.turn_on`.
- Added ignored local configuration for the two actual HA scene entity IDs; the application exposes logical `climate.air_conditioner` only when both are configured.
- Mapped logical `turn_on` to the Cool 24 C scene and logical `turn_off` to the Off scene.
- Added a physical-target precheck that rejects unavailable or non-switch scene mappings.
- Added normalized HomeContext metadata stating that AC control is scene-based and feedback is command-only.
- Added deterministic hot-room policy: when current indoor temperature is above the existing hot threshold, a request containing `too hot`, `cool down`, or `make it cooler` closes an open curtain and sends the Cool 24 C preset.
- Updated the web execution label to distinguish an accepted IR scene command from a state-confirmed curtain movement.
- Investigated the first live Cool 24 command after the user reported no physical response. Both virtual switches were `off`, but an explicit `AC Cool 24` `turn_off`, two-second delay, and `turn_on` sequence produced a fresh `on` edge. HA automatically returned the switch to `off` about five seconds later.
- The user observed that this reset-and-trigger sequence physically turned on the AC.
- Updated the adapter to perform `switch.turn_off`, a configurable one-second reset delay, and `switch.turn_on` for every AC preset request.
- Added deterministic wording for explicit AC on/off requests so the response says the IR preset was sent and never claims the physical AC state changed.
- Diagnosed the final browser microphone request from the retained browser trace instead of inferring from endpoint structure.
- Increased the Scene Sync reset delay from one second to the empirically successful two seconds.
- Generalized hot-room normalization for natural STT variants while still requiring live `is_hot=true` and the physical AC allow-list.
- Bumped the browser script cache version so command-only AC results display as unverified instead of using a stale state-confirmed label.

## Modified Files

- `.env` (ignored local entity configuration only)
- `.env.example`
- `app/config.py`
- `app/main.py`
- `services/home_assistant.py`
- `services/parser.py`
- `static/app.js`
- `tests/test_home_assistant.py`
- Documentation listed in this commit

## Test Evidence

- HA state and registry inspection found `switch.ac_cool_24` and `switch.ac_off`, both with Matter outlet device class and Aqara M3 as their parent bridge.
- Python unit suite passed 17 tests after implementation.
- Live `GET /api/health` reported Home Assistant reachable and AC scene control configured.
- Live `GET /api/context` reported indoor temperature 28.08 C, curtain closed, and command-only AC scene control metadata.
- A live request, `It is too hot in the living room. Make it comfortable.`, ran through local Ollama, FastAPI, Home Assistant, and `switch.ac_cool_24`. HA accepted `switch.turn_on` with no errors.
- The initial single `switch.turn_on` did not cause a physical AC response. A direct `turn_off` then `turn_on` experiment did, as observed by the user. The unit test now verifies the full reset-and-trigger sequence.
- The failed browser microphone request transcribed as `It is too hot in the living room, make it comfortable.` using `faster-whisper:tiny.en`.
- Its request-time context contained temperature 28.08 C, `is_hot=true`, and curtain state `open` at position 100.
- The raw LLM plan incorrectly proposed three living-room lights and `set_temperature=24`, but normalization replaced it with `close_cover` and logical AC `turn_on`; context policy did not change that plan.
- Final execution included both the curtain and `climate.air_conditioner`, with no reported HA error. HA history independently recorded `switch.ac_cool_24` changing to `on` at 05:19:27 UTC and automatically returning to `off` five seconds later.
- Therefore the failed physical result was not caused by STT, context, parsing, allow-list filtering, or a missing HA call. The remaining material difference from the successful direct experiment was the one-second versus two-second reset interval.
- Python unit suite passed 19 tests after adding cooling variants for `too hot`, plain `hot`, `really hot`, `make it cooler`, `make the room comfortable`, uppercase, and punctuation variation. The existing below-threshold suppression test also passed.
- The first post-fix microphone attempt captured only `It's...` and was safely suppressed. The second captured `It's hot here.`; this produced the AC command and the two-second reset-and-trigger execution. Because that exact Whisper variant initially relied on the LLM rather than deterministic normalization, `hot here` was added to the normalized variants before final acceptance.
- The second microphone request reached the Cool 24 virtual switch but the user observed no physical AC startup. The selected appliance-level sequence is now the actual `AC Off` Scene followed by the `AC Cool 24` Scene. This is distinct from resetting the Cool Scene's virtual switch state.
- Final ON acceptance used current temperature 28.08 C with `is_hot=true` and curtain already closed. The normalized text variant `It is hot here.` produced logical AC `turn_on`. HA history recorded the `AC Off` Scene turning on at 14:34:12 local time and `AC Cool 24` at 14:34:16. The user then observed the physical AC turn on.
- After that confirmation, the updated FastAPI path sent the standalone `AC Off` Scene with no HA error and command-only wording; physical shutdown observation remained pending at the time of this record.
- Final filmed acceptance confirmed physical AC OFF as well as the Off-Scene-then-Cool-Scene AC ON sequence. The user then repeated AC Off twice and AC On once, with correct physical responses throughout.

## Unresolved Issues

- The Scene Sync switch acknowledges the command but does not provide verified AC power, mode, or target-temperature feedback.
- No physical acceptance item remains for the demonstration MVP. IR state feedback remains unavailable by design.

## Next Step

Keep the completed demonstration path stable. Treat autonomous control and edge-device migration as separate future work.
