# 2026-10-19 Public KICS Artifact Preparation

## Objective

Keep the development repository private, strengthen the existing public repository,
feature the unchanged KICS submission paper, and put English and Korean three-line
what/how/why summaries at the top of its README.

## Work Completed

- Reused the original sanitized public repository rather than merging private history.
- Selected KICS source snapshot `0cdca36e0cdd408c9998fbdfa58e00ede841a784` and
  exported the runtime, relevant regression tests, evaluation code, frozen fixtures,
  aggregate reports, and methodological decisions.
- Retained previously sanitized network records and approved public photographs.
- Excluded operational participant collection deployments, private raw outputs,
  recordings, mapping/consent records, unfinished follow-up inputs and parser revisions.
- Added the supplied KICS PDF without editing it, preserving the printed author
  identity/contact and explicitly labeling it a submission manuscript.
- Added release provenance and reproduction limits. No repository-wide license
  grant was selected or inferred from public visibility.

## Modified Files

- `README.md`, `docs/README.md`, and `docs/public-release.md`.
- `docs/papers/README.md` and `docs/papers/KICS_2026_Undergraduate_Seokhyeon_Kim.pdf`.
- `docs/experiments/kics_2026/` and relevant decision records.
- Application/parser/adapter/configuration files and relevant tests from the snapshot.
- `.env.example` and `.gitignore`.
- `docs/decisions/ADR-019-public-kics-artifact.md`.

## Verification Observed

- Windows, Python 3.12.14; isolated test environment with the repository-pinned
  FastAPI 0.115.6, httpx 0.28.1, python-multipart 0.0.20, jsonschema 4.23.0,
  requests 2.32.5, and Astral 3.2. No STT package or model was needed for these checks.
- `python -m unittest discover -s tests -v`: 71 tests passed.
- `validate_cases.py`: frozen 40-case dataset validated, including 18 no-op labels.
- `validate_stt_cases.py`: 12 prompts and three takes validated, 36 expected files.
- Rule-only C02 harness smoke check: exact match, no processing error. This is
  only a harness check, not a new accuracy result.
- SHA-256 of both frozen command datasets and the voice manifest matched their
  recorded values. Their bytes were not reformatted.
- PDF SHA-256 matched the supplied submission file:
  `b5efae02604be9b9eb6c58b59aaada6ffe7d91b570e8dda0308917037997e8c1`.
  Both pages were extracted and visually reviewed. Metadata contains Word producer
  and creation/modification timestamps, with no embedded files or root action.
- The existing four public images contain no GPS IFD; their inspected EXIF fields
  contain color-space and image-dimension tags, not recording-location metadata.
- Public-tree pattern checks covered private filesystem paths, RFC1918 addresses,
  MAC addresses, common credential/private-key formats, collection/Drive URLs, and
  text-file email addresses. No candidates were found in the initial 131-file scan.
  The paper's printed author contact is intentionally public and checked separately.
- No participant media, Word files, collection workflows, or follow-up experiment
  directories were included. Final staged-tree review checks links, hashes, and
  source identity again before publishing.

## Limits and Next Step

Pattern checks are a scoped review, not a guarantee that every possible secret
format is detectable. Historical empirical results were not rerun. No microphone,
LLM inference, physical Home Assistant control, or latency benchmark was performed.
Private raw voice and candidate files remain unavailable for public replay.

Publish this reviewed tree as an ordinary commit with tag `kics-2026-artifact-v1`,
preserving `4e16ebc` and keeping development private. Future changes must retain
the distinction between historical KICS evidence and newer experimental revisions.

## README Motivation Clarification

After the author's README edit at `83f283f`, revised both three-line summaries to
state the local-processing motivation: reduce exposure of voice and command data
to external AI services while evaluating command correctness after post-processing.
This is a design objective, not evidence of a security audit, a guarantee of
security, or a claim that optional weather retrieval is offline. The general IoT
description does not expand the documented physical evaluation beyond the curtain
and IR AC. The existing scope and optional-external-service caveats remain intact.

Changes are documentation-only. Verification checks preserve the three-line format
in both languages, local links, and the unchanged paper/runtime. No empirical
experiment is rerun or new performance/security result asserted.
