# Public Release Scope and Provenance

Release preparation date: 2026-10-19, Asia/Seoul.

## Source Identity

- Public repository: `jaydenkim197/local-llm-smart-home-public`.
- Previous public head: `4e16ebc499989384030f312c6471ebcbdb4d34db`.
- Reviewed KICS source snapshot: `0cdca36e0cdd408c9998fbdfa58e00ede841a784`.
- This is a reviewed file export, not a merge of private Git history.
- The private repository remains the development source of truth. This repository
  is a public distribution, not a second independent development branch.

The KICS snapshot predates subsequent experimental parser changes. Publishing
those changes beside historical KICS scores without a version boundary would
misrepresent the implementation/result relationship. They are therefore excluded
from this release. The tag `kics-2026-artifact-v1` identifies the verified public tree.
The initial public commit is retained without history rewriting.

Source commit IDs in historical reports identify the original experiment record;
they are not necessarily Git objects available in this public repository. Published
runtime files and datasets can instead be inspected in this release. Public Git
commit times do not independently prove the historical pre-result freezes.

## Included

- KICS reference application, parser, Home Assistant adapter, web client, and
  example-only environment configuration.
- Requirements, simulation launcher, and relevant Python regression tests.
- Frozen developer-authored 40-case and prospective 20-case command sets,
  synthetic contexts, fixed voice prompt manifest, and physical-test case manifests.
- Evaluation and replay code, reviewed aggregate result reports, and relevant
  methodological decisions.
- The author's unchanged KICS submission PDF, explicitly requested for public posting.
- Previously published, reviewed demonstration images and sanitized MVP documents.

The original network documentation and media privacy edits in the public repository
are retained; private copies are not copied back over them.

## Excluded

- Private Git commits and their pre-sanitization network/VM records.
- `.env`, tokens, pairing codes, operational coordinates, private network addresses,
  router details, and personal filesystem paths.
- Participant audio, transcripts, row-level voice traces, private folder mappings,
  consent records, and collection access codes.
- Operational recording portals, deployed collection endpoints, Apps Script
  receiver code, and collection deployment workflows.
- Raw experiment output folders and external-drive backups. Only the existing
  reviewed aggregates and integrity hashes are distributed.
- School administrative documents, Word working files, and unpublished paper drafts.
- Follow-up experimental datasets, independent-author responses, and unfinished
  experimental parser revisions.

Author names, affiliation, the contact printed in the requested PDF, the repository
owner, and already approved demonstration photographs are intentional public
attribution/media, not newly anonymized data. The installation photographs disclose
part of the home interior and exterior view even without GPS metadata.

## Reproduction Boundaries

Frozen dataset files are copied without reformatting so their original SHA-256
values remain meaningful. The 40-case dataset hash is
`80bc08ce34a6e280eecd60ecca0c2da354793013f8f53bca27f29f49e3dd6f86`;
the 20-case hash is
`73ec95c9e3c1642606c6e803a0f3f534f0cf8f4cf9d555a885f1c1277e0d4691`.
The voice manifest hash is
`3d0b65da145a3eaa5898a523b6e636d9e04bef9877887d8c63279b8268289737`.

For raw LF-byte hash checks on Windows, clone with `git -c core.autocrlf=false clone
<public-repository-url>` or otherwise ensure checkout does not convert line endings.
Do not overwrite historical hashes merely because a local checkout uses CRLF.

Fresh model runs can be conducted with the supplied harness, but matching the model
tag alone does not guarantee the original model digest or outputs. Raw-output replay
and original speech results cannot be independently recomputed from the public tree
alone because their original inputs are not distributed. Tests are code regression
checks, not replacement empirical results.

Only the 300-lux field profile changes the low-light condition in its separately
documented functional checks. The frozen command evaluations retain the 100-lux
default and 800-lux bright threshold.

## Publication Practice

Develop and preserve full records privately. Export only reviewed stable files,
test the exported tree, scan the complete public tree, and publish a new ordinary
commit/tag. Never merge the private repository into this public repository or
force-push its history here. Public release notes must distinguish implemented
behavior, measured results, and unverified follow-up work.

No repository-wide code license or publisher license has been selected by this
packaging task. Third-party dependency/model terms are unchanged.
