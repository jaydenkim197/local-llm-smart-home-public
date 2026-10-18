# ADR-019: Keep Development Private and Publish a Versioned KICS Artifact

Date: 2026-10-19. Status: accepted for this public distribution.

## Context

The development repository contains full experimental history, private operational
records in older commits, and unfinished follow-up revisions. The existing public
repository was deliberately initialized from a sanitized snapshot at `4e16ebc`.
The author requested strengthening that public repository and featuring the KICS
paper without exposing private material.

## Decision

Keep the development repository private. Update this public repository through
reviewed file exports, never by merging private history. Use the KICS reference
snapshot `0cdca36e0cdd408c9998fbdfa58e00ede841a784`, keep the existing sanitized
operational documents/media, and publish the author's unchanged submission PDF.
Include relevant regression tests and methodological/result documents; exclude
private raw inputs, operational collection deployments, and later experimental
parser revisions. Record public artifact identity with an ordinary commit/tag.

## Alternatives

- Making the development repository public would require auditing its complete
  history, logs, attachments, and operational records, and is unnecessary here.
- Publishing only the paper would omit the executable evaluation method.
- Publishing the latest parser with historical KICS scores would blur version
  identity before follow-up evaluation is complete.

## Consequences

Development has one source of truth and the public tree has a deliberate release
boundary. Public code/results are more inspectable, but private speech and raw
candidate files still limit independent reproduction. No new model-performance or
physical-device result is established by packaging or unit tests. Future public
exports must repeat the review and preserve this release's identity.
