# Repaired quote contract — single cloud GMA batch accepted

> **Last Updated:** October 23, 2026, 12:07 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The repaired four-target GMA batch passes real cloud transport, strict response structure and evidence-reference validation.** Exactly one Gemini request is made. Its immutable response passes two network-disabled offline replays. The worker is deployed, the budget ledger is stopped and no article correction, event or polygon is saved. This establishes **one-batch acceptance**, not full-article semantic accuracy, spatial eligibility or three-article seeding completion.

## Release and authority

The existing local `quote-option-enum-v1` repair is reviewed without changing its full-article/proposal content, passage order, model or generation settings. Every evidence field enumerates the article's passage IDs; instructions distinguish them from source-character offsets. Existing duplicate/range/target/size and source/time/depth validation remains strict. No rejected response is translated into guessed references.

New `scripts.verify_news_gemini_quote_contract` uses a distinct **`news-evidence-diagnostic-authority-v2`** and input format. The previous v1 command/authority contract is unchanged. V2 admits only the approved request, exact release/application/database identity, stable diagnostic session, old source/parent identities, four original target IDs, model/configuration and US$0.0420974 reservation. It defaults to read-only preflight. The sole explicit execution permits one provider request and **zero SQL writes**.

Read-only SQL verifies saved NER run **375**, native version **574**, GMA article **47**, original parent pipeline/result hash, complete original body, original first four graph targets and failed correction **376**. No NER is rerun, no old record is relabeled, and the narrow diagnostic admits no ordinary processing or publication bypass. Tribune **25** and Philstar **274** remain selected and unprocessed.

| Property | Frozen value |
|---|---|
| Manual-worker image | `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:0d5763f281a688ac5efc695f75aa5ccee824e9c6c78ecb27cae2b8701e3f0449` |
| Release SHA-256 | `835349f5b705c9334ac4b9372d07f0cee7a7a319f18068f4d45f58bacfdb8b2d` |
| Reader descriptor SHA-256 | `5f582c649461932ac2cbc05d08b49853e9626a79d2336572552b13a4f97a59fe` |
| Approved request SHA-256 | `02f4b9b633a06363912fa0f47262377de92e7cb083dcc00011ce76a6cf1ddd8a` |
| Request/reservation identity | `5bbbfc086b4f48acaee3f0459114ee6794cd70d0e836c4aefe25df1137c3a412` |
| Exported replay bundle SHA-256 | `e8b539af345e16930d541dbea1791ddd7ff6a71f4ca63821bc2eeb54ba06cf4b` |
| Diagnostic session | `quote-contract-20261022-v1` |
| Serving API | `lanes-api-gemini-fix-20261022-v5`, unchanged at 100% |
| Provider | `gemini-3.5-flash-lite`, LANES secret version 2, temperature 0, max output 8,192 tokens |
| Worker profile | Linux amd64, 1 CPU, 3 GiB, timeout 600 seconds, zero retries, manually invoked |

The model bundle/inference worker/spatial assets are unchanged. New application/reader identities are frozen for this worker; the API keeps its accepted existing reader identity. No frontend, public API, database schema/model/migration, dependency, training or scheduled RSS change occurs. Existing migration head remains `f1a9c7e2b604`. The worker's default is read-only preflight and general provider execution stays disabled.

Private receipt access adds only two conditional runtime grants, `storage.objectCreator` and `storage.objectViewer`, scoped to `private/news-pilot/20261022-5512bbaa/diagnostics/quote-contract-20261022-v1/`. Existing grants remain unchanged; no overwrite/delete/public-access permission is added. Durable reservation and immutable intent precede POST; bounded response retention precedes parsing. Transport, retention, evidence validation and final article acceptance remain separate states. Credentials/authorization headers are absent from retained artifacts and public diagnostics.

## Qualification and actual executions

**127 tests pass**, with no skips or removed tests and three existing dependency/Pydantic warnings. Added V2 tests cover exact admission, rejection of old/expanded/wrong-target authorities and modified payloads, zero-spending default preflight, stopped-ledger repeat protection after both success and failure, and response retention. Existing suites cover invalid/duplicate references, malformed/oversized results, unsupported facts, wrong/duplicate/missing targets, interruption, storage failures, tamper, budget concurrency and disposable PostGIS handoff/readers/reuse/pilot behavior.

The newly frozen image passes all seven network-disabled contracts and reader/asset identity checks before upload. Cloud stages complete in order:

| Execution | Scope | Verified outcome |
|---|---|---|
| `lanes-news-verified-h4fp9` | Read-only readiness and seven mock-provider contracts | Pass; zero provider calls, NER inference and SQL writes |
| `lanes-news-verified-dw9wb` | Dedicated private-storage contract | Rejected mock response retained; overwrite blocked; two offline replays; zero provider calls/SQL writes |
| `lanes-news-verified-7jdbx` | Exact V2 GMA input/parent/authority preflight | Pass; zero provider calls, NER inference and SQL writes |
| `lanes-news-verified-dgd76` | One approved real repaired batch | HTTP 200; four exact targets; all evidence references valid; response retained; zero NER inference/SQL writes |

The real request reports **6,349 input and 1,005 output tokens** using the selected model. The retained response has no duplicate or out-of-range evidence failure. It is exported with its exact request, ordered quote map, parent/source hashes and reservation binding. Both subsequent offline replays run in the frozen Docker image with `--network=none`, read-only input and no provider credentials. Both exit 0 with `evidence_references_passed`, four targets and **zero provider calls**.

These checks do not run the remaining GMA batches or full-article semantic/ownership recomputation. Article acceptance remains `not_evaluated`; database publication and seeding remain `not_attempted`. Legal passage IDs alone do not prove every selected fact correct.

## Spending and preservation

The original **18 ledger attempts and US$0.6885786 conservative reservations remain identical**. One explicitly resumed attempt reserves **US$0.0420974** before POST. The final ledger contains **19 attempts and US$0.7306760 reserved**, with the unchanged US$1 cap, no in-flight request, and stopped reason `single_quote_contract_diagnostic_completed_requires_review`. Remaining reservation capacity is US$0.2693240. Reservations are not confirmed charges; no reset, refund, reconciliation, second batch, automatic retry, model fallback or additional connection probe occurs.

Fresh preflight fingerprints match the previous baseline exactly. Final comparison verifies unchanged source articles/versions, runs 375/376, accounts, community posts/links, citizen reports, moderation, flood/news-output tables, configuration and every other table **except `visitor_daily_visits`**. Counts remain **175 articles, 226 versions, two extraction runs, eight accounts, 37 community posts and zero events/reports/zones**. Constraints, triggers and all sequences are unchanged.

The initial strict all-table audit deliberately reports the visitor-table difference instead of claiming complete equality. Investigation confirms unchanged visitor row count **173**, one record with `last_seen_at` **2026-10-22T15:59:56.931293Z**, and a successful normal public `/visits` POST on the unchanged API revision beginning **2026-10-22T15:59:56.923176Z** (October 22, 11:59:56 PM Manila). The existing visitor service updates that timestamp for repeat activity. Diagnostic SQL is explicitly read-only and its receipt confirms zero writes. This concurrent website activity is recorded as an exception; original before/after fingerprints are preserved without rebasing or undoing the visitor update. All other table fingerprints match exactly.

API specification/serving traffic and old seed specification remain unchanged. News scheduler stays PAUSED; collection/processing/publication are false; both expiry switches are OFF. The existing expiry scheduler configuration remains unchanged, with only routine execution timestamps advancing. API/discovery/manual verification all retain `lanes-gemini-api-key` version 2; personal version 3 remains unused.

## Completion and next gate

The authorized **single-batch verification is complete**. News Intelligence Flooded Areas, Flood History and Active Zones remain empty because this phase creates no accepted article/flood outputs. The three saved sources remain available for later processing. Full GMA correction, spatial qualification and three-article seeding are pending a fresh cumulative estimate and separately approved continuation; do not assume the remaining US$0.2693240 reservation capacity covers them.

Private baseline/recovery snapshots, all immutable inputs/authorities/manifests, frozen release artifacts, test/cloud receipts, ledger snapshots, original/returned response pair, replay pins and concurrent-visit evidence are retained under ignored `data/quote-contract-cloud-20261022/` and the dedicated GCS prefix. The session directory date names the October 22 preparation; completion is after midnight October 23 Manila. No additional provider dispatch follows this report.

Recovery retains the accepted API and previous manual-worker snapshot/image. On a release problem, restore that worker specification while keeping the ledger stopped and general execution disabled; retain database/receipt evidence. No reset, deletion, replacement incident or activation is part of recovery. Rollback was not required for this accepted release.
