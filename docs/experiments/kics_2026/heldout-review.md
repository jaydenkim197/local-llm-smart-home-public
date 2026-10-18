# KICS 2026 Gold Dataset Review

> Dataset-only rendering. No model inference or experiment result is included.

- Status: `frozen_before_results`
- Frozen: `true`
- Cases: 20
- Action required: 13
- No-op: 7

The source of truth is `heldout_cases.json`. Context values below are synthetic evaluation inputs.

| ID | Category | Utterance | Synthetic Home Context | Expected intent | Expected commands |
| --- | --- | --- | --- | --- | --- |
| H01 | direct_curtain | Part the drapes in the lounge. | neutral_closed: 24.0 C, 50.0% RH, 400.0 lux, curtain closed (0%), derived=none | `curtain_control` | `cover.living_room_curtain:open_cover` |
| H02 | direct_curtain | Bring the lounge blinds down. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `curtain_control` | `cover.living_room_curtain:close_cover` |
| H03 | direct_curtain | Hold the curtain right there. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `curtain_control` | `cover.living_room_curtain:stop_cover` |
| H04 | direct_ac | Switch on cooling. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `air_conditioner_scene_control` | `climate.air_conditioner:turn_on` |
| H05 | direct_ac | Power down the aircon. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `air_conditioner_scene_control` | `climate.air_conditioner:turn_off` |
| H06 | direct_ac | Set the AC fan to high. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `unsupported` | <none> |
| H07 | context_cooling | This room is boiling. Do something about the heat. | hot_open: 29.5 C, 48.0% RH, 900.0 lux, curtain open (100%), derived=is_bright, is_hot | `reduce_heat` | `cover.living_room_curtain:close_cover`<br>`climate.air_conditioner:turn_on` |
| H08 | context_cooling | The heat in here is unbearable. Please deal with it. | hot_closed: 29.5 C, 48.0% RH, 900.0 lux, curtain closed (0%), derived=is_bright, is_hot | `reduce_heat` | `climate.air_conditioner:turn_on` |
| H09 | context_cooling | I am feeling warm in here. | cool_open: 26.0 C, 48.0% RH, 400.0 lux, curtain open (100%), derived=none | `context_no_action` | <none> |
| H10 | context_cooling | Make it pleasant in the living room. | unavailable: unavailable | `context_unavailable` | <none> |
| H11 | context_light | The room could use some sunlight. | dark_closed: 22.0 C, 50.0% RH, 80.0 lux, curtain closed (0%), derived=is_dark | `increase_natural_light` | `cover.living_room_curtain:open_cover` |
| H12 | context_light | The room could use some sunlight. | dark_open: 22.0 C, 50.0% RH, 80.0 lux, curtain open (100%), derived=is_dark | `context_no_action` | <none> |
| H13 | context_light | The sunlight is dazzling in here. | bright_open: 22.0 C, 50.0% RH, 950.0 lux, curtain open (100%), derived=is_bright | `reduce_natural_light` | `cover.living_room_curtain:close_cover` |
| H14 | context_light | The sunlight is dazzling in here. | lux_800_open: 22.0 C, 50.0% RH, 800.0 lux, curtain open (100%), derived=none | `context_no_action` | <none> |
| H15 | scene_and_global | We are about to watch a film. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `movie_mode` | `cover.living_room_curtain:close_cover` |
| H16 | scene_and_global | We are leaving the house for the night. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `away_mode` | `cover.living_room_curtain:close_cover`<br>`climate.air_conditioner:turn_off` |
| H17 | scene_and_global | Bring every supported device online. | neutral_closed: 24.0 C, 50.0% RH, 400.0 lux, curtain closed (0%), derived=none | `whole_home_on` | `cover.living_room_curtain:open_cover`<br>`climate.air_conditioner:turn_on` |
| H18 | scene_and_global | Turn off everything that is connected. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `whole_home_off` | `cover.living_room_curtain:close_cover`<br>`climate.air_conditioner:turn_off` |
| H19 | unsupported_and_safety | Open the garage door. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `unsupported` | <none> |
| H20 | unsupported_and_safety | Create a study mode and activate it now. | neutral_open: 24.0 C, 50.0% RH, 400.0 lux, curtain open (100%), derived=none | `unsupported` | <none> |