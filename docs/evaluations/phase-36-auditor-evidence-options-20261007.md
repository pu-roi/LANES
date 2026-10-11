# Phase 36: Exact-source evidence options for the free auditor

> **Last Updated:** October 07, 2026, 12:45 AM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Result

The independent auditor now receives exact article spans whose quotes and
positions are calculated by the backend. It selects/copies supporting spans
rather than calculating character positions. All existing strict evidence,
place, observation, depth, access, historical/conflict and publication checks
remain. **170 distinct checks pass**. Synthetic live `openrouter/free` probes
pass at both 60 seconds and the ordinary 20-second worker deadline.

Both successful probes returned `valid_response`, `outcome=review`,
`reason=historical_claim_evidence`. Their exact source evidence validated; the
invented January 2020 fixture remains historical and cannot publish. No live
database access, flood-zone activation, cloud migration/deployment, commit or
push occurred. These samples do not establish real-event accuracy, sustained
free-model availability or current-article/map acceptance.

## Investigation and implementation

The preceding [timeout investigation](phase-36-news-runtime-packaging-20261007.md#october-7-live-timeout-follow-up)
received model quotes with positions that did not match the original text. The
validator correctly rejected them. Asking a generative model to count characters
was an avoidable formatting burden; the source-quotation requirement remains.
The discarded response does not establish precisely how the model miscounted.

- `news_claim_auditor._evidence_options` supplies the already validated candidate
  sentence and other article paragraphs as exact `{start, end, quote}` slices.
  It keeps occurrence identity for repeated text, preserves Unicode/CRLF offsets,
  caps each quote at the existing 4,000 characters and the list at 256 options.
  The candidate remains available even late in a long article.
- Full immutable article/body context remains in the request, independently of
  this bounded list. The options are source excerpts, not pre-confirmed facts;
  the model must independently select evidence and inspect the whole article for
  conflicting/forecast/historical reports. Excess request size fails before a call.
- Prompt identity is now `news-independent-audit-v2`; the response/storage evidence
  schema remains `news-independent-evidence-v1`. Existing policy fingerprints
  incorporate the prompt/options identity, so old terminal evaluations cannot
  silently satisfy the new policy. Historical data is preserved.
- Returned quote/offset triples are still verified against the immutable body.
  Fabricated quotes, altered offsets, wrong claim/place/time/depth, coercions,
  incomplete output and unsupported facts are rejected. No provider output is
  repaired into a confirmation or converted into a current flood automatically.
- The internal `IndependentAuditResult` adds optional numeric
  `provider_http_status`. Non-200 failures expose only this bounded status, never
  raw response bodies, headers or credentials. The synthetic probe includes it
  for actionable diagnostics. Existing JSONB storage needs no schema migration.

## Verification and receipts

| Check | Result |
|---|---|
| Auditor, synthetic-probe, evaluation-policy, pipeline CLI | 139 passed |
| Source-alert publication lifecycle unit checks | 11 passed |
| Native evaluation/lease/history/policy tests in fresh local PostGIS | 20 passed |
| Updated Linux Docker image build and network-disabled asset verification | Passed |
| Live synthetic free probe, 60-second override | `valid_response`, historical review |
| Live synthetic free probe, normal 20-second default | `valid_response`, historical review |

New representative transport cases cover exact Unicode/CRLF slices in both
provider formats, late repeated text with a bounded option list, long source
paragraphs and whole-request size rejection. Existing wrong-evidence, ambiguous
facts, malicious publisher text, provider isolation, timeout and paid-router
refusal checks continue to pass. The single existing multipart deprecation
warning is unchanged.

Native tests applied the existing migration head `d7e4b9a21c60` in the fresh
loopback database `lanes_evaluation_test_spans_e713e2225a`. That database was
removed in final cleanup. Normal/cloud databases were not used.

After the prompt change, the first free probe returned a sanitized HTTP error
without a status available in that older diagnostic. A further request after
adding safe status reporting succeeded; then one default-timeout request also
succeeded. No automatic retry loop, alternate provider or paid fallback was used.
The earlier HTTP failure's cause is unknown; future availability errors remain
explicit failures, not publication permission.

Image tag: `lanes-news-release-check:20261007`. Final OCI manifest-list digest:
`sha256:2c2468ac6af2ed5b89448bfa1fca22cb2747bf121ffa4c39756b499aac345d60`.
Asset identities are unchanged: 897 NOAH tiles, manifest
`cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce`,
and twenty qualified Pasig community boundaries. No dependency, database model,
migration definition, UI component or architecture decision changed.

## Next release checks

Follow the [exact release checklist](../guides/news-zone-release-checklist.md)
from the reviewed `roi-branch` commit/push step. Matching Cloud Build migration,
API/job image/configuration and separate Firebase frontend rollout remain open.
Then perform one controlled current-article execution and inspect eligible zones,
existing desktop/mobile layers, routing and observation-based lifecycle. Synthetic
auditor success does not create a demonstration flood or prove physical PWA
acceptance. The ordinary worker still defaults to twenty seconds; availability
and scheduler/freshness limits remain as previously documented.
