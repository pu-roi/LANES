# GMA clean-source correction and withdrawal of superseded history

> **Last Updated:** October 23, 2026, 4:09 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The database repair is deployed. **Two clean-source GMA observations are visible; the five superseded history events/polygons are withdrawn from current history, maps, analytics and exports. No replacement polygon qualifies yet.** This is partial source correction, not completed automatic plotting. F. Sevilla's citation and both accepted observations' spatial qualification remain unresolved. Tribune 25, Philstar 274 and active presentation zones remain pending.

## Evidence and root cause

The fresh original [GMA publisher article](https://www.gmanetwork.com/news/topstories/metro/1001693/list-flooded-roads-in-metro-manila-wednesday-sept-9-2026/story/) matches retained original version **140**, compatible native **569**, and the current article-47 body: **1,297 characters**, SHA-256 `f5ff7d13e255ed82ab9c024bcd1aae02fee4ce5806c4a7411bc818e2f58ed763`. Its 3:09 PM update lists three Malabon/Marikina roads observed at **2:47 PM on September 9, 2026**, with gutter-deep water and passage for all vehicle types.

The earlier pipeline selected indexed version **137** / native **574** despite the clean capture already existing. NER 375, correction 380 and events/zones 71–75 are consistent with that older input, but were not authenticated as the original publisher capture. Do not transplant those Quezon City roads or shared 37/26-inch depths to the clean article. The earlier indexed body may represent a different update; this repair withdraws its derived outputs rather than claiming every earlier report was fabricated. [Earlier provenance investigation](news-source-review-20261023.md).

The other retained candidates were compared read-only: Tribune's complete 1,136-character body exactly matches the fresh publisher capture, including 4:34 PM; Philstar's retained 2,708-character body has header/social/caption/related-story material absent from the 2,284-character clean body, while its 4:30 PM flood list agrees. Neither has processed observations or flood events. Their sources were not overwritten or processed.

## Actual processing and outcomes

Actual cloud NER ran **once**, creating immutable raw run **382** with 11 mentions from native 569. A new bounded correction processed the complete original article in three batches of 4/4/3 targets. Gemini returned three retained HTTP-200 responses; backend reference/semantic validation and final recomputation saved completed correction **384**. Raw labels and source bytes remain unchanged.

| Clean source observation | Current result | Historical mapping outcome |
|---|---|---|
| Rizal Ave Extn, San Agustin, City of Malabon | Accepted; gutter deep; Sep 9, 2:47 PM PHT; passable to all vehicle types; no measured inches/meters | Unresolved: authenticated barangay boundary unavailable (`missing_valid_barangay_boundary`) |
| F. Sevilla Blvd. (Bayan), Malabon | Unresolved: provider omitted required city evidence (`native_resolution_city_evidence_missing`) | No event or geometry created |
| Marcos Highway Underloop, City of Marikina | Accepted; gutter deep; Sep 9, 2:47 PM PHT; passable to all vehicle types; no measured inches/meters | Unresolved: raw NER classified Marcos Highway as LANDMARK; current road adapter cannot establish a reported road (`no_reported_road`) |

The remaining city/barangay/pump-context targets are retained as unsupported/context outcomes. Do not turn pump-operation narrative into additional measured flood incidents. The accepted result has two projected groups, `resolved-n6` and `resolved-n10`; all 11 targets have saved outcomes. F. Sevilla remains visible in the complete source and correction's processing outcomes, not an accepted area card. No model label, city citation, geometry, depth scalar or replacement reference was guessed.

### Request identity repair

The first correction attempt, **383**, stopped at `source_repair_uncounted_request` before any provider dispatch. Offline comparison showed semantically identical embedded JSON documents serialized with different object-key order after JSONB read/reconstruction. Array, passage and target order were unchanged. Hash guarding correctly blocked an uncounted payload.

`SourceRepairResolver` now canonically serializes the embedded document (`canonical-document-v1`) while preserving all source text, target/passage ordering and strict validation. Its separately identified resolver creates a new derived pipeline; raw NER identity remains unchanged. Counting and execution now produce identical hashes. Failed 383 and all earlier runs remain retained. The unused count schedule was replaced through an immutable, generation-protected transition; none of its unused slots was treated as a paid request or erased from evidence.

## Atomic database reconciliation

Before writes, Cloud SQL backup **1792737347666** completed successfully (`gma-original-source-correction-20261023-prewrite`). Fresh schema/configuration/row fingerprints and prior serving/worker specifications are retained privately.

`news_source_repair.py` authenticates the exact target, release, clean source/version/run hashes, old lineage and preview. Apply serializes through transaction/incident locks, rechecks eligibility, and appends two new claim cases/sources and unresolved evaluations. Five `news_source_superseded` timeline entries link old events 71–75 to replacement run 384 and its clean source. Original event fields, old inactive geometry, reports, article/version bodies, extraction results and older evaluations are unchanged. No delete, trigger disable, FK bypass or reset occurred.

History SQL, historical maps, analytics, exports, legacy history lists and future news-archive matching exclude these exact versioned supersession markers. Direct current-history inspection returns 409 for a superseded event. Original news processing evidence remains inspectable. No replacement ended event, polygon, publication decision or active instance was created because neither accepted location qualifies spatially.

| Application table | Before | After | Reason |
|---|---:|---:|---|
| `news_extraction_runs` | 5 | 8 | Raw 382, rejected pre-dispatch 383, completed 384 |
| `news_claim_cases` | 5 | 7 | Two clean-source observation cases |
| `news_claim_sources` | 5 | 7 | Bind two claims to completed 384 |
| `news_claim_evaluations` | 10 | 12 | Two explicit unresolved spatial outcomes |
| `flood_event_timeline_entries` | 5 | 10 | Five append-only supersession markers |
| `flood_events` / `flood_avoidance_zones` | 5 / 5 | 5 / 5 | Old immutable evidence retained; zero visible current history / active zones |

All other application-table fingerprints match except one concurrent normal **LOGIN_SUCCESS audit entry 669**. All 658 earlier audit rows match exactly; that entry was retained. The 175 articles, 226 versions, 8 accounts, 37 community posts, citizen-report/moderation records, event locations and existing event/zone fields match their baseline. Migration **f1a9c7e2b604**, trigger states and foreign keys are unchanged. Normal sequence advances from inserts/conflict checks are retained; a repeated correction can consume a sequence number without creating a row. No sequence was reset.

## Release and acceptance

- API: **`lanes-api-source-correction-20261023-v23`**, 100% serving after protected canary acceptance; frontend build **2026-10-23-002** unchanged.
- Worker/API image: `sha256:47487e7eed95a55dc20234bf5cf3818e34553d73a56928251c76d44786f28cda`. Frozen application/script files: **457**. Release/read-context hashes are retained privately in `release-v23.json`.
- Derived pipeline: `ner-v1:dc33bdea0ca42bed17d268e87602f1f27f8f56299a2b2439bde9cecc068cace9`; raw pipeline remains `ner-v1:c94df15a2c730f3e789d369275a8356001d60a03718e67e4cf36949419a47360`.
- Linux amd64 manual worker remains **1 CPU, 3 GiB, 600 seconds, zero retries**, default read-only preflight, general processing disabled, LANES secret version **2**. No personal key use.
- **63 initial disposable PostGIS regression tests passed. Nine accounting/serialization tests passed after the request-order repair** (overlapping tests are not summed as distinct tests). Frozen offline comparison proves identical counted/executed payloads without networking.
- Seven final frozen-worker software contracts and read-only cloud preflight passed in `lanes-news-verified-4fmdf`, with zero real provider calls/inference/database writes. An earlier qualification dispatch used the invalid CLI mode `contracts`; argparse rejected it before application work. Its failed execution/logs remain retained; the explicit inspected correction used `contract-check`.
- Actual retained clean data was loaded into a fresh disposable PostGIS at the existing head. Read-only preview, stale-preview rejection, complete transaction rollback, concurrent apply/reuse, repeat-zero-write and preservation of old facts/geometry all pass. Outbound HTTP was forbidden; no provider/inference call occurred in the rehearsal.
- Cloud correction repeat reuses completed 384 with **zero Gemini requests**. Cloud archive repeat reports **reused / zero database writes**.
- Three retained request/response bundles were exported with external SHA-256 pins and replayed twice inside a **network-disabled** frozen container. All evidence references reproduce; zero provider calls. Semantic/full-result verification also runs in the disposable transaction rehearsal.
- Hosted and local **desktop/mobile** checks pass: two area cards, selected depth/time/location, clean source text and scrolling, immutable earlier input/raw NER through processing history, no overflow or browser exceptions. The first local mobile attempt exposed a transient Next.js upstream socket reset; the existing interface showed a visible history-load error/retry. A fresh warm rerun passed both viewports. No UI code changed for it.
- Final historical UI checks also pass on hosted/local desktop/mobile: existing empty-state text, no old event cards, and zero historical map features. Earlier browser attempts encountered an expired hosted verification JWT and a slow local startup; refreshed verification credentials/warm startup passed, without application changes.
- Protected production API checks verify two results/counts/pagination, matching source, zero history cards/map features/analytics/JSON export records, zero public active zones and superseded-event inspection rejection. Pagination intentionally clamps a page beyond the end; acceptance uses that existing contract.

The first acceptance helpers incorrectly assumed a raw-claim field in the summary DTO, expiry settings inside the operational JSON, and an empty page beyond the final page. Those checks were corrected to the actual existing DTO/configuration/pagination contracts, without product changes or weakening acceptance. All failed helper receipts are retained.

## Spending, recovery and remaining work

Keep the unchanged **US$1 cumulative news cap**. All previous 36 attempts and settlements are retained; exactly three new generation attempts bring the ledger to **39**, stopped. Effective commitment is **US$0.7418188** after usage reconciliation (17,489 input + 2,041 candidate tokens, zero thinking for the new correction); this is an accounting bound, not a verified invoice. The complete three-request maximum schedule was reserved before dispatch and fit below US$1. There were six non-generating token-count calls across the original and canonical schedules, one actual NER invocation, and no further paid retries/fallbacks. Cloud hosting and ordinary website weather usage remain outside the news allowance.

News collection/processing/publication stays paused; automatic expiry and Pasig ML expiry stay OFF; the old seed stays disabled. Ordinary routing still receives no operational flood exclusions. Local private reader selection was updated to the same derived pipeline while preserving its local connection identity; task-equivalent backend/frontend checks use Cloud SQL and remain available.

Remaining work: validate and repair F. Sevilla's missing city citation using retained evidence; qualify a trustworthy San Agustin boundary and a source-supported Marcos Highway Underloop road interpretation before plotting. Do not remove locality/road gates or assign arbitrary coordinates/buffers to obtain a polygon. Tribune/Philstar and presentation activation are not performed here.

Retain the backup, private manifests, input proofs, stopped ledger, immutable request/response/accounting/validation objects, previews, application fingerprints, release specifications and screenshots under ignored `data/gma-source-correction-20261023/`. Recovery stops further execution and retains evidence. Any serving fallback must understand supersession markers (v22 also does); reverting blindly to v20 would make withdrawn history visible again. No destructive rollback, reseeding, commit or push was performed.
