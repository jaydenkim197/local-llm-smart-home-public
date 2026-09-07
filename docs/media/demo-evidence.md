# Demo Media Catalog

## Repository Assets

### `docs/assets/demo/context-aware-dashboard.png`

- Source: frame from the final 2026-09-06 screen recording
- Shows: live indoor context, solar/window context, Open-Meteo context, local model status, and command result
- Recommended caption: `Context-aware control dashboard combining Aqara sensor state, solar data, weather data, local STT, and local LLM output.`

### `docs/assets/demo/physical-living-room.jpg`

- Source: public JPEG conversion of `IMG_1953.HEIC`
- Shows: the living-room installation with the curtain open, TV, and air conditioner visible
- Recommended caption: `Physical test environment with the Aqara-controlled living-room curtain and IR-controlled air conditioner.`
- Privacy: the converted JPEG does not retain the source GPS metadata

### `docs/assets/demo/physical-curtain-controller-left.jpg`

- Source: public JPEG conversion of `IMG_1954.HEIC`
- Shows: one Aqara curtain controller installed in the recessed ceiling rail
- Recommended caption: `Aqara curtain controller installed on the living-room curtain rail.`
- Privacy: the converted JPEG does not retain the source GPS metadata

### `docs/assets/demo/physical-curtain-controller-right.jpg`

- Source: public JPEG conversion of `IMG_1955.HEIC`
- Shows: the second Aqara curtain controller and the opposite side of the rail
- Recommended caption: `Second Aqara curtain controller used for the paired curtain installation.`
- Privacy: the converted JPEG does not retain the source GPS metadata

## Local Raw Recording

### `artifacts/demo/final-physical-acceptance-2026-09-06.mov`

- Original source: `Screen Recording 2026-09-06 at 15.10.14.mov`
- Duration: 153.86 seconds
- Resolution: 2880 x 1800
- Codec: H.264
- Size: 25,469,001 bytes
- Git status: intentionally ignored to avoid adding a large binary to repository history
- Content: live dashboard, microphone interaction, context display, and command results

Before public upload, trim portions that show the ChatGPT project page and consider cropping the browser profile area. The recording does not display Home Assistant tokens or `.env` secrets in the sampled frames.

### `artifacts/demo/raw/physical-demo-short-original.mov`

- Original source: `IMG_1956.MOV`
- Duration: 13.715 seconds
- Resolution: 1920 x 1080
- Codecs: HEVC, AAC, timed metadata
- Size: 22,933,912 bytes
- Content: physical test environment, curtain/window area, wall control, and MacBook dashboard
- Git status: local original, intentionally ignored

### `artifacts/demo/raw/physical-demo-full-original.mov`

- Original source: `IMG_1957.MOV`
- Duration: 73.738 seconds
- Resolution: 1920 x 1080
- Codecs: HEVC, AAC, timed metadata
- Size: 122,894,232 bytes
- Content: MacBook dashboard and microphone interaction followed by the living-room curtain view
- Git status: local original, intentionally ignored

The two phone videos are the stronger physical evidence because they connect the software dashboard to the installed environment. Review their audio and trim inactive portions before publishing.

## Local Photo Originals

The original HEIC files are retained under `artifacts/demo/raw/`. They contain location metadata and therefore must not be committed or published directly. The repository JPEG derivatives contain no indexed latitude or longitude metadata.

## Excluded Desktop Captures

- `Screenshot 2026-08-21 at 19.34.06.png`: unrelated YouTube page
- `Screenshot 2026-08-24 at 21.30.31.png`: unrelated employment PDF with personal browsing context

These files were inspected but were not copied into the project.

The UTM configuration screenshot is also excluded from the public repository because it displays local network identifiers. A verified copy remains available locally as `artifacts/demo/raw/home-assistant-utm-original.png` for a later private report.
