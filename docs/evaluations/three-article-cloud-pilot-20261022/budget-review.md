# GMA four-target continuation and receipt-backed accounting

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 23, 2026, Asia/Manila.

## Verified outcome

**Accounting/request repair deployed; GMA seeding remains incomplete.** All three new generation requests returned HTTP 200. The compatibility batch and the next batch passed source semantics. The following response passed structure/evidence-reference validation but failed source semantics. Processing stopped, without retries or subsequent requests, at failed correction **379** (`native_resolution_status_evidence_missing`). No complete GMA correction, accepted Flooded Areas observations, events or polygons were saved. Tribune 25, Philstar 274 and activation remain pending.

The matching API **`lanes-api-gma-budget-20261023-v11`** serves 100% after protected canary acceptance. The manual worker retains 1 CPU, 3 GiB, 600 seconds, zero retries, default read-only preflight and general processing disabled. LANES secret version **2** remains selected everywhere; personal version 3 is unused.

## Accounting and request controls

- Preserved all original **20 attempt objects and US$0.7731994 historical reservations**, byte-for-byte at canonical-object level. Original V1 ledger is retained locally and as an immutable private object; V1 workers reject V2 rather than reinterpret it.
- Reconciled only attempts 18/19/20 from their exact retained response hashes: **US$0.0041091 / US$0.0044172 / US$0**. Initial effective commitment became **US$0.6566749**. Every other old attempt retains its conservative reservation. HTTP-200 semantic/reference failures remain billable usage estimates; only evidenced provider HTTP 400/500 use the documented zero-token-charge policy.
- Frozen V2 batch manifest has **twelve four-target batches plus one three-target batch**. Original first-four response is adopted without another request. Full article, quotes/order, native proposals, strict validation, temperature 0 and 8,192-token output maximum remain unchanged. OpenRouter's existing path is preserved.
- All **13 non-generating countTokens requests** passed. Calibration returned exactly **6,349**, equal to the retained first request's prompt usage. Full remaining 12-request reservations totaled **US$0.2899290**, for a worst-case effective schedule of **US$0.9466039**, below the unchanged US$1 cap.
- Input reservation uses provider count + response-schema UTF-8 bytes + 1,024 framing tokens; output reserves all 8,192 tokens. Pinned rates are 300/2,500 nanodollars per input/output token. Payload/model/policy/count pins and CAS protect dispatch. Complete schedule fit is checked before generation; uncertain/missing/inconsistent usage retains the maximum and blocks progression.
- Every response is privately retained before parsing, and trustworthy prompt/candidate/thinking/total usage is settled **before article validation**. Immutable settlement receipts preserve failed fact-validation costs. No historical attempt was deleted, reset or automatically refunded.

Final ledger is **stopped at 23 attempts**. Original-plus-new maximum reservations remain **US$0.8456788** as historical evidence; effective commitment is **US$0.6673744**. The three new responses report **US$0.0106995** in token-based usage estimates. These figures are accounting bounds/estimates, **not a verified Google invoice**. Cloud hosting and normal website weather remain outside the news allowance.

## Exact live sequence

| Execution | Stage | Result |
|---|---|---|
| `lanes-news-verified-x7dh8` | Read-only preflight | Passed; expected target/schema/assets, no provider request/write |
| `lanes-news-verified-kg9h9` | Deployed software contracts | Seven pass; no provider request/write |
| `lanes-news-verified-frfgk` | Exact 13-payload token counting | Passed; zero generation/SQL writes |
| `lanes-news-verified-xl8wh` | Four-target compatibility gate, `n4–n7` | HTTP 200; reference/source semantics pass; zero SQL writes |
| `lanes-news-verified-8sthw` | Full GMA continuation | Reuses original `n0–n3` and gate `n4–n7`; `n8–n11` passes; `n12–n15` fails source semantics; stops |

Gate reports 6,349 input / 837 candidate / 0 additional thinking tokens, estimated **US$0.0039972**. Its pinned bundle passes two Docker `--network=none` replays with zero provider calls. A separate continuation receipt prefix prevents create-only gate receipts from colliding with later adoption/semantic receipts. Its access is restricted to create/read, without overwrite/delete. The frozen Linux continuation contract exercises both cached adoptions and the remaining eleven mock requests.

### Offline diagnosis of the rejected response

The rejected response's passage IDs are legal; this is **not another HTTP 400 or out-of-range evidence failure**. Network-disabled replay and individual canonical row checks identify:

| Target | Exact validation result | Retained evidence problem |
|---|---|---|
| `n12`, Brgy. Sienna | `native_resolution_status_evidence_missing` | Status passages 12/14/15/16 cover locality, time and road-list entries; none establishes flood status under the existing validator. |
| `n13`, Don Jose St. | `native_resolution_place_evidence_missing` | Place evidence cites only city/barangay passages 12/14, omitting the street occurrence at characters 924–936. |
| `n14`, Palali St. | `native_resolution_place_evidence_missing` | Place evidence cites only passages 12/14, omitting the street occurrence at characters 955–965. |
| `n15`, repeated Brgy. Sienna | `native_resolution_fact_target_mismatch` | At least one supporting time/depth/access/section citation crosses another road target under the existing source-ownership rule. |

No references were guessed, replaced or deduplicated. No source check was weakened and no partial response was promoted to article acceptance. All successful and rejected responses, exact requests, quote options, semantic receipts and accounting metadata are retained for future offline inspection/adoption. The run receipt's zero aggregate token counters on its failure path do not mean zero paid usage; the independent settlements retain the truthful provider usage before semantic rejection.

## Release and evidence pins

- Image: `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:05c9c3dc91dd21642c5b25fc6b17fde4a9f1bb6f18ab9ef2f57ba845fca33df2`.
- Release: `c02020ffbf6123c5b8d991c06fc2353bec098057e5738c9000f81761e9255577`.
- Count catalog: `a9db1a68b517eb6406a8feb290cf78504d75ed98707fa0633c24cdc37a16f68d`.
- Accepted gate bundle: `5369af1476f009aad3c98b9585b210ec87929778c956bd22e0bb203d4ca1df49`.
- Failed semantic bundle: `715c98cc084bbe1e9b9e8070aaffbc1da65161f034448ac9cb0a2bf55a83bd88`.
- Private local evidence: ignored `data/gma-budget-20261023/`; dedicated immutable GCS diagnostic and continuation prefixes under the existing pilot. Credentials, authorization headers, full articles and returned private content are excluded from this public record.

Earlier v10 candidate manifests and previous v5/v8/v9 releases/evidence remain. The v11 candidate only corrects cache-context compatibility: the original pinned diagnostic contains an additional diagnostic-session field, while article/parent/target bindings must still match exactly. No provider call was used to discover or repair that software mismatch.

## Verification and preservation

- **161-test regression run passed**, including disposable PostGIS; a later expanded **18-test accounting suite passed**, plus seven frozen-image/deployed contracts. Additional frozen-image checks authenticate the original ledger, all three historical reconciliation bundles, all 13 wire hashes, cached adoption and complete reservation fit. Invalid JSON/evidence despite HTTP 200, evidenced 400/500, inconsistent/thinking totals, count tampering, storage failure, stale generations, cap exhaustion and interrupted/reserved requests fail closed.
- Fresh private **806,883-byte cloud backup** restored to disposable PostGIS; all restored row fingerprints and migration head `f1a9c7e2b604` match. No model, migration, schema or dependency was added.
- Protected canary/serving readers, pagination/collection counts, analytics/maps/JSON exports and unauthenticated 401 checks pass. Hosted desktop/mobile checks pass original articles, failure history, all 51 retained NER mentions, evidence scrolling, close controls and existing flood empty states. No frontend source/build/UI modification.
- Final complete snapshot changes **only `news_extraction_runs`**: new failed 379. Original 375/376/378 rows match the restored backup exactly. Accounts, profiles, community posts and related content, original articles/versions, citizen reports/moderation, event/zone tables and schema constraints/triggers are unchanged.
- Final counts: **175 articles / 226 versions / 4 runs / 8 accounts / 37 posts / 0 reports / 0 events / 0 zones**. Scheduled news remains paused, old seed remains the disabled no-op, both expiry switches remain OFF, and no routing exclusions were added.
- A direct stopped-ledger resend check rejects before dispatch, with zero provider calls and unchanged ledger. Complete correction/archive-repeat idempotence and populated map acceptance remain **pending**, because no complete article was accepted.

Core-record audit: task plan, progress and bug log updated. Tech stack, decisions, feature reference, system screen/API documentation and database design reviewed; no dependency, architectural pillar, UI/API shape or schema change requires altering those records.

## Remaining work and recovery

GMA correction, spatial qualification, historical insertion and populated-view acceptance are **not complete**. Repair/qualify source-evidence selection offline before a fresh reviewed continuation. Preserve/adopt already accepted responses where their exact contract permits; do not repeat consumed requests or reuse a failed authority. There are nine untouched generation payloads in this frozen schedule, and the rejected batch needs its own reviewed resolution; remaining capacity must be re-estimated without resetting the ledger or increasing the cap. Tribune, Philstar and all active-zone work remain pending user review.

Recovery retains the pre-stage API **v9**, exact prior worker specification/image and tested backup. Restore serving specifications/revisions and keep the ledger stopped; retain database evidence and every private receipt. Do not reset the database, erase failed runs, downgrade the ledger or launch the old seed.

Official basis: [Google token counting](https://ai.google.dev/api/tokens), [failed-request billing](https://ai.google.dev/gemini-api/docs/billing#am-i-charged-for-failed-requests), [standard model pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite), and [OpenRouter usage-accounting pattern](https://openrouter.ai/docs/cookbook/administration/usage-accounting). The older eight-target provider rejection remains a compatibility observation; its exact Google-side cause is unconfirmed.
