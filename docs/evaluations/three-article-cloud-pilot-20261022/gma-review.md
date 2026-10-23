# GMA-only review — cloud request rejected; seeding stopped

> **Last Updated:** October 23, 2026, 12:56 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: incomplete.** The GMA-only continuation was authorized and executed, but Gemini rejected the first new eight-target request with HTTP 400 / `INVALID_ARGUMENT`. No corrected article, flood event or polygon was saved. A failed correction receipt is retained as run **378**. There was exactly **one new provider POST**, no automatic retry, and no Tribune/Philstar processing or activation.

## Delivered and verified

- Added narrowly scoped `news-gma-review-v1` resolve/archive authority, authenticated adoption of original NER **375** / native version **574**, and an exact seven-batch manifest: cached four targets followed by 8/8/8/8/8/7 targets. Old runs 375/376 are unchanged.
- Reused the accepted first response without a provider call or reservation. Its full per-row semantics pass, but it yields zero projected claims under the existing locality rules. Legal evidence references alone do not establish a qualified observation.
- Extracted the existing semantic validation into a shared pure function and now validate every batch before dispatching the next. Retained strict references, source ownership and canonical full-result recomputation.
- Implemented a separate archive-only command using existing event/zone/location/timeline and case/source/evaluation tables. Disposable PostGIS proves ended events, inactive geometry and idempotence without publication decisions or active instances. **This cloud archive stage was not reached.**
- Passed **151 targeted tests**, seven offline frozen-image contracts, actual cloud read-only preflight and seven cloud software contracts. An offline full-GMA mock verifies all frozen request hashes, cached adoption, exact cost reservations and final saved-result recomputation; it is software evidence, not extraction accuracy.
- Restored a fresh private pre-stage cloud backup to disposable PostGIS and verified all rows/head. Authenticated NER 375 against its original v5 image with networking disabled; no inference reran.
- Promoted matching API/readers only after protected canary acceptance. No frontend, public response shape, model/schema/migration, dependency, training or scheduled method changes.

## Actual cloud outcome

| Item | Verified value |
|---|---|
| API serving 100% | `lanes-api-gma-review-20261023-v9` |
| Worker image | `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:25c3f6d0b524b53a5264952407677b8a48fdc1945d24425506b76918f701d71e` |
| Release SHA-256 | `92cb231daababeaa78491ca905714dfbd52e2dbaf015803c52edac2a26a0d2b9` |
| Reader SHA-256 | `206d25c32eb4031840e2d93810dbac094f1081cb06096b7154fc13d42cf9326d` |
| Raw / derived pipeline | `ner-v1:5e339215f356369687d09ec7ae79c4af2bbeacfe8faa1ffd4ffe8a9fb5614d6a` / `ner-v1:e121dfb9d367a10fa2adee132ff6899cc2c673c13be0400a88bc5d2e684f35cd` |
| Cloud software / GMA preflight | `lanes-news-verified-jm4x8` / `lanes-news-verified-9w4zh` |
| Live execution | `lanes-news-verified-pnn9b`, one task attempt, exit 1, zero retries |
| Newly selected targets | `n4`–`n11` |
| Rejected request SHA-256 | `566111dde6fafd17a800ca3b0104265c4b8a049cb66a45768da40a3bd0fc23fe` |
| Credential | LANES `lanes-gemini-api-key:2`; personal version unused |
| Worker | 1 CPU, 3 GiB, 600-second timeout; default read-only; general processing disabled |
| Result | HTTP transport returned a retained 400 error body; response retention passed; evidence/semantic validation and full article acceptance were **not reached** for this request |

The immutable retained body contains only code 400, status `INVALID_ARGUMENT` and message “Request contains an invalid argument.” It has no diagnostic details, generated candidates or usage. Two pinned network-disabled replays reproduce `provider_rejected`, with zero provider calls. Separate cached-adoption/semantic receipts retain the first batch's successful reuse. Failed run 378 remains visible in article processing history and Collection status; it cannot silently fall back to an older successful extraction.

## Investigation: known facts versus hypothesis

The complete article, quote ordering, all native facts/groups, instructions, model, temperature, 8,192-token output limit and schema profile match the accepted four-target request. The selected target list changes, and exactly three schema paths differ: target-ID enum, `results.minItems` (4→8) and `results.maxItems` (4→8). No missing source text or output truncation was observed; the provider rejected the request before returning article facts.

**Leading hypothesis, not a confirmed root cause:** the larger structured response crosses a serving schema-complexity limit. Google's [structured-output documentation](https://ai.google.dev/gemini-api/docs/structured-output?hl=en) lists array limits, enum branching and other schema complexity as possible causes of HTTP 400. The generic retained error does not identify which constraint caused this rejection or establish an exact batch-size threshold. Local schema and mock tests cannot prove provider acceptance. Do not declare the API key, billing or NER defective on this evidence.

No further paid experiment or automatic fallback followed. A cause-specific request repair and new cumulative cost plan are required before explicit resumption.

## Budget — unchanged US$1 cap

The original **19 attempts / US$0.7306760** are preserved exactly. One new conservative reservation of **US$0.0425234** produces **20 attempts / US$0.7731994**. The ledger is **stopped**, with no in-flight attempt. These are reservations, not confirmed charges; no reservation was reset or refunded.

The initially frozen six-new-request schedule would have ended at US$0.9858854 if all six passed. Repeating the failed work would exceed that estimate. A network-disabled estimate of completing the remaining 47 targets using the previously accepted four-target format needs **12 new requests / US$0.5051406**, projecting **US$1.2783400** cumulatively. It **does not fit** the existing cap and is not authorized. This does not require buying another key or adding funds; it requires an explicit internal allowance decision or a separately qualified, cheaper request contract. No cap change occurred.

## Tables and existing screens

| Persistence / screen | Actual result |
|---|---|
| Original articles and versions / Collection | 175 articles, 226 versions preserved, including GMA 47, Tribune 25, Philstar 274 |
| `news_extraction_runs` / article processing history | Original completed 375 and failed 376 unchanged; new failed 378 (`native_resolution_http_error`, null result, one attempt) |
| Case/source/evaluation and publication tables | Still empty; no archive qualification/apply occurred |
| Event/zone/location/timeline / Flood History, maps, analytics, exports | Empty; no records fabricated |
| Active Zones / Spatial Operations / routing exclusions | Empty and unchanged; activation was excluded from this stage |
| Accounts, community posts, citizen reports, surveys, moderation | All pre-stage fingerprints unchanged; eight accounts, 37 posts, zero citizen flood reports |

Protected canary and serving API reads pass. Actual hosted desktop/mobile tests pass failed-run visibility, all 51 retained original mentions, evidence scrolling/close controls, 175 saved articles, empty Flooded Areas, empty history/analytics/exports, empty flood moderation and Spatial Operations. Populated flood cards/map focus/evidence and archive idempotence on the cloud remain untested because no accepted correction exists. No UI edits or frontend deployment occurred.

The final whole-database audit detects **only** `news_extraction_runs` and its sequence changing. Every other table fingerprint, original runs 375/376, trigger/FK definitions, existing article versions, reports/moderation and unrelated notifications match the pre-stage baseline. News automation remains paused, both expiry switches OFF, old seed specification unchanged and personal credential unused.

## Evidence and recovery

Private source/request/response and credentials are excluded from this public evaluation. Retained ignored evidence: `data/gma-review-20261023/`, including original-parent recomputation, backup/restore proof, frozen context/image, exact authorities, cloud receipts, immutable response bundle and external pin, two offline replays, budget states, protected API receipts, desktop/mobile screenshots and final preservation audit. Private GCS receipts use `private/news-pilot/20261022-5512bbaa/diagnostics/gma-review-20261023-v1/`; create/read grants are conditional on this prefix and do not authorize overwrite/deletion. [Content-free summary](gma-review-summary.json).

Recovery may restore serving traffic to `lanes-api-gemini-fix-20261022-v5` and the saved pre-stage v8 manual job specification/image. Retain the failed run, artifacts and stopped ledger. Do not reset the database, delete evidence, reuse consumed request identities, enable schedules or activate zones. The previous revision/image, fresh backup and exact before configurations are retained; rollback has not been needed because the matching readers pass acceptance.

## Pending ordered gates

1. Identify/qualify a compatible request contract and review fresh cumulative spending against the unchanged cap. Do not silently resend the failed request or change schema validation.
2. Explicitly resume only inspected GMA correction. Reuse original NER and valid retained responses under exact identity checks; require complete article acceptance before spatial writes.
3. Preview/apply qualified **ended history / inactive geometry only**, then verify populated hosted views and zero-cost repeat reuse.
4. Stop for the user's review. Tribune/Philstar processing and all active presentation instances remain separate pending stages.
