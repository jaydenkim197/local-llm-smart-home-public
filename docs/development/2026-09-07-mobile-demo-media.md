# Mobile Demo Media Packaging

## Objective

Add the phone photos and physical demonstration videos to the existing evidence package without committing large media or source location metadata.

## Work Completed

- Inspected three HEIC photos and sampled both MOV files at multiple timestamps.
- Identified the photos as a living-room overview and close-ups of the two installed Aqara curtain controllers.
- Identified the videos as physical demonstration footage connecting the MacBook dashboard and the installed curtain environment.
- Copied all five originals into the local Git-ignored `artifacts/demo/raw/` directory with descriptive names.
- Converted the three HEIC photos to repository-ready JPEG files at 1600-pixel width.
- Verified that the converted JPEG files do not expose indexed latitude or longitude metadata.
- Rejected the first direct conversion after verification showed retained GPS metadata, then regenerated the public files from pixel-only intermediate images and verified the replacement paths reported no latitude or longitude.
- Added descriptions, captions, metadata, privacy notes, and publication guidance to the demo media catalog.
- Added the living-room installation image to the root README and final report.

## Modified Files

- `.gitignore`
- `README.md`
- `artifacts/demo/README.md`
- `docs/README.md`
- `docs/media/demo-evidence.md`
- `docs/reports/2026-09-06-mvp-final-report.ko.md`
- `docs/assets/demo/physical-living-room.jpg`
- `docs/assets/demo/physical-curtain-controller-left.jpg`
- `docs/assets/demo/physical-curtain-controller-right.jpg`
- `artifacts/demo/raw/*` (local, Git-ignored originals)

## Test Evidence

- Source metadata inspected with macOS `mdls` and `stat`.
- `IMG_1956.MOV`: 13.715 seconds, 1920 x 1080, HEVC/AAC, 22,933,912 bytes.
- `IMG_1957.MOV`: 73.738 seconds, 1920 x 1080, HEVC/AAC, 122,894,232 bytes.
- Video review frames sampled at 1, 7, and 12 seconds for `IMG_1956.MOV`, and 2, 20, 40, and 65 seconds for `IMG_1957.MOV`.
- Converted JPEG metadata reported no indexed latitude or longitude values.

## Unresolved Issues

- The videos remain unedited originals and may contain inactive footage or incidental background audio.
- Original HEIC files retain location metadata and must remain private.

## Next Step

Trim the two phone videos and the desktop recording only when a specific submission duration and format are known.
