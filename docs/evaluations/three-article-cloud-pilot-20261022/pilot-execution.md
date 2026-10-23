# Three-article pilot execution — stopped at GMA evidence validation

October 22, 2026, 10:50 PM Asia/Manila. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Current result

**The pilot is not complete.** GMA's actual NER run succeeds and all 13 Gemini requests return successfully, but canonical source-evidence validation rejects the assembled correction with `native_resolution_evidence_invalid`. Processing stops before Tribune, Philstar, spatial output preview or flood writes, as required by the first-article acceptance gate. No historical events, active presentation instances or polygons were created.

API `lanes-api-gemini-fix-20261022-v5` and the accepted manual-worker image remain unchanged. The earlier HTTP 400/schema compatibility repair remains accepted; this failure is in backend validation of real-article evidence references, not a renewed HTTP/authentication rejection.

## Preparation and source outcomes

Fresh preflight confirms the accepted release, LANES secret version 2, migration head `f1a9c7e2b604`, unchanged database baseline, paused news flags/scheduler, both expiry flags OFF and disabled old seed. Three successful Cloud SQL backup references are retained privately. The original full article bodies and September package remain unchanged.

Philstar registration is previewed with the existing archive-only authority, then applied through the supervised cloud worker. Registration does not extract or publish news. It creates article **274**, original capture version **573**, with the existing scheduled-processing exclusion. Exact NER/resolve permissions are separately frozen against the accepted release, three input hashes and stable session `september2026-three-article-20261022-v1`; archive authority is not given activation permission.

| Selected source | IDs | Recorded outcome |
|---|---|---|
| GMA September 9 list | Article 47; original version 137; native version 574 | Actual NER run 375 completed; correction run 376 failed evidence validation |
| Tribune September 24 list | Article 25; original version 568 | Frozen; not started because GMA acceptance failed |
| Philstar September 9 / 4:30 PM list | Article 274; original version 573 | Registered and frozen; not started because GMA acceptance failed |

GMA's seven original projection groups are recorded as blocked by article-level correction failure. The 51 attempted correction targets do not have accepted saved outcomes; they must not be counted as successfully processed groups. Tribune/Philstar have deferred outcomes, not successful extraction receipts. No replacement article was selected.

## Executions and spending

| Execution | Operation | Outcome |
|---|---|---|
| `lanes-news-verified-rvxsb` | Philstar registration preview | Eligible full capture; zero writes/provider calls |
| `lanes-news-verified-zj8hg` | Philstar registration apply | Source version 573 retained; no inference/provider calls |
| `lanes-news-verified-5qvmv` | GMA actual NER | Run 375 completed; 51 neural location mentions; peak recorded memory 1,165,025,280 bytes, within 3 GiB |
| `lanes-news-verified-cwz6z` | GMA Gemini correction | 13 requests; 80,985 input and 12,733 output tokens; run 376 failed `native_resolution_evidence_invalid` |
| `lanes-news-verified-9j2d5` | Repeat completed GMA NER | Reuses run 375; `no_work`, zero extra inference, no extra records or Gemini requests |

Before paid GMA execution, an offline Linux run reconstructs all 13 request payloads from the saved actual NER graph. Mock transport and disabled networking prove zero external calls. The conservative article reservation is **US$0.5255618**, fitting the existing US$0.8774132 remaining reservation allowance. The exact article and all 51 requested targets are retained; no text or target truncation was used to reduce cost.

The same private ledger explicitly resumes from its four previous attempts without reset. After GMA it contains **17 preserved attempts**, no in-flight request, and **US$0.6481486 cumulative conservative reservations**. It is stopped with reason `native_resolution_evidence_invalid`; remaining reservation capacity is US$0.3518514. No paid retry, model fallback, personal-key use or additional fictional connection test occurred.

Reported GMA text tokens correspond to approximately **US$0.056128** at the pinned standard text prices. This is a token-price estimate, not confirmed billing. Original conservative reservations remain held; no automatic refunds or reconciliation were performed.

## Investigation and diagnostic limit

The exact error originates in `_spans` in `news_ner_durable/resolution.py`. At least one evidence-index list contains a duplicate index or an index outside the source's quote-option range. Both conditions intentionally share `native_resolution_evidence_invalid`; the receipt does not distinguish them or name the affected target/field. Structural target/count/schema parsing and all 13 transports had already succeeded.

The current correction worker assembles all provider responses before applying source validation. If that later validation fails, the failed run stores no result. It retains request IDs, token counts, error code and immutable parent NER, **but does not retain the returned evidence arrays or partial correction payload**. Consequently, this attempt cannot establish the precise offending target/index, or support a cached correction replay. Do not invent a specific duplicate/out-of-range diagnosis or treat removal of evidence checks as a repair.

Before another paid attempt, repair this diagnostic/retention gap: preserve bounded provider output privately per batch before canonical validation, identify target/field/range/duplicate failures safely, and validate each response before dispatching later batches. Inspect the retained rejected evidence, retain strict source ownership/clock/depth checks, and qualify any cause-specific repair locally and in the matching release. Any resumption must preserve prior attempts and respect remaining ledger capacity. Raising the allowance or discarding reservations is not authorized by this record.

## Preservation and hosted verification

- Existing 174 article rows and 224 original version rows match their preflight row multisets exactly after excluding only the new Philstar article/version and GMA native-compatible version. Existing bodies and review state were not replaced.
- All unrelated table fingerprints and database constraints/triggers are unchanged. Eight accounts and 37 community posts remain intact, with no flood-report links introduced. Citizen reports/moderation remain empty and unchanged.
- Final counts: **175 articles, 226 versions, two extraction runs, zero events, reports or zones**. No claim/publication/operational output was inserted.
- Protected API reads show GMA's selected failed run 376 and completed raw history 375, without fallback to a successful legacy/raw result. Collection status includes GMA under processing failed. News Intelligence flood cards, history, analytics, reports and zones remain empty.
- Desktop/mobile hosted checks verify empty news/history/analytics/export/moderation and spatial active/history views. Separate real-page checks show the failed correction, retained 51 original mentions, working wheel/touch evidence scrolling and visible close control. No page errors or failing protected API requests are observed. No UI code was changed.
- An initial reused UI helper looked for Active Zones as a tab rather than its existing button. Corrected the verification selector only; retain the initial failure and successful spatial recheck. This was a test-helper mismatch, not an application change.

Private source/authority/control receipts, exact payload estimates, baseline/final fingerprints, failed execution logs and hosted screenshots are retained in ignored `data/pilot-execution-20261022/`. The old release, model bundle, inference isolation, worker resource limits/default preflight and serving traffic remain unchanged. News and ledger stay stopped; expiry stays OFF. Do not retry run 376 automatically or advance to the second article before resolving and accepting the first-article stage.
