# LANES documentation

> **Last Updated:** October 24, 2026, 04:33 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Source publication — October 24

[PR #143](https://github.com/pu-roi/LANES/pull/143) publishes the scoped Tribune pilot, context repair, cleared-area filtering and CI checks on `roi-branch`. Validation: 385 normal-gate tests and 42 required PostGIS checks pass. Main review/merge and its deployment remain pending. [Latest evidence](evaluations/tribune-context-repair-20261024.md).

## Tribune context and cleared-list repair — October 24

[Context, saved evidence and release checks](evaluations/tribune-context-repair-20261024.md). Correction 395 saves three Tribune road observations; the patched reader excludes Quezon City subsided evidence from Flooded Areas while preserving authenticated source inspection. API `lanes-api-tribune-context-20261024-v6` now serves the repair; candidate/serving and hosted/local desktop/mobile checks pass. Four active zones and all original data/ledger are preserved. [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Tribune saved-article pilot — October 24

[Approved source/lifecycle plan](plans/tribune-saved-article-pilot.md) · [Actual cloud runs, spending, tests and limitations](evaluations/tribune-pilot-20261024.md). Raw NER 390 and zero-provider finalized correction 392 are saved. Active event/zone **80** is deployed through `lanes-api-tribune-20261024-v3`; protected candidate/serving checks and hosted/local desktop/mobile acceptance pass. Source/CI changes are published on `roi-branch` in [PR #143](https://github.com/pu-roi/LANES/pull/143); reviewed main integration remains pending. Quirino/Gov. Pascual and specific cleared-road evidence gaps remain unresolved. Tribune's selected lifecycle enters unified history after manual deactivation; GMA's original exclusion is unchanged.


## Latest completion — event details and checked CI/CD restored

[@roicambe](https://github.com/roicambe) (Roi Cambe). PR [#142](https://github.com/pu-roi/LANES/pull/142), main `8c33ae04b071bdf587b4b72e98289de5f77db583`, cloud build `d52b144e-2809-4f3c-b941-5d378c21bc33`: all gates and final desktop/mobile acceptance pass. Serving API `lanes-api-build-d52b144e-2809-4f3c-b941-5d378c21bc33` loads event 76 with zero media; three correction-388 observations and active zones 77–79 remain intact. The existing main trigger is enabled; news automation remains paused. [Release evidence](evaluations/event76-inspection-20261024.md#completed-publication-and-restored-cicd). Earlier sections retain their checkpoint status.

## Latest investigation — event 76 details and CI/CD integration

[Event-detail 503 diagnosis](evaluations/event76-inspection-20261024.md): the current API is still the repaired reader release. A separate JSON-null photo-count query fails when opening event 76; list/news readers remain healthy. The patch and expanded PostGIS/canary/desktop/mobile checks now pass on serving API `lanes-api-history-details-20261024-v1`, without data edits. The backend trigger remains disabled pending scoped PR/main integration and an exact merged-commit build. [Current follow-up](task_plan.md#current-follow-up--event-76-history-inspection-failure).

## Latest recovery — News Intelligence serving normally

API `lanes-api-reader-recovery-20261024-v1` restores the three saved correction-388 observations without changing database records. Active zones 77–79, desktop/mobile source details/maps and unrelated history 76 remain intact. The normal API image now packages its authenticated reader manifest and deployment uses a protected canary gate. Automatic backend deployment stays disabled until the repair is reviewed and merged into `main`; the qualified manual worker is unchanged.

- [October 24 reader outage, recovery and verification](evaluations/news-reader-recovery-20261024.md)
- [Saved-reader release and recovery procedure](guides/news-reader-release.md)
- [Current pilot inventory, completed GMA work and pending gates](task_plan.md#current-pilot-inventory-and-remaining-work)
- [Conversation bug/status reconciliation](others/bug-log.md#conversation-status-reconciliation--october-24)
- [Current screen behavior and reader release](others/system-documentation.md#current-news-intelligence-readers-and-presentation-state--october-24)

The latest verified pilot has five observations and four active polygons: unchanged GMA 77–79 plus Tribune Boni event/zone 80. Tribune 25 is processed with partial evidence acceptance; Philstar 274 remains unprocessed. Existing history contains unrelated event 76, not replacement GMA archives. Older headings below record earlier results and are not the current work queue.


## Prior spatial rollout — three connected-road GMA active zones

Three corrected GMA active presentation event/zone pairs **77–79** are deployed through API/manual worker **v30**, linked directly to article **47**, source **140/native 569**, unchanged correction **388**. Rizal Avenue Extension, Tañong F. Sevilla Boulevard and the ground-level Marcos Highway Underloop qualify under opt-in `connected-road-noah-v1`. Administrative names disambiguate roads without clipping geometry. Source observations remain gutter deep, September 9 at 2:47 PM, passable to all vehicles, with measured inches/metres unknown. These instances have no ended counterpart and are excluded from Flood History, historical analytics/exports and routing; unrelated history event 76 is preserved. [Release and geometry verification](evaluations/gma-connected-road-20261023.md); [current checklist](task_plan.md#current-state--three-connected-road-gma-active-locations-saved). Hosted/local desktop/mobile acceptance passed. Earlier stopped checkpoints below describe their earlier releases.


## Earlier v27 verification — scoped GMA cleanup; plotting blocked

[Incorrect-capture cleanup and active-only gate](evaluations/gma-active-cleanup-20261023.md): old event/zone pairs 71–75 and their incorrect capture/processing chain were removed after backup/rehearsal. Three corrected run-388 observations remain visible; unrelated history event 76 is preserved. API/worker v27 supports active-only output without ended counterparts, but the actual three-location spatial preview remains unresolved and **no active GMA polygons were created**. No provider calls; stopped ledger unchanged at 42 / US$0.7524937. [Current work and blockers](task_plan.md#current-state--incorrect-gma-chain-removed-active-plotting-blocked).

## Earlier extraction completion — three GMA News Intelligence observations

[GMA three-location completion](evaluations/gma-three-location-completion-20261023.md): correction 388 is live on API v26 and localhost, including **Tañong F. Sevilla Blvd. (Bayan)**. Exact article evidence, gutter depth, Sep 9 at 2:47 PM and vehicle passage agree across all three cards. Cached responses and zero-provider finalization avoided further calls after the one authorized request. Hosted/local desktop/mobile pass; ledger stopped at **42 attempts / US$0.7524937**. No GMA history/polygon/active output; other articles and spatial qualification remain pending review.


## Earlier cloud checkpoint — heading repair deployed; continuation stopped

[GMA city-heading repair and duplicate-locality diagnosis](evaluations/gma-city-heading-20261023.md): v3 fixes plain-list city context and passes offline/disposable qualification. The real second batch additionally classified Brgy San Agustin using Rizal Avenue's road evidence, so processing stopped before batch three. Only failed run 386 was appended. API v23/local readers still show two accepted observations, current history/active zones remain empty, and the ledger is stopped at **41 attempts / US$0.748841**. No promotion, retry, NER inference or polygon creation followed.


## Previous accepted source correction — two observations; plotting unresolved

[GMA clean-source correction and superseded-history withdrawal](evaluations/gma-source-correction-20261023.md): actual NER/Gemini processing now uses original 140/native 569. Two correct gutter-deep observations at Sep 9, 2:47 PM appear in News Intelligence. Five obsolete history polygons are retained as evidence but withdrawn from current history/maps/analytics/exports; **no replacement polygon qualifies yet**. F. Sevilla citation and spatial coverage/road interpretation remain pending. API/worker v23, frontend unchanged; preserved accounts/posts/reports and repeat/offline/desktop/mobile checks pass. Stopped ledger: 39 attempts / US$0.7418188, cap US$1. Older checkpoints below are not current geometry acceptance.

## Earlier source review — GMA capture mismatch and deployed admin reader repair

[GMA source review and summary repair](evaluations/news-source-review-20261023.md): the pilot reused an indexed snapshot despite a clean publisher body already being saved. The current source display now matches that publisher capture; selected Flood Details replaces duplicated raw NER diagnostics, and immutable processing evidence stays accessible. API/frontend/manual guard deployed and hosted/local desktop/mobile checks pass without data or Gemini-budget changes. Existing five derived observations/events require reprocessing/review before source accuracy is claimed. Other articles and activation remain pending.

## Earlier historical population — later superseded and cleaned up

[GMA shared-depth historical archives](evaluations/three-article-cloud-pilot-20261022/gma-shared-history.md): five ended incidents and five inactive estimated corridors now appear in existing hosted/local history cards, maps, analytics and exports. News Intelligence retains five observations. Source-supported shared severity is preserved without individual depth measurements; old evaluations remain immutable. Worker v18 only, API v17 unchanged; no extra Gemini/inference calls, ledger unchanged/stopped, protected records preserved. Desktop/mobile acceptance and repeat zero-write checks pass. Tribune, Philstar and active instances remain pending.


## Earlier hosted checkpoint — five corrected GMA observations; archives unresolved

[GMA population, reader patch and remaining historical blocker](evaluations/three-article-cloud-pilot-20261022/gma-population.md): run 380 supplies five live News Intelligence cards with September 9, 8:55 AM times; all 51 targets have outcomes. Five historical evaluations remain unresolved because shared depth cannot satisfy the current individual-depth polygon rule; Flood History/Active Zones stay empty. Corrected-group Info HTTP 422 is patched, desktop/mobile scrolling/source work, replay/idempotence pass and the ledger is stopped at US$0.7314696 under US$1. Tribune, Philstar and activation await review. Earlier dated checkpoints below remain retained.

## Latest cloud verification — one GMA batch accepted; review stop

[Restricted scoped GMA gate](evaluations/three-article-cloud-pilot-20261022/scoped-cloud-gate.md): 231 tests and seven worker contracts pass; one token-count and one real generation accept both road observations with correct source dates/clocks/shared depth, leaving barangay headings as context. Two offline replays reproduce the result. Ledger stopped at 24 attempts/US$0.6726674 effective commitment; new usage estimate US$0.005293. Manual worker v14 deployed, API v11 and all application-table fingerprints unchanged. **No seeding or new public data**; full GMA/article/history/presentation stages remain pending. Earlier entries retain their dated scope.

## Latest implementation — scoped Gemini evidence contract (offline candidate)

[Scoped contract repair and qualification](evaluations/three-article-cloud-pilot-20261022/scoped-evidence-repair.md) records the opt-in V2 passage/heading/field contract, explicit unresolved row outcomes, strict recomputation, usage compatibility and offline retained-response checks. **197 regression tests and seven frozen Linux worker contracts pass**. Cloud deployment, new budgeting/authority review and real-model acceptance remain pending. No paid requests or flood data were created; v11 is still the last verified hosted checkpoint. The research entries below retain their dated scope.

## Latest investigation — GMA evidence handoff and grounding options

[Source-evidence investigation](research/gemini-evidence-validation-20261023.md) reproduces the real four-row failure offline and finds an additional missing-date citation in every row, plus a latent thinking-token transport mismatch. Research compares current Google docs with firsthand developer-forum, Reddit and Stack Overflow reports; older Search/JSON incompatibility advice is checked against its October 5, 2026 fix. Recommended repair pre-binds target passages, represents heading scope and context-only barangay roles, collects complete diagnostics, and evaluates row-level unresolved outcomes. Search/Maps remain a separate enrichment/cost/attribution decision. **Investigation only:** no runtime/source-code deployment, paid request, database write or ledger change. GMA seeding remains incomplete.

## Latest GMA continuation — accounting repaired; source evidence blocks seeding

[Four-target cloud execution and V2 accounting](evaluations/three-article-cloud-pilot-20261022/budget-review.md): matching API/worker v11 deployed after local, Linux, cloud and protected-reader checks. CountTokens fits the complete schedule under US$1. Three new requests return HTTP 200; gate and next batch pass, following response fails strict source semantics and stops at run 379. Final ledger: 23 preserved attempts/US$0.6673744 effective commitment; usage estimates are not an invoice. No complete correction, flood history or active zone was created. Hosted desktop/mobile failure/scroll/empty-state checks and full preservation audit pass. Source-evidence repair, complete GMA acceptance and seeding remain pending. Earlier entries retain dated scope.

## Latest GMA-only continuation — stopped before seeding

[GMA-first release and retained HTTP 400](evaluations/three-article-cloud-pilot-20261022/gma-review.md): v9 worker/API readers pass 151 tests, seven image/cloud contracts and hosted desktop/mobile failure/history/scroll/empty-state checks. Cached four-target evidence is reused without a request; the first new eight-target call is rejected with generic `INVALID_ARGUMENT`. No later batches, corrected flood observations, history or active zones. New failed run 378 is preserved; all pre-existing protected data and original 375/376 are unchanged. Ledger stopped at 20 attempts/US$0.7731994 reservations under unchanged US$1 cap. A compatible request and fresh cost plan are required; schema complexity is a hypothesis. Earlier entries below retain dated scope.

## Current three-article pilot

[Single repaired GMA cloud batch accepted](evaluations/three-article-cloud-pilot-20261022/quote-contract-cloud.md): separate V2 authority, matching deployed manual worker, 127 tests and seven image/cloud contracts. Exactly one HTTP-200 four-target response passes evidence-reference validation and two offline replays. Ledger stops at 19 preserved attempts/US$0.7306760 conservative reservations. API/protected data unchanged; concurrent normal visitor heartbeat is recorded separately. No full article correction, spatial output or seeding; the three-article continuation remains pending.

[Cause-specific evidence-contract repair](evaluations/three-article-cloud-pilot-20261022/evidence-contract.md): article-specific passage-ID enums and explicit offset/index instructions pass 114 local tests and seven network-disabled Linux contracts. Full inputs and semantic/source checks are preserved; original rejected evidence remains rejected. No provider call, cloud/database deployment or ledger change. Matching cloud release, live acceptance and three-article outputs remain pending.

[Private retention repair and single GMA diagnostic](evaluations/three-article-cloud-pilot-20261022/evidence-retention.md): worker-only release passes 91 local tests, seven local/cloud contracts and real private-storage retention/immutability checks. One frozen GMA batch returns HTTP 200 but nine evidence fields reference 318/327/347 instead of valid passage IDs 0–58. The retained response replays twice without networking or paid calls; source-character/index confusion is the evidence-supported explanation. Every database fingerprint and serving API v5 remains unchanged. The ledger stops at 18 preserved attempts/US$0.6885786 conservative reservations. Full GMA correction, spatial qualification and all seeding remain pending. [Retention/replay operator guide](guides/news-gemini-runtime.md#private-batch-retention-and-offline-inspection). Earlier entries below retain their dated scope.

[Pilot execution and evidence-validation blocker](evaluations/three-article-cloud-pilot-20261022/pilot-execution.md): Philstar is registered, all three inputs/permissions are frozen, and actual GMA NER succeeds with 51 mentions. Thirteen successful Gemini requests are followed by a backend evidence-index rejection. The pilot stops before other articles or flood writes; no events/zones were created. Exact rejected arrays are not retained by the current failed-run handler, so diagnostic retention and evidence repair remain pending. Existing rows and paused/expiry settings are preserved; the same US$1 ledger is stopped with US$0.6481486 conservative reservations. Protected API and desktop/mobile failure/history/scroll/empty-state checks pass. This is not completed seeding.

[Gemini repair and real cloud acceptance](evaluations/three-article-cloud-pilot-20261022/provider-repair.md): schema-only comparison isolates HTTP 400, and the compact response with exact batch IDs/count passes actual provider/backend validation. Matching API v5 serves navlanes.live after protected canary/serving checks; all database fingerprints remain unchanged. Fifty focused tests and seven local/cloud contracts pass. Three original articles remain frozen and unprocessed; news remains paused, expiry OFF and the US$1 ledger stopped pending the article stage. [Pilot inventory and implementation](evaluations/three-article-cloud-pilot-20261022/README.md) · [Earlier no-generation-call investigation](evaluations/three-article-cloud-pilot-20261022/provider-investigation.md).

## Latest Gemini credential attempt — not promoted

[Personal-key rotation and recovery](evaluations/gemini-key-rotation-20261022/README.md): the withdrawn personal credential remains stored as version 3 and unused. API/discovery/manual verification retain original LANES version 2; its later successful acceptance is recorded above. Three-article seeding remains pending; news stays paused and expiry stays OFF.

## Current database state — authorized flood reset completed

[Execution, verification and recovery](evaluations/flood-data-reset-20261022/README.md) · [Counts and hashes](evaluations/flood-data-reset-20261022/summary.json). Flood/history/report/moderation/news-output records are cleared. Preserved all 37 community posts, eight accounts and 174 source articles/224 versions; 34 post/report links detached. Backups restored/rehearsed; 12 guard tests and actual desktop/mobile/API/map/SSE/export checks pass. Public access restored. News processing/scheduling stays paused; old extraction IDs are absent. Earlier delivery records below retain their original pre-reset checkpoints.

## NER → Gemini verification

[Implementation/release plan](plans/ner-gemini-verification.md) · [Operator guide](guides/ner-gemini-verification.md) · [Guarded cloud release and provider blocker](evaluations/ner-gemini-cloud-release-20261022/README.md). Matching backend/readers now serve navlanes.live; the separate manual verification worker reuses the existing key. The single authorized real request returned HTTP 402, so successful provider correction remains unqualified. Sixty current local checks, cloud software contracts, protected hosted APIs and desktop/mobile empty-state/export checks pass. All database fingerprints remain unchanged; news automation stays paused and no articles were seeded. Earlier [297-check local acceptance](evaluations/ner-gemini-verification-20261022/README.md) remains retained; test counts are not additive.

## Completed Part 2A shared execution

[Final release and aggregate evidence](evaluations/news-history-shared-execution-20261022/README.md): 111 full articles / 56 actual cloud batches, all 56 repeated without inference; 33 training publisher outcomes unresolved. All 629 group receipts remain unresolved, so no new archive/polygon was created. Original citizen/event/zone rows are unchanged; hosted counts/filters/source/history/maps/exports agree. Existing frontend source was deployed only for reader compatibility; no UI edits. Manual seed execution disabled; Part 2B remains separate. Earlier preparation snapshots below retain their original dates.

## NER deployment first — separate test package verified locally

**Latest result: the trained NER passes the full isolated Cloud Run qualification.** `lanes-ner-check-nbpmz` independently matches 355 graph/provenance results, 352 retained prediction records and 53 reviewed mentions; all 358 resource snapshots, isolation, timing and clean shutdown pass under the approved cloud profile. Peak memory 2,067.3 MiB (<2,688). The ordinary worker, Cloud SQL, schedules and application remain unchanged; production integration/history seeding are still separate. [Cloud acceptance and evidence](evaluations/ner-cloud-check-20261022/README.md#cloud-acceptance--full-frozen-workload-passed).

[Original local/failed attempts and current cloud acceptance](evaluations/ner-cloud-check-20261022/README.md) · [Operator guide](guides/ner-cloud-check.md). Local software checks: 150 tests and 12 Linux profile cases. Earlier 75/83/103-test checkpoints and both diagnostic executions are retained and are not additive totals. Cloud qualification is complete for the separate inference-only job; connecting the automatic news worker, shared Part 2A seeding, Part 2B and temporary resource cleanup remain separately gated.

## Part 2A — news-derived history and general article seeding

[Implementation, read-only audit and verification](evaluations/news-history-part2a-20261022/README.md): 374 backend passes; 19 desktop/mobile passes with one intentional skip; TypeScript, focused lint and production build pass. Twelve saved full-body articles and 132 training sources are inventoried; shared processing/application remains blocked and unexecuted. [General operator workflow](guides/historical-news-preparation.md#part-2a--general-source-inventory-and-archive-preparation).

## Publisher-body capture corrected before Phase 2

[Fix, tests and prepared September 9 replacement](evaluations/news-publisher-body-capture-20261022/README.md) · [Structured evidence](evaluations/news-publisher-body-capture-20261022/summary.json). GMA standard/AMP body selection excludes page chrome while retaining temporal evidence. September 24 is unchanged. Capture/native regression union: 245 distinct passes plus 13 subtests; the two separately reproduced pre-existing extraction failures were subsequently resolved in Part 2A. With explicit one-article approval, article 47 now uses original-publisher version 140/completed rules-only run 140; old extraction/history remain intact. No UI redesign or flood activation. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## September database cleanup question — inspected read-only

[Current Cloud SQL records, table dependencies and recommendation](evaluations/september-database-reuse-20261022/README.md) · [Structured evidence](evaluations/september-database-reuse-20261022/summary.json). Articles 25/47 retain three versions, ten legacy runs and six ended/inactive event/zone pairs. No native run or historical-import output exists. Immutable publication dependencies and unchanged E0 inputs are confirmed; retaining the records supports separately qualified active September output. No deletion, migration or other cloud write occurred. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Phase 1 — connected local workflow verification

**Latest user amendment:** [unified history restored](evaluations/news-historical-phase1-20261022/README.md#unified-history-amendment). The historical-dataset dropdown is removed; dataset/session tracking remains internal. Existing history filters and event links remain.

[Backend integration and final acceptance record](evaluations/news-historical-phase1-20261022/README.md) · [Operator guide](guides/historical-news-preparation.md#phase-1--saved-output-materialization-and-reading). **Complete locally:** all eight tasks pass with 434 backend checks, 45 desktop/mobile project checks (three intentional skips), TypeScript, focused lint and production build. The final changed-workflow/offline rerun passes 12 checks. The visible demonstration label and added badge/modal presentation are removed as requested. No real September inference, shared/cloud output or deployment. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## October 25 presentation — two active phases

**Phase 2 execution order:** [2A — seed Flood History from saved articles and NER training articles](task_plan.md#part-2a--seed-flood-history-including-ner-training-articles), then [2B — generate September active flood zones and verify deactivation/history](task_plan.md#part-2b--september-articles-for-active-flood-zones). Both shared execution paths remain unexecuted; Part 2A implementation is locally verified.

**Latest scope correction:** [Phase 2 includes existing saved articles in Flood History](task_plan.md#phase-2--deploy-and-demonstrate). The selected September articles are specifically intended for active flood zones; their original historical records remain retained. Other saved articles supply supported Flood History observations. General batch support, source inventory and cross-article reuse are locally verified; shared qualification, actual NER processing/application and deployment remain pending.

[Phase 1 — connect the existing system; Phase 2 — deploy and demonstrate](task_plan.md#october-25-presentation--two-phase-delivery-plan). Completed E0/E1 remains retained; existing extraction, plotting and interfaces are reused. [Technical details](plans/historical-news-demonstration-phase-e.md) and manual UI checks stay linked. This is a planning reorganization only. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## E1 — complete historical processing software delivery

[345 passing checks](evaluations/news-historical-e1-20261022/README.md) · [Aggregate evidence](evaluations/news-historical-e1-20261022/summary.json) · [Current operator guide](guides/historical-news-preparation.md#e1--complete-controlled-historical-processing). Exact-target policy, constrained shared worker, source/date interpretation and existing placement-preview handoff are complete locally. E0 remains unchanged. No cloud processing, September inference, flood publication or UI changes occurred. Next: Phase 1 integration, followed by Phase 2 hosted qualification and demonstration (legacy E2–E6 references below are earlier checkpoints). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## E1.2 — historical operator command verified locally

[227-check verification](evaluations/news-historical-command-e12-20261022/README.md) · [Aggregate](evaluations/news-historical-command-e12-20261022/summary.json) · [Operator command guide](guides/historical-news-preparation.md#e12--manifest-bound-preflight-and-disposable-processing) · [Next E1 task](task_plan.md#e1--connect-controlled-historical-processing). Frozen-package preflight is database-enforced read-only; processing uses exact captures/runs on disposable storage only and preserves failures/leases/completed evidence. E0's real package authenticates unchanged; no real September inference, cloud access, activation or UI change occurred. The cloud-target policy and remaining E1–E6 gates are open. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## E1.1 — maintenance correction verified locally

[82-check verification](evaluations/news-maintenance-e11-20261022/README.md) · [Aggregate](evaluations/news-maintenance-e11-20261022/summary.json) · [Next E1 task](task_plan.md#e1--connect-controlled-historical-processing). Invalid auditor settings no longer block independent due-case expiry; the original configuration error remains visible and scheduler maintenance counts/errors remain separate. Expiry OFF preserves actual fixture zones and history. No frontend/cloud setting change or deployment; next is the manifest-bound historical command. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## E0 — September inputs prepared

[Verified preparation and 27 checks](evaluations/news-historical-e0-20261021/README.md) · [Aggregate evidence](evaluations/news-historical-e0-20261021/summary.json) · [Operator guide](guides/historical-news-preparation.md) · [Completed E0 checklist](task_plan.md#e0--prepare-and-freeze-real-article-inputs). The private manifest binds two exact saved article versions, two native captures, five existing history references and one stable demonstration session. Repeated read-only execution verifies the same package. Quirino/Guazon is primary, Gov. Pascual backup; both still need independent neural/source/geometry acceptance. Publication provenance gaps stay explicit. No inference, cloud write or activation occurred. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Historical presentation and Phase E — detailed plan

**Corrected presentation target:** selected September articles must generate visible active examples on **both public map and Spatial Operations**, with original dates and historical-demonstration labels; other outputs remain historical. The detailed plan includes demo activation/deactivation-to-history and repeat-safe original/demo identities. This supersedes the earlier archive-only interpretation; no example has been activated by these documentation changes.

**September reuse recheck:** [existing cloud article/run/history identities and text comparison](evaluations/news-historical-readiness-20261021/README.md#7-september-record-reuse-and-redundancy-recheck) confirm these articles and ended zones already exist. E0 verifies/reuses them; E2 must match existing incidents before any insertion. A new neural extraction record must not become a duplicate flood event.

[Two-phase delivery checklist](task_plan.md#october-25-presentation--detailed-e0e6-delivery-plan) · [Technical blueprint and acceptance matrix](plans/historical-news-demonstration-phase-e.md) · [Planning milestone](progress.md#historical-presentation-and-phase-e--detailed-delivery-plan-documented). The plan targets the existing hosted system with authenticated saved articles, reused NER/OSM/NOAH services, selected active demonstration examples plus historical persistence, explicit date/demo/assumption semantics, Phase E interface integration and qualified cloud rehearsal. It selects no database reset for this delivery. E0/E1 and Phase 1 are verified locally; Phase 2 remains pending. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Historical news presentation — readiness review

[Review, 54 component checks, spatial assets and read-only cloud findings](evaluations/news-historical-readiness-20261021/README.md) · [Agreed requirements and next planning task](task_plan.md#october-25-presentation--review-complete-detailed-implementation-plan-next) · [Completed-work checkpoint](progress.md#historical-news-demonstration--readiness-review-complete). Existing captured articles and OSM/NOAH services are the selected path to historical results on the existing hosted system. Detailed import/reset/date semantics and Phase E/cloud acceptance remain unfinished; the Phase D maintenance finding is subsequently fixed locally in E1.1, with cloud release still pending. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Current spatial/history delivery checkpoint

[Progress summary](progress.md#spatial-operations-and-flood-history--branch-delivery-checkpoint) · [Remaining acceptance tasks](task_plan.md#spatial-operations-and-complete-flood-history-performance--implemented-acceptance-qualified). The requested `roi-branch` handoff includes stricter 50 m original-geometry grouping, all-history 20-card browsing, shared map presentation, camera-only zone navigation and coordinated bounded reads. The latest camera fix passes four desktop/mobile browser checks, TypeScript and focused lint. Scale latency/mobile stress and overview visual acceptance remain open. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Spatial Operations and complete Flood History browsing

[Approved performance plan](plans/spatial-history-performance.md) · [Implementation, 1,000/10,000-record measurements and acceptance limits](evaluations/spatial-history-scale-20261021/README.md). Smaller batched reads, exact indexed grouping, complete SQL-paged historical cards, bounded map responses and paged inspection. Local implementation is delivered; dense grouping/mobile, cold/concurrent latency and overview visual acceptance remain explicitly qualified. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Flood Event Records map consistency

[Equal columns, shared Needs Review styling, historical heatmap data and verification](evaluations/flood-history-map-20261021/README.md). Preserves saved footprints, historical filters, individual evidence and routing separation. Verified locally with 72 backend and 23 desktop/mobile Chromium checks; one desktop mobile-only skip. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Shared Spatial Operations queues — verified locally

[Grouped Active Zones, shared controls and acceptance limits](evaluations/spatial-zone-queues-20261021/README.md). 73 backend and 34 distinct desktop/mobile browser checks pass. Needs Review rules, individual zone actions and ungrouped history are preserved. No schema/dependency change or hosted deployment. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Chris frontend integration — verified locally

[Scope, preservation checks and local verification](evaluations/chris-integration-20261021/README.md). The reviewed Chris commit integrates without conflicts: 41 desktop/mobile browser checks pass, with three desktop mobile-only skips. The local merge includes the touch-dialog focus fix and preserves completed backend/NER work. No backend, schema, NER activation or cloud change. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Phase D — backend monitoring passed locally

[Implementation, API contracts and cloud disposition](evaluations/rss-ner-monitoring-20261021/README.md) · [Aggregate](evaluations/rss-ner-monitoring-20261021/summary.json) · [Roadmap](task_plan.md#phase-d--correct-monitoring-and-error-classification).

**608 distinct tests pass, including 21 new checks**, plus inference-free parity on 788 cached inputs / 407 saved graphs. Source eligibility/selection/retrieval, independent article retrieval filters, truthful counters, safe configuration failures and the last ten worker attempts are available in backend contracts. The dated cloud retry is reconciled; its original collection error is not retained in logs and is not claimed repaired. All 9,796 predecessor receipt files remain unchanged. **Next: Phase E interface**, including visible monitoring corrections. No frontend, neural inference, migration, dependency, cloud write/deployment or production activation. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**Earlier checkpoints below are historical.**

## NER documentation for groupmates

Start with the [NER development, dataset and evaluation guide](guides/ner-groupmate-handoff.md): how the model was created, annotation structure, 345/60/60 data tables, training configuration, precision/recall/F1 results and limitations. The [branch-content review](evaluations/ner-handoff-review-20261021/README.md) records pending push scope, evidence dependencies and the checks performed for this handoff.


## Phase C3b — controlled RSS-to-NER backend integration passed locally

[Implementation and verification report](evaluations/rss-ner-rss-integration-20261021/README.md) · [Aggregate](evaluations/rss-ner-rss-integration-20261021/summary.json) · [Current roadmap](task_plan.md#phase-c--connect-automatic-article-processing).

**754 distinct checks pass**, plus retained replay, Linux preflight/eight fault probes and one one-CPU / 3-GiB real-model attempt. Eight mocked-RSS articles and two pre-existing short capture controls complete; all 4,483 spans/53 reviewed predictions match, duplicate inference is zero and peak memory is 2,492.09 MiB. Native evidence/readers and downstream gates work locally; historical publication stays paused. Production scheduling remains legacy, and frontend work has not started. **Next: Phase D monitoring, then Phase E interface and Phase F 403 investigation.** Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**Earlier checkpoints below are historical.**

## C3a review follow-up — bounded CLI startup errors

[Verification and separate CLI source-delta record](evaluations/rss-ner-cli-bootstrap-20261020/README.md): 16 focused checks pass, including nine fresh-interpreter cases. Settings/import/cancellation failures now produce bounded process output. Historical qualification receipts remain unchanged; frontend and automatic-processing work remain pending.

**Earlier checkpoints below are historical.**

## Phase C3a — native runtime/queue boundary passed locally

[Implementation and verification report](evaluations/rss-ner-native-worker-20261020/README.md) · [Current roadmap](task_plan.md#phase-c--connect-automatic-article-processing).

Native capture, lazy runtime reuse and owned durable completion pass **251 checks**, Linux preflight and eight fictional subprocess probes. The single one-CPU / 3-GiB attempt completes ten retained inputs with exact 4,483-span/graph/projection parity and no duplicate inference. [Aggregate](evaluations/rss-ner-native-worker-20261020/summary.json). Automatic processing, full Phase C and cloud release remain gated.

**Earlier checkpoints below are historical.**

## Phase C2 — native projection and source evidence

[Implementation and verification report](evaluations/rss-ner-native-projection-20261020/README.md) · [Ordered roadmap](task_plan.md#phase-c--connect-automatic-article-processing).

The new isolated backend adapter preserves exact captured evidence and translates supported observations through `ner-claim-projection-v1`, with separate `source-ner-v1` checking. **C2 is complete locally:** 225 checks, 355 retained outputs, 352 exact prediction records, all 53 reviewed predictions and 788-input / 407-graph parity pass; prior artifacts remain unchanged. [Aggregate](evaluations/rss-ner-native-projection-20261020/summary.json). Automatic NER, native evaluator activation, UI, shared/cloud changes and deployment remain gated.

**Earlier checkpoints below are historical.**

## Current RSS-to-NER integration — Phase C1 compatibility boundary delivered

[93-check report](evaluations/rss-ner-method-boundary-20261020/README.md) · [Aggregate](evaluations/rss-ner-method-boundary-20261020/summary.json) · [Ordered Phase C tasks](task_plan.md#phase-c--connect-automatic-article-processing).

Explicit methods isolate queue claims and saved-history serialization preserves native details without coercing them to legacy output. Unsupported versions fail visibly; scalar card/evaluation consumers remain closed to native data. **Phase C is in progress:** projection/source checking, runtime/queue integration, RSS admission and end-to-end acceptance are pending. Default writes remain `rules_only`. No inference, new migration, shared/cloud change, UI change or deployment occurred. Prior runtime/schema receipts remain preserved.

**Earlier checkpoints below are historical.**

## Current RSS-to-NER integration — schema foundation verified locally

[Schema verification report](evaluations/rss-ner-mode-schema-20261020/README.md) · [Aggregate](evaluations/rss-ner-mode-schema-20261020/summary.json) · [Approved proposal and rollback rules](plans/rss-ner-processing-mode-schema-proposal.md) · [Current Phase C roadmap](task_plan.md#phase-c--connect-automatic-article-processing).

The approved minimal model/check migration permits `ner_rules_v1` alongside `rules_only`, with one new head `e8a6f1c2d903`. **66 local checks pass**, covering migration, legacy preservation, native-row downgrade refusal, lock contention and publication/queue regressions. Both runtime failures and the passing three-GiB qualification are preserved; the authorized current model-line delta is recorded separately. **Next: Phase C integration.** Writers remain legacy; no automatic NER wiring, inference, shared/cloud migration or deployment occurred.

**Earlier checkpoints below are historical.**

## Current RSS-to-NER integration — local Phase B passes at 3 GiB

[One-CPU / 3-GiB qualification](evaluations/rss-ner-runtime-phase-b-3g-20261020/README.md) · [Aggregate](evaluations/rss-ner-runtime-phase-b-3g-20261020/summary.json) · [Runtime guide](guides/ner-subprocess-runtime.md) · [Current roadmap](task_plan.md#phase-b--qualify-the-production-inference-runtime) · [Schema proposal — approval pending](plans/rss-ner-processing-mode-schema-proposal.md).

The explicitly authorized frozen local attempt completes all 355 requests and matches 352 retained neural records, including all 53 reviewed-article predictions and its full saved graph. Peak container consumption is 1,972.21 MiB, below 2,688 MiB; performance, cleanup, 31 constructed checks, eight real failure probes and independent verification pass. Both earlier failed profiles and the runtime/model/rules remain unchanged. **This is a local pass, not Cloud Run/deployment approval.** Next is separate schema approval and Phase C controlled integration; no automatic-processing/schema/cloud change occurs here. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Current RSS-to-NER integration — 2-GiB follow-up fails headroom

[One-CPU / 2-GiB outcome](evaluations/rss-ner-runtime-phase-b-2g-20261020/README.md) · [Aggregate](evaluations/rss-ner-runtime-phase-b-2g-20261020/summary.json) · [Runtime guide](guides/ner-subprocess-runtime.md) · [Current roadmap](task_plan.md#phase-b--qualify-the-production-inference-runtime).

The authorized local follow-up completed the 100,000-character case, but reached 2,048 MiB against a below-1,792-MiB requirement. The guard stopped before the reviewed article; the loaded worker shut down cleanly. All 351 completed saved neural comparisons and 354 graphs match; 25 constructed and eight real fictional fault checks pass. Phase B remains open. The original failure, runtime/model/rules and Google Cloud settings are preserved; no further resource escalation or automatic wiring occurred. A 3-GiB local profile is only a proposed next decision. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Current RSS-to-NER integration — Phase B memory gate failed

[Phase B measured outcome](evaluations/rss-ner-runtime-phase-b-20261020/README.md) · [Supervised runtime guide](guides/ner-subprocess-runtime.md) · [Aggregate verification](evaluations/rss-ner-runtime-phase-b-20261020/summary.json) · [Current roadmap](task_plan.md#phase-b--qualify-the-production-inference-runtime).

The isolated runtime is implemented; its single frozen one-CPU / 1-GiB attempt completed 345 training passages, six articles and two stress cases before the maximum-length case caused OOM. All 351 completed passage/article predictions and 353 graphs reconcile; 788 cached inputs / 407 saved graphs also match. Phase B remains open. A separate resource decision precedes another qualification attempt; no retry, resource increase, automatic wiring, schema, cloud or interface change occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Current RSS-to-NER integration — Phase A contract delivered

[Integration contract and acceptance matrix](plans/rss-ner-integration-contract.md) · [Processing-mode schema proposal — approval pending](plans/rss-ner-processing-mode-schema-proposal.md) · [Ordered roadmap](task_plan.md#current-milestone-rss-to-ner-integration-and-news-intelligence).

Phase A defines candidate capture versus flood eligibility, immutable native NER results, conservative legacy projection, source-checking and reader compatibility, correction handling, and 23 future acceptance scenarios. It preserves the full v19/v40/v44/v42 graph and exposes facts that cannot be projected safely. The separate proposal adds only an allowed `ner_rules_v1` processing mode to the current database check; no model/migration edit is approved or delivered. **Next: Phase B runtime qualification.** Automatic durable NER processing, interface changes and production release remain pending. Documentation/source inspection only; no inference, tests, database or cloud changes in this delivery. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V46 backend location integration — complete; interface next

[Approved plan](plans/ner-backend-location-repairs-v46.md) · [Outcome](evaluations/flood-ner-backend-location-v46-20261020/README.md) · [Metrics](evaluations/flood-ner-backend-location-v46-20261020/metrics.json) · [Independent verification](evaluations/flood-ner-backend-location-v46-20261020/verification.json) · [Backend guide](guides/ner-backend-preview.md).

The selected combined repairs are connected through the existing backend preview. 1,281 tests, 788 cached inputs / 407 graphs / 418 applicable cases / three paired checks and one real isolated-worker API request pass. Original predictions, source link and v1 fields remain intact; chain/graph tampering fails closed. Flag remains disabled by default. Next plan the admin interface. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V45 scoring reassessment — completed; qualified views remain offline

[Plan](plans/ner-location-scoring-v45.md) · [Outcome](evaluations/flood-ner-location-scoring-v45-20261020/README.md) · [Metrics](evaluations/flood-ner-location-scoring-v45-20261020/metrics.json) · [Independent verification](evaluations/flood-ner-location-scoring-v45-20261020/verification.json) · [Guide](guides/ner-location-scoring-v45.md).

Strict serialized scoring and separate original/repaired checks pass. Missing-junction, boundary-replacement and combined views qualify for later proposals; type correction lacks real correction evidence. All 418 applicable cases and three conditional pairs pass per method, with 176 software tests. Saved article gains remain eight occurrences / 40 facts, with 11 unresolved rows. No extraction, inference, worker rerun or backend promotion; historical v44 remains unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V44 location study — completed; acceptance blocked

[Approved design](plans/ner-location-repair-v44.md) · [Outcome](evaluations/flood-ner-location-repair-v44-20261020/README.md) · [Frozen metrics](evaluations/flood-ner-location-repair-v44-20261020/metrics.json) · [Independent verification](evaluations/flood-ner-location-repair-v44-20261020/verification.json) · [Scorer diagnostic](evaluations/flood-ner-location-repair-v44-20261020/scoring-diagnostic.json) · [Evidence guide](guides/ner-location-repair-v44.md).

One 788-input study completes. Combined proposals correct eight article occurrences and restore 40 facts; 11 rows remain unresolved. The frozen scorer serialization defect and three preserved fixture conflicts block qualification. Independent saved-output checks preserve the original scores; no backend promotion or model/rule tuning follows. Next separately qualify scoring and original-control/repaired-view contracts. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Location recognition assessment — current checkpoint

[Assessment, case accounting and recommended study](evaluations/flood-ner-recognition-gaps-20261020/README.md) · [Aggregate verification](evaluations/flood-ner-recognition-gaps-20261020/verification.json).

Nineteen unresolved rows contain 34 target occurrences: 17 missing, three boundary errors, one incompatible type and 13 individually consumer-compatible spans. All 93 affected facts are retained unassigned. No model, rules, references or application behavior changed. Next is a separately frozen location-proposal study, retaining meaning/type uncertainties. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V42 extraction repair — current checkpoint

[Approved design](plans/ner-context-repair-v42.md) · [Executed outcome](evaluations/flood-ner-context-repair-v42-20261019/README.md) · [Metrics](evaluations/flood-ner-context-repair-v42-20261019/metrics.json) · [Independent verification](evaluations/flood-ner-context-repair-v42-20261019/verification.json) · [Operator guide](guides/ner-context-repair-v42.md).

Bounded acceptance passes after one 371-input isolated comparison. Five complete junctions, list clock/access/caution and dateline handling pass; 18 measured rows remain recognition-limited. All 120 old contextual view sets remain intact. V42 is promoted to the default-disabled local backend; 1,195 post-promotion tests pass. No model inference, proposal regeneration, database access, frontend or plotting change. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Saved-article source link and extraction review — current checkpoint

[Source review and next repair recommendation](evaluations/flood-ner-saved-article-review-20261019/README.md) · [Aggregate receipt](evaluations/flood-ner-saved-article-review-20261019/verification.json) · [Backend guide](guides/ner-backend-preview.md).

The backend now returns the saved article URL. 379 preview checks and one actual read-only database/API/worker check pass. Source review finds full-article extraction gaps despite the successful connection: equivalent-depth/junction pairing, list clock/access context, dateline scope and missing/incomplete locations. No model/rule, frontend or plotting change. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Extraction-only backend preview — current checkpoint

[Backend specification](plans/ner-extraction-only-backend-preview.md) · [Local verification and limits](evaluations/flood-ner-backend-preview-20261019/README.md) · [Aggregate receipt](evaluations/flood-ner-backend-preview-20261019/verification.json) · [Operator guide](guides/ner-backend-preview.md).

Implemented a default-disabled, local, active-admin saved-article preview returning grouped facts/evidence and separate neural/rule provenance. 798 checks, nine real-worker API responses, six article neural parity checks and 120 context-view comparisons pass. A planned config change is reconciled explicitly; frozen research/evidence and excluded metadata remain intact. No frontend, durable history, map or normal-processing change. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V41 context repair — current checkpoint

[Bounded acceptance and remaining limitations](evaluations/flood-ner-context-repair-v41-20261019/README.md) · [Metrics](evaluations/flood-ner-context-repair-v41-20261019/metrics.json) · [Independent verification](evaluations/flood-ner-context-repair-v41-20261019/verification.json) · [Read-only guide](guides/ner-context-repair-v41.md).

All 36 old temporal, 36 new regression and 238 preserved context cases pass. Combined cached proposals recover six of seven old links, with 104 TP / zero FP / one FN on unchanged training references. The non-flood access miss, three reference holds and language/evaluation limitations remain. No system connection or model/location-rule change occurred. Next separately scope extraction-only backend integration; passing this task is not deployment approval. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V40 offline location-repair study — current checkpoint

[Outcome, time semantics and next task](evaluations/flood-ner-location-repair-20261019/README.md) · [Metrics](evaluations/flood-ner-location-repair-20261019/metrics.json) · [Independent verification](evaluations/flood-ner-location-repair-20261019/verification.json) · [Read-only operator guide](guides/ner-location-repair-v40.md).

One frozen 679-input study completed. Transport proposals recover four old links; shared locality introduces one scope error; unchanged time rules pass 29/36 new checks. No complete method qualifies for connection. No neural inference/training, validation/holdout content, reference changes or database/map changes. V19 and 345/60/60 remain unchanged. Next separately scope temporal-role and collective-association repairs. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Remaining extraction-gap assessment — current checkpoint

[Assessment, case accounting and recommended next task](evaluations/flood-ner-extraction-gap-assessment-20261019/README.md) · [Saved-evidence verification](evaluations/flood-ner-extraction-gap-assessment-20261019/verification.json).

Seven missed associations involve three target occurrences: two mistypes and one missing mention. All three reference holds remain held and pure-Tagalog real performance remains unmeasured. The review is complete; recognition repair and LANES connection are not delivered. Next separately scope recognition feasibility with downstream recovery checks. No new inference, training, reference changes or validation/holdout content. Learned DEPTH/TIME remains unfinished. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V38 fixed-reference repair — contextual gate passed, connection blocked

**Four incorrect links removed; eight contextual misses recovered**, including the lost baseline-correct status. One frozen Linux comparison processed 24 unchanged training inputs + 238 fictional cases. All **238 cases and 1,158 fresh affected tests (298 new)** pass. References, model and 345/60/60 membership remain unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Fixed-reference result: 98 TP / zero FP / seven FN; 96.55% association F1**, versus saved v37's 90.45% on the same 23 silver training references. All 90 v37-correct, 14 original-rules-correct and 70 mapped associations are retained. No new strict DEPTH/TIME span errors or qualifier losses. This exposed training-subset result is not independent system accuracy.

**Next gate:** separately assess seven missing/mistyped-neural-target links, three reference holds and unmeasured real-world Tagalog performance before proposing a read-only LANES demonstration. Contextual repair passes; overall connection remains blocked. Learned DEPTH/TIME stays unfinished. No new data, neural inference, training, integration, upload, commit or push occurred. [Outcome](evaluations/flood-ner-context-fixed-links-20261019/README.md) · [Metrics](evaluations/flood-ner-context-fixed-links-20261019/metrics.json) · [Verification](evaluations/flood-ner-context-fixed-links-20261019/verification.json) · [Guide](guides/ner-context-association-v38.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V37 grouping clarification and repair — complete, acceptance blocked

**Current stage remains offline context acceptance.** A uniform source-only review froze 14 retained/nine corrected proposals, all 168 entities and three prior holds unchanged. All 103 old relations and 70 previously correct associations are mapped. One frozen Linux successor processed **24 unchanged real inputs + 208 fictional cases**. All 208 cases and **860 fresh affected tests (299 new)** pass. No post-result tuning or retry occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Revised-reference result:** **90 TP / four FP / 15 FN; 90.45% association F1**. All 70 pre-frozen source-supported mappings and all 61 revised-reference v36-correct links are retained. One additional original-rules-correct local status under revised references is missed, so retention and zero-incorrect gates fail. Seven misses require absent/mistyped neural targets; eight are contextual omissions. TIME-span checks introduce zero FP/FN and recognition F1 is 95.65%. These are exposed silver training-subset results, not independent accuracy or learned DEPTH/TIME performance.

**Reference encodings stay separate:** saved v36 scores 66.67% and the successor 90.45% on the clarified references; under unchanged v36 references the successor scores **69.74%**, versus saved v36's 78.21%. Representation revisions are not model improvement. The isolated review's incidental generic-code/filename exposure is recorded; no actual prediction/output/score data was exposed. Pure-Tagalog real performance remains **unmeasured** despite 48 passing Tagalog fixtures.

**Next proposal:** separately repair the four wrong links and eight contextual misses, including the lost baseline-correct status; keep seven recognition-dependent misses and three contextual holds explicit. No LANES connection is cleared. Preserve **345/60/60**, trained models and completed holdout exclusion. Learned DEPTH/TIME remains unfinished; no new data, neural inference, training, integration, upload, commit or push occurred. October 25 readiness is unestablished. [Outcome](evaluations/flood-ner-context-grouping-20261019/README.md) · [Metrics](evaluations/flood-ner-context-grouping-20261019/metrics.json) · [Verification](evaluations/flood-ner-context-grouping-20261019/verification.json) · [Guide](guides/ner-context-association-v37.md) · [Representation](plans/ner-context-representation-v37.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V36 comprehensive association review — task complete, connection blocked

**Current stage: offline flood-context acceptance.** Runtime qualification and the location-only shadow comparison are complete; the association method is still not cleared for a LANES connection. One frozen successor processed **24 real training inputs + 160 fictional cases**. All 160 behavior cases pass; **561 fresh affected tests pass (295 new)**. Independent review retained 14/corrected nine proposals and preserved all three holds. All **13 incorrect + 43 missed** old links have evidence-bound dispositions. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Real result:** eight incorrect / 31 missed associations on 23 revised references, **78.21% association F1**. All 48 revised-reference v35-correct links are retained and 22 are gained. On unchanged v35 references, successor F1 is 78.11%; reference revisions are reported separately. There is **one newly introduced wrong link versus v35** despite six removed. TIME expression recognition declines to 84.00% F1, so aggregate association gains do not mean every component improved. Seven misses require absent exact neural targets. Passing fixtures does not override the zero-total-incorrect gate or the three reference holds.

**Language scope:** all software checks pass (English 64, Tagalog 32, Taglish 64); real references are English/Taglish only. Pure-Tagalog empirical/neural performance remains **unmeasured**, with AI-assisted language/borrowing uncertainty. Preserve **345/60/60**, saved six-class model mentions and completed holdout exclusion. Learned DEPTH/TIME remains unfinished; no neural inference, training or integration ran. No post-result tuning occurred.

**Next proposal:** separately address the eight wrong resolved links, the remaining code omissions, required missing neural targets and contextual holds. Freeze any later repair before another authorized comparison; do not silently add/resize/retag mentions or introduce fallback. A read-only LANES demonstration and its language limitations remain a later gate, not automatic next execution. October 25 readiness is unestablished. [Outcome](evaluations/flood-ner-context-three-language-20261019/README.md) · [Metrics](evaluations/flood-ner-context-three-language-20261019/metrics.json) · [Verification](evaluations/flood-ner-context-three-language-20261019/verification.json) · [Operator guide](guides/ner-context-association-v36.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## V35 source-only review and repair checkpoint — acceptance remains open

**Review-first v35 task complete; read-only LANES connection is not qualified.** An isolated source-only reviewer froze nine retained / fourteen corrected / one newly held contextual proposals; two earlier holds remain unchanged. Schema/frozen-tokenizer qualification passes. One candidate worker processed 24 raw training passages plus 64 fictional inputs. **64/64 behavior cases pass; 39 correct links gained, zero supported baseline-correct links lost, seven introduced strict disagreements on 23 revised references.** All 46 revised-reference v34-correct links and all 40 previously original-reference-correct links are retained. **470 fresh tests pass (111 new)**. No post-result tuning occurred.

**Next proposal:** narrowly repair recession-time precedence and collective/gauge semantics, with independent source-only disposition of remaining status-reference coverage questions before another freeze. Preserve the three contextual holds, original and revised score reports, all 345/60/60 membership and completed holdout exclusion. No LANES connection, new data or retraining is authorized by this failed gate. Learned DEPTH/TIME remains unfinished; October 25 readiness is unestablished. [Outcome](evaluations/flood-ner-context-repair-20261019/README.md) · [Metrics](evaluations/flood-ner-context-repair-20261019/metrics.json) · [Verification](evaluations/flood-ner-context-repair-20261019/verification.json) · [Operator guide](guides/ner-context-association-v35.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Offline context association checkpoint — not qualified

**Offline association implementation and one comparison are complete; acceptance failed.** All 24 eligible training proposals and 40 fictional cases were processed with references outside extraction; the two held records remain unscored. **36/40 behavior cases pass; 34 correct links gained, zero baseline-correct links lost and 20 new strict silver-reference disagreements.** Those disagreements include demonstrated scope/time errors and separately recorded reference/grouping concerns; none was relabeled or hidden. **277 fresh tests pass (61 new)**; a broader timed-out test attempt remains incomplete. No empirical retuning occurred.

**Next proposal:** separately repair clause/time updates, collective/list scope and nearby-facility abstention, and independently resolve the recorded reference questions. Freeze a successor before a separately authorized comparison. **Read-only LANES connection is not cleared.** Preserve 345/60/60, the two holds and completed holdout exclusion; no retraining/new data is needed for this repair proposal. Learned DEPTH/TIME remains unfinished; October 25 readiness is unestablished. [Outcome](evaluations/flood-ner-context-association-20261019/README.md) · [Metrics](evaluations/flood-ner-context-association-20261019/metrics.json) · [Final package hashes](evaluations/flood-ner-context-association-20261019/package-hashes.json) · [Four additional monitor checks](evaluations/flood-ner-context-association-20261019/monitor-verification.json) · [Verification](evaluations/flood-ner-context-association-20261019/verification.json) · [Operator guide](guides/ner-context-association.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Current interim acceptance package

[Acceptance-package outcome](evaluations/flood-ner-context-acceptance-20261019/README.md) · [Frozen specification](plans/ner-interim-context-acceptance.md) · [Verification](evaluations/flood-ner-context-acceptance-20261019/verification.json) · [Operator guide](guides/ner-interim-context-acceptance.md).

The user selected the temporary hybrid demonstration priority. All 26 training counterparts have proposed dispositions (20 retain / four corrected / two held); 40 fictional cases are frozen. **753 fresh tests pass (94 new)** and reference/tokenizer qualification passes. Next is offline association repair/testing using saved training-only location predictions, before any read-only LANES connection. Learned DEPTH/TIME remains unfinished; no new data, inference, training or integration ran. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier review checkpoints below are historical; later proposals do not overwrite their references or findings.**

## Current contextual audit

[Existing depth/time/association gap report](evaluations/flood-ner-context-gaps-20261019/README.md) · [Aggregate verification](evaluations/flood-ner-context-gaps-20261019/verification.json) · [Audit operator guide](guides/ner-context-gap-audit.md).

All 405 records are inventoried; one guarded rules pass completed. Only 26 training records have exact contextual counterparts: 21 support limited diagnostics and five remain held. All 60 validation records lack matching contextual references. The next proposed task is a fixed contextual annotation/association specification and source-bound reference completion on existing texts. Learned DEPTH/TIME and live integration remain unfinished; no new data or training ran. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier scope clarification below records the requirement; its documentation-only activity is historical.**

## Current NER scope checkpoint

Read the [current task-plan scope/defense checkpoint](task_plan.md#current-ner-scope-and-defense-checkpoint) and [detailed requirements/deadline status](plans/lanes-ner-training-plan.md#current-requirements-and-deadline-status). The original learned location/DEPTH/TIME goal remains unfinished. V19 learns six location labels; depth/time rules are separate. A hybrid before October 25 is recommended, not a permanent cancellation or an accepted postponement of additional training. This update changes documentation only. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier execution checkpoints below are historical.**

**Repaired offline location comparison completed.** One explicitly authorized new Linux attempt processed all **six saved training articles and eight fictional cases**. Independent verification reconciles every input/hash, Unicode span, label and comparison count. Startup **5.688 s**, slowest input **0.666 s**, peak worker RSS **450.79 MiB** and wall time **9.206 s** all pass unchanged limits. The previous failed attempt, source bindings and claim are preserved; its verified stopped-owner lock was archived. The successful attempt is stopped and its active lease is cleared. [Executed outcome](evaluations/flood-ner-shadow-execution-20261019/README.md).

**Next:** separately design and test how location mentions associate with clause-local flood status, time, depth and uncertainty. No live processing is connected. Preserve all **345 training / 60 validation / 60 research-holdout passages**; no new data, retraining or validation/holdout evaluation occurred. The 604 passing software checks remain preparation evidence; this task adds actual execution and independent verification, with no source change or suite rerun. [Operator guide](guides/ner-shadow-comparison.md).

**Earlier dated checkpoints below are historical.**

**Offline location shadow adapter implemented; comparison execution remains pending.** The single Linux attempt stopped during startup before processing any article. An ORM-import/engine-construction conflict is reproduced with a constructed probe. The repaired offline import boundary passes **604 checks / 62 new checks** and read-only preparation verification, but has not been rerun in Linux. Failed receipts, original source bindings, stopped container and lease remain preserved; no automatic retry occurred. [Outcome](evaluations/flood-ner-shadow-comparison-20261019/README.md).

**Next:** explicitly reconcile the stopped failed attempt and execute one new offline comparison with the repaired grant and an absent destination. Only after that comparison completes should claim-context integration be scoped. Gate 3 remains passed for its earlier frozen Linux profile; the shadow-comparison gate is still open. No new data, training, validation/holdout evaluation or live connection occurred. Membership remains **345/60/60**. [Operator guide](guides/ner-shadow-comparison.md).

**Earlier dated checkpoints below are historical.**

**Gate 3 Linux CPU qualification passes for the frozen local profile.** Retained v19 control seed 0 runs in the unchanged backend image on Linux/Python 3.12.15/spaCy 3.7.5. All 345 saved training predictions match exactly; tokenizer parity, runtime limits and eight executed fictional fault-containment checks pass. **475 fresh regressions pass**, including 82 versioned-runner checks. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Measured:** cold readiness 4.078 s, passage p95 36.23 ms, slowest selected article 0.507 s, 100,000-character stress 5.368 s and peak worker RSS 1.839 GiB under two CPUs / 4 GiB. These are single-worker local measurements, not deployment performance or improved accuracy. All 633 protected file hashes and stat-only validation/holdout entries remain unchanged. V19 and 345/60/60 membership are unchanged.

**Next:** separately implement the read-only shadow adapter. No retraining, new data, completed-holdout evaluation or live connection is needed for this next scope. Keep context/evidence/placement gates; durable neural processing remains separately gated by the existing `rules_only` database constraint. The desktop GPU can remain off.

[Linux execution and qualification](evaluations/flood-ner-linux-execution-20261019/README.md) · [Runtime guide](guides/ner-runtime-qualification.md). No production API, dependency or schema changes; no integration, deployment, upload, commit or push.

**Earlier dated checkpoints below are historical.**

**Clean-launch task stopped at failed graceful exit.** One normal Docker Desktop stop timed out and reported failure; six Desktop/backend processes remain, while its WSL distribution is stopped. The Linux API is unavailable. **No independent Start-menu launch occurred**, so the launch-environment hypothesis and ordinary PowerShell connectivity remain untested. Gate 3 is open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next user action:** use Docker Desktop's normal **Quit** action (tray menu or error-window Quit), then report that it has closed. Verify process exit before one independent Windows Start-menu launch. No force-stop, reset, update, socket cleanup or reboot is authorized. Stop before image builds or model execution.

[Clean-launch outcome](evaluations/flood-ner-docker-clean-launch-20261019/README.md) · [Runtime guide](guides/ner-runtime-qualification.md). All 564 protected hashes and stat-only validation/holdout entries remain unchanged. No new software tests ran; the prior 393-pass result remains historical. V19 and 345/60/60 membership are unchanged.

**Earlier dated checkpoints below are historical.**

**Linux qualification attempted: blocked before image build.** Docker's backend records an inaccessible `sailor-ingest.sock` rename, its Linux API is absent and WSL reports the engine stopped. Normal start reports already running; the single restart attempt did not return a completed receipt and was interrupted. No reset, socket deletion, reinstall, security change or reboot occurred. **Gate 3 remains open; compatibility and performance are unmeasured.** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Delivered:** separate Linux measurement helpers, an authenticated raw-only projection of all 345 training records with expected predictions kept separate, frozen local limits and **393 fresh passing regressions / 71 new Linux checks**. These are constructed tests, not a Linux execution. The full article-use workload and actual operational fault/restart qualification remain pending. V19 control seed 0 and 345/60/60 membership remain unchanged.

**Next:** restore normal Docker Desktop startup on the laptop, then resume this qualification scope: supported article workload, pinned image, parity, latency/RSS and operational failure checks. Do not move to the shadow adapter until evidence passes. No retraining, new data or completed-holdout reuse is needed; the desktop GPU can remain off.

[Linux outcome](evaluations/flood-ner-linux-qualification-20261019/README.md) · [Operator guide](guides/ner-runtime-qualification.md). No Linux inference, production connection, deployment, upload, commit or push.

**Earlier dated checkpoints below are historical.**

**Gate 3 runtime preflight completed; Linux qualification remains blocked.** The retained v19 control seed-0 checkpoint (11 files) and pinned resources (23 files) authenticate. Existing Windows/Python 3.12.14/spaCy 3.7.5 CPU inference passes four fictional probes and 40 warm calls with deterministic predictions and frozen-tokenizer parity. Docker's Linux engine is unavailable; Linux inference, representative article latency, peak RAM and failure/restart qualification remain pending. **Gate 4 live integration has not started.** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** finish isolated Linux CPU qualification, then separately implement a read-only shadow adapter. The [integration design](plans/ner-v19-shadow-integration.md) preserves context/placement gates, original-body offsets and six-class mapping. Durable processing currently has a `rules_only` database constraint; do not bypass it. No retraining, data collection or completed-holdout reuse is needed. The desktop GPU can remain off.

[Runtime preflight report](evaluations/flood-ner-runtime-preflight-20261019/README.md) · [Operator guide](guides/ner-runtime-qualification.md). Fresh **322 tests pass, including 54 new runtime checks**. V19 remains retained; 345/60/60 membership is unchanged. No dependency installation, production connection, upload, commit or push.

**Earlier dated checkpoints below are historical.**

**Training-only road-boundary study completed: no qualifying rules.** Trimming and explicit crossing separation pass fictional checks, but all 345 original control prediction records remain unchanged. Descriptor trimming abstains twice; directional trimming and explicit splitting have no observed corrective applicability. Both families are partially supported and empirically unproven. **V19 corrected control seed 0 remains retained.** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current disposition:** close this bounded feasibility study without a validation comparison or integration proposal. An empty qualifying subset is not evidence of improvement; do not tune rules from exposed findings or combine rejected prototypes automatically. Any future development direction requires a separate scope. The desktop can remain off.

[Boundary study](evaluations/flood-ner-road-boundaries-20261019/README.md) · [Boundary operator guide](guides/ner-road-boundary-study.md). All seven training ROAD-error records and five complete saved articles were reviewed. Fresh **269 tests** pass, including **71 new checks**; 24 fictional core cases remain outside membership. Ten replay files reproduce byte-for-byte. Protected 507 hashes, prior-validation metadata and 55 stat-only holdout entries remain unchanged; no validation or holdout content was supplied to this study.

**Earlier dated checkpoints below are historical.**

**Frozen validation comparison completed: retain v19 corrected control, seed 0 primary.** The two-rule shadow method increases strict validation F1 from 71.60% to 76.54% on unchanged 60 validation passages, but **does not qualify** under the prospectively frozen zero-new-strict-FP gate. Four correct entities are gained, none lost; five typed FPs are resolved and one typed FP is introduced when an already-truncated road span changes type but remains incomplete. No new textual entity or boundary is added. References, model selection and the prototype remain unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current disposition:** keep the prototype separate from production and close this bounded comparison. Any future method, revised policy or integration proposal needs a separate scope; no automatic rule tuning, retraining or completed-holdout evaluation follows. The desktop can remain off.

[Validation comparison](evaluations/flood-ner-context-validation-20261019/README.md) · [Validation operator guide](guides/ner-context-safeguard-validation.md). All 60 records are accounted for; three changed passages and complete saved articles were reviewed. Fresh **250 tests** pass, including **52 new checks**. One comparison consumed one persistent claim; no replay or retry occurred. Protected 505 hashes and 55 stat-only holdout entries remain unchanged.

**Earlier dated checkpoints below are historical.**

**Training-only context-safeguard study completed.** V19 corrected control seed 0 remains retained. The unchanged 345 training passages support two frozen rules for a later validation proposal: named-asset typing and bounded shared identifiers. Three shadow retags resolve three typed FPs and gain three TPs, with zero introduced training FP/FN; training F1 changes from 98.09% to 98.45%. Organization/role exclusions and direct designator corrections remain empirically unproven. No validation comparison, holdout content access, neural inference, training or integration occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** separately scope a frozen validation-only comparison of the two qualifying rules using saved predictions. Do not tune further rules against validation or reopen the completed holdout. Data, annotations and the retained model stay unchanged; the desktop can remain off.

[Training-only study](evaluations/flood-ner-context-safeguards-20261019/README.md) · [Context-safeguard operator guide](guides/ner-context-safeguards.md). Fresh checks: **198 passing tests**, including **94 new context checks**; the 48 fictional cases stay outside corpus membership. Eleven output files reproduce byte-for-byte; 451 protected hashes and 55 stat-only holdout entries remain unchanged.

**Earlier dated checkpoints below are historical.**

**Current NER diagnosis completed: retain corrected v19 control, seed 0 primary.** Saved predictions reproduce candidate validation F1 69.71% versus control 71.60%. All 405 records are accounted for; 22 affected validation passages/18 complete saved captures and 33 training contexts were reviewed. Candidate gains seven correct entities, loses four, introduces eighteen FPs and resolves eight. No supported reference correction or training/scoring defect was found; one inherited boundary question remains unresolved. Fresh 197 tests/20 subtests pass. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** a separately scoped development-only feasibility task for convention/training-derived context safeguards and constructed contrasts. No additional optimizer search, data collection, model selection or training is authorized. The completed holdout stays excluded; the desktop can remain off.

[Diagnosis report](evaluations/flood-ner-regularization-diagnosis-20261019/README.md) · [Comparison guide](guides/ner-regularization-comparison.md)

**Earlier dated checkpoints below are historical.**

**Publication checkpoint:** Matching public v21 execution/scoring code and metadata accompany this roi-branch update. The [new private result backup](https://drive.google.com/drive/folders/14A4kgWRH0LNay8My9vCutIQp_ro-ezTl) has nine fully byte-verified, owner-only files; older handoffs are unchanged. Corrected v19 control seed 0 remains primary, and no further runs or holdout evaluation occurred. [Publication report](evaluations/flood-ner-regularization-publication-20261019/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

- [Regularization publication and private backup](evaluations/flood-ner-regularization-publication-20261019/README.md): verified nine-file archive and publication scope.

- [Regularization v21 desktop execution](evaluations/flood-ner-regularization-v21-execution-20261019/README.md): seed-0 F1 69.7143% fails screening against control 71.6049%; seeds 1/2 omitted, control retained. 291 tests and all preservation checks pass.
- [Regularization v21 conditional execution plan](plans/ner-regularization-v21-execution-20261019.md): seed-0 screening, conditional seeds 1/2 and protected-label retention.

**Earlier receipt/delivery checkpoints below are historical.**

**Current desktop result: regularization v21 receipt and actual GPU/schema verification are complete.** Exactly 20 experiment files / 12 trainer files and all 23 pinned model files verify. Actual result: `verified_read_only`, schema/GPU true, training false. All 248 focused tests pass. No training or inference occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Stopped before training, as required.** A separate explicit task may run the fixed seed-0 screen and conditional seeds 1/2. The completed research holdout remains excluded from tuning and repeat evaluation.

[Desktop verification receipt](evaluations/flood-ner-regularization-desktop-verification-20261019/README.md).

- [Regularization v21 actual desktop verification](evaluations/flood-ner-regularization-desktop-verification-20261019/README.md): authenticated extraction, GPU/schema result and preservation evidence.

**Earlier publication checkpoints below are historical; pending desktop statements are superseded by this receipt.**

**Current NER handoff: the regularization experiment is verified on private Drive; matching code and instructions accompany this roi-branch publication.** The 345 training / 60 validation exports are unchanged. One L2 = 0.05 candidate has seed 0/1/2 configs and a fixed maximum-three-run protocol. All four uploaded files match authenticated readback; parent, destination and files are owner-only. Desktop receipt and GPU verification remain pending. No training, inference or holdout access occurred during delivery. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next on the desktop:** preserve local changes, pull roi-branch with --ff-only, authenticate and extract the delivered archive into an absent destination, then run read-only GPU/schema verification and STOP. Actual training is a separate explicit task after verification; the completed research holdout stays outside tuning.

[Delivery report](evaluations/flood-ner-regularization-delivery-20261018/README.md) · [Desktop instructions](guides/ner-regularization-experiment.md) · [Private Drive handoff](https://drive.google.com/drive/folders/1vKssoZurLa6WjuJPftXRbJ7GcoefimKq)

- [Corrected v19 desktop experiment and laptop handoff](evaluations/flood-ner-corrected-v19-execution-20261018/README.md): five-run results, frozen selection and original transfer history; subsequent laptop evaluation supersedes its pending status.

**Earlier dated checkpoints below are historical.**

**Current NER task completed: one stronger-weight-decay experiment is prepared and CPU-qualified.** The existing 345 training/60 validation records, annotations, tokenizer and grouping remain unchanged. One twelve-file package supplies seed 0/1/2 configs with only `L2: 0.01 -> 0.05` changed. Fresh 341 tests/four subtests pass; 72 new checks also pass in the pinned runtime. No inference, training or research-holdout content access occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** separately publish matching code and privately deliver the experiment bundle; then perform actual desktop read-only GPU verification. Training follows as a separate explicit task: seed 0 screening, conditional 1/2, maximum three runs, with overall improvement and ROAD/LOCAL_AREA protection required. The completed holdout stays outside tuning. Delivery/GPU verification remain pending; the desktop can remain off.

[Preparation report](evaluations/flood-ner-regularization-preparation-20261018/README.md) · [Operator guide](guides/ner-regularization-experiment.md)

**Prior checkpoints follow; their dated “current/next” wording is historical.**

**Current NER status: v19 diagnosis and the one-time frozen research evaluation are complete on the laptop.** Dataset 345/60/60 and validation-selected control/seed 0 stay unchanged. V19 seed 0 training/validation/holdout F1: **98.09% / 71.60% / 73.63%**. Historical v16 seed 0 holdout 74.74%; rules 53.49%. Holdout three-seed means: control 70.34%, v16 75.13%. These results do not establish an overall v19 improvement or authorize choosing a model using the holdout.

**Next:** a separate development plan from the existing training/validation error review; no new articles or automatic retraining. Gate 3 research measurement is complete, while operational qualification, integration and release remain open. The holdout has now been evaluated and must not be tuned against or evaluated again under this protocol. AI-assisted silver, incomplete history/accounting and no certified-fresh claim remain. No collection, new training, reference/partition change, integration, upload, commit or push occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

[Diagnosis/evaluation report](evaluations/flood-ner-v19-diagnosis-evaluation-20261018/README.md) · [Laptop evaluation guide](guides/ner-corrected-holdout-laptop.md)

**Historical checkpoints follow.** Their “current/next” wording describes earlier dated tasks and is superseded by the status above.

**Current handoff: corrected v19 packages are verified on Drive; matching public code and instructions accompany this roi-branch publication.** Dataset remains 345 training / 60 validation / 60 separate research holdout. Three twelve-file packages and the fixed future protocol are delivered; all uploaded bytes match authenticated readback and five owner-only permission checks pass. No training, inference or holdout access occurred. [Delivery report](evaluations/flood-ner-corrected-experiment-delivery-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: desktop receipt and read-only GPU verification for all three packages, then STOP.** Preserve local work, pull roi-branch with --ff-only and receive the new private ZIP from [Drive](https://drive.google.com/drive/folders/1LDO770D82NXHZRiYNZrHe5oyLo7-vJU7). Actual desktop receipt/GPU checks remain pending. A Git pull does not deliver ignored data; do not rerun preparation or historical v16 training commands. Actual training is a separate explicit task. [Exact commands and copyable desktop prompt](guides/ner-corrected-experiment-desktop.md).

**Historical completed task: corrected-data experiment preparation on the laptop.** A separate 345 training / 60 validation revision adopts only 12 supported training-boundary corrections across nine records. Validation, tokenizer and partition/group bytes remain unchanged; the 60-passage research holdout stays unopened. Three twelve-file trainer packages and all nine seed/config schemas qualify in Python 3.11.17/spaCy 3.7.5. Fresh 367 tests / 35 subtests pass, including 83 new tests. No new articles/passages, inference or training occurred. [Preparation report](evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Prior preparation next-step (delivery now completed; desktop verification still pending): publish/deliver the corrected packages and frozen experiment protocol.** At that earlier preparation checkpoint, delivery/GPU verification were pending and no upload, commit or push had occurred. The specified future study uses five runs if control wins screening, otherwise at most seven. No guaranteed score follows. The desktop can remain off. [Operator guide](guides/ner-corrected-experiment-preparation.md).

**Historical completed task: existing-data development audit.** All three models reproduce desktop validation scores on CPU across 345 training / 60 validation records (1215 predictions); the separate 60 research-holdout passages remain unopened. Seed 0 training F1 is 99.40% versus validation 66.67%, consistent with overfitting/example differences. Source-bound review proposes 12 training-span boundary corrections across 9 existing records; one validation-boundary question remains unresolved, with its frozen scored reference retained. No data, partitions or models changed. Fresh 209 tests / 35 subtests pass, including 53 new audit tests. [Audit report](evaluations/flood-ner-development-error-audit-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Prior audit next-step (now completed as preparation above): choose supported corrections and define a bounded regularization experiment using existing data only.** No new articles/passages, corpus admission, replacement export, holdout access, training, upload, commit or push occurred in this task. The desktop can remain off. [Operator guide](guides/ner-development-error-audit.md).

Earlier training/publication checkpoints below remain historical; the current user constraint is no new data collection.


- [Successor publication and private Drive backup](evaluations/flood-ner-successor-publication-20261018/README.md): matching Windows launcher, trained selected checkpoints, complete SHA-256 readback and owner-only access.


**Publication checkpoint:** Matching combined launcher and three-seed reports are included in this `roi-branch` publication. The new [private v17 Drive backup](https://drive.google.com/drive/folders/1ZFFNL9Vu-dg5xLyWsSR2wd99_qsGTE_J) preserves the combined trainer and all three selected checkpoints/logs; all eleven uploaded files pass full SHA-256 readback and all twelve folder/file permission checks are owner-only. Older folders remain unchanged. The local `.env` change stays outside the commit. [Publication evidence](evaluations/flood-ner-successor-publication-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current successor v16 desktop result:** All three successor seeds complete and their selected checkpoints verify; seed 0 remains primary. 75 focused tests and combined GPU/schema verification pass. Development F1 for seeds 0/1/2: 66.67% / 65.41% / 67.46%. All 12,387 protected historical files and `.env` remain unchanged. Holdout evaluation is separate. [Execution evidence](evaluations/flood-ner-successor-v16-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier preparation, delivery, correction and failed-attempt checkpoints below are historical unless explicitly carried forward.

- [Successor v16 desktop integration and training retry](evaluations/flood-ner-successor-v16-desktop-training-20261018/README.md).


- [Successor desktop GPU repair and training](evaluations/flood-ner-successor-desktop-training-20261018/README.md): exact package receipt, Windows runtime repair, desktop verification and authorized sequential seed runs.


**Current desktop status:** successor receipt, 64 focused tests and read-only GPU verification pass after the Windows startup repair. Seed 0 failed before optimizer updates on supplied case-sensitive optimizer keys; later seeds were not launched and no retry occurred. The delivery checkpoints below are historical. [Execution report](evaluations/flood-ner-successor-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current desktop handoff: private trainer delivery to Drive is verified; successor code and public reports accompany this handoff on `roi-branch`.** Dataset membership stays **345 training / 60 validation / 60 research-holdout**. The twelve-file trainer ZIP, checksum and instructions match authenticated readback and remain owner-only. Research-holdout content stays on the laptop. No training ran. [Delivery report](evaluations/flood-ner-successor-delivery-20261018/README.md) · [Private Drive folder](https://drive.google.com/drive/folders/1WuhvnWfKybY8lbKKO55aToTUQ_PY6RqJ). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: receive the package on the desktop and run read-only GPU verification.** Preserve local changes, pull `roi-branch` with `--ff-only`, verify the ZIP checksum, extract only to an absent destination, then use the successor launcher with `--verify-gpu`. A Git pull alone cannot transfer ignored data. Desktop receipt/GPU verification are unconfirmed; seeds0/1/2 training is a later explicit action. [Exact instructions](guides/ner-successor-desktop-training.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current successor status: configuration correction v16.** The desktop reported seed 0 failed before optimizer updates because the v15 package builder lowercased case-sensitive spaCy arguments; seeds 1/2 were not started. The generator now preserves `L2`, `L2_is_weight_decay` and `nO`, and all three configs pass real spaCy 3.7.5 schema resolution. Dataset **345 training / 60 validation / 60 research-holdout** and all eight non-config trainer files remain unchanged. No training/retry or inference ran during this correction. [Correction report](evaluations/flood-ner-successor-config-correction-20261018/README.md) · [Corrected private Drive package](https://drive.google.com/drive/folders/15sxU7utCM9Nf429BXWUQlXgtEoC1nTQH). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: preserve the failed run, pull the matching corrected code, receive v16-configfix into a new destination, and repeat read-only GPU verification.** Require `verified_read_only`, `configuration_schema_verified: true`, `gpu_verified: true` and `training_started: false`. Desktop receipt/GPU re-verification remain pending. A later explicit seed-0 retry needs a new output directory; do not start seeds 1/2 automatically. [Exact instructions](guides/ner-successor-desktop-training.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


Earlier checkpoint counts and pending tasks below are historical unless explicitly carried forward by the current status.

- [Verified successor desktop delivery](evaluations/flood-ner-successor-delivery-20261018/README.md): owner-only Drive ZIP/readback, code publication and desktop receipt/verification instructions.

- [Prepared successor345/60/60](evaluations/flood-ner-successor-preparation-20261018/README.md): admitted/locked membership, qualified separate exports, measured coverage and local handoff.
- [Successor desktop training guide](guides/ner-successor-desktop-training.md): private delivery and read-only GPU verification before explicit training.

- [Adopted research standard](evaluations/flood-ner-provenance-adoption-20261018/README.md): direct user decision, unchanged limitations and exact proposal counts.
- [Successor preparation specification](plans/ner-successor-preparation-20261018.md): decision-complete next implementation task.

- [Saved-evidence clearance assessment](evaluations/flood-ner-clearance-assessment-20261018/README.md): fresh source/group/reference checks and separate global limitations.
- [Research provenance decision](plans/ner-provenance-standard-decision-20261018.md): two explicit options; neither is adopted automatically.

- [Gemini recovery response](evaluations/flood-ner-gemini-recovery-response-20261018/README.md): access limitation recorded; same request closed pending genuinely new evidence.

- [Gemini evidence recovery outcome](evaluations/flood-ner-gemini-evidence-recovery-20261018/README.md): eleven request/result dispositions, twelve historical-file dispositions, tested evidence intake and explicit awaiting-evidence result.

- [Gemini evidence recovery instructions](guides/ner-gemini-evidence-recovery.md): copyable request for existing original records; no new searches or training.

- [Four-passage completion and readiness](evaluations/flood-ner-four-passage-completion-20261018/README.md): conditional 60 reached using saved material; history/accounting blockers remain.

- [Latest saved-candidate reuse review](evaluations/flood-ner-latest-candidate-reuse-20261018/README.md): verified 56-member conditional witness, four-positive Taglish gap and explicit protocol amendment.


**Historical v9 checkpoint:** all 27 mistaken reductions were reversed, restoring 49 and preserving 53. V10 below/above separately reconsiders metadata-only holds and latest saved windows; the old protocol comparison remains preserved.

- [Baseline recovery and corrected review precedence](evaluations/flood-ner-baseline-recovery-20261018/README.md): restored 49, preserved 53 and separate evidence/protocol restrictions.


**Superseded v8 progress reduction:** its 22-passage result omitted later source-bound review decisions. V9 reverses all 27 mistaken reductions; the v8 report remains preserved. The ten software repairs remain in force.

- [V7 workflow repair and isolated reassessment](evaluations/flood-ner-v7-workflow-repair-20261017/README.md): ten retained code fixes; its baseline reduction is corrected by v9.

Earlier checkpoints below retain their historical counts; v7 readiness claims are superseded.

**V6 audit completed; collection blocked:** preserve **345 training / 60 validation / 49 conditional test**. Four Taglish members are newly exposure-quarantined; the historical 53 artifact remains unchanged. English 30/30, Taglish 19/30; **eleven Taglish positives remain missing**. Local v5 ledger replay is consistent, but complete original search-tool receipts are unavailable. Claimed 649 identities + four uncertain slots / 84 attempts do not certify remaining 47/16 headroom; additional v5 exposure is unquantified. This task sent **zero network requests**, passed 27 offline guards and preserved 6,896 protected files. Next: recover original tool receipts for isolated reconciliation; no collection, admission, seal, export or training. Desktop action none. [Current outcome](evaluations/flood-ner-taglish-budget-continuation-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below retain their historical claims and counts.

**Taglish completion evaluation (Round v5) completed; shortage unchanged:** **345 training / 60 validation / 53 conditional test**. Executed bounded targeted collection round v5 (11 queries reserved and accounted for; cumulative raw identities 649 / 700 ceiling; publisher attempts 84 / 100 ceiling; collection closed). All 53 baseline members preserved. English 30/30 (27 pos + 3 neg) and Taglish 23/30 (20 pos + 3 neg); **seven Taglish positives still needed**. Candidates from historical weather events evaluated showed either training/validation event overlap or English-dominant regional reporting without operational Taglish. Next: bounded acquisition proposal for unexposed localized floods (2017–2023) or authorized source-use evidence resolution before successor admission, grouped partition freeze, qualified exports or desktop GPU training. [Current outcome](evaluations/flood-ner-taglish-test-completion-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Source-evidence gate review completed; shortage unchanged:** **345 training / 60 validation / 53 conditional test**. Audited 86 held identities and 19 exclusions under saved material with zero network operations; zero holds resolved. All 53 baseline members preserved. English 30/30 and Taglish 23/30; **seven Taglish positives still needed**. Collection remains closed at 585 raw identities + four uncertain slots / 84 publisher attempts under prospective 600/100. Next: concrete bounded follow-up proposal with exact accounting or external acquisition authorization before successor admission, grouped partition freeze, qualified exports or desktop GPU training. [Current outcome](evaluations/flood-ner-source-evidence-gate-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Taglish follow-up completed; coverage still short:** **345 training / 60 validation / 53 conditional test**. Four Taglish positives gained; all 49 earlier members retained. English 30/30 and Taglish 23/30; **seven Taglish positives still needed**. Two bounded rounds used 22 queries / two captures; current ledger 585 raw identities + four uncertain slots / 84 publisher attempts under prospective 600/100. Collection is closed, with no further ceiling increase in this task. Next: supported original-source/use and history evidence for reconsiderable held leads, then the remaining positive windows. Admission, freeze, seal, export and desktop GPU handoff remain pending. [Current outcome](evaluations/flood-ner-taglish-completion-followup-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Targeted collection and review completed:** **345 training / 60 validation / 49 conditional test passages**. Seven test passages gained (five English positives and two Taglish positives); all 42 earlier members retained. English meets its target; **eleven Taglish positives remain missing**. Nine searches and eight captures are complete; cumulative accounting is 377 raw URL identities + four uncertain slots / 82 publisher attempts, within the prospective 400/100 ceilings. Collection is closed; all exposed identities and proposed references are accounted for. Final checks: 19 acquisition mocks, 26 rejection guards, zero schema/tokenizer errors and 6,535 protected files unchanged. The test remains unsealed; no training or desktop action. [Current report](evaluations/flood-ner-taglish-targeted-collection-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below preserve their historical counts and permissions.

**Six-known-lead task completed:** **345 training / 60 validation / 42 conditional test passages**. All six leads are history-held; **zero publisher GETs**. New source-only history evidence holds eight prior witness members; the earlier 50 remains an unchanged historical artifact. Remaining positives: **5 English / 13 Taglish**. URL accounting is 296 actual + four uncertain slots under the prospectively authorized 306 ceiling; attempts remain 74/100. Unused allowance is not replacement/discovery permission. Test stays unsealed; desktop can remain off. [Current evidence](evaluations/flood-ner-six-known-leads-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below retain their recorded outcomes and counts.

**Saved-test evidence review completed:** preserve **345 training / 60 validation**, with **50/60 conditional test passages** after saved review and exposure quarantine. Positive shortage **1 English / 9 Taglish**. All 49 prior unresolved references and 68 saved sources are accounted for. Zero network requests; accounting stays 296 actual URLs + four uncertain slots / 74 publisher attempts. One progress disclosure is documented and affected components held; prior 50 remains historical. Test stays unsealed; desktop can remain off. [Latest evidence](evaluations/flood-ner-saved-test-evidence-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below retain their recorded outcomes and counts.

**Non-GDELT search completed:** preserve **345 training / 60 validation**, with **50/60 conditional independent-test passages**. Positive shortage now **1 English / 9 Taglish**. Ordinary web search used one query at a time with all returned URLs audited under the unchanged 300/100 ceilings; no GDELT troubleshooting. Actual URLs 296 + uncertain slots 4, leaving 0 usable URL slots / 26 publisher attempts. Test remains unsealed; desktop can remain off. [Latest outcome](evaluations/flood-ner-non-gdelt-search-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Previous checkpoints below retain their recorded counts and outcomes.

**Final GDELT diagnostic blocked locally; hardening complete:** **0 outbound GETs**, no provider response. The one diagnostic operation stopped at a pre-dispatch guard; exact original message was not retained. Corrected a platform-sensitive timer comparison and verified it with mock responses (101 tests pass / one skips), without reopening the authorization. Stop GDELT troubleshooting. Preserve **345 training / 60 validation / 42 conditional test**, still missing six English and twelve Taglish positives. Carry **204 actual exposed URLs + 4 uncertain slots** (92 unreserved URL slots / 34 article attempts remain). The test stays unsealed; desktop can remain off. [Latest outcome](evaluations/flood-ner-final-gdelt-diagnostic-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier diagnostic checkpoints below retain their original outcomes and allowances.

**Controlled retry completed; provider remains blocked:** preserve **345 training / 60 validation / 42 conditional test passages**, still missing **six English and twelve Taglish positives**. The authorized single retry returned HTTP 429; no new articles or passages and no further retry/fallback. Carry **204 actual URL exposures + four unresolved reserved slots**, leaving **92 unreserved slots / 34 article attempts** under 300/100. Twelve exact history metadata/helper payloads remain unavailable; no new source identities were found. The test stays unsealed and desktop can remain off. [Latest outcome](evaluations/flood-ner-controlled-retry-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Previous checkpoints below retain their original outcomes and allowances.

**Bounded discovery completed with a provider blocker:** preserve **345 training / 60 validation** and **42/60 conditional test passages**; **six English and twelve Taglish positives** remain missing. The first GDELT one-record probe returned **HTTP 429**; collection stopped without retry, fallback or new articles. Actual exposure is **204 URLs + one pending slot**, leaving **95 unreserved URL slots / 34 article attempts** under 300/100. Three exact historical payloads were recovered from Drive; twelve named metadata/helper payloads remain unavailable. The test stays unsealed and the desktop can remain off. [Outcome](evaluations/flood-ner-bounded-discovery-20261017/README.md) and [research guide](guides/ner-bounded-test-discovery.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below retain their original recorded outcomes.

**Current successor proposal: 345 training / 60 validation; independent test 42/60 conditional.** Three saved-source positive windows close the validation gap; preserve all prior 402 qualified candidates, 64 exclusions, 99 holds and historical fitted-source guards. The test still needs **6 English and 12 Taglish positives** under the current joint witness. Desktop inventory is received and reconciled within its named readable scope; user knowledge is now “only inside LANES,” with exclusions/unprovided receipt payloads explicitly limited. The test remains unsealed; no actual admission, freeze, export or training. [Current outcome](evaluations/flood-ner-desktop-history-gap-completion-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next action stays on the laptop:** resolve the report’s remaining independent-test coverage/evidence and bounded-discovery limits. New cumulative test ceilings are 300 URLs / 100 capture attempts; the earlier 202/200 overrun is preserved as historical. The desktop can remain off until an explicit GPU training handoff is ready. Do not rerun the old inventory/restoration/training instructions by default. [Desktop status](guides/ner-desktop-history-inventory.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the successor targets above are newer.

**Targeted isolated collection and desktop-history handoff completed with blockers:** Review five pre-breach captures and preserve all prior material. Nine complete positive proposals are added; the supported finite-pool joint witness after known history/use filters is **37/60**, conditional on unresolved global history and the failed acquisition gate. **Discovery reached 202/200 URLs (17 new versus at most 15); collection stopped and the entire final 11-URL batch remains held/ineligible.** Capture attempts stay **37/100**. The **402 qualified development candidates / proposed 345+57** remain unchanged. A portable, tested metadata/hash inventory and desktop instructions are ready; the original desktop has not yet been inventoried. **Next: run and reconcile the desktop inventory, resolve acquisition compliance and independent-test coverage/evidence before admission/freeze/export or desktop GPU training.** No training has started; the test remains unsealed with zero admitted/scored records. [Report](evaluations/flood-ner-targeted-test-history-handoff-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the targeted-collection/handoff outcome above is newer:

**Archive history and saved-test selection completed; training remains pending:** Verify all **3,863 recorded v3 payloads / 11 parts / 2,357 objects**, **seven historical ZIP entries** and metadata for **19 known Drive items**, with no missing/conflicting recorded payload. Complete isolated positive-window selection and source-only historical comparisons in a separate private curator package; retain the unchanged **60 / 30+30 / 27-positive+3-negative-per-language** target. **Unknown external cross-computer history remains unresolved; test stays unsealed with zero admitted/scored records.** The **402 qualified development candidates / proposed 345+57** remain unchanged. **Next: address the specific remaining independent-test history/evidence/coverage gaps before admission/freeze/export and desktop GPU handoff.** [Archive and saved-test outcome](evaluations/flood-ner-archive-history-test-selection-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the archive/selection outcome above is newer:

**Successor qualification and isolated-test reassessment complete; training remains pending:** **402 qualified proposal candidates / 149 source cases**, retaining **345 proposed training / 57 validation**; all 259 relationship entries qualify for supported conservative joint grouping without incident-identity or independence claims. Carry forward 64 exclusions and 99 holds; record 16 scoped project-use adoptions for 20 saved-source windows. **The separate 60-passage test stays unsealed: the user is unsure whether all older cross-computer article histories are represented.** Curator-specific evidence/count gaps remain in the safe report. No actual admission, freeze, export or training. **Next: resolve the concrete history/isolated-test gaps; reuse completed development qualification before a separate admission/export/desktop GPU handoff.** [Qualification and test reassessment](evaluations/flood-ner-successor-qualification-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the qualification status above is newer:

**Successor dataset design complete; retraining remains pending:** Use all **402 provisional candidates** in a separate **345 training / 57 validation proposal** (170/175 training English/Taglish; 37/20 validation). Actual original/A/recovery/B input bindings anchor all 280 historical training records, including now-excluded/held examples. **The old additional 240 / exact-balance quotas are prospectively superseded for this version by explicit user choice; historical specifications and results remain unchanged.** Validation has no Taglish ROAD/LANDMARK or short-code-theme examples; conservative grouping does not certify event independence. **Next: resolve proposed-member source-use/group admission qualifications and complete the separate unchanged 60-passage fresh-test boundary before admission/freeze/export and desktop training.** No actual admission or partition freeze occurs. [Successor design](evaluations/flood-ner-successor-design-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the successor design above is the current status:

**Saved-article successor proposal complete; retraining remains pending:** Read all **91 remaining saved bodies**, account for **565 considered records**, and propose **402 provisional candidates / 64 exclusions / 99 holds**. Candidates comprise 214 original training records, 168 reviewed drafts and 20 new saved-source windows. The 20 windows add 14 LOCAL_AREA spans; all 41 proposed new windows align. **Additional coverage still fails the 240 design: 188 candidates, capped theme/language capacity 169, at least 71 missing cell slots.** Fresh test remains unsealed with zero admitted records. Original data, drafts, reviews, tokenizer, models, scores and source-use decisions verify unchanged. **Next: resolve coverage/use/reference/group constraints and the independent evaluation boundary before admission/export or desktop GPU training; saved-only scope remains in force.** [Successor proposal](evaluations/flood-ner-successor-proposal-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical additional-review checkpoint (the successor proposal above is newer):

**Additional dataset review complete; training readiness remains open:** Read all **244 drafts / 49 full saved articles**, reconcile **65 prior additional holds and 33 original training holds**. New recommendations: **166 keep, 2 correct, 29 exclude, 47 hold**. Eight prior additional holds resolve under existing rules or supported corrections; twelve are excluded with reference questions unresolved; 45 remain held and two new holds are flagged. Two original holds receive separate correction proposals; 31 remain held. The 168 new candidates have **zero usable LOCAL_AREA spans** and capped theme/language capacity 154. **Next: choose successor membership, address coverage/group constraints and complete the independent evaluation boundary before export or desktop training.** All original data, drafts, models, scores and historical partitions remain unchanged. [Additional review](evaluations/flood-ner-additional-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical original-training review checkpoint (its next-step wording predates the completed additional review):

**Original training-data review complete:** Read all **280 training passages / 94 saved article bodies** and check 966 existing spans. Future-only recommendations: **203 keep, 17 correct, 27 exclude from the successor core, 33 hold**. Shared validation passes 301 original/proposal records; frozen tokenizer alignment passes 966 original and 73 proposal spans. Preserve the original experiment, models and all 244 additional drafts. **Next: review the additional drafts under the same criteria, resolve holds/event relationships, then decide successor membership; no retraining yet.** [Full training review](evaluations/flood-ner-original-training-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current NER workflow:** Original experiment and six-class data contract remain intact. Windows checkout bytes are repaired/protected; 80 focused tests pass. Laptop handles review/preparation; training stays on the qualified desktop GPU. Successor corpus/annotation compatibility and existing data/test readiness must pass before a distinct export/experiment. [Consistency review](evaluations/flood-ner-consistency-review-20261016/README.md); [relevance and v3-transfer evidence](evaluations/flood-ner-topic-audit-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical October 16 backup-delivery checkpoint:

**Laptop backup verified:** The owner-only [v3 Drive backup](https://drive.google.com/drive/folders/1JrrMzZ3FyP0LGU00xWKF54enyyC87ffX) contains the newer research artifacts: 3,863 files, including trained checkpoints and additional-dataset packages. All 19 uploaded files pass full SHA-256 readback. Download all files and follow `START-HERE.md` / the [backup receipt](evaluations/flood-ner-laptop-backup-20261016/README.md). Dataset readiness remains open; resume the existing Gate 3 task after verified laptop restoration. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical acquisition checkpoint; Gate 3 readiness remains open:** Flood-focused acquisition records 365 development candidate URLs (363 article keys) / 182 capture attempts / 159 captures. The draft has **244 passages / 49 articles**; **179 source-reading candidates and 65 held records** cannot meet the 240-passage theme/language quotas (candidate capacity 156). One frozen-tokenizer alignment failure is preserved. Admission, grouped partition freeze, export and training remain zero. The isolated curator result is recorded separately; no fresh-test readiness is assumed. **Next: resolve the recorded dataset-readiness gaps under the same Gate 3 task.** [Readiness report](evaluations/flood-ner-additional-dataset-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical improvement-preparation checkpoint:

**Gate 3 improvement preparation complete; no retraining started:** The versioned reference-scope addendum accounts for all 14 review questions. The constructed matrix has **48 cases / 24 English / 24 Taglish**, including **30 positives, 16 negatives and 2 explicitly unscored unresolved cases**; 12 preparation-integrity tests pass. Training/validation coverage and acquisition requirements are recorded, together with a fresh **60-passage / 30+30-language test protocol, three negatives per language**. Original annotations, scores and model roles stay frozen. **Next: prepare and admit the additional dataset**, reconciling historical exclusions, source-use eligibility, grouping and isolated held-out access before deciding size/recipes. CPU/Linux/failure/performance qualification and Gate 4 integration remain pending. [Report](evaluations/flood-ner-improvement-preparation-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current NER order:** Resolve the [additional-dataset readiness gaps](evaluations/flood-ner-additional-dataset-20261016/README.md) in the existing Gate 3 item; admission/export/training remain blocked by actual coverage, references, grouping and isolated test readiness. Preserve the completed original experiment. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical Gate 3 review checkpoint:

**Gate 3 qualification review complete; operational qualification remains open:** Codex reads all **60 held-out passages / 22 articles**, records **120 original/A seed 0 assessments** and accounts for all **391 FP/FN events**. Fourteen passages retain AI reference/convention questions; no label, offset, score or model choice changes. Original seed 0 remains primary (**63.12 test F1**) and A seed 0 exploratory (**67.72**). All 42 event-count slices and preservation checks pass. Next prepare the remaining Gate 3 qualification specification (reference-scope addendum, constructed regression matrix and bounded CPU/Linux/failure/performance plan) before Gate 4 integration. No inference, training or test rerun occurs in this review. [Review](evaluations/flood-ner-model-qualification-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical held-out benchmark execution:

**Held-out NER evaluation complete:** The six frozen original/A checkpoints and two baselines complete one evaluation on **60 test passages / 290 spans**, 30 English/30 Taglish. Original seed 0 remains primary at **63.12 six-class F1**; exploratory A seed 0 scores **67.72**. Three-seed means are **68.46 original / 70.24 A**, with sample SD **4.85 / 2.20 percentage points**. Rules score **58.97 six-class F1**; native LOC scores **67.02 on the separate coarse task**. All 59 focused tests, 240 metric reconciliation checks and preservation checks pass. Test results are now exposed; no further tuning or seed selection uses them. Next complete the existing Gate 3 model-qualification/error review before Gate 4 isolated integration. [Held-out report](evaluations/flood-ner-heldout-test-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical development-only checkpoint:

**Frozen experiment and bounded validation trials complete:** Original seeds 0/1/2 reproduce development F1 **67.15 / 70.59 / 72.29**; seed 2 succeeds in its separate authorized recovery folder. Recipe A wins the seed 0 comparison (**71.81**, versus B **70.70**) and completes robustness seeds 1/2. A family mean is **72.61**, sample SD **0.92 percentage points**; original mean is **70.01**, sample SD **2.62**. Original seed 0 remains primary. All five permitted new runs complete before the renewed cutoff; 43 focused tests pass. Prior artifacts, GPU environment, dependencies and .env verify unchanged. Next freeze the final experiment/checkpoint decision, then perform separate held-out testing under the frozen protocol; test predictions remain untouched. [Completed report](evaluations/flood-ner-validation-study-20261016-v2/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical primary-training checkpoint:

**Primary seed 0 training complete:** The researcher manually ran the frozen GPU recipe. The selected development checkpoint is step 455, F1 67.15 / precision 68.32 / recall 66.03; early stopping ends at step 630 after 175 steps without improvement. All 103 run files remain unchanged; test predictions remain untouched. Manual check-only launchers for robustness seeds 1/2 pass; 29 focused tests pass. Next run seeds 1/2 and the frozen baseline comparisons, keeping seed 0 primary. [Training result](evaluations/flood-ner-primary-training-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical preparation checkpoint:

**Baseline/training preparation complete:** Frozen rules type/original-offset mapping and seed 0/1/2 configurations pass initialization on the RTX 3060 Ti using the verified qualified export. Each initializes six location labels, 46 GPU parameter arrays and the two CPU upper-classifier arrays required by the pinned architecture, with the exact candidate tokenizer and copied pretrained NER encoder. No optimizer updates, corpus prediction evaluation or held-out test reading occurred. Twenty-one focused unittest methods pass. All 10,531 prior artifact hashes, 23 model files, 22,759 audited research-environment file stats, CLI package versions and .env are unchanged. The next task is the first primary-seed training run under the frozen development-selection protocol. [Preparation verification](evaluations/flood-ner-experiment-preparation-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical qualified export checkpoint:

**Qualified training-format export complete:** The new offline export-qualified-corpus command binds the admitted 400 samples/138 articles to the passing calamanCy tokenizer and frozen evaluation contract. Verified 280/60/60 DocBins, 200/200 languages, 1,465 spans, 48 negatives and 40 contextual references without adding contextual samples. All six primary/replay DocBins reload correctly; their three partition files, tokenizer and metadata provenance match byte-for-byte. Twelve focused unittest methods pass. All 10,500 prior artifact hashes, 23 model files, research-environment file metadata and .env remain unchanged. Baseline/training preparation is next; no model predictions, training or deployment occurred. [Export verification](evaluations/flood-ner-qualified-export-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical tokenizer qualification checkpoint:

**Desktop CLI repaired; corpus tokenizer qualified:** Restored only the existing NumPy 1.26.4 / SciPy 1.14.1 pins in backend/venv; spaCy, Thinc and the GPU research environment remain unchanged. The separately recorded qualification passes on 400 samples / 138 articles / 40 contextual pairs / 1,465 spans, with zero candidate alignment errors, all 56 constructed controls passing and reproducible serialization/reload. The frozen evaluation contract now binds the qualified candidate. All 10,458 pre-existing artifact hashes, 23 model files, research-environment file metadata and .env verify unchanged. Training-format export is next; no export, NER predictions, training or deployment occurred. [Qualification and repair](evaluations/flood-ner-desktop-tokenizer-qualification-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical first desktop attempt:

**Desktop restoration complete; tokenizer qualification blocked:** Fast-forwarded the existing roi-branch checkout to 4736cea, verified the private ZIP and restored 697 missing files while skipping 1,060 identical files without conflicts. All 1,757 payload hashes verify. The admitted corpus reconciles to 400 samples / 138 articles / 40 contextual pairs / 1,465 spans, with 200/200 languages and 280/60/60 partitions. All 9,744 existing artifact hashes, 23 model files, research-environment file metadata and local .env are unchanged. The single generated qualification attempt exits during the backend CLI spaCy/Thinc import with a NumPy ABI size mismatch, before the isolated worker starts. No alignment/reload pass, dependency repair, export or training is claimed. Resolve CLI compatibility before a separately recorded qualification attempt. [Desktop result](evaluations/flood-ner-desktop-restoration-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical laptop delivery checkpoint:

**Private desktop handoff delivered:** The [new Drive folder](https://drive.google.com/drive/folders/1gnGV2wP0gNHx2LNa64fwc-U4AIQxRdkT) contains seven owner-only files, including the unchanged v2 ZIP and desktop instructions. All seven uploaded files pass byte/hash readback; the ZIP matches 28,476,420 bytes and its frozen SHA-256. The 400 samples/40 contexts, original capture evidence, partitions and scoped admission are unchanged; all 5,234 prior preservation entries verify. No sharing changes, desktop restoration, corpus qualification, export or training occurred. [Verified delivery](evaluations/flood-ner-desktop-drive-delivery-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical laptop preparation before personal-account access:

**Git handoff implementation pushed:** `ac1ae53` is verified on `origin/roi-branch`; private data/ZIPs remain ignored. Drive delivery remains pending, with no desktop restoration or qualification claimed. [Receipt](evaluations/flood-ner-desktop-handoff-20261016/publication-receipt.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Laptop handoff prepared and restoration verified:** The private v2 ZIP contains **400 admitted locations / 40 contexts**, 138 selected articles and all **407 original capture-evidence files**. Its **1,757 payload files** restore with identical hashes; a second restore skips every identical file. All 400/40 qualification inputs and selected publication evidence revalidate offline. **880 software tests passed; one skipped** (40 new handoff tests). The 23 recorded desktop/laptop model identities match; weights and environments are excluded. Three historical evidence gaps remain unreconciled; eleven invalid-test references and ten copied-manifest path aliases are separately classified. Drive delivery remains pending because this chat still sees the school account and cannot access the owner-only personal folder. Desktop restoration and tokenizer qualification have not run. [Handoff report](evaluations/flood-ner-desktop-handoff-20261016/README.md); [desktop instructions](guides/ner-desktop-handoff-20261016.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier corpus-tokenizer checkpoint:

**Corpus-tokenizer tooling delivered; actual qualification blocked:** Added the separate tokenizer-only qualify-corpus-tokenizer command and froze the silver-reference evaluation protocol. The one permitted unchanged-environment retry fails at spaCy import with Windows Application Control error 4551 on torch_python.dll or a dependency, before tokenizing any passage. No model predictions, alignment pass, tokenizer promotion, export or training is claimed. **840 software tests passed; one skipped**, including 68 new tests; the older 772/one result remains historical. Verified 17 artifact checks, 5,234 preserved prior files and all 23 model hashes. The 400 admitted locations/40 contexts, 200/200 languages, 280/60/60 partitions, twelve nonacademic outcomes and research-only originals remain unchanged. The contract is protocol-frozen with qualified-tokenizer binding pending; no test-set model results were opened. [Qualification attempt](evaluations/flood-ner-corpus-tokenizer-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier completed admission checkpoint:

**Private academic-use admission applied:** A separate derivative contains **400 admitted location samples from 138 articles and 40 consistently updated contextual pairs**. Only source.admission_status, source.reuse_status and scoped source.reuse_terms change; text, annotations, identities, reporting groups, 200 English/200 Taglish, 280/60/60 partitions, all holdouts and ten pilots are preserved. The ledger retains 69 explicit adoptions, 68 desktop-reported adoptions and one prior local adoption; the missing detailed desktop predecessor remains unreconciled. This is an AI-authored project-use application under researcher delegation, not publisher permission, legal approval or a dataset license. All twelve nonacademic outcomes are unchanged. Verified 41 negative artifact checks, 21 byte-identical replay files, 5,101 preserved checkpoint/capture files and 23 model hashes. The new derivative/replay adds 960 complete-body string fields, not new articles. Research-only originals remain unchanged and refuse export. Source admission is 400; exports and training remain zero. No pytest rerun; 772 passed/one skipped remains historical. [Admission results](evaluations/flood-ner-academic-admission-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier research-only checkpoint:

**Frozen research revision v5 complete:** Cohort-v5/contextual-v5 reload successfully with **400 locations/40 contexts from 138 articles**, 200 English/200 Taglish, 280/60/60 partitions, 1,465 location spans and 48 negative passages. Exact reviewed assembly preserves 388 location records (including all 383 fixed records, holdouts and ten pilots) and 38 contextual pairs; twelve locations/two pairs are replaced without reselection. Four scoped decisions and 134 preserved dispositions are bound to every source/sample and the new manifests, giving **derived recorded private-basis coverage of 138/400**. The missing detailed desktop predecessor remains unreconciled; no publisher permission or admission is inferred. Verified 32 negative artifact checks, 22 byte-identical replay files, 2,966 preserved prior files and 23 model hashes. The complete generated-copy audit counts 960 body-string fields, including contextual evidence; these are copies, not new articles/samples. All source flags remain research_only/unknown; admission/export remain zero. No pytest rerun; 772 passed/one skipped remains historical. [Current frozen dataset](evaluations/flood-ner-research-assembly-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoint summaries retain their then-current dataset and decision measurements.

**Proposed seventeen-passage scope review complete:** All twelve draft sentences are accepted silver location candidates, five retained windows are confirmed unchanged, and two contextual replacements are reviewed. The proposed **400 locations/40 contexts** pass every quota in memory while preserving all **383 unaffected records**, test samples and pilots. Four changed article selections receive explicit private project-basis adoptions; carrying 134 prior dispositions gives **derived proposed coverage of 138 articles/400 passages**, with the detailed desktop predecessor still unreconciled. The current cohort-v4/contextual-v4 and its four old holds/17 passages remain unchanged; no frozen revision, admission or export was created. Verified 33 negative artifact checks, fourteen byte-identical replay files, 2,903 preserved checkpoint files and 23 model hashes. No new complete-body copies or pytest rerun; 772 passed/one skipped remains historical. [Reviewed inputs and decisions](evaluations/flood-ner-held-scope-review-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoint summaries retain their then-current dataset and decision measurements.

**Seventeen-passage alternatives feasibility complete:** Verified a reviewed 400-slot witness and a smaller conditional proposal with all **383 unaffected records fixed**. The recommended proposal retains five existing windows and adds twelve unaccepted sentence drafts, reducing selected text across four held articles from **3,087 to 2,057 characters**. All quotas pass conditionally; twelve language/location reviews, four changed-scope use assessments and two contextual replacements remain. Current cohort-v4/contextual-v4, 400/40 records, 134/383 project-basis coverage and four holds/17 passages are unchanged; admission/export remain zero. Verified 2,839 prior files, 23 model hashes, byte-identical replays and 17 direct negative artifact checks. No pytest rerun; 772 passed/one skipped remains historical. The [generated-copy inventory](evaluations/flood-ner-held-alternatives-20261016/copy-inventory.json) separately records the new private witness/replay representations; no new articles were collected. [Results and proposal](evaluations/flood-ner-held-alternatives-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoint summaries retain their then-current dataset and decision measurements.

**Twelve-case private-use decision review complete:** Eight articles/32 passages receive explicit limited project-basis adoptions; four editorial articles/17 Taglish training passages retain their holds. Preserving the other 126 dispositions gives derived coverage of **134 articles/383 passages** for cohort-v4, with **4/17 held**. All 400 location records, 40 contextual-v4 pairs, partitions, tests/pilots and source flags remain unchanged. Verified 2,802 prior files, 23 model hashes, deterministic replay and 35 direct negative artifact checks. Admission/export remain zero; the missing detailed desktop predecessor remains unreconciled. The 772-passed/one-skipped software result is historical; no pytest rerun occurred. [Current decisions](evaluations/flood-ner-held-decisions-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoint summaries retain their then-current dataset and decision measurements.

**Bounded research revision complete:** 400 reviewed location records from 138 articles and 40 contextual-v4 pairs meet every unchanged quota. Reviewed 120 windows (110 accepted/ten rejected); preserved 330 unaffected references, all 60 test samples and ten pilots, using two of the permitted 20 additional changes. Final cohort-v4/contextual-v4 replay byte-for-byte; 2,661 prior files and model/tokenizer hashes remain unchanged. Derived project bases cover 126 articles/351 passages; 12 articles/49 passages remain held. Admission/export are zero; the detailed desktop predecessor remains unreconciled. **772 tests passed; one skipped.** [Current report](evaluations/flood-ner-research-revision-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoint summaries below retain their historical datasets and measurements.

**Saved-pool revision feasibility complete:** All four tested scenarios are infeasible with the 332 unaffected records fixed. Verified the 1,340-passage/342-article pool; 893 unused candidates remain after fixed-sample conflicts, plus 106 unreviewed whole-paragraph shortening proposals. GMA is at its 160-sample cap, RMN lacks reviewed English candidates, and specific training/validation label quotas remain deficient. No qualifying 400-slot proposal was found. All 400 location records, 40 contextual-v3 pairs, partitions, ten pilots and source-use decisions remain unchanged; admission/export remain zero. [Feasibility and exact deficits](evaluations/flood-ner-revision-feasibility-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**58-case default-adoption correction complete:** Read all 58 complete articles and their 205 selected passages. Explicit reassessments retain 49 adopted private project bases / 157 passages and assign nine holds / 48 passages. Preserving the ten special cases and 71 earlier dispositions gives derived adopted coverage of **125 articles / 332 passages**, with **14 held articles / 68 passages**. The earlier completion claim and 134/380 totals are superseded. All 400 samples/40 contextual-v3 pairs, partitions and source flags remain unchanged; training admission/export remain zero. Acquisition remains Unknown / Codex collected. The unavailable detailed desktop predecessor is still unreconciled. Structural checks bind the authored findings; they do not prove substantive/legal adequacy. [Current correction](evaluations/flood-ner-default-adoption-correction-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoint summaries below preserve their then-current measurements.

**GMA AFP case decision recorded:** One source-bound private-use adoption advances the derived project total to 71 articles/160 passages; 68 articles/240 passages remain held. This AI delegated decision preserves uncertainty and does not grant publisher permission or admission. All 400/40 records and prior checkpoints remain unchanged. [Current decision](evaluations/flood-ner-afp-case-decision-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Acquisition audit and proposed decision supplement complete:** Verified 68 ABS-CBN/Philstar browser captures and prepared 69 source-bound decision drafts, preserving all 400 samples/40 contextual pairs and actual dispositions. Historical login, paid-access and explicit-acceptance facts remain unrecorded; current HTTP defaults are not substituted. No admission or training. [Results and next actions](evaluations/flood-ner-acquisition-decisions-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Laptop source-use research supplement complete:** Reassessed all 69 held articles / 243 passages and reconciled all 139 articles / 400 memberships using the existing laptop corpus, original evidence and verified desktop summaries. Proposed one narrow private research basis for the GMA AFP story (three passages); 68 retain the research hold recommendation. All 69 actual project holds and the 70 reported delegated adoptions / 157 passages remain unchanged. Confirmed Reuters attribution, corroborated the selected AFP-caption credit and matched the QA-source wording to the public Philstar counterpart. Saved 21 capture attempts (12 initial content passes / nine failures), 21 verified clause pointers and explicit uncertainty. 64 focused tests pass; 1,402 prior files and 23 model files verify unchanged. No v2 decision, admission, export, inference/training, publisher message, upload or Git publication. [Research supplement](evaluations/flood-ner-held-reassessment-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Laptop continuation handoff prepared:** The latest completed record remains delegated decisions v1: 70 GMA articles / 157 passages adopted; 69 articles / 243 passages held. Official-source research is approved but unfinished; preliminary browsing produced no saved v2 checkpoint or new hash-bound research evidence. Continue the same source-use task on the laptop using the [handoff guide](guides/ner-laptop-continuation-20261015.md). A verified local private delta ZIP carries the two new desktop checkpoints and documentation snapshots; older research artifacts remain prerequisites. No Git publication, cloud upload, laptop restoration or admission/training/deployment was performed. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Existing source-use task — delegated decisions recorded (partial):** Codex, acting under explicit researcher delegation, adopted the saved private academic-use recommendation for 70 GMA articles / 157 passages and retained the 69 holds / 243 passages (one AFP-credit GMA article, 50 ABS-CBN and 18 Philstar). The source-use basis is not finalized for the held articles. Original AI proposals and blank historical forms remain unchanged; the current dispositions are in a separate ignored versioned record. No independent human review, publisher authorization or legal approval is claimed. All 139 articles / 400 memberships, nine proposal bindings and saved evidence verify. Admission and source-use flags remain unchanged; no export, training or deployment. [Delegated decision record](evaluations/flood-ner-project-decisions-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Source-use decision checklist prepared:** Created the ignored academic-decision-checklist-20261015-v1 checkpoint with a publisher checklist, 139-article CSV and hash-bound verification. Reconciled all 400 memberships without duplicates or omissions; preserved 70 recommended/69 held articles and 157/243 passages. All nine proposal bindings, nine used evidence records and the existing read-only proposal validator pass. The three missing historical audit references remain separately recorded. Original annotations, 40 contextual-v3 pairs, partitions, decision forms, source-use flags, GPU checkpoint and backend/.env remain unchanged. Checklist preparation alone is complete; researcher decisions and admission remain unresolved. [Completion report](evaluations/flood-ner-decision-checklist-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Laptop research restoration complete:** Three downloaded ZIPs match the supplied SHA-256 hashes. Restored 946 missing files at organized and original checkpoint paths, skipped 17 identical files and found no conflicts. Verified 400 locations/139 articles, 40 contextual-v3 pairs, 200 English/200 Taglish and 280/60/60 splits. Current review/proposal validation passes with all nine required bindings; three older audit references remain absent from the supplied backup. Existing desktop work, backend/.env and GPU environment are preserved. No admission, training or deployment. [Restoration report](evaluations/flood-ner-desktop-restore-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**GPU preflight review fix complete:** Timeout handling now preserves partial stdout/stderr for either worker and includes the logs in the failed report hashes. Four regression scenarios reproduced the defect before repair; all 126 focused tests now pass. Previous GPU qualification evidence is preserved; no dependencies, model weights, news admission or schema changed. [Fix verification](evaluations/flood-ner-gpu-timeout-fix-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**RTX desktop GPU preparation complete:** Actual RTX 3060 Ti 8 GB / driver 610.47 verified. Isolated Python 3.11.17, spaCy 3.7.5, CuPy 13.6.0 and Torch 2.11.0+cu128 pass native inference, six-class constructed updates at batch sizes 1/4/8 and saved-model CPU replay. 122 focused tests pass; 73 installed packages are compatible. All 23 original model files verify unchanged. No news-model processing, admission, production or schema change. [Results](evaluations/flood-ner-desktop-gpu-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Desktop publication checks complete:** User authorized `roi-branch` publication for desktop continuation. Fresh full NER/location verification: 721 passed, one Windows symlink test skipped (67.31 seconds). New tooling uses existing dependencies or the standard library; no schema/migration change. Git attributes preserve hash-bound helper/guide bytes. The collector and metadata reports transfer through Git; full dataset text, weights and environments require the private backup and local environment recreation. All 400 samples/40 contextual-v3 pairs and admission holds remain unchanged. [Publication checkpoint](evaluations/flood-ner-desktop-publication-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Existing NER plan continued — desktop inventory prepared:** Preserve the corrected 400 samples/139 articles, 40 contextual-v3 pairs, frozen partitions, calamanCy and tokenizer checkpoints. The researcher confirmed an October 25 defense target requiring deployed LANES integration and RTX desktop availability this week. Publisher correspondence is optional clarification: a supported applicable statutory exception remains an existing use-basis route. No recommendation or admission was changed. Delivered a standard-library-only hardware inventory; this machine is the MX330 laptop, so RTX desktop/CUDA/training qualification remains pending. 83 focused tests pass, one Windows symlink test skipped; 1,366 prior files and 23 model files verify unchanged. [Readiness and route alignment](evaluations/flood-ner-desktop-readiness-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Held-article clarification packet prepared:** Four unsent drafts and four blank response forms cover 69 held articles / 243 passages (50 ABS-CBN, 18 Philstar, one AFP-credit GMA story). Verified exact identities, 10 bindings, nine substantive evidence records, Unicode CSV round trips and 1,341 prior files; 64 focused tests pass. All 400 samples/40 contextual-v3 pairs and partitions remain unchanged; no messages, uploads, resolved holds, decisions or admission. [Report](evaluations/flood-ner-held-clarification-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Private academic-use proposals completed (702 regressions pass; owner-only Drive delivery verified):** Prepared 139 article recommendations and three publisher summaries, rechecking all 78 flagged sources under private owner-only research/training. Recommend 70 GMA articles covering 157 passages; hold 69 articles covering 243 passages (50 ABS-CBN, 18 Philstar, one AFP-credit GMA story). Missing bylines alone are not exclusions. All 400 annotations and 40 contextual v3 pairs remain frozen; actual project decisions, training admission and exports remain zero. The recommended subset alone fails the original 400-sample/publisher requirements. Retention is undecided and is not itself a training prohibition; adviser guidance is researcher-reported and the ethics framework unspecified. [Proposals](evaluations/flood-ner-academic-proposals-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**NER publication checkpoint:** The corrected 400-sample/139-article AI silver cohort and 40 contextual v3 pairs remain frozen. Constructed tokenizer qualification, versioned correction/packaging tools and three academic-use AI reviews are complete. Adviser guidance is researcher-reported: private research/training only; the ethics framework is unspecified. Drive backup is verified and owner-only across 22 checked items. Three academic-use decisions remain unresolved; retention is undecided and is not itself a training prohibition. The next task is the supported academic-use basis and article-exception decisions, followed by separate admission, news-cohort tokenizer qualification and desktop GPU preparation. Fresh focused verification passes 664 tests (94.60 seconds); no new dependency, database migration, training or production change. [Publication checks](evaluations/flood-ner-publication-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Private research access verified:** Recorded researcher-reported adviser acknowledgment and private research/training-only guidance. At the user’s explicit owner-only instruction, restricted the original Drive folder and verified all 17 original items and five subsequent guidance files have only the owner, with no anyone/domain access. No teammate/adviser invitations were sent. The ethics framework remains unspecified, retention undecided, and three academic-use decisions unresolved. No publisher permission or admission is inferred. [Record](evaluations/flood-ner-private-access-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier adviser-guidance snapshot (before the owner-only change):** The user reports adviser acknowledgment and instruction to keep the dataset private, solely for research/training. The reported international ethics framework is unspecified; no written institutional approval or publisher permission is inferred. Drive still allows anyone-with-link editing, so named-account access needs to be arranged using exact teammate/adviser accounts. No sharing settings or admission flags changed. Retention remains undecided and is not by itself a training prohibition. [Record](evaluations/flood-ner-adviser-guidance-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier storage checkpoint (before the owner-only change):** Recorded the user’s BSIT capstone purpose, no known school instructions or publisher permission, and undecided retention with an interest in preservation for a year or longer. Completed a user-authorized, hash-verified Drive backup of the corrected study package and article/sample CSVs. The user reports sharing the link only with groupmates and chose to retain anyone-with-link editing; access is not restricted to named team/adviser accounts. Future-researcher use remains undecided. All three academic-use decisions and training admission remain unresolved; source-use basis and article-exception dispositions are still next. No model work or Git publication. [Storage report](evaluations/flood-ner-study-arrangements-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next NER work:** Inspect already saved captures for additional bounded, source-backed windows supplying the measured gaps: training Taglish ROAD needs at least six more spans and four positive passages; validation English needs four more LANDMARK spans, three LOCAL_AREA spans, and one additional ROAD-positive passage/article beyond the tested relaxed bounds. New windows need fresh complete annotation, language/group review and selected-extent source-use assessment. If unavailable, a separate authorization for limited train/validation rebalancing is needed; preserve test/pilots and all hard quotas. No new URL collection or automatic admission. Current project-basis coverage remains 125 articles/332 passages adopted and 14/68 held; full-cohort admission remains open. [Feasibility and exact deficits](evaluations/flood-ner-revision-feasibility-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Academic-use review completed:** Completed three source-bound AI academic-use conclusions and 139 article credit/amount reviews for private research-team/adviser use. GMA policy supports educational/noncommercial downloading; scope-matched NER permission is not established for the full workflow. ABS-CBN and Philstar likewise need a supported scope-specific basis. Seventy-eight articles have overlapping follow-up flags, including missing captured bylines, eight opinion/editorial sources, nine whole-article samples and origin/caption/host questions. Three academic decisions and twelve other-use outcomes remain unresolved; training admission/export stay zero. All 400 locations, 40 contextual v3 pairs, partitions and checkpoints are unchanged. [Report](evaluations/flood-ner-academic-use-20261015/README.md), [publisher conclusions](evaluations/flood-ner-academic-use-20261015/publisher_assessments.json), [article exceptions](evaluations/flood-ner-academic-use-20261015/article_exceptions.json), [decision summary](evaluations/flood-ner-academic-use-20261015/decision-summary.md) and [method notes](evaluations/flood-ner-academic-use-20261015/methods-notes.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Annotation-correction checkpoint:** Corrected three location records and one contextual pair in a new revision: 400 AI silver samples from 139 articles, 1,497 location spans and 40 contextual v3 pairs. Passage/source text, identities, reporting groups, 280/60/60 partitions and ten retained pilots are unchanged; every hard quota passes. The corrected organized package has 606 verified files plus its manifest and a byte-identical replay. 638 focused NER/location tests pass; the historical 666-test result is a different selection. All fifteen source-use outcomes remain unresolved; training admission, DocBin export and distribution readiness remain zero. Earlier cohorts, contextual v2, packages, model/tokenizer artifacts and checkpoints are preserved. [Results](evaluations/flood-ner-annotation-correction-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Branch-publication checkpoint:** Documentation is synchronized for the requested roi-branch commit/push. Research/tooling, the 400-record silver cohort and first qualification diagnostics are delivered; source-use/model/reference qualification, training and deployment remain pending. Full news captures and the dataset backup are ignored local artifacts, so Git publication includes code and source-linked metadata rather than a backup of those full-text files. That publication checkpoint verified 455 software checks. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**NER qualification diagnostics delivered:** [Report](evaluations/flood-ner-qualification-20261014/README.md), [coverage/holds](evaluations/flood-ner-qualification-20261014/qualification.json), [model metadata](evaluations/flood-ner-qualification-20261014/model_register.json), [source-use inventory](evaluations/flood-ner-qualification-20261014/source_use_inventory.json), [draft scoring contract](evaluations/flood-ner-qualification-20261014/evaluation_contract_draft.json) and [audit](evaluations/flood-ner-qualification-20261014/audit.json). 455 checks pass; corpus remains frozen, v3 remains opt-in, and training admission/model results remain zero. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Find the original preserved dataset:** A dedicated local folder groups the 400 samples, all 132 source articles and two CSV link lists. See the [folder and backup record](evaluations/flood-ner-corpus-400-20261014/bundle_register.json) and [dataset report](evaluations/flood-ner-corpus-400-20261014/README.md). Full-text copies remain ignored by Git; original files are preserved. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**400-sample annotation cohort delivered:** [Report](evaluations/flood-ner-corpus-400-20261014/README.md), [400-sample register](evaluations/flood-ner-corpus-400-20261014/selection_register.json), [132-source register](evaluations/flood-ner-corpus-400-20261014/source_register.json), [entity spans](evaluations/flood-ner-corpus-400-20261014/entity_spans.json), [partitions](evaluations/flood-ner-corpus-400-20261014/partition_manifest.json), [group decisions](evaluations/flood-ner-corpus-400-20261014/group_reviews.json), [coverage](evaluations/flood-ner-corpus-400-20261014/coverage.json), [exclusions](evaluations/flood-ner-corpus-400-20261014/exclusion_register.json), [context pointers](evaluations/flood-ner-corpus-400-20261014/context_register.json), [audit](evaluations/flood-ner-corpus-400-20261014/audit.json), [follow-up review](evaluations/flood-ner-corpus-400-20261014/followup_review.json) and [paper-method notes](evaluations/flood-ner-corpus-400-20261014/methods-notes.md). Exactly 200 English/200 Taglish silver records; 280/60/60 research partitions; 1,374 place spans; zero training admission/export/model results. Publisher/language confounding and AI language/label uncertainty remain explicit. 425 tests pass after contextual JSONL correction; original 100-register and frozen location cohort unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**AI annotation pilot delivered:** [Report/method wording](evaluations/flood-ner-ai-pilot-20261014/README.md), [annotation metadata](evaluations/flood-ner-ai-pilot-20261014/annotation_register.json), [location spans](evaluations/flood-ner-ai-pilot-20261014/entity_spans.json), [coverage](evaluations/flood-ner-ai-pilot-20261014/coverage.json) and [audit](evaluations/flood-ner-ai-pilot-20261014/audit.json). Twelve passages (six English/six Taglish) contain 116 location spans; ten have same-teacher acceptance, two remain unresolved. Explicit location-only export scope separates six place labels from paired rich drafts; admission/splits/human/gold/model results remain zero. The developer authorized AI annotation, and the paper's manual-method wording remains to be reconciled. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Full-body editorial review and paper target resolved:** [Report](evaluations/flood-ner-editorial-20261014/README.md), [paper evidence](evaluations/flood-ner-editorial-20261014/paper_reference.json), [source-bound review decisions](evaluations/flood-ner-editorial-20261014/editorial_reviews.json), [context metadata](evaluations/flood-ner-editorial-20261014/block_register.json), [manual-pilot shortlist](evaluations/flood-ner-editorial-20261014/manual_pilot_shortlist.json), [event findings](evaluations/flood-ner-editorial-20261014/event_findings.json), [excluded cue dispositions](evaluations/flood-ner-editorial-20261014/cue_dispositions.json), [readiness](evaluations/flood-ner-editorial-20261014/readiness.json) and [audit](evaluations/flood-ner-editorial-20261014/audit.json). Reviewed 100 full sources into 113 contiguous context blocks; 78 match the paper's English/Taglish scope. The paper requires 400 total manually annotated samples with 280/60/60 splits. Human annotations, admission and split assignments remain zero; source-use, grouping and manual review remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Pilot readiness reviewed; gate remains open:** [Audit](evaluations/flood-ner-readiness-review-20261014/README.md), [diagnostics](evaluations/flood-ner-readiness-review-20261014/audit.json), [corrected candidate metadata](evaluations/flood-ner-readiness-review-20261014/candidate_register.json), [pending groups](evaluations/flood-ner-readiness-review-20261014/group_review_queue.json) and [holds](evaluations/flood-ner-readiness-review-20261014/readiness.json). Source identities/holds are strengthened, source notes retained and per-passage diagnostics explicit; 378 checks pass. All 100 remain drafts; editorial/language/group/reuse readiness is unresolved. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Initial pilot review queue prepared:** [Readiness report](evaluations/flood-ner-readiness-20261014/README.md), [candidate metadata](evaluations/flood-ner-readiness-20261014/candidate_register.json), [group-review queue](evaluations/flood-ner-readiness-20261014/group_review_queue.json), [reuse evidence](evaluations/flood-ner-readiness-20261014/reuse_register.json) and [measured holds](evaluations/flood-ner-readiness-20261014/readiness.json). Includes 100 source-exact draft windows, 37 provisional event buckets and eight publisher-policy snapshots; 371 focused checks pass. No passage language/labels/splits/training admission are claimed. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Completed NER work reviewed:** [Audit and corrections](evaluations/flood-ner-review-20261014/README.md), [per-source audit metadata](evaluations/flood-ner-review-20261014/audit.json) and [live publisher checks](evaluations/flood-ner-review-20261014/live_checks.json). All 100 frozen entries remain valid, 98 bodies reproduce, 20 case pointers and 36 supporting hashes pass, and 22 live publication days are corroborated with one recorded Philstar metadata conflict. Corrected offline identity/provenance/malformed-input/line-ending/export-group/Wikipedia retention gaps; 362 checks pass. Pilot labeling remains pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical flood-news collection completed locally:** [100-article acceptance and coverage](evaluations/flood-news-corpus-100-20261014/README.md), [news metadata register](evaluations/flood-news-corpus-100-20261014/news_register.json), [collection outcomes](evaluations/flood-news-corpus-100-20261014/collection_outcomes.json), [coverage data](evaluations/flood-news-corpus-100-20261014/coverage.json) and [separate supporting references](evaluations/flood-news-corpus-100-20261014/supporting_references.json). Includes ABS-CBN/GMA/RMN/Philstar/Tribune across 2022–2026; five Wikipedia revisions remain supporting only. Offline verification and 338 focused checks pass. All articles remain research-only, with balance/licensing/annotation gates recorded. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**NER milestone 1 delivered locally:** [Acceptance and corpus coverage](evaluations/flood-ner-milestone1-20261014/README.md), [source-backed location/fact research](research/flood-ner-semantics-20261014.md), [annotation specification](guides/flood-ner-annotation-v1.md), and [offline tooling](../backend/training/flood_ner/README.md). Includes 54 research-only captures, 20 research cases, validation/DocBin export and the subsequent authorized temporal paragraph repair; 301 checks pass. No trained NER or deployed release is claimed. [Roadmap](plans/lanes-ner-training-plan.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**NER lifecycle roadmap:** The [spaCy NER research and training proposal](plans/lanes-ner-training-plan.md) covers shared-fact research, annotation, model training, integration, proposed acceptance targets, packaging, staged Google Cloud deployment/rollback, monitoring and offline model maintenance. Offline tooling is delivered locally; trained inference remains planned. Weather Insights and separate ChatGPT/MCP experiments are preserved, and presentation expiry is unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Cadence repair deployed:** PR #136 / main 5c6da28 passed 285 Linux release tests, migrations and worker checks. API/jobs and automatic frontend rollout are verified; the natural 11:30 PM Scheduler collection succeeded with zero inference and next risk due 11:45 PM. Shared 3000/8000/live readers retain all six active zones. Expiry remains disabled at the developer's explicit request for video recording. [Deployment and operating limits](evaluations/news-autonomy-fixes-20261013.md).

**Autonomy audit:** A fresh automatic 10:15 PM delivery/worker succeeds with zero LLM requests; local/cloud API readers agree and 99 focused checks pass. Current main is 5febb73 / PR #135. Readiness remains partial: actual risk collection is often 30 minutes despite its 15-minute target, PAGASA parsing is uncertain, one body failure and 186 missing qualified boundaries remain, and expiry is still disabled for the shared historical demo. No application code/settings changed during this audit. [Measured readiness and remaining work](evaluations/news-autonomy-audit-20261013.md).

**Connected presentation verified:** Explicitly authorized historical reconstruction on the same 3000/8000/cloud-database application generates five estimated news zones, with source dates intact and zero LLM requests. Actual Active Zones shows six including the existing citizen zone; localhost and navlanes.live return matching IDs. Operator-disabled expiry keeps the historical zones visible. This later demonstration is separate from the release's earlier current-news baseline. [Evidence and limitations](evaluations/news-connected-demo-20261013.md).

**Latest verified production release:** Main 5c6da28 / PR #136 passed 285 Linux release checks, existing migrations and the release worker. Matching API/news/expiry and frontend rollouts are live. The natural 11:30 PM Scheduler delivery completed collection with zero LLM requests; shared 15/30/60-minute due slots fix the skipped risk tick. Automatic expiry remains disabled at the operator's request for the historical video demonstration. [Deployment evidence](evaluations/news-autonomy-fixes-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Autonomous news release:** Local NLP/source consistency, measurement-first depth, scheduled-worker and real map acceptance, adaptive cloud collection and secure production signing. Optional MCP/framework experiments are excluded from this main-based release. [Verification](evaluations/news-source-validation-20261013/README.md).

**Credit-free news mode live:** Local NLP/source consistency replaces mandatory external inference for the selected mode. Captured replay proves 31 evaluations, 26 source alerts, six estimated zones and zero LLM requests, with repeat/expiry and desktop/mobile acceptance. Focused production API/news/expiry release is active on the existing dependency baseline; MCP remains separate. [Plan](plans/news-source-validation-defense.md), [acceptance](evaluations/news-source-validation-20261013/README.md), [defense/restart guide](guides/news-source-validation-defense.md). Main Git integration and optional frontend diagnostics publication remain pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Adaptive scheduling live (October 13):** The existing Scheduler now checks the protected controller every 15 minutes; collection follows the implemented 60/15/30-minute quiet/risk/uncertain policy. Same main application image, configured machine identity and minimal dispatch roles. Real Scheduler delivery returned HTTP 200 and the dispatched worker completed successfully. [Release evidence](evaluations/news-adaptive-scheduler-release-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Publication checkpoint:** The developer requests this whole local implementation on roi-branch. Real ChatGPT plan sign-in/model discovery are verified; strict live auditing remains blocked at 3/5. MCP remains disabled/unconnected, and Linux/PostGIS shared-upgrade qualification is pending. [MCP startup/rollback](guides/lanes-mcp-pilot-runtime.md), [live results](evaluations/chatgpt-news-live-20261013.md), [offline implementation checks](evaluations/chatgpt-plan-signin-20261013.md). Earlier notices below are historical. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Real ChatGPT plan connection:** Personal-account authorization and model discovery pass. Three of five permitted news POSTs were sent; the final eight-claim response parses but yields seven time reviews and one saved/source depth disagreement. Automatic-news qualification is blocked, with two requests unused; providers/production unchanged. [Measured live results](evaluations/chatgpt-news-live-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier sign-in preparation:** A Windows ChatGPT plan sign-in helper is implemented; actual account authorization/inference is pending. Existing MCP read/preview code is implemented but disabled, and the requested shared dependency upgrade remains a candidate pending Linux/PostGIS qualification. Earlier research paragraphs below describe their historical stage. [Sign-in steps](guides/chatgpt-plan-local-signin.md), [measured checks](evaluations/chatgpt-plan-signin-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier MCP library research:** FastMCP 4.1.0 with qualified MCP SDK 2.3.0 is recommended for a separate Python 3.12 gateway. Local Python already qualifies; dry-run resolution proves current Pydantic and FastAPI/Starlette conflicts and succeeds in isolation. No package installation, source/config change or MCP connection. [MCP library comparison](research/lanes-mcp-library-selection-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier additive MCP research:** Existing OpenRouter/Gemini code/configuration is retained by developer request. The proposed separate gateway offers authenticated saved-evidence reads and later strict audit previews; remote OAuth, SDK dependency isolation and durable review policy/ownership still need implementation. No MCP connection, LLM POST, database write or deployment. [Research](research/lanes-mcp-chatgpt-feasibility-20261013.md), [phased plan](plans/lanes-mcp-chatgpt-review.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest Gemini/Groq research:** The exact Gemini blocker is daily Flash quota exhaustion (20/day). Groq accepts the full strict schema; clarified identity instructions pass eight captured claims, a separate single and conservative negation. Its 1,000 output-token/minute account cap requires smaller batches/pacing. 12/12 shared requests used; 215 offline tests pass. Runtime provider/cloud configuration unchanged. [Provider trial results](evaluations/gemini-groq-live-trials-20261013.md); [official-doc investigation](research/gemini-groq-free-auditing-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**PR #133 synchronization:** Current main history is integrated into roi-branch without source changes, preserving both Gemini repairs. The deleted temporary branch is no longer needed; its commits survive in roi history. [Resolution evidence](evaluations/gemini-repair-integration-20261013.md#pr-133-main-history-synchronization). No new inference or cloud release. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current combined integration:** Gemini news-auditor repair `df16a02` is integrated into roi-branch alongside weather repair `680118b`. Canonical evidence validation/publication gates remain strict. Both Gemini schema and weather settings are retained in `.env.example`; encrypted runtime configuration and existing feed edits are preserved. Live qualification remains blocked at shared 3/12 POSTs; no deployment or additional inference. [Merge acceptance](evaluations/gemini-repair-integration-20261013.md), [news repair plan](plans/news-gemini-audit-repair.md), [initial qualification](evaluations/news-gemini-qualification-20261013.md), [latest quota/weather evidence](evaluations/gemini-weather-followup-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier weather-only publication scope (680118b):** The developer requested pushing all primary changes to `roi-branch`, including verified weather repair, encrypted configuration/history, research/docs and existing feed spacing edits. Gemini auditor branch `df16a02` remains separate/unqualified; no cloud release or additional inference. [Verification and scope](evaluations/gemini-weather-followup-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 13 weather/Gemini follow-up (roi-branch, local):** Public weather errors now use a safe message; backend explanations use Gemini with cache/cooldowns and strict output. 151 backend checks and TypeScript/scoped lint pass; six responsive cases pass for desktop/mobile errors, success and missing forecast. Fresh captured-news audit still returns 429 (shared 3/12 POSTs); scheduled worker extracted 11 articles with zero audits, so live Gemini news acceptance remains blocked. Direct issuing-project quota read confirms Flash 5/minute, 20/day; usage/remaining is unknown. Developer-authorized roi-branch publication is prepared; cloud deployment remains pending. [Follow-up verification](evaluations/gemini-weather-followup-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

New evaluation: [Follow-up verification](evaluations/gemini-weather-followup-20261013.md).

**October 13 Gemini HTTP 400 investigation:** Others report schema-dependent generic errors. Four controlled POSTs reproduce full-schema 400 and same-request minimal-schema 200; two 503 results leave exact constraint isolation unfinished. The inspected deployed v11 auditor matches local source. A Gemini-specific schema/diagnostics/readiness repair is proposed; no backend or deployment change. [Gemini request investigation](research/gemini-news-audit-invalid-argument-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 13 Gemini key replacement:** The supplied replacement key now serves encrypted local defaults, the existing preview and Cloud Run API/news worker through Secret Manager version 2. Version 1 is destroyed; the developer confirmed deleting the original issuing key. Authentication/basic generation and health return 200; the LANES structured audit returns 400 INVALID_ARGUMENT, so flood-audit compatibility remains unverified. [Current runtime record](guides/news-gemini-runtime.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Final-code verification:** Current final-code verification passes **507 combined backend/native checks**. A fresh v20 September 24 normal-worker replay completes five checkpoints/five locations/eleven negative decisions without audits or zones, and unchanged input remains idempotent. Current-code 3004/8004 desktop/mobile preview checks display September 24 first, then preserved v19 September 9 data (33 locations/three ended events/zero active zones). Actual account GET at 01:34 PHT remains 50/50/0; cooldown through 02:04 PHT. The developer skipped V11 live qualification and a fresh eligible Santo Domingo target replay; these remain unverified. Git publication to `roi-branch` is authorized; merged TypeScript/news lint and 46 responsive cases across main/follow-up runs pass. Primary feed/profile edits are preserved. No cloud deployment. [Completion audit](evaluations/news-reliability-goal-20261012.md#final-code-completion-audit-and-latest-isolated-checks). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current construction follow-up:** [Generated-intersection precision plan](plans/news-generated-intersection-precision.md) traces original source hashes and tests conservative float construction under unchanged strict parent/core gates. Current v20 strict real-source construction passes; v11 audit option-index/source-occurrence changes require live production-composition qualification. Actual allowance is 50/50/0; unconfirmed free allowance now defers safely. The requested [manual chat review](evaluations/news-chat-source-review-20261013.md) is complete. No source-polygon repair or policy override. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Completed news reliability implementation (live acceptance skipped):** [Implementation plan](plans/news-reliability-goal.md), [research](research/news-audit-reliability-20261012.md), [source-coordinate repair](plans/news-source-line-precision-repair.md), [remaining audit/corridor plan](plans/news-audit-and-corridor-followup.md) and [current evidence](evaluations/news-reliability-goal-20261012.md). Bounded recovery/diagnostics, compact auditing and the default 1,524-polygon NCR registry are implemented locally. Ordered real replays and responsive previews retain admission/evidence rejections. Sienna/Tatalon plotting/history passes; Santo Domingo target depth-update acceptance remains unproved: local construction is repaired, while current audit qualification and fresh activation replay await confirmed allowance. [Earlier ordered replay](evaluations/news-retry-20261012.md) is preserved. No cloud release. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 12 evening replay retry:** [September 24–25 followed by September 9](evaluations/news-retry-20261012.md). Fresh scheduled replays retain five/33 locations. OpenRouter recovers to 50 available requests; twenty actual batch calls produce four verified text alerts, but footprint gates prevent zones/history and the 19-inch → 10-inch pair expires unverified. Source facts and prior databases are preserved. Preview/browser limitations and remaining acceptance are recorded separately; no application/schema/dependency change or cloud release. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 12 batch auditing:** [Implementation plan](plans/news-batch-auditing.md) and [verification/preview](evaluations/news-batch-audit-20261012/README.md): eight eligible same-version claims share one bounded audit request while retaining separate results; quota-aware deferrals, safe diagnostics and existing Overview details are implemented. 492 offline, 226 native and 14 desktop/mobile checks pass. Initial real quota 52/50/0 prevented positive plotting acceptance; the evening retry above records quota recovery and remaining footprint/audit failures. Separate port-3004 replay preview preserves the existing local snapshot. The developer subsequently authorized documentation updates and Git publication to `roi-branch`; cloud release remains separate. [Planner and publication audit](evaluations/news-batch-audit-20261012/README.md#planner-and-publication-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 12 historical news repairs (local):** Approved article-refresh and heading/locality fixes use existing capture timestamps, reviewed source provenance and scoped original evidence; processing advances to v17. 271 focused checks pass. Final continuous replay recaptures edited GMA content and retains all 26 QC sites plus the 19-inch/10-inch comparison, but real auditor rate limits/HTTP errors prevent any first operational zone. Successful zone-update behavior remains unverified. [Scope and evidence](evaluations/news-scheduled-historical-workflow-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Roi team integration:** [Branch scope, preserved records and final acceptance](evaluations/roi-team-integration-20261012.md). News Intelligence work is pushed first; Jace's compatible updates and the mobile dialog repair are accepted locally, and Chris is already included. 133 backend checks and 103 distinct desktop/mobile browser cases pass across final acceptance runs. The developer retains the manual merge to `main`. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**News Intelligence tabs (local):** [Layout and responsive acceptance](evaluations/news-intelligence-tabs-20261011/README.md) covers the concise Overview, separate Flooded Areas view, shared admin components, expandable diagnostics and preserved read-only workflows. Cloud release remains separate. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Adaptive scheduling publication audit:** [Decision 25](decisions.md#25-database-governed-operational-policy-and-fixed-automation-tick) now records the controller rationale, weather/evidence boundaries, exact Google identity, dispatch reconciliation and release/rollback consequences. [Planner audit](evaluations/news-weather-scheduling-20261011/README.md#planner-and-publication-audit) covers the eight core records, preserved test evidence and dependency/migration state for the requested `roi-branch` push. Cloud trigger activation remains a separate gate. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Automatic weather-based news scheduling:** [Implemented policy and sampled coverage](plans/news-weather-scheduling.md), [local acceptance and real provider probe](evaluations/news-weather-scheduling-20261011/README.md), and [coordinated rollout/rollback](guides/news-weather-scheduling-rollout.md). Collection now follows backend 60/15/30-minute policy; interval editing is removed. Machine-only controller, durable dispatch reconciliation and desktop/mobile status are accepted locally. Cloud remains on its recorded three-hour worker trigger until the separate release. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**News documentation/publication audit:** The eight core records, placement/activation plans and replay guide now distinguish accepted local repairs from open clearance-history, fresh v16 evaluation and shared-release gates. Dependency/SQL migration state is unchanged; catalog lineage, source syntax, local Markdown targets and added-content checks pass. The developer requested publication on `roi-branch`; pushing does not deploy the code or transfer the local simulation database. [Audit record](evaluations/news-shared-context-and-history-20261011.md#planner-and-publication-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Gov. Pascual local acceptance:** The source-preserving OSM locality catalog now connects Sitio Sais/6 to a bounded estimated road candidate. The existing OSM/NOAH worker creates **Zone/Event #60** from the previously verified report. Public APIs and authenticated history searches return **Boni #58, Quirino #59 and Gov. Pascual #60**; source text, labels and per-road facts remain unchanged. **493 focused and 163 native PostGIS checks pass.** This uses the local September simulation; shared/cloud deployment and clearance-only prior-event history remain separate gates. [Fix, provenance and verification](evaluations/news-shared-context-and-history-20261011.md#source-locality-to-road-repair-and-gov-pascual-acceptance).

**Jace branch publication audit:** [Moderation details/map handoff, owner notifications, hydration, daily UTC homepage statistics and Community filters](evaluations/jace-moderation-feed-publication-20261011.md). Includes recorded local acceptance, dependency/credential checks and the requested branch-push scope; production deployment is separate. Jace H. Bellen (Git author Jace; jace-branch), with Codex.

**Community filtering (local):** [API contract, visibility correction and desktop/mobile acceptance](evaluations/community-feed-filters-20261011.md). Sorting/date/status/severity/radius filters reuse the existing feed and map lifecycle; no schema/dependency change or deployment. Jace H. Bellen (Git author Jace; jace-branch), with Codex.

**What to expect when testing:** [Runtime behavior, acceptance steps and remaining accuracy work](guides/pasig-recession-observation-collection.md#what-to-expect-when-running-the-system) explain the saved selected model, eligibility/fallback, fixed issuance, p90 deadline and Unconfirmed expiry. Depth-sensitive predictive accuracy remains unvalidated even though local/cloud integration and hosted display are accepted. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current hosted UI acceptance:** [Rollout 005 and actual desktop/mobile forecast/calculation checks](evaluations/pasig-subsidence-v3-acceptance-20261011.md#hosted-ui-continuation--october-11-425-pm-pht) complete the frontend release gate. Earlier local-only checkpoints are historical. The developer has no additional government files yet; [prepared acquisition specification and verified FOI limitations](guides/pasig-recession-observation-collection.md#government-data-acquisition-specification--october-11-continuation) support the remaining real-outcome/model-accuracy work. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Planner publication checkpoint:** [Eight-document audit and fresh pre-push verification](evaluations/pasig-subsidence-v3-acceptance-20261011.md#planner-and-pre-push-audit--october-11-408-pm-pht) records 166 native backend/database and 88 model/dataset checks, migration compatibility and separate operational, accuracy and hosted-UI status. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Real-outcome dataset continuation:** [Offline pairing and actual collection readiness](evaluations/pasig-recession-collection-readiness-20261011/README.md): 26 checks pass for interval/right-censored same-section pairing, independent reviews, test exclusions, clocks and immutable input hashes. The complete live export has three pending follow-ups across two reports, zero numeric depths and zero eligible episodes. No retraining, production admission or new runtime deployment. [Collection/file contract](guides/pasig-recession-observation-collection.md#offline-pairing-and-qualification). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 11 Pasig expiry v3:** [Engineering acceptance and release](evaluations/pasig-subsidence-v3-acceptance-20261011.md) and [17 post-release active records](evaluations/pasig-subsidence-v3-active-zones-20261011.csv): transient cache repaired, report locality reconciled to final geometry, fallback evidence retention explicit, all current active Pasig zones have saved ML deadlines. Matching shared API/workers are deployed; the new Info UI is verified locally on desktop/mobile. Model accuracy remains unqualified. [Offline depth-shape candidate](evaluations/pasig-depth-shape-candidate-20261011/README.md) shows no improvement; [real observation collection guide](guides/pasig-recession-observation-collection.md) describes the remaining evidence gate. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical pre-fix investigation:** [Availability and numerical audit](evaluations/pasig-subsidence-availability-audit-20261011.md), [22 pre-fix active records](evaluations/pasig-subsidence-active-zones-20261011.csv), [18 depth-sensitivity calculations](evaluations/pasig-subsidence-depth-sensitivity-20261011.csv) and [recession-model research/sources](research/pasig-flood-recession-depth-and-availability-20261011.md). Preserve these original snapshots separately from v3 acceptance.

**Community Feed Local Updates:** coverage now includes Metro Manila weather, traffic, transport and safety/service advisories, as well as flood reports. The saved commuter-news path does not enqueue flood extraction. Local desktop/mobile checks show five actual articles from ten new captures, with publisher/date/source links. Matching cloud API/workers/frontend release is accepted; live desktop/mobile show five actual source-linked articles. [Implementation and verification](evaluations/community-local-updates-20261011.md#commuter-news-coverage--october-11-noon-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Pasig coverage and abstention:** Eligible Pasig polygons can use the shared Pasig model even when their barangay has no local historical outcomes. This is not guaranteed inference for every record. Unverified location, missing observation time without an accepted registration/submission proxy, incompatible depth snapshots, changed/review-pending evidence or unavailable model assets can still produce an explicit unavailable/fixed-fallback state. A saved operational forecast remains visible after expiry even when the current research preview is inactive or stale. Expiry means Unconfirmed, not observed flood clearance; p90 is an experimental policy estimate, not calibrated certainty. [Evidence](evaluations/pasig-ml-automatic-expiry-20261010.md#documentation-and-pre-push-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 10, 9:15 PM recovery accepted:** policy v2 recovers immutable original forecasts after late initialization without bypassing current source/review gates. #17/#18 are now inactive with original p90 deadlines October 9, 7:25:02 AM / October 10, 5:04:13 AM (PHT); event timelines say Unconfirmed. #19/#20/#21 retain their deadlines. Production API `lanes-api-00069-fey` serves 100% traffic; cloud jobs use the matching recovery image and minute scheduling is enabled. The local map exposes saved p10/p50/p90 forecasts at Active Zones → All History → Info, verified on actual desktop/mobile records. 106 backend checks, 10 responsive fixtures and four actual Info workflows pass. Accuracy remains experimental; cloud frontend release is separate. [Acceptance](evaluations/pasig-ml-automatic-expiry-20261010.md#legacy-recovery-and-saved-ui-acceptance--october-10-915-pm). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 10, 8:36 PM: Pasig ML expiry is operational locally and in the shared cloud worker.** API revision `lanes-api-00067-zox` serves 100% of cloud traffic. Independent job `lanes-zone-expiry` runs every minute; the matching news worker also completed successfully. Cloud inference reproduced saved deadlines for pooled zones 19/20 and cross-location zone 21 exactly. Fixed fallback, global pause, source preservation and Unconfirmed expiry remain explicit. Local controls are available on port 3000; the cloud frontend was not released in this scope. Scientific accuracy remains unverified. [386 backend/10 responsive checks and live cloud verification](evaluations/pasig-ml-automatic-expiry-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current expiry checkpoint:** Cloud Boni #23 was deactivated by fixed-deadline maintenance at 6:00:29 PM; earlier visibility snapshots below are historical. The automatic-expiry toggle is implemented locally under System Settings → Evidence expiry and visible on port 3000. Matching cloud API/workers are now deployed; shared policy is unchanged. Earlier local-only checkpoints below are historical. [Expiry semantics and verification](evaluations/automatic-expiry-toggle-20261010.md).

**Current connected reconstruction:** Actual automatic **Zone #23** now appears with cloud Active Zones 17–21 on the normal [port 3000 map](http://localhost:3000/map?lat=14.58323758&lng=121.02823311&zoom=17) and [Admin](http://localhost:3000/admin/map?tab=zones). Original Daily Tribune content/link and September 24 dates are retained. Wrong #22 is deactivated; other 18 zone records are unchanged. Desktop/mobile actual checks and targeted/native tests pass; developer visual review remains pending. Use ordinary startup tasks; the separate private mode below still deliberately selects a different database. [Instructions](guides/local-news-replay.md#connected-source-faithful-reconstruction-on-port-3000).

**Current port correction:** Boni reconstruction now uses the developer's usual [port 3000 public map](http://localhost:3000/map?lat=14.58323758&lng=121.02823311&zoom=17) and [Admin Active Zones](http://localhost:3000/admin/map?tab=zones), with session-scoped login/cache and guarded backend 8001. Use **Start LANES Reconstruction**, reload tabs; **LANES: Use Current Data** plus reload restores normal data. [Current instructions](guides/local-news-replay.md#current-persisted-boni-reconstruction). Earlier 3001 checkpoints below are historical.

**Historical reconstruction checkpoint:** Original Boni reconstruction creates persisted **Zone #56** through the actual system and live auditor. In private mode, public/Admin Active Zones both return `[56]`; the stale review item is excluded; shared inner/outer layers and desktop/mobile interactions pass actual browser checks. Use **Start LANES Reconstruction** only to select that separate historical dataset on port **3000**. Developer visual acceptance remains pending. [Root causes, exact files, verification and local inspection](evaluations/news-boni-corridor-reconstruction-20261010.md).

Earlier checkpoints below preserve their recorded outcomes; the new persisted-zone evaluation supersedes their unfinished Boni status.

[October 10 historical reconstruction and activation corrections](evaluations/news-reconstruction-activation-fixes-20261010.md) — Daily Tribune registration/capture identity, verified passable-zone activation and Admin review publication clock fixed. The requested 4:34 PM reconstruction uses actual system services/provider; Boni publishes a text alert after retry and appears in Needs Review, but four ambiguous sections still prevent a polygon. 180 backend, 47 PostGIS and four responsive checks pass.

[October 10 persisted simulation session](evaluations/news-persisted-simulation-session-20261010.md) — port 3001 routes public/Admin/auth/SSE to one guarded private backend and frozen read clock. Original Boni still creates zero Active Zones. Docker recovered; normal data preserved.

[October 10 placement-alternative overlap correction](evaluations/news-placement-alternatives-20261010.md) — public simulation draws only resolved placement geometry; Admin inspects one alternative at a time. Original Boni remains unresolved and is excluded from public zone painting, with all evidence retained. This supersedes drawing every Boni carriageway in the two-layer overlay. Actual activation and cross-article reconciliation remain open.

[October 10 automatic plot inner/outer layers](evaluations/news-shared-map-renderer-20261009.md#october-10-requested-solid-inner-line-and-transparent-outer-area) — requested public appearance now uses the existing solid core and polygon aura with a backend-derived dissolved decorative halo. Actual desktop/mobile automatic-plot and read-only Boni checks pass; activation remains separate and developer visual review is pending.

[Shared map renderer correction](evaluations/news-shared-map-renderer-20261009.md) supersedes the initial Phase 1 rendering/interaction checkpoint below. News placement now adapts into the existing zone hook; backend presentation union joins exact endpoints and removes coincident coverage. Original Boni remains Needs Review, with four candidates/three display sections; actual activation/admin Active Zones parity is still open. Developer visual review is pending.

[Automatic news map Phase 1 investigation and UI plan](plans/automatic-news-map-phase1.md) — shared preview information, selected-camera focus and zoom-scaled topology-preserving rendering are implemented; visual review is pending before activation work. [Phase 1 verification](evaluations/news-map-ui-phase1-20261009.md) records exact files, 17 responsive checks, original-source live hover/focus and remaining backend/lint limits. Public Boni candidates remain Needs Review.

[Current additive port-3000 simulation](guides/local-news-replay.md#current-port-3000-simulation-session) — normal connected-database API/auth/SSE and existing zones 17/18 are preserved. Original captured September 24 coverage is added as article 25/run 61 with five extracted locations; four backend-generated Boni review lines are additional overlays. Earlier global-private and port-3001 instructions are superseded. Source admission, active-polygon and subsidence acceptance remain open.

[September 24 as simulated present: flood zones and subsidence](evaluations/september24-plotting-simulation-20261009.md#september-24-as-the-simulated-present-zone-and-subsidence-checks) - clock-consistent collector/map checks, future-source exclusion, 43 focused/23 native tests and read-only cloud prediction controls; zero actual-event zones and incomplete estimated-news prediction integration. No report panel changes.

[Connected cloud database and empty interface check](evaluations/news-live-plotting-check-20261009.md#october-9-318-am-screenshot-and-connected-database-reconciliation) - normal port 3000 reads Cloud SQL with 24 excluded articles and zero news locations/zones; historical replay lives only on separate ports 3001/8001 and also produces no active polygon. Actual-news plotting acceptance remains open.

[Corrected September 24 system replay](evaluations/september24-plotting-simulation-20261009.md#latest-correction-actual-source-collector-and-pipeline-replay) - original publisher captures through collector/pipeline, unchanged approvals and chronology, zero new polygons; rejected invented fixture archived. Shared coordinate handoff repaired with browser-free checks; actual-news/map acceptance remains open.

[September 24 manual replay map](guides/local-news-replay.md#october-9-september-24-manual-map-inspection) - isolated port-3001 preview, preserved historical evidence, archived inspection handoff and four modeled Boni suggestions; no active historical zone or browser use.

[Automatic news plotting backend acceptance](evaluations/news-auto-plotting-backend-test-20261009.md) - recovered local Docker, native publication lifecycle and real RSS-parser/extractor near/corner tests produce automatic polygons in the Active Zones API using synthetic publisher/assets/audit fixtures. No browser or live flood publication.

[September 24 historical plotting simulation](evaluations/september24-plotting-simulation-20261009.md) - five readable roads, three wet/two cleared, zero generated polygons; actual publication-time replay exposes source approval, observation-time and affected-section blockers. No live flood data or browser interaction.

[September 9 historical plotting simulation](evaluations/september9-plotting-simulation-20261009.md) - three captured articles, 33 readable locations, 30 timely preliminary claims and zero plotting geometries due to qualified-boundary/road-placement gaps; 84 focused checks pass. Independent auditing and database publication remain unexecuted.

[October 9 news-to-map runtime check](evaluations/news-live-plotting-check-20261009.md) - deployed pipeline enabled, zero news publications/zones, three-hour schedule versus 30-minute settings, Rappler partial failure and 106 focused backend checks; browser work stopped at the user's request.

[Zone #18 approved-citizen simulation](evaluations/zone18-submission-simulation-20261008.md) - full Pasig cross-barangay footprints, immutable submission/approval proxies, preserved unknown observation time and stable read-only forecasts; 77 backend/model/location and 12 targeted responsive checks.

[Calculation details walkthrough](evaluations/calculation-details-walkthrough-20261008.md) - existing Overview explanation of actual AFT coefficients, elapsed-time conditioning and forecast-date arithmetic; source records remain accessible, with no new inputs or prediction behavior change.

[Complete prediction locality and feature-model evaluation](evaluations/pasig-location-feature-models-20261008/README.md) - validated COD geometry for all 30 barangays, future LANES source/review snapshots and private evidence export, actual held-group comparison failures and explicit unselected feature candidates; 256 backend/38 responsive checks and live source-context verification. Includes the [eight-document senior-planner audit](evaluations/pasig-location-feature-models-20261008/README.md#senior-planner-documentation-audit).

[Automatic Pasig location and feature-model plan](plans/pasig-location-and-feature-duration.md) - complete source-backed 30-barangay prediction location catalog, source-qualified condition features, grouped model comparison and trajectory investigation. Location coverage completed; feature input/candidate evaluation implemented, but learned street-specific improvement remains open.

[Pooled Pasig/new-street prediction decision](decisions.md#october-8-amendment-pooled-pasig-prediction-on-new-streets) - 30 canonical experimental input identities, actual training cohorts, registration versus observed references, complete 30-polygon prediction locality versus separate 20-polygon news placement, future LANES evidence collection and pending Unconfirmed/public-update workflow.

[Separate Pasig passability model](evaluations/pasig-passability-model-20261008/README.md) - source-bound nine-projection/seven-barangay/two-summary experimental AFT fit, including Ugong; vehicle recovery is separate from dry/subsidence. Pooled transfer and actual automatic official-zone simulation are recorded in the [current prediction acceptance](evaluations/case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation).

[Pasig barangay coverage audit](evaluations/pasig-barangay-coverage-20261008/README.md) - all 30 barangays have retained historical evidence across annual/wet datasets; 21 have named wet claims across the main/overlay registers, while four belong to the existing duration cohort. Ugong evidence and remaining outcome/boundary/model gates are reconciled without changing immutable inputs.

[Case-linked ML review assistant plan](plans/case-linked-ml-review-assistant.md) and [local acceptance](evaluations/case-linked-ml-review-assistant-20261008.md) — recorded case evidence, immutable staff suggestions, current-evidence review signals, native follow-up acceptance and Active Zone suggestion integration. The later placement correction removes both experimental queues and per-report ML controls from Moderation Center; the accepted prediction UI is the compact Overview summary and read-only inline details. Automatic geometry/evidence selection, explicit pooled transfer and labeled registration simulation are delivered locally without manual fields; forecast-to-Unconfirmed/public retention and independent accuracy remain open. Separate staff follow-up review access and release remain open.

[Community Trending Hotspots verification](evaluations/community-trending-hotspots-20261007.md) — server-ranked place activity, bounded 24/48-hour fallback, consistent desktop/mobile states, nine native PostGIS checks and ten browser checks.

[Duration-model follow-up search notes](evaluations/pasig-duration-model-20261007/followup-search-notes.md) — source acquisition notes and evidence limitations for the conditional study.

[Pasig subsidence model validation](evaluations/pasig-subsidence-validation-20261007/README.md) — numerical/API tests, reproduced source-verified candidates and held-summary lognormal versus exponential comparison; operational prediction remains gated.

[Functional System Settings verification](evaluations/functional-system-settings-20261007.md) — atomic versioned configuration, citizen corroboration, independent news stages, per-depth evidence deadlines, desktop/mobile acceptance and explicit release limits.

[System Settings rollout](guides/system-settings-rollout.md) — matching API/worker/frontend release, fixed 15-minute Scheduler tick, 30-minute database interval, approval activation and rollback.

[Implemented System Settings contract](plans/functional-system-settings.md) — operational rules, retained history and staged activation.

[Live news collection and plotting audit](evaluations/news-live-operational-audit-20261007.md) — successful scheduled six-feed collection, empty eligible cloud claim state, 404 backend checks, desktop/mobile fixture verification, Docker recovery, a live free-auditor timeout and remaining real-article/cadence/PWA acceptance.

[Senior-planner pre-push checkpoint](evaluations/cloud-performance-20261007.md#senior-planner-pre-push-checkpoint) — eight-record audit, reconciled deployed behavior, unchanged dependencies/schema, migration head and user-authorized `roi-branch` delivery.

[Second performance pass](evaluations/cloud-performance-20261007.md#second-pass-shared-polling-and-responsive-weather-handlers) — API/job/Firebase rollout completed for shared DB polling, responsive weather handlers and idle offline warm-up; 37 backend and 16 desktop/mobile regressions plus public smoke checks pass, with rollout limits, rollback and primary-source research.

[October 7 Cloud/application performance verification](evaluations/cloud-performance-20261007.md) — API/job/Firebase rollout completed; 32 backend, 14 distinct browser regressions and public desktop/mobile smoke checks passed. Includes resource evidence, bounded routing, changed refresh, deferred startup, PWA reconnect behavior and verification limits.

**October 7 exact-source auditor repair (current):** The backend now supplies exact quote/offset options; the model copies selected supporting spans, and strict immutable-source validation remains unchanged. **170 focused checks pass**. Live free synthetic probes passed at both 60 seconds and the normal 20-second worker limit, producing historical review without database/public writes. Prompt v2 changes the existing evaluation policy identity; no new package/model/migration or UI design. Matching release, real-article/map/routing and physical PWA acceptance remain open. [Verification](evaluations/phase-36-auditor-evidence-options-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier provider failure (resolved locally by the update above):** A 60-second free synthetic retry received a response but failed exact evidence-offset validation. The timeout diagnostic was implemented and tested; the subsequent exact-source repair above passed synthetic provider acceptance. Release remains pending. [Follow-up evidence](evaluations/phase-36-news-runtime-packaging-20261007.md#october-7-live-timeout-follow-up-earlier-diagnosis).

**October 7 initial runtime packaging checkpoint:** The checked NOAH vector bundle is now versioned under `backend/runtime_data/noah-placement` and verified during Docker build. Final Linux build/offline image verification and **188 focused tests** pass. Free-router configuration is verified; the optional single synthetic provider probe, matching cloud migration/API/job/frontend rollout, real-article and physical PWA acceptance remain open. No live cloud/provider write or deployment was performed. [Verification](evaluations/phase-36-news-runtime-packaging-20261007.md), [exact operator steps](guides/news-zone-release-checklist.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Start with the [project README](../README.md), [agent instructions](../AGENTS.md), and [system design](../DESIGN.md). The files below are grouped by purpose. The eight registered project records retain their established paths so existing workflows can find them.

[Current estimated-road integration verification](evaluations/phase-36-estimated-road-zone-integration-20261006.md) — local automatic corridor activation and existing desktop/mobile map integration; real-article/runtime release and physical PWA acceptance remain open.

[Latest automatic footprint worker verification](evaluations/phase-36-automatic-footprint-worker.md) — 456 distinct local checks; real current source and desktop/mobile map acceptance remain pending.

[October 6 developer-intent plotting audit](evaluations/phase-36-user-plotting-alignment-audit-20261006.md) — historical source comparison that identified the now-implemented estimated activation/centerline gaps; current verification is linked above.

## Project records

- [Cross-location learning decision](decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison) — adopts the implemented private research comparison, source/uncertainty contract and evaluation gates while retaining primary baselines and operational lifecycle separation.

- [Task plan](task_plan.md) — active sprint and backlog.
- [Progress tracker](progress.md) — delivery history.
- [Feature reference](feature-reference.md) — major platform capabilities.
- [Architecture decisions](decisions.md) — significant design choices; [Decision 24](decisions.md#24-purpose-specific-reported-subsidence-proxy-and-prospective-prediction-reference) records the target/reference policy, [Decision 23](decisions.md#23-metro-manila-product-coverage-pasig-duration-study-and-separated-evidence-datasets) records geographic scope and duration-dataset architecture, and [Decision 22](decisions.md#22-separate-observed-flood-status-evidence-expiry-and-predicted-clearance) records status/expiry semantics.
- [Tech stack](tech-stack.md) — technologies and deployment components.
- [System documentation](others/system-documentation.md) — screens, routes, endpoints, and components.
- [Database design plan](others/database-design-plan.md) — schema and spatial design.
- [Bug log](others/bug-log.md) — investigated issues and fixes.

## Plans

- [Historical presentation and Phase E delivery](plans/historical-news-demonstration-phase-e.md): E0–E6 input/processing/history/UI/cloud/rehearsal gates, existing-service reuse, dataset lineage, no-reset scope and truthful occurrence/closure analytics for October 25.

- [spaCy NER research through production operation](plans/lanes-ner-training-plan.md) — shared-fact research, silver annotations, local model qualification/integration, proposed acceptance contract, cloud packaging/deployment/rollback, monitoring and model maintenance; preserves weather/experimental scope.

- [Additive LANES MCP review pilot](plans/lanes-mcp-chatgpt-review.md) — preservation contract, isolated gateway, authenticated reads, strict previews and later gated handoff.

- [Cross-location flood prediction implementation](plans/cross-location-flood-prediction.md) — qualified fixed-prior depth/location AFT experiments and source-bound automatic comparison; primary model promotion remains gated.

- [Flood Zone community updates](plans/flood-zone-community-updates.md) — shared Report Flood panel, editable road extent, New report discard confirmation, Still flooded / No floodwater actions and optional camera evidence and private review exclusively under Spatial Operations → Active Zones; implemented locally.

- [Structured Pasig flood follow-up evidence](plans/flood-followup-evidence-plan.md) — owner observations, independent staff review, existing append-only storage and later duration-dataset qualification.

- [Pasig subsidence model implementation](plans/pasig-subsidence-model-implementation.md) — fitted conditional research AFT baseline, distinct first-recorded-wet target, protected preview API and pending operational validation.

- [Pasig reported-subsidence target](plans/pasig-reported-subsidence-target.md) — adopted proxy target, 37 conditional projections/three summary outcomes, prospective references, source availability and model gates.

- [Flood evidence lifecycle and duration estimation](plans/flood-evidence-lifecycle-and-duration-plan.md) — Metro Manila collection/plotting, Pasig evaluation, reviewed conditional proxy labels and pending prospective training export, conditional two-hour Unconfirmed fallback and model/storage/routing/release gates.

- [News publication backend readiness contract](plans/news-publication-readiness-plan.md) — approved five-table storage tested locally; delivered auditor/evaluation and source-alert lifecycle, claim continuity, transaction/API contracts, geometry/asset gates and remaining lifecycle policy.

- [F4b monitoring telemetry implementation](plans/news-monitoring-telemetry-plan.md) — approved durable discovery/fallback history, tested local migration and remaining rollout/manual acceptance.

- [Priority 5 publication, review, corrections, expiry and frontend plan](plans/news-publication-review-frontend-plan.md) — F1–F4 reading/monitoring implemented, F5 inspection delivered locally; F6 decisions/F7 source-alert visibility delivered locally; operational-zone and integrated release acceptance remain open.
- [Flood event history design](plans/flood-event-history-design.md)
- [Flood report merging plan](plans/flood-report-merging-plan.md)
- [LiPAD & UP NOAH flood placement](plans/lipad-noah-flood-placement.md)
- [News activation safety gates](plans/news-activation-safety-gates.md)
- [RSS news discovery plan](plans/rss-news-discovery-plan.md)
- [Smart auto-activation and hybrid NLP plan](plans/smart-auto-activation-and-hybrid-nlp-plan.md)

## Evaluations and simulations

- [Historical news presentation readiness review — October 21](evaluations/news-historical-readiness-20261021/README.md): completed conversation/code/cloud inspection, 54 component passes and spatial-asset checks; historical persistence, timestamp/analytics semantics, cleanup scope and cloud/Phase E delivery remain open.

- [Desktop history and dataset gap completion](evaluations/flood-ner-desktop-history-gap-completion-20261017/README.md) — reconciled desktop inventory, three qualified validation additions, isolated test outcome and remaining readiness limits.
- [Targeted test collection and desktop history handoff](evaluations/flood-ner-targeted-test-history-handoff-20261017/README.md) — isolated saved-capture review, explicit collection-budget failure, unchanged development candidates and a tested metadata-only desktop inventory.
- [Verified desktop-to-laptop private backup](evaluations/flood-ner-laptop-backup-20261016/README.md) - owner-only v3 delivery, all 19 cloud hashes, restore checks and laptop continuation instructions.
- [October 16 NER publication audit](evaluations/flood-ner-publication-20261016/README.md) - synchronized documentation, constructed tooling regressions, dependency/schema scope and private-file exclusion before roi-branch publication.
- [Additional NER dataset acquisition/readiness](evaluations/flood-ner-additional-dataset-20261016/README.md) - flood-topic draft pool, per-record/source-use holds, tokenizer failure, bounded isolated curation and unmet quotas; no admission/export/training.
- [Gate 3 NER improvement preparation](evaluations/flood-ner-improvement-preparation-20261016/README.md) - 14-question addendum, 48 constructed cases, train/dev coverage, acquisition requirements and [future evaluation protocol](evaluations/flood-ner-improvement-preparation-20261016/future-evaluation-protocol.md); no retraining.

- [First manual NER training run](guides/ner-first-manual-training-20261016.md) - seed 0 PowerShell command, terminal output, logs, stopping and handback to Codex.
- [Gate 3 model-qualification review](evaluations/flood-ner-model-qualification-20261016/README.md) - all 60 passages, 120 model assessments, 391 reconciled events, AI reference questions, supported/pending uses and required qualification work.
- [Held-out NER test evaluation](evaluations/flood-ner-heldout-test-20261016/README.md) - sealed six-model roster, one fixed test attempt, exact/coarse baselines, per-class/language/negative errors, reconciled metrics and preservation.
- [Completed original experiment and bounded validation study](evaluations/flood-ner-validation-study-20261016-v2/README.md) - five successful new runs, reproduced selected models, A/B choice, three-seed variability, preservation and next held-out-test gate.
- [Validation study: partial results and seed 2 repair](evaluations/flood-ner-validation-study-20261016/README.md) - available-model/baseline metrics, verified encoding fix, preregistered unrun recipes and preservation audit.
- [Primary seed 0 training result](evaluations/flood-ner-primary-training-20261016/README.md) - successful manual run, selected development checkpoint, early stopping and checked manual robustness launchers.
- [Baseline/training preparation](evaluations/flood-ner-experiment-preparation-20261016/README.md) - frozen rule mapping, three seed configurations, GPU initialization, development checkpoint tie selection and unchanged-input verification; no training.
- [Qualified training-format export](evaluations/flood-ner-qualified-export-20261016/README.md) - isolated candidate-tokenizer DocBin export, 12 focused tests, complete disk reload, byte-identical replay and preservation of all frozen inputs.

- [Desktop CLI repair and passing corpus tokenizer qualification](evaluations/flood-ner-desktop-tokenizer-qualification-20261016/README.md) - two pinned package replacements, zero candidate alignment errors, 56 passing controls, frozen evaluation contract and preserved corpus/GPU checkpoints.

- [Desktop corpus restoration and blocked tokenizer qualification](evaluations/flood-ner-desktop-restoration-20261016/README.md) - verified 697-file restoration, frozen 400/138/40 counts, preservation checks and the outer CLI NumPy/Thinc blocker.

- [NER saved-pool revision feasibility](evaluations/flood-ner-revision-feasibility-20261016/README.md) — four infeasible scenarios with 332 records fixed, 106 draft paragraph proposals, exact support deficits and unchanged 400/40 corpus; 99 focused tests pass.
- [NER default-adoption correction](evaluations/flood-ner-default-adoption-correction-20261016/README.md) — 58 explicit reassessments, corrected 68-case outcomes, 125/332 derived adopted coverage, 14/68 holds and unchanged 400/40 corpus.
- [NER remaining 68 case decisions](evaluations/flood-ner-remaining-decisions-20261016/README.md) — historical report; completion and 134/380 totals superseded by the explicit correction above. Original evidence is preserved.
- [NER GMA AFP project case decision](evaluations/flood-ner-afp-case-decision-20261015/README.md) — one delegated private-use adoption, derived 71/68 adopted/held article totals and unchanged admission; missing desktop v1 remains unreconstructed.
- [NER acquisition audit and decision supplement](evaluations/flood-ner-acquisition-decisions-20261015/README.md) — 68 browser-capture checks, 69 proposed decision records, precise remaining questions and unchanged admission.
- [NER laptop held-source reassessment](evaluations/flood-ner-held-reassessment-20261015/README.md) — 69 article reassessments, 139-source inventory, one proposed narrow basis, 68 retained research holds, unchanged actual project holds and explicit missing-v1 reconciliation.

- [NER desktop publication verification](evaluations/flood-ner-desktop-publication-20261015/README.md) — 721 passing checks, one skipped, byte-preserving files and private-artifact transfer boundaries for the requested branch publication.

- [NER desktop readiness and route alignment](evaluations/flood-ner-desktop-readiness-20261015/README.md) — standard-library hardware collector, local handoff, MX330-only evidence, optional publisher clarification and unchanged source-use holds.

- [NER held-article clarification preparation](evaluations/flood-ner-held-clarification-20261015/README.md) — four unsent drafts, 69-article question register, blank response forms and preservation checks; holds/admission unchanged.

- [NER private academic-use proposals](evaluations/flood-ner-academic-proposals-20261015/README.md) — 139 article recommendations, 70 recommended/69 held, evidence bindings and measured private-copy inventory; no applied admission.

- [News shared context and history repair](evaluations/news-shared-context-and-history-20261011.md) — narrative-clock, road/locality alias, exact audit-reference and history fixes; automatic Boni/Quirino/Gov. Pascual Zones/Events 58/59/60 verified locally; 493 focused plus 163 native checks; clearance-only prior-event history and production release remain open.

- [Cross-location duration implementation and evaluation](evaluations/cross-location-duration-20261008/README.md) — 36 conditional rows/three summaries, purged transfer/forward tests and verified research bundle; 131 backend and 24 responsive cases, primary baseline retained.

- [Active Zone community updates acceptance](evaluations/flood-zone-community-updates-20261008.md) — original report/update acceptance plus 39 native admin-comparison/editor/growth checks and 14 distinct desktop/mobile scenarios, individual evidence handoff and responsive draft/media review; provider/device/release verification remains pending.

- [Structured Pasig flood follow-ups](evaluations/structured-flood-followups-20261007.md) — local owner observation/staff review/JSON export implementation, existing append-only storage, privacy safeguards, completed source review and pending runtime/browser acceptance.

- [Pasig additional follow-up acquisition](evaluations/pasig-clearance-followup-20261007/README.md) — five new captures, one outcome-only subsidence report and separate vehicle-passability comparisons; independent source review complete, zero new subsidence-duration pairs.

- [Pasig conditional duration-model experiment](evaluations/pasig-duration-model-20261007/README.md) — actual fitted intercept-only AFT artifact, 37 assumption-qualified projections/three summaries, composite interval likelihood, sensitivity/graphs and zero production admission.

- [Exact-source free-auditor evidence options](evaluations/phase-36-auditor-evidence-options-20261007.md) - 170 passing checks, strict source spans, safe HTTP status and successful synthetic free probes at the 20/60-second limits; real-article/deployment acceptance remains open.

- [Phase 36 runtime packaging and release preparation](evaluations/phase-36-news-runtime-packaging-20261007.md) - 897 checksummed NOAH tiles, final Linux image/offline asset checks, 188 focused tests and remaining cloud/live acceptance.

- [Phase 36 trusted current footprint contract](evaluations/phase-36-trusted-footprint-contract.md) — BUG-110 source/incident approval, CRS/full locality/component gates, safe renewal fallback and 398 distinct local checks; real footprint provisioning and worker/map integration remain open.

- [Phase 36 news zone metadata and retained-support repair](evaluations/phase-36-zone-metadata-support-repair.md) — BUG-108/109, native public-zone serialization/routing policy, 37 new cases and 289 distinct passing local checks.
- [Phase 36 BUG-107 activation and refresh repair](evaluations/phase-36-bug107-activation-repair.md) — strict evidence/revision/retry guards, existing transaction constraints, private provenance and 240 distinct passing local checks.
- [Phase 36 integration and completion audit](evaluations/phase-36-integration-audit-20261005/README.md) — original call-chain audit at `67cdffa`, historical 78 passing/two failing checks, remaining metadata/support/trust findings and reproducible runner; BUG-107 repair is recorded above.

- [Automatic source-alert publication and lifecycle](evaluations/phase-36-news-publication-lifecycle.md) — atomic source alerts, supported refresh/clearance, historical supersession, finite Unconfirmed retention, staff controls and public desktop/mobile views; operational zones remain gated.

- [Independent evaluation and spatial coverage](evaluations/phase-36-independent-evaluation-and-spatial-coverage.md) — provider-separated evidence audit, leased immutable evaluation queue, C5 relation coverage repair, twenty Pasig OSM community preview polygons and remaining boundary/operational geometry gaps.

- [Disconnected news placement](evaluations/phase-36-disconnected-news-placement.md) — local v11 locality repair, exact fragments and transparent review auras; operational publication still pending.

- [Approved news publication storage](evaluations/phase-36-news-publication-storage.md) — five models/migration `d7e4b9a21c60`, initial 60 focused checks and separate 59-check pre-push rerun, full/repeated upgrade and downgrade/re-upgrade evidence preservation, immutable history and local Docker socket recovery; no public publication or cloud migration.

- [Pasig follow-up acquisition and collector v3 repair](evaluations/pasig-duration-followup-20261005/README.md) — 819 combined wet observations, eight new official captures, 37 conditional proxy projections/three summaries, original evidence preserved and zero training admission.

- [Pasig source and duration-outcome qualification](evaluations/pasig-duration-qualification-20261005/README.md) — reviewed overlays for 467 wet observations, 221 candidate timelines, three usable reported-subsidence summaries, 37 conditional interval candidates and twelve historical rows; raw evidence preserved, physical-section outcome admission pending.

- [Expanded Pasig and NCR flood-evidence register](evaluations/metro-manila-flood-duration-20261004/README.md) — older-year acquisition, regional coverage, separate historical incident records, explicit clearance candidates, source citations and reproducible coverage summaries; graph exports were removed, while source data and plotting scripts remain.

- [Pasig flood-duration data cleanup, 2021–2026](evaluations/pasig-duration-cleanup-20261004/README.md) — Pasig-only working exports separated into wet reports, clearance summaries, 2021 historical report rows, candidate intervals, DRRMO location/depth context and locality duration references; zero training-admitted examples.

- [First Pasig flood-duration public-report pilot](evaluations/flood-duration-pilot-20261004/README.md) — 18 captured/cited official sources, 398 observations, 37 candidate bounds across three shared clearance episodes, conflicts and reproducible coverage summaries; no training admission or fitted model.

- [Backend publication readiness assessment](evaluations/phase-36-publication-readiness-audit.md) — runtime/storage/deployment audit, mocked auditor defects, seven passing hybrid regressions and confirmed absence of DRRMO duration fields; no live publication or schema change.

- [Needs Review queue and placement inspection](evaluations/phase-36-needs-review-inspection.md) — protected mixed-source reads, server search/location filters, shared report/zone details, related user cards, source styling, reviewed cross-boundary growth with retained coverage, native PostGIS/JWT checks, desktop/mobile workspace, October 4 readiness audit with 70 focused checks and remaining lifecycle acceptance.

- [Backend OSM/NOAH/Pasig placement preview](evaluations/phase-36-backend-placement-preview.md) — local shared extraction/protected API, exact vector assets, 550 distinct passing checks; F5 inspection subsequently integrated, while operational geometry/publication remains pending.

- [Flood Zone rendering and placement integration investigation](evaluations/phase-36-flood-zone-rendering-investigation.md) — shared active-zone/preview renderers, inner/outer geometry roles, runtime placement gaps and recommended backend-preview-first slice.

- [Four-article source/database audit](evaluations/phase-36-four-article-source-audit.md) — complete source rereads, 38-record API parity, faithful depth/clearance labels, generic passability, corrected provinces and local v9 verification.

- [News workflow defect follow-up](evaluations/phase-36-news-workflow-follow-up.md) — approved caution contract, per-road facts, publisher corrections, visible retrieval failures, v8 replay, 555-test branch review, documentation preparation and verified three-hour freshness gap.

- [September 9 production-day replay](evaluations/phase-36-september9-production-day-replay.md) — three actual articles, 33 audited locations, reconstructed discovery, private persistence/API checks, v7 corrections, RSS/GDELT audit and incomplete visual verification.

- [September 24 historical flood replay](evaluations/phase-36-september24-historical-replay.md) — actual publisher retrieval, street-fact corrections, v6 city-context reconciliation, private saved replay, PostgreSQL parity and pending release/placement gaps.

- [News Intelligence content correction and release](evaluations/phase-36-news-content-quality-investigation.md) — foreign/prevention false-positive audit, shared evidence/geography fixes, preserved versioned history and verified production rollout.
- [Automatic pipeline plan alignment audit](evaluations/phase-36-automatic-plan-alignment-audit.md) — automation alignment, remaining integration/telemetry rollout dependency, runtime OSM dependency isolation with 140 passing checks and residual raw-PBF restriction.
- [F4b durable monitoring verification](evaluations/phase-36-f4b-monitoring-check.md) — 214 news regressions, PostgreSQL migration/queue checks, local head and remaining visual acceptance.

- [Phase 36: F2 article browsing verification](evaluations/phase-36-f2-article-browsing-check.md)
- [Phase 36: F3 unified news reading and F4a source monitoring verification](evaluations/phase-36-f3-result-browsing-check.md)
- [Phase 36: Open article fallback check](evaluations/phase-36-open-article-fallback-check.md)
- [Phase 36: Three 2026 flood article extraction check](evaluations/phase-36-three-article-check.md)
- [Phase 36: Three full-article backend simulation](evaluations/phase-36-new-article-service-simulation.md)
- [Phase 36: Publisher body and pagination audit](evaluations/phase-36-publisher-body-and-pagination-audit.md)
- [Phase 36: Santo Domingo article-to-road-span audit](evaluations/phase-36-sto-domingo-road-span-audit.md)
- [Phase 36: Reusable article-to-road match check](evaluations/phase-36-reusable-road-match-check.md)
- [Phase 36: NOAH road-section ranking check](evaluations/phase-36-noah-road-ranking-check.md)
- [Phase 36: Article and DRRMO road-section context check](evaluations/phase-36-article-road-context-check.md)
- [Phase 36: Metro Manila OSM and NOAH coverage audit](evaluations/phase-36-metro-spatial-coverage-audit.md)

## Guides

- [Desktop NER history inventory](guides/ner-desktop-history-inventory.md) — safe roi-branch pull, direct helper command, desktop Codex prompt, historical Drive backup and private-file availability; run inventory before restoration or training.

- [Flood NER reference-scope addendum v1](guides/flood-ner-reference-scope-addendum-v1.md) - prospective conventions and all 14 historical questions; original annotations/scores remain frozen.

- [NER desktop preflight](guides/ner-desktop-preflight.md) — run the read-only inventory on the RTX desktop before selecting isolated GPU dependencies; no news or environment installation is performed.

- [News-zone release: exact operator steps](guides/news-zone-release-checklist.md) - free-only synthetic auditor probe, reviewed Git release, Cloud Build migration/API/job checks, separate Firebase rollout and controlled live acceptance; includes Docker socket recovery.

- [News publication/lifecycle operator guide](guides/news-publication-lifecycle.md) — explicit saved-article pipeline, current-policy gates, public/staff reads, retention, retries and rollout limitations.

- [Independent news claim evaluation](guides/news-claim-evaluation.md) — explicit provider/model configuration, bounded seed/evaluate handoff, safe retries and no publication writes.

- [Reviewed barangay boundary assets](guides/news-barangay-boundary-assets.md) — versioned polygon identity, checksum and coverage requirements.

- [News placement preview and NOAH catalog](guides/news-placement-preview.md) — deterministic build, external runtime assets and protected immutable-evidence reads.

- [Private local News Intelligence replay](guides/local-news-replay.md) — Docker test database, guarded historical article persistence, loopback launchers and return to cloud-backed development.
- [Flood history verification](guides/flood-history-verification.md)
- [Routing logic](guides/routing-logic.md)
- [Vehicle passability](guides/vehicle-passability.md)

## Research and capstone

- [MCP library comparison](research/lanes-mcp-library-selection-20261013.md) — stable framework choice, real resolver conflicts and successful isolated dependency resolution.

- [LANES MCP/ChatGPT feasibility](research/lanes-mcp-chatgpt-feasibility-20261013.md) — official-doc review and actual dependency/auth/read/ownership integration gaps.

- [News audit reliability and placement repair research](research/news-audit-reliability-20261012.md) — measured batch payload overhead, timeout/streaming and model-routing diagnosis, official/GitHub/Reddit/DEV/Stack Overflow findings, confirmed Pasig-only placement coverage and ordered repair/acceptance proposal. Research complete; implementation and new live benchmarks pending.

- [Cross-location flood prediction research](research/cross-location-flood-prediction.md) — literature-backed regionalization, partial pooling, transfer learning and ensembles; current model/dataset audit, recommended depth-aware AFT investigation, uncertainty limits and staged integration/acceptance. Research and a separate local comparison are delivered; primary model selection remains pending.

- [Research documentation follow-up notes](research/chapter1-3-revision-notes.md) — scope alignment, authentic Chapter III result boundary, and items to revisit after system features are implemented and evaluated; working notes only.

- [Flood-duration dataset source register](research/flood-duration-data-sources.md) — report citations, earlier-source acquisition inventory and recent public-study/simulation metadata; distinguishes reviewed/obtained/admitted status and contribution limits.

- [Metro Manila flood-duration literature review](research/metro-manila-flood-duration-rrl.md) — official Pasig consultation durations, recent August 2026 wet/clear chronologies, contemporary MMDA access leads, local studies, shared ML candidates and data-sufficiency limits.

- [Automatic flood expiry and duration research](research/flood-expiry-and-duration-research.md) — Pasig CSV/workbook audit, NOAH/Google/PAGASA/weather datasets, geographic limits, censoring-aware model comparison and documentation requirements.

- [Routing engine research](<research/Routing Engine Research.md>) — research context; use the current [tech stack](tech-stack.md) and [decisions](decisions.md) for adopted architecture.
- [Capstone defense reviewer](capstone/capstone_defense_reviewer.md)
- [Capstone defense Q&A and suggestions](capstone/capstone_defense_qna_suggestions.md)

`others/` also contains local, Git-ignored working notes. Those notes are outside the shared documentation index.
