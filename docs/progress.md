# LANES — Progress Tracker

> **Last Updated:** October 21, 2026, 03:24 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Shared Spatial Operations queues — completed locally

Active Only now groups nearby zone polygons across sources before filtering/pagination and shares cards and browsing controls with Needs Review. Confirmed matching road/city pairs use 500 m; all other pairs use 50 m, with complete-link membership and no zone creation-time cutoff. Group inspection retains individual evidence, map focus, contributors, public updates, editing and confirmed deactivation. All History remains individual records. Bulk selection is page-scoped and its action is available in the mobile panel.

**73 backend checks pass** (48 queue/review unit/HTTP regressions and 25 native PostGIS/expiry-policy checks). **34 distinct desktop/mobile browser checks pass**, including 320 px layout, filters/back navigation, group/member pagination, errors, explicit bulk payloads, report-to-zone handoffs, forecast details and edit-draft/save regressions. TypeScript and focused changed/new-component lint pass. LiveMap retains its 12 existing lint errors with no introduced signatures. Native checks apply existing migrations to head in an owned disposable database, which is removed afterward. No SQLAlchemy model, dependency or deployment changes. [Acceptance and limits](evaluations/spatial-zone-queues-20261021/README.md). Git publication is limited to `roi-branch`. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Chris frontend changes integrated into roi-branch

Preserved the Phase D checkpoint `64c49413` and integrated Chris's reviewed `5aeaafc9` without conflicts. Legal dialogs, admin map focus, Flood Events dialog, saved-place controls, mobile route/report behavior, profile spacing and drawer scrolling are retained alongside Roi's continuous feed. Fixed touch-trigger focus restoration and aligned browser fixtures/selectors with the merged UI.

**41 browser checks pass across desktop/mobile Chromium; three desktop cases are intentionally skipped because their controls are mobile-only.** TypeScript passes, isolated lockfile installation succeeds, and changed legal/test files have zero lint errors. Changed production files retain 95 baseline lint errors with no new error signatures. Backend, migrations, NER assets and News Intelligence UI match the checkpoint. [Evidence and limits](evaluations/chris-integration-20261021/README.md). No push, deployment or Phase E implementation. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Phase D — backend monitoring and error classification passed locally

Sources now separate registry eligibility, worker selection, global activity and saved feed/body health. Collection exposes retrieval counts/filtering independently of flood eligibility; excluded articles remain excluded. Feed history adds the accurate saved/seen counter and monitoring identifies the uncomputed publication-delay metric. Rules-only extraction no longer loads audit settings; bounded audit configuration failures leave automation status readable and stop evaluation before claims. Snapshot versus result/storage failures remain distinct.

The existing runtime JSON preserves the last ten completed attempts, known-stage errors/outcomes and Cloud Run retry identity. Successful retries retain earlier failures; skipped collection does not advance retrieval success. Cancellation and aggregate failures are not recorded as success. **608 distinct tests pass (21 new), without skips**, with owned PostGIS persistence/lease/publication checks and 788-input / 407-graph inference-free parity. [Report](evaluations/rss-ner-monitoring-20261021/README.md) · [Aggregate](evaluations/rss-ner-monitoring-20261021/summary.json). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

Read-only cloud logs confirm `lanes-news-discovery-mnmjd` attempt 0 exited 1 and attempt 1 exited 0. The original collection reason is missing from retained logs; the disposition preserves that uncertainty and claims no publisher recovery. All 9,796 prior receipts remain unchanged. One owned PostGIS container is stopped with PID zero and private test evidence retained. No new schema/dependency/model/rule/frontend/neural-inference/cloud-write/deployment/activation change. **Next is Phase E**, carrying all visible monitoring corrections; Phase F 403 and production gates remain open.

**Earlier checkpoints below are historical.**

## NER documentation handoff — October 21, 2026

Prepared a [groupmate reading guide](guides/ner-groupmate-handoff.md) consolidating model creation, annotation/data structure, 345/60/60 coverage, training/selection and saved recognition results, with explicit silver-reference and rule-based context limitations. Added a [pending-branch review](evaluations/ner-handoff-review-20261021/README.md) distinguishing shareable NER documents/code, ignored private artifacts and unrelated feed changes. Tables reference saved aggregates; no training, inference, migration, commit or push ran. Documentation prepared by [@roicambe](https://github.com/roicambe) (Roi Cambe).


## Phase C3b — RSS admission, native readers and downstream acceptance passed locally

Connected controlled native collection/corrections and exact feed-timezone/body provenance to the qualified runtime, durable results, intended-method group readers, nullable-confidence placement, native source evaluation and existing publication gates. Newer failed/pending runs cannot revive older cards/publications; zero-claim corrections append review without fabricated clearance. Legacy scheduled defaults remain unchanged.

**754 distinct tests pass without skips**, plus 355 retained-output replay / 788-input / 407-graph parity, Linux full-pipeline preflight and eight fictional subprocess probes. The single one-CPU / 3-GiB attempt processes eight mocked-RSS inputs and two pre-existing short controls in one session; all 4,483 neural spans and 53 reviewed predictions match. Four native cards and three source/evaluation rows persist; duplicate inference is zero. Retained publication is paused and creates no decisions, alerts or zones. Positive publication uses separate fictional evidence tests. Peak 2,492.09 MiB; main pipeline 75.772 s; longest article 62.723 s; cleanup 0.309 s. [Report](evaluations/rss-ner-rss-integration-20261021/README.md) · [Aggregate](evaluations/rss-ner-rss-integration-20261021/summary.json).

All 1,085 frozen source bindings and 3,639 predecessor receipt files verify unchanged. Earlier preparation failures are preserved; the first package's missing reader module failed preflight before any neural attempt. A private database dump retains evidence; five owned containers are stopped with PID zero and the internal network removed. No new dependency/schema/model/rule/frontend/shared-cloud/deployment change. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**Local Phase C acceptance is complete; production activation remains gated. Next is Phase D monitoring/error classification**, followed by Phase E interface and Phase F 403 investigation. The dated cloud partial-attempt finding is still open; the 60/15/30 policy remains unchanged.

**Earlier checkpoints below are historical.**

## C3a review follow-up — bounded CLI startup errors

Protected application/dependency imports before native-worker processing begins. Invalid settings now return `ner_configuration_invalid` / exit 1, unexpected import failures return `ner_runtime_failed` / exit 1, and startup cancellation returns `ner_runtime_cancelled` / exit 130. Partial imports cannot reference uninitialized exception classes. Error output contains one JSON record without raw diagnostics; normal argument handling and existing worker guards remain intact.

**16 focused CLI checks pass:** seven existing checks plus nine fresh-interpreter cases. The seven new startup-failure cases failed before the correction; fresh children prohibit database connections, network connections and subprocess launches. Historical C3a receipts (613 files across the two preparation/acceptance packages) are unchanged, and this later CLI source delta has its own receipt. [Verification](evaluations/rss-ner-cli-bootstrap-20261020/README.md). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

This fixes backend terminal/process reporting only. No inference, schema, dependencies, frontend, cloud or activation changes; overall Phase C and the C3b acceptance work remain open.

**Earlier checkpoints below are historical.**

## Phase C3a native runtime/queue boundary — passed locally

Connected native immutable capture, independently bound pipeline identity, one lazy Linux model subprocess and owned durable completion in a separate disposable-local service/entrypoint. Legacy scheduling/processing remain unchanged. Shared 450-second invocation and 125-second article budgets include CPU normalization and bounded SQL; the existing 300-second lease/backoff remain authoritative.

**251 checks pass** (224 software / 27 PostgreSQL), plus Linux queue/timer preflight and eight fictional subprocess probes. The one authorized one-CPU / 3-GiB run completes all ten retained inputs, matches all 4,483 neural spans and 53 reviewed predictions plus exact graph/projection output, saves twenty legacy/native versions and performs no duplicate inference. Peak 2,339.29 MiB; job 70.074 s; longest article 62.238 s; cleanup 0.515 s. Four owned containers are stopped and the internal network removed. No alerts/publication/zones are created. [Report and aggregate](evaluations/rss-ner-native-worker-20261020/README.md). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

All six prior receipt packages/1,511 files and trained/runtime/rule assets remain unchanged. Failed preparation receipts and the frozen successful attempt are retained; the final thin-CLI interruption/error reporting correction has seven separate checks and a distinct source freeze, with the one post-integration source delta declared. No second inference attempt or resource escalation occurred.

**Next: C3b** RSS admission/corrections, original feed provenance, intended-method native readers, downstream compatibility and controlled end-to-end acceptance. Overall Phase C, automatic NER and production release remain open. No schema, dependency, frontend, shared/cloud or deployment change.

**Earlier checkpoints below are historical.**

## Phase C2 projection/source evidence — complete locally

Implemented the separate `news_ner_durable` adapter: independently trusted asset identities, native capture/publication provenance, exact Unicode graph recomputation, conservative occurrence-based compatibility projection and `source-ner-v1` checking. Unknown confidence/time remain unknown; joint/collective/LOCAL_AREA facts and projection omissions retain explicit native evidence. Native-only groups use exact graph references to meet the unchanged 8 MiB result bound.

**225 checks pass** (211 software / 14 disposable PostgreSQL). Complete retained replay preserves 355 outputs, 352 saved prediction records and all 53 reviewed predictions; cached parity matches 788 inputs / 407 saved graphs. Largest result is 8,203,832 / 8,388,608 bytes. All 17 retained compatibility claims remain review-only because observation time is unresolved. Five prior packages/1,327 receipt files and all C1 source bindings remain unchanged. Failed/partial attempts are preserved; no new inference or runtime qualification occurred. [Report and aggregate](evaluations/rss-ner-native-projection-20261020/README.md). Owner: Roi Cambe.

**Next: C3** runtime/queue budgets, RSS admission/corrections, intended-method native readers/nullable-confidence consumers and controlled end-to-end acceptance. Automatic NER and the scheduled native evaluator remain disabled. No schema, dependencies, frontend, shared/cloud or deployment changes. The owned local server is stopped; existing placement/publication and 60/15/30 scheduling remain gated/unchanged.

**Earlier checkpoints below are historical.**

## Phase C1 method/history boundary — 93 checks pass

Queue claims/completion retain explicit method, pipeline and immutable version identity. Native and legacy work cannot cross even with colliding pipeline strings; native enqueue requires an explicit identity. Saved-run schemas preserve native graph/proposals/abstentions/groups/provenance and unknown confidence; unsupported versions return bounded HTTP 409. Existing scalar card/evaluation consumers remain closed to native data, which stays inspectable in attention/history. [Report](evaluations/rss-ner-method-boundary-20261020/README.md) · [Aggregate](evaluations/rss-ner-method-boundary-20261020/summary.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**81 software and 12 PostgreSQL checks pass**, including concurrency, retries/leases, Unicode/role/graph serialization, protected read-only APIs and JSON-null discriminator rejection. Both owned disposable servers are stopped; unchanged migrations reach head. Four prior runtime/schema receipt packages remain immutable. Eight current-source differences from the old runtime freeze (including the approved model line) are explicitly recorded separately.

**Phase C remains open.** Next is native projection/deterministic source checking, then runtime/session-budget, admission/correction and intended-method/native-group reader integration with end-to-end acceptance. Default writers remain `rules_only`. No inference, live fetch, new migration/dependency, shared/cloud mutation, UI or deployment change. The 60/15/30 policy remains untouched.

**Earlier checkpoints below are historical.**

## Approved NER mode schema — implemented and locally verified

The focused SQLAlchemy check and manually authored revision `e8a6f1c2d903` after `d7e4b9a21c60` permit `ner_rules_v1` alongside `rules_only`. The finalized constraint name and every other schema object/history rule are preserved. **66 unique checks pass:** 23 focused schema cases, 37 publication-storage regressions, four queue regressions and two harness-cleanup cases. Fresh/repeated upgrade, exact fictional row/link preservation, legacy rollback/re-upgrade, atomic native-row/drift refusal, generated SQL and observed exclusive-lock contention pass. [Verification report](evaluations/rss-ner-mode-schema-20261020/README.md) · [Aggregate](evaluations/rss-ner-mode-schema-20261020/summary.json).

Only owned disposable loopback PostGIS databases were used, and their container is stopped. Zero inference, shared/cloud DDL, dependency or deployment changes occurred. Failed runtime attempts and passing three-GiB artifacts remain unchanged; the single authorized current model-check delta is recorded separately, with all 1,039 other qualification bindings preserved. **Next: Phase C native readers, worker isolation, RSS admission, runtime/queue integration, extraction/source checking and publication compatibility.** Writers remain `rules_only`; automatic NER processing and News Intelligence interface work have not shipped.

**Earlier checkpoints below are historical.**

## Phase B passes locally — one CPU / 3 GiB, full workload and reviewed article

The explicitly authorized single frozen three-GiB attempt completes **355/355 requests**, matching **352/352 retained neural records**, all **53 reviewed-article predictions plus its saved proposal/graph**, and all 355 live graph bindings. Cached parity remains 788 inputs / 407 saved graphs. Peak cgroup consumption **1,972.21 MiB** passes below **2,688 MiB**, and clean loaded-model shutdown/reaping succeeds in **0.33864 s**. [Independent measured report](evaluations/rss-ner-runtime-phase-b-3g-20261020/README.md) · [Aggregate](evaluations/rss-ner-runtime-phase-b-3g-20261020/summary.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Cold readiness **2.28559 s**, passage p95 **0.04511 s**, prior complete-article maximum **0.65357 s**, reviewed article **0.17172 s**, maximum-length stress **12.27257 s** and complete session **28.60577 s** pass their unchanged deadlines. Thirty-one constructed checks, eight real fictional fault checks, real syscall denial, deliberate OOM containment and independent inference-free receipt/output verification pass. Both failed profiles, original runtime/model/rules/V46 and historical evidence remain unchanged; only separate versioned qualification tooling/tests and documentation are added. Prior unresolved source facts/research limitations remain explicit.

**Gate B passes for the approved local one-CPU / three-GiB profile; no Cloud Run readiness or production activation is claimed.** No extra inference retry, dataset/retraining, external dependency, schema/database connection/write, automatic-processing/UI wiring, cloud resource/migration or deployment change occurs. The inspected one-GiB production job and 60/15/30 policy are untouched by this task. **Next:** separate approval of the existing mode-check schema proposal, then Phase C controlled integration and later cloud/full-job verification.

**Earlier checkpoints below are historical.**

## Phase B authorized 2-GiB follow-up — maximum input completes; headroom fails

Executed one separately frozen local one-CPU / 2-GiB qualification using new versioned controller/probe/verifier/resource-guard tests. Preserved the original failed one-GiB attempt and every runtime/model/rule byte. All 345 training passages, six complete articles and three stress cases complete; **351 saved neural comparisons and 354 graphs** reconcile. **Phase B remains open:** combined peak reaches **2,048 MiB**, exceeding the **below-1,792-MiB** gate. The guard stops before the reviewed 53-prediction article; loaded-model shutdown/reaping succeeds in **0.35039 s**, child exit 0, with no measurement OOM. [Independent outcome](evaluations/rss-ner-runtime-phase-b-2g-20261020/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Twenty-five constructed checks, eight actual fictional subprocess checks, syscall denial, separate disposable OOM containment and 788-input / 407-graph cached parity pass. Cold readiness is 2.12705 s, passage p95 0.04295 s, completed-article maximum 0.62650 s and maximum-length stress latency 11.27966 s. Memory measurements and incomplete-workload status remain explicit. No automatic retry, further resource escalation, new data/training, schema/database write, cloud change, deployment or automatic processing follows.

**Next decision:** a proposed one-CPU / 3-GiB local qualification with below-2,688-MiB peak, or a separate design review if larger resources are unacceptable. Neither is authorized by this completed 2-GiB run. Phase C and schema/release gates remain pending.

**Earlier checkpoints below are historical.**

## Phase B runtime delivered — one-CPU / 1-GiB qualification failed

Implemented the separate supervised Linux NER subprocess, authenticated persistent model loading, bounded sequential IPC, supervisor graph recomputation, deadlines/session budget, seccomp network denial and cleanup. Preserved V46 and normal processing. **Phase B is not complete:** the single frozen attempt hit 1 GiB on the existing 100,000-character fictional input, exceeding the below-896-MiB requirement; no retry or resource increase followed. [Measured outcome](evaluations/rss-ner-runtime-phase-b-20261020/README.md) · [Guide](guides/ner-subprocess-runtime.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Independent inference-free verification reconciles all 345 training and six complete-article predictions, 353 completed graphs, 788 cached inputs / 407 saved graphs, resource receipts and stopped child/container state. Nineteen constructed checks, eight real fictional subprocess probes, syscall denial and separate disposable-container OOM containment pass. Cold 2.298 s, passage p95 0.04272 s and completed article maximum 0.63465 s pass their partial workload limits. The reviewed 53-prediction article, maximum-length response/latency and successful full model-session shutdown remain unmeasured. Frozen identities, snapshots and failed receipts stay private; only aggregates are published.

**Next:** a separate resource-qualification decision within Phase B. Phase C, schema approval, monitoring/interface work, 403 investigation and production release remain gated. No new dataset, retraining, model/rule tuning, database connection/write, schema edit, external dependency, normal Dockerfile/build change, cloud setting/deployment or automatic-processing wiring occurred. The 60/15/30 policy is unchanged; no new live-cloud health claim is made.

**Earlier checkpoints below are historical.**

## Community Feed — Continuous Infinite Scroll & Navigation Refresh Delivered

Removed the traditional page-by-page numbered desktop pagination (`<nav aria-label="Feed pagination">`) and the separate mobile-only append state from the Community Feed center panel in [`FeedPage.tsx`](../frontend/src/features/feed/FeedPage.tsx). Implemented a unified, Reddit- and Facebook-style continuous feed stream across both desktop and mobile platforms:

- **Unified Infinite Query Streaming**: Refactored feed data ingestion to TanStack React Query's `useInfiniteQuery`, managing page parameters, fetch queries, and deduplication atomically in `postsToDisplay`.
- **Automatic Sentinel Loading**: Integrated an `IntersectionObserver` sentinel element (`rootMargin: '350px'`) that automatically triggers the next batch of posts as the user approaches the bottom of the feed on all viewports, backed by an accessible fallback *"Load more posts"* button and *"You're all caught up! ✨"* end indicator.
- **Preserved Feed Capabilities & Tri-State Optimistic Voting**: Maintained 100% of existing functionality, including Recent/Oldest sorting, UTC date range filters (today, 24h, 3d, 7d), flood status filters, severity levels, and nearby auto/expanded radius checks. Upgraded `voteMutation` to optimistically mutate across all loaded pages within `InfiniteData<FeedResponse>`, maintaining 0ms UI transitions, toggle-off, vote-switching, authoritative backend synchronization, and error rollback.
- **Desktop & Mobile Navbar Feed Refresh**: Updated the Feed link across [`FloatingNav.tsx`](../frontend/src/features/navigation/FloatingNav.tsx) (desktop header navbar), [`MobileNav.tsx`](../frontend/src/features/navigation/MobileNav.tsx) (mobile bottom navigation bar), [`LeftSidebar.tsx`](../frontend/src/features/feed/LeftSidebar.tsx), and the mobile drawer menu. Clicking the Feed button smoothly scrolls the user back to the top of the page (`window.scrollTo({ top: 0, behavior: 'smooth' })`), clears query filters if applied, and dispatches `lanes:refresh-feed` to reset the infinite query back to page 0 with the newest incoming reports.
- **Verification**: Updated Playwright end-to-end specifications in `tests/community-feed-filters.spec.ts` to test continuous streaming and navbar reload. Passed `npx tsc --noEmit` and production `npm run build` with zero errors. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Phase A delivered — RSS-to-NER integration contract and schema proposal

Completed the six Phase A specification tasks in the [current roadmap](task_plan.md#phase-a--establish-the-integration-contract). The [contract](plans/rss-ner-integration-contract.md) records the actual discovery/capture/processing/placement/evaluation/publication/reader call chain, pre-NER legacy recognizer dependencies, exact-body offset requirements, lossless native artifact and conservative compatibility projection. It specifies old/new method dispatch, source-consistency checking without an old-recognizer agreement requirement, matched correction reconciliation, errors and saved-read interfaces. All **23 acceptance scenarios are specified, not executed**. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Prepared the [minimal processing-mode proposal](plans/rss-ner-processing-mode-schema-proposal.md): preserve tables/columns/history/uniqueness and extend only the allowed-mode check to include `ner_rules_v1`, subject to explicit human approval. Upgrade, mixed-version release, worker isolation and refusal of lossy downgrade are documented. Schema approval, runtime qualification, automatic processing, monitoring/UI fixes, detailed 403 investigation and production release remain open. **Next: Phase B runtime qualification; this does not require schema implementation.**

Verification for this delivery is source/consumer inspection plus Markdown link, contract/checklist and diff checks. No application/model/migration/dependency edit, inference, dataset/reference access, automated application tests, database access/write or cloud mutation occurs. V46 and historical research evidence remain unchanged. The earlier interface-only next-step descriptions below are historical; automatic RSS-to-NER integration is the current agreed scope.

**Earlier checkpoints below are historical.**

## Documentation audit — current NER milestone synchronized

Checked the task plan, roadmap, guide, system/issue records and documentation index against v46's saved verification receipts and current worker/host wiring. Backend completion is recorded correctly; clarified that the one remaining preview task includes admin-interface planning, implementation and mobile/desktop verification. Updated the feature reference's stale current checkpoint and the tech-stack runtime description to include the v44 repair stage. Historical results remain intact. This audit changes documentation only; no tests or inference were rerun. [Current task](task_plan.md#v46-backend-location-repair-integration--complete-and-verified). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## V46 qualified location repairs — backend integration delivered

Added a verbatim v44 runtime copy and shared v40/v44 adapter used by worker and host. Original neural predictions, ordered proposal hashes, stage-labeled abstentions and effective locations stay separate. Host validation recomputes the complete chain and graph; source URL and v1 fields are retained. [Outcome](evaluations/flood-ner-backend-location-v46-20261020/README.md) · [Verification](evaluations/flood-ner-backend-location-v46-20261020/verification.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**1,281 tests**, 788 cached inputs, 407 saved graphs, 418 applicable fixtures and three repaired-view checks pass. One real isolated-worker request through the API with fake read-only storage preserves all 53 neural mentions and matches the full saved combined output. Actual isolation, cleanup and restored disabled flag are independently verified. The same article gains remain eight occurrences / 40 facts; 11 rows remain unresolved. Five intended application/test changes are reconciled against 20 snapshots; frozen research/model/reference/excluded evidence remains intact. No database access/write, frontend, environment or normal-processing/map change occurs. Next is the admin-panel interface plan.

**Earlier checkpoints below are historical.**

## V45 scoring qualification — completed using saved evidence

Delivered strict JSON-list/tuple normalization, immutable original/effective checks, three source-authored repaired-view oracles, frozen reassessment controller and independent verifier. **176 scoring-only tests pass**; all 418 applicable candidate cases and three conditional pairs pass per method, with 788/788 original-mention checks. Original fixture control expectations remain unchanged. [Outcome](evaluations/flood-ner-location-scoring-v45-20261020/README.md) · [Verification](evaluations/flood-ner-location-scoring-v45-20261020/verification.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Missing-junction, boundary-replacement and combined views qualify for a later proposal; the type family has no real correction and remains unqualified. Saved article findings remain eight corrected occurrences / 40 restored facts / 11 unresolved rows. All 34 targets, 19 affected rows, 93 facts, eight earlier complete rows and seven historical misses reconcile. Independent counts/source/provenance/preservation verification passes. No extraction, inference, worker rerun, model/rule/reference change, database access or backend promotion occurred; historical v44 remains unchanged.

**Earlier checkpoints below are historical.**

## V44 junction location study — completed with blocked outcome

Delivered separate source-supported additions/boundary/type proposals, 36 fictional cases, frozen worker/controller/scorer and independent saved-output verification. One **788-input** attempt restores **40 article facts across eight measured rows** in the combined view; 11 rows remain unresolved. All 34 target occurrences, 19 rows, 93 facts and seven historical misses are reconciled privately. The eight earlier complete rows and six earlier recoveries remain intact. [Outcome](evaluations/flood-ner-location-repair-v44-20261020/README.md) · [Verification](evaluations/flood-ner-location-repair-v44-20261020/verification.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

560 pre-freeze software checks pass. A frozen scorer serialization defect and three preserved fixture conflicts block qualification; independent normalized comparison of saved new-case spans matches 36/36 for each method but does not replace official scores. Training controls remain 823 TP / 12 FP / 17 FN and contextual controls 104 TP / 0 FP / 1 FN, with no new strict errors/losses. Type correction has no real gain. No post-result tuning, retry, inference, reference revision or application promotion occurred. Next qualify scoring and fixture contracts separately.

**Earlier checkpoints below are historical.**

## Remaining article recognition gaps — assessment completed

Reconciled **34 target occurrences across 18 measured rows and one unmeasured junction**. Twenty-one occurrences are deficient: 17 absent, three boundary errors and one incompatible type. All 93 affected depth/time/status/access facts remain saved and unassigned. Six overlapping cases need meaning/type review. This assessment makes no corrections or new accuracy claims. [Report and recommendation](evaluations/flood-ner-recognition-gaps-20261020/README.md) · [Verification](evaluations/flood-ner-recognition-gaps-20261020/verification.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Eight input bindings, exact offsets, individual dispositions, counts and private manifests verify. Protected evidence, v41/v42 code, original predictions/references and excluded metadata remain preserved. No application changes, extraction/inference, source fetch or database access occurred. Next separately scope a frozen source-supported location-proposal study; the preview remains disabled.

**Earlier checkpoints below are historical.**

## V42 context repair — accepted and promoted to disabled local preview

Delivered a separate junction/list-context/clock/dateline successor, 36 fictional scenarios, frozen worker/controller and independent saved-output verification. One isolated 371-input/1,419-graph attempt passes all prescribed fixtures and retains all 120 contextual view link/expression sets. Five complete junction rows now retain co-described depths; list observation/access/caution and dateline handling pass. All 52 depth spans and 59 prior facts remain source-backed. Recognition limitations leave 18 measured rows and an additional unmeasured junction unresolved. [Outcome](evaluations/flood-ner-context-repair-v42-20261019/README.md) · [Guide](guides/ner-context-repair-v42.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

The worker, projection/host validator and provenance now use v42 after acceptance. Cached response-contract verification preserves URL/input hashes, mentions and output shape. 1,158 pre-freeze / 1,195 post-promotion tests pass. Prior application/test sources were snapshotted; all 55 frozen v41 and 208 protected evidence hashes remain intact, with historical/excluded metadata preservation explicitly reconciled. No neural inference, proposal regeneration, database access, new data, frontend/map change, upload, commit or push. Flag remains off; language, reference and learned-DEPTH/TIME limitations remain.

**Earlier checkpoints below are historical.**

## Backend article link and real saved-article review

Added `source.canonical_url`, bound to the existing immutable request snapshot. All 379 preview checks pass. One endpoint call with actual read-only database storage and the real isolated worker returns the saved URL and exact body hash; its transaction is rolled back and the ordinary feature flag stays off. Review accounts for 59 facts/26 measured rows and reveals junction/equivalent-depth pairing, missed list time, header access, dateline and location-specificity problems. All 52 depth substrings are source-exact, but complete extraction correctness is not established. [Findings](evaluations/flood-ner-saved-article-review-20261019/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Private pre-change source snapshots preserve earlier hash bindings. No model/context-rule change, reference revision, database write, publisher fetch, validation/holdout file content, frontend or plotting change occurred. Extraction repairs remain separately scoped work.

**Earlier checkpoints below are historical.**

## Extraction-only backend preview — locally verified

Implemented the [local saved-article preview](evaluations/flood-ner-backend-preview-20261019/README.md): protected active-admin API, exact-body/input hashes, grouped fields/evidence, preserved time/collective semantics, separate neural/rule provenance, private inference-only bundle, isolated CPU worker, explicit errors and owned cleanup. **798 checks pass**; nine real-worker API calls succeed using fake read-only storage, six original article neural outputs match and 120 cached context views match. Startup/extraction maxima are 4.314/1.466 seconds and peak worker RSS is 368.6 MiB on this fixed workload. Live isolation and zero remaining owned containers are verified. [Guide](guides/ner-backend-preview.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

The frozen checker retained a final metadata-audit failure for the intentional four-setting `config.py` change. Separate saved-receipt verification reconciles it without neural retry or extractor tuning. All 208 protected evidence hashes, 55 frozen v41 files and 82 excluded metadata entries match; 1,538 historical metadata entries match, with one declared config change. No new articles, training, validation/holdout contents, live database writes, frontend/map changes, uploads, commits or pushes. The default flag remains off and operational processing is unchanged. Three holds and known language/learned-DEPTH/TIME limits remain.

**Earlier checkpoints below are historical.**

## V41 context repair — bounded acceptance passed

Delivered separately versioned time-predicate and collective-locality handling, 36 new regressions and a context-only worker/controller with unchanged input/output contract. One frozen Linux comparison completes all 334 raw inputs. All 36 old temporal cases, 36 new regressions and 238 preserved context fixtures pass. The combined cached-location view scores 104 TP / 0 FP / 1 FN on 23 unchanged silver training references; six old misses recovered, one non-flood access miss retained, no supported correct links lost or newly incorrect links introduced. [@roicambe](https://github.com/roicambe) (Roi Cambe)

419 pre-execution software checks pass. Independent verification confirms all view counts, seven outcomes, exact source slices, untouched cached location proposals, isolation and stopped state. All 55 frozen code/test hashes and 208 protected evidence hashes match; metadata-only preservation remains explicit for historical/excluded packages. No tuning/retry, model/location-rule changes, neural inference, study-data recognition, training, validation/holdout content or production/database/map change. Three holds, unmeasured real pure-Tagalog performance and learned DEPTH/TIME remain open. [Outcome and next proposal](evaluations/flood-ner-context-repair-v41-20261019/README.md) · [Verification](evaluations/flood-ner-context-repair-v41-20261019/verification.json).

**Earlier checkpoints below are historical.**

## V40 offline location-repair study — complete, acceptance blocked

Delivered separate source-only location proposals, 72 new fictional cases, frozen preparation/worker/scoring and 347 passing pre-execution software checks. One 679-input Linux attempt completed under fixed isolation; no retry or post-result tuning. All 238 old fixtures are preserved and pass. Transport recognition recovers four old links; shared locality introduces one strict scope error; exact road typing has no demonstrated correction. Unchanged v38 passes 29/36 temporal cases, with seven onset/report role failures retained. No complete method qualifies. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Independent saved-output verification reconciles location and association counts, provenance, seven old errors, raw joins and exact container mount identities. All 50 frozen source/test hashes and 208 protected evidence hashes match; historical/excluded entries remain metadata-unchanged. V19, 345/60/60, three reference holds and completed-holdout exclusion are preserved. No neural inference, new training, production/database/map change, upload, commit or push. Real pure-Tagalog performance and learned DEPTH/TIME remain unfinished. [Outcome and next repair proposal](evaluations/flood-ner-location-repair-20261019/README.md) · [Verification](evaluations/flood-ner-location-repair-20261019/verification.json).

**Earlier checkpoints below are historical.**

## Remaining extraction-gap assessment — complete

Reviewed seven missed links across three training passages: two exact-boundary location mistypes and one absent mention. Accounted individually for three depth, two status and two access links; separated a non-flood closure and missing downstream facts from the necessary target-recognition issues. All three held references remain held; two receive concrete clarification proposals. Real pure-Tagalog performance remains unmeasured. No score/reference/model change or accuracy measurement occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Saved-evidence checks verify 208 unchanged hash-bound files, 1,539 unchanged historical metadata entries and 82 unchanged validation/holdout metadata entries (overlapping sets). Private source/offset/prediction ledger and seven individual dispositions are preserved outside Git. No extraction/inference, training, validation/holdout contents, new software suite, application connection, upload, commit or push. Membership remains 345/60/60. [Assessment and next task](evaluations/flood-ner-extraction-gap-assessment-20261019/README.md) · [Verification](evaluations/flood-ner-extraction-gap-assessment-20261019/verification.json).

Next is a separately scoped recognition-feasibility proposal with downstream recovery/retention checks, not automatic training or integration. Learned DEPTH/TIME remains unfinished. [@roicambe](https://github.com/roicambe) (Roi Cambe)

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

**Next proposal:** narrowly repair recession-time precedence and collective/gauge semantics, with independent source-only disposition of remaining status-reference coverage questions before another freeze. Preserve the three contextual holds, original and revised score reports, all 345/60/60 membership and completed holdout exclusion. No LANES connection, new data or retraining is authorized by this failed gate. Learned DEPTH/TIME remains unfinished; October 25 readiness is unestablished. [Outcome](evaluations/flood-ner-context-repair-20261019/README.md) · [Verification](evaluations/flood-ner-context-repair-20261019/verification.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Offline context association checkpoint — not qualified

**Offline association implementation and one comparison are complete; acceptance failed.** All 24 eligible training proposals and 40 fictional cases were processed with references outside extraction; the two held records remain unscored. **36/40 behavior cases pass; 34 correct links gained, zero baseline-correct links lost and 20 new strict silver-reference disagreements.** Those disagreements include demonstrated scope/time errors and separately recorded reference/grouping concerns; none was relabeled or hidden. **277 fresh tests pass (61 new)**; a broader timed-out test attempt remains incomplete. No empirical retuning occurred.

**Next proposal:** separately repair clause/time updates, collective/list scope and nearby-facility abstention, and independently resolve the recorded reference questions. Freeze a successor before a separately authorized comparison. **Read-only LANES connection is not cleared.** Preserve 345/60/60, the two holds and completed holdout exclusion; no retraining/new data is needed for this repair proposal. Learned DEPTH/TIME remains unfinished; October 25 readiness is unestablished. [Outcome](evaluations/flood-ner-context-association-20261019/README.md) · [Verification](evaluations/flood-ner-context-association-20261019/verification.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

## Interim flood-context acceptance package prepared

The user selected the limited **location-model + depth/time-rule demonstration** as the temporary defense priority; learned DEPTH/TIME remains unfinished. A separate source-only proposal accounts for all 26 contextual training counterparts: **20 retain / four corrected / two held**. Three earlier holds have supported proposed dispositions; two remain incomplete/unresolved. Current corpus references and all 345/60/60 membership are unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

The 24 eligible proposals contain 35 DEPTH / 22 TIME spans, with unknown/unassigned associations explicit. **40 fictional cases** freeze ten behavior families across English/Taglish and supported/counterexample contrasts. **753 fresh regressions pass, including 94 new checks**, and a guarded CPU worker verifies schema, source spans, repeated occurrences and frozen tokenizer reconstruction without extraction or model execution. The acceptance specification, references, cases and hashes are frozen before repairs; no general accuracy or behavioral pass is claimed.

Next implement separately scoped offline association repairs using saved training-only v19 location predictions. Read-only LANES connection follows only after acceptance; learned DEPTH/TIME training remains separate. Validation and the completed holdout stayed outside review/qualification. No new corpus passages, applied corrections, exports, neural inference, training, production change, upload, commit or push occurred. [Outcome](evaluations/flood-ner-context-acceptance-20261019/README.md) · [Specification](plans/ner-interim-context-acceptance.md) · [Guide](guides/ner-interim-context-acceptance.md).

**Earlier checkpoints below are historical.**

## Existing depth/time and association gap review completed

All **405 development records** have a completed inventory disposition. The active contextual pilot matches 26 training passages: **21 supported for limited diagnostics / five held**, with **379 missing contextual counterparts**, including every validation passage. The 113 editorial context blocks have no completed annotations. Existing location references and all 345/60/60 membership remain unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)

One guarded Linux rules worker processed all 405 unchanged passages without references, model files, credentials, network or database access. It produced 567 location-bearing claims, including 108 depth and 27 time claims; these are diagnostic outputs, not accuracy. Source-bound list/qualifier/time gaps and missing-context limitations are separately recorded. **659 fresh tests pass, including 48 new audit checks.** Protected 1,383 hashes and 55 stat-only holdout / 27 earlier-validation-study entries verify unchanged; no holdout content was opened.

Next proposed work is a fixed contextual annotation/association specification and source-bound reference-completion plan on existing texts, followed separately by bounded repairs or a learned DEPTH/TIME experiment. The original trained goal remains open; the October 25 interim-hybrid recommendation is still proposed. No collection, applied corrections, neural inference, training, export, integration, upload, commit or push occurred. [Aggregate report](evaluations/flood-ner-context-gaps-20261019/README.md) · [Operator guide](guides/ner-context-gap-audit.md).

**Earlier checkpoints below are historical.**

## NER requirements clarified before further implementation

Documentation now keeps the original learned **location + DEPTH + TIME** goal open, separately from completed six-class location training and existing depth/time rules. Location scores do not establish full-system extraction performance. The proposed October 25 interim hybrid/postponement schedule is not recorded as a permanent scope reduction or as separately accepted. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Next proposed work is an existing-training/development contextual-evidence gap review and bounded association plan. No new articles, annotation/data changes, inference, training, integration or deployment ran for this documentation task. [Current tasks](task_plan.md#current-ner-scope-and-defense-checkpoint).

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

## October 19: Regularization results and private backup publication

**Publication checkpoint:** Matching public v21 execution/scoring code and metadata accompany this roi-branch update. The [new private result backup](https://drive.google.com/drive/folders/14A4kgWRH0LNay8My9vCutIQp_ro-ezTl) has nine fully byte-verified, owner-only files; older handoffs are unchanged. Corrected v19 control seed 0 remains primary, and no further runs or holdout evaluation occurred. [Publication report](evaluations/flood-ner-regularization-publication-20261019/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 19: Regularization v21 screening completed; control retained

The new controller/scorer pass 291 tests and fresh actual GPU/schema verification. One successful L2 = 0.05 run selects step 945 and reaches the 1,000-step budget; CPU loading and strict development scoring pass. Candidate validation F1 69.7143% trails control 71.6049%, while ROAD/LOCAL_AREA rise to 53.3333%/73.6842%. Screening fails overall, so seeds 1/2 are omitted and corrected control seed 0 remains primary. All 8,047 protected files are unchanged. No holdout evaluation, data/annotation change, deployment, commit or push. [Execution evidence](evaluations/flood-ner-regularization-v21-execution-20261019/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 19: Regularization v21 desktop verified

**Current desktop result: regularization v21 receipt and actual GPU/schema verification are complete.** Exactly 20 experiment files / 12 trainer files and all 23 pinned model files verify. Actual result: `verified_read_only`, schema/GPU true, training false. All 248 focused tests pass. No training or inference occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Stopped before training, as required.** A separate explicit task may run the fixed seed-0 screen and conditional seeds 1/2. The completed research holdout remains excluded from tuning and repeat evaluation.

[Desktop verification receipt](evaluations/flood-ner-regularization-desktop-verification-20261019/README.md).

**Earlier publication checkpoints below are historical; pending desktop statements are superseded by this receipt.**

**Current NER handoff: the regularization experiment is verified on private Drive; matching code and instructions accompany this roi-branch publication.** The 345 training / 60 validation exports are unchanged. One L2 = 0.05 candidate has seed 0/1/2 configs and a fixed maximum-three-run protocol. All four uploaded files match authenticated readback; parent, destination and files are owner-only. Desktop receipt and GPU verification remain pending. No training, inference or holdout access occurred during delivery. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next on the desktop:** preserve local changes, pull roi-branch with --ff-only, authenticate and extract the delivered archive into an absent destination, then run read-only GPU/schema verification and STOP. Actual training is a separate explicit task after verification; the completed research holdout stays outside tuning.

[Delivery report](evaluations/flood-ner-regularization-delivery-20261018/README.md) · [Desktop instructions](guides/ner-regularization-experiment.md) · [Private Drive handoff](https://drive.google.com/drive/folders/1vKssoZurLa6WjuJPftXRbJ7GcoefimKq)

**Earlier dated checkpoints below are historical.**

## October 18: Existing-data regularization package qualified

**Current NER task completed: one stronger-weight-decay experiment is prepared and CPU-qualified.** The existing 345 training/60 validation records, annotations, tokenizer and grouping remain unchanged. One twelve-file package supplies seed 0/1/2 configs with only `L2: 0.01 -> 0.05` changed. Fresh 341 tests/four subtests pass; 72 new checks also pass in the pinned runtime. No inference, training or research-holdout content access occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next:** separately publish matching code and privately deliver the experiment bundle; then perform actual desktop read-only GPU verification. Training follows as a separate explicit task: seed 0 screening, conditional 1/2, maximum three runs, with overall improvement and ROAD/LOCAL_AREA protection required. The completed holdout stays outside tuning. Delivery/GPU verification remain pending; the desktop can remain off.

[Preparation report](evaluations/flood-ner-regularization-preparation-20261018/README.md) · [Operator guide](guides/ner-regularization-experiment.md)

**Prior checkpoints follow; their dated “current/next” wording is historical.**

## October 18: V19 diagnosis and frozen comparison completed

**Current NER status: v19 diagnosis and the one-time frozen research evaluation are complete on the laptop.** Dataset 345/60/60 and validation-selected control/seed 0 stay unchanged. V19 seed 0 training/validation/holdout F1: **98.09% / 71.60% / 73.63%**. Historical v16 seed 0 holdout 74.74%; rules 53.49%. Holdout three-seed means: control 70.34%, v16 75.13%. These results do not establish an overall v19 improvement or authorize choosing a model using the holdout.

**Next:** a separate development plan from the existing training/validation error review; no new articles or automatic retraining. Gate 3 research measurement is complete, while operational qualification, integration and release remain open. The holdout has now been evaluated and must not be tuned against or evaluated again under this protocol. AI-assisted silver, incomplete history/accounting and no certified-fresh claim remain. No collection, new training, reference/partition change, integration, upload, commit or push occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)

[Diagnosis/evaluation report](evaluations/flood-ner-v19-diagnosis-evaluation-20261018/README.md) · [Laptop evaluation guide](guides/ner-corrected-holdout-laptop.md)

**Historical checkpoints follow.** Their “current/next” wording describes earlier dated tasks and is superseded by the status above.

## October 18: Corrected v19 desktop experiment completed

All five sequential desktop runs succeeded. Control seeds 0/1/2 validation F1: 71.6049%, 71.5152%, 66.2722%; mean 69.7974%, sample SD 3.0533 percentage points. Control seed 0 remains primary. The original desktop handoff and checkpoint-rounding resolution remain in the [execution record](evaluations/flood-ner-corrected-v19-execution-20261018/README.md); the subsequent laptop evaluation above supersedes its original pending status. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Corrected experiment delivered privately

Three qualified trainer packages plus protocol delivered with complete authenticated byte readback and owner-only permissions. Desktop receipt/GPU checks remain pending; no training. [Evidence](evaluations/flood-ner-corrected-experiment-delivery-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current handoff: corrected v19 packages are verified on Drive; matching public code and instructions accompany this roi-branch publication.** Dataset remains 345 training / 60 validation / 60 separate research holdout. Three twelve-file packages and the fixed future protocol are delivered; all uploaded bytes match authenticated readback and five owner-only permission checks pass. No training, inference or holdout access occurred. [Delivery report](evaluations/flood-ner-corrected-experiment-delivery-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: desktop receipt and read-only GPU verification for all three packages, then STOP.** Preserve local work, pull roi-branch with --ff-only and receive the new private ZIP from [Drive](https://drive.google.com/drive/folders/1LDO770D82NXHZRiYNZrHe5oyLo7-vJU7). Actual desktop receipt/GPU checks remain pending. A Git pull does not deliver ignored data; do not rerun preparation or historical v16 training commands. Actual training is a separate explicit task. [Exact commands and copyable desktop prompt](guides/ner-corrected-experiment-desktop.md).

## October 18: Corrected-data experiment qualified on laptop

Twelve source-supported boundaries adopted in a separate development revision; three twelve-file packages and nine configs qualify. Fixed five/seven-run future protocol; no training, holdout access or delivery. [Evidence](evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical completed task: corrected-data experiment preparation on the laptop.** A separate 345 training / 60 validation revision adopts only 12 supported training-boundary corrections across nine records. Validation, tokenizer and partition/group bytes remain unchanged; the 60-passage research holdout stays unopened. Three twelve-file trainer packages and all nine seed/config schemas qualify in Python 3.11.17/spaCy 3.7.5. Fresh 367 tests / 35 subtests pass, including 83 new tests. No new articles/passages, inference or training occurred. [Preparation report](evaluations/flood-ner-corrected-experiment-preparation-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Prior preparation next-step (delivery now completed; desktop verification still pending): publish/deliver the corrected packages and frozen experiment protocol.** At that earlier preparation checkpoint, delivery/GPU verification were pending and no upload, commit or push had occurred. The specified future study uses five runs if control wins screening, otherwise at most seven. No guaranteed score follows. The desktop can remain off. [Operator guide](guides/ner-corrected-experiment-preparation.md).

**Historical completed task: existing-data development audit.** All three models reproduce desktop validation scores on CPU across 345 training / 60 validation records (1215 predictions); the separate 60 research-holdout passages remain unopened. Seed 0 training F1 is 99.40% versus validation 66.67%, consistent with overfitting/example differences. Source-bound review proposes 12 training-span boundary corrections across 9 existing records; one validation-boundary question remains unresolved, with its frozen scored reference retained. No data, partitions or models changed. Fresh 209 tests / 35 subtests pass, including 53 new audit tests. [Audit report](evaluations/flood-ner-development-error-audit-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Prior audit next-step (now completed as preparation above): choose supported corrections and define a bounded regularization experiment using existing data only.** No new articles/passages, corpus admission, replacement export, holdout access, training, upload, commit or push occurred in this task. The desktop can remain off. [Operator guide](guides/ner-development-error-audit.md).

Earlier training/publication checkpoints below remain historical; the current user constraint is no new data collection.



**Publication checkpoint:** Matching combined launcher and three-seed reports are included in this `roi-branch` publication. The new [private v17 Drive backup](https://drive.google.com/drive/folders/1ZFFNL9Vu-dg5xLyWsSR2wd99_qsGTE_J) preserves the combined trainer and all three selected checkpoints/logs; all eleven uploaded files pass full SHA-256 readback and all twelve folder/file permission checks are owner-only. Older folders remain unchanged. The local `.env` change stays outside the commit. [Publication evidence](evaluations/flood-ner-successor-publication-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Successor private backup verified

Combined trainer and three selected checkpoints/logs backed up without overwriting prior handoffs; 11 authenticated full-byte readbacks and 12 owner-only permission checks pass. [Evidence](evaluations/flood-ner-successor-publication-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current successor v16 desktop result:** All three successor seeds complete and their selected checkpoints verify; seed 0 remains primary. 75 focused tests and combined GPU/schema verification pass. Development F1 for seeds 0/1/2: 66.67% / 65.41% / 67.46%. All 12,387 protected historical files and `.env` remain unchanged. Holdout evaluation is separate. [Execution evidence](evaluations/flood-ner-successor-v16-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Successor v16 desktop training execution

All three successor seeds complete and their selected checkpoints verify; seed 0 remains primary. Each selected checkpoint reloads with six labels and matching finite development metrics; seed 0 remains primary. [Evidence](evaluations/flood-ner-successor-v16-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier preparation, delivery, correction and failed-attempt checkpoints below are historical unless explicitly carried forward.

## October 18: Successor seed-0 attempt stopped on supplied configuration defect

Seed 0 reached the GPU initialization command but spaCy rejected lowercase `l2`/`l2_is_weight_decay`; the pinned optimizer requires `L2`/`L2_is_weight_decay`. No optimizer updates, checkpoint or validation score. Failed output/logs remain intact; seeds 1/2 were not launched and no retry or recipe edit occurred. A separate versioned config repair and later authorized retry are needed. [Evidence](evaluations/flood-ner-successor-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Desktop successor receipt and GPU startup repair

Received the exact twelve-file package, preserved the original and created a separately bound launcher derivative without changing eleven payload files. All 23 model files, 64 focused tests and actual RTX read-only GPU verification pass. The pre-launch inventory records 12,343 persistent predecessor files; the subsequent failed attempt is recorded above. Holdout references remain on the laptop. [Evidence](evaluations/flood-ner-successor-desktop-training-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier delivery/preparation checkpoints below retain their historical status.

**Current desktop handoff: private trainer delivery to Drive is verified; successor code and public reports accompany this handoff on `roi-branch`.** Dataset membership stays **345 training / 60 validation / 60 research-holdout**. The twelve-file trainer ZIP, checksum and instructions match authenticated readback and remain owner-only. Research-holdout content stays on the laptop. No training ran. [Delivery report](evaluations/flood-ner-successor-delivery-20261018/README.md) · [Private Drive folder](https://drive.google.com/drive/folders/1WuhvnWfKybY8lbKKO55aToTUQ_PY6RqJ). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: receive the package on the desktop and run read-only GPU verification.** Preserve local changes, pull `roi-branch` with `--ff-only`, verify the ZIP checksum, extract only to an absent destination, then use the successor launcher with `--verify-gpu`. A Git pull alone cannot transfer ignored data. Desktop receipt/GPU verification are unconfirmed; seeds0/1/2 training is a later explicit action. [Exact instructions](guides/ner-successor-desktop-training.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current successor status: configuration correction v16.** The desktop reported seed 0 failed before optimizer updates because the v15 package builder lowercased case-sensitive spaCy arguments; seeds 1/2 were not started. The generator now preserves `L2`, `L2_is_weight_decay` and `nO`, and all three configs pass real spaCy 3.7.5 schema resolution. Dataset **345 training / 60 validation / 60 research-holdout** and all eight non-config trainer files remain unchanged. No training/retry or inference ran during this correction. [Correction report](evaluations/flood-ner-successor-config-correction-20261018/README.md) · [Corrected private Drive package](https://drive.google.com/drive/folders/15sxU7utCM9Nf429BXWUQlXgtEoC1nTQH). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Next: preserve the failed run, pull the matching corrected code, receive v16-configfix into a new destination, and repeat read-only GPU verification.** Require `verified_read_only`, `configuration_schema_verified: true`, `gpu_verified: true` and `training_started: false`. Desktop receipt/GPU re-verification remain pending. A later explicit seed-0 retry needs a new output directory; do not start seeds 1/2 automatically. [Exact instructions](guides/ner-successor-desktop-training.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


Earlier checkpoint counts and pending tasks below are historical unless explicitly carried forward by the current status.

## October18: Successor desktop delivery verified

Exact twelve-file trainer ZIP and two companion files uploaded owner-only and fetched back byte-identically; current code/reports included on roi-branch. Fresh344 tests/190subtests pass, one symlink skip. Desktop receipt/GPU verification pending; no training. [Evidence](evaluations/flood-ner-successor-delivery-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Successor preparation completed locally

465 locked silver records; separate strict/reload-qualified exports and portable configs; fresh215 tests/165subtests pass; 7,320 predecessor files unchanged. Private delivery and desktop GPU verification pending. No training/upload/push. [Evidence](evaluations/flood-ner-successor-preparation-20261018/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Limited-provenance standard adopted and successor preparation specified

Direct user choice recorded; exact development selection405 and holdout60 retained. No further provenance decision needed. No admission/freeze/export or training executed in this design step. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Source-bound clearance assessment and explicit protocol options

Fresh isolated review checks60 selected records and280 fitted anchors; known fitted/development overlap matches0/0. Preserve7,283 protected files. No amendment or training; decision remains with the user. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Gemini reports original evidence inaccessible

Record user-relayed recovery limitation; preserve345/60/60 and all prior packages. No native receipts returned; no new tests, collection or training. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Gemini recovery handoff prepared; clearance awaits original evidence

Preserve345/60/60; account for eleven missing search pairs, five saved query-field differences and twelve historical payloads. Fresh107 tests /116subtests pass; 7,245 protected files unchanged. No native Gemini evidence has been returned and no collection or training ran. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Four saved Taglish positives complete conditional test coverage

Preserve345/60 development and all56 prior test candidates; reach one conditional60 proposal without collection. Fresh324 distinct tests pass / one existing symlink test skips; all7,193 protected files unchanged. History and original acquisition accounting remain unresolved. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 18: Saved latest candidates reused in 56-member conditional proposal

Preserve 49 baseline; reconsider four prior metadata-only cases and add three source-exact supported windows. Actual development/event/component overlap cases stay excluded. Fresh 311 tests pass / one skips; 7,159 protected inputs unchanged. [@roicambe](https://github.com/roicambe) (Roi Cambe)


**Historical v9 checkpoint:** all 27 mistaken reductions were reversed, restoring 49 and preserving 53. V10 below/above separately reconsiders metadata-only holds and latest saved windows; the old protocol comparison remains preserved.

## October 18: Conditional baseline restored after source-review precedence correction

Isolated saved-evidence replay restores 49 with 0 baseline removals; the preserved historical 53 and its four protocol holds are reported separately. All27 erroneous v8 reductions are reversed without undoing software safeguards. Fresh 302 regression tests pass / one skips. [@roicambe](https://github.com/roicambe) (Roi Cambe)


**Superseded v8 progress reduction:** its 22-passage result omitted later source-bound review decisions. V9 reverses all 27 mistaken reductions; the v8 report remains preserved. The ten software repairs remain in force.

Earlier checkpoints below retain their historical counts; v7 readiness claims are superseded.

## October 17: Historical v7 readiness claim — superseded

**Superseded v7 claim:** the reported sealing, export qualification and training unlock are unsupported. The frozen v7 report/artifacts remain historical evidence; follow the current recovery outcome above.

## October 17: V6 accounting gate blocked and exposure quarantine recorded

**V6 audit completed; collection blocked:** preserve **345 training / 60 validation / 49 conditional test**. Four Taglish members are newly exposure-quarantined; the historical 53 artifact remains unchanged. English 30/30, Taglish 19/30; **eleven Taglish positives remain missing**. Local v5 ledger replay is consistent, but complete original search-tool receipts are unavailable. Claimed 649 identities + four uncertain slots / 84 attempts do not certify remaining 47/16 headroom; additional v5 exposure is unquantified. This task sent **zero network requests**, passed 27 offline guards and preserved 6,896 protected files. Next: recover original tool receipts for isolated reconciliation; no collection, admission, seal, export or training. Desktop action none. [Current outcome](evaluations/flood-ner-taglish-budget-continuation-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below are historical claims and do not override this audit.

## October 17: Taglish test completion evaluation (Round v5)

**Taglish completion evaluation (Round v5) completed; shortage unchanged:** **345 training / 60 validation / 53 conditional test**. Executed bounded targeted collection round v5 (11 queries reserved and accounted for; cumulative raw identities 649 / 700 ceiling; publisher attempts 84 / 100 ceiling; collection closed). All 53 baseline members preserved. English 30/30 (27 pos + 3 neg) and Taglish 23/30 (20 pos + 3 neg); **seven Taglish positives still needed**. Candidates from historical weather events evaluated showed either training/validation event overlap or English-dominant regional reporting without operational Taglish. Next: bounded acquisition proposal for unexposed localized floods (2017–2023) or authorized source-use evidence resolution before successor admission, grouped partition freeze, qualified exports or desktop GPU training. [Current outcome](evaluations/flood-ner-taglish-test-completion-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: Source-evidence gate review for held test leads

**Source-evidence gate review completed; shortage unchanged:** **345 training / 60 validation / 53 conditional test**. Audited 86 held identities and 19 exclusions under saved material with zero network operations; zero holds resolved. All 53 baseline members preserved. English 30/30 and Taglish 23/30; **seven Taglish positives still needed**. Collection remains closed at 585 raw identities + four uncertain slots / 84 publisher attempts under prospective 600/100. Next: concrete bounded follow-up proposal with exact accounting or external acquisition authorization before successor admission, grouped partition freeze, qualified exports or desktop GPU training. [Current outcome](evaluations/flood-ner-source-evidence-gate-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints retain their historical counts and scope.

## October 17: Taglish follow-up gained four; independent-test coverage remains open

**Taglish follow-up completed; coverage still short:** **345 training / 60 validation / 53 conditional test**. Four Taglish positives gained; all 49 earlier members retained. English 30/30 and Taglish 23/30; **seven Taglish positives still needed**. Two bounded rounds used 22 queries / two captures; current ledger 585 raw identities + four uncertain slots / 84 publisher attempts under prospective 600/100. Collection is closed, with no further ceiling increase in this task. Next: supported original-source/use and history evidence for reconsiderable held leads, then the remaining positive windows. Admission, freeze, seal, export and desktop GPU handoff remain pending. [Current outcome](evaluations/flood-ner-taglish-completion-followup-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints retain their historical counts and scope.

## October 17: Targeted collection and isolated review completed

**Targeted collection and review completed:** **345 training / 60 validation / 49 conditional test passages**. Seven test passages gained (five English positives and two Taglish positives); all 42 earlier members retained. English meets its target; **eleven Taglish positives remain missing**. Nine searches and eight captures are complete; cumulative accounting is 377 raw URL identities + four uncertain slots / 82 publisher attempts, within the prospective 400/100 ceilings. Collection is closed; all exposed identities and proposed references are accounted for. Final checks: 19 acquisition mocks, 26 rejection guards, zero schema/tokenizer errors and 6,535 protected files unchanged. The test remains unsealed; no training or desktop action. [Current report](evaluations/flood-ner-taglish-targeted-collection-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below preserve their historical counts and permissions.

## October 17: Six-lead preflight, wrapper and history reassessment

**Six-known-lead task completed:** **345 training / 60 validation / 42 conditional test passages**. All six leads are history-held; **zero publisher GETs**. New source-only history evidence holds eight prior witness members; the earlier 50 remains an unchanged historical artifact. Remaining positives: **5 English / 13 Taglish**. URL accounting is 296 actual + four uncertain slots under the prospectively authorized 306 ceiling; attempts remain 74/100. Unused allowance is not replacement/discovery permission. Test stays unsealed; desktop can remain off. [Current evidence](evaluations/flood-ner-six-known-leads-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below retain their recorded outcomes and counts.

## October 17: Saved-test evidence review and exposure containment

**Saved-test evidence review completed:** preserve **345 training / 60 validation**, with **50/60 conditional test passages** after saved review and exposure quarantine. Positive shortage **1 English / 9 Taglish**. All 49 prior unresolved references and 68 saved sources are accounted for. Zero network requests; accounting stays 296 actual URLs + four uncertain slots / 74 publisher attempts. One progress disclosure is documented and affected components held; prior 50 remains historical. Test stays unsealed; desktop can remain off. [Latest evidence](evaluations/flood-ner-saved-test-evidence-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Earlier checkpoints below retain their recorded outcomes and counts.

## October 17: Isolated non-GDELT search and source review completed

**Non-GDELT search completed:** preserve **345 training / 60 validation**, with **50/60 conditional independent-test passages**. Positive shortage now **1 English / 9 Taglish**. Ordinary web search used one query at a time with all returned URLs audited under the unchanged 300/100 ceilings; no GDELT troubleshooting. Actual URLs 296 + uncertain slots 4, leaving 0 usable URL slots / 26 publisher attempts. Test remains unsealed; desktop can remain off. [Latest outcome](evaluations/flood-ner-non-gdelt-search-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

All 6,277 protected predecessor files remain unchanged. No admission, freeze, inference, training, upload or push.

## October 17: Final diagnostic blocked before dispatch; request hardening verified

**Final GDELT diagnostic blocked locally; hardening complete:** **0 outbound GETs**, no provider response. The one diagnostic operation stopped at a pre-dispatch guard; exact original message was not retained. Corrected a platform-sensitive timer comparison and verified it with mock responses (101 tests pass / one skips), without reopening the authorization. Stop GDELT troubleshooting. Preserve **345 training / 60 validation / 42 conditional test**, still missing six English and twelve Taglish positives. Carry **204 actual exposed URLs + 4 uncertain slots** (92 unreserved URL slots / 34 article attempts remain). The test stays unsealed; desktop can remain off. [Latest outcome](evaluations/flood-ner-final-gdelt-diagnostic-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Verification: 101 focused unit tests pass, one Windows symlink test skips; all 6,219 protected predecessor files remain unchanged. Zero outbound diagnostic GETs; no collection, inference, training or push.

## October 17: Controlled continuation verified; single retry halted

**Controlled retry completed; provider remains blocked:** preserve **345 training / 60 validation / 42 conditional test passages**, still missing **six English and twelve Taglish positives**. The authorized single retry returned HTTP 429; no new articles or passages and no further retry/fallback. Carry **204 actual URL exposures + four unresolved reserved slots**, leaving **92 unreserved slots / 34 article attempts** under 300/100. Twelve exact history metadata/helper payloads remain unavailable; no new source identities were found. The test stays unsealed and desktop can remain off. [Latest outcome](evaluations/flood-ner-controlled-retry-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Verification: 72 unit tests pass / one skips; 35 isolated fault guards pass; 92 references / 116 spans validate without errors. All 6,166 protected coordinator inputs remain unchanged. No training or publication occurred.

## October 17: Bounded discovery tested; provider route halted

**Bounded discovery completed with a provider blocker:** preserve **345 training / 60 validation** and **42/60 conditional test passages**; **six English and twelve Taglish positives** remain missing. The first GDELT one-record probe returned **HTTP 429**; collection stopped without retry, fallback or new articles. Actual exposure is **204 URLs + one pending slot**, leaving **95 unreserved URL slots / 34 article attempts** under 300/100. Three exact historical payloads were recovered from Drive; twelve named metadata/helper payloads remain unavailable. The test stays unsealed and the desktop can remain off. [Outcome](evaluations/flood-ner-bounded-discovery-20261017/README.md) and [research guide](guides/ner-bounded-test-discovery.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Verification: 54 unit tests pass, one Windows symlink test skips; the isolated curator passes 29 fault guards and validates 92 complete references / 116 spans without errors. All 6,103 protected coordinator inputs remain unchanged. No admission, freeze, export, inference, training, upload or push occurred.

## October 17: Desktop history reconciled; validation count gap closed

The returned desktop inventory is verified: 6,369 files / zero errors; recorded readable backup scope reconciles without changed or unexplained missing payloads. Add three qualified saved-source validation proposals, preserving 345 training and reaching 60 validation. Isolated test review finishes with 42/60 conditional passages (6 English / 12 Taglish positive shortfall), cumulative 202/300 URLs and 66/100 attempts. Keep source/history/use holds and scan exclusions explicit; no unsealed test material enters development. 28 coordinator checks pass / one skip; 6,039 protected files remain unchanged. No admission, freeze, sealing, export, training or push. [Report](evaluations/flood-ner-desktop-history-gap-completion-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: Desktop inventory publication handoff prepared

Prepare the reviewed helper, byte-preservation tests, public audit reports and [desktop continuation guide](guides/ner-desktop-history-inventory.md) for `roi-branch` publication. The guide includes safe branch/pull commands, a direct repository helper invocation, a desktop Codex prompt, the historical v3 Drive link and explicit Git/private-artifact availability. Preserve 345 proposed training passages and the user's 60-validation/60-test targets; three validation and 23 positive test passages remain missing under current conditional eligibility. Actual desktop inventory, history reconciliation, further collection, admission and training remain pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: Successor count targets clarified; desktop inventory pending

**Current successor targets clarified: retain 345 proposed training passages and target 60 validation + 60 independent test passages (465 total if all qualify).** The reviewed development proposal still contains **345 training / 57 validation**; **three additional eligible validation passages are needed**. The independent test still has only **37 conditionally supported passages / 23 positive passages missing (10 English, 13 Taglish)** for its current joint witness. These are targets and conditional counts, not admitted/frozen records. Keep all historical fitted-source groups training-only; never use isolated test material to fill validation or validation material to fill test. **Next: run and reconcile the original desktop history inventory before further collection; then qualify additional validation/test material under separate roles and resolve the recorded acquisition-budget failure.** No new search, capture, admission, export or training is authorized by this count clarification. Previous review/design/qualification packages and their completed counts remain historical. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the successor targets above are newer.

## October 17: Targeted isolated collection and desktop inventory handoff

**Targeted isolated collection and desktop-history handoff completed with blockers:** Review five pre-breach captures and preserve all prior material. Nine complete positive proposals are added; the supported finite-pool joint witness after known history/use filters is **37/60**, conditional on unresolved global history and the failed acquisition gate. **Discovery reached 202/200 URLs (17 new versus at most 15); collection stopped and the entire final 11-URL batch remains held/ineligible.** Capture attempts stay **37/100**. The **402 qualified development candidates / proposed 345+57** remain unchanged. A portable, tested metadata/hash inventory and desktop instructions are ready; the original desktop has not yet been inventoried. **Next: run and reconcile the desktop inventory, resolve acquisition compliance and independent-test coverage/evidence before admission/freeze/export or desktop GPU training.** No training has started; the test remains unsealed with zero admitted/scored records. [Report](evaluations/flood-ner-targeted-test-history-handoff-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical checkpoint below; the targeted-collection/handoff outcome above is newer:

## October 17: Recorded archives and isolated positive test-window selection reconciled

**Archive history and saved-test selection completed; training remains pending:** Verify all **3,863 recorded v3 payloads / 11 parts / 2,357 objects**, **seven historical ZIP entries** and metadata for **19 known Drive items**, with no missing/conflicting recorded payload. Complete isolated positive-window selection and source-only historical comparisons in a separate private curator package; retain the unchanged **60 / 30+30 / 27-positive+3-negative-per-language** target. **Unknown external cross-computer history remains unresolved; test stays unsealed with zero admitted/scored records.** The **402 qualified development candidates / proposed 345+57** remain unchanged. **Next: address the specific remaining independent-test history/evidence/coverage gaps before admission/freeze/export and desktop GPU handoff.** [Archive and saved-test outcome](evaluations/flood-ner-archive-history-test-selection-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: Successor qualification and isolated saved-test reassessment completed

**Successor qualification and isolated-test reassessment complete; training remains pending:** **402 qualified proposal candidates / 149 source cases**, retaining **345 proposed training / 57 validation**; all 259 relationship entries qualify for supported conservative joint grouping without incident-identity or independence claims. Carry forward 64 exclusions and 99 holds; record 16 scoped project-use adoptions for 20 saved-source windows. **The separate 60-passage test stays unsealed: the user is unsure whether all older cross-computer article histories are represented.** Curator-specific evidence/count gaps remain in the safe report. No actual admission, freeze, export or training. **Next: resolve the concrete history/isolated-test gaps; reuse completed development qualification before a separate admission/export/desktop GPU handoff.** [Qualification and test reassessment](evaluations/flood-ner-successor-qualification-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: Successor dataset design and historical training boundary completed

**Successor dataset design complete; retraining remains pending:** Use all **402 provisional candidates** in a separate **345 training / 57 validation proposal** (170/175 training English/Taglish; 37/20 validation). Actual original/A/recovery/B input bindings anchor all 280 historical training records, including now-excluded/held examples. **The old additional 240 / exact-balance quotas are prospectively superseded for this version by explicit user choice; historical specifications and results remain unchanged.** Validation has no Taglish ROAD/LANDMARK or short-code-theme examples; conservative grouping does not certify event independence. **Next: resolve proposed-member source-use/group admission qualifications and complete the separate unchanged 60-passage fresh-test boundary before admission/freeze/export and desktop training.** No actual admission or partition freeze occurs. [Successor design](evaluations/flood-ner-successor-design-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: Saved-only successor dataset proposal completed

**Saved-article successor proposal complete; retraining remains pending:** Read all **91 remaining saved bodies**, account for **565 considered records**, and propose **402 provisional candidates / 64 exclusions / 99 holds**. Candidates comprise 214 original training records, 168 reviewed drafts and 20 new saved-source windows. The 20 windows add 14 LOCAL_AREA spans; all 41 proposed new windows align. **Additional coverage still fails the 240 design: 188 candidates, capped theme/language capacity 169, at least 71 missing cell slots.** Fresh test remains unsealed with zero admitted records. Original data, drafts, reviews, tokenizer, models, scores and source-use decisions verify unchanged. **Next: resolve coverage/use/reference/group constraints and the independent evaluation boundary before admission/export or desktop GPU training; saved-only scope remains in force.** [Successor proposal](evaluations/flood-ner-successor-proposal-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: Additional NER dataset and all existing holds reviewed

**Additional dataset review complete; training readiness remains open:** Read all **244 drafts / 49 full saved articles**, reconcile **65 prior additional holds and 33 original training holds**. New recommendations: **166 keep, 2 correct, 29 exclude, 47 hold**. Eight prior additional holds resolve under existing rules or supported corrections; twelve are excluded with reference questions unresolved; 45 remain held and two new holds are flagged. Two original holds receive separate correction proposals; 31 remain held. The 168 new candidates have **zero usable LOCAL_AREA spans** and capped theme/language capacity 154. **Next: choose successor membership, address coverage/group constraints and complete the independent evaluation boundary before export or desktop training.** All original data, drafts, models, scores and historical partitions remain unchanged. [Additional review](evaluations/flood-ner-additional-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 17: All original NER training passages reviewed

**Original training-data review complete:** Read all **280 training passages / 94 saved article bodies** and check 966 existing spans. Future-only recommendations: **203 keep, 17 correct, 27 exclude from the successor core, 33 hold**. Shared validation passes 301 original/proposal records; frozen tokenizer alignment passes 966 original and 73 proposal spans. Preserve the original experiment, models and all 244 additional drafts. **Next: review the additional drafts under the same criteria, resolve holds/event relationships, then decide successor membership; no retraining yet.** Record AI silver/source-bound judgments, partial correction proposals, language eligibility and 75 conservative cross-pool event-component links. All 52 original admission hashes, 565 additional manifest hashes and 66 selected-model file hashes verify. The 27 exclusion recommendations are training-subset findings, separate from earlier weak validation/test windows. [Review](evaluations/flood-ner-original-training-review-20261017/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Original-plan consistency checked; NER checkout hashes repaired

Review the supplied desktop notes, the entire available original NER conversation and historical/current roadmap. Revalidate 684 schema objects, 52 original admission hashes, 27 qualification/export/preparation payloads, sixteen recorded source bindings and 66 selected-model files. Fix checkout-byte portability through .gitattributes byte preservation and four historical CRLF overrides; source semantics and frozen evidence remain unchanged. A real Git checkout regression and the accumulated tooling/data-gate suites pass 80 methods. Record laptop review/preparation and desktop-only GPU training. New corpus size/convention compatibility and existing readiness/test gates remain open; no collection, export or training occurs. [Report](evaluations/flood-ner-consistency-review-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: V3 Drive restore verified; flood dataset coverage rechecked

Verify eleven transport parts and the 700,047,334-byte archive; restore 2,221 missing files while skipping 1,642 identical files, with zero conflicts. All 565 development manifest hashes and 66 files across six frozen selected models verify; original 460 audited inputs and .env are unchanged. Recheck 244 drafts/179 candidates/65 holds: candidates contain 101 negatives, 78 positives and zero LOCAL_AREA spans. Read six unused captured flood sources and preserve a source-bound positive-coverage review queue. Fresh-test private texts/labels are not inspected; readiness/admission and training remain open. [Audit](evaluations/flood-ner-topic-audit-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Original NER corpus topic audit completed

Rechecked 400 samples/138 articles/40 contexts/1,465 spans, all 52 admission-manifest hashes and four published export input bindings. Source windows/spans and saved grouping separation pass; 460 protected files remain unchanged. Focused reading of five sources queues 19 passages for future selection review; six general-news windows are strong replacement candidates in a successor corpus. Preserve historical flood data and the completed exposed benchmark. Drive review distinguishes the older 139-article backup and 138-article handoff; newer private checkpoints are unavailable here, so additional-dataset readiness remains open. [Audit](evaluations/flood-ner-topic-audit-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: New desktop research artifacts backed up for laptop continuation

**Laptop backup verified:** The owner-only [v3 Drive backup](https://drive.google.com/drive/folders/1JrrMzZ3FyP0LGU00xWKF54enyyC87ffX) contains the newer research artifacts: 3,863 files, including trained checkpoints and additional-dataset packages. All 19 uploaded files pass full SHA-256 readback. Download all files and follow `START-HERE.md` / the [backup receipt](evaluations/flood-ner-laptop-backup-20261016/README.md). Dataset readiness remains open; resume the existing Gate 3 task after verified laptop restoration. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Publication documentation synchronized

Audit the eight authoritative document scopes and update stale feature/system/tooling/handoff summaries to the measured incomplete dataset-readiness state. Preserve the original experiment, historical reports and pending Gate 3/Gate 4 requirements. The existing v2 ZIP does not include newer desktop private checkpoints; Git publishes metadata/code only. Database/schema and architecture decisions are unchanged. Fresh publication checks and excluded local configuration are recorded in the [publication audit](evaluations/flood-ner-publication-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Additional NER acquisition reviewed; readiness incomplete

**Historical acquisition checkpoint; Gate 3 readiness remains open:** Flood-focused acquisition records 365 development candidate URLs (363 article keys) / 182 capture attempts / 159 captures. The draft has **244 passages / 49 articles**; **179 source-reading candidates and 65 held records** cannot meet the 240-passage theme/language quotas (candidate capacity 156). One frozen-tokenizer alignment failure is preserved. Admission, grouped partition freeze, export and training remain zero. The isolated curator result is recorded separately; no fresh-test readiness is assumed. **Next: resolve the recorded dataset-readiness gaps under the same Gate 3 task.** [Readiness report](evaluations/flood-ner-additional-dataset-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Gate 3 improvement specification prepared

**Gate 3 improvement preparation complete; no retraining started:** The versioned reference-scope addendum accounts for all 14 review questions. The constructed matrix has **48 cases / 24 English / 24 Taglish**, including **30 positives, 16 negatives and 2 explicitly unscored unresolved cases**; 12 preparation-integrity tests pass. Training/validation coverage and acquisition requirements are recorded, together with a fresh **60-passage / 30+30-language test protocol, three negatives per language**. Original annotations, scores and model roles stay frozen. **Next: prepare and admit the additional dataset**, reconciling historical exclusions, source-use eligibility, grouping and isolated held-out access before deciding size/recipes. CPU/Linux/failure/performance qualification and Gate 4 integration remain pending. [Preparation report](evaluations/flood-ner-improvement-preparation-20261016/README.md); [reference-scope addendum](guides/flood-ner-reference-scope-addendum-v1.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Full Gate 3 model-qualification review complete

**Gate 3 qualification review complete; operational qualification remains open:** Codex reads all **60 held-out passages / 22 articles**, records **120 original/A seed 0 assessments** and accounts for all **391 FP/FN events**. Fourteen passages retain AI reference/convention questions; no label, offset, score or model choice changes. Original seed 0 remains primary (**63.12 test F1**) and A seed 0 exploratory (**67.72**). All 42 event-count slices and preservation checks pass. Next prepare the remaining Gate 3 qualification specification (reference-scope addendum, constructed regression matrix and bounded CPU/Linux/failure/performance plan) before Gate 4 integration. No inference, training or test rerun occurs in this review. [Review](evaluations/flood-ner-model-qualification-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Senior-planner documentation synchronization

Audit all eight authoritative record scopes against the hash-verified [held-out report](evaluations/flood-ner-heldout-test-20261016/README.md), saved 59-test verification and 240 metric checks. Update the existing feature/system NER descriptions from preparation-only status to completed offline evaluation, register both test commands, and keep runtime integration/production acceptance open. Preserve dated research/release history, Decision 30 and unchanged database design; no new architecture decision or flagship feature is introduced. Task plan, roadmap, index and current guides agree that the next work is the existing Gate 3 error/qualification record before Gate 4 isolated integration. No training, test-inference rerun, fresh test suite, dependency change, commit or deployment occurs in this documentation audit. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Fixed-roster held-out NER evaluation complete

**Held-out NER evaluation complete:** The six frozen original/A checkpoints and two baselines complete one evaluation on **60 test passages / 290 spans**, 30 English/30 Taglish. Original seed 0 remains primary at **63.12 six-class F1**; exploratory A seed 0 scores **67.72**. Three-seed means are **68.46 original / 70.24 A**, with sample SD **4.85 / 2.20 percentage points**. Rules score **58.97 six-class F1**; native LOC scores **67.02 on the separate coarse task**. All 59 focused tests, 240 metric reconciliation checks and preservation checks pass. Test results are now exposed; no further tuning or seed selection uses them. Next complete the existing Gate 3 model-qualification/error review before Gate 4 isolated integration. [Held-out report](evaluations/flood-ner-heldout-test-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Original NER family and bounded validation trials complete

**Frozen experiment and bounded validation trials complete:** Original seeds 0/1/2 reproduce development F1 **67.15 / 70.59 / 72.29**; seed 2 succeeds in its separate authorized recovery folder. Recipe A wins the seed 0 comparison (**71.81**, versus B **70.70**) and completes robustness seeds 1/2. A family mean is **72.61**, sample SD **0.92 percentage points**; original mean is **70.01**, sample SD **2.62**. Original seed 0 remains primary. All five permitted new runs complete before the renewed cutoff; 43 focused tests pass. Prior artifacts, GPU environment, dependencies and .env verify unchanged. Next freeze the final experiment/checkpoint decision, then perform separate held-out testing under the frozen protocol; test predictions remain untouched. [Completed report](evaluations/flood-ner-validation-study-20261016-v2/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Validation comparisons delivered; seed 2 output repair verified

**Validation study partial; seed 2 retry pending:** Seed 0/1 selected-model F1 reproduces at 67.15/70.59 on 60 development passages. Frozen rules score 63.28 six-class F1; native pretrained NER scores 68.83 only on the separate coarse LOC task. Seed 2 stops on redirected Windows Unicode output; the UTF-8 repair passes regression tests, but no further training runs under the approved failure rule. Recovery and A/B recipes are preregistered, not executed. All 10,859 prior artifact hashes, 23 model files, environment/package audits and .env remain unchanged; 43 focused tests pass. Test predictions remain untouched. [Partial report](evaluations/flood-ner-validation-study-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Primary training complete; manual robustness launchers ready

**Primary seed 0 training complete:** The researcher manually ran the frozen GPU recipe. The selected development checkpoint is step 455, F1 67.15 / precision 68.32 / recall 66.03; early stopping ends at step 630 after 175 steps without improvement. All 103 run files remain unchanged; test predictions remain untouched. Manual check-only launchers for robustness seeds 1/2 pass; 29 focused tests pass. Next run seeds 1/2 and the frozen baseline comparisons, keeping seed 0 primary. [Training result](evaluations/flood-ner-primary-training-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Manual primary-seed launcher ready

Delivered an explicit opt-in PowerShell launcher for the researcher to run seed 0. Default mode only revalidates frozen inputs; -StartTraining starts the existing GPU recipe with live output, persistent logs and a completion record. It refuses changed inputs/existing destinations. PowerShell parsing, actual check-only execution and 26 focused tests pass. No training starts and later seeds are not automatic; Codex will review the manual result before handling later runs. [Instructions](guides/ner-first-manual-training-20261016.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Baselines/configurations frozen; GPU initialization passes

**Baseline/training preparation complete:** Frozen rules type/original-offset mapping and seed 0/1/2 configurations pass initialization on the RTX 3060 Ti using the verified qualified export. Each initializes six location labels, 46 GPU parameter arrays and the two CPU upper-classifier arrays required by the pinned architecture, with the exact candidate tokenizer and copied pretrained NER encoder. No optimizer updates, corpus prediction evaluation or held-out test reading occurred. Twenty-one focused unittest methods pass. All 10,531 prior artifact hashes, 23 model files, 22,759 audited research-environment file stats, CLI package versions and .env are unchanged. The next task is the first primary-seed training run under the frozen development-selection protocol. [Preparation verification](evaluations/flood-ner-experiment-preparation-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Qualified location export verified

**Qualified training-format export complete:** The new offline export-qualified-corpus command binds the admitted 400 samples/138 articles to the passing calamanCy tokenizer and frozen evaluation contract. Verified 280/60/60 DocBins, 200/200 languages, 1,465 spans, 48 negatives and 40 contextual references without adding contextual samples. All six primary/replay DocBins reload correctly; their three partition files, tokenizer and metadata provenance match byte-for-byte. Twelve focused unittest methods pass. All 10,500 prior artifact hashes, 23 model files, research-environment file metadata and .env remain unchanged. Baseline/training preparation is next; no model predictions, training or deployment occurred. [Export verification](evaluations/flood-ner-qualified-export-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: CLI compatibility repaired; corpus tokenizer qualified

**Desktop CLI repaired; corpus tokenizer qualified:** Restored only the existing NumPy 1.26.4 / SciPy 1.14.1 pins in backend/venv; spaCy, Thinc and the GPU research environment remain unchanged. The separately recorded qualification passes on 400 samples / 138 articles / 40 contextual pairs / 1,465 spans, with zero candidate alignment errors, all 56 constructed controls passing and reproducible serialization/reload. The frozen evaluation contract now binds the qualified candidate. All 10,458 pre-existing artifact hashes, 23 model files, research-environment file metadata and .env verify unchanged. Training-format export is next; no export, NER predictions, training or deployment occurred. [Qualification and repair](evaluations/flood-ner-desktop-tokenizer-qualification-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Desktop corpus restored; tokenizer execution blocked

**Desktop restoration complete; tokenizer qualification blocked:** Fast-forwarded the existing roi-branch checkout to 4736cea, verified the private ZIP and restored 697 missing files while skipping 1,060 identical files without conflicts. All 1,757 payload hashes verify. The admitted corpus reconciles to 400 samples / 138 articles / 40 contextual pairs / 1,465 spans, with 200/200 languages and 280/60/60 partitions. All 9,744 existing artifact hashes, 23 model files, research-environment file metadata and local .env are unchanged. The single generated qualification attempt exits during the backend CLI spaCy/Thinc import with a NumPy ABI size mismatch, before the isolated worker starts. No alignment/reload pass, dependency repair, export or training is claimed. Resolve CLI compatibility before a separately recorded qualification attempt. [Desktop result](evaluations/flood-ner-desktop-restoration-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Private desktop handoff delivered

**Private desktop handoff delivered:** The [new Drive folder](https://drive.google.com/drive/folders/1gnGV2wP0gNHx2LNa64fwc-U4AIQxRdkT) contains seven owner-only files, including the unchanged v2 ZIP and desktop instructions. All seven uploaded files pass byte/hash readback; the ZIP matches 28,476,420 bytes and its frozen SHA-256. The 400 samples/40 contexts, original capture evidence, partitions and scoped admission are unchanged; all 5,234 prior preservation entries verify. No sharing changes, desktop restoration, corpus qualification, export or training occurred. [Report](evaluations/flood-ner-desktop-drive-delivery-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Git handoff implementation pushed:** `ac1ae53` is verified on `origin/roi-branch`; private data/ZIPs remain ignored. Drive delivery remains pending, with no desktop restoration or qualification claimed. [Receipt](evaluations/flood-ner-desktop-handoff-20261016/publication-receipt.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Laptop handoff and temporary restoration verified

**Laptop handoff prepared and restoration verified:** The private v2 ZIP contains **400 admitted locations / 40 contexts**, 138 selected articles and all **407 original capture-evidence files**. Its **1,757 payload files** restore with identical hashes; a second restore skips every identical file. All 400/40 qualification inputs and selected publication evidence revalidate offline. **880 software tests passed; one skipped** (40 new handoff tests). The 23 recorded desktop/laptop model identities match; weights and environments are excluded. Three historical evidence gaps remain unreconciled; eleven invalid-test references and ten copied-manifest path aliases are separately classified. Drive delivery remains pending because this chat still sees the school account and cannot access the owner-only personal folder. Desktop restoration and tokenizer qualification have not run. [Report](evaluations/flood-ner-desktop-handoff-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Corpus-tokenizer tooling/protocol delivered; execution blocked

**Corpus-tokenizer tooling delivered; actual qualification blocked:** Added the separate tokenizer-only qualify-corpus-tokenizer command and froze the silver-reference evaluation protocol. The one permitted unchanged-environment retry fails at spaCy import with Windows Application Control error 4551 on torch_python.dll or a dependency, before tokenizing any passage. No model predictions, alignment pass, tokenizer promotion, export or training is claimed. **840 software tests passed; one skipped**, including 68 new tests; the older 772/one result remains historical. Verified 17 artifact checks, 5,234 preserved prior files and all 23 model hashes. The 400 admitted locations/40 contexts, 200/200 languages, 280/60/60 partitions, twelve nonacademic outcomes and research-only originals remain unchanged. The contract is protocol-frozen with qualified-tokenizer binding pending; no test-set model results were opened. [Report](evaluations/flood-ner-corpus-tokenizer-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Private academic-use admission applied

**Private academic-use admission applied:** A separate derivative contains **400 admitted location samples from 138 articles and 40 consistently updated contextual pairs**. Only source.admission_status, source.reuse_status and scoped source.reuse_terms change; text, annotations, identities, reporting groups, 200 English/200 Taglish, 280/60/60 partitions, all holdouts and ten pilots are preserved. The ledger retains 69 explicit adoptions, 68 desktop-reported adoptions and one prior local adoption; the missing detailed desktop predecessor remains unreconciled. This is an AI-authored project-use application under researcher delegation, not publisher permission, legal approval or a dataset license. All twelve nonacademic outcomes are unchanged. Verified 41 negative artifact checks, 21 byte-identical replay files, 5,101 preserved checkpoint/capture files and 23 model hashes. The new derivative/replay adds 960 complete-body string fields, not new articles. Research-only originals remain unchanged and refuse export. Source admission is 400; exports and training remain zero. No pytest rerun; 772 passed/one skipped remains historical. [Results](evaluations/flood-ner-academic-admission-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Research cohort/context v5 frozen

**Frozen research revision v5 complete:** Cohort-v5/contextual-v5 reload successfully with **400 locations/40 contexts from 138 articles**, 200 English/200 Taglish, 280/60/60 partitions, 1,465 location spans and 48 negative passages. Exact reviewed assembly preserves 388 location records (including all 383 fixed records, holdouts and ten pilots) and 38 contextual pairs; twelve locations/two pairs are replaced without reselection. Four scoped decisions and 134 preserved dispositions are bound to every source/sample and the new manifests, giving **derived recorded private-basis coverage of 138/400**. The missing detailed desktop predecessor remains unreconciled; no publisher permission or admission is inferred. Verified 32 negative artifact checks, 22 byte-identical replay files, 2,966 preserved prior files and 23 model hashes. The complete generated-copy audit counts 960 body-string fields, including contextual evidence; these are copies, not new articles/samples. All source flags remain research_only/unknown; admission/export remain zero. No pytest rerun; 772 passed/one skipped remains historical. [Current frozen dataset](evaluations/flood-ner-research-assembly-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Proposed seventeen-passage scope reviewed

**Proposed seventeen-passage scope review complete:** All twelve draft sentences are accepted silver location candidates, five retained windows are confirmed unchanged, and two contextual replacements are reviewed. The proposed **400 locations/40 contexts** pass every quota in memory while preserving all **383 unaffected records**, test samples and pilots. Four changed article selections receive explicit private project-basis adoptions; carrying 134 prior dispositions gives **derived proposed coverage of 138 articles/400 passages**, with the detailed desktop predecessor still unreconciled. The current cohort-v4/contextual-v4 and its four old holds/17 passages remain unchanged; no frozen revision, admission or export was created. Verified 33 negative artifact checks, fourteen byte-identical replay files, 2,903 preserved checkpoint files and 23 model hashes. No new complete-body copies or pytest rerun; 772 passed/one skipped remains historical. [Reviewed inputs and decisions](evaluations/flood-ner-held-scope-review-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Seventeen held-passage alternatives checked

**Seventeen-passage alternatives feasibility complete:** Verified a reviewed 400-slot witness and a smaller conditional proposal with all **383 unaffected records fixed**. The recommended proposal retains five existing windows and adds twelve unaccepted sentence drafts, reducing selected text across four held articles from **3,087 to 2,057 characters**. All quotas pass conditionally; twelve language/location reviews, four changed-scope use assessments and two contextual replacements remain. Current cohort-v4/contextual-v4, 400/40 records, 134/383 project-basis coverage and four holds/17 passages are unchanged; admission/export remain zero. Verified 2,839 prior files, 23 model hashes, byte-identical replays and 17 direct negative artifact checks. No pytest rerun; 772 passed/one skipped remains historical. The [generated-copy inventory](evaluations/flood-ner-held-alternatives-20261016/copy-inventory.json) separately records the new private witness/replay representations; no new articles were collected. [Results and proposal](evaluations/flood-ner-held-alternatives-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Twelve held private-use cases decided

**Twelve-case private-use decision review complete:** Eight articles/32 passages receive explicit limited project-basis adoptions; four editorial articles/17 Taglish training passages retain their holds. Preserving the other 126 dispositions gives derived coverage of **134 articles/383 passages** for cohort-v4, with **4/17 held**. All 400 location records, 40 contextual-v4 pairs, partitions, tests/pilots and source flags remain unchanged. Verified 2,802 prior files, 23 model hashes, deterministic replay and 35 direct negative artifact checks. Admission/export remain zero; the missing detailed desktop predecessor remains unreconciled. The 772-passed/one-skipped software result is historical; no pytest rerun occurred. [Verification and remaining actions](evaluations/flood-ner-held-decisions-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Bounded research revision completed

**Bounded research revision complete:** 400 reviewed location records from 138 articles and 40 contextual-v4 pairs meet every unchanged quota. Reviewed 120 windows (110 accepted/ten rejected); preserved 330 unaffected references, all 60 test samples and ten pilots, using two of the permitted 20 additional changes. Final cohort-v4/contextual-v4 replay byte-for-byte; 2,661 prior files and model/tokenizer hashes remain unchanged. Derived project bases cover 126 articles/351 passages; 12 articles/49 passages remain held. Admission/export are zero; the detailed desktop predecessor remains unreconciled. **772 tests passed; one skipped.** [Verification and scopes](evaluations/flood-ner-research-revision-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Saved-pool revision feasibility completed

**Saved-pool revision feasibility complete:** All four tested scenarios are infeasible with the 332 unaffected records fixed. Verified the 1,340-passage/342-article pool; 893 unused candidates remain after fixed-sample conflicts, plus 106 unreviewed whole-paragraph shortening proposals. GMA is at its 160-sample cap, RMN lacks reviewed English candidates, and specific training/validation label quotas remain deficient. No qualifying 400-slot proposal was found. All 400 location records, 40 contextual-v3 pairs, partitions, ten pilots and source-use decisions remain unchanged; admission/export remain zero. All four bounded solver runs return status 2 and their replays match. Independent necessary upper bounds identify six support deficits. Five contextual pairs would need future replacement; the other 35 retain category/language/article support. 99 focused tests pass (13 new analysis guardrails plus existing selection/qualification tests); 2,621 prior files and 23 model hashes verify unchanged. No corpus replacement, new collection, admission, inference/training, messages, uploads or Git publication. [Feasibility and exact deficits](evaluations/flood-ner-revision-feasibility-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Corrected default source-use adoptions

**58-case default-adoption correction complete:** Read all 58 complete articles and their 205 selected passages. Explicit reassessments retain 49 adopted private project bases / 157 passages and assign nine holds / 48 passages. Preserving the ten special cases and 71 earlier dispositions gives derived adopted coverage of **125 articles / 332 passages**, with **14 held articles / 68 passages**. The earlier completion claim and 134/380 totals are superseded. All 400 samples/40 contextual-v3 pairs, partitions and source flags remain unchanged; training admission/export remain zero. Acquisition remains Unknown / Codex collected. The unavailable detailed desktop predecessor is still unreconciled. Structural checks bind the authored findings; they do not prove substantive/legal adequacy. Verified 1,524 preserved files, 116 content pointers, 22 statute/policy pointers, 23 model file hashes, 26 direct negative artifact checks, deterministic replay and 400 research-only export refusals. A separate focused constructed evidence/package run passed 109 tests; no new full-suite or model result. [Current correction](evaluations/flood-ner-default-adoption-correction-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 16: Earlier 68-case completion claim — superseded

**Historical claim, superseded by the correction above:** Recorded 63 new limited private-use project-basis adoptions / 220 passages and five specific retained holds / 20 passages under explicit researcher delegation. Preserved 71 prior dispositions, producing derived coverage of 134 articles/380 passages. All 400 location samples, 40 contextual-v3 pairs, partitions and source flags remain unchanged; admission/export remain zero. Acquisition is Unknown / Codex collected. Corrected the Philstar contents-only evidence pointer in the new packet; 22 substantive/provenance pointers and 14 negative artifact checks pass. Recomputed four local copy containers, including the ZIP; verified 1,500 prior files and 23 model hashes unchanged. No runtime/dependency/schema changes, suite rerun, model processing, messages, uploads or publication. Missing desktop predecessor remains unreconstructed. [Results](evaluations/flood-ner-remaining-decisions-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: GMA AFP private-use project case decision recorded

Codex, acting under existing researcher delegation, adopted the completed narrow private research rationale for one AFP-attributed GMA article / three passages, retaining all recorded uncertainties. The derived total is 71 adopted-basis articles/160 passages (70 from verified desktop metadata plus one local case decision), with 68 articles/240 passages held. No missing private v1 was reconstructed or canonical v2 claimed. Verified 1,479 prior files unchanged, 23 model hashes, 13 inherited/two new clause pointers, frozen 400/40 bindings and 400 research-only export refusals. Two primary legal captures pass; one IPOPHL refresh fails explicitly. No admission, exports, training or test-suite rerun. [Results](evaluations/flood-ner-afp-case-decision-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Acquisition audit and proposed decision supplement completed

Verified all 68 ABS-CBN/Philstar browser captures / 240 passages, 204 source/entry/snapshot references and all 139 source-text hashes. Prepared 69 source-bound decision drafts: one proposed AFP-story adoption and 68 retained holds with precise questions. No historical login or acceptance facts were inferred from missing snapshot fields or current HTTP code. All 400 samples/40 contextual-v3 pairs, partitions, flags and twelve nonacademic outcomes remain unchanged; 1,462 prior files verify. Existing validation passes and all 400 research-only records refuse export. No new applied decision, admission, export or training; no test-suite rerun. [Report](evaluations/flood-ner-acquisition-decisions-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Laptop held-source research supplement completed

**Laptop source-use research supplement complete:** Reassessed all 69 held articles / 243 passages and reconciled all 139 articles / 400 memberships using the existing laptop corpus, original evidence and verified desktop summaries. Proposed one narrow private research basis for the GMA AFP story (three passages); 68 retain the research hold recommendation. All 69 actual project holds and the 70 reported delegated adoptions / 157 passages remain unchanged. Confirmed Reuters attribution, corroborated the selected AFP-caption credit and matched the QA-source wording to the public Philstar counterpart. Saved 21 capture attempts (12 initial content passes / nine failures), 21 verified clause pointers and explicit uncertainty. 64 focused tests pass; 1,402 prior files and 23 model files verify unchanged. No v2 decision, admission, export, inference/training, publisher message, upload or Git publication. [Research supplement](evaluations/flood-ner-held-reassessment-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Laptop continuation handoff prepared

**Laptop continuation handoff prepared:** The latest completed record remains delegated decisions v1: 70 GMA articles / 157 passages adopted; 69 articles / 243 passages held. Official-source research is approved but unfinished; preliminary browsing produced no saved v2 checkpoint or new hash-bound research evidence. Continue the same source-use task on the laptop using the [handoff guide](guides/ner-laptop-continuation-20261015.md). A verified local private delta ZIP carries the two new desktop checkpoints and documentation snapshots; older research artifacts remain prerequisites. No Git publication, cloud upload, laptop restoration or admission/training/deployment was performed. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Existing source-use task advanced through delegated decisions

**Existing source-use task — delegated decisions recorded (partial):** Codex, acting under explicit researcher delegation, adopted the saved private academic-use recommendation for 70 GMA articles / 157 passages and retained the 69 holds / 243 passages (one AFP-credit GMA article, 50 ABS-CBN and 18 Philstar). The source-use basis is not finalized for the held articles. Original AI proposals and blank historical forms remain unchanged; the current dispositions are in a separate ignored versioned record. No independent human review, publisher authorization or legal approval is claimed. All 139 articles / 400 memberships, nine proposal bindings and saved evidence verify. Admission and source-use flags remain unchanged; no export, training or deployment. [Delegated decision record](evaluations/flood-ner-project-decisions-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Source-use decision checklist prepared

**Source-use decision checklist prepared:** Created the ignored academic-decision-checklist-20261015-v1 checkpoint with a publisher checklist, 139-article CSV and hash-bound verification. Reconciled all 400 memberships without duplicates or omissions; preserved 70 recommended/69 held articles and 157/243 passages. All nine proposal bindings, nine used evidence records and the existing read-only proposal validator pass. The three missing historical audit references remain separately recorded. Original annotations, 40 contextual-v3 pairs, partitions, decision forms, source-use flags, GPU checkpoint and backend/.env remain unchanged. Checklist preparation alone is complete; researcher decisions and admission remain unresolved. [Completion report](evaluations/flood-ner-decision-checklist-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Laptop NER research checkpoint restored on desktop

**Laptop research restoration complete:** Three downloaded ZIPs match the supplied SHA-256 hashes. Restored 946 missing files at organized and original checkpoint paths, skipped 17 identical files and found no conflicts. Verified 400 locations/139 articles, 40 contextual-v3 pairs, 200 English/200 Taglish and 280/60/60 splits. Current review/proposal validation passes with all nine required bindings; three older audit references remain absent from the supplied backup. Existing desktop work, backend/.env and GPU environment are preserved. No admission, training or deployment. [Restoration report](evaluations/flood-ner-desktop-restore-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: GPU preflight timeout diagnostics repaired

**GPU preflight review fix complete:** Timeout handling now preserves partial stdout/stderr for either worker and includes the logs in the failed report hashes. Four regression scenarios reproduced the defect before repair; all 126 focused tests now pass. Previous GPU qualification evidence is preserved; no dependencies, model weights, news admission or schema changed. [Fix verification](evaluations/flood-ner-gpu-timeout-fix-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: RTX desktop GPU environment qualified

**RTX desktop GPU preparation complete:** Actual RTX 3060 Ti 8 GB / driver 610.47 verified. Isolated Python 3.11.17, spaCy 3.7.5, CuPy 13.6.0 and Torch 2.11.0+cu128 pass native inference, six-class constructed updates at batch sizes 1/4/8 and saved-model CPU replay. 122 focused tests pass; 73 installed packages are compatible. All 23 original model files verify unchanged. No news-model processing, admission, production or schema change. [Results](evaluations/flood-ner-desktop-gpu-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Desktop publication verification

**Desktop publication checks complete:** User authorized `roi-branch` publication for desktop continuation. Fresh full NER/location verification: 721 passed, one Windows symlink test skipped (67.31 seconds). New tooling uses existing dependencies or the standard library; no schema/migration change. Git attributes preserve hash-bound helper/guide bytes. The collector and metadata reports transfer through Git; full dataset text, weights and environments require the private backup and local environment recreation. All 400 samples/40 contextual-v3 pairs and admission holds remain unchanged. [Publication checkpoint](evaluations/flood-ner-desktop-publication-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: NER route alignment and desktop inventory

**Existing NER plan continued — desktop inventory prepared:** Preserve the corrected 400 samples/139 articles, 40 contextual-v3 pairs, frozen partitions, calamanCy and tokenizer checkpoints. The researcher confirmed an October 25 defense target requiring deployed LANES integration and RTX desktop availability this week. Publisher correspondence is optional clarification: a supported applicable statutory exception remains an existing use-basis route. No recommendation or admission was changed. Delivered a standard-library-only hardware inventory; this machine is the MX330 laptop, so RTX desktop/CUDA/training qualification remains pending. 83 focused tests pass, one Windows symlink test skipped; 1,366 prior files and 23 model files verify unchanged. [Readiness and route alignment](evaluations/flood-ner-desktop-readiness-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Held-article clarification drafts prepared

**Held-article clarification packet prepared:** Four unsent drafts and four blank response forms cover 69 held articles / 243 passages (50 ABS-CBN, 18 Philstar, one AFP-credit GMA story). Verified exact identities, 10 bindings, nine substantive evidence records, Unicode CSV round trips and 1,341 prior files; 64 focused tests pass. No recipients verified, messages sent, uploads, resolved holds, project decisions, admissions or successful exports. All 400 samples/40 contextual-v3 pairs and partitions remain unchanged; the 70 GMA/157-passage recommendation is preserved. [Packet report](evaluations/flood-ner-held-clarification-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Private academic-use decision proposals

**Private academic-use proposals completed (702 regressions pass; owner-only Drive delivery verified):** Prepared 139 article recommendations and three publisher summaries, rechecking all 78 flagged sources under private owner-only research/training. Recommend 70 GMA articles covering 157 passages; hold 69 articles covering 243 passages (50 ABS-CBN, 18 Philstar, one AFP-credit GMA story). Missing bylines alone are not exclusions. All 400 annotations and 40 contextual v3 pairs remain frozen; actual project decisions, training admission and exports remain zero. The recommended subset alone fails the original 400-sample/publisher requirements. Retention is undecided and is not itself a training prohibition; adviser guidance is researcher-reported and the ethics framework unspecified. Four refreshed publisher-policy pages are readable; the IPOPHL ordinary fetch failed its content check and is retained explicitly. New forms replace ambiguous bare-filename references with bound root-relative paths, while older forms remain unchanged. All twelve other-use outcomes retain their states. [Proposals and method notes](evaluations/flood-ner-academic-proposals-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: NER documentation and publication audit

**NER publication checkpoint:** The corrected 400-sample/139-article AI silver cohort and 40 contextual v3 pairs remain frozen. Constructed tokenizer qualification, versioned correction/packaging tools and three academic-use AI reviews are complete. Adviser guidance is researcher-reported: private research/training only; the ethics framework is unspecified. Drive backup is verified and owner-only across 22 checked items. Three academic-use decisions remain unresolved; retention is undecided and is not itself a training prohibition. The next task is the supported academic-use basis and article-exception decisions, followed by separate admission, news-cohort tokenizer qualification and desktop GPU preparation. Fresh focused verification passes 664 tests (94.60 seconds); no new dependency, database migration, training or production change. User authorized commit/push to roi-branch; Git publication is verified separately after these checks. Full text, weights, environments, Drive account evidence and editable project decisions remain ignored. The existing Drive backup retains the full corrected study package. Audited decisions/database/bug-log records without introducing routine architectural or schema entries. [Checks](evaluations/flood-ner-publication-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Owner-only study access verified

**Private research access verified:** Recorded researcher-reported adviser acknowledgment and private research/training-only guidance. At the user’s explicit owner-only instruction, restricted the original Drive folder and verified all 17 existing items have only the owner, with no anyone/domain access. No teammate/adviser invitations were sent. The ethics framework remains unspecified, retention undecided, and three academic-use decisions unresolved. No publisher permission or admission is inferred. Earlier dataset, backup and review hashes remain preserved. No software/dependency change, model work or Git publication. [Record](evaluations/flood-ner-private-access-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Adviser guidance recorded and access mismatch identified

**Adviser guidance reported:** The user reports adviser acknowledgment and instruction to keep the dataset private, solely for research/training. The reported international ethics framework is unspecified; no written institutional approval or publisher permission is inferred. Drive still allows anyone-with-link editing, so named-account access needs to be arranged using exact teammate/adviser accounts. No sharing settings or admission flags changed. Retention remains undecided and is not by itself a training prohibition. Current permission reads confirm the root folder and uploaded ZIP remain link-editable. Exact recipients are requested before changing access. All prior study/review artifacts remain unchanged; no software or dependency change. [Record](evaluations/flood-ner-adviser-guidance-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Researcher facts and verified study backup

**Study storage update:** Recorded the user’s BSIT capstone purpose, no known school instructions or publisher permission, and undecided retention with an interest in preservation for a year or longer. Completed a user-authorized, hash-verified Drive backup of the corrected study package and article/sample CSVs. The user reports sharing the link only with groupmates and chose to retain anyone-with-link editing; access is not restricted to named team/adviser accounts. Future-researcher use remains undecided. All three academic-use decisions and training admission remain unresolved; source-use basis and article-exception dispositions are still next. No model work or Git publication. Uploaded twelve files into four new Drive folders. The 6,206,707-byte ZIP has 607 verified entries and a matching downloaded SHA-256; CSVs contain 139 article rows and 400 sample rows. All earlier local files and admission flags are unchanged. Data/docs only; the earlier 664-test result was not rerun. [Report](evaluations/flood-ner-study-arrangements-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Academic-use review completed with admission decisions unresolved

Completed three source-bound AI academic-use conclusions and 139 article credit/amount reviews for private research-team/adviser use. GMA policy supports educational/noncommercial downloading; scope-matched NER permission is not established for the full workflow. ABS-CBN and Philstar likewise need a supported scope-specific basis. Seventy-eight articles have overlapping follow-up flags, including missing captured bylines, eight opinion/editorial sources, nine whole-article samples and origin/caption/host questions. Three academic decisions and twelve other-use outcomes remain unresolved; training admission/export stay zero. All 400 locations, 40 contextual v3 pairs, partitions and checkpoints are unchanged. Final focused verification: 664 tests pass; historical broader counts remain separate. Retained failed policy checks and precise source/amount distinctions; no institutional sign-off or retention period is invented. The next-action sheets separate researcher facts, school guidance and rights-holder questions. Checkpoint/model/environment verification passes and the 400-record export hold remains enforced. [Report](evaluations/flood-ner-academic-use-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: NER annotation corrections and refreshed study package

Corrected three location records and one contextual pair in a new revision: 400 AI silver samples from 139 articles, 1,497 location spans and 40 contextual v3 pairs. Passage/source text, identities, reporting groups, 280/60/60 partitions and ten retained pilots are unchanged; every hard quota passes. The corrected organized package has 606 verified files plus its manifest and a byte-identical replay. 638 focused NER/location tests pass; the historical 666-test result is a different selection. All fifteen source-use outcomes remain unresolved; training admission, DocBin export and distribution readiness remain zero. Earlier cohorts, contextual v2, packages, model/tokenizer artifacts and checkpoints are preserved. Verified 9,145 prior artifact files, the earlier 26,679-file preservation set, 514 earlier evaluation files and all 23 model files; main environment unchanged. [Report](evaluations/flood-ner-annotation-correction-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Source-use assessment and organized study package

Prepared an organized private study/appendix/download-candidate/use-review folder for the 400 samples from 139 articles and 40 contextual v2 pairs. Nine AI use assessments are reviewed and six production/model-distribution assessments deferred; all fifteen outcomes remain unresolved. Ten training-only appendix examples have five English/five Taglish passages, all six location classes and all three publishers. The download candidate has 391 passage texts plus nine metadata-only entries; two contextual payloads are also withheld because their passages equal complete articles. All 400/40 remain intact privately. Byte-identical replay verifies 603 files plus the manifest. Training admission, DocBin export and distribution readiness remain zero. 666 regression tests pass; 41 bundle tests were rechecked after adding saved-file indexes. No publication or external backup. [Results](evaluations/flood-ner-study-use-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Constructed calamanCy tokenizer qualification

Constructed tokenizer qualification passes on 48 cases (24 English/24 Taglish): candidate lanes.tl.calamancy-address-v1 has zero strict alignment errors and all 56 controls pass. Native has 22 errors; unchanged corpus v3 has 14 on these expanded probes. Tokenization changes in 13 cases and coarse model predictions in 12, without establishing accuracy. Replay tokenizer bytes/predictions match; original 24 native predictions, all 23 model files, 26,584 prior artifacts and main packages are unchanged. Final verification: 625 tests pass. The 400 silver locations and 40 contextual v2 pairs remain prepared; twelve source/use decisions, news-cohort tokenizer qualification and GPU preparation remain open. News evaluation/admission/export/training stay zero. [Results](evaluations/flood-ner-tokenizer-qualification-20261015/README-v2.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Documentation and roi-branch publication audit

Audited all eight authoritative records against the completed stronger cohort and isolated preflight. Updated the task plan and roadmap with ordered source-use, tokenizer and desktop GPU preparation gates; recorded the proposed i7 9th-generation/16 GB RAM/RTX 3060 Ti 8 GB machine without claiming a GPU benchmark. Updated the documentation index and system research status. Retained separate production/research dependencies and source-use holds. A fresh isolated regression run passes 586 tests in 32.30 seconds with one existing spaCy/Click deprecation warning. No SQLAlchemy model or migration changes, so no migration run is required. Added raw-byte Git attributes for frozen report formats to preserve their manifest identities. Full article text, weights, datasets and environments remain ignored and require a separate external backup. Publication is explicitly authorized for roi-branch; training and deployment remain pending. [@roicambe](https://github.com/roicambe) (Roi Cambe).

## October 15: Study-use packet and isolated calamanCy preflight

Prepared the 139-article/400-sample study-use packet with twelve separate publisher/use decisions still unresolved. Pinned calamanCy md 0.1.0 passes isolated CPython 3.11.17/spaCy 3.7.5 CPU preflight on 24 constructed cases (12 English/12 Taglish), with 240 measured calls, repeat-identical predictions and two native tokenizer reference-boundary gaps. All 23 model files and dependency lock hashes verify. Main LANES environment, current 400 location records/contextual v2, frozen partitions and 3,668 prior artifact files are unchanged. 586 tests pass. News-model inference, training admission/export/training and production qualification remain zero. The measured short-probe CPU profile has 681.95 ms load excluding imports, 13.66 ms median/15.58 ms p95 and ~405 MiB peak working set. Preserved transient resolver/security, relative-path, Click and UTF-8 failures; no security protection changed. Restored only the task-owned launcher registration and recorded --no-registry for future setup. [Report](evaluations/flood-ner-preflight-use-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: NER follow-up source review and pre-evaluation qualification

Follow-up source review corrected 13 contextual facts in five records in a new v2: nine access-negation rows, one rainfall/flood-onset role and three unsupported universal vehicle closures. All 40 paired records still meet coverage; the 400 location records and frozen 280/60/60 partitions are unchanged. Qualification of the 139 selected sources and all 400 spans/records passes. Saved-tokenizer hash reporting is corrected. A silver-evaluation protocol and publisher source-use inventory are delivered; 546 tests pass and 1,779 prior artifact files are unchanged. Source-use admission, actual model/tokenizer/resource qualification and independent reference review remain open; model inference/training/export are zero. Added explicit access-phrase and non-flood temporal-role guards plus stable candidate-tokenizer hash reporting, with 21 new regressions. The updated dedicated folder contains current contextual-pilot-v2 and 1,059 verified bundled files. No dependency/schema/runtime/model installation, deployment or Git publication. [Report](evaluations/flood-ner-review-qualification-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 15: Stronger 400-sample annotation revision completed

Completed the stronger annotation revision: 400 AI silver location samples from 139 articles, exact 200 English/200 Taglish and frozen 280/60/60 partitions; every hard quota passes. Forty reviewed contextual pairs belong to training and add no samples. All 156 pending captures were read and all 36 failures retried within the original ledger. The reviewed research register contains 342 sources; 1,331 eligible passages remain after duplicate/overlap rejection. Both cumulative bounds are reached: 300 additional URLs and 200 additional admitted articles. All ten retained pilots are in training. 525 tests pass, both final and legacy selections replay byte-for-byte, and all 1,313 original/prior checkpoint files checked remain unchanged. Training admission/export/model results remain zero; reuse, independent reference review and actual model qualification remain open. [Report](evaluations/flood-ner-continuation-400-20261015/README.md), [source/sample folder](evaluations/flood-ner-continuation-400-20261015/bundle_register.json). Captured-version identity/path binding, rendered publication evidence and optimizer resource-status handling were repaired with 17 added regressions; no dependencies, runtime, database, deployment or Git publication. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Stronger NER revision tooling and bounded reviewed pool

Delivered configurable 2017–October 14, 2026 research windows with legacy defaults preserved, source-bound date-only evidence, versioned hard publisher/article/group/label quotas, explicit v3 assembly/validation/export, contextual-pilot validation and bounded source controls. Repaired two truncated GMA extractions into immutable new versions; browser recovery preserves 14 ABS-CBN and one Philstar body. The 300-URL attempt adds 50 reviewed sources: 192 source articles, 639 accepted silver inputs and 629 eligible passages. Current pool quotas fail, so no new 400 selection or partitions are frozen. Forty contextual drafts remain unreviewed. Other captured material still needs review; this is not a global source-infeasibility claim. Original dataset/backup and 496 checked checkpoint files are unchanged; legacy replay is byte-identical. 508 software checks pass, with no admission/export/model/deployment/Git publication. [Report](evaluations/flood-ner-revision-400-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: NER documentation synchronized for branch publication

The pre-push check also records NER provenance JSON as exact-byte Git evidence through .gitattributes, following the existing research-artifact convention. This prevents Windows/Linux checkout line-ending conversion from invalidating recorded source/register/schema hashes. Raw artifacts remain ignored. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Audited all eight authoritative documentation records and preserved the distinction between completed research/tooling/400-sample silver assembly/first qualification diagnostics and pending training admission, scientific references, model loading/training and release. Latest verification remains 455 passing software checks; schema changes are offline annotation contracts, with no SQL model/migration or dependency additions. The original article captures, frozen dataset and 418-file convenience bundle stay local and Git-ignored; code, source-linked metadata and reports are prepared for the developer-authorized roi-branch commit/push. Production deployment is separate. [Current qualification](evaluations/flood-ner-qualification-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: First NER dataset/model qualification pass

Completed the first qualification pass: verify 132 selected source bindings, all 400 annotations and frozen hashes; report sparse language/label holdouts and publisher confounding; capture four calamanCy metadata revisions; keep source use unresolved. Add the read-only qualify-cohort command, opt-in tokenizer v3 numeric-dash candidate and exact Unicode-separator JSONL preservation. 455 regressions and byte-identical report replay pass; the frozen corpus/default tokenizer/backup are unchanged. The actual model/resource, source-use and scientific evaluation gates remain open. [Report](evaluations/flood-ner-qualification-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Final dataset grouped for finding and private backup

Created the dedicated ignored `400-sample-dataset-20261014` folder with 400 annotated passages, separate context, all 132 original article captures, 400-row sample/132-row article CSV indexes, reports and file/path manifests. Verified 418 file hashes and exact copied bytes, both CSV totals and 400 records in each JSONL layer. Earlier research files and frozen originals remain intact; no source/label changes, external backup, model training or publication. [Folder record](evaluations/flood-ner-corpus-400-20261014/bundle_register.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Completed NER cohort rechecked; contextual JSONL corrected

Reverified all 142 reviewed sources, all 400 annotation/source bindings, frozen hashes, exact language/partition counts, ten pilot assignments and source-use export refusal. A fresh CLI replay matches all frozen cohort files byte for byte. Found that the auxiliary context-v1 file concatenated pretty-printed JSON objects despite its JSONL extension. Extracted a reusable context writer, wrote context-v2 as exactly 400 independently parseable lines and verified that every object, original character, offset and unreviewed cue is unchanged; preserve context-v1. Added a multiline/Unicode/determinism/overwrite regression. Final run: 425 passed, one existing deprecation warning, 27.46 seconds. The first run inherited an encrypted local auditor setting; explicit isolated settings resolve its 19 failures without production changes. No new labels, human verification, training admission or model results. [Review](evaluations/flood-ner-corpus-400-20261014/followup_review.json). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: 400-sample AI NER research cohort assembled

Reviewed 561 location annotation records from 142 articles and selected 400 distinct, complete silver records from 132 articles with exact 200/200 language and 280/60/60 partition counts. Publishers are GMA 193, RMN 194 and ABS-CBN 13. Retain ten pilots in training; exclude two unresolved originals. Preserve 1,374 source-exact place spans, separate contextual views, raw names/parents, original source metadata and the original 100-register. Add configurable collection counts, separate passage language, constrained grouped cohort assembly and tokenizer v2 delimiter repair using existing dependencies. All 142 source/hash/publication checks pass; CLI replay is byte-identical; 424 software regressions pass. Research-only reuse/admission blocks actual DocBin export. Publisher/language confounding, language/label independence, exact incident grouping and missing address/taxonomy slices remain explicit. No model training, runtime/SQL/dependency/Google-document change or deployment. [Report](evaluations/flood-ner-corpus-400-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Developer-authorized AI NER annotation pilot and explicit location export profile

The final offline regression run passes 400 checks; these are software tests, not training samples. All 1,204 checked local documentation links resolve. The task plan and Decision 30 record the 400-total/280–60–60 target, delegated AI method and separate location/context profiles. [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer delegated annotation work to Codex. Selected twelve source-backed contiguous passages (six English/six Taglish) and annotated 116 location spans with raw source spelling and supported parent mentions. Ten location-only records pass same-teacher source review; two compressed-road cases retain incomplete/unresolved status. Preserve actual AI teacher/reviewer provenance as silver, with zero human/gold claims. Paired rich drafts retain 41 depth/47 time spans, 95 fact nodes and three relationships without claiming complete contextual/severity labels or doubling the sample count. Added backward-compatible rich/default and explicit six-place-label export profiles, profile/vocabulary/schema-hash manifests and wrong-profile rejection. Both actual JSONL layers validate, and research-only pilot export writes no dataset because admission/groups/splits remain unresolved. Final regression evidence is in the [pilot report](evaluations/flood-ner-ai-pilot-20261014/README.md). The 400-total/280–60–60 target remains open; method wording in the supplied paper must reflect AI annotation. No source edits, training, model install, runtime/API/UI/SQL/dependency/operational-data change, Google document modification, commit/push or deployment. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Full-body editorial review and research-paper dataset alignment

Read the developer-supplied LANES_Original without editing it and resolved the requirement to 400 total manually annotated English/Taglish samples partitioned 280 training / 60 validation / 60 testing. Primary NER recognizes locations; severity mapping is separate, and the document places methodology/results/conclusions in Chapters II/III/IV. Inspected all 100 complete frozen news bodies and recorded explicit exclusions, caption/post/measurement/scope notes and passage languages in a separate editorial contract/CLI. Preserved 113 contiguous context blocks (English 45, Taglish 33, Tagalog 34, unknown 1), with 78 language-compatible blocks and 22 sibling-context holds. Restored numbered-locality context, identified five RMN language misclassifications and related-story pollution, retained all original sources/register/queues, and shortlisted 12 sources for the research-team manual pilot. No AI review is reported as manual ground truth; labels/admission/splits remain zero. Final verification is linked in the [editorial report](evaluations/flood-ner-editorial-20261014/README.md). Source use, group freezing, manual annotation, coverage growth and a qualified location-only export/model profile remain pending. No runtime/API/UI/schema/dependency/operational-data change, training, deployment, commit or push. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Pilot readiness audited; preparation gate remains open

Revalidated all 100 draft windows/eight policy hashes and found additional candidate-contract gaps. Bound candidate/article identities to source/version/bounds, require unresolved review/provenance holds, reject empty cue roles and carry existing source-review notes/measurement ambiguity into the queue. Corrected review-queue-v3 preserves all original source/text/hash/boundary identities and earlier queues; 378 checks pass in 25.24s. Explicit diagnostics identify nine interface-text windows, one possible caption, 43 truncated-source windows, two omitted numbered-locality cues and one crop-height ambiguity; these are review signals, not model accuracy. All passage languages, 37 event buckets and source reuse admission remain unresolved. No pilot labels/training or phase advancement, operational writes, dependency/schema/runtime changes, deployment or commit/push. [Readiness decision](evaluations/flood-ner-readiness-review-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Initial pilot source-readiness packet and passage-review queue prepared

After the developer authorized proceeding, prepared 100 contiguous source-exact draft passage windows from the reviewed article register, 37 provisional event buckets, five publisher-use assessments and eight hashed primary-policy snapshots. A separate candidate schema/prepare-pilot command preserves source text, offsets, cue hashes and explicit review/admission holds; raw candidates stay ignored and cannot be passed as accepted training annotations. Article-level 64/33/3 language tags are retained, while all passage languages remain unknown pending review. Reuse evidence does not establish training/model/data redistribution permission; no source metadata was promoted. The expanded suite passes 371 checks in 23.73s. The queue inherits coverage imbalance and retains two legacy capture gaps; group/language/bounds/reuse and missing-case review remain open. No labels, split assignments, model selection/training, operational writes, dependency/schema changes, deployment, commit or push. [Readiness evidence](evaluations/flood-ner-readiness-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Completed NER groundwork and historical-news collection audited

Revalidated all 100 frozen article records, reproduced 98 bodies from their actual saved capture recipes, verified all 20 research-case pointers and 36 supporting hashes, compared JSON Schema to the current contract and rechecked the PSGC/OSM Sitio Seis candidate. A stratified 22-page live check corroborates every publication day; Philstar AMP's epoch JSON-LD conflict is retained alongside its matching explicit article-header datetime. Found and corrected offline canonical/provenance spoofing, malformed-review crashes, CRLF normalization, URL-alias split leakage, provisional export groups and repeated/language-colliding Wikipedia revision handling. The full focused suite passes 362 checks in 26.00s; original 100-register bytes remain unchanged. Corrected documentation implying a commit. Source reuse/grouping/language/semantic review and coverage balance remain open; two original fixture HTML/retrieval gaps remain recorded. No labels, model installation/training, production changes, operational writes, commit/push or deployment. [Audit evidence](evaluations/flood-ner-review-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Historical flood-news research expanded to 100 reviewed articles

Retained 17 qualifying earlier reports and added 83 distinct Philippine flood-news articles within January 2022–October 14, 2026. Frozen register counts 22/21/23/18/16 by year; publishers are GMA 88, ABS-CBN 5, RMN 5, Philstar 1 and Daily Tribune 1. Article-level English/Tagalog/Taglish counts are 64/33/3. Preserved bodies/date evidence/hashes, canonical/revision identities, reviewer decisions, failures/exclusions and provisional split groups; separate inventory holds 30 official bulletins, one directory and five Wikipedia revisions with attribution/license metadata. Offline tooling handles JSON-LD body HTML, rendered ABS-CBN snapshots, date boundaries, immutable versions and verifiable reviewed registers. All 338 focused checks pass in 53.18s and the real register passes file/evidence verification. Raw new bodies remain ignored. Publisher/language imbalance, number/address/shared-fact slices, licensing and grouping remain explicit preparation gaps. All 100 are research-only; no pilot labels, model installation/training, runtime/schema changes, operational writes or deployment in this expansion. [Measured deliverables](evaluations/flood-news-corpus-100-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Offline NER groundwork delivered and temporal gap repaired locally

Delivered source inventory/capture, 54 research-only original-text captures, a 20-case source-linked research matrix, the v1 annotation guide/JSON Schema, strict validation, parent-scoped number/PSGC/OSM inspection and deterministic reviewed DocBin export. Source bodies/artifacts stay ignored and excluded from Docker. After the developer authorized continuing with gaps, bounded inherited narrative clocks at unsupported paragraph boundaries while preserving existing city-led continuations, explicit/list clocks and source/chronology guards; extraction/durable identities advance to v1.8/v21 without rewriting saved history. All 301 focused checks pass in 25.65s under isolated source-mode test configuration and in-memory fixtures. No pilot labels/model training, dependency/schema/API/UI changes, shared data writes, expiry changes or deployment. [Evidence and remaining admission/coverage work](evaluations/flood-ner-milestone1-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Number and address research scope broadened before NER implementation

Expanded the [NER research gate](plans/lanes-ner-training-plan.md#philippine-numbers-locality-designators-and-compound-addresses) and task plan beyond the illustrative 4/6 cases to number families, language/spelling variants, sitio/purok/block and other designators, abbreviations, Roman numerals, suffixes, leading zeros and combined address components. Code inspection and constructed local probes confirm existing compound-number handling and gaps for Blk., Prk., Lot and Roman-number Phase examples. Added official address references and a source-linked coverage-matrix requirement; broader research, parser changes and training remain pending. Documentation only; no runtime or operational-data changes. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: NER plan aligned with existing PSGC and OSM location services

Traced captured-news extraction through PSGC administrative resolution and OSM road placement/locality anchors. Verified the bundled catalog loads with 17 cities, 66,129 complete named ways and 1,374 locality points, including Sitio Sais/Sitio 6 in Malabon with Catmon quarter context. Existing geographic hierarchy, number-variant and locality-anchor tests pass: 163 in 27.99s. Updated the [NER plan](plans/lanes-ner-training-plan.md#verified-location-integration-and-ner-alignment) and tasks to reuse these services, preserve source wording and parent uncertainty, include local-area annotations, and evaluate mention recognition separately from identity and placement. This was local code/asset verification and documentation alignment; no trained NER, runtime change, operational database write or live/cloud verification is claimed. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: NER lifecycle plan extended through production operation

Extended the [NER roadmap](plans/lanes-ner-training-plan.md) and active tasks through proposed measurable acceptance, reproducible model/image packaging, staged Google Cloud deployment, coordinated rollback, natural Scheduler verification, production monitoring/operator recovery and controlled offline retraining. Recorded the in-repository training/runtime layout. Accuracy/resource targets and the 24-hour soak are proposals to qualify; no metrics, model, deployment or operational readiness are claimed. Existing weather/experimental exceptions and shared-data/expiry boundaries remain intact. Documentation only; all execution gates remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: NER research and training roadmap documented

Recorded the [spaCy NER research and training proposal](plans/lanes-ner-training-plan.md) and ordered tasks. Further research on shared depth/time attribution and flood time roles is the first gate. The plan preserves existing contextual rules, production source checks, Weather Insights with proposed Gemini → OpenRouter fallback, and separate ChatGPT/MCP experiments. AI-assisted training labels are proposed silver data, not human-verified ground truth. This is a documentation milestone only: no application, dependency, configuration, database, annotation, trained model or deployment change. Research, implementation and model qualification remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: Restore immediate community sharing for flood reports

Explicitly shared pending reports now appear in Community Feed and public post detail immediately, with a responsive Awaiting review label. Official map-zone approval stays separate. Report, owner notification and requested post save together; share failures roll back instead of silently succeeding. Submission invalidates Feed/My Posts caches. Private, rejected, archived, hidden and deleted content remains excluded. No schema, migration or dependency changes. Verification is recorded in the [bug log](others/bug-log.md#resolved-locally-flood-report-community-sharing-waited-for-map-approval). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 14: PR #137 conflicts resolved against main

Integrated main 5c6da28 into roi-branch. All five conflicts were documentation overlaps with PR #136's earlier pre-deployment snapshot; retained the later verified rollout, automatic Scheduler evidence, completed task statuses and known Feed issues. Existing cadence source matches main; connected replay and Feed edits are preserved. This synchronization changes no application code, schema, dependencies, records or expiry setting. [PR #137](https://github.com/pu-roi/LANES/pull/137). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: roi-branch documentation and publication preparation

Synchronized the nine core/index records with deployed main 5c6da28 / PR #136, corrected the connected-reconstruction storage exception and retained operator-disabled expiry for video recording. Branch save includes deployed cadence repairs, the authorized two-date reconstruction extension and existing Community Feed edits. Pre-push verification passes 292 backend checks (285 release + seven reconstruction guards) and TypeScript. Feed lint remains blocked by three pre-existing state-in-effect errors and three warnings; no clean frontend-release claim. No new dependencies, models or migrations. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Quarter-hour cadence repair deployed

Main 5c6da28 / PR #136 passes 285 Linux release checks, migrations and a real worker before API promotion. API/news/expiry share the new main image; automatic frontend rollout 004 serves 100%. Natural 11:30 PM delivery collects successfully after the prior 11:15 PM cycle, records zero inference and sets the next risk due slot to 11:45 PM. Shared readers retain six active zones. Known-operation/overlap protections and uncertain-date handling remain; expiry stays off for video presentation. [Evidence](evaluations/news-autonomy-fixes-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13 late evening: Autonomous operation audit

Observed a fresh automatic 10:15 PM Scheduler delivery and completed source_rules worker, compared real local/live public and authenticated APIs, and passed 99 focused existing checks. No manual worker/code/settings action. Main 5febb73 / PR #135 serves the same news pipeline. Identified quarter-hour jitter/collector-start cadence defect (actual risk cycles approximately 30 minutes), PAGASA parse uncertainty, incomplete collection/boundary coverage, and intentionally disabled shared-demo expiry. The supplied administrator credential also needs operator replacement. These issues are recorded as open, not resolved. [Audit](evaluations/news-autonomy-audit-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13 evening: Same-system historical presentation

Extended the approved connected reconstruction command for both preserved dates, exact database confirmation, credit-free/runtime/expiry preconditions and retention of both results. Seven focused guard/provenance tests pass. Real collector/NLP/source-rules/publication/footprint services generate five estimated news zones (59–63); the existing citizen zone remains active. Same Cloud SQL records appear in local 3000/8000, actual authenticated Spatial Operations and navlanes.live APIs. Original source/observation/deadline dates are intact; no additional runtime instance or schema change. The operator disabled expiry; shared live users see this historical presentation data. [Evidence and remaining withheld claims](evaluations/news-connected-demo-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest verified production release:** Main 5c6da28 / PR #136 passed 285 Linux release checks, existing migrations and the release worker. Matching API/news/expiry and frontend rollouts are live. The natural 11:30 PM Scheduler delivery completed collection with zero LLM requests; shared 15/30/60-minute due slots fix the skipped risk tick. Automatic expiry remains disabled at the operator's request for the historical video demonstration. [Deployment evidence](evaluations/news-autonomy-fixes-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Autonomous news release:** Focused source-mode backend is already deployed; current feature branch records the runtime plus regression/replay tools and responsive diagnostics without MCP dependency changes. Complete timeline/API acceptance and reproducible main deployment are the current release gates. [Evidence](evaluations/news-source-validation-20261013/README.md).

**Earlier PR #134 rollout checkpoint:** PR #134 merged the focused source-mode implementation into main at 420b38f, excluding MCP/framework upgrades. Complete September 24/9 scheduled-worker/public-API timelines pass with zero inference, initial 19-inch and later 10-inch Santo Domingo publication, duplicate safety and final expiry. Fresh coordinated Cloud Build and frontend rollout are currently running. [Evidence](evaluations/news-source-validation-20261013/README.md).

**October 13 follow-up:** Deployed measurement-first source policy v2, restored saved evidence without decorative source bullets/composed ellipses, and exercised the production scheduled-worker entry point on captured historical news. It produces 27 alerts/seven zones including Santo Domingo at 19 inches, with no inference, repeat duplication or expiry failure. Linux release checks: 275 passed; actual map checks: desktop/mobile passed. Production API/news/expiry share the v2 image; worker execution succeeds. [Evidence](evaluations/news-source-validation-20261013/README.md#measurement-precedence-and-scheduled-worker-follow-up).

## October 13: Credit-free NLP news and focused backend release

Implemented source_rules validation with immutable occurrence/fact/span checks and no inference/quota calls. Normal local collector-to-zone replay creates 26 alerts and six estimated road zones from 31 evaluations, without duplicates; expiry passes. 270 Linux checks, one native PostGIS scenario and four desktop/mobile checks pass; TypeScript/scoped lint pass. Fixed nullable-evidence publication and misleading list excerpts. API/news/expiry run the tested focused image; authenticated controller dispatch/worker completion and zero model requests are observed. Production JWT now requires a private Secret Manager binding; development bootstrap stays local and old exposed tags are retired. Encrypted local provider selection is updated, original provider keys/history preserved. Main Git and optional frontend diagnostics rollout remain separate. [Acceptance](evaluations/news-source-validation-20261013/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Enable production adaptive news scheduling

The next autonomous 1:30 PM delivery also returned HTTP 200, incremented controller checks to 2 and retained one worker start without duplication. Longer operation/reconciliation and representative quiet/uncertain periods remain pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

Corrected the still-active three-hour direct-job schedule to a quarter-hour OIDC controller check. Configured the existing API and narrow job/operation permissions; configuration revision lanes-api-00081-n4x uses the same main image. 61 policy/auth/dispatch tests pass; one authentic Scheduler delivery returns HTTP 200, saves a 15-minute risk decision and starts the existing news worker, which completes successfully. No MCP/ChatGPT rollout, schema change or extra container. [Evidence](evaluations/news-adaptive-scheduler-release-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Senior-planner publication audit

Prepared the developer-authorized roi-branch bundle: disabled five-tool MCP review, shared dependency candidate, Windows protected ChatGPT sign-in, strict bounded inference runner and test/docs records. Real plan authorization is proved; live auditing fails evidence acceptance at 3/5. Original providers/history are preserved. The separate [MCP runbook](guides/lanes-mcp-pilot-runtime.md) includes prerequisites, enabled-only local startup and baseline rollback. No cloud deployment or additional provider request. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Real ChatGPT plan connection and captured-news inference

User completed authorization; verified current plan scopes and account-specific model catalog (HTTP 200). Added bounded Responses streaming qualification and passed 23 offline transport/budget/evidence checks. Three actual gpt-6.1-sol requests reached HTTP 200/completion; first two failed local parsing. Fixed thin completion handling via finalized item events. The eight-claim result parses and strictly validates, but seven claims lack confirmed time and the original Santo Domingo half-knee/knee conflict is rejected. Stop at 3/5; no qualified positive case, publication, worker replacement or deployment. [Evidence](evaluations/chatgpt-news-live-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Repair local ChatGPT token-pair verification

Found missing access-token input to python-jose ID-token validation; valid at_hash-bearing signed fixture fails before repair and passes afterward. Preserve all identity/permission checks and reject mismatched token pairs. 43 focused tests pass. Launched updated helper on 1457; exact real discarded-token claim and actual account connection remain unverified. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Diagnose real ChatGPT callback rejection

Added fixed validation-stage codes to the local page and last_error_code status, preserving strict checks and no unvalidated credential saving. 35 focused offline tests pass. Started the updated helper on port 1456 because automatic review blocked stopping/restarting the old process. Exact actual identity/permission failure remains unproved until one fresh user attempt. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Repair local ChatGPT button request

Reproduced the developer-reported HTTP 403: the page referrer policy made Chrome send Origin: null. Corrected only the landing-page policy, retaining strict local/CSRF checks and private callbacks. Added actual button-origin checks in desktop/mobile Chrome plus backend form/callback regression; restarted the helper for another real user sign-in attempt. No inference, provider or production change. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Local ChatGPT plan sign-in prepared

Implemented a loopback Windows sign-in helper with PKCE, verified identity/permissions, one-use callback and DPAPI storage outside Git. 88 combined offline authentication/MCP tests and two desktop/mobile Chromium page checks pass. Actual ChatGPT account authorization and inference remain pending; no automatic worker integration, provider change, publication or deployment. Shared dependency/MCP implementation is a candidate with remaining Linux/PostGIS gates. [Results](evaluations/chatgpt-plan-signin-20261013.md), [startup](guides/chatgpt-plan-local-signin.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: FastMCP selection research and measured compatibility

Follow-up official-doc/release research recommends FastMCP 4.1.0 on existing Python 3.12 in a separate gateway using qualified MCP SDK 2.3.0. Real pip dry runs prove Pydantic 2.7.4 and FastAPI 0.111.0/Starlette <0.38 cannot share its current dependencies, while isolated resolution succeeds (68 Windows distributions). All eighteen inspected source hashes and installed LANES versions remain unchanged; no installation, server test, model request, database operation or deployment. Auth/account binding, explicit tool allowlist and target Linux runtime remain implementation gates. [MCP library comparison](research/lanes-mcp-library-selection-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: MCP repository review and additive pilot design

Completed official-doc and code research for ChatGPT-assisted captured-news review. Existing read APIs/source snapshots can support a gateway; external audit submission is absent, Python MCP SDK Pydantic requirements conflict with the backend pin, remote MCP OAuth is missing, and worker lease/policy gates prevent casual chat-result insertion. A phased separate-gateway/read-only/strict-preview plan preserves provider code/configuration and all publication/history gates. Research/documentation only: zero provider POSTs, database queries/writes, installs or deployments. [Findings](research/lanes-mcp-chatgpt-feasibility-20261013.md), [plan](plans/lanes-mcp-chatgpt-review.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Gemini quota isolation and Groq captured-evidence trials

Official-doc research and bounded trials identify Gemini 20/day exhaustion. Groq strict canonical output passes eight original claims, the separate 10-inch afternoon single and conservative negation after explicit place-identity instructions. Account output/minute cap prevents treating eight-claim success as repeatable throughput. 12/12 total POSTs used; 215 offline tests pass. No active-provider/cloud/source changes. [Provider trial results](evaluations/gemini-groq-live-trials-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Resolve PR #133 conflicts against main

PR #133 reported documentation conflicts between roi-branch and main. Main `6340c2a` contains the weather publication through PR #132 and has the exact tree of `680118b`; roi-branch `8e00f8c` already preserves that content plus the news repair. The two shared merge bases (`680118b` and `2cf147b`) explain the crossed documentation history. Merge origin/main into roi-branch; local Git resolves it automatically with **zero file changes**, verified by identical complete tree hashes. Recording this merge makes the current main commit an ancestor of roi-branch and removes the PR conflict blocker. Both original repair heads and the 271 targeted/234 native passing implementation are retained; no re-test or live request is needed for unchanged source. Documentation records this branch synchronization only. The developer-requested codex/gemini-audit-repair ref is deleted locally and remotely; its df16a02 commit and ignored qualification receipts remain preserved. No main commit/PR merge or cloud deployment in this task; live Gemini qualification is still blocked at 3/12. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Combined news and weather repair integration

Gemini news-auditor repair `df16a02` is integrated into roi-branch alongside weather repair `680118b`. Canonical evidence validation/publication gates remain strict. Both Gemini schema and weather settings are retained in `.env.example`; encrypted runtime configuration and existing feed edits are preserved. Live qualification remains blocked at shared 3/12 POSTs; no deployment or additional inference. Documentation conflicts preserve the prior primary records and incoming repair plan/qualification/bug evidence; earlier separate-branch descriptions below describe the pre-integration state. Combined verification passes 271 targeted and 234 fresh native checks plus offline readiness; ten primary files and thirteen incoming implementation/test files preserve exact committed bytes. Results are recorded in [merge acceptance](evaluations/gemini-repair-integration-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: roi-branch publication package

The developer explicitly requested documentation synchronization followed by publication to `roi-branch`. The package includes the verified Gemini weather service/public error and responsive layout repair, prior encrypted runtime configuration/rotation records, schema/quota research, and existing feed summary/sidebar/Local Updates spacing edits. No dependency, SQLAlchemy definition or migration change; plaintext credential scan passes. Earlier verification is 151 backend checks and six responsive weather cases plus TypeScript/scoped weather lint. The separate unqualified auditor branch remains unmerged, 429 blocks live acceptance (shared 3/12), and cloud release is not part of this push. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Public weather error repair and measured Gemini quotas

**October 13 weather/Gemini follow-up (roi-branch, local):** Public weather errors now use a safe message; backend explanations use Gemini with cache/cooldowns and strict output. 151 backend checks and TypeScript/scoped lint pass; six responsive cases pass for desktop/mobile errors, success and missing forecast. Fresh captured-news audit still returns 429 (shared 3/12 POSTs); scheduled worker extracted 11 articles with zero audits, so live Gemini news acceptance remains blocked. Direct issuing-project quota read confirms Flash 5/minute, 20/day; usage/remaining is unknown. Developer-authorized roi-branch publication is prepared; cloud deployment remains pending. [Follow-up verification](evaluations/gemini-weather-followup-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Gemini structured-request research

Reviewed Google documentation and firsthand forum/GitHub reports, inspected the exact schema and current serving/worker images, and ran four bounded synthetic controls without DB writes. The same request succeeds with a minimal schema and fails with the full LANES schema. Two provider-demand 503 results prevent identifying a specific failing constraint. The proposed Gemini wire projection retains strict backend/evidence gates and requires real single/eight-claim qualification before release or historical replay. Research is complete; repair is pending. [Gemini request investigation](research/gemini-news-audit-invalid-argument-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Gemini selected for news auditing

Local/default and existing isolated-preview configuration, the actual API serving revision and news worker use the replacement Gemini key (issuing project number `32816280739`, Secret Manager version 2). The old deployment version is destroyed; the developer confirmed deleting the original issuing key. Basic generation and health pass, resolving the original 402 billing error. The LANES structured audit still returns generic 400 INVALID_ARGUMENT; eight-claim/model and historical activation acceptance remain unverified. Earlier 123 deterministic checks cover unchanged source. [Runtime record](guides/news-gemini-runtime.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Goal status: Implementation complete; remaining live verification skipped by developer.** The developer explicitly chose to skip the remaining OpenRouter-dependent qualification and fresh September 9 target replay because the account allowance is exhausted. Local implementation/manual review and independent verification are complete. Current v11 live qualification and Santo Domingo automatic zone/depth-update acceptance are **skipped and unverified**, not passed. No further provider retries or automatic follow-up are part of this task. The developer subsequently authorized Git publication to `roi-branch`; cloud deployment remains excluded. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Approved closure and roi-branch publication readiness

The developer skipped remaining OpenRouter-dependent acceptance and authorized publication to `roi-branch`. Local implementation/manual review is complete, with 507 final backend/native checks, 46 responsive browser cases across the main run/single-case follow-up, merged TypeScript and scoped news lint. Primary feed/profile edits are preserved; earlier research/replay history survives five documentation conflicts. Existing feed lint findings are unchanged. Root/nested NCR assets now preserve raw Git bytes across Windows/Linux, verified for all nine files. No schema/dependency/cloud deployment changes; automatic Santo Domingo activation/depth-update acceptance stays skipped and unverified. [Publication checks](evaluations/news-reliability-goal-20261012.md#authorized-git-integration-and-publication-checks). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Final-code verification and current preview

Current final-code verification passes **507 combined backend/native checks**. A fresh v20 September 24 normal-worker replay completes five checkpoints/five locations/eleven negative decisions without audits or zones, and unchanged input remains idempotent. Current-code 3004/8004 desktop/mobile preview checks display September 24 first, then preserved v19 September 9 data (33 locations/three ended events/zero active zones). Actual account GET at 01:34 PHT remains 50/50/0; cooldown through 02:04 PHT. V11 live qualification and a fresh eligible Santo Domingo target replay remain pending. [Completion audit](evaluations/news-reliability-goal-20261012.md#final-code-completion-audit-and-latest-isolated-checks). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Conservative construction, allowance preflight and manual review

Current follow-up: v20/corridors-v7 conservative generated-intersection construction passes strict read-only predicates for the three real source claims without source repair. V11 retains exact occurrence/parent evidence and >35% reduction on eight-claim batches, but live qualification remains pending. Actual allowance is 50/50/0; free-model unknown allowance now also defers without audit attempts. Latest focused/native runs pass 161/35 checks. The developer requested and received a [manual chat review](evaluations/news-chat-source-review-20261013.md), separate from automatic approvals. Target activation acceptance remains open; the preserved preview is v19. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 13: Ordered real replay and source-coordinate repair

The default reviewed NCR registry qualifies 1,524 barangays across all seventeen parents, with immutable OSM/COD provenance and 186 explicit exclusions. September 24 completes five checkpoints with delayed-observation admission rejection. The v18 September 9 repeat completes 26 ticks, nine HTTP-200 requests and 33 locations without timeouts, but target text alerts fail containment. Separate tracing identifies inverse-scale roundoff at an original border vertex; a [separate repair](plans/news-source-line-precision-repair.md) preserves original coordinates and strict gates. Ninety-seven geometry and 163 native lifecycle checks pass. The fresh v19 repeat completes all 26 ticks and creates three Sienna/Tatalon zones/events, verified through actual initial/later/final desktop/mobile APIs/map/History. All expire/end; unchanged input repeats no completed audits or records. Santo Domingo's initial 19-inch audit is rejected for wrong occurrence; later 10-inch audit verifies but fails polygon containment. The [remaining acceptance plan](plans/news-audit-and-corridor-followup.md) preserves these blockers. At that v19 checkpoint allowance was 46/50/4, with no new timeout/429. Larger real replays do not establish broad free-model qualification. Prior artifacts and primary Zones 58/59/60 remain unchanged. [Evidence](evaluations/news-reliability-goal-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 12 evening: News reliability goal implementation checkpoint

Implemented bounded request diagnostics, scoped connection reuse, credential/account quota identity, per-model recovery circuits and scheduled request/time budgets with zero-attempt deferrals. Compact eight-claim payloads shrink 39.66%/38.62%. Generalized NCR builder and parent-bound numbered-name handling qualify 692 immutable OSM polygons; a hashed multi-source registry preserves source provenance and old Pasig assets. Twelve real benchmark calls expose Apodex HTTP 400 and a Santo abbreviation evidence defect; after repair, two Dots/eight requests verify all sixteen target claims in about nineteen seconds each. Native/targeted verification and actual asset checks are recorded separately, without claiming all later changes were included in earlier counts. Geography gaps, preview/mobile verification and fresh zone/history replay acceptance remain open. [Evidence](evaluations/news-reliability-goal-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 12: News audit and placement repair research

Completed implementation/community/official-source research and measured three saved batches without new inference/database mutations. Eight-claim user payloads are 19,860/25,069 UTF-8 bytes versus 1,999/2,710-byte articles; preparation takes milliseconds. Confirmed nonstreaming provider request, opaque shared timeout classification, random free-model attribution gap and twenty Pasig-only news polygons. Saved the [diagnostic/compact-batch/free-model/coverage repair proposal](research/news-audit-reliability-20261012.md), distinguishing demonstrated blockers from unproven delay causes. Product repairs, selected-model accuracy/reliability, new geographic assets and actual zone/history/depth-update acceptance remain pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 12 evening: Historical news retry with restored provider quota

Completed September 24–25's five checkpoints first, then September 9's 26 half-hour ticks in fresh guarded local databases. Existing migrations reach head; six target/output refusal checks and duplicate-checkpoint checks pass. September 24 saves five locations rejected by original admission; September 9 retains four versions/runs and 33 cards. Twenty actual batch requests produce four independently verified text alerts, but three missing barangay-boundary outcomes and one ungrounded underloop prevent zones/history. Both 19-inch/10-inch observations expire after actual audit failures; positive zone-update acceptance remains open. Final provider GET is 20/50/30, distinguishing this run from earlier exhaustion. Browser/preview findings are recorded without claiming complete visual acceptance. Original Zones 58/59/60, source hashes and port-3000 configuration remain preserved; application source/schema/dependencies and cloud release are unchanged. [Full retry record](evaluations/news-retry-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 12: Batch audit documentation and publication checkpoint

Audited the eight core records against the batch/quota implementation and prior verification. Updated the plan, master catalog, task/progress and evaluation to reflect the developer's subsequent request to publish on `roi-branch`. Existing migrations and runtime manifests are unchanged; retained acceptance is 492 offline, 226 native PostgreSQL and 14 desktop/mobile checks. Real provider plotting/depth/history acceptance and the coordinated cloud rollout remain separate open gates. [Publication audit](evaluations/news-batch-audit-20261012/README.md#planner-and-publication-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 12: Batch auditing and quota diagnostics verified locally

Implemented eight eligible claims per same-version/policy request, separate strict evidence results, zero-attempt quota deferrals, bounded safe failure JSON and persistent cooldowns in existing settings storage. Database ownership/leases survive interruptions; cooldown-only work does not hot-launch the worker. Existing Overview diagnostics expose request/claim/quota counts and deadlines on desktop/mobile. 492 offline, 226 native PostgreSQL and 14 browser checks pass, plus TypeScript/scoped lint. Original 60/15/30-minute policy, source facts, location labels, SQL schemas and dependencies remain unchanged. [Verification and plan](evaluations/news-batch-audit-20261012/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Fresh normal-worker replays retain 33 September 9 and five September 24 locations. Real OpenRouter 52/50/0 prevents audit dispatch; zero zones/history are recorded, and the original 19-inch/10-inch comparison cannot reach zone update logic. The isolated port-3004/8004 preview is available without replacing `lanes_plotting_20261011`. Positive real plotting acceptance and a coordinated cloud rollout remain open. Git publication was excluded from the original implementation task and subsequently authorized in the checkpoint above. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 12: News collection/extraction repairs verified locally

Follow-up provider inspection confirms the current daily allowance is exhausted: 52 requests used, limit 50, zero remaining. The existing audit probe returns HTTP 429. Failed evaluation persistence also discards the auditor's returned HTTP status, preventing exact diagnosis of four earlier generic HTTP failures. This investigation changes no audit behavior/model/schema; successful plotting verification remains pending real auditor availability. [Evidence](evaluations/news-scheduled-historical-workflow-20261012.md#follow-up-current-provider-quota-and-diagnostic-loss). [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer authorized article-refresh and heading/locality fixes. Existing capture timestamps bound periodic body checks to thirty minutes and twenty oldest captures per cycle across reviewed publishers, including unchanged/empty feeds. Scoped city/time/depth headings survive numbered addresses while per-road facts and original evidence offsets remain intact; v17 preserves previous extraction history. 271 focused checks pass. Final continuous replay retains all 26 QC sites and recaptures the later GMA body into a fourth immutable article version; provider HTTP 429/errors prevent zones/history. Successful operational-zone refresh remains unverified; no cloud release, schema or dependency change. [Evidence](evaluations/news-scheduled-historical-workflow-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Before these repairs, the real scheduled worker completed the September 24–25 sample-source scenario without manual stage processing: the two GMA advisories were local news; Tribune produced five road locations but its original observations exceeded twelve-hour admission, so no zones/history events were created. September 9 captured HTML processing finished with 33 road locations, provider failures/retries and zero zones/events. The indexed-text checkpoint comparison also reproduced stale-body capture and missing heading context; 26 continuous half-hour worker ticks reproduced those failures. Earlier indexed GMA text supplies a depth comparison but lacks original HTML and remains separately qualified. Full workflow acceptance is pending. [Evidence](evaluations/news-scheduled-historical-workflow-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 12: Local plotting connection restored

- Restore backend 8003 for the existing `lanes_plotting_20261011` snapshot and point the normal port-3000 frontend at it through an ignored development override. Add the explicit local build task and reusable guarded private startup helpers. Both API paths return News Zones 58/59/60 Active, five news locations and searchable history for all three; desktop/mobile History lists show the saved events. Repeating startup preserves the same processes/records. Cloud records, application labels/source, schemas and expiry settings are unchanged. [Local startup instructions](guides/local-news-replay.md#october-12-restore-the-same-local-map-and-history). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 12: PR #128 merge-base discrepancy corrected

- GitHub uses an older base (`0400eef`) from the two competing merge bases after Jace integration, reproducing twelve conflicts despite the clean local automatic preview. Synchronize current main history into `roi-branch`; the automatic merge preserves the exact application/document tree before adding this audit. Correct the premature GitHub-readiness claim and require a live PR metadata check after push. Source, dependencies and schemas are unchanged; previous acceptance remains applicable. [Cause and recovery](evaluations/roi-team-integration-20261012.md#conflict-resolution-and-retained-behavior). The developer retains the final merge into main. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 12: Teammate updates integrated into Roi branch

- Push News Intelligence tabs first as `c32646d`; integrate Jace's moderation/map, owner notifications/ownership, daily UTC statistics and Community filter/visibility updates. Chris `622173d` is already included. Preserve both authors' records across eight documentation conflicts and remap Jace's reused BUG-146/147/148 to BUG-152/151/150. Screenshot review finds and repairs BUG-153 (mobile sidebar over report dialog) with the existing body portal/modal layer and a foreground regression. Fresh dependency installation, migration to existing head on disposable PostGIS, 133 backend checks, 103 distinct browser cases across combined/final responsive runs, TypeScript and scoped lint pass. The final rerun has 46 passes/two fixture skips; all three original skips are intentional. [Acceptance and screenshots](evaluations/roi-team-integration-20261012.md). The developer retains the manual merge to `main`; cloud release remains separate. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: News Intelligence organized into two views

- Overview summarizes worker status, next collection, pipeline switches, recent counts and weather health using existing admin components. Flooded Areas retains reported-location cards, search/filtering and source inspection, with state preserved across tabs. Advisory clocks, coverage and run diagnostics remain expandable; source/dispatch issues remain visible in the summary. Shared Tabs opts into accessible panels and keyboard navigation. **37 browser checks pass (three intentional skips)** with TypeScript/scoped lint and desktop/mobile screenshot review. [Local acceptance](evaluations/news-intelligence-tabs-20261011/README.md); cloud release is separate. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Adaptive scheduling documentation and publication audit

- Audit all eight core records and expand existing Decision 25 with the controller rationale, conservative weather policy, exact machine identity, durable uncertainty handling, legacy compatibility and pending cloud activation/rollback. Keep the completed 146 backend/native and 43 browser checks separate from deployment or flood-prediction accuracy. No source/dependency/schema changes in this continuation; the developer requests committing/pushing all current work to `roi-branch`. [Publication audit](evaluations/news-weather-scheduling-20261011/README.md#planner-and-publication-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Adaptive news scheduling accepted locally

- Implement sampled Open-Meteo/PAGASA scheduling, positive-risk precedence, 30-minute freshness and 60-minute cooldown; 60/15/30-minute policy is shared by worker/controller. Add Google OIDC machine endpoint, separate existing-setting JSON state, PostgreSQL locks, dispatch reservations and execution reconciliation. Preserve paused-collection processing/maintenance and independent expiry. Remove interval editing, preserve stored legacy values and extend desktop/mobile automation health with source clocks, coverage, due reason and failures. 146 backend/native checks, 28 adaptive/settings browser checks and 15 news regressions pass (one intended desktop skip), with TypeScript/scoped lint and actual read-only provider probes. No new package/model/migration. Cloud inspection confirms the three-hour trigger remains unchanged; matching deployment, unattended acceptance and savings measurement are separate gates. [Evidence](evaluations/news-weather-scheduling-20261011/README.md), [rollout](guides/news-weather-scheduling-rollout.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Moderation, notification and homepage publication checkpoint

- Complete authoritative report details and status-based map focus; retain one Spatial Location map action. Notify report owners when entering the existing pending queue and receiving approval, preserving rejection reasons/post warnings. Protect notification read ownership and report-detail hydration. Count active zones created today in UTC on the homepage and refresh through existing polling/SSE. Audit all eight core records and synchronize dependency/lock state for the requested `jace-branch` push. Local acceptance includes 51 backend and the final 30 feed/home browser checks, with earlier 18 map and 18 notification checks recorded separately. No model/migration change or production deployment. [Audit and limitations](evaluations/jace-moderation-feed-publication-20261011.md). Jace H. Bellen (Git author Jace; jace-branch), with Codex.

### October 11: Community feed filtering implemented locally

- Extend the existing feed API with validated sort/date/status/severity/radius parameters applied before pagination. Default to newest publication and All Time; retain UTC Today and existing Nearby location logic. Shared desktop/mobile controls persist through refresh and tabs, support Reset Filters and 20-post pagination, and protect cache rollback when a pending vote finishes after filters change. Public readers now exclude linked pending/rejected/private/archived reports, preserving owned My Posts access. [Local acceptance](evaluations/community-feed-filters-20261011.md); no schema/dependency/workflow changes or deployment. Jace H. Bellen (Git author Jace; jace-branch), with Codex.

### October 11: Three news flood zones and searchable history verified locally

- Repair shared narrative clocks, supported short road/crossing aliases, independently validated provider evidence references and missing news event-location records. Add researched numbered-locality normalization and 1,374 source-backed OSM place points; match unique locality names to nearby bounded road candidates before existing NOAH/grade/ambiguity and automatic publication checks. Preserve original labels, raw evidence, depth/access and temporal gates; maintain legacy claim hashes and version new runs as v16. The local September scenario returns Boni Zone/Event 58, Quirino 59 and newly automatic Gov. Pascual 60 on public APIs and authenticated history searches; the actual map shows Gov. Pascual Active with the existing estimated-corridor label. Duplicate worker activation is zero. 493 focused and 163 native PostGIS tests pass; existing migrations upgrade to head, and a strengthened source-locality native test passes separately. Audit all eight core records and affected plans/runbook for the requested `roi-branch` push. No SQL schema, dependency or frontend changes. Clearance-only prior-event matching, Aurora audit disagreement, fresh v16 collection/evaluation and shared/cloud release remain open. [Evidence and publication audit](evaluations/news-shared-context-and-history-20261011.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Runtime expectations and remaining accuracy gates documented

- Add a [system-testing handoff](guides/pasig-recession-observation-collection.md#what-to-expect-when-running-the-system) covering approved-zone eligibility, shared-location inference, saved calculations, original clocks, unavailable/fixed fallback and scheduled expiry as Unconfirmed. Explain that p90 drives operational expiry, pooled estimates ignore depth and the cross-location depth response remains weak. Audit the eight core records, retain existing Decisions 26/27 and BUG-145 accuracy status, and correct stale current-versus-historical hosted-release wording. No source, model, dependency, schema or deployment changes; prior engineering/migration and hosted desktop/mobile acceptance remain applicable. Real outcomes and calibrated depth-sensitive prediction remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Hosted saved-forecast UI released and verified

- Resume the remaining hosted UI gate at the developer's request. App Hosting rollout 005 from `e150fea` serves 100%; Cloud Build `60d53a00-4dcb-40da-8bd5-fe8fb79b5ab2` succeeds. Six actual desktop/mobile Info flows plus six expanded-calculation checks pass for #50/#37/#36. Shared v3 API and scheduled expiry stay accepted. Four live feed widths also verify the pushed navigation-spacing preview, news HTTP 200 and no overflow. No application source, dependency, schema, model or policy changes. Developer confirms no additional government flood-history files; prepare precise acquisition fields and record FOI lead limitations. Accuracy remains open. [Acceptance](evaluations/pasig-subsidence-v3-acceptance-20261011.md#hosted-ui-continuation--october-11-425-pm-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Additional official outcome-source screening

- Check public Pasig/MMDA/NDRRMC evidence for independent wet-to-clearance observations. Confirm the August 30 city bulletin is already represented by the existing shared outcome; the Quezon City MMDA example uses a different reference clock and lacks numeric initial depth, while the NDRRMC lead remains unfetched. No new qualified event, refit, admission or deployment. Preserve sources and acquisition limits in the [research continuation](research/pasig-flood-recession-depth-and-availability-20261011.md#official-source-screening-continuation--october-11-413-pm-pht). Real reviewed outcomes remain the scientific gate. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Pasig documentation and pre-push audit

- Synchronize the eight core records and documentation catalog for the requested `roi-branch` publication. Fresh pre-push checks pass: 166 native PostGIS/backend tests with the existing Alembic chain upgraded to head, 88 model/dataset tests, TypeScript and scoped component lint. Preserve the earlier 66 responsive and six actual local Info workflow checks without counting them as new runs. No dependency, SQL model or migration changes. Operational repairs are delivered; real reviewed outcomes and scientific accuracy remain open, and hosted forecast UI release remains separate. [Audit](evaluations/pasig-subsidence-v3-acceptance-20261011.md#planner-and-pre-push-audit--october-11-408-pm-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Reproducible recession-outcome qualification delivered locally

- Add an offline builder for complete existing staff follow-up exports and explicit episode reviews. Derive same-section interval/right-censored bounds with frozen numeric depth, real/test exclusions, independent source reviews, scope/clock/recurrence guards, simulated hindcast versus actual forecast provenance and immutable byte/code hashes. No DB write, training admission, runtime model replacement or new deployment. 26 tests pass, including mutation-during-build lineage and sanitized-output checks. Actual authorized shared export has three pending follow-ups across reports #26/#29, no numeric depths and zero eligible episode candidates. Real observed outcomes and calibrated prediction improvement remain open; source/record-ID clarification is pending. [Evidence and reproducible contract](evaluations/pasig-recession-collection-readiness-20261011/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Pasig expiry v3 and geometry-derived locality accepted

- Repair transient null caching without moving original forecast clocks; reconcile submitted locality to final validated geometry through the reviewed COD/PSGC catalog and auditable, clock-preserving corrections. #36 recovers pooled ML; reports #29/#30 now resolve to Manggahan and #50 receives cross-location ML. When ML abstains and no timer exists, use the existing configured retention deadline from zone activation, separately labelled from subsidence. #47/#49/#54/#55/#56 become Unconfirmed, with pending claims unreviewed. Shared API revision `lanes-api-subsidence-v3-20261011-1350` serves 100%, both cloud jobs use the matching image, and minute expiry succeeds. Repeatable-read acceptance finds 17 active Pasig zones, all with ML deadlines, zero unscheduled. Local Info shows the saved chosen forecast/calculation; 166 native backend/database checks, 62 distinct model checks across runs, 66 responsive scenarios and six actual local desktop/mobile workflows pass. Migration head and dependencies unchanged; hosted frontend remains rollout 004. [Acceptance and release](evaluations/pasig-subsidence-v3-acceptance-20261011.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Implement and evaluate an optional nondecreasing depth-centre candidate offline. The constraint is inactive, shallow/deep medians remain about 1.5% apart, and none of its forward-time folds qualify. No runtime artifact promotion or demonstrated accuracy gain. Add a [reviewed observation collection guide](guides/pasig-recession-observation-collection.md); manual test reports and administrative expiry cannot become clearance ground truth. Scientific accuracy remains open. [Candidate evidence](evaluations/pasig-depth-shape-candidate-20261011/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Pasig prediction availability and depth research completed

- Read-only connected DB/protected production audit finds 22 active Pasig zones: 15 saved ML forecasts and seven unscheduled null fallbacks. Confirm #36 caches a transient early-clock rejection; distinguish pending subsided follow-up, conflicting Rosario/Manggahan records and legacy missing observation audits. Reproduce zero depth effect in the pooled model and only about 1.5% median change from gutter to knee in an unseen-location depth candidate. Three shared historical outcomes and uncalibrated uncertainty limit the scientific model. Save [individual record/numerical evidence](evaluations/pasig-subsidence-availability-audit-20261011.md) and [primary-source research with proposed fixes/model sequence](research/pasig-flood-recession-depth-and-availability-20261011.md). Implementation, evidence correction and validation remain open; no runtime/model/schema/dependency/cloud or flood-record mutation. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Modest navigation width and smaller outer margin

- Undo the unpublished 376-pixel left-panel experiment after developer feedback. Use 280 pixels on large screens (24 more than before), retain 256 pixels on tablets and the existing mobile drawer. Remove the centered 1,600-pixel page cap, place navigation inside a 24-pixel desktop outer gutter, and center the capped 720-pixel feed within its own grid column beside the existing 376-pixel updates panel. Seven actual local widths (1920/1600/1440/1280/1024/768/390) pass, including real news responses, mobile navigation and no horizontal overflow; TypeScript and scoped lint pass. This is a local layout preview; production remains on rollout 004. [Evidence](evaluations/community-local-updates-20261011.md#navigation-spacing-preview--october-11-1249-pm-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: More visible right-panel width increase

- Respond to developer feedback that the first 24-pixel increase was too subtle. Increase the outer sidebar from 344 to 376 pixels and reduce horizontal padding from 24 to 16 pixels, giving cards 344 pixels instead of 296 (48 additional usable pixels). Actual local desktop widths 1920/1440/1280 and smaller 1024/390 checks pass with five articles and no horizontal overflow. TypeScript passes; sidebar lint retains only existing image warnings. The existing scrollbar and responsive breakpoint remain. Frontend rollout `build-2026-10-11-004` from `37f59e1` now serves 100% traffic; actual live desktop/tablet/mobile checks confirm the new widths, scrolling, five articles and no horizontal overflow. [Evidence](evaluations/community-local-updates-20261011.md#visible-sidebar-width-follow-up--october-11-1227-pm-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Quieter and slightly wider Community Feed sidebar

- Increase the large-screen right sidebar from 320 to 344 pixels, reuse the existing hidden-until-hover/focus scrollbar, and keep wheel scrolling contained with keyboard access. Below 1280 pixels, use the shared expandable Local Updates card to avoid the cramped three-column laptop layout. Actual local checks at 1920/1440/1280/1024/768/390 widths pass; mobile refresh is reachable and returns 200. TypeScript passes; RightSidebar lint has only its two existing image warnings. FeedPage's six errors/four warnings are identical before/after this class-only change. Frontend rollout `build-2026-10-11-003` is accepted live from `b93dc0b`; all six actual live widths pass, and ten responsive Local Updates regressions pass after the UI change. [Acceptance](evaluations/community-local-updates-20261011.md#sidebar-scrolling-and-width--october-11-1215-pm-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Local Updates commuter coverage

- Correct the flood-only scope after developer clarification. Collect body-grounded Metro Manila commuter stories from the approved publishers, including GMA official Metro/weather/transport/Walang Pasok feeds. Persist non-flood stories in the existing article table with `local_update` state, without queuing flood extraction or changing schema. Display the latest five stories with broader shared desktop/mobile text. 143 backend and 10 responsive checks pass; actual collection saves ten articles while extraction runs remain 84, and unmocked local desktop/mobile reads show five articles. Matching cloud API/workers/frontend release is accepted. Live desktop/mobile return 200 with five source-linked articles; health and staff denial pass, and the exact build revision promotion is verified in a real successful Cloud Build. [Evidence](evaluations/community-local-updates-20261011.md#commuter-news-coverage--october-11-noon-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Live Local Updates loading failure resolved

- Live `/news/local-updates` returned 404 because Cloud Run traffic remained pinned to recovery revision `lanes-api-00069-fey` after a successful newer build. Verify the newer revision through a temporary preview, promote `lanes-api-00064-kjc` to 100%, and remove the preview tag. Live desktop/mobile reads now return 200 and display the actual empty state; health/database and unauthenticated staff denial pass. Update Cloud Build to prepare a unique build revision without traffic and explicitly promote it after both worker deployments. No schema/dependency/settings/schedule change. [Evidence](evaluations/community-local-updates-20261011.md#live-loading-failure-and-traffic-repair--october-11-1130-am-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Local Updates documentation and pre-push audit

- Audit all eight core records and synchronize delivered Local Updates behavior, source/date filters, desktop/mobile coverage, actual empty saved-data result and pending cloud release. Public metadata/security and dependency/schema checks reuse the verified final implementation; no code changes or repeated tests are needed. Prepare all changes for the developer-requested `roi-branch` publication. [Audit](evaluations/community-local-updates-20261011.md#planner-and-pre-push-audit--october-11-144-am-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 11: Community Feed Local Updates connected

- Replace sample headlines with a public read-only collected-article endpoint and shared desktop sidebar/mobile expandable news card. Approved recent Metro Manila flood stories show source links, publisher and publication date before durable extraction/public-alert approval; private diagnostics and current-flood activation remain separate. Loading/empty/retry/offline/cache states are implemented. 24 backend checks, 10 responsive browser checks, TypeScript and scoped lint pass; an actual read-only PostgreSQL check returns no qualifying recent articles. No schema/dependency/cloud release or map-alert removal. [Verification](evaluations/community-local-updates-20261011.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Documentation and roi-branch pre-push acceptance

- Synchronize deployed recovery, saved historical UI and eligible Pasig coverage/explicit abstention. Scientific accuracy and cloud frontend release remain open. Repeat 63 native PostGIS cases successfully with existing Alembic upgrade to head; changed packages/models/migrations are absent, staged secret/artifact checks pass and changed documentation links/catalog resolve. Preserve previous 106 backend/10 responsive/four actual Info acceptance without double-counting the repeat. Prepare all current working-tree changes for the developer-requested `roi-branch` push under AGENTS.md. [Evidence](evaluations/pasig-ml-automatic-expiry-20261010.md#documentation-and-pre-push-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Recover legacy ML expiry and saved Info forecasts

**October 10, 9:15 PM recovery accepted:** policy v2 recovers immutable original forecasts after late initialization without bypassing current source/review gates. #17/#18 are now inactive with original p90 deadlines October 9, 7:25:02 AM / October 10, 5:04:13 AM (PHT); event timelines say Unconfirmed. #19/#20/#21 retain their deadlines. Production API `lanes-api-00069-fey` serves 100% traffic; cloud jobs use the matching recovery image and minute scheduling is enabled. The local map exposes saved p10/p50/p90 forecasts at Active Zones → All History → Info, verified on actual desktop/mobile records. 106 backend checks, 10 responsive fixtures and four actual Info workflows pass. Accuracy remains experimental; cloud frontend release is separate. [Acceptance](evaluations/pasig-ml-automatic-expiry-20261010.md#legacy-recovery-and-saved-ui-acceptance--october-10-915-pm). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10, 8:48 PM: Legacy investigation checkpoint (superseded by recovery above)

- Complete read-only RCA for #17/#18 after reviewing all four developer-linked conversations and live source audits. Shared Pasig transfer and valid registration/submission proxies exist; preview wall-clock age gates suppress the first late worker application, leaving cached null fixed fallbacks. Original reconstructed p90 values are October 9, 7:25:02 AM and October 10, 5:04:13 AM PHT, both overdue. No operational/source/configuration changes; runtime recovery/testing/release are open. [Evidence](evaluations/pasig-ml-automatic-expiry-20261010.md#follow-up-investigation-legacy-zones-17-and-18--october-10-848-pm). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Pasig ML expiry activated locally and in the cloud

**October 10, 8:36 PM: Pasig ML expiry is operational locally and in the shared cloud worker.** API revision `lanes-api-00067-zox` serves 100% of cloud traffic. Independent job `lanes-zone-expiry` runs every minute; the matching news worker also completed successfully. Cloud inference reproduced saved deadlines for pooled zones 19/20 and cross-location zone 21 exactly. Fixed fallback, global pause, source preservation and Unconfirmed expiry remain explicit. Local controls are available on port 3000; the cloud frontend was not released in this scope. Scientific accuracy remains unverified. [386 backend/10 responsive checks and live cloud verification](evaluations/pasig-ml-automatic-expiry-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Automatic expiry toggle and fixed-timer clarification

- Delivered locally under System Settings → Evidence expiry, with existing audited permission/revision flow and shared scheduled expiry/public/Admin/news/routing behavior. OFF preserves active records without changing deadlines; manual deactivation/qualified clearance remain active; no resurrection. Fixed deadlines apply across cities, while Pasig ML remains research-only. 51 targeted, 186 native PostGIS and 18 unique responsive scenarios pass; actual port-3000 desktop/mobile reads pass. Native databases use existing migrations. Shared cloud policy/deployment remain unchanged. #23 expired at 6:00:29 PM, superseding earlier availability claims; developer review and matching worker rollout are pending. Additional legacy merge duplicate-location failure is tracked separately. [Evidence](evaluations/automatic-expiry-toggle-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Restore actual news content alongside cloud zones on port 3000

- Delivered actual automatic **Zone #23** through the existing services and live independent auditor; source excerpt/title/URL, original observation/expiry and geometry match private #56. Deactivated wrong official #22; other 18 zone responses unchanged; both active readers return `[17,18,19,20,21,23]`. Scoped local clocks preserve historical eligibility without source retiming. Actual desktop/mobile layers/details/link/sign-in/Admin card/deactivation target pass; 117 targeted and 160 native PostGIS tests plus TypeScript/ESLint pass. Developer acceptance and separate clearance exceptions remain open. [Evidence](evaluations/news-boni-corridor-reconstruction-20261010.md#connected-source-fidelity-correction). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Source-fidelity checkpoint after cloud-test rejection

- Read-only live comparison identifies the regression: official #22 lacks a news link and uses operator notes/creation time; actual historical #56 retains source evidence/URL/observation. Record the user's requirement to simulate the real system without altered labels or content. Prior rendering checks are insufficient and developer acceptance remains rejected. Full news-lifecycle coexistence/source-fidelity correction is pending; no database repair is claimed. [RCA](evaluations/news-boni-corridor-reconstruction-20261010.md#source-fidelity-rejection). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Show Boni display test alongside cloud data

- Following developer authorization, create **Zone #22 — [TEST] Boni reconstruction** using the historical system-generated road core through existing staff APIs. Set a two-hour test expiry (7:03 PM Manila) and restore normal data on port 3000. Public/Admin return existing active IDs 17–21 plus 22; all 18 preexisting zone responses remain unchanged. Preserve original article observation/expiry and private automatic reconstruction separately. Actual desktop/mobile shared layers, test details, real sign-in, Admin card and correct Deactivate confirmation pass; cancel confirmation so the developer can test and deactivate it. [Evidence](evaluations/news-boni-corridor-reconstruction-20261010.md#shared-cloud-visibility-follow-up). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Move reconstructed Boni viewing to port 3000

- Correct the testing-origin mismatch: the same port 3000 frontend now selects private historical backend 8001 explicitly. Preserve normal login and dynamic offline floods with session-scoped storage; label reconstruction on desktop/mobile and add the reversible Current Data task. Public/Admin APIs return Zone #56; twelve session regressions and TypeScript pass. Real desktop/mobile public/Admin layers, source details, real UI login, desktop logout and normal-token preservation pass on port 3000; neither screen sends normal API requests while reconstruction is enabled. The Current Data task restores normal zone IDs `[17,18,19,20,21]` in an actual browser. [Current steps](guides/local-news-replay.md#current-persisted-boni-reconstruction). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10 afternoon: Original Boni persisted-zone reconstruction

- Deliver bounded paired-carriageway placement, exact core/gap preservation and dissolved outer margin; repair same-observation continuity and consumed-evidence review filtering. The original collector/extractor/live auditor/publisher/worker creates Zone #56 in the private historical session, with unchanged 4:34 PM observation/6:34 PM expiry and all-vehicle passability. Public/Admin return `[56]`; the stale review item is absent; repeat processing creates no zone. Actual desktop/mobile layers, source details and interactions pass. 152 focused backend and 159 native lifecycle checks pass; four responsive fixture cases pass after one standalone desktop timeout retry. Add the VS Code reconstruction task and recover Docker without deleting volumes. Developer visual acceptance and other time/clearance exceptions remain open. [Evidence](evaluations/news-boni-corridor-reconstruction-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Reconcile reconstruction outcome before shutdown

- Confirm from saved real-service replay and API evidence that the historical reconstruction ran but did not create the original Boni Active Zone. Port-3000 screenshots show existing manual zones 17/18; private public/Admin readers both return no active polygons. Record the remaining road-geometry investigation, service rerun and map acceptance in the task plan. This documentation checkpoint does not deliver a geometry fix or successful plotting. [Handoff](evaluations/news-reconstruction-activation-fixes-20261010.md#shutdown-handoff-and-acceptance-status). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 10 reconstruction/activation corrections:** Registered Daily Tribune, repaired capture source identity, allowed independently verified low-depth passable flooding to create persisted zones, and added guarded historical reconstruction with unchanged observation expiry. Deeper passability/depth conflicts remain review-only. Corrected Needs Review's publication clock and current geometry explanation. Actual original-source services/provider publish Boni as a text alert after retry; four ambiguous sections still prevent a polygon. 180 backend, 47 PostGIS and four responsive checks pass; developer review and geometry/clearance-auditor fixes remain open. [Evidence](evaluations/news-reconstruction-activation-fixes-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 10 persisted simulation session:** Deliver explicit private port-3001 API/auth/SSE routing, shared public/Admin zone clock and genuine persisted-activation/expiry regressions. Docker recovered through backed-up runtime sockets. Real Boni replay still yields zero zones under unchanged policy; developer acceptance remains open. [Evidence](evaluations/news-persisted-simulation-session-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 10: Separate road alternatives from zone display

- Restrict Active-style preview core/halo to the server-resolved candidate; retain unresolved alternatives for explicit one-at-a-time Admin inspection. Stop fitting public camera bounds to excluded alternatives. Preserve genuine gaps and shared rendering; no database/schema/activation changes. Read-only connected records identify the Boni issue as parallel candidate strokes rather than persisted duplicates. Developer acceptance and cross-article reconciliation remain open. [Evidence](evaluations/news-placement-alternatives-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

> Tracking completed milestones, delivered features, and past sprints.

### October 10: Automatic plot solid inner line and transparent outer area

- Deliver the explicitly requested two-layer public automatic-plot appearance through canonical Active core/fill paint. Backend supplies one claim-level core and dissolved decorative 25-m halo; the adapter maps both to existing zone geometry inputs. Preserve source/review status, routing/publication gates and Admin Needs Review styling. Forty-six backend checks, TypeScript/scoped lint, responsive automatic-plot checks and read-only live original Boni fly/hover pass. No SQL/dependency/live publication changes. Developer visual acceptance remains pending. [Evidence and exact responsibilities](evaluations/news-shared-map-renderer-20261009.md#october-10-requested-solid-inner-line-and-transparent-outer-area). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Correct shared news map rendering after developer review

- Replace the separate news painter/controller with an adapter into `useFloodZonesLayer`. Use canonical status paint, zoom-14 layer visibility, shared hover/mobile tap, desktop fly-only clicks, measured popup positioning and mobile close/reopen. Backend presentation-only union joins exact endpoints and removes duplicate coverage while preserving candidate evidence, real gaps and separate carriageways. Original Boni returns four candidates/three drawable sections and remains Needs Review. Forty-eight backend checks, TypeScript/scoped lint and read-only real-source desktop fly/hover pass; responsive acceptance is recorded in the linked evaluation. The preceding Phase 1 checkpoint was rejected for incomplete parity and is superseded. Activation/staff-list parity remains open; await developer visual review. [Correction and limits](evaluations/news-shared-map-renderer-20261009.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Automatic news map Phase 1 UI checkpoint

- Reuse shared FloodZonePopup for news placement hover/tap, original-source information and explicit Needs Review status. Stabilize candidate layers, scale review stroke widths, preserve true gaps/carriageways, isolate selected camera bounds and measure/reposition longer desktop popups. Seventeen browser checks, TypeScript/scoped lint and read-only live Boni hover/zoom-17 focus verification pass, including narrow/landscape mobile details and existing active-news public/admin fixtures. Repository-wide lint and actual original-source activation are not claimed. Await developer visual review before backend grouping/activation work. [Verification](evaluations/news-map-ui-phase1-20261009.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Preserve current zones and add the requested original article

- Remove the unrequested simulation status box from the public map, News Intelligence and shared desktop/mobile news-alert content. Keep September 24 records, road previews, normal database routing and existing zones. Drawing/request errors use the existing map toast; News Intelligence remains available if optional snapshot metadata fails. TypeScript/scoped lint and HTTP page compilation pass; no browser or database mutation in this correction. [@roicambe](https://github.com/roicambe) (Roi Cambe)

- Correct the global private API switch that hid cloud zones. Keep existing interface/work; normal API/login/SSE again use the connected database. Add original captured Tribune article through normal capture/extraction services as Cloud SQL article 25/run 61, yielding five locations; scoped evaluation stops at `unapproved_article_source`. The real estimated-road builder rejects all five sections, so no active polygon is inserted. Full zone snapshots confirm 17/18 unchanged. Retained review overlay uses the connected run identity, and camera bounds include original zones plus replay. Eleven backend checks, TypeScript/scoped lint and browser-free additive map/routing checks pass. No schema/dependency/report-panel changes or browser use. [Current steps](guides/local-news-replay.md#current-port-3000-simulation-session). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Initial private frontend connection (global routing superseded)

- Connect development localhost API/password login/profile and live SSE to guarded private backend 8001. Port 3000 returns five real Tribune locations and four Boni review candidates. Public map reuses the transparent review layer, keeps these previews visible below zoom 14 and focuses candidate bounds. Nine backend guard/clock tests, TypeScript/scoped lint, HTTP page compilation and browser-free map/routing checks pass. No report panel, schema/dependency or cloud publication changes. Physical visual and complete active-zone/subsidence acceptance remain open. [Current steps](guides/local-news-replay.md#current-port-3000-simulation-session). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Check simulated-present flood zones and subsidence

- Add timestamp-aware September 24 collector checkpoints, future-source exclusion, actual zone-reader projection and explicit prediction-stage results. Repair backend-only Active Zones clock injection; normal database-clock behavior is preserved. Forty-three focused and 23 native checks pass. Separate read-only cloud zone 17/18 controls calculate labeled proxy research estimates. Selected news still creates zero zones; estimated news corridors are excluded by the existing prediction adapter, so complete-chain acceptance remains open. No report panel/interface changes. [Evidence](evaluations/september24-plotting-simulation-20261009.md#september-24-as-the-simulated-present-zone-and-subsidence-checks). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Verify the database behind the empty news interface

- Confirm normal port 3000 uses backend 8000 and the configured Cloud SQL `lanes-db` database, while replay ports 3001/8001 use isolated `lanes_news_test`. Cloud stores 24 excluded articles and zero eligible news locations/claim cases/linked zones; selected September 24 replay is absent. Both normal public API paths return zero alerts and existing zone IDs 17/18. Latest collector #63 retains Rappler partial failure. Read-only inspection explains the screenshots; no successful real-news map activation or cloud write is asserted. [Evidence](evaluations/news-live-plotting-check-20261009.md#october-9-318-am-screenshot-and-connected-database-reconciliation). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Correct replay scope and repair map-coordinate handoff

- Capture actual September 24 coverage and run existing collector/pipeline under original chronology/registry. Two GMA feed items admit no flood candidates; Tribune is unapproved, so zero new zones/provider calls result. Archive the rejected invented zone 55 in the private test DB; shared zones remain unchanged. Fifty-three backend checks pass. Successful real-news plotting remains open. [Evidence](evaluations/september24-plotting-simulation-20261009.md#latest-correction-actual-source-collector-and-pipeline-replay). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Move shared public-map URL cleanup after its delayed camera action, preventing Next search updates from cancelling the zoom. TypeScript and a browser-free effect harness pass at two fixture widths; physical mobile/desktop verification remains pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Earlier fabricated plotting demonstration (subsequently rejected)

- The labeled synthetic Quirino Avenue article goes through normal RSS capture, extraction, checked bundled OSM/NOAH, audit evidence validation and automatic PostGIS publication. Zone 55 is present in public and staff APIs, with polygon/core and finite expiry. Publisher/provider responses are offline fixtures; 17 demo/guard checks pass. Shared data and original historical article are preserved. Public preview returns 200; browser acceptance remains open. [Demo links and assumptions](guides/local-news-replay.md#october-9-superseded-fabricated-active-plotting-demonstration). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Prepare developer-selected September 24 archived map inspection

- Seed the captured article offline into the guarded local test database, apply its missing existing publication migration and expose a separate loopback preview on port 3001. Add a shared News Details map handoff that selects archived inspection without changing review eligibility. HTTP authentication/results/detail/placement/map checks pass: five roads, four Boni previews, inspection-only permissions and zero local Active Zones; original zones 17/18 remain unchanged. TypeScript and scoped dialog lint pass. [Manual steps](guides/local-news-replay.md#october-9-september-24-manual-map-inspection). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- No browser/visual verification, provider request, production write, new schema definition/dependency, deployment or push. The responsive shared button and existing mobile/desktop evidence layouts are retained; user visual acceptance remains pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Recover Docker and verify automatic news plotting on native PostGIS

- Preserve failed runtime socket parents and restart Docker successfully without changing database volumes. Existing migrations apply to fresh disposable targets; final combined native suite passes 137 checks, including two new RSS-parser/real-extractor near/corner cases, alongside 116 focused regressions (253 distinct this turn). The synthetic acceptance produces automatically active estimated polygons, road cores, public API source metadata and routing blocks. [Evidence](evaluations/news-auto-plotting-backend-test-20261009.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- No browser/provider/publisher network use, live publication, schema/dependency/frontend changes, deployment or push. Real-news and visual/PWA acceptance remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Review existing automatic news plotting and repair local placement defects

- Confirm the committed pipeline already derives OSM/NOAH estimated polygons and activates qualified audited current claims. Repair local near/corner qualifier handling, locality-before-limit filtering, parallel-carriageway uncertainty and numerical scenario-overlap reconstruction. **221 focused backend checks pass**. Actual September 24 Boni now has four modeled review previews; ambiguous geometry and original stale evidence still prevent activation. [Review and limits](evaluations/september24-plotting-simulation-20261009.md#backend-review-and-local-repair-follow-up). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- No model/migration/dependency/frontend changes, provider calls, browser use, database publication, deployment or push. Broader qualified location coverage and positive real-current-article/PostGIS/map acceptance remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 9: Senior-planner cross-location decision and publication audit

- Reconcile all eight core records against the implemented model/service/router/UI, evaluation manifests and actual verification. Record [Decision 26](decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison) for source-bound partial pooling as a separate research comparison; maintain the primary baselines, conditional training admission and operational lifecycle boundaries. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Preserve the recorded 131 backend/model/API and 24 responsive acceptance, with native Docker/PostGIS, prospective calibration, physical PWA and deployment gates open. Requirements/Node manifests and SQLAlchemy/Alembic definitions are unchanged. The developer authorizes committing all working changes and pushing to `roi-branch` after pre-push verification; this audit does not deploy or promote a model. [Results](evaluations/cross-location-duration-20261008/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Implement automatic cross-location research comparison

- Add separate fixed-prior depth/location AFT and hash-verified qualification/comparison, with purged dependent-source/location/forward folds and declared prior sensitivity. Thirty-six conditional rows share three summaries; unsupported/mixed tests leave primary baselines unchanged. Approximate coefficient/unseen-location uncertainty is explicit. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Connect authenticated Reports+Zones no-store source-audit reads to existing calculation details on both layouts. Preserve frozen depth and actual/null clocks, labelled gauge/recording proxies, abstention and visible retry. 131 backend/model/API checks and 24 distinct responsive cases pass across runs, plus TypeScript/scoped lint and runtime validation. Native PostGIS/build/release and prospective accuracy remain open; no schema/package/push/deployment changes. [Results](evaluations/cross-location-duration-20261008/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Document cross-location flood prediction research

- Save the literature review, local model/dataset findings, source scope, failed feature comparisons and recommended depth-aware AFT partial-pooling investigation in [research notes](research/cross-location-flood-prediction.md). Record the developer's intent to proceed and the qualification, grouped transfer evaluation, uncertainty and automatic integration stages as pending work. Index the document and synchronize research completion with the task plan. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- This is documentation of the research already performed: CSV/artifact inspection and matching prior-evaluation input checksums, not a new model training or application test run. Application code, models, dependencies, SQL schema, operational state and release are unchanged by this documentation task. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Support approved-citizen simulations across Pasig barangays

- Remove the single-barangay restriction for full footprints verified inside the source-consistent Pasig parent. Validate every footprint identity for pooled transfer, retain all detected names and reject outside-city extents. Add immutable source/approval qualification for untimed approved citizen reports; malformed clocks, changed source/zone versions, missing approval, later follow-ups/public evidence and closed/stale cases do not produce simulations. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- The existing Overview and calculation walkthrough distinguish report-submission versus official-registration proxies without new inputs. Real Zone #18/report #16 returns a read-only simulation based on audits #164/#166, median October 9, 2:52:59 PM PHT, with actual observation still null and unchanged operational fields. Seventy-seven backend/model/location checks, twelve targeted responsive workflows, TypeScript and scoped lint pass. Native disposable-DB recheck remains blocked by Docker; no artifact, SQL schema, package, push or deployment change. [Acceptance](evaluations/zone18-submission-simulation-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Explain the actual prediction calculation in existing Overview

- Refine View calculation details into a reference-clock → fitted formula → duration/date walkthrough, with real backend coefficients/conditional percentile values and explicitly rounded display arithmetic. Preserve actual/registration-proxy distinctions and stable forecast anchors; keep source records/model checksum available in a separate disclosure. No new input, tab/page, bubble or Moderation content. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Twenty mathematical/API-preview checks pass, including independent normal-CDF validation and stable refresh results; the new walkthrough passes desktop/mobile workflows. TypeScript and scoped lint pass. Local Docker socket/WSL startup failures block native PostGIS rechecks; the runtime folders are preserved and Docker is stopped, with no data reset. No artifact/kernel, SQL schema/dependency, operational status/expiry/routing or cloud release change. [Evaluation](evaluations/calculation-details-walkthrough-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Senior-planner tech stack and system documentation reconciliation

- Audit all eight core records against the current ML services/endpoints, dependency manifests, audit actions and hashed runtime artifacts. Register selected AFT baselines versus unselected feature candidates, complete prediction locality versus separate news geometry, current Overview/private API contracts and future-report JSON storage. Correct the latest acceptance link and stale catalog wording; explicitly record the delivered future collection/export task. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Preserve Decision 24 and its future LANES source choice after review; no routine architecture decision is added. Street-specific model improvement, forecast-to-Unconfirmed/public retention, release and physical PWA acceptance remain open. This documentation-only audit reuses recorded verification and does not rerun application tests, migrate, deploy, commit or push. [Audit](evaluations/pasig-location-feature-models-20261008/README.md#senior-planner-documentation-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Future LANES model-evidence collection path

- At the developer's selection, extend snapshots to public zone condition reports and owner follow-ups; preserve actual/null observation versus post-validation recorded clocks, numeric versus gauge/unknown depth, proposed-road/spot/official-context scope and causal environmental availability. Independent reviews remain source assessments, not automatic training admission. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Add bounded private per-zone model-evidence export with Reports+Zones capability, keyset/no-store/privacy guards and qualification blockers; existing owner/staff exports include frozen feature snapshots. Final comprehensive 256 backend/model checks pass, preserving operational state and both runtime baselines. Existing 38 responsive checks remain applicable; no new UI controls are added in this collection follow-up. [Acceptance](evaluations/pasig-location-feature-models-20261008/README.md#developer-selected-future-lanes-evidence-collection). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Complete prediction locality and source-qualified feature pipeline

- Extract all 30 Pasig source polygons and the source-consistent city from licensed OCHA/HDX COD data using bounded ZIP ranges. Validate exact PSGC identities, unchanged source rings, disjoint interiors and full city partition; install the separate prediction-locality catalog. Old 20-record OSM/NOAH news footprint/activation gates stay intact. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Freeze model-input snapshots in new citizen/official-create/edit audit records without UI fields or schema changes; preserve missing clocks, gauge proxy meaning and cache-only write behavior. Add protected source-context reads and lazy existing calculation-details inspection with bounded Open-Meteo/Copernicus modelling, visible errors and no invented zero/drainage capacity. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Evaluate depth AFT on 36 qualified rows and depth/location regression on 251 adjacent pairs across three episodes. One AFT fold is unidentifiable and remaining scores are worse; trajectory MAE is worse than persistence in every held episode. Keep both feature candidates unselected and existing baseline artifacts unchanged. More independent outcomes/available street features remain required. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Comprehensive 256 backend/model checks, 38 responsive workflows, TypeScript/scoped lint, runtime asset verification and two actual Zone #17 context/lookup flows pass. The final run includes rainfall precision and future-source/export coverage. Native migrations reach existing head in disposed local databases. No SQL model/schema, package, production/status/expiry/routing write or branch publication; runtime baseline artifacts remain unchanged. [Acceptance](evaluations/pasig-location-feature-models-20261008/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Record pooled Pasig/new-street prediction decision

- At the developer's request, amend Decision 24 with explicitly pooled experimental support for all 30 canonical Pasig barangays and streets absent from training data. Record source/reference assumptions, separate subsidence/passability targets, unchanged training-label admission and actual 20-polygon automatic-location limit. Forecast-to-Unconfirmed/public updates and independent accuracy remain pending; no runtime/code/database/release change is made. [Amendment](decisions.md#october-8-amendment-pooled-pasig-prediction-on-new-streets). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Senior-planner ML completion and next-task audit

- Reconcile all eight authoritative records, model/evidence plans and evaluation index with the source/artifact state. Preserve local delivery versus deployment/accuracy: 127 recorded backend checks, 34 responsive workflows and two actual Zone #17 browser flows; no tests, runtime, database or application code changed during this planner update. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Correct stale Zone #17/unavailable and four-barangay coverage wording, distinguish 30 historical/experimental identities from 20 geometry polygons and actual four/seven training cohorts, and separate passability, subsidence and registration simulations. Order the next task as forecast-to-Unconfirmed → public retention → citizen/admin updates → routing/verification, with independent data/model qualification and release still open. [Current checkpoint](task_plan.md#current-ml-checkpoint-and-next-task), [acceptance](evaluations/case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Pooled research transfer, Ugong transport model and automatic zone simulation

- Fit the separate light-vehicle-passability AFT target using nine source-bound road projections/seven barangays/two summaries, including Ugong. Original dry/subsidence labels and parameters remain preserved; both targets use explicit pooled experimental transfer metadata across 30 canonical Pasig identities, without claiming geography accuracy. One passability held-out fit is unidentifiable. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Automatically simulate subsidence from an unchanged official registration audit when actual observation time is absent; keep the proxy separate from source/training evidence and label it in the existing Overview without form inputs. Fix refresh conditioning so the deadline remains anchored until new evidence arrives. Real Zone #17 now displays October 8 around 5:13 PM PHT, a broad interval and unknown-observation qualifier on both sizes; no expiry/status write. 127 native/model/API checks, 34 desktop/mobile workflow cases, TypeScript/scoped lint and two actual browser flows pass. [Acceptance](evaluations/case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Operational forecast-to-Unconfirmed, public retained-zone updates, independent accuracy and release remain separate open work. No observed-label imputation, schema/package, public map content or deployment change. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Full Pasig historical coverage and Ugong evidence reconciliation

- Add canonical PSGC coverage views for all 30 barangays and a source-linked Ugong index. Annual data covers 29, main wet claims cover 20, and their union covers all 30; main plus October 7 overlay wet claims cover 21. Ugong has eight annual, seven main wet, three overlay wet and one passability projection, but zero matched subsidence-duration rows in retained exports. Current four-barangay model scope is a training-subset limit, not missing collection geography. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Verify 80 retained captures, manifest-bound exports, deterministic rebuild, aggregate counts and unchanged model/input identity. Preserve all raw/versioned datasets; repair coverage reporting/alias grouping without admitting outcomes, adding UI fields or widening the model flag. Broader outcome recovery, pooled-model/location-transfer evaluation, ten missing boundary identities and operational expiry remain open. [Audit](evaluations/pasig-barangay-coverage-20261008/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Automatic geometry/evidence prediction without test inputs

- Replace the rejected hypothetical form and save/acknowledgment controls with read-only Overview calculation on entry/refresh. Server location comes from the full polygon and reviewed boundaries; candidate-only 500 m discovery follows Needs Review. Qualified same-zone/event citizen or current linked news evidence supplies explicit clocks. Positive predictions/abstention pass 69 native checks, 30 responsive browser scenarios, TypeScript/scoped lint, and two actual desktop/mobile Zone #17 browser flows. Zone #17 resolves to Ugong but lacks timed linked evidence and supported model coverage; no forecast is invented. [Acceptance](evaluations/case-linked-ml-review-assistant-20261008.md#automatic-zone-prediction--october-8-correction). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Correct the data explanation: reported subsidence bounds exist; 37 conditional rows share three summaries. Wider model/admin boundary coverage, matched independent outcomes, prospective accuracy and operational expiry/release remain open. No SQL model, migration, package or public-map change in this correction. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Earlier live backend model test (UI withdrawn) in Flood Zone Overview

- Add a collapsed Test model calculation control using the existing authenticated read-only duration API and artifact-supplied barangay choices. Explicit hypothetical PHT inputs produce a median and interval; errors/abstention remain visible and edits discard the old preview. Restore responding local API/frontend servers with their existing encrypted configuration. Inspect shared Zone #17 without writes: no linked report/news or observation time; notes identify unsupported Ugong. The test is separate from real-zone prediction coverage and does not change zone status/expiry. [Acceptance](evaluations/case-linked-ml-review-assistant-20261008.md#live-model-test-calculation). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Compact admin prediction display

- Finish the existing Info Overview prediction summary after timestamps: saved median, remaining time, model interval, inline evidence/model details and visible unavailable, changed/stale, elapsed and retry states. Preserve the original expiry field, map bubble content and Moderation Center scope. 54 distinct desktop/mobile checks pass across recorded runs, with TypeScript/scoped lint and screenshot review. Live Zone #17 confirms the unlinked-report unavailable state; backend coverage for official/news/manual zones and automatic forecasting remain pending. [Acceptance](evaluations/case-linked-ml-review-assistant-20261008.md#compact-overview-prediction-ui). [@roicambe](https://github.com/roicambe) (Roi Cambe)


**October 8 bubble badge only:** The existing status badge displays the supplied news status (Active/Unconfirmed/Cleared), defaulting to Active for existing active-zone records. All other bubble content, styling and controls remain unchanged. TypeScript and the two existing desktop/mobile map scenarios pass. Backend retained-state delivery is unchanged and remains separate work. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Restore Moderation Center report-status scope

- Remove the ML review assistant list, Flood condition follow-ups queue and per-report ML button from `FloodModerationQueue.tsx`. The developer confirms Moderation Center tracks pending/approved/rejected outcomes; active-zone operations belong in Spatial Operations. Existing filters/cards/Info/Review on Map are retained. Both removed queue components are currently unmounted; no replacement section is added. Backend APIs, Profile owner follow-ups and the existing Active Zone suggestion remain unchanged. Responsive acceptance is recorded in the [current evaluation](evaluations/case-linked-ml-review-assistant-20261008.md#moderation-center-placement-correction). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Case-linked ML staff review assistant and follow-up acceptance

- Connect the existing conditional Pasig model to recorded citizen-case evidence; save immutable inputs, observation/availability/issuance clocks, model checksum, staff assumptions and review suggestions in existing private audit JSONB. Staff Reports permissions, bounded latest-per-case pagination, serialized UUID retries and abstention prevent missing times, changed correspondence or pending/accepted subsidence evidence from being bypassed. Later public zone observations signal review even without an observation time; stale evidence remains a request for a current update. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Add ML review assistant to Flood Report moderation and share the case panel with Active Zone Overview on desktop/mobile. Verify owner timed follow-up retry and independent staff review/export against real disposable PostGIS/FastAPI; fix two pre-existing follow-up React lint issues (BUG-126). **119 focused backend checks and 16 distinct responsive browser scenarios pass**, with TypeScript, zero scoped lint errors and one existing warning. Both layouts were visually inspected. Existing migrations apply and generated databases are removed. [Acceptance](evaluations/case-linked-ml-review-assistant-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- Model artifact, schema definitions, dependencies, public status/expiry/routing and training admission are unchanged. Matching deployment, physical PWA, monitored pilot, qualified prospective outcomes and feature-model accuracy remain pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Admin-comparison senior-planner completion audit

- All eight authoritative records, index, feature plan and acceptance were reconciled with the verified local delivery. Existing dependencies/models/migrations remain synchronized; 39 native and 14 distinct desktop/mobile checks, TypeScript and scoped lint/baseline evidence are recorded. Work is local and uncommitted on `roi-branch`; release/device verification remains pending. [Audit](evaluations/flood-zone-community-updates-20261008.md#senior-planner-completion-audit-october-8). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Active Zone details and individual community-evidence editor handoff

- Shared Needs Review/Active Overview facts, readable vehicle vocabulary, separate source/operational notes, location/media and fixed dialog actions. Individual submissions have list/detail comparison, source media and separate review/application status.
- Use in editor prepares explicit server-selected fields; Incorporate confirmation preserves the existing draft and baseline. Atomic version-checked official saves record actually changed fields and evidence provenance; stale earlier drafts remain inspectable until explicit replacement. Mobile Edit stays within Spatial Operations beside the navigation rail.
- Thirty-nine native observation/editor/growth checks and fourteen distinct desktop/mobile browser scenarios pass across recorded runs; responsive acceptance is recorded in [the feature evaluation](evaluations/flood-zone-community-updates-20261008.md#admin-comparison-follow-up-october-8). No package/model/migration addition or branch publication in this follow-up. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Final zone-update documentation and branch publication checkpoint

- All eight authoritative records were audited; the catalog/feature plan/acceptance reflect the single Report Flood panel, original guest view, editable proposed extent, Active Zones staff review, New report discard confirmation and WebGL recovery. Sixteen native checks and twenty-two desktop/mobile browser scenarios pass across recorded task runs; TypeScript and scoped lint/baseline checks pass. Existing migration head `d7e4b9a21c60` is verified in removed disposable PostGIS databases; package/model/migration definitions are unchanged. User-authorized `roi-branch` commit/push is prepared and its Git result is reported separately. Physical camera/media-provider checks and matching deployment remain pending. [Acceptance](evaluations/flood-zone-community-updates-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Compact New report header action with discard confirmation

- Move the signed-in update return action into the existing panel header as New report. Shared confirmation warns that current update fields/files will be lost; Keep editing preserves them, and Discard restores the unfinished new-report draft. The action is disabled during upload and hidden from the original guest gate. Responsive checks include a 320px title/action layout and warning bounds, plus guest UI parity; TypeScript/scoped lint pass. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: WebGL startup and context-loss recovery

- Reproduced and handled browser-blocked WebGL construction without a page crash, removed development double allocation, added visible/manual retry and context-restoration handling, and cancelled stale map timers. Four recovery checks plus two popup regressions pass across desktop/mobile, with TypeScript and unchanged lint baseline. Browser GPU recovery remains external; no deployment/package/schema changes. [Verification](evaluations/cloud-performance-20261007.md#october-8-webgl-recovery). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Original Report Flood login view shared by both modes

- Replaced the remaining custom update sign-in prompt with the original shared badge/heading/message/button and spacing; guest zone context and extra desktop close control removed. Login return preserves the selected zone/condition. Two desktop/mobile parity comparisons and two signed-in upload regressions pass; TypeScript/scoped lint pass. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Report Flood panel reused with editable update extent

- Removed the separate update panel and reused the existing public report shell/fields. Restored the survey button/view, large media picker plus one camera action, editable start/end locations and road preview/map picking. Independent update-road state protects unfinished original reports. Server rebuilds proposed extent into audit JSON; missing observation time stays null and official zones remain staff-controlled. Sixteen native checks pass; responsive acceptance is recorded in the [evaluation](evaluations/flood-zone-community-updates-20261008.md). No schema/package change; physical capture/provider/release remain pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Report Flood observation-time removal and reuse review

- Removed the new-report observation-time field and its state/submission path, including legacy queued timestamps. Six desktop/mobile checks pass for restored draft omission, backend feedback and selected media retention. Current backend reports without explicit observations proceed to staff review; timestamps are not inferred. Recommended one public panel with separate report/update modes and shared field components; consolidation remains proposed. [Review](plans/flood-zone-community-updates.md#october-8-follow-up-reuse-the-report-flood-panel). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Revised Active Zone community observations implemented locally

- Public zone quick actions open one contextual form with observation time/spot, canonical depth/survey, description and optional camera/media. Active Zones retains existing cards/actions and adds Info, unreviewed indicators and private per-zone staff review; official conditions change through existing Edit/Deactivate. Ten native PostgreSQL/PostGIS/API checks and eight desktop/mobile browser checks pass; media focus/Escape follow-up passes four rerun checks. No schema/package change; provider/device verification and release remain pending. [Acceptance](evaluations/flood-zone-community-updates-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 8: Community hotspots delivery documentation audited

- Final behavior and release limits are recorded in the [acceptance contract](evaluations/community-trending-hotspots-20261007.md). All eight authoritative records were audited; native PostGIS/API (nine), desktop/mobile browser (ten), TypeScript/scoped lint and existing migration-head acceptance pass. No dependency, model or migration definition changed. The withdrawn Flood Zone update feature is excluded. Commit/push to `roi-branch` is user-authorized; Git results are reported separately, and matching deployment remains pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Trending Hotspots 48-hour fallback implemented locally

- The backend searches 24 hours first and checks 48 only if no place qualifies; partial lists stay at 24 hours. Both windows retain two distinct contributors, six-hour per-author recency weights and public/located-content filters. The shared sidebar discloses the chosen window, distinguishes empty results from failures, and returns to 24 hours after new activity qualifies. Nine native PostGIS/API checks pass on a fresh disposable database with existing Alembic migrations; the generated database is removed. Ten desktop/mobile browser checks, TypeScript and scoped lint pass; fallback screenshots reviewed on both viewports. Matching deployment remains pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Trending Hotspots sidebar consistency

- Match Saved Places loading bars, muted empty-state spacing, compact location rows and the existing blue sidebar action style for retry. Remove the ranking explanation and show the 24-hour community-activity caption only with results. The shared component covers desktop and mobile; screen-reader loading feedback and reduced-motion support are retained. TypeScript/scoped lint and all eight hotspot browser checks pass; loading, empty, error and populated screenshots reviewed on both viewports. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Recent community Trending Hotspots implemented locally

- Replace desktop/mobile placeholder places with public `GET /api/v1/feed/hotspots` and shared `TrendingHotspots.tsx`. Rank only the last 24 hours, require two distinct contributors, weight each contributor's latest post with a six-hour half-life, and group normalized matching labels within approximately 500 m using PostGIS. Exclude hidden/deleted posts, inactive/deleted accounts, private/rejected/deleted reports and old report reshares; return an empty list when nothing qualifies. Refresh every minute and after feed mutations, with accessible map links, loading/empty/error/retry states. Existing models, migrations and dependencies are unchanged. Backend: 13 checks pass with the existing migration chain applied to a fresh disposable PostGIS database; TypeScript and focused lint pass. Eight desktop/mobile Chromium browser checks pass, including automatic expiry refresh; both screenshots reviewed. Verification is recorded in BUG-120. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Senior-planner pre-push checkpoint

- [x] Audit all eight authoritative records and index the settings, follow-up and duration evaluations/plans; preserve historical verification and open release gates. **174 native PostGIS checks pass** after existing migrations to `d7e4b9a21c60`, and disposable databases are removed. The latest **89 focused ML/settings/pipeline checks** and a fresh frontend production build including TypeScript pass. SciPy is declared; hashed research artifacts/builders are preserved across operating systems. Commit/push to `roi-branch` is user-authorized; its result is reported separately after Git completes. [Pre-push audit](evaluations/pasig-subsidence-validation-20261007/README.md#senior-planner-pre-push-checkpoint). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Subsidence ML baseline comparison and tests completed locally

- [x] Rebuild the original source-verified 37 projections/three shared summaries and reproduce the existing fit; implement summary-held-out lognormal versus exponential comparison with saved fold artifacts and scientific PNG/PDF. Exponential has lower equal-summary interval NLL (2.801 versus 4.123), without establishing prospective accuracy. **89 numerical/API/settings/pipeline checks pass**. Existing data/runtime artifact, operational expiry, schema and deployment are unchanged. [Validation](evaluations/pasig-subsidence-validation-20261007/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Functional System Settings implemented and verified locally

- [x] Replace inactive sliders with typed, revision-guarded operational configuration: staff road margin, per-depth evidence deadlines, human-history citizen eligibility and three independent news stages/publisher controls. Settings and audit commit together; permissions, conflict recovery, recorded stage health and mobile/desktop observation input are connected. No schema/migration or settings-related dependency addition. Production rollout and real-current-news plotting remain separate gates. [Verification](evaluations/functional-system-settings-20261007.md), [rollout](guides/system-settings-rollout.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Structured Pasig follow-up collection implemented locally

- [x] Complete independent review of the five new source captures and regenerate reviewed metadata/hashes without admitting a new subsidence-duration pair. Add owner still-flooded/subsided observations, independent staff review and paged JSON export using existing append-only audit/timeline storage; preserve original geometry/reporter/source availability separately from observation/submission/review clocks. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Integrate Profile/Reports and staff moderation narrow/wide layouts, explicit time/evidence, same-draft retry UUIDs, permission-aware actions and visible errors. Exclude private follow-up records from general audit reads (BUG-118) and use mobile navigation/safe-area padding. TypeScript/AST, independent source/security inspection and hash/diff checks pass. No schema/dependency/model fitting or operational expiry change; actual DB/API/browser/PWA acceptance and deployment remain pending. [Evaluation](evaluations/structured-flood-followups-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Additional Pasig follow-ups captured with separate outcome targets

- [x] Capture five new official/publisher reports with ten immutable HTML/text artifacts. Publish 33 source-reviewed claims (30 wet), one C5 Ortigas southbound October 10, 2025 subsidence outcome with unresolved earlier wet reference, and nine descriptive light-vehicle passability comparisons sharing two outcomes. No new subsidence-duration pair, independent storm verification or production admission. Preserve original 819 wet rows/37 proxies/70 captures and current model; no fitting/runtime/DB/test/deployment change. The initially interrupted independent capture review completed at the later checkpoint above. [Acquisition and source register](evaluations/pasig-clearance-followup-20261007/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Conditional Pasig subsidence model fitted and research preview implemented

- [x] Fit a real intercept-only lognormal AFT research baseline using 37 conditional projections/three shared summaries, with 35 positive bounds only under explicit uninterrupted-episode assumptions. Publish source-linked first/last reference rows, JSON artifact, composite-likelihood diagnostics, three summary-removal sensitivities, evidence and model graphs. All 819 source rows and 70 capture artifacts remain preserved. Median sensitivity is about 13.39–22.61 hours from first recorded wet evidence; no prospective accuracy or depth/locality effects are established. [Experiment](evaluations/pasig-duration-model-20261007/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Implement timezone-aware authenticated staff duration status/preview APIs, explicit assumptions/abstention, bounded JSON loading and no publication/expiry/routing writes. Add explicit SciPy 1.14.1; replace incompatible local 1.18.0 while preserving NumPy 1.26.4. Actual fitting/manual service preview and independent source/runtime audits completed; automated/API/auth/browser tests and deployment remain unperformed. No SQLAlchemy/Alembic or frontend change. Production training admission remains zero; operational prediction is not finished. [Contract](plans/pasig-subsidence-model-implementation.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


### October 7: Live news collection and controlled plotting/lifecycle audit

- [x] Verify six successful scheduled full-pipeline executions after the 1 GiB release. Latest 6 PM run parses 94 entries from six feeds with no saved eligible flood report; read-only cloud checks show all 24 saved articles excluded and zero published claim/zone records. Production API and existing migration head are healthy. This establishes collection, not real-current-news plotting acceptance. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Verify **404 distinct backend checks**, including 131 native PostGIS activation/routing/refresh/clearance/expiry cases, and ten public desktop/mobile browser cases. Four distinct staff cases pass across runs, with a documented desktop timing failure and successful isolated rerun. Pin public browser fixture clocks; verify the 897-tile/20-qualified-barangay runtime bundle. Recover recurring Docker socket startup using preserved runtime-folder backups. [Audit and limitations](evaluations/news-live-operational-audit-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [ ] Complete real-current-article and physical PWA acceptance; evaluate the three-hour collector versus two-hour evidence lifetime. One live free synthetic auditor request timed out at the normal 20-second deadline, so current provider availability remains unaccepted (BUG-117). Staff geometry-editor handoff, coverage and duration-model acceptance remain open. No public data, schedule, deployment, schema or dependency change. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Senior-planner audit before the authorized performance push

- [x] Review all eight authoritative records against both performance passes and deployed API/job/Firebase releases. Reconcile current news-worker release status, shared polling, weather provider, routing safety and idle offline warm-up descriptions; preserve earlier checkpoint history. No new flagship feature, dependency or architectural decision is introduced. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Confirm unchanged dependencies/models/migrations and read-only cloud/local Alembic head `d7e4b9a21c60`. Retain the already completed **37 backend and 16 desktop/mobile browser checks**, production builds, scoped lint and public smoke checks without repeating unchanged code tests. The developer authorizes commit/push of this snapshot to `roi-branch`; Git completion is reported after the operation. Physical-device speed, sustained load, next scheduled job memory and real-current-article acceptance remain open. [Evaluation](evaluations/cloud-performance-20261007.md#senior-planner-pre-push-checkpoint). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Second performance pass — shared sync reads and weather responsiveness

- [x] Share one authoritative flood read per 15-second cycle per API worker, with atomic subscriber capacity, bounded latest snapshots and idle/shutdown cleanup. Move blocking current/forecast provider work to FastAPI's thread pool. Warm offline routing after map rendering during idle time, retaining timeout/fallback/on-demand initialization. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Verify **37 focused backend and 16 desktop/mobile browser tests**, frontend build/TypeScript and scoped lint. A controlled 100-client check proves one database read per poll, and blocked weather requests leave other ASGI requests responsive. API `lanes-api-00057-cuf`, matching discovery image and Firebase `build-2026-10-06-003` are deployed; real health/weather/route/concurrent-sync and public desktop/mobile navigation/reconnect checks pass. Exact limits/rollback are in the [performance evaluation](evaluations/cloud-performance-20261007.md). No additional resource/specification, schema, dependency or authentication change; source uncommitted. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Application and Cloud performance improvements

- [x] Apply authorized API minimum instance 1 and news-job RAM 1 GiB; deploy the tested API image with checked assets and matching discovery image. No database/resource-size expansion elsewhere. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Overlap bounded routing searches off the API loop, remove unchanged flood refetches, defer initial map/panel work and preserve PWA reconnect state. **32 focused backend and 14 distinct desktop/mobile browser checks**, frontend build/type/lint and public desktop/mobile Feed-to-Map/reconnect smoke checks pass. Firebase rollout `build-2026-10-06-002` succeeded; API and frontend serve 100% of traffic on the tested revisions. Source remains uncommitted; next scheduled job memory and physical PWA acceptance remain open. [Performance evaluation](evaluations/cloud-performance-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Pre-push documentation and release-state audit

- [x] Audit all eight authoritative records and synchronize completed local worker/map integration, 897-tile runtime packaging, free-auditor source options and remaining release/current-article/PWA acceptance. Architectural decisions remain unchanged; this implements existing boundaries. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Confirm declared dependencies and unchanged migration/model definitions; retain fresh disposable `d7e4b9a21c60` verification and successful default/extended free probes. **61 focused pre-push regressions pass**, supplementing the documented checkpoints without additive totals. Verify encrypted environment changes and byte-preserved manifest identity. User-authorized `roi-branch` commit/push is the following operation; no merge or deployment is claimed. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Exact-source evidence options repair the free auditor's formatting

- [x] Supply bounded exact-source quote/offset options under prompt v2, preserve the complete article and strict response/evidence rules, and expose only safe numeric HTTP error status. Existing policy fingerprints change; historical records remain preserved. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Verify **170 distinct checks**, including twenty native saved-evaluation cases in a fresh removed local PostGIS database. Rebuild the Linux image and pass offline assets verification. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Verify live synthetic `openrouter/free` responses at 60 seconds and the normal 20-second worker default. Both return valid historical review; no database/public write. Earlier generic HTTP failure remains an availability limitation, not a waived gate. Matching cloud/API/job/frontend release, real article and PWA acceptance remain open. No package/model/migration, deployment, commit or push. [Verification](evaluations/phase-36-auditor-evidence-options-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Free-auditor timeout diagnosed; provider acceptance pending

- [x] Add bounded `--timeout-seconds` for the synthetic probe and transport; preserve the 20-second worker default, exact free-router guard and all evidence/publication checks. **134 focused tests pass**. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Execute one 60-second free synthetic retry. The provider responded, but invalid evidence offsets were rejected (`audit_evidence_offset_mismatch`). No database/public writes or deployment. This is a diagnosed reliability gap, not successful live acceptance. [Evidence](evaluations/phase-36-news-runtime-packaging-20261007.md#october-7-live-timeout-follow-up-earlier-diagnosis). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 7: Runtime assets packaged and Docker startup recovered

- [x] Package 897 unchanged Metro Manila NOAH tiles with manifest checksums and ODbL attribution in the API/job build context. Add build/runtime asset verification, preserve Windows/Linux bytes and retain explicit directory overrides. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Add a free-only auditor configuration check and opt-in synthetic response probe with no database/publication access. Local encrypted configuration passes; no live AI probe was made. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Verify **188 distinct focused tests**, the existing migration/storage lifecycle in a removed disposable local PostGIS database and the final Linux Docker build/offline runtime check. Recover Docker's Windows socket startup error using preserved runtime-folder backups; original containers/database volume remain present. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Write [exact release instructions](guides/news-zone-release-checklist.md). Matching cloud migration/deployment, provider response, real current article and physical PWA acceptance remain open. No new dependency/model/migration, cloud write, commit or push. [Evidence](evaluations/phase-36-news-runtime-packaging-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


---

### October 6: Estimated road activation and existing flood-zone UI integrated locally

- [x] Add server-derived, uniquely grounded OSM/NOAH corridor activation after independent current-news auditing, using existing source_geometry and decision JSONB. Preserve every disconnected component, exact asset binding, depth/access, revision/idempotency and two-hour observation lifecycle; recompute before activation/refresh. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Queue unsupported estimates for Needs Review and skip unchanged spatial-review revisions on repeat sweeps. Reuse existing public/staff layers and shared detail layouts for source, observation, status and estimated/verified basis; invalidate existing map caches and expose refresh failures. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Verify native PostGIS/HTTP/routing/refresh/expiry and desktop/mobile layer/detail fixtures; final totals are recorded in the [integration report](evaluations/phase-36-estimated-road-zone-integration-20261006.md). No new design, model/migration/dependency, live provider call, deployment or push. Real-article, matching release and physical PWA acceptance remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 6: Automatic plotting intent and existing-design audit

- [x] Compare the clarified C5/locality → OSM/NOAH estimated placement → automatic Active Zone target with the actual code. Location clues, narrowed candidates, ranked modeled fragments and selected transparent review previews exist. Catalog-backed activation remains locally complete; estimated-section activation, source centerline for the solid core, safe news details/types and immediate refresh remain unfinished. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] **10 focused checks pass** using deterministic fixtures/existing C5/Ugong assets. Reconcile the next-task wording: backend placement-to-activation and existing UI integration both remain. Existing severity/layer/panel/shared UI must be reused; no redesign or source-code change was made in this audit. [Evidence](evaluations/phase-36-user-plotting-alignment-audit-20261006.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: Automatic footprint worker connected and verified locally

- [x] Add bounded exact-catalog activation after saved extraction, independent evaluation and source-alert publication/maintenance. Recheck all approval/evidence/revision gates atomically, protect staff choices, continue after per-claim failures and preserve stable retries. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Add discovery `--pipeline`, including unchanged/error feed responses and saved-only execution; retain extraction-only mode. Prepare the local Cloud Build job command for the full pipeline, without deploying or running it. Restart seeding skips current-policy handoffs/empty/old runs, and footprint failures cannot block later eligible catalog cases within the bounded sweep. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] **456 distinct checks pass**: 258 targeted, 194 related and four event regressions. The native saved-processing → audit → publication → zone → retry → expiry test uses mocked extraction/provider results and a synthetic approved perimeter. Existing migrations reach `d7e4b9a21c60`; all four final-run disposable databases are removed. No new dependencies/models/migrations, live provider call or normal/cloud data change. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Synchronize plans/records and record BUG-111. Gate 3 is complete locally; actual current-source provisioning, desktop/mobile polygons and full live routing/staging/PWA acceptance remain pending. This slice is uncommitted and unpushed. [Verification](evaluations/phase-36-automatic-footprint-worker.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: Planner audit for the operational repair push

- [x] Reconcile all eight authoritative records with the completed BUG-107/108/109/110 repairs and the latest **398-check** verification. Update detailed geometry rules to full qualified containment and exact server approval; index current and historical evaluations. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Audit dependencies and migration state: existing declared libraries and existing JSONB/metadata columns cover the changes; no new model/migration/package. Disposable upgrades reached `d7e4b9a21c60`, and test databases were removed. Architectural decisions remain unchanged because this implements existing boundaries. Approved real current footprints, worker integration, desktop/mobile polygons and staging/PWA acceptance remain open. Commit/push is the next Git operation. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: BUG-110 trusted current footprint contract verified locally

- [x] Require an approved exact current incident record or authenticated staff review, explicit SRID, full qualified locality coverage and all component identities. Reject caller labels, modeled classifications, missing assets and mismatched input/claim/observation/source/geometry. Preview and submit share the gates; legacy snapshots stay readable. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Prevent unsupported perimeter renewal: current matching extent/components/metadata can refresh; missing or changed proof falls back to a source alert and withdraws unsupported prior links. Staff relinking verifies incident ownership and unchanged geometry/metadata. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] **398 distinct checks pass**: 200 targeted, 194 related and four event regressions across 18 suites. Existing upgrades reach `d7e4b9a21c60` in fresh disposable databases; final runs remove all four allocated databases. No schema/dependency, normal/cloud data, live provider, frontend, deployment or push change. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Synchronize the delivery plan: BUG-110/Gate 1 contract is complete locally. No real current footprint catalog is provisioned; approved source provisioning, automatic worker and desktop/mobile map integration remain next. [Verification](evaluations/phase-36-trusted-footprint-contract.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: BUG-108/109 zone metadata and retained support verified

- [x] Persist independently supported canonical depth/severity and audited access on every staff/automatic news polygon using existing zone metadata fields. Reject unknown depth, passable-to-all activation and unconfirmed known access. Decode contributor polygons for real public-zone responses; vehicle restrictions only tighten existing policy. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Count newly current same-case links during withdrawal; exact retention/retries preserve expiry. Verify final withdrawal/clearance/expiry, replacement, concurrent revision control, rollback and expired-zone rejection. Existing independent news/citizen support checks pass. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] **289 distinct checks pass**: 140 targeted plus 145 related auditor/evaluation/schema/presentation and four event checks. Native public HTTP/zone/routing reads use disposable PostGIS and fixture clocks. Existing upgrades reach `d7e4b9a21c60`; both final runs removed all allocated databases. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Synchronized current plans/records. BUG-110, real worker/map geometry integration and staging/PWA acceptance remain pending. No SQLAlchemy model/migration/dependency, normal/cloud data, live/paid provider, frontend, deployment or push change. [Verification](evaluations/phase-36-zone-metadata-support-repair.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: Automatic news-zone delivery goal clarified

- [x] Checked the active plan, earlier automatic plotting tasks and Git diff/history: automatic news-derived flood-zone polygons remain in scope. Earlier operational completion gates were reopened by the integration audit, not removed. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Made the active delivery target explicit and separated prerequisite metadata/support/trusted-footprint repairs from automatic worker integration, desktop/mobile map polygons and full lifecycle/routing acceptance. These implementation tasks remain pending; this clarification adds no application code or new test result. [Active delivery plan](task_plan.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: BUG-107 activation and refresh repair verified locally

- [x] Reused strict JSON audit loading and current source/policy/claim/freshness/clearance validation; added expected revision and complete geometry/provenance/actor/policy retry identity. Private immutable geometry attribution remains in existing decision JSONB and survives qualified refresh/clearance/expiry. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Replaced the unsupported activation operation with existing approved evaluate/correct operations; write the active decision before its support links. Parallel retries create one result and caller rollback leaves no partial event/zone/link/revision. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] **240 distinct checks passed**: 103 targeted (including both original failures and 23 new checks), 133 auditor/evaluation regressions and four event regressions. Disposable PostGIS upgrades reached `d7e4b9a21c60`; all allocated databases were removed. The event harness seeds its required fixture admin only in its disposable database. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Synchronized plans, bug record and operator boundaries. BUG-108/109/110, actual worker/frontend geometry integration and staging/physical PWA acceptance remain open. No SQLAlchemy model/migration/dependency, live provider request, normal/cloud data, deployment or Git push change. [Verification](evaluations/phase-36-bug107-activation-repair.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: Integration audit reopens operational completion

- [x] Audited checkpoint `67cdffa` against the referenced handoff, active plans and actual collector/worker/API/frontend call chains. The explicit source-alert pipeline is connected, while the configured discovery job stops after extraction and operational activation has no runtime caller. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Fresh verification across eight suites: **78 passed, 2 failed**. Both new native operational activation tests crash after strict audit decoding is swallowed. Staff probes confirm waist-depth zones become medium/no-depth and correcting to the same zone deactivates retained coverage. Basic linked expiry/clearance and staff freshness/policy rejection work. Four disposable databases were created/removed; three full existing upgrades reached `d7e4b9a21c60`. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Reopened gates 1/3/4/5 and recorded BUG-107–BUG-110. Source-alert delivery remains complete locally; operational activation/metadata/support and trusted geometry integration must be fixed before staging/PWA acceptance. Historical test checkpoints below remain historical, with their operational completion claim superseded by this audit. No application source, schema/dependency, normal/cloud DB, paid request or release change. [Evidence and reproduction](evaluations/phase-36-integration-audit-20261005/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: Earlier operational implementation checkpoint (acceptance superseded)

- [x] **Operational helper implementation recorded (October 05, 2026, 7:52 PM, Asia/Manila; completion/test claim superseded by the integration audit above):**
  - **Gate 1 (Operational Footprint Validation):** Implemented `validate_operational_footprint` in `operational_footprint_service.py` to strictly enforce GeoJSON/Shapely `Polygon`/`MultiPolygon` (SRID 4326), area >= 1 sqm, bounds check, non-bridging multi-part separation, and parent locality intersection.
  - **Gate 2 (Non-Committing Flood Event Helper):** Added non-committing transaction support (`commit=False`) to `flood_event_service.py` (`create_verified_event_with_zone`, `deactivate_zone_and_end_event_if_final`) using `db.flush()` for outer atomicity.
  - **Gate 3 (Atomic Publication Service Linking):** Implemented `activate_operational_footprint` and enhanced `apply_staff_decision` and `publish_completed_evaluation` in `news_publication_service.py` to atomically generate/support `FloodEvent` and `FloodAvoidanceZone`s linked via `NewsClaimZoneLink` (`created` or `supported`), with multi-part decomposition and observation refresh.
  - **Gate 4 (Zone Reader Provenance):** Exposed safe `report_source` (`"news"`) and news contributor attribution in `FloodAvoidanceZone` properties without altering database schemas or breaking existing citizen contributors.
  - **Gate 5 (Verification):** All 254 news unit/integration tests and 18 routing tests pass. Verified that operational news avoidance zones inject exclusion polygons into Valhalla and trigger blocked baseline detour warnings. Multi-surface verification with Playwright passes 12 desktop and mobile specs. Native PostGIS lifecycle integration suite verifies multi-part non-bridging, atomic zone creation, and observation refresh extending zone expiry. Full frontend and backend regressions intact. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### October 5: Pre-push documentation audit

- [x] **Pre-push documentation checkpoint (October 05, 2026, 7:08 PM, Asia/Manila):** Senior-planner re-audit confirms **452 broad backend checks, 28 native PostGIS/actual JWT API checks and 16 distinct mocked desktop/mobile browser checks**, with final TypeScript/scoped lint, Python compilation, diff checks and primary screenshot review passed. Locally delivered source alerts, independent auditing, qualified refresh/clearance, two-hour Unconfirmed expiry, finite retention and F6/F7 interfaces are synchronized with current code. Operational flood-zone/routing activation, broader coverage, physical PWA/developer acceptance and deployment remain open. Existing approved migration head is `d7e4b9a21c60`; no new model/dependency/migration, paid provider call or normal/cloud DB write. User-authorized commit/push to `roi-branch` is the following Git step; this checkpoint does not claim push success. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### Phase 36: Automatic source alerts and evidence lifecycle (October 5, 2026)

- [x] Automatic source-labeled **text-only news alerts**, atomic append-only decisions, supported observation refresh, matched clearance and two-hour evidence expiry are implemented locally. Read-time expiry becomes **Unconfirmed** even before maintenance; the default current feed retains it for 24 hours after expiry (configurable 1–72 hours), while safe historical detail remains available. Staff correction/defer/reject/reopen/clearance controls and desktop/mobile public-map News alerts are connected. Operational flood-zone activation/routing remains blocked by missing verified current affected polygons; OSM/NOAH/community boundaries remain placement evidence. No live deployment, paid provider request, new schema/dependency or normal/cloud database migration occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Revalidate independent audit/current policy, immutable article/claim hashes, approved sources and observation clocks under short publication locks. Append decision/case revision and a safe audit row atomically; UUID retries return their original outcome. Historical clearance survives reopening/defer/rejection; consumed evaluations cannot publish a duplicate source case. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Public source reads are bounded and private-note-free. Needs Review excludes current resolved/deferred-not-due identities by exact run/ordinal; staff decision preview is read-only. Existing citizen/manual support is preserved during news withdrawal. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Add bounded saved-article processing → seed → independent evaluation → publication/expiry CLI; discovery remains independent. No application database or production worker was executed. [Verification](evaluations/phase-36-news-publication-lifecycle.md), [runbook](guides/news-publication-lifecycle.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

- [x] Current verification: **452 broad backend + 21 native lifecycle + 7 native read/actual JWT API checks** pass; **16 mocked desktop/mobile browser checks**, TypeScript/scoped ESLint, Python compilation and diff checks pass. Native databases upgraded the existing head and were removed. Shared Select menus now flip/cap against the visual viewport; existing location filters and Active Zone styles/actions remain verified. Primary public/staff screenshot review passes; developer acceptance, physical PWA and deployment remain open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### Phase 36: Independent evaluation and explicit C5 route coverage (October 5, 2026)

- [x] Implement provider-separated independent auditing, full immutable article context, strict evidence offsets and structured place/status/time/depth/access. Explicit model/provider/config revision drives safe policy identity; credentials never fall back across providers. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Bind completed extraction to immutable cases/sources and leased evaluations in the approved schema; retries, lock ownership, safe failures and completion freshness remain separate from extraction. The bounded seed/evaluate CLI creates no decisions/publication/zones. [@roicambe](https://github.com/roicambe) (Roi Cambe)
- [x] Enrich the existing September 27 OSM snapshot with explicit C5 route memberships: 45 Pasig ways/14 ambiguous sections. Deliver read-only coverage checks, explicit administrative-parent mismatch and offline immutable polygon provisioning. GeoRisk/Pasig atlas research yields no suitable official polygon source. Subsequent same-snapshot OSM community review packages twenty valid exact-PSGC Pasig polygons including Ugong, with automated-review/ODbL provenance; ten barangays and operational flood geometry remain unresolved. [@roicambe](https://github.com/roicambe) (Roi Cambe)

- [x] Final combined verification: **449 backend checks across twenty suites and 20 native PostGIS checks pass**. The fresh disposable database completed the full migration chain to `d7e4b9a21c60` and was removed afterward. Mocked providers verify transport/evidence without live or paid requests. Normal application/cloud databases, frontend and dependencies remain unchanged; no new model/migration, public activation or deployment. [Current evaluation](evaluations/phase-36-independent-evaluation-and-spatial-coverage.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

The real constructed C5/Ugong probe returns thirteen clipped candidates and 250 modeled fragments, eleven disconnected preview geometries and zero linework outside Ugong. The result remains `unique_ranked_prediction_not_verified_flood_extent`, with no current-flood or routing assertion.

[Current verification and remaining work](evaluations/phase-36-independent-evaluation-and-spatial-coverage.md). No schema/dependency, frontend/public map, cloud deployment or live activation change.

### Phase 36: Senior planner and pre-push checkpoint (October 5, 2026)

- [x] Audit all eight authoritative records, current plans/evaluations and the index for approved publication storage, Pasig research qualification/follow-up and local v11 disconnected placement. Correct superseded frontend-pause/approval-pending instructions and the stale task anchor while preserving historical checkpoints. Retain Decision 24 without adding a routine architecture decision or new flagship feature. Real reviewed barangay polygons, C5/Pasig road coverage and automatic publication/expiry remain open. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Fresh pre-push verification: **59 checks passed** (37 publication storage, 18 extraction units, four native extraction queue checks). Full `alembic upgrade head`, repeated upgrade and publication downgrade/re-upgrade preserve synthetic evidence in two newly created disposable local databases; both removed afterward. Normal application/replay/cloud databases untouched. Dependencies unchanged; prior 226 placement checks and 14 browser cases/two project-specific skips remain separate evidence, with overlapping extraction tests not added together. [Checkpoint details](evaluations/phase-36-news-publication-storage.md#october-5-pre-push-checkpoint). Commit/push completion is reported after Git succeeds. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Locality repair and disconnected news placement (October 5, 2026)

**Local v11 placement follow-up:** locality aliases now validate barangay level and exact parent city; reviewed boundary catalogs clip supported road candidates; exact NOAH intersections preserve disconnected fragments with scenario/source identity. Spatial Operations uses the existing transparent review aura, with reported-depth severity and gray for unknown depth. No solid news core or public/routing write is introduced. Real reviewed barangay polygon provisioning remains pending. [Disconnected placement verification](evaluations/phase-36-disconnected-news-placement.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

- 226 distinct backend checks, TypeScript/scoped lint and 14 desktop/mobile browser cases pass (two project-specific skips). Synthetic boundaries validate loader behavior; they do not establish real barangay coverage. No deployment or article backfill.

### Phase 36: Approved publication storage and local Docker recovery (October 5, 2026)

- [x] Implement the explicitly approved five additive publication models and migration `d7e4b9a21c60` after `c5a7e9d2104f`: immutable source/decision/link history, finalized evaluations, actor/active-expiry constraints, unique request/revision/source/policy identity and single zone creation owner with multiple support links. Register relationships to existing extraction/users/zones; add no dependency, backfill, fabricated report or automatic activation. [Evaluation](evaluations/phase-36-news-publication-storage.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Pass 60 focused checks: 37 native/storage/metadata tests, 18 extraction units, four native extraction queue checks and one telemetry migration round-trip. Verify full/repeated upgrades and downgrade/re-upgrade preserve original article/version/extraction/zone rows and geometry in disposable local PostGIS. Adapt dedicated extraction-test cleanup to RESTRICT publication FKs. Recover Docker Desktop by preserving stale runtime socket folders and recreating them together; existing PostGIS/Valhalla start, volumes remain intact. Normal application/replay/cloud databases were not migrated; services, endpoints, frontend, push and deployment remain pending. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Phase 36: Pipeline, plotting and expiry continuation review (October 5, 2026)

- [x] Read the three referenced chats and compare relevant decisions with current source/storage and delivered Pasig exports. Reaffirm automatic plotting first, basic freshness before release and Pasig duration evaluation after implementation. Replace the stale next-bundle instruction to repeat readiness assessment with the [concrete backend sequence](plans/news-publication-readiness-plan.md#october-5-continuation-checkpoint). Exact five-table approval, auditor repair, durable publication/expiry, operational geometry and retention/routing remain open. Preserve current F5 inspection and paused frontend scope. [Review evidence](evaluations/phase-36-publication-readiness-audit.md#october-5-conversation-and-source-reconciliation). Documentation only; no application/schema changes, data acquisition, training, new application tests or deployment. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Phase 36: Pasig follow-up, target definition and collector v3 repair (October 5, 2026)

- [x] Deliver the [follow-up bundle](evaluations/pasig-duration-followup-20261005/README.md): eight new official captures/352 verified wet observations, 819 combined wet observations with all 467 original raw rows preserved, three five-hour depth-update pairs and checksummed provenance for 35 source identities/70 artifacts. Recheck older-year leads; 2023 remains uncollected and clearance summaries remain three. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Repair offline collector v3 range/unit/heading/list/pending-row defects and reparse original 18 captures separately: 398 identities/evidence/clocks and 37 bounds retained, supported feature corrections exposed in parser overlays. Independent source and integration reviews corrected qualitative-depth metadata and aligned timeline/snapshot identity across layers. Define the [reported-subsidence contract](plans/pasig-reported-subsidence-target.md) and [Decision 24](decisions.md#24-purpose-specific-reported-subsidence-proxy-and-prospective-prediction-reference); publish 37 conditional proxy projections shared across three summaries, zero training admission. No automated tests, new dependencies, schemas, model fitting, runtime integration, commit or push. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Phase 36: Pasig source and duration-outcome qualification (October 5, 2026)

- [x] Deliver the [reviewed qualification bundle](evaluations/pasig-duration-qualification-20261005/README.md) with three read-only agents and an offline standard-library builder. All 467 wet claims match captured evidence; 463 have supported clocks. Preserve all raw fields, add purpose-specific depth/location/time overlays, group 221 candidate timelines/466 candidate snapshots, and review 37 interval candidates against three usable reported-subsidence summaries (260 minutes inclusive, 120 exclusive, 360 inclusive). Retain twelve NDRRMC rows as historical context. Verify 27 source identities/54 capture hashes, input preservation and interval/reference consistency; independent follow-up confirms overlay and methodology. Zero model labels admitted. No new acquisition, application tests, dependencies, schema, training, runtime publication, commit or push in this task. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Phase 36: Research and expiry checkpoint preparation (October 4, 2026)

- [x] Audit `.gitignore` and pending files for the authorized `roi-branch` checkpoint. Exclude Windows metadata, new local/plaintext env files, private keys, caches/test outputs and regenerable coverage charts in the two dated collection bundles. Preserve datasets, original evidence and research materials. Add `.gitattributes` to prevent line-ending conversion of immutable source captures/PDFs; verify all 75 staged evidence/document artifacts match local bytes. Normalize only trailing whitespace in the expanded source-citation Markdown. Checked pending text for private-key/token patterns without printing values; tracked environment settings are dotenvx-encrypted. Plotting requirements match imports; no SQLAlchemy/Alembic changes exist, so no migration upgrade is introduced. Prior desktop/mobile filter verification remains documented; no new application tests, training or deployment performed. Commit/push outcome is reported after Git completes. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Phase 36: Scope and dataset architecture decision consolidation (October 4, 2026)

- [x] Record [Decision 23](decisions.md#23-metro-manila-product-coverage-pasig-duration-study-and-separated-evidence-datasets): Metro Manila news/plotting coverage, Pasig thesis/initial prediction evaluation, separate evidence registers and a later qualified incident/section training CSV. Update Decision 22 to distinguish rule-based status changes from model retraining. Synchronize the lifecycle plan, active tasks and catalog with the delivered working exports and pending outcome/model gates. Documentation only; no new data, training admission, fitted model or runtime implementation. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Phase 36: Pasig-only expiry-data cleanup (October 4, 2026)

- [x] Export a Pasig-only 2021–2026 working bundle separating 467 wet observations, three clearance summaries, 12 NDRRMC historical incident rows, 37 summary-linked candidate intervals, 679 DRRMO location/depth context rows and eight local duration references. Audit found no exact duplicate observation rows or IDs; retain repeated updates, uncertainty flags, source provenance and the 2023 gap. No records are admitted for model training. Preserve the NCR evidence bundle for regional news collection/plotting. [Cleanup report](evaluations/pasig-duration-cleanup-20261004/README.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Phase 36: Older Pasig years and NCR evidence collection (October 4, 2026)

- [x] Captured 17 selected publisher articles and a 123-page NDRRMC government report with immutable evidence/checksums. Combined the original pilot into **753 evidence records: 739 report observations plus 14 separate historical incident records**, representing 16 of 17 NCR LGUs. Pasig 2021 has eight observations plus 12 historical incidents, 2022 three observations, 2023 a documented acquisition gap; 2024–2026 retain partial source selection. Preserved blocked leads and archive/government-report inspection findings in Markdown. [Register and figures](evaluations/metro-manila-flood-duration-20261004/README.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Derived five unadmitted Manila remaining-time candidates across two dates; flagged eight unresolved chronology conflicts. Independent review corrected road/depth fields and clock evidence. Offline rebuild completed and three standard Matplotlib PNG/PDF/SVG figures visually inspected; coverage bars separate occurrence/status records from observations. No automated tests, live application/database changes, training admission or model accuracy claim. Older-year/NCR acquisition continues as an unresolved task. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Second public flood-duration collection batch (October 4, 2026)

- [x] Captured four additional official Pasig reports and rebuilt source citations, registers and Matplotlib exports: 18 captured sources, 398 candidate observations across six candidate continuity groups and 14 barangays. Clearance episodes remain three; 2021–2023 remain uncollected. Revised v2 extraction handles spaced list numbering, flags disagreeing alternate units/unsupported bullets, and records 32 exceptions. Inspected newly saved evidence and selected derived rows, and viewed updated coverage PNG; no automated tests, application/database changes or trained model. [Report](evaluations/flood-duration-pilot-20261004/README.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Revised duration-data collection window (October 4, 2026)

- [x] Recorded the developer’s expanded **2021–2026** scope, with 2026 explicitly partial through the recorded collection cutoff. Updated the plan, source register, pilot report and active collection task. Missing-year coverage and independent-storm outcome requirements remain explicit; no extra source capture or model training is claimed. [Collection scope](plans/flood-evidence-lifecycle-and-duration-plan.md#evidence-work-package-metro-manila-collection-pasig-duration-evaluation). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Standard Python research graphs (October 4, 2026)

- [x] Replaced both custom SVG diagrams with Matplotlib default-style plots, readable axes/gridlines and interval endpoint markers. Delivered 300 dpi PNG plus vector PDF/SVG; visually inspected both PNG exports. Added a standalone offline plotting helper reused by the collector and synchronized requirements, tech stack and reproduction instructions. Existing observations and candidate bounds remain the figure inputs; no ML fitting or automated tests. [Pilot figures](evaluations/flood-duration-pilot-20261004/README.md#files). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: First public flood-duration dataset pilot (October 4, 2026)

- [x] Built a bounded/cached offline standard-library collector and captured 14 selected official Pasig reports with immutable HTML/text, checksums, source manifest and complete Markdown citations. Exported 276 candidate observations, 37 location/clearance-bound candidates sharing three reported-clearance episodes, a two-row depth conflict exception list, data-coverage and interval figures. Saved Figshare simulation metadata separately. [Pilot report](evaluations/flood-duration-pilot-20261004/README.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Preserved unknown onset, summary-scope inference, observed-vs-administrative clearance and correlated episode identity. Offline rebuild completed; selected source/clock/conflict records inspected. No new automated tests, application/schema/dependency change, database write, full five-year collection, simulation-archive download, training admission, model fitting or accuracy result is claimed. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Recent-study and public-supplement verification (October 4, 2026)

- [x] Extended the [RRL](research/metro-manila-flood-duration-rrl.md#10-recent-study-supplementation-without-waiting-for-external-requests) with a 2026 Philippine study covering recent storm simulations and verified UrbanFlood24 public Figshare metadata/license/file size. Rechecked Google's public news-derived archive methodology. Updated source register and plan to use accessible online sources without making external requests a dependency; keep empirical labels, context/priors and simulations distinct. No raw dataset archive downloaded, training register admitted, model fitted or accuracy demonstrated. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Original-goal reconciliation after scope drift (October 4, 2026)

- [x] Reread “Flood plotting on map 2” and “Plan AI flood NLP and NER” and reconciled the current duration-research decisions. Corrected the [plan](plans/flood-evidence-lifecycle-and-duration-plan.md#scope-and-delivery-sequence) and active tasks: location-dependent duration investigation and public-data pilot remain active; the deadline-driven fallback-first deferral was a recommendation, not developer acceptance, and is withdrawn as active priority. Preserve conditional two-hour Unconfirmed fallback, evidence-based clearance, five-year target, graphs and optional ML selection. Documentation only; no collector/model/lifecycle delivery claim. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Defense deadline and evidence-based lifecycle scope (October 4, 2026)

> **Superseded recommendation:** the developer subsequently challenged this scope shift. The entry below records the earlier proposal only; see the scope correction above for the active goal.

- [x] Recorded next-week defense and the developer's clarification that trained duration ML is not mandatory. Proposed automatic evidence ageing to Unconfirmed, matched credible report-based clearance and a small traceable replay, with five-year collection/agency requests later. This deferral was not accepted and is superseded by the [scope correction](plans/flood-evidence-lifecycle-and-duration-plan.md#scope-and-delivery-sequence). Two hours is a freshness policy, not validated physical drainage. No application, schema, dataset or model change, new lifecycle evaluation or release is claimed. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Earlier-source acquisition reconciliation (October 4, 2026)

- [x] Audited documented findings against the source register and existing project data files. Expanded the [source inventory](research/flood-duration-data-sources.md#earlier-research-acquisition-status-and-priority) to retain all earlier source families with reviewed-vs-acquired status and pilot priority. Marikina raw gauge histories, JICA survey/GIS and UP temporal simulation outputs have not been obtained; five-year collection remains pending. Documentation only, with no dataset acquisition or outreach performed in this audit. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Research dataset source register (October 4, 2026)

- [x] Created [flood-duration-data-sources.md](research/flood-duration-data-sources.md) with original report citations, stable source IDs, access dates, inspection limitations and unacquired MMDA leads. Added collector requirements for source snapshots/checksums, version/admission status and observation/incident linkage; indexed the document. Full collection and dataset admission remain pending. Documentation only. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Five-year collection target and next deliverable (October 4, 2026)

- [x] Recorded the accepted five-year research collection target, 2021–2025 with available 2026 updates for recent evaluation, and the immediate offline Pasig collector/observation/incident-register work package. Specify immutable sources, supported embedded clocks, automatic quality checks, sample/exception review, coverage graphs and a measured training-data gate. 2021–2023 archive coverage remains unverified. [Work package](plans/flood-evidence-lifecycle-and-duration-plan.md#evidence-work-package-metro-manila-collection-pasig-duration-evaluation). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Clarified that the next delivered result should be a traceable dataset plus coverage report before model training. Planning/documentation only; no collector implementation, full archival scrape, dependency/schema/application change or model training occurred. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Revised fallback, recent-data evidence and shared ML study plan (October 4, 2026)

- [x] Recorded the developer's revised **two-hour observation-based fallback to Unconfirmed where validated duration support is insufficient**, future commuter confirmation interaction, and retention of the current CSV primarily for plotting. Updated current plans/decisions while preserving the earlier rejected-policy history below. No runtime feature was implemented. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Directly retrieved official Pasig August 2026 reports and verified candidate wet/clear chronologies for Maybunga and Dela Paz. Preserved interval bounds, summary scope, unknown onset and same-episode correlation. Checked 2026 MMDA request responses: information emailed privately or still pending, with no verified public training schema. [Recent-data follow-up](research/metro-manila-flood-duration-rrl.md#9-recent-data-and-revised-plan-october-4-follow-up). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Clarified data sufficiency: enough for design and a recent labeling pilot, insufficient to claim validated NCR duration accuracy. Added shared feature-based model investigation, interval-aware XGBoost AFT and completed-duration quantile boosting comparators, geographic holdouts, abstention and mandatory graphs. No model/package/schema/code changes, application tests, agency outreach or deployment. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Metro Manila flood-duration RRL and accepted study direction (October 4, 2026)

- [x] Completed parallel local-literature, data-source and methods research; reconciled observed survey durations, river-threshold distributions, consultation summaries, simulation trajectories and accessible clearance advisories in the [RRL](research/metro-manila-flood-duration-rrl.md). Checked requested repository search/access limits without claiming an exhaustive dataset search. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Verified the original official Pasig DRRM Plan 2023–2028 readable text: Table 19 contains Duration estimates for qualified barangay areas based on consultations. This separate source complements the verified CSV/workbook absence of duration fields; its ranges are not incident-level ground truth. Direct raw-file download failed, so no visual table-layout check is claimed. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Recorded explicit rejection of universal two-hour expiry and acceptance of survival analysis for investigation in current plans/decisions. Added offline register acquisition, interval-aware empirical/AFT candidates, reporting-bias checks and mandatory graphs. No runtime/schema/dependency changes, model training, provider forecasting calls, agency/author outreach, commit or deployment. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Flood evidence lifecycle and duration research (October 4, 2026)

- [x] Recorded developer acceptance of **Unconfirmed**, distinct from Active and evidence-confirmed Cleared. Updated the [lifecycle plan](plans/flood-evidence-lifecycle-and-duration-plan.md), publication readiness and architecture decision; finite freshness/retention and ML selection remain open. The earlier two-hour proposal is unaccepted. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Completed [primary-source research and local file audit](research/flood-expiry-and-duration-research.md): 726 cleaned Pasig rows and original CSV/workbook lack duration labels; NOAH products, Google river/urban-flash forecasts and Groundsource, permitted external weather/hydrologic data, censored-duration model choices and mandatory graphs are documented. Existing event durations describe operational closure and require provenance audit. No application/schema/dependency changes, training, authenticated provider calls or deployment. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Backend publication readiness assessment (October 4, 2026)

- [x] Completed storage/runtime/geometry/asset assessment and prepared a [five-table proposal with lifecycle, transaction and API contracts](plans/news-publication-readiness-plan.md). Reuse verified multi-section events/zones; unresolved alerts need separate durable claim storage. Schema approval, expiry decision, operational footprints/boundaries and F6/F7/F8 implementation remain pending. No model/migration/application/dependency or cloud changes. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Seven existing hybrid regressions pass. Isolated MockTransport confirms Google-key-to-OpenRouter fallback and missing article context in the dormant auditor; fixes remain pending under BUG-098. Inspected DRRMO workbook, raw CSV and 726 cleaned rows: no onset/clearance/duration fields. Recommended two-hour evidence freshness, not estimated flood duration; expired observations must remain unknown rather than imply clearance. [Evidence](evaluations/phase-36-publication-readiness-audit.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Automatic plotting readiness and documentation reconciliation (October 4, 2026)

- [x] Audited the eight authoritative records and reconciled current task, frontend, spatial, hybrid, feature/system and catalog descriptions with local F5 inspection and v10 analytical previews. Earlier implementation/release history remains intact; nationwide target is distinguished from current Metro Manila coverage. Recorded the next backend storage/geometry/auditor/asset assessment before dependent publication UI. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Read-only investigation verified 55 placement/activation checks plus 15 grouping/extent checks (70 passing; one database-backed preview check deselected). A constructed C. Raymundo claim returns 25 sections and a unique NOAH/DRRMO-ranked prediction; adding Rosario returns `missing_valid_barangay_boundary`. The result remains read-only and cannot affect routing. This is neither a live article nor an activation test. No new application/schema/dependency changes, PostGIS growth transaction rerun, deployment or browser visual acceptance. [Evidence and limits](evaluations/phase-36-needs-review-inspection.md#october-4-automatic-plotting-readiness-audit). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Local Needs Review inspection workspace (October 4, 2026)

- [x] Make Barangay a city-first filter: disabled with “Select a city first” until a city is chosen, then use its existing server-scoped barangays; changing/clearing city clears the barangay. Reuse shared Select disabled support and verify desktop/mobile. [Verification](evaluations/phase-36-needs-review-inspection.md#october-4-city-first-barangay-filter). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

- [x] Audited the Primary Panel checkpoint with the senior-planner skill: synchronized existing feature/system/task/progress/bug records, catalog and F5 plan; confirmed no dependency/model/migration changes and retained prior 33 backend/38 browser checks, TypeScript/scoped lint evidence. The fresh local Alembic check could not complete because Docker/PostGIS is offline; no cloud database was used. Prepare the requested `roi-branch` commit/push. [Audit](evaluations/phase-36-needs-review-inspection.md#october-4-primary-panel-push-audit). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

- [x] Refined Spatial Operations Primary Panel in the existing design: server-side queue search and city/barangay/severity filters retain full related groups, cards summarize locations/conditions/latest report, and reports/zones/contributors share a flat detail component. Compact desktop actions retain mobile touch sizes and own-record targets. 33 backend checks and 38 distinct desktop/mobile browser cases pass across the suite and focused reruns (two expected skips); TypeScript/scoped ESLint pass. [Verification](evaluations/phase-36-needs-review-inspection.md#october-4-primary-panel-search-and-detail-consistency). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

- [x] Completed the requested senior-planner audit for the Needs Review/related-report and reviewed flood-growth `roi-branch` checkpoint: eight authoritative records checked, existing Spatial Operations behavior synchronized, no new dependency/model/migration or architectural pivot, and native user-review checks separated from unfinished news publication/native news-placement acceptance. Prior 46 backend/34 desktop-mobile checks and TypeScript/scoped lint remain applicable. [Checkpoint audit](evaluations/phase-36-needs-review-inspection.md#october-4-senior-planner-checkpoint-audit). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Implemented reviewed cross-boundary flood growth locally: nearby active-zone discovery, extension/evidence-only/separate-section actions, shared server preview, retained coverage/core and atomic report/history/audit saves. Existing event locations/zones support multiple streets/barangays and section-specific conditions without schema/dependency changes. 46 distinct backend and 34 distinct desktop/mobile browser checks pass (two viewport skips), with TypeScript/scoped lint. Native JWT/PostGIS verified in rollback-isolated local test DB; actual screenshot incident membership, developer acceptance and publication remain open. [Verification](evaluations/phase-36-needs-review-inspection.md#october-4-cross-boundary-growth-implementation). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Audited the developer's cross-boundary flood-growth concern against Phase 33. Existing event locations already support multiple roads/barangays; identified pending-report-only discovery and inconsistent corroboration/geometry replacement across merge paths. Recorded proposed backend-first extension work as pending, with no application/schema change or new test run. [Scope review](evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-cross-boundary-growth-scope). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Fix stale related-report membership after selecting a different map report. Resolve the selected identity's current group in the backend, including non-anchor members, without changing styling or merge rules. Native local database verification remains pending after a connection timeout. [Verification](evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-selected-report-group-resolution). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Reuse the original full report layout for related reports, including badges, timestamp/location, Info and individual moderation actions. Remove the duplicated selected report; approving/rejecting another report preserves the current detail. [Verification](evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-consistent-related-report-layout). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Move related-report comparison into report details and remove the queue dropdown. Preserve source cards/grouping, individual moderation/map focus, lazy member paging and return-to-queue focus. Desktop/mobile verification is recorded in the [detail follow-up](evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-related-reports-inside-details). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Refined Needs Review from developer screenshots: light blue user/light violet news cards, related same-road user groups within 500 m/two hours, individual severity/depth/evidence and lazy member pagination. Reused merge name normalization without tracing, synthesis or automatic merges. 95 backend checks, TypeScript/scoped lint and 18 distinct current Spatial Operations browser checks pass (two viewport skips). Native database/load/developer acceptance remain open. [Follow-up](evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-related-cards-and-source-styling). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Pushed checkpoint `d435f02` to `roi-branch`, then implemented protected combined queue/detail reads, Needs Review source filters, in-place evidence and separate blue dashed news placement suggestions. Existing user-report actions remain; Create/Merge/Edit drafts are preserved. No model/migration/dependency change or news publication/routing writes. Subsequent implementation remains local; 82 backend checks, TypeScript/scoped lint and 37 browser cases pass (five expected skips). Native API/PostGIS and developer visual acceptance remain open. [Evaluation](evaluations/phase-36-needs-review-inspection.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Local backend OSM/NOAH/Pasig placement preview (October 3, 2026)

- [x] Delivered shared typed previews and protected no-write current-placement reads with exact tiled NOAH overlap, matching Pasig road/crossing history, alternatives and explicit source/boundary errors. Built 897 local vector tiles plus manifest; preserved attribution/checksums. Spatial probes reproduce the 86.2 m Santo Domingo span and six Caruncho candidates without routing effects. 550 distinct checks pass (one skip). No SQLAlchemy/migration/dependency change, actual replay, UI change, commit/push or release. [Verification](evaluations/phase-36-backend-placement-preview.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Flood Zone rendering and placement investigation (October 3, 2026)

- [x] Completed requested source investigation of shared Map/Spatial Operations active-zone rendering and Report/Create/Edit previews. Recorded centerline versus operational polygon roles, existing buffer/geometry compatibility checks, unconnected runtime NOAH ranking and section-specific Pasig DRRMO requirements. Recommended backend placement preview followed by existing map integration and durable gated publication. Documentation only; application code, database, dependencies and deployment unchanged. [Investigation](evaluations/phase-36-flood-zone-rendering-investigation.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Four-article source/database re-audit (October 3, 2026)

- [x] Freshly fetched all four original publisher bodies with unchanged content; independently audited body/context/caption evidence and every stored/detail record. Local v9/v1.7 repairs overstated depth precision, missing generic passability, incorrect homonym provinces and clearance-bound labels. All 595 backend tests pass; real backend/frontend proxy match 38 details, four histories and Collection with zero mismatches. Four new immutable runs preserve previous records; reports/zones stay zero. Browser visual acceptance is still blocked by saved policy. No schema/dependency/production change or new commit/push. [Audit](evaluations/phase-36-four-article-source-audit.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Documentation synchronized before v8 branch publication (October 3, 2026)

- [x] Completed the requested senior-planner audit before the authorized `roi-branch` commit/push. Current task, feature, stack, database, system, bug and evaluation records distinguish tested local v8 from production v4; index links and historical results are preserved. Decisions require no new entry because no architectural pivot occurred. Visual acceptance, freshness policy, fallback integration and automatic map publication remain open. No application source changed after the 555-test review. [Preparation](evaluations/phase-36-news-workflow-follow-up.md#documentation-preparation-before-branch-publication). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: v8 branch readiness review (October 3, 2026)

- [x] Reviewed the complete pending bundle with senior-planner/merge-coordinator guidance; fetched `origin/roi-branch` with zero divergence. Expanded verification to 555 backend checks including routing, depth, authorization and geometry; TypeScript and scoped lint pass again. Synchronized current feature/stack/database notes with local v8 while preserving release history. No dependency, model, migration or deployment source changes; final visual acceptance and freshness remain open. This is readiness evidence, with no commit or push performed. [Review](evaluations/phase-36-news-workflow-follow-up.md#branch-readiness-review--october-3). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: News workflow correctness follow-up (October 3, 2026)

- [x] Corrected approved cautious passability, independent road facts, discarded publisher corrections and hidden retrieval failures. Added server-owned Road passability details and removed the dead Collection filter from shared mobile/desktop UI. Local v8/v1.6 preserves history and 33 replay sites with 20 caution records; 452 backend tests, TypeScript, scoped lint and real private API/proxy evidence checks pass. Read-only Scheduler inspection confirms three-hour collection and an unchanged-RSS gap; refresh policy remains unapproved. No database schema/dependency or production changes; no browser implementation/debugging. [Evaluation](evaluations/phase-36-news-workflow-follow-up.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: September 9 multi-location day replay (October 3, 2026)

- [x] Team-tested three actual publisher reports through reconstructed September 9 RSS and the real saved processing/reading services in private `lanes_news_test`. Source comparison matches all 33 locations; corrected missing roads, passability wording, PSGC qualifiers, shared list evidence/clocks, approved exact GMA update-header anchoring and forecast/drill/narrative boundaries. Local v7/v1.5 preserves older inputs/runs, unknown facts and zero reports/zones; 410 related tests pass. Authenticated real backend/frontend proxy lists and all detail evidence match. Fixed the private launcher's failing Windows reload behavior. Additional RSS/GDELT audit is recorded; registrations and scheduled fallback are unchanged. Visual verification remains blocked by saved browser permission, and production v4/release/map integration remain unchanged. [Evaluation](evaluations/phase-36-september9-production-day-replay.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Documentation and branch pre-push verification (October 3, 2026)

- [x] Audited the eight registered documents and reconciled monitoring's verified production rollout with the still-pending v6 release/automatic placement. Dependencies are unchanged; private configuration and replay data remain ignored. Verified 355 news/backend cases plus five disposable PostgreSQL queue/migration cases (360 distinct checks), existing local `alembic upgrade head`, TypeScript, scoped lint and 25 responsive UI cases. Three optional/project UI cases were skipped. Corrected the existing publisher-option test to account for the shared Select portal; both previously failing desktop/mobile cases pass on focused rerun. Remote `roi-branch` had no divergence. This verifies branch preparation, not production v6 deployment or automatic map integration. [Evidence](evaluations/phase-36-september24-historical-replay.md#branch-pre-push-verification--october-3). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: City summaries remain context beside specific flood sites (October 3, 2026)

- [x] Added article-level extraction reconciliation: a broad city observation becomes `location_context_only` when credible specific sites in that same resolved city are present. City-only reports, other cities, unreliable specific mentions and distinct explicit observation times remain independent. Source evidence/offsets and each street's facts remain unchanged. Bumped immutable processing identity to v6/v1.4 and reprocessed the private Docker article into a second run, preserving the original run. Actual authenticated API/browser now show five street cards and zero Collection attention items. All 224 related backend tests pass. No schema/dependency/frontend changes; production v4 remains unchanged. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Explicit location fields in news flood details (October 3, 2026)

- [x] Added a flat Reported location section before the detail measurements, showing the existing extracted street, barangay, reported section/intersection and local area/landmark. A city/area mention without an extracted road explicitly says **Not specified for this mention**, without borrowing another claim's street. Live local replay checks confirm Boni/F. Ortigas, Gov. Pascual/Sitio 6 and long Aurora directions at desktop and 390/320px mobile widths with no horizontal overflow. TypeScript, scoped ESLint and both existing desktop/mobile Info modal tests pass (automated API fixtures; live checks use actual local API data). No backend/schema/dependency change or deployment. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Private Docker replay visible in News Intelligence (October 3, 2026)

- [x] Recovered Docker Desktop from failed Ingest/Secrets Engine runtime sockets through preserved-directory backups, without resetting volumes. Created separate `lanes_news_test`, applied the complete existing Alembic chain to `c5a7e9d2104f`, saved the real September 24 body through the durable processor and restarted loopback-only frontend/backend using ignored test overrides. Verified authenticated API and actual browser main list (seven locations/five roads), Boni detail/source and Collection ready with zero questionable mentions; no API mocking. Repeated seeding retains one article/one run and unchanged zone totals. All 29 focused replay/isolation tests pass. Added reproducible launchers/[guide](guides/local-news-replay.md). Production configuration/data and the existing local `lanes` database are preserved; v5 deployment and automatic plotting remain pending. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: September 24 historical pipeline replay (October 3, 2026)

- [x] Tested the real Daily Tribune report through publisher retrieval, production extraction entry point and local OSM; verified durable queue/main SQL reading in an isolated database and the actual PostgreSQL predicate with read-only literals. Corrected streamed body retrieval, numeric compounds, intersections/directions, city/PSGC attribution, cleared states, explicit recent weekday clocks, adjacent passability and duplicate qualifiers/attention counts. Five road sites now preserve correct original facts. All 373 related backend tests pass (one disposable-database migration skip); 19 PostgreSQL policy and 11 real-claim parity checks pass. Version v5 is local and not deployed; production history remains unchanged. [Evidence](evaluations/phase-36-september24-historical-replay.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Strict actual-flood collection follow-up (October 3, 2026)

- [x] Released affirmative Metro Manila reporting-body admission, blocked-body rejection and explicit excluded history. Forecasts/simulations/drills/habitual references and caption-only artifacts cannot qualify. API `00049-q25`, the matching collector and Firebase frontend `build-2026-10-03-002` are live. Saved-only and normal executions succeed; ten v4 results preserve all 30 prior runs, ten source versions and 24 articles. All 341 backend tests, 15 PostgreSQL checks, TypeScript and 15 deployed desktop/mobile cases pass (mocked API/session). All 24 legacy articles are excluded; zero qualify for the main or attention lists. No additional schema change. [Evidence](evaluations/phase-36-news-content-quality-investigation.md#v4-backend-release-verification). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: News observation and geography correction (October 3, 2026)

- [x] Released the correction to API `00048-xc7`, the matching collector image and Firebase frontend `build-2026-10-03-001`. Approved migration `c5a7e9d2104f` succeeded. Corrective and normal collector executions pass; ten new completed runs preserve all 20 previous runs, ten source versions and 24 articles. The nine false main-list cards are excluded. Final eight PostgreSQL checks and 13 deployed desktop/mobile tests pass; frontend tests mock API/session boundaries. Automatic plotting remains the next integration bundle. [Release evidence](evaluations/phase-36-news-content-quality-investigation.md#completed-production-release). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

- [x] Implemented shared prevention/habitual and Metro Manila evidence checks across extraction, discovery, SQL counts/pagination and reader explanations; closed the metadata-local body bypass and common-noun gazetteer matches. Versioned the corrected extractor/processing pipeline. All 306 backend regressions, eight read-only PostgreSQL policy checks, 13 distinct desktop/mobile UI cases and TypeScript pass. The same 24-article database yields zero qualifying rows under the corrected reader, excluding nine false cards while preserving source/history. Production migration, reprocessing and synchronized release are complete as recorded above. See [verification](evaluations/phase-36-news-content-quality-investigation.md#corrective-implementation-and-verification--october-3). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: News content quality investigation (October 3, 2026)

- [x] Traced the reported foreign/prevention stories through 24 configured saved articles, latest immutable runs and local main-list predicates. Confirmed nine misleading displayed claims and reproduced the errors with the current pure local rules parser. Verified API/collector release metadata and live route probes: healthy/authenticated source boundary, but the new results route is absent from production. Recorded [BUG-085](others/bug-log.md#bug-085-news-intelligence-displays-foreign-floods-and-prevention-projects-as-flood-observations), the [investigation](evaluations/phase-36-news-content-quality-investigation.md), and data correctness/release alignment as the immediate priority before plotting. Read-only database/Cloud inspection; no external AI, stored writes, functional correction or deployment. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Monday deployed-site demonstration priorities (October 3, 2026)

- [x] Recorded the developer-confirmed October 5 presentation on the deployed website. Prioritized the automatic article-to-map integration, operational NOAH/DRRMO context and actual auditor participation, followed by synchronized migration/API/collector/frontend release and deployed desktop/mobile rehearsal. Deferred optional administration/monitoring polish; retained original evidence/routing gates and a clearly labeled isolated replay proposal for repeatability. Documentation planning only; no implementation, schema change, push, deployment or replay delivery is claimed. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Runtime OSM dependency isolation (October 3, 2026)

- [x] Removed unnecessary native-PBF loading from runtime catalog matching by deferring the existing `osmium` import/handler to the bounded raw-file reader. All 140 focused regression checks pass, including the 26 formerly failing checks and a fresh-process native-dependency isolation case. Windows security remains unchanged; raw-PBF tooling is still subject to its separate unsigned-library restriction. No schema, dependency or UI changes, no deployment or completed automatic publication claim. See [BUG-084](others/bug-log.md#bug-084-windows-application-control-blocks-osmium-during-pipeline-verification) and [verification](evaluations/phase-36-automatic-plan-alignment-audit.md#verification-recovery-runtime-dependency-isolation). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Completed-work alignment audit (October 3, 2026)

- [x] Compared recent committed reading and uncommitted telemetry changes with the automatic pipeline target. Found no removed activation path or new routine staff approval; recorded existing disconnected publication/NOAH ranking and preview-only geometry limits. Telemetry introduces a migration-before-collector deployment dependency. Focused checks: 81 passed, 26 failed on Windows Application Control blocking `_osmium`; this audit does not replace prior verification with a passing result. Recorded [BUG-084](others/bug-log.md#bug-084-windows-application-control-blocks-osmium-during-pipeline-verification) and the [alignment evidence](evaluations/phase-36-automatic-plan-alignment-audit.md). No application/schema/dependency/security-policy changes. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Automatic pipeline plan reconciliation (October 3, 2026)

- [x] Reconciled the architecture, active task plan, publication/frontend plan, spatial integration plan and feature/system references with the original automatic workflow: RSS/news → NLP/NER → OSM placement assisted by UP NOAH vectors and matching Pasig DRRMO history → automatic eligible map alerts/zones. Staff review remains an exception/correction path. The next delivery bundle connects runtime placement and lifecycle contracts, with F5/F6 exception controls and F7 commuter visibility developed alongside each other after shared contracts are available. This records a documentation correction, not completed automatic integration or release acceptance; application code and database schemas were unchanged. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: F4b durable discovery and fallback history (October 3, 2026)

- [x] After explicit schema approval, added four normalized telemetry tables and revision `c5a7e9d2104f`, durable staff/collector discovery feed outcomes and fallback attempt/lead metadata. Staff history APIs and responsive Pipeline sections provide pagination, read-only refresh, safe links, explicit empty/error/retry and interrupted outcomes. Start records survive worker/finalization failure; conditional finalization and atomic lead commits prevent duplicate/replaced outcomes. Captured fallback inputs remain consistent across concurrent article revisions. Fresh PostgreSQL migration round-trip and local upgrade succeed; original evidence preserved. All 214 news regressions, four PostgreSQL queue cases, one migration round-trip, TypeScript and scoped ESLint pass. Desktop/mobile fixture cases prepared without browser execution. No dependencies added; production rollout, manual acceptance and publication-delay contract remain open. Next: durable review/publication backend checkpoint before F5–F7. See [verification](evaluations/phase-36-f4b-monitoring-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: F4b saved pipeline monitoring (October 3, 2026)

- Verification: all 53 focused news backend regression tests pass; full frontend TypeScript and scoped ESLint pass. Sandbox temporary-folder permission failures were resolved by running the same suite with normal temporary-folder access. No browser/dev server execution; developer visual acceptance remains pending.

- [x] Added staff-protected GET /monitoring with SQL body aggregates, newest extraction counts and ten current retrieval issues, without bodies/result payloads. Sources & feeds adds a lazy responsive Pipeline tab, GET-only refresh and visible empty/error/retry states. Access controls, newer-failure precedence, zero/bounded datasets and sanitized 503 are tested. TypeScript and scoped ESLint pass; manual visual acceptance remains pending. No dependency/model/migration change. Discovery/fallback history requires the [storage proposal](plans/news-monitoring-telemetry-plan.md) approval; alert delay awaits publication records. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: News frontend delivery checkpoint (October 3, 2026)

- [x] Audited the completed news reading and source-monitoring changes against the task plan, component/API reference, dependency manifests and migration record before the requested roi-branch push. Remote roi-branch matches the local baseline; no incoming merge is needed. Reran 49 focused backend tests, full frontend TypeScript and news/shared-component/test ESLint: all pass with existing dependency/image warnings. The initial pytest attempt hit sandbox temporary-directory access; the retry passed with normal access. Documentation now consistently records F3 design acceptance, F4a implementation and remaining manual/F4b work. No new dependency, model or migration; no browser or development server started. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: F3 design acceptance and F4a source/feed monitoring (October 3, 2026)

- [x] The developer accepted the revised news design and authorized the next task. Recorded that the recent reading/modal refinements belonged to F3, then implemented F4a Sources & feeds on the same page. The shared drawer has Publishers / Feed checks tabs, existing protected GET source/configuration and checkpoint reads, enabled/source-verification fields, saved last-check/success/error dates, visible errors/retry/empty states and read-only refresh. No backend/model/migration/dependency changes or live probe/collection calls. TypeScript and changed-file lint pass; mixed-success/error, unsafe-link, lazy-feed, retry, empty, narrow/landscape and GET-only fixture cases were added without browser execution. Full manual checks and F4b discovery/fallback/delay telemetry remain pending; the durable backend checkpoint still precedes F5–F7. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Administrator-focused source and history inspection (October 3, 2026)

- [x] Applied primary/secondary content separation after researching NN/g progressive disclosure and GOV.UK optional details guidance. Source Article shows the captured text directly, with concise metadata and a clear publisher link. History is a secondary status/date/count timeline; View details opens full-width saved record inspection with Mentions / Article / Technical tabs. Back preserves reader/history scroll, mobile pane choice and opener focus. Reuses shared dialog, panels, timeline, tabs and buttons; no nested modal, new dependency or backend/schema change. Full TypeScript and changed-file lint pass. Existing fixtures now cover older record provenance, inspection tabs and Back/focus restoration without executing browsers. Manual desktop/mobile acceptance remains with the developer. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Source Article reader refinement (October 3, 2026)

- [x] Refined the Source Article layout from developer screenshot feedback: larger reading column, compact publication/save metadata, quieter shared underline tabs and full text open by default. The narrower history sidebar has a sticky heading, concise record actions and compact location summaries with expandable supporting sentences. Current article text is not repeated in history; older captured versions remain available. Mobile retains Article/Processing history switching and 44px actions. TypeScript and changed-file lint pass; existing fixtures updated without browser execution. Frontend only; backend/extraction work and manual visual acceptance remain separate. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: News Info frontend layout refinement (October 2, 2026)

- [x] Reused Flood History's timeline pattern through shared RecordTimeline, now used by both features. News Info uses a wide shared dialog with independently scrolling article/history panes inside Source Article on desktop and Article/Processing history switching within that tab on mobile. Flood Details shows only flood facts and evidence. One extraction record opens at a time; extracted locations, captured text and technical metadata stay expandable. Collection inspection retains More details. TypeScript and changed-file lint pass; browser fixtures are updated without execution. Developer manual desktop/mobile acceptance remains pending. Backend, database and extraction behavior were not changed or rerun for this frontend-only refinement. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Unified flood-location reading design (October 2, 2026)

- [x] Implemented the developer-finalized single list with source-specific intersection/segment cards, two Info tabs (Flood Details / Source Article), Collection status drawer and processing history under More details. Reuses shared facts, tabs, forms, dialog focus behavior and Spatial Operations metric styling; mobile and desktop layouts are implemented. Failed/empty/questionable articles remain accessible without a second main article list. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added protected read-only collection monitoring and SQL newest-run/readability gates. Older results stay in immutable history; a failed newest attempt cannot show an older success as current. Forty-nine backend tests, TypeScript/lint, read-only PostgreSQL summary agreement and seven PostgreSQL predicate cases pass. Local Philstar reads retain the specific NS Amoranto/Don Jose intersection, 37-inch depth and separate 4:30 PM flood / 5:03 PM publication / October 2 save clocks. Zero stored writes, new dependencies, model/migration changes or public/routing activation. No browser or development server was started; developer manual desktop/mobile acceptance remains pending. Remaining F4 work is feed/source health. See [verification](evaluations/phase-36-f3-result-browsing-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: News reading clarity revision (October 2, 2026)

- [x] Renamed visible tabs to News Articles/Flood Locations and clarified one story versus one location mention. Simplified article cards and collapsed filters/full text/technical details. Info opens location, water level, source flood time and article publication directly, using shared `FloodLocationSummary`, `RecordDetailsDialog` and the same `FloodDetailMetric` now used by Spatial Operations' report modal. Article details retain grouped locations and extraction history with compact facts. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Backend-derived summaries preserve unknown clocks/depths, source qualifiers and forecast/negation/historical distinctions. Forty-one focused backend tests, TypeScript and changed-file lint pass; actual historical PostgreSQL summaries agree between article and result reads with zero writes. The NS Amoranto sample distinguishes 4:30 PM flood observation from 5:03 PM article publication. No schema definition, dependency, production or public-state change. No browser or development server was started; updated Articles/Flood Locations still await developer desktop/mobile manual acceptance. See [verification](evaluations/phase-36-f3-result-browsing-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Priority 5 F3 result browser implementation (October 2, 2026)

- [x] Implemented read-only Results cards, server search/publisher/condition/placement filters, timestamp ordering and pagination. Result Details shows one saved claim with its immutable evidence and provenance; publication/zone/review outcomes stay explicitly unavailable. Shared UI/admin styling and responsive dialog code preserve list context. Identity uses saved run plus claim ordinal without a schema definition change. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Backend result/article/extraction checks, actual local PostgreSQL-backed staff reads and direct local HTTP checks pass; full TypeScript and new news-file lint pass. The local historical sample returns 28 separate claims over three pages, with zero SQL writes during verification. The developer requested no browser checks for F3; desktop/mobile manual UI acceptance remains pending. Updated browser fixtures without executing them. No production rollout, dependency addition, public-state write or routing activation. F4 Overview/Sources is the next implementation stage. See [verification and manual checklist](evaluations/phase-36-f3-result-browsing-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Priority 5 F2 saved article browser (October 2, 2026)

- [x] Connected `/admin/news` Articles to new protected, server-filtered/ordered/paginated reads over existing evidence tables. Added shared-component cards and Source/Extracted Facts/Processing History details, immutable capture/run selection, Philippine times, explicit missing/error states and list/page/scroll/focus restoration. Overview, Results and Sources remain later stages; no review/publication write controls were added. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Thirty-three focused backend checks, ten article browser checks, full TypeScript and new-file lint pass. The actual September 9 Philstar capture first passed isolated SQLite/response replay, then was saved as local PostgreSQL article #3 with a completed run containing 28 candidate claims, not verified flood zones. Two live authenticated desktop/mobile checks verified the actual article endpoints and all detail tabs without mocked news responses. Recovered Docker/PostgreSQL by preserving/recreating inaccessible socket directories (BUG-081 resolved), then applied existing migration `f29b6c8d104e` with explicit developer approval. No production rollout, model/migration definition change, dependency addition or public-state write. F3 Results is next. See [verification](evaluations/phase-36-f2-article-browsing-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Priority 5 F1 News Intelligence foundation (October 2, 2026)

- [x] Implemented the local `/admin/news` route and four-tab feature page using shared Card/CardContent/CardTitle, Tabs, TabContentPanel, Button and Skeleton. Reused Flood History/Moderation Center styling; added route loading/error states, News Intelligence navigation, current-page names, keyboard sidebar expansion and a tap-operated mobile menu. Responsive admin padding supports narrow screens. All tab bodies explicitly state unavailable capabilities; no article/result/publication data is invented. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Full TypeScript check and lint of new route/feature/test files pass. Playwright checks cover tab switching, keyboard activation, map navigation/return, mobile menu/Escape/selection, narrow/landscape overflow and existing non-staff redirects with mocked API/session responses. Desktop/mobile screenshots were inspected. Three existing AdminLayout lint errors (mount effect and two `any` casts) were confirmed in HEAD; this change adjusts its padding only. No backend/schema/dependency changes or production rollout. F2 article browsing remains next. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Priority 5 planning review (October 2, 2026)

- [x] Checked the phased roadmap against the referenced Review article pipeline progress chat and retained its accepted interface. Corrected the next-step wording: F1 is the first build stage; the former F0 layout/API checklist belongs within relevant implementation stages. Frontend direction and delivery breakdown are planned; outstanding wireframes and lifecycle contracts remain unverified prerequisites. No application code changed; implementation remains paused. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Divided the [frontend plan](plans/news-publication-review-frontend-plan.md#7-frontend-delivery-phases-and-acceptance) into F0–F8: wireframes/contracts, page/navigation, Articles, Results, Overview/Sources, Needs Review, staff decisions, public alerts and integration verification. Each stage has prerequisites and desktop/mobile acceptance; durable backend contracts gate review/public functionality. This delivers the phased roadmap only. All implementation stages remain pending and coding remains paused. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Recorded the accepted News Intelligence card-list/detail-window design using Flood History's familiar View interaction. Articles opens Source/Extracted Facts/Processing History; Results opens one claim's evidence/outcome. Closing preserves list context, with desktop/mobile accessibility and error states included in planned wireframe checks. Verification remains in Needs Review. Documentation only; implementation stays paused. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Recorded the developer's accepted mixed-source Spatial Operations interface: Needs Review/Active Zones, source filters All/User Reports/News Claims, and in-place verification with Next item. Updated the proposed News Intelligence page to monitoring and read-only Results inspection. This is completed plan synchronization, not implemented frontend/backend or schema approval; coding remains paused. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

- [x] Compared official admin navigation, labeling, investigation and map-operations patterns. The [research recommendation](plans/news-publication-review-frontend-plan.md#9-admin-grouping-research-and-revised-recommendation) is a dedicated News Intelligence page, contextual map review with existing Pending Reports/Active Zones, and commuter alert presentation. This is completed research, not developer acceptance or implemented UI. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

- [x] Reviewed task/design/agent boundaries and the existing moderation/spatial/map architecture; drafted the [Priority 5 lifecycle and frontend plan](plans/news-publication-review-frontend-plan.md). Reconciled older current-status notes with deployed extraction and OSM evidence. This records completion of a planning draft only: publication, staff claim decisions, corrections, expiry and frontend implementation remain open, and coding is paused at the developer's request. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Deployed article-to-OSM placement connection (October 2, 2026)

- [x] Shared article processing now persists source-identified bounded centerline/candidate evidence from a bundled NCR OSM snapshot, with explicit ambiguity and coverage gaps. Full catalog hashes version the pipeline; existing inputs/results are preserved. Broad road names cannot choose a flood extent or close a road. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Verified the corrected Linux runtime after adding the native reader's `libexpat1` dependency: ten map-aware backlog results persist, repeat creates no work, public rows stay unchanged, and the actual historical GMA narrative matches an 86.2 m span. All 50 backlog placement outcomes remain unresolved; no routing activation is claimed. The focused broad suite passes 135 tests, with a final 55-test rerun. See [verification](evaluations/phase-36-reusable-road-match-check.md#production-release-verification). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Production rules extraction release (October 2, 2026)

- [x] Released the approved queue after production migration `f29b6c8d104e`; API health/database/authentication checks pass and the collector now runs `--discover --process --limit 50`. Bundled administrative/history references have matching production/development checksums. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Processed 10 existing RSS-linked article bodies into 10 durable results with 50 source-linked candidate claims. Repeat processing creates no duplicates; public reports/events/zones remain unchanged. All artifacts pass typed validation and evidence linkage. Twenty-eight focused tests pass. Fresh current-article discovery/matching, verified road geometry, alerts, corrections, and routing integration remain open. See [release evidence](evaluations/phase-36-open-article-fallback-check.md#production-extraction-release--october-2). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Additional database compatibility checks before requested push (October 2, 2026)

- [x] Verified a fresh full migration and fourteen additional queue/domain/storage API cases in guarded disposable PostgreSQL/PostGIS, bringing distinct validated cases to 385. Existing flood-event lifecycle/metrics/analytics, profile/password, OTP, archive, saved-place, and login-limit checks pass. A seeded sequence error was corrected only in the disposable test setup before the profile rerun. No runtime/test source changes. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Verified no remote roi-branch divergence, no deleted files/definitions or frontend edits, no obvious added secret markers, and existing dependency coverage. Cloud Build's trigger targets main only and its pipeline waits for migrations. Cleaned the disposable database/proxy; production untouched. A 100% guarantee cannot be claimed; thirteen legacy/live cases and release acceptance remain open. See [pre-push evidence](evaluations/phase-36-open-article-fallback-check.md#additional-pre-push-verification--october-2). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: New-branch compatibility review (October 2, 2026)

- [x] Compared the new branch's working changes against roi-branch, local main, and fetched remote main without modifying their commit histories. No removed definitions/endpoints/schema properties, deleted files, or frontend changes. All 149 roi-branch operations retain their contracts; three news operations/two approved tables are additive. Old local-main differences are earlier delivered work. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Validated 371 distinct backend cases across news plus existing routing, road validation, authorization/privacy/feed, retention, and geocoding controls. Four current PostgreSQL cases skipped; twenty-three database/live legacy cases remain unexecuted. A cleaner temporary-folder setup error cleared on permitted retry. Documented the pre-existing test isolation gap as BUG-076 and retained the migration-before-release gate. No runtime fixes, merge, commit, push, deployment, or production data change. See [review](evaluations/phase-36-open-article-fallback-check.md#branch-compatibility-review--october-2). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Approved Priority 3 durable extraction (October 2, 2026)

- [x] Implemented the approved two-table migration, immutable canonical input snapshots, typed rules-only results, idempotent enqueue, and bounded leased retries. RSS/manual revisions retain prior evidence; saved work survives restart and unchanged-feed responses. Staff status/processing APIs and collector processing options are protected and bounded. The combined regression run passed 223 tests; the final 17-test focused rerun adds one manual revision/storage-failure case. Public moderation and flood report/event/zone writes remain untouched. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Verified migration apply/rollback/apply on disposable Cloud SQL PostgreSQL/PostGIS and four real database checks for immutable inputs, constraints, concurrent enqueue/claims, stale lease ownership, restart, and persisted rules output. Seventeen focused worker/API checks pass, including manual revision idempotency and safe storage failures. The disposable database was deleted and its local proxy stopped. No new runtime dependency or paid instance, production schema/job change, push, or deployment. Release/live collected-body acceptance remains pending; Priority 2 live positive matching stays open. See [evaluation](evaluations/phase-36-open-article-fallback-check.md#priority-3-durable-extraction--october-2). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Continued Priority 2 acceptance and flood-control false-positive repair (October 2, 2026)

- [x] Found and repaired policy/project text becoming active flood evidence. All 13 focused cases and the final **207 combined regressions pass**, including mixed actual flood reports, explicit gauges, project measurements, clause separation, original offsets, and RSS/body shortlisting. Existing deprecation warning only; whitespace checks pass. No dependency/schema/public-state change, push, or deployment. See [continued evaluation](evaluations/phase-36-open-article-fallback-check.md#continued-priority-2-acceptance--october-2) and [BUG-075](others/bug-log.md#bug-075-flood-control-discussions-were-classified-as-active-flooding). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Rechecked all six live feeds before/after the repair: HTTP 200, 95 parsed entries each, no eligible candidates or extractions. A real manually selected Philstar administrative body (2,439 characters) has no qualifying flood observation after repair. The first publisher-body command failed at approval review; account status showed ordinary usage available and one same-process retry was approved and succeeded. No policy bypass or change. Live positive matching remains unverified; Priority 2 stays active and Priority 3 deferred. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Priority 2 acceptance closeout and sequencing correction (October 2, 2026)

- [x] Assessed the existing discovery/freshness/observation-comparison fixes against Priority 2 acceptance. The latest controlled suite passes 152 tests; live feed parsing succeeded but no current eligible candidate exercised live incident matching. Local checks pass; live matching/rollout remains unverified. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Corrected the active task after the developer clarified that “proceed” meant finishing Priority 2 assessment first. Priority 3 previews/storage design were prepared prematurely and remain local/deferred; no models/migrations changed and no schema approval is required for this closeout. Durable grouping/retry and actual zone updates remain later work. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Priority 3 saved-extraction preparation and scope correction (October 2, 2026)

- [x] Corrected the broad Priority 2 hold: local freshness/comparison repairs are validated; durable grouping, processing retry, and zone updates are later contracts. Live update verification remains open without blocking authorized preparation. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Shared saved/collected rules-only extraction now returns real saved IDs, source timestamps, stable input identity, and typed claims through staff preview and bounded CLI reading. Errors remain visible and SQL/evidence/review/public state stays unchanged. **152 combined tests pass**, with the existing deprecation warning. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Prepared the immutable-version/extraction-run schema proposal. No model, migration, dependency, deployed job configuration, push, or deployment changed; persistence and processing retries await explicit schema approval. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Observation-ordered update proposals — Priority 2 follow-up (October 2, 2026)

- [x] Final combined discovery, open-search, ingestion-safety, and hybrid-extraction regression suite: **141 passed**, with the existing `python_multipart` deprecation warning. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Replaced blanket depth/clearance conflicts with per-city/road observation-order proposals: later increases, decreases, and clearance; older or stale evidence; same-time disagreement; segment differences; incomplete timestamps; and possible recurrence after clearance. Different publishers and shared names still do not verify one incident. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Prefer newer feed coverage, refresh same-URL publication revisions, preserve successful body/date on blocked refresh, reject older feed overwrites, and block retained errored bodies from activation. The read-only live rerun parsed all six feeds (95 entries) with no current flood candidates. Priority 2 live acceptance remains open; Priority 3 is held. No dependency, model, migration, push, or deployment. See the [evaluation](evaluations/phase-36-open-article-fallback-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Free open-index leads for blocked publisher articles (October 1, 2026)
- [x] Final Priority 2 regression suite passes 123 tests across discovery, fallback, ingestion safety, and hybrid extraction; whitespace checks pass. Improved discovery and alternate event-review behavior remain local, with live current-candidate validation pending. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added Priority 2 discovery improvements: bounded body-location probes for unknown-scope flood headlines, extracted local-claim checks, visible run notices, future-date rejection, and accepted/rejected duplicate persistence. Alternate review now compares city-qualified roads, specific places, dates, depth/status, and copied body fingerprints without claiming event verification or independent confirmation. New controlled tests pass; all six feeds parsed live but contained no matching current flood candidate. Priority 1 live blocked-page recovery remains open. No dependency/schema or deployed service change. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Final combined discovery, fallback, ingestion-safety, and hybrid-extraction suite passes 107 tests; whitespace checks pass. Verified bounded HTML-entity compatibility, custom-entity rejection, controlled RSS-to-claims processing, visible blocked-body/per-candidate errors, no DB/auditor calls, and honest no-candidate outcomes. Production article processing remains disconnected. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Restored Inquirer RSS parsing by translating known HTML character references to numeric XML references while retaining CDATA/XML escaping and rejecting custom entities. All six feeds parsed live (95 entries total). Added read-only collection-to-rules extraction in the existing collector script, with controlled feed/body/claim tests and explicit no-candidate/error outcomes. A historical manually supplied Philstar body produced 29 review claims; the live feed snapshot had no matching current candidates. Headless Chrome still received the Inquirer challenge, and GDELT still returned 429. No production integration or new dependencies. See the [evaluation](evaluations/phase-36-open-article-fallback-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Diagnosed local and Cloud Run TLS taking about 8–11 seconds, exceeding the staff route's 3-second connect budget. Added GDELT-specific 15-second connect / 20-second read limits, optional place/date search, recent approved-feed fallback independent of index availability, and read-only network diagnostics in the existing collector script. The combined suite passes 87 tests. Live GDELT still returned 429; five feeds parsed but contained no matching recent Metro Manila flood lead. A previously supplied Philstar body was retrieved (8,933 characters), without automatic discovery or same-event verification. Changes are local, with no new dependency, schema, or deployed service. See the [evaluation](evaluations/phase-36-open-article-fallback-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added process-wide GDELT pacing, bounded successful-query caching, exponential cooldowns, and Retry-After handling. The final focused suite passes 70 tests, including concurrency, expiry, throttling, provider dates, recovery, and API wait metadata. Live HTTP 429 plus a repeat produced exactly one outbound request; a later retry timed out, so provider success remains unverified. No new dependency or schema. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Verified retrieval-option API behavior and ingestion safety offline; repaired malformed provider URLs and surfaced HTTP status codes while stopping immediate fallback searches after provider errors. Live GDELT returned 429, while the GMA feed control parsed 15 entries. Live fallback success remains unverified. See the [evaluation](evaluations/phase-36-open-article-fallback-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added optional bounded retrieval of three approved alternate publisher articles, retaining independent provenance and visible errors. Bodies require same-event review; no database schema or dependency changes. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added a staff-only backend lookup for incomplete RSS publisher candidates using the free public GDELT DOC index. It searches by article title, then RSS phrase if needed, and returns bounded source-labeled URLs and index-seen times without treating them as full article text or publishing any flood data. It needs no payment card or API key. Live GDELT reachability from this development network could not be verified; scheduled fallback remains open. Focused offline tests pass. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36 Gates 1–3 acceptance checks (September 30, 2026)
- [x] Closed the pre-Gate-4 article, activation-safety, and location-prediction checks. Blocked/incomplete Inquirer and Rappler articles remain incomplete leads; 10 activation failure cases plus negated/forecast/subsided paths prove no public flood writes; generic landmark scope and the 17-city OSM/NOAH coverage audit are recorded. A real historical GMA Pasig claim was traced through six bounded road candidates, place-matched DRRMO rows, and all three NOAH scenarios, and a separate Quezon City span trace covers a non-Pasig example. The current article remains ineligible for activation and no report, alert, zone, or route was written. Focused suite: 122 passed. Gate 4 has not started. See [task plan](task_plan.md), [article context evaluation](evaluations/phase-36-article-road-context-check.md), and [spatial coverage audit](evaluations/phase-36-metro-spatial-coverage-audit.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Phase 36: Article and Pasig history road context (September 30, 2026)
- [x] Added a read-only matcher from extracted article road/cross-street/span context and row-level Pasig DRRMO records to bounded OSM sections. A constructed Bernal Street claim narrows 25 C. Raymundo sections to two; three actual Rosario/Bernal CSV rows support both, while ungrounded rows remain visible. Non-Pasig claims do not use the Pasig history. The local NOAH audit accepts this context and all three scenarios; 21 focused tests pass. This is not yet a live RSS geometry provider, alert, zone, or routing write. See the [context evaluation](evaluations/phase-36-article-road-context-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Flood report media attachment repair (September 30, 2026)
- [x] Copied picked files before clearing the native input, made the picker directly tappable in the mobile sheet, and stopped the backend from creating a report after an evidence upload fails. Desktop and mobile viewport browser regressions pass (2/2); backend failure-path test passes (1/1). Physical-device picker confirmation remains open. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Online route alternatives and pedestrian costing (September 30, 2026)
- [x] Unified Valhalla and ORS fastest/shortest candidate passes under the existing flood policy. The ranker now fills four distinct eligible cards when available, while Walking keeps pedestrian graph access without a vehicle heading. Focused routing tests pass 24/24; live provider behavior and specific street access remain to be verified. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### Metro Manila NOAH hazard display on `/map` (September 29, 2026)
- [x] Exported three lightweight transparent display images from the locally verified Metro Manila NOAH polygons, retaining class colors and source-ring holes at image resolution. Added a 3D-only desktop scenario control above Saved Places and a short mobile drawer under the `+` menu. Entering 3D leaves hazards hidden until 5-, 25-, or 100-year selection; 2D clears the selection. A legend distinguishes modeled hazard from current flooding, and the visual layer remains independent of active zones and routing. TypeScript and production build pass; local desktop/mobile browser checks covered 3D selection, all three images, style switching, 2D reset, and an image-load error toast. ([@roicambe](https://github.com/roicambe) (Roi Cambe))


### Phase 36: Read-only full-article and road-match checks (September 28–29, 2026)
- [x] Split C. Raymundo Avenue into 25 read-only OSM sections between distinct mapped cross streets inside the repository's Pasig polygon; one has an alternative carriageway. The NOAH ranking still finds multiple equally supported sections, so a road-name-only report remains unresolved instead of arbitrarily closing one. The new network audit command, nine matcher tests, and six ranking tests pass. No public map or routing write. See the [NOAH ranking evaluation](evaluations/phase-36-noah-road-ranking-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added read-only NOAH ranking of bounded OSM centerlines, recording exact modeled overlap by scenario and hazard class. The GMA Santo Domingo location stays a single predicted candidate; C. Raymundo's Bernal audit window ranks ahead of Mercedes by modeled overlap but neither arbitrary 100 m window is selected as a bounded prediction. Six focused ranking tests and both local audit commands passed. No public map or routing write. See the [NOAH ranking evaluation](evaluations/phase-36-noah-road-ranking-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added a reusable read-only article-to-OSM road matcher for explicit cross-street spans, aliases, city/barangay containment, and alternative-carriageway rejection. The existing audit now uses it and reproduces the Santo Domingo 86.2 m result; the PNA Araneta span remains unresolved at the OSM junction check. Eleven focused tests pass. No current flood extent, report, zone, or routing decision was created. See the [match check](evaluations/phase-36-reusable-road-match-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added a read-only article-to-OSM/NOAH span audit for the August GMA Sto. Domingo Avenue report. The article's Atok-to-Calamba phrase selects one approximately 86.2 m OSM centerline path inside OSM's Quezon City administrative relation; all three NOAH scenarios intersect it at modeled `Var=3`. The script fails on ambiguous, disconnected, or out-of-city evidence; six offline tests pass. This is a historical research candidate, not a current flood extent or active zone. See the [evaluation](evaluations/phase-36-sto-domingo-road-span-audit.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Expanded the article-body sample to the first ten feed positions per publisher. Fifty accessible article responses were checked; the Rappler rolling article remains an incomplete lead and 49 responses supplied text. Ten Inquirer article requests returned a Cloudflare challenge. Rappler still links to another page after `?next=32`, so ordinary bounded article assembly is not appropriate for that rolling format. See the [publisher audit](evaluations/phase-36-publisher-body-and-pagination-audit.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Added a bounded Asia/Manila observation-clock resolver for explicit `as of` flood evidence. It anchors a clock to a timezone-aware article publication within 12 hours, handles midnight rollover, and leaves report-only or date-ambiguous wording unresolved. A live August GMA replay resolved named road observation clocks while leaving an explicitly dated embedded post unresolved; no zone was activated. The focused suite passes 77/77. See [source check](evaluations/phase-36-three-article-check.md) and [BUG-063](others/bug-log.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Expanded the publisher audit to five current entries per source. A Rappler rolling-updates page had a `?next=2` continuation but was previously accepted from page one; it is now an incomplete lead. The five Inquirer article pages still returned Cloudflare challenges. Repaired the fixed PNA historical replay domain mapping without enabling its feed, but both PNA article requests now return HTTP 500, so their older 16/16 and 8/8 site results were not freshly revalidated. See [publisher audit](evaluations/phase-36-publisher-body-and-pagination-audit.md) and [BUG-066](others/bug-log.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Pruned the runtime RSS registry from 51 research entries to six verified feeds, so disabled candidates cannot be selected through the default collector, staff source list, or `--all-leads` probe. The 50 Feedspot names remain documented for research. All six current feed probes returned HTTP 200, and three focused source/API tests passed. Inquirer remains enabled because its RSS works; its article-page Cloudflare challenge still produces an incomplete lead. Updated the source API contract test and discovery plan accordingly. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Audited the first two RSS articles from each enabled publisher. Repaired Philstar's missing body extraction, narrowed Rappler and BusinessWorld to their article containers, excluded sampled related-story widgets, and rejected common same-article page-two links without `rel=next`. Ten sampled pages returned bodies; two Inquirer articles returned a Cloudflare challenge while its RSS feed stayed available. The historical 51-site check still matched all cited sites. This is a sampled publisher check, not proof of universal article completeness; see [audit](evaluations/phase-36-publisher-body-and-pagination-audit.md) and [BUG-064](others/bug-log.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Replayed both GMA pages after excluding their related-story widget. The August 29 page yielded 27 review-only claims covering seven named sites; the July 10 page yielded 26 claims across the expected Metro Manila cities. Repaired July list road/city matches, grouped 4:35 and 2:50 clocks, list-to-narrative context leakage, and the España/Espana clearing pair. The embedded August `Maynila` road report kept Jose Abad Santos as a crossing street in Manila. Both newer-first clearing pairs remained review-only/suppressed. At this checkpoint the publisher-backed 51-site check matched 27/27, 16/16, and 8/8, and 64 focused backend tests passed. Observation-clock resolution and the single read-only geometry candidate were evaluated later, as recorded above. See [source evaluation](evaluations/phase-36-three-article-check.md) and [BUG-065](others/bug-log.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Initial July 10 GMA replay returned 3,218 parsed characters and 25 claims, showing a newer-first clearing update. Those initial road/city and grouped-time gaps were repaired in the later replay above; this was the diagnostic checkpoint. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Initial August 29 GMA replay fetched 3,750 parsed characters, including a related-story widget, and returned 28 review-only claims. It identified the false `2 in` depth from “Valley 2 in Barangay,” missed San Antonio Valley 2, Zapote Junction, and Alido Bridge, vehicle restrictions, clock leakage, and incidental weather/credit lines. The later replay above removed the widget and retested these cases. Inquirer returned HTTP 403, so its full-body evaluation remains open. See [GMA source check](evaluations/phase-36-three-article-check.md) and [BUG-065](others/bug-log.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Removed a silent 30,000-character cut in article text retrieval: a long parsed page is now kept whole up to 100,000 characters, then rejected with an explicit incomplete-body error rather than partially extracted. HTML `rel=next` continuation links also make the article incomplete until all pages can be fetched. Three regressions pass, the real three-article fetch/extraction check still matches all 51 cited sites, and the focused backend suite passes 68/68. Publisher-specific pagination without `rel=next` remains open. See [BUG-064](others/bug-log.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Preserved lead photo flood-road mentions as `photo_caption_only` review claims while filtering photo credits, dateline cities, and rainfall-only places. Added a bounded-road contradiction marker and action check so a later clearing update sends an earlier active claim to staff review; metadata-only leads also cannot approve zones. After bypassing a process-only `127.0.0.1:9` proxy setting, the real publisher-backed rerun matched all 51 cited list sites (27/27, 16/16, 8/8); total claims are 29/25/9 including two review-only photo roads. Five targeted and 65 focused backend tests passed. A separate real contradictory-update article remains open; no public zone or database write was made. See [follow-up evaluation](evaluations/phase-36-new-article-service-simulation.md) and [BUG-062](others/bug-log.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Turned the three manually compared source lists into a tracked 51-site expected-facts fixture and a `--check` mode for the real, read-only article simulation. The live rerun matched all 27 Philstar, 16 PNA August 17, and eight PNA August 8 sites with their stated fields. Three new matcher tests and the focused backend suite pass 73/73. This does not establish unseen-article recall, remove incidental claims, or verify map geometry. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Repaired the missed-location cases found by comparing the three full articles with actual backend output: all 27/16/8 listed flood sites now produce a location claim with the reported road intersection, bounded phrase, or landmark. City-qualified PSGC matching, grouped and individual report times, depths, passability, stated travel direction, and later subsidence are retained where present. This remains textual extraction; no OSM/NOAH geometry was certified. Focused tests: 70/70 passed. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Ran three new historical Metro Manila articles through the existing publisher-domain fetcher, deterministic extraction, PSGC/location ranking, and action evaluator without interface, database, Gemini, or live map writes. The initial diagnostic produced 24, 34, and 18 total claims; the corrected results and per-site comparison are in the [simulation report](evaluations/phase-36-new-article-service-simulation.md). None auto-activated. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Preserved HTML list boundaries, scoped city/barangay/passability headings, prevented `Metro Manila` from resolving to the City of Manila, and removed arbitrary whole-article city fallback in geometry ranking. Regression tests were added for these cases. Remaining full-article errors are tracked in Phase 36 Gate 1 and Gate 3. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Capstone Phase 38: Interactive MMDA Flood Gauge Visual & Vehicle Clearance Rules (🟢 COMPLETED)
- [x] **Interactive Split-View MMDA Flood Gauge with Reference Human Silhouette & Dual-Screen Support** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - **Interactive Human Silhouette (`FloodGaugeSilhouette.tsx`)**:
    - Engineered inline SVG modern commuter silhouette calibrated to 165 cm (5'5") reference height according to DOST-FNRI adult Filipino standards and MMDA flood classifications.
    - Implemented flat soles firmly planted on the ground baseline ($y=415.0$), eliminating floating/awkward foot contours, with a comfortable, natural, and comfortably bulky build.
    - Calibrated 50/50 Golden Ratio anatomical inseam ($y=230.0$), achieving balanced thigh/calf proportions and natural mid-thigh relaxed arm hang.
    - Features Framer Motion spring physics (`stiffness: 120, damping: 18`) to smoothly raise and lower water fill clipped to the human silhouette (`clipPath`).
    - Upgraded high-visibility depth callout badge ($120\text{px} \times 44\text{px}$, bold 12.5px title, 11px measurement, subtle drop shadow) positioned clear of the figure, paired with a prominent centimeter depth ruler (0 to 165 cm) with active bold ticks and DOST-FNRI calibration badge.
  - **Interactive Depth & Vehicle Clearance Table (`FloodGaugeTable.tsx`)**:
    - Interactive 8-level MMDA depth table mapping each canonical level (`gutter`, `half-knee`, `half-tire`, `knee`, `tires`, `waist`, `chest`, `neck`) to severity color tokens and dual-unit measurements (`inches` and `meters`).
    - Features expandable vehicle accessibility badges (`PATV` Passable to All, `NPLV` Heavy Only, `NPATV` Impassable) revealing detailed vehicle routing clearance guidelines on hover (desktop) or tap (mobile).
  - **Split Container & Dual-Screen Optimization (`FloodGauge.tsx`, `LandingView.tsx`)**:
    - Replaced static 4-card `FloodLegend` on Landing Page (`/`) with unified split-view `FloodGauge` (7/5 grid on desktop, single-column stacked on mobile).
    - Added mobile-specific interaction handling: tapping a depth level automatically smooth-scrolls (`scrollIntoView`) the silhouette into view on smaller viewports.
  - **Verification**: Complete Next.js production build (`npm run build`) succeeded with 0 TypeScript/lint errors across 25 routes.

---

### Capstone Phase 37: Official MMDA Flood Depth Measurement Integration (🟢 COMPLETED)
- [x] **Deterministic MMDA Flood Depth Single-Source-of-Truth & Cross-Platform Measurement Integration** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - **Architecture & 3NF Compliance**: Implemented Option 1 (Single-Source-of-Truth in Backend & Presentation Shell) maintaining strict Third Normal Form (3NF) without modifying database schemas or Alembic migrations.
  - **Backend Foundation (`backend/app/services/flood_depth.py`, `backend/app/models/report.py`, `backend/app/schemas/report.py`, `backend/app/schemas/flood_event.py`)**:
    - Created authoritative registry mapping all 8 canonical MMDA depth levels (`gutter`, `half-knee`, `half-tire`, `knee`, `tires`, `waist`, `chest`, `neck`) to exact metric meters/centimeters and imperial inches (`0.20m / 8"`, `0.28m / 11"`, `0.33m / 13"`, `0.48m / 19"`, `0.66m / 26"`, `1.00m / 39"`, `1.22m / 48"`, `1.52m / 60"`).
    - Added `@property` getters on `FloodReport`, `FloodAvoidanceZone`, and `FloodEvent` for `depth_meters`, `depth_inches`, and `depth_formatted`.
    - Auto-populated Pydantic response schemas (`FloodReportBase`, `FloodReportResponse`, `ZoneContributorResponse`, `FloodAvoidanceZoneResponse`, `NearbyZoneResponse`, `FloodEventResponse`) with depth measurement fields via `@model_validator(mode="after")`.
    - Enriched contributor metadata dictionaries in `FloodAvoidanceZone` with depth measurements.
    - Verified backend with 7/7 unit tests in `test_flood_depth_contract.py` (32/32 backend routing/extraction tests passing).
  - **Frontend Centralization (`frontend/src/lib/floodDepth.ts`)**:
    - Created client single-source-of-truth utility exporting `FLOOD_DEPTH_SPECS`, `FLOOD_DEPTH_OPTIONS`, `getFloodDepthSpec()`, and `formatFloodDepth()` with both verbose (`19" (0.48m) • Knee`) and compact (`19" (0.48m) • Knee`) display modes.
  - **Comprehensive UI/Admin Surface Upgrades**:
    - **Landing Page (`FloodLegend.tsx`)**: Upgraded vehicle clearance rules legend with dual-unit measurements (meters and inches) across Low, Medium, High, and Extreme hazard tiers.
    - **Hazard Reporting (`FloodReportPanel.tsx`)**: Replaced raw depth keys with visual selector options displaying metric and imperial measurements; formatted draft queue badges.
    - **Admin Spatial Operations & Zone Modals (`ZoneDataEditorForm.tsx`)**: Integrated measurement badges into the shared zone editor form utilized by **Create Zone**, **Edit Zone**, and **Review Merge Suggestions** panels on `/admin/map`.
    - **Merge Management (`MergeWorkspacePanel.tsx`, `ReportComparisonCard.tsx`, `ReportComparisonMatrix.tsx`)**: Formatted water depth in suggestion cards, side-by-side comparison matrix, and merge finalization summary.
    - **Live Map & Layer Popups (`FloodZonePopup.tsx`)**: Formatted popup height metric and contributor report depths with physical measurements.
    - **Universal Details Modals (`FloodReportDetailsModal.tsx`, `FloodZoneDetailsModal.tsx`)**: Integrated formatted water level and estimated depth across shared report and zone modals in Moderation Center, Spatial Operations, and Archive Center.
    - **Moderation Queue & Active Panels (`FloodModerationQueue.tsx`, `PendingReportsPanel.tsx`, `ActiveZonesPanel.tsx`)**: Enhanced moderation cards, pending report items, active zone badges, and zone contributor breakdowns with compact measurement tags.
    - **Flood History Records & Modals (`FloodEventDetailModal.tsx`, `FloodEventDetailsTabs.tsx`, `FloodEventRecords.tsx`)**: Formatted peak flood depth and official zone historical water levels.
  - **Dual-Screen & Mobile/PWA Verification & Layout Optimizations**:
    - Mobile-optimized responsive 4x2 depth button grids in `ZoneDataEditorForm.tsx` and `FloodReportPanel.tsx` with responsive gaps, text-centering, leading-tight, and `whitespace-nowrap` depth descriptions preventing text clipping on narrow 360px–390px viewports.
    - Enhanced card badge wrapping in `PendingReportsPanel.tsx` and contributor metadata footer in `ActiveZonesPanel.tsx` for narrow mobile screens.
    - Verified mobile drawer mode in `FloodZonePopup.tsx` and single-column responsive modals in `FloodReportDetailsModal.tsx` and `FloodZoneDetailsModal.tsx`.
  - **Verification**: Complete Next.js production build (`npm run build`) succeeded with 0 TypeScript errors across 25 routes.

---

### Capstone Phase 36: Trusted Flood Intelligence — News Discovery & Taglish Extraction (🟡 IN PROGRESS)
- [x] **Metro Manila road extract and exact C. Raymundo junction-window overlay** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): downloaded a 60.55 MB Metro Manila OSM PBF into ignored local `data/`, identified 26 C. Raymundo ways, grounded one Bernal and two Mercedes shared junction nodes, and matched the relevant Pasig DRRMO place rows. Added a reproducible read-only script that intersects 100 m road-centerline inspection windows with original 5-/25-/100-year NOAH polygons while preserving holes and repairing invalid source rings. Bernal's roughly 199.8 m window overlaps modeled medium hazard in the 5-/25-year scenarios and high hazard in the 100-year scenario; Mercedes's roughly 208.1 m window has differing low/medium coverage. These windows are arbitrary probes, not reported flood extents or active zones; map vintage, full Metro Manila coverage, general article matching, and routing validation remain open. No Cloud SQL, collector, or public map writes. See [spatial plan](plans/lipad-noah-flood-placement.md).
- [x] **Metro Manila NOAH archive and Pasig road-overlay feasibility audit** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): downloaded only the 5-, 25-, and 100-year Metro Manila ZIPs into ignored local `data/`; verified CRC, WGS 84 polygon geometry, three `Var` classes, and sampled Pasig polygon coverage in every scenario with a reproducible read-only inspection script. A single OSM road query found 26 distinct C. Raymundo Avenue ways. Roughly 15-meter sample points on those ways intersect different NOAH classes, establishing that whole-road assumptions would be unsound. Exact intersection/landmark matching, original license and map vintage, full Metro Manila coverage, import design, and public zone activation remain open. No database or production map writes were made. See [spatial plan](plans/lipad-noah-flood-placement.md).
- [x] **DRRMO source-time audit and Gate 3 placement-plan refinement** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): inspected the original Pasig workbook, raw annual-section CSV, cleaned 726-row CSV, and current history service. Confirmed `source_year` identifies the 2020–2025 section; `source_record_no` is a row number and `Water Level (Estimated)` is depth. No event date, observation/onset/clearance clock time, coordinates, or distinct-event ID exists in those records, so current `recurrence_count` is a record count, not a verified count of separate floods. Used C. Raymundo Avenue's different barangay/landmark rows to specify a Metro Manila-first road-segment and NOAH-overlap prediction path within existing Phase 36 Gate 3 and its supporting spatial plan. NOAH archives remain uninspected, no spatial import or database change was made, and news collector/map connection remains pending.
- [x] **Automatic activation direction and NOAH source lead restored** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): corrected the temporary blanket disabled write boundary to an evidence-gated automatic path that reevaluates the claim at ingestion. The present geometry service still cannot mark a bounded segment verified, and the collector remains disconnected, so no live news zone or alert is delivered yet. Reprioritized the plan around fast source-labeled public news alerts, automatic routing zones for exact verified segments, and staff exception handling. Inspected DavFlood's UP NOAH workflow and located Metro Manila 5-/25-year archive listings in the linked dataset; Pasig coverage and license details still need file-level verification. No article simulation, database change, or deployment. Python checks pending below. See [spatial integration plan](plans/lipad-noah-flood-placement.md).
- [x] **Gate 2 activation evidence hardening, pending pytest verification** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): marked generated road and point polygons as review-only previews with offline/caller-coordinate provenance; made missing or failed external audit unconfirmed; required recent resolved observation and publication times, confirmed depth, active condition, and verified affected-segment geometry for an approval decision; removed the post-approval `0.98` assignment. `NewsAutoIngestionService` now independently reevaluates evidence before a public write, with no synthetic depth or Pasig city fallback. Added focused regression cases for missing gates and forged approval labels. Python syntax parsing passed; pytest remains unrun because the available local Python runtimes lack the package. No article simulations, Cloud SQL writes, migration, or public map changes. See [the safety contract](plans/news-activation-safety-gates.md) and [BUG-060](others/bug-log.md).
- [x] **Full Manila Bulletin reporting-body claim inventory in simulation** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): replayed the indexed August 29 article body and verified 26 named-location claims plus 11 broad barangay mentions, with separate values for impassable sites, light-vehicle closures, and passable flooded roads. Split M.H. Del Pilar across Tugatog and Tinajeros; preserved the shared 10–19-inch range without individual measurements; retained the source spelling `Santulan` as unverified against Malabon PSGC. Added a paraphrased full-body regression fixture and a Pydantic passability field; no database or public-map writes. Tests pass 22/22 focused and 41/41 across extraction, location service, and news discovery. [The source-linked check](evaluations/phase-36-three-article-check.md) records the groups and remaining geometry/date limitations.
- [x] **Developer-reviewed article extraction repair** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): corrected the Quezon City/Calamba Street collision, preserved Sto. Domingo Avenue's cross-street segment, separated Biak-na-Bato and Mauban road depths, and extracted M.H. Del Pilar plus three Malabon sites with local-area phrases. The later Malabon named-road list yields 13 place claims with a shared 10–19-inch range and no invented per-road measurement. Explicit 37-, 19-, and 26-inch values map to configured gauge keys; approximation and upper-bound qualifiers remain attached to raw evidence, while unpaired ranges and `thigh-deep` alone remain uncertain. `as of 1:12 p.m.` is an observation time and the Malabon office's 7 p.m. statement a report time; Inquirer streets have unknown observation time. Tests: 21/21 focused and 40/40 extraction/location/news discovery; the 50-item constructed set retains 100% canonical barangay/depth recall with a 96% article-level negation metric on mixed-status items. Full article semantics, RSS integration, geometry, and map publication remain open. See [the source-linked check](evaluations/phase-36-three-article-check.md) and [BUG-058](others/bug-log.md).
- [x] **Read-only 2026 publisher evidence check, test isolation, and documentation reconciliation** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): ran three short August 2026 GMA, Inquirer, and Manila Bulletin passages through the deterministic extractor without Cloud SQL writes or zone activation. It recognized some flood/depth facts but produced malformed road spans, missed city context, misresolved Calamba Street as a city, and split a `p.m.` timestamp. Results and source links are in [the three-article check](evaluations/phase-36-three-article-check.md). Isolated the staff news API test from external PostgreSQL with in-memory SQLite (`1 passed`; [BUG-059](others/bug-log.md)); [BUG-058](others/bug-log.md) tracks the extraction defects. Updated the active plan and reference documents to distinguish existing prototypes from the disconnected production collector; real-article accuracy and activation safety remain open.
- [x] **Section 1 DRRMO Historical Flood Ingestion & Section 3.5 Nationwide Place Coverage (Deterministic Rule & PSGC Grounding without ML NER)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - **Section 1 Historical DRRMO Ingestion (`pasig_historical_service.py`)**:
    - Ingested and indexed all 726 verified historical flood records (2020–2025) from `data/flooded_areas_pasig_clean.csv`, tracking 304 unique streets, 301 unique landmarks, centimeter depth ranges, year spans, and recurrence counts.
    - Wired `PasigHistoricalService` into `NationwideGeometryService`, replacing hardcoded street strings with dynamic DRRMO recurrence bonuses (+0.02 to +0.06) and explainable score rationales for top corridors (e.g. Urbano Velasco Ave, Sandoval Ave, Caruncho Ave, Ortigas Ext, C5 Road).
    - Verified with 4/4 unit tests in `backend/tests/test_pasig_historical_service.py`.
  - **Section 3.5 Nationwide Place Extraction without ML NER (`taglish_extraction_service.py`)**:
    - Expanded deterministic place extraction beyond Pasig using precompiled single-pass regex patterns: all 82 PSA Philippine provinces, chartered cities and regional hubs across Luzon, Visayas, and Mindanao, national thoroughfares (EDSA, MacArthur Highway, Colon Street, Osmeña Boulevard, etc.), dynamic `<Name> City` and administrative `City of / Lungsod ng / Bayan ng` prefixes, and nationwide prefixed barangays (`Brgy. <Name>`) grounded in `PhilippineLocationService.barangays`.
    - Enriched `ExtractedClaim` with `canonical_city`, `canonical_province`, `canonical_road`, `island_group` (Luzon, Visayas, Mindanao), and `psgc_code` via `resolve_location_hierarchy`.
    - Populated MMDA physical depth measurements (`depth_meters`, `depth_inches`, `depth_formatted`) on claims and auto-activated avoidance zones while preserving strict 3NF database architecture with zero schema alterations.
    - Verified with 16/16 unit tests in `test_taglish_extraction.py` across Luzon, Visayas, Mindanao, and Pasig corridors, while preserving 100% barangay, depth, and condition recall on the 50-item benchmark (`scripts/evaluate_taglish_extraction.py`) at 0.73 ms/item on CPU.
  - **Zero Heavy ML Dependencies**: Strictly adhered to user directive avoiding ML NER / `calamanCy` / transformer models in this phase, maintaining sub-millisecond CPU speed and zero dependency footprint.
- [x] **Section 2 Discovery Hardening: Release-Time Cloud Run Deployment, Broad Nationwide Relevance Filter, Broadcaster Investigation & Manual Staff Ingestion** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Updated `cloudbuild.yaml` release automation to deploy the built backend container image to the `lanes-news-discovery` Cloud Run job in `asia-east1`, preventing release desynchronization.
  - Enhanced `likely_philippine_flood` in `backend/app/services/news_discovery_service.py` to evaluate Philippine places nationwide, filter out explicit international events, and preserve flood headlines lacking recognized places for full-text extraction/review.
  - Investigated broadcaster RSS endpoints: documented that ABS-CBN blocks automated RSS with HTTP 403 / Cloudflare bot protection and News5 times out, confirming 6 enabled and verified active broadsheets (GMA, INQUIRER, Rappler, Philstar, Manila Bulletin, SunStar).
  - Implemented `POST /api/v1/admin/news/manual-candidate` in `backend/app/api/v1/endpoints/admin_news.py` allowing administrators to paste DRRMO Facebook posts, citizen social posts, or news links directly into the pending news ingestion pipeline without requiring paid APIs.
  - Added unit and API tests in `backend/tests/test_news_discovery.py` (13/13 passing, 42/42 across Phase 36).
- [x] **Smart Auto-Activation Engine, Gemini 1.5 Flash Double-Check Auditor, OpenStreetMap Way Buffering, and Nationwide Geometry Service (`nationwide_geometry_service.py`, `news_auto_ingestion_service.py`, `hybrid_extraction_service.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Architected explicit division of labor: primary Taglish rules + 43,778 PSGC grounding lead detection; Gemini 1.5 Flash acts strictly in a supporting auditor role to double-check candidate claims before activation.
  - Implemented Smart Auto-Activation (Option 2): When active flooding with canonical depth and exact road/landmark is verified by primary rules and confirmed by Gemini auditor (>=95% confidence), `NewsAutoIngestionService` creates the verified `FloodReport`, official `FloodEvent`, and operational `FloodAvoidanceZone` atomically in PostGIS and Valhalla routing without admin delay.
  - Implemented Safety Suppression Gates: News indicating water has subsided ("humupa na") or weather predictions/advisories ("posibleng bahain") are strictly suppressed with zero created avoidance zones, preventing false closures of dry, passable roads.
  - Built `NationwideGeometryService`: resolves administrative hierarchy, generates authoritative 50m road corridor polygons and circular buffer polygons (SRID 4326 GeoJSON), disambiguates repeated place names, and enforces city-level safety guards.
  - Implemented OpenStreetMap (OSM) multi-point way LineString buffering (`buffer_osm_linestring_to_polygon`) and Nominatim `polygon_geojson=1` geocoding.
  - Extended news discovery with `likely_philippine_flood` across Luzon, Visayas, and Mindanao.
  - Created comprehensive test suites: `test_hybrid_extraction_service.py` (6/6), `test_nationwide_geometry.py` (9/9), `test_news_auto_ingestion.py` (3/3), `test_philippine_location_service.py` (6/6), `test_taglish_extraction.py` (11/11), and `test_news_discovery.py` (12/12) — 47/47 passing backend tests.
- [x] **Nationwide PSGC Geographic Ingestion and Dynamic Location Service (`philippine_location_service.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Built `backend/scripts/fetch_psgc_data.py` downloading and compiling the official PSA Philippine Standard Geographic Code (PSGC) reference dataset into `data/philippines_psgc_reference.csv` (43,778 records covering 82 provinces, 1,417 cities/municipalities, and 42,000+ barangays; 3.52 MB).
  - Implemented `PhilippineLocationService` in `backend/app/services/philippine_location_service.py` with fast in-memory indexing (0.24s load time, 15 MB RAM) to dynamically resolve places, normalize barangay aliases, and disambiguate repeated names using article text context (e.g. San Fernando, Pampanga vs San Fernando, La Union).
  - Refactored `taglish_extraction_service.py` to completely eliminate hardcoded place tuples in application source code, delegating place lookups dynamically to the reference service.
  - Added unit test suite in `backend/tests/test_philippine_location_service.py` (6/6 passing); verified 33/33 total Phase 36 backend tests pass cleanly with zero new third-party dependencies.
- [x] **Evidence-linked Taglish NLP extraction service and 50-item evaluation benchmark** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Evaluated calamanCy feasibility: documented that `tl_calamancy_md` requires `spacy>=3.8.3` (conflicting with pinned `spacy==3.7.5`), pulls 350+ MB of PyTorch and `spacy-transformers` dependencies, and lacks flood-specific NER entities. Built a deterministic, explainable, lightweight rule/gazetteer and regex extraction engine in `backend/app/services/taglish_extraction_service.py` that runs in 0.71 ms/item on CPU with zero heavy dependencies.
  - Constructed a 50-item ground truth evaluation dataset (`data/taglish_flood_eval_set.json`) covering Filipino, English, and Taglish reports, active floods, negated reports ("walang baha", "hindi binaha", "passable"), forecasts/warnings ("babala", "posibleng bahain"), historical events ("noong Ondoy"), and multi-location sentences.
  - Implemented read-only `NewsArticleExtractorInput` and versioned `NewsExtractionResult` schemas in `backend/app/schemas/news_extraction.py`.
  - Implemented PSGC-backed Pasig barangay alias normalization, strict canonical depth gauge mapping (`gutter`, `half-knee`, `half-tire`, `knee`, `tires`, `waist`, `chest`, `neck`), condition extraction (`active`, `rising`, `receding`, `subsided`, `unknown`), event time extraction, character offset preservation, and metadata-only lead handling.
  - Built offline benchmark runner `backend/scripts/evaluate_taglish_extraction.py`, achieving 100% canonical barangay recall (50/50), 100% canonical depth match (43/43), and 100% condition recall (59/59).
  - Added full test suite in `backend/tests/test_taglish_extraction.py` (11/11 passing; 27/27 total backend discovery & extraction tests passing).
- [x] **Production RSS discovery rollout** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): PR #105 merged into `main`; Cloud Build `8d552907` completed the production migration and deployed `lanes-api-00035-khl`. The dedicated `lanes-news-discovery` Cloud Run job completed two manual runs across all six enabled feeds and one Scheduler-triggered run. A dedicated `lanes-news-scheduler` identity has `roles/run.invoker` on that job only; `lanes-news-discovery-every-3-hours` runs at `0 */3 * * *` in `Asia/Manila`. The initial job run failed because Python arguments were passed as one string; the job configuration was corrected and all later runs succeeded. No sampled live article matched the Pasig flood shortlist, and no public map or routing zone was activated.
- [x] **Local PostGIS migration and persistent RSS verification** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): applied Alembic revision `a83c1d4e7b92` to development PostGIS, confirmed it is head, and completed two persisted collector runs across six enabled feeds. Six checkpoint rows remained healthy; three feeds returned conditional `304` on the repeat run. No sampled live entry met the Pasig flood filter; a mocked article against the same PostGIS database retained one article and provenance row across two runs, then the synthetic records were removed. All 12 focused RSS tests passed.
- [x] **Approved durable evidence storage implemented in code** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): added the three approved SQLAlchemy tables and Alembic revision, per-feed ETag/Last-Modified checkpoints, persistent article and GUID provenance deduplication, a staff-only candidate list and on-demand run, and a dry-run CLI option. A PostgreSQL advisory lock serializes the same feed across concurrent runs. No Cloud Run job, scheduler, NER, or map-zone activation was added.
- [x] **Configurable publisher registry and direct feed pilot** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): recorded 50 Feedspot candidates plus News5, verified six recent publisher feeds locally (GMA, Inquirer, Rappler, Philstar, BusinessWorld, Interaksyon), and kept other candidates disabled pending checks. The source loader validates HTTPS feed URLs and publisher article domains.
- [x] **RSS/Atom probe and initial Pasig flood discovery** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): added bounded HTTP/XML retrieval, explicit per-source errors, a one-run command, staff-only source listing/probing, broad Taglish flood/place shortlisting, safe public article retrieval with metadata-only fallback, and within-run deduplication. Scheduling remains Phase 36 work.

---

### Pasig Flood-History Dataset Preparation (🟢 COMPLETED)
- [x] **Reproducible historical flood-data cleaner** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): added a standard-library pipeline that converts the 2020–2025 DRRMO CSV into 726 traceable records, preserves raw location and depth evidence, normalizes safe whitespace/administrative aliases, and extracts explicit centimeter ranges without geocoding or merging events.
- [x] **PSA/PSGC barangay validation and quality gates** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): added the 30-barangay Pasig reference with PSGC codes, resolves San Miguel and safe aliases, and records reviewed corrections for `Maybunnga` → Maybunga and `Pala` → Palatiw. Dedicated pytest coverage verifies the row/year totals, normalization, depth parsing, and output traceability.

---

### Capstone Phase 35: Admin Profile Management, Self-Healing Profile Provisioning & Secure Password Updates (🟢 COMPLETED)
- [x] **Self-Healing Profile Lifecycle & Creation Bug Fix (`admin.py`, `auth.py`, `users.py`, [`BUG-051`])** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Resolved `404 Profile not found` when editing accounts created via Admin User Registry by automatically provisioning a linked `models.Profile` on user creation in `POST /api/v1/admin/users`.
  - Added self-healing fallback to `POST /api/v1/auth/test-token`, `PATCH /api/v1/users/me/profile`, `POST /api/v1/users/me/avatar`, and `DELETE /api/v1/users/me/avatar` so existing profile-less accounts heal instantaneously on session validation without 404 or not-null integrity violations.
  - Implemented automated pytest suite (`tests/test_admin_profile.py`) verifying token self-healing, profile updates, and password security.
- [x] **Native Admin Profile Management Page (`/admin/profile`, `AdminProfilePage.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Created dedicated profile management screen for Super Admins, DRRM Officers, and Moderators natively within the Admin Panel.
  - Reused exact public profile aesthetic: full-bleed cover banner with color picker, avatar container with preview modal, Cloudinary upload, and remove confirmation dialog.
  - Integrated `EditProfileForm` with personal information, Philippine Standard Geographic Code (PSGC) address selectors, and live unique username verification.
  - Displayed staff role badges, verified staff account ID, email, and joined date.
  - Provided privacy preferences ("Display Full Name" and "Hide Profile Picture" toggles).
- [x] **Secure Admin & User Password Change with Email OTP Verification (`users.py`, `auth_service.py`, `email_service.py`, `PasswordOtpModal.tsx`, `PasswordStrength.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Implemented `POST /api/v1/users/me/password/request-otp` and updated `PUT /api/v1/users/me/password` to require email OTP verification before changing passwords.
  - Implemented `send_password_change_otp_email_async` with hosted branding, logo header, single-use 6-digit code box, 5-minute expiry notice, and security disclaimers matching signup/register emails.
  - Built reusable `PasswordOtpModal` with 6-box zero-click auto-submitting numeric inputs, auto-focus, paste support, live countdown ticker, and inline validation, integrated across both `/profile` and `/admin/profile`.
  - Added Password & Security section with interactive eye reveal toggles and live `<PasswordStrength>` checklist validation.
- [x] **Admin Navigation Integration (`AdminSidebar.tsx`, `AdminLayout.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added user profile card in the sidebar footer with avatar, display name, and staff role tag linking directly to `/admin/profile`.
  - Configured edge-to-edge padding (`p-0`) in `AdminLayout` for `/admin/profile` to support full-bleed cover banners.


---

### Capstone Phase 34: 30-Day Archive Retention Lifecycle, Auto-Purge Worker, Delete Controls & User Self-Deletion (🟢 COMPLETED)
- [x] **Automatic 30-Day Archive Retention & Background Worker (`retention_service.py`, `main.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Implemented automated cleanup service purging soft-deleted records older than 30 days (`users`, `community_posts`, `flood_reports`, `flood_avoidance_zones`).
  - Integrated periodic background task in FastAPI lifespan that runs daily without blocking API requests or database connections.
  - Added on-demand administrator trigger endpoint `POST /api/v1/admin/archive/purge-expired`.
- [x] **User Account Restoration & Permanent Purge Controls (`admin.py`, `adminApi.ts`, `ArchivePage.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added dedicated endpoints `POST /api/v1/admin/users/{user_id}/restore` and `DELETE /api/v1/admin/users/{user_id}/permanent`.
  - Added explicit "Restore User" and "Delete Permanently" actions with typed confirmation in Archive Center.
  - Added color-coded 30-day countdown badges indicating remaining days before permanent auto-purge.
- [x] **Public User Self-Deletion Danger Zone (`users.py`, `auth.py`, `ProfileView.tsx`, `useProfile.ts`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added `DELETE /api/v1/users/me` endpoint allowing citizens to deactivate their own accounts.
  - Added Danger Zone in Profile Settings with confirmation modal requiring typed `"DELETE"` verification.
  - Integrated 30-day reactivation grace period: logging in within 30 days automatically restores the deactivated account with welcome-back notification.
- [x] **Soft-Deleted User Re-creation Conflict Mitigation (`admin.py`, `UsersPage.tsx`, [`BUG-050`])** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Resolved `psycopg.errors.UniqueViolation` when re-creating accounts previously archived by purging stale archived records prior to user insertion.
  - Replaced raw inline error banners with shared toast system (`useToast`).

---

### Capstone Phase 33: Flood Event Lifecycle Foundation & Historical Tracking (🟡 IN PROGRESS)

- [x] **Cloud SQL Flood Event integrity audit** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): verified that active Events #6 and #8 retain timeline snapshots for reports/zones that no longer exist, leaving zero report/zone links. The investigation is recorded as [BUG-055]; remediation requires a user-approved schema/data plan and is not yet deployed.
- [x] **Flood Event Reports evidence master-detail** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): refined the protected event record so all reports linked to the incident can be examined without leaving historical context. Desktop keeps the report list beside the shared report-detail/evidence panel; mobile replaces the list with that panel and provides a Back to reports action. Report map focus remains historical-only.
- [x] **Admin Dashboard bento grid alignment** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): restructured the overview bento layout so that System Health Check and Quick Administration Tasks sit beside Top 5 Most Flooded Barangays in Row 2, completely eliminating dead whitespace on desktop and establishing a balanced 2x3 grid across all breakpoints.
- [x] **Privacy-preserving first-party visitor analytics** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): replaced the mutable landing-page counter with daily HMAC-pseudonymous browser activity, optional account-level aggregate deduplication, known-bot filtering, and rate limiting. The Admin Dashboard now has a compact responsive 30-day unique-visitor graph and a Today card; it never stores IP addresses, raw browser IDs, fingerprints, or location data.
- [x] **Today’s Flood Report rejection summary** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): exposed the existing admin-authorized `total_rejected_today` metric as a responsive Dashboard card. Its action opens Flood Report Moderation with the Rejected filter selected, keeping historical moderation review in its dedicated workspace.
- [x] **Flood Event Records three-tab staff case record** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): reorganized protected event details into Overview, Official History, and Supporting Reports tabs. Staff can inspect official conditions and timeline separately from normalized original evidence, use the shared report/media detail view, and focus an event, zone, or source report only on the read-only historical map—never the live routing map.
- [x] **Flood Event Records lifecycle detail and planning clarity** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): completed the staff record detail with first-report, official verification/end, official duration, peak conditions, affected places, official-zone history, typed incident timeline, and protected original supporting evidence. The planning dashboard now distinguishes active/ended events, surfaces the most affected road, explains metric definitions, and renders verification timing in Philippine time; all controls continue using the shared UI system.
- [x] **Flood History visual-system consistency** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): aligned the planning dashboard and event-record filter treatment with the admin dashboard's compact blue-led graph language; replaced raw controls with shared `Input`, `Select`, `DatePicker`, `Button`, `Card`, and `Tabs` components; tightened chart/card density; and retained the desktop map/list and mobile switcher behavior.
- [x] **Phase 33.7 safety and verification** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): delivered Playwright desktop/mobile smoke-test infrastructure without checked-in credentials, lifecycle and protected-route authorization coverage, a repeatable release script, and a static privacy/security review. The verified migration and release checklist are recorded in `docs/guides/flood-history-verification.md`.
- [x] **Phase 33.6 event-based planning analytics and exports** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): added admin-only distinct-Flood-Event aggregation for recurrence, roads, peak severity, official durations, verified-event/report time series, UTC verification timing, and separate approved-report volume; delivered filtered CSV/JSON planning exports that deliberately omit reporter identity, raw evidence, exact report geometry, and media. Recharts now presents a responsive trend/evidence combination chart, severity doughnut, duration columns, recurrence rankings, and an accessible timing heatmap; the historical map legend explains peak severity in text and marks selected events with an outline rather than relying on color alone.
- [x] **Phase 33.5 Flood Event Records workspace** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): delivered a separate historical `BaseMap` source/layer set, synchronized map/list selection and map focus, server-backed date/place/severity/status filters, an accessible severity legend, mobile map/list switcher with safe-area spacing, and in-context event/report evidence views. Historical geometry remains isolated from active routing zones.
- [x] **Phase 33.5 protected history-read foundation** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): added admin-only filtered Flood Event history and full evidence/timeline detail reads, used by the completed Records workspace without exposing active routing data.
- [x] **Phase 33.5 Flood History & Analytics entry surface** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): added protected `/admin/flood-history` navigation, a server-owned Flood Event list read, responsive Overview metrics, and an initial Flood Event Records list with mobile-safe bottom spacing.
- [x] **Focused moderation map handoff and depth-label cleanup** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): removed unverified gauge measurements, added the Spatial Operations-style Info modal, and made review handoffs fetch any report state, isolate it from active zones, and re-run on repeat clicks.
- [x] **Verified Flood Event lifecycle safeguards** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): server-owned duration/evidence/peak metrics, readable zone-update and severity-peak timeline records, final-zone event ending, and admin-only event summary reads.
- [x] **Idempotent report operations and private rejection notification** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): retries reuse an existing event/report association without duplicate trust credit or moderation outcome; report rejection notifies the submitting user through the existing bell without exposing staff-only notes.
- [x] **Flood Report Moderation tracking surface** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): separates Community and Flood Report queues, supports operational-status/source/date/location/reporter/rejection-reason filters, and hands cases back to Spatial Operations through one map-review action.
- [x] **Shared moderation tab treatment** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): uses the shared underline `Tabs` component and responsive overflow behavior to match the established Archive Center navigation pattern.

---

## Completed Milestones (40+ Commits Integrated)

| # | Milestone | Status | Key Features Delivered |
|---|-----------|--------|------------------------|
| 35 | Admin Profile Management, Self-Healing Profile Provisioning & Secure Password Updates | Completed | Native Admin Profile hub (`/admin/profile`, `AdminProfilePage.tsx`) with cover color banner, avatar management, and address configuration; auto-provisioning of `Profile` in `create_admin_user`; self-healing fallback in `test-token` and `users/me/profile` ([`BUG-051`]); secure password update endpoint (`PUT /users/me/password`) with live `<PasswordStrength>` meter; and user profile card in `AdminSidebar.tsx` footer |
| 34 | 30-Day Archive Retention Lifecycle, Auto-Purge Worker, Delete Controls & User Self-Deletion | Completed | Automatic 30-day retention countdown and daily background purge worker (`retention_service.py`), explicit user account restoration (`POST /admin/users/{id}/restore`) and permanent purge (`DELETE /admin/users/{id}/permanent`), manual on-demand purge trigger (`POST /admin/archive/purge-expired`), public user self-deletion Danger Zone modal (`DELETE /users/me`) with 30-day login grace period, and unique constraint conflict mitigation ([`BUG-050`]) |
| 33 | Flood Event Lifecycle Foundation & Historical Tracking | Completed | Verified Flood Event persistence model, server-owned duration/evidence metrics, idempotent report operations, staff Moderation Center queue, protected Flood Event Records map/list workspace, distinct-event city-planning analytics, privacy-safe CSV/JSON exports, and completed safety/release verification |
| 32 | Reddit-Style Community Feed Voting Engine, True Optimistic UI & Disaster Recency Windowing | Completed | Unified compact net score vote pill (`▲ Net Score ▼`), instant 0ms optimistic updates with tri-state transitions and flip mechanics across Feed, Post Detail, and Profile, authoritative `VoteResponse` backend synchronization, and clean built-in disaster/civic recency duration (72h / 3 days) with graceful fallback |
| 31 | Automated Cloud Run Database Migration CI/CD Pipeline & Cloud Logging Hardening | Completed | Google Cloud Build CI/CD pipeline automation (`cloudbuild.yaml`), automated Alembic database migration execution via Cloud Run Job (`lanes-migration --wait`) before web service rollout, and Cloud Logging option hardening (`CLOUD_LOGGING_ONLY`) |
| 30 | Community Feed & Profile Post Tab Spaced Card UI Redesign | Completed | Replaced dividing lines with standalone card architecture (`space-y-3 sm:space-y-4`), mobile margin padding (`px-3 sm:px-0`), Profile post tab de-nesting, and post count badge |
| 29 | Archive Center Redesign, Spatial Avoidance Zones Archive, Admin Removal Notifications & Media Gallery | Completed | Complete Archive Center overhaul (Users, Spatial Data [Reports/Zones], Archived Posts [Deleted/Hidden]), community post soft-deletion on feed, admin removal reason modal with in-app author notifications, avoidance zone media gallery, PostGIS/SSE zone restore & purge, and typed 'DELETE' permanent purge protection |
| 28 | Database Connection Pool Resilience, Profile Photo Management & Dev UX Optimization | Completed | Ephemeral DB sessions for SSE streaming (/sync & /sse), NullPool/QueuePool connection starvation resolution, full profile picture viewer modal & Cloudinary upload pipeline, optimistic privacy toggle sync, and Next.js dev indicator cleanup |
| 27 | Edit Flood Zone Geometry Switching, TerraDraw Collision Hardening & Production Weather Insights | Completed | Non-destructive mode switching (Line ↔ Polygon), Option 2 reference map styling, TerraDraw source collision resolution (Source 'td-polygon' already exists), BaseMap MapTiler 403 reload throttling, and production AI Weather Insights gateway routing on Firebase App Hosting |
| 26 | Profile Picture Privacy, Tab Title Standardization & About Contact Form | Completed | User preference to hide profile picture across public feeds, post comments, leaderboard, and profile with initial fallback; brand tab titles (LANES \| <Page>); and official contact details with interactive Resend email form on /about. |
| 25 | Fast Map Startup, Automatic Basemap Recovery & Live-Sync Pool Resilience | Implemented / manual verification pending | Same-instance MapTiler-to-OSM fallback at a 1.5-second first-map budget, guarded automatic MapTiler restoration, responsive recovery status, App Hosting key configuration, and short-lived SSE polling sessions that no longer monopolize Postgres connections. |
| 24 | Unified Flood-Routing Policy & Provider Parity | Implemented / cloud verification pending | Centralized four-profile/four-severity passability policy, PostGIS intersection exposure measurement, normalized 4-card ranking (Fastest, Safest, Balanced, Alternative), and Valhalla exclude_polygons contract alignment |
| 23| Identity-First Google Auth, Password Recovery & Resilient Admin Routing | Completed | Google Sign-in/Sign-up integration with automatic profile prefill and citizen onboarding completion, self-service Resend OTP password recovery workflow, hardened admin login redirection ([BUG-034]) directly to /admin/dashboard, and NavigationWrapper route guard enforcement |
| 22| Private Valhalla Cloud Run Recovery | Ready for cloud deployment | Private Valhalla deployment assets, Cloud Storage tile artifact flow, Cloud Run identity-token calls, automatic ORS availability fallback, typed engine metadata, and matched desktop/mobile backup notice |
| 21| Production Cloud Infrastructure & Firebase App Hosting Deployment | Completed | Production deployment of Next.js frontend to Firebase App Hosting (asia-east1), build-time API variable injection via apphosting.yaml, backend CORS middleware whitelist expansion (*.hosted.app, *.web.app, *.firebaseapp.com), dotenvx environment encryption, and deployment gitignore hygiene |
| 20| Complete Email Infrastructure Migration to Resend | Completed | Full excision of Brevo configuration, seamless transition to Resend REST API (from `Lanes <noreply@navlanes.live>`), 100% preservation of OTP email HTML layout/CDN branding, and verified outbound domain delivery |
| 19| Authentication Lifecycle, Resilient SSE Synchronization & 100MB Feed Media Pipeline | Completed | Soft-delete re-registration conflict resolution, explicit login redirect without auto-login, unconditional EventSource unmount cleanup, direct port 8000 SSE streaming, 100MB multipart video upload support across Next.js proxy & FastAPI, exact file size error notifications, post edit history and post reporting with shared select dropdown, Profile "Display Full Name" SQL preference resolution across feed/comments, Community Feed mobile responsiveness (iPhone SE/12 single-row action bar & standalone Lucide voting buttons), mobile route search bar collapsibility, and explicit geolocation diagnostics |
| 1 | Architecture & Core Services | Completed | FastAPI setup, PostGIS routing, PWA support, Modular frontend, Domain-based backend structure |
| 2 | Advanced 3D Map Engine | Completed | 3D MapTiler integration, Pasig boundary overlay, Persistent Global Map, Location Autocomplete |
| 3 | Spatial Flooding & Routing | Completed | Road-based flood highlights, Dynamic route gradients, LineString avoidance logic, Ignore-floods toggle |
| 4 | Immersive UI & Navigation | Completed | Floating animated navigation (Framer Motion), FAB menu, Route picker panel, Split-screen Auth layout |
| 5 | Authentication & Identity | Completed | OTP Registration (Resend integration), User Profiles, Profile Picture Uploads, Secure Sessions |
| 6 | RBAC & Admin Dashboard | Completed | 3NF DB Normalization, Roles CRUD, User Management, Audit Trails, Data Mgmt & System Settings |
| 7 | Real-Time Operations | In Progress | Server-Sent Events (SSE) broadcasting, Live active zones, Real-time admin dashboard invalidations |
| 8 | Community Feed & Moderation | Completed | Feed layout, Upvotes/Downvotes, Post archiving, Soft deletes, Map coordinate rendering |
| 9 | Spatial Analytics & Heatmap | Completed | Global Heatmap, Top Barangays stats, Dedicated Analytics Pages for Commuters and Admins |
| 10| Official Flood Zones (DRRMO) Moderation | Completed | Admin panel restructuring, backend Zone Override schemas, bulk merging operations, troll filtration, DRRMO Official Zone mapping with Terra Draw |
| 11| Intelligent Bidirectional Flood Reporting | Completed | Hybrid Carriageway Detection Strategy, Valhalla Map Matching for opposite-side road detection, GeometryCollection PostGIS storage, dual-buffer approval |
| 12| Spatial Operations & Map Hover Badge Engine | Completed | Multi-geometry layers (MultiLineString/Polygon), 400ms hover dwell timer, smart collision-free positioning, two-row FloodZonePopup, Lenis scroll scoping |
| 13| Community Feed Emergency Hotline Directory | Completed | Cached national hotline integration, Pasig city/barangay directory, responsive feed hotline card, lazy-loaded directory modal |
| 14| Saved Places Camera Sync & Navigation UX | Completed | Camera fly-to alignment (zoom 16, 1500ms duration), 3-second pulsing red indicator, saved places panel activation from feed, pin order fix, custom scrollbars |
| 15| Community Post Geolocation & Seamless Map Fly-to | Completed | PostGIS `location_lat`/`location_lng` columns, clickable red pin header navigation, ResizeObserver layout compensation for 340px sidebar, draft auto-save across auth redirection |
| 16| Route Focus, Saved Places & Map Polyline Engine | Completed | Stray click protection, two-click map picking, sequential saved place recalculation, resilient MapLibre getStyle() route polyline rendering, auto camera framing, sign-out memory cleanup |
| 17| Automated Street, Barangay & City Reverse-Geocoding | Completed | Multi-provider structured reverse geocoding (Nominatim/Photon), representative geometry coordinate midpoint parsing, PostGIS city column migration, automatic location ingestion, historical report backfill, and Community Feed post location card deduplication |
| 18| Intelligent Flood-Report Merging & Spatial Operations | In Progress | Feature-based Official Zone Drawer with Cloudinary uploads and five-section parity; candidate scoring and carriageway analysis; four-step merge workspace with a contextual, persistent secondary drawer. Developer-led end-to-end validation remains. |

---

## Capstone Roadmap - Delivered Phases

### Capstone Phase 32: Reddit-Style Community Feed Voting Engine, True Optimistic UI & Disaster Recency Windowing (🟢 COMPLETED)
- [x] **Reddit-Style Unified Vote Pill (`PostItem.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Consolidates the upvote arrow, net score, and downvote arrow into a unified compact pill: `▲ Net Score ▼`.
  - Added active state highlight styling: subtle blue tint and filled blue arrow when upvoted; subtle rose tint and filled rose arrow when downvoted.
  - Retained full precision breakdown (`X upvotes, Y downvotes`) in the native hover tooltip.
  - Enhanced horizontal space efficiency on narrow mobile screens (360px).
- [x] **True Optimistic UI Updates & Error Rollbacks (`FeedPage.tsx`, `PostDetailPage.tsx`, `ProfileView.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Implemented `onMutate` optimistic state transitions in TanStack Query `useMutation` across Feed, Post Detail modal, and Profile post views.
  - Applies instant score calculation in 0ms (fresh vote $+1$/$-1$, flip $\pm 2$, and un-vote toggle).
  - Rolls back to snapshot and prompts user on network failure or session expiration.
  - Eliminates the previous 50-post feed re-fetch lag after voting.
- [x] **Clean Built-in Disaster/Civic Recency Windowing (`FeedPage.tsx`, `feed.py`, `crud/feed.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Maintained a clean social media interface without unnecessary UI button clutter by embedding the 72-hour (3-day) DRRMO flood lifecycle directly into the Recent feed query.
  - Implemented automatic fallback to latest posts if no items exist in the 72h window, ensuring the feed is never an empty screen.
- [x] **Authoritative Backend Voting Response (`schemas/feed.py`, `crud/interaction.py`, `endpoints/feed.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Defined `VoteResponse` Pydantic model (`post_id`, `upvotes`, `downvotes`, `net_score`, `user_interaction`).
  - Added `get_post_vote_summary` in `crud/interaction.py` to return the updated authoritative counts directly in `POST /feed/{post_id}/vote`.
  - Added unit test suite `tests/test_feed_voting.py` verifying schema contracts.

### Capstone Phase 31: Automated Cloud Run Database Migration CI/CD Pipeline & Cloud Logging Hardening (🟢 COMPLETED)
- [x] **Automated Database Migration via Cloud Run Job (`cloudbuild.yaml`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Configured Cloud Build with automated deployment and execution steps for `lanes-migration` (`gcloud run jobs deploy lanes-migration ...` and `gcloud run jobs execute lanes-migration --wait ...`).
  - Executes batch Alembic migrations synchronously (`alembic upgrade head`) using the newly compiled container image prior to deploying new `lanes-api` service revisions, ensuring zero schema drift against production PostgreSQL.
- [x] **Cloud Build Custom Service Account Logging Option (`cloudbuild.yaml`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added `options: logging: CLOUD_LOGGING_ONLY` to `cloudbuild.yaml` to prevent invalid argument errors when executing builds under a user-managed Google Cloud service account.
- [x] **Encrypted Secrets & Environment Integrity (`backend/.env`, `frontend/.env.local`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Re-encrypted local environment files using `@dotenvx/dotenvx` prior to committing to ensure sensitive credentials and API keys remain protected in version control.

### Capstone Phase 30: Community Feed & Profile Post Tab Spaced Card UI Redesign (🟢 COMPLETED)
- [x] **Standalone Post Card Styling (`PostItem.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Removed legacy bottom border divider line (`border-b border-gray-100 last:border-b-0`).
  - Redesigned the root `<article>` element into an independent card styled with `bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100 transition-all hover:border-gray-200/90`.
  - Added optional `className` prop to `PostItemProps` to allow callers (like single-post views) to customize or augment card styling.
- [x] **Community Feed Spaced Card Container (`FeedPage.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Replaced the single giant white card enclosing all posts with a responsive spaced layout (`space-y-3 sm:space-y-4`).
  - Added responsive horizontal margin padding (`px-3 sm:px-0 pt-3 sm:pt-4`) ensuring post cards float cleanly on mobile viewports while aligning with the header tab bar.
  - Converted empty feed, loading skeleton, and error states into standalone rounded cards.
- [x] **Profile Page Post Tab Overhaul (`ProfileView.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Resolved "box-in-a-box" nesting by conditionally bypassing the enclosing white container panel when `activeTab === "posts"`, letting post cards float directly on the `bg-slate-50` background on both desktop and mobile.
  - Formatted posts with responsive spacing (`space-y-3 sm:space-y-4`).
  - Added a post count indicator pill badge next to "My Community Posts" in the tab header.
  - Rendered loading skeletons and empty states as dedicated cards.
- [x] **Post Detail Page Refinement (`PostDetailPage.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Removed the redundant outer border wrapper around `PostItem` and adjusted comments section spacing to match card proportions.

### Capstone Phase 29: Archive Center Redesign, Spatial Avoidance Zones Archive, Admin Removal Notifications & Media Gallery (🟢 COMPLETED)
- [x] **Alembic Migration & Post Soft-Delete Schema (`models/post.py`, `alembic/versions/e2f891ab7034_add_post_soft_delete_fields.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Generated and verified Alembic revision `e2f891ab7034` adding nullable `deleted_at` (DateTime with index) and `deleted_by_user_id` (ForeignKey to `users.id` with `ondelete='SET NULL'`) columns to `community_posts`.
  - Added SQLAlchemy relationships `deleted_by` and `hidden_by` mapped to the `User` model.
- [x] **Spatial Archive Backend Extensions & Media Aggregation (`crud/report.py`, `endpoints/admin.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Updated `update_flood_report_status` to automatically set `deleted_at = datetime.utcnow()` whenever a report is rejected in the Live Map moderation panel.
  - Implemented `restore_flood_report` to clear `deleted_at`, revert status to `pending`, and refund reporter trust score penalties.
  - Implemented `hard_delete_flood_report` to nullify linked community post references and permanently purge the report with `HARD_DELETE_REPORT` audit logging.
  - Extended `get_all_avoidance_zones_filtered` with `archived: bool`, eager `selectinload` for `reports`, `user`, and `profile`, and search query filters.
  - Added `POST /api/v1/admin/zones/{zone_id}/restore` to reactivate zones, clear past expiry, create `RESTORE_ZONE` audit logs, and broadcast SSE `zone_updated`.
  - Added `DELETE /api/v1/admin/zones/{zone_id}/permanent` to nullify linked report `zone_id` foreign keys, permanently delete the zone, log `HARD_DELETE_ZONE`, and broadcast SSE `zone_deactivated`.
  - Enhanced `_attach_report_media` to aggregate photo/video attachments across all child reports in `zone.reports` alongside direct zone media, stamping provenance tags (`"Zone"` vs `"Report"`).
- [x] **Administrative Post Removal & Author Notification Workflow (`schemas/post.py`, `crud/post.py`, `crud/feed.py`, `endpoints/posts.py`, `endpoints/admin.py`, `feedApi.ts`, `PostItem.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added `CommunityPostDeletePayload(reason, details)` Pydantic schema in `schemas/post.py`.
  - Extended `DELETE /api/v1/posts/{post_id}` to accept optional removal payload with `Body(None)` dependency.
  - Differentiated author self-deletion from administrative removals in `PostItem.tsx`. For staff/admin removals, prompts for a reason category dropdown (Inappropriate Content, Harassment/Hate Speech, Spam/Advertising, Misinformation, Irrelevant to Flood/Commute, Other) and mandatory notes.
  - Dispatches an in-app `SYSTEM` notification to the post author detailing the removal justification, logs an `ADMIN_DELETE_POST` entry in `AuditLog`, and broadcasts real-time SSE `feed_post_deleted`.
  - Added parity in `resolve_community_post_reports` (`endpoints/admin.py`) to compile reported reasons and deliver an in-app moderation notice to authors upon post hiding.
  - Enhanced `NotificationBell.tsx` to highlight moderation notices with an amber `AlertTriangle` icon badge.
- [x] **Archive Center Frontend Overhaul & Evidence Media Gallery (`ArchivePage.tsx`, `adminApi.ts`, `TypedDeleteModal.tsx`, `ZoneDetailsModal.tsx`, `PostDetailsModal.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Redesigned `/admin/archive` with three main tabs: **Archived Users**, **Spatial Data**, and **Archived Posts**.
  - Structured **Spatial Data** with dual sub-tabs: *Archived Reports* and *Archived Zones*, removing redundant sub-tab count badges to prevent UI clutter.
  - Structured **Archived Posts** with dual sub-tabs: *Deleted Posts* and *Hidden Posts*, displaying post content, author avatar, media badges, removal timestamp, and remover identity.
  - Built comprehensive **Attached Media & Evidence** gallery in `ZoneDetailsModal.tsx` displaying thumbnails, video badges, source provenance tags, and full-resolution tab previews.
  - Connected `onOpenMedia` in `ArchivePage.tsx` so report media links in `ReportDetailsModal` also preview seamlessly.
  - Built reusable `TypedDeleteModal` enforcing safety for permanent hard deletions across reports, zones, and posts by requiring the admin to type `"DELETE"` before purging.
- [x] **Live Map Archive Redirection Toasts (`LiveMapPage.tsx`, `ModerationCenterPage.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added clear toast alerts in `LiveMapPage.tsx` upon rejecting a report or deactivating single/bulk avoidance zones informing admins that records are accessible in the Archive Center.
  - Standardized toasts using central `useToast` from `@/shared/ui` and removed extraneous `react-hot-toast` imports.

### Capstone Phase 28: Database Connection Pool Resilience, Profile Photo Management & Dev UX Optimization (🟢 COMPLETED)
- [x] **Backend Database Connection Pool Exhaustion Fix (`sync.py`, `sse.py`, `database.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Removed persistent session dependency injection (`db: Session = Depends(get_db)`) from long-running SSE streaming endpoints (`/api/v1/sync` and `/api/v1/sse`).
  - Switched generator loops to ephemeral `with SessionLocal() as session:` blocks scoped strictly to each poll snapshot, immediately closing and returning connections to the pool between heartbeats.
  - Hardened PostgreSQL pool settings (`pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=300`) to eliminate `QueuePool limit of size 20 overflow 10 reached` timeout errors under persistent client streaming.
- [x] **Profile Picture Privacy Instant Sync & Optimistic Updates (`useProfile.ts`, `ProfileView.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added optimistic cache updates (`onMutate`) in `useProfile.ts` for immediate UI response without waiting for background HTTP refetches, accompanied by automatic rollback on error.
  - Synchronized React Query cache across `['auth-user']`, `['my-posts']`, and `['posts']` on mutation success, resolving toggle lag and switch bounce.
  - Added explicit toast notifications ("Your profile picture is now hidden from public view." / "Your profile picture is now visible to the public.").
- [x] **Profile Picture Viewer Modal & Cloudinary Upload Pipeline (`ProfileView.tsx`, `users.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Built high-resolution Profile Picture modal showing user avatar, full name, `@username`, and "Hidden from public" privacy badge with direct action shortcuts. Made clicking the profile avatar directly open this modal.
  - Connected native file selector to new backend endpoint `POST /api/v1/users/me/avatar` with image MIME validation, 10MB file size guard, and Cloudinary upload integration.
  - Added `DELETE /api/v1/users/me/avatar` and "Remove Picture" action with `<ConfirmDialog>` to allow reverting to the default initials avatar.
  - Removed duplicate "Hide Profile Picture" option from the camera dropdown menu and added outside-click dismissal.
- [x] **Next.js Development Indicator Cleanup (`next.config.ts`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added `devIndicators: false` in `next.config.ts` to disable the distracting dev-only `● Rendering...` badge caused by active background SSE streams.

### Capstone Phase 27: Edit Flood Zone Geometry Switching, Option 2 Reference UX & TerraDraw Collision Hardening (🟢 COMPLETED)
- [x] **Non-Destructive Dual-Session Geometry Caching (`OfficialZoneDrawer.tsx`)**: Introduced `lineSessionCacheRef` and `polygonSessionCacheRef` to preserve line start/end coordinates and drawn polygon features across mode switches without premature state destruction. Added "Reset to Saved" action to revert geometry and attributes back to baseline.
- [x] **Option 2 Reference Map Styling & Pin Visibility (`useFloodMapPreview.ts`, `MapContext.tsx`, `AdminFloodMapInteraction.tsx`, `MapCanvas.tsx`)**: Extended `useFloodMapPreview` with `showMarkers: boolean` and exposed `floodShowMarkers` in `MapContext`. In polygon mode, start and end pins are hidden to provide a clean canvas while the existing road line remains visible as an orange broken reference line.
- [x] **Active Zone Layer Isolation (`LiveMapPage.tsx`)**: Excluded `editingZone` from `visibleMapZones` in `useFloodZonesLayer` so that only the preview reference line represents the zone during editing, returning to the solid active style cleanly if cancelled.
- [x] **TerraDraw Instance Gating & Source Collision Resolution (`useTerraDraw.ts`, `OfficialZoneDrawer.tsx`)**: Gated TerraDraw mounting behind `isEnabled: isOpen` so Create and Edit drawers do not clash over the same MapLibre sources. Hardened `removeStaleTerraDrawArtifacts` to purge all `td-*` layers and sources before adapter creation and on unmount. Directly set active mode on `draw.start()` and monitored `drawInstance` in mode sync effect to immediately activate the crosshair cursor and instruction banner.
- [x] **Permanent Map Style Reload Halting (`BaseMap.tsx`)**: Detected permanent 401/403 authorization failures on MapTiler styles and capped retries, preventing perpetual background `map.setStyle()` reloads that wiped map layers.
- [x] **Production Weather Insights Gateway Standardization (`WeatherInsightsModal.tsx`, `apphosting.yaml`)**: Standardized AI weather insights to query `NEXT_PUBLIC_API_URL` directly rather than a hardcoded relative path, and added `BUILD` availability to `BACKEND_URL` in `apphosting.yaml` to prevent Firebase App Hosting 500 rewrite errors.

### Capstone Phase 26: Profile Picture Privacy, Tab Title Standardization & About Contact Form (🟢 COMPLETED)
- [x] **Profile Picture Privacy Toggle & Query Masking (`profile.py`, `feed.py`, `user.py`, `posts.py`, `comments.py`, `ProfileView.tsx`, `4389876f4499_add_hide_profile_picture_to_profile.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added `hide_profile_picture = Column(Boolean, default=False)` to the `profiles` table with Alembic migration `4389876f4499`.
  - Masked `author_avatar`/`avatar_url` to `None`/`NULL` in public post feeds, comment threads, top contributor leaderboards, and user profile endpoints when enabled.
  - Added toggle in Profile Settings tab under Privacy section and rendered fallback uppercase initial letter avatar with `EyeOff` indicator on profile view and quick menu.
  - Added unit test suite `backend/tests/test_profile_privacy.py` covering model flags and privacy masking across endpoints.
- [x] **Browser Tab Title Standardization (`layout.tsx`, `manifest.json`, subpages)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Configured root App Router metadata template to `LANES | %s` with default fallback `LANES`.
  - Standardized tab titles across subpages (`LANES | Map`, `LANES | Community Feed`, `LANES | Profile`, `LANES | Flood Risk Analytics`, `LANES | About`).
  - Updated PWA manifest application name to `"LANES - Localized Alternative Navigation for Environs under Submersion"`.
- [x] **Official Contact Channels & Interactive Resend Inquiries (`ContactSection.tsx`, `about/page.tsx`, `public.py`, `email_service.py`, `contact.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Displayed official contact channels (`lanes@navlanes.live` with backup `navlanes.live@gmail.com`) with one-click copy support on `/about`.
  - Implemented rate-limited `POST /api/v1/public/contact` (5/min) and asynchronous Resend transactional dispatch (`send_contact_email_async`) with direct `reply_to` headers to deliver commuter messages directly to project administrators.

### Capstone Phase 25: Fast Map Startup, Automatic Basemap Recovery & Live-Sync Pool Resilience (🟡 IMPLEMENTED / MANUAL VERIFICATION PENDING)
- [x] **One-instance basemap lifecycle (`BaseMap.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Replaced the preflight-and-recreate cycle with a 1.5-second initial MapTiler render budget and in-place OSM fallback.
  - Restores LANES-owned flood, boundary, and route layers through existing `style.load` hooks instead of creating another WebGL map.
  - Retries MapTiler after connectivity returns and on bounded backoff; recovery allows six seconds because OSM is already a usable baseline.
  - Uses LANES-specific fallback identifiers rather than generic `osm` names, allowing a loaded MapTiler retry to be recognized correctly.
  - Treats the first rendered map frame as usable rather than waiting on every remote font glyph; production repeat visits reuse cached MapTiler style, font, sprite, and tile assets after an early connection warm-up.
- [x] **Admin TerraDraw lifecycle repair (`useTerraDraw.ts`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Cancels stale deferred style callbacks and removes only abandoned `td-*` artifacts before initialization, preventing duplicate MapLibre sources during repeated zone editing.
- [x] **Responsive status and safe configuration (`BaseMap.tsx`, `MapCanvas.tsx`, `apphosting.yaml`, `.env.local`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Positioned the recovery notice relative to the viewport, below the desktop floating navigation and with a width cap/wrapping for smaller screens.
  - Centralized MapTiler style construction under `NEXT_PUBLIC_MAPTILER_KEY`; App Hosting now references the `maptiler-api-key` secret rather than a literal production value.
- [x] **SSE database-pool resilience (`sync.py`, `database.py`, `main.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Removed the request-lifetime SQLAlchemy dependency from `/sync/stream`, moved active-zone queries to short-lived worker-thread sessions, and added fail-fast pool/JSON error handling.
- [ ] **Remaining verification** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): Confirm the MapTiler restoration path in a clean browser session and deployed Firebase build after creating/restricting the `maptiler-api-key` secret.

### Capstone Phase 23: Identity-First Google Authentication, Self-Service Password Recovery & Resilient Admin Routing (🟢 COMPLETED)
- [x] **Google OAuth Citizen Onboarding & Sign-In (`useGoogleAuth.ts`, `auth.py`, `auth_service.py`, `RegisterForm.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Implemented secure Google Identity Services ID token verification in FastAPI (`POST /auth/google`) using `google-auth` token decoders.
  - Sign-In Mode: Authenticates registered citizens and returns JWT access tokens with instant profile retrieval. If no account is registered, returns a structured 404 prompting the user to complete onboarding.
  - Sign-Up Mode: Automatically extracts verified name, email, and Google avatar, pre-populating citizen identity fields while guiding users to complete their local PSGC residential address before minting their account.
- [x] **Self-Service Forgot Password Recovery Flow (`ForgotPasswordForm.tsx`, `auth.py`, `auth_service.py`, `email_service.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Built a 3-step password recovery flow strictly matching the visual system of the register/login pages.
  - `POST /auth/forgot-password/request-otp`: Dispatches a single-use 6-digit OTP code to the registered email via the Resend REST API, enforcing progressive cooldown tiers (1m, 3m, 5m) with anti-enumeration response masking.
  - `POST /auth/forgot-password/verify-otp`: Validates the recovery OTP code and mints a cryptographically signed 15-minute `password_reset` JWT token.
  - `POST /auth/forgot-password/reset`: Verifies the reset token, enforces password complexity, commits the updated bcrypt password hash, and purges all active OTP records.
  - UI Features: 6-box auto-advancing OTP inputs with clipboard paste support, progressive resend countdown timer, `<PasswordStrength>` validation meter, and hold-to-view eye toggles.
- [x] **Resilient Admin Login Redirection & Route Guard Hardening (`LoginForm.tsx`, `login/page.tsx`, `useGoogleAuth.ts`, `NavigationWrapper.tsx`, `[BUG-034]`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Resolved `[BUG-034]`: Fixed inversion bug where guest commuter post intents (`lanes_post_intent`) and public URL redirect targets took precedence over role verification.
  - Authenticated admin logins (`Super Admin`, `DRRM Officer`, `Moderator`, and `*admin*`) now immediately purge commuter draft flags and route directly to `/admin/dashboard` (or explicit `/admin/*` deep links).
  - Preserved commuter navigation to `/feed?openPostModal=true` for drafted posts, explicit deep links, and default `/map`.
  - Hardened `NavigationWrapper.tsx` route guards to safely eject non-staff from `/admin/*` routes and keep `Super Admin` sessions centered on administrative operations.

### Capstone Phase 22: Private Valhalla Cloud Run Recovery (🟡 READY FOR CLOUD DEPLOYMENT)
- [x] **Resilient provider orchestration** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): Valhalla remains the default online engine; connection, timeout, identity-token, and 5xx availability failures retry through ORS while valid no-route responses do not.
- [x] **Private-service contract & responsive status** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): Route responses now identify the provider used and whether fallback occurred; the shared route state renders the same backup explanation in desktop and mobile layouts.
- [x] **Cloud deployment assets** ([@roicambe](https://github.com/roicambe) (Roi Cambe)): Added a versioned Cloud Storage artifact workflow and private `lanes-valhalla` Cloud Run deployment script with backend-only `roles/run.invoker` access.

### Capstone Phase 21: Production Cloud Infrastructure & Firebase App Hosting Deployment (🟢 COMPLETED)
- [x] **Next.js App Hosting Setup & Production Deployment (`apphosting.yaml`, `firebase.json`, `.firebaserc`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Initialized Firebase App Hosting in `frontend/` on project `lanes-project-508809` (backend `lanes-frontend` in `asia-east1`) with Node.js 22 automatic base image security updates.
  - Successfully verified production build and rollout to `https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app`.
- [x] **Production API Environment Variable Ingestion (`apphosting.yaml`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Configured `NEXT_PUBLIC_API_URL` (`https://lanes-api-557679867071.asia-east1.run.app/api/v1`) with `BUILD` and `RUNTIME` availability so Next.js embeds the live Cloud Run backend URL into client-side bundles during Cloud Build.
  - Configured `BACKEND_URL` (`https://lanes-api-557679867071.asia-east1.run.app`) with `RUNTIME` availability for server-side route rewrites.
- [x] **Backend Cloud Run CORS Expansion (`main.py`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Updated FastAPI `CORSMiddleware` `allow_origin_regex` to whitelist Firebase App Hosting domains (`https://.*\.hosted\.app`), Firebase Hosting web domains (`https://.*\.web\.app`), and Firebase project domains (`https://.*\.firebaseapp\.com`), unblocking cross-origin REST calls and persistent SSE streams (`/sse/stream`, `/sync/stream`).
- [x] **Environment Secrets Re-encryption & Git Hygiene (`.env`, `.gitignore`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Re-encrypted `backend/.env` using `@dotenvx/dotenvx` to prevent raw database credentials, Resend keys, and Google Routes API tokens from being tracked in cleartext.
  - Added `.firebase/` local cache and `firebase-debug.log*` patterns to both root and `frontend/.gitignore` files.

### Capstone Phase 19: Authentication Lifecycle, Resilient SSE Synchronization & 100MB Feed Media Pipeline (🟢 COMPLETED)
- [x] **Profile "Display Full Name" SQL Privacy Resolution & Comment Avatars (`feed.py`, `comments.py`, `posts.py`, `user.py`, `PostDetailPage.tsx`, `feedApi.ts`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Implemented server-side SQL `case()` evaluation in `feed.py` and `get_user_display_name` helper in `user.py` ensuring that `Profile.display_full_name` strictly governs whether the author's real full name or username handle appears across the Community Feed, post detail pages, and comments.
  - Added profile eager loading (`joinedload`) to comment queries, attached `user_id` and `author_avatar` to `CommentResponse`, and rendered author avatars in comment items.
  - Migrated frontend permission checks (`isPostAuthor`, `isOwn`) from username string matching to reliable numeric ID comparisons (`user.id === post.user_id` / `user.id === comment.user_id`).
- [x] **Profile Subtabs Mobile Margin Polish (`ProfileView.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Removed redundant mobile wrapper padding classes on Posts and Reports tabs, giving mobile users full-width cards without double-margin inset.
- [x] **Contextual Authentication Navigation (`FloatingNav.tsx`, `MobileNav.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Preserves current pathname context across unauthenticated navigation bar clicks, preventing accidental redirection diversion.
- [x] **Community Feed Mobile Responsiveness & Standalone Action Buttons (`PostItem.tsx`, `FeedPage.tsx`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Redesigned voting interactions in `PostItem.tsx` to use standalone `ArrowBigUp` and `ArrowBigDown` icon buttons without heavy pill enclosures, adhering to the "Anti Box-in-a-Box" principle.
  - Implemented responsive severity badges: compact (`Medium`, `High`, `Extreme`, `Low`) on mobile (<640px) and full (`Medium (Warning)`) on desktop/tablet (≥640px) to prevent post header crowding.
  - Resolved multi-row action bar wrapping on compact mobile devices (iPhone SE 375px, iPhone 12 390px) via responsive label management (`🗺️ Map` on mobile / `🗺️ View on Map` on desktop, hidden `Share` text on small screens), keeping all 4 primary actions on a single sleek row.
  - Enhanced composer placeholder responsiveness in `FeedPage.tsx` (`"What's happening?"` on small screens vs `"What's happening in your area?"` on larger viewports) and scaled touch targets (`w-5 h-5` icons, `p-2`) for comfortable mobile ergonomics.
- [x] **Community Post Moderation Center (`ModerationCenterPage.tsx`, `AdminSidebar.tsx`, `admin.py`, Alembic `d1f6e2a9b730`)** ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added a staff-only queue that groups open private reports by Community Post and exposes Dismiss, Warn, and Hide actions on desktop and mobile-safe layouts.
  - Resolving a case atomically updates every open report for that post, records the action and reviewer, optionally soft-hides the post from public feeds, and creates reporter/author system notifications.
- [x] **Registration Confirmation De-duplication** (`LoginForm.tsx`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Retained the global Account Created toast and removed the duplicate success banner displayed after the Login redirect.
- [x] **EventSource Zombie Connection & SSE Dev Proxy Resolution (`useLiveSync.ts`, `useSSE.ts`, `sse.ts`)** (@roicambe):
  - Fixed persistent zombie connections and connection thrashing by removing the restrictive `readyState === 1` guard during React StrictMode unmount cleanup, ensuring `source.close()` executes unconditionally.
  - Implemented centralized `getSseUrl('/sse/stream')` directing browser SSE connections straight to FastAPI on port `8000` in local dev/LAN, eliminating Next.js proxy response buffering and SSE dropouts.
  - Standardized error logging in `useLiveSync` from intrusive console.error floods to graceful `console.warn`.
- [x] **Auth Soft-Delete Re-registration Conflict & Explicit Login Flow (`auth.py`, `RegisterForm.tsx`, `LoginForm.tsx`)** (@roicambe):
  - Resolved `IntegrityError` unique constraint failure when a citizen whose account was previously soft-deleted attempts to re-register with the same email or username. The endpoint now distinguishes active collisions from archived ones, automatically purging stale soft-deleted records upon OTP verification to permit clean re-registration.
  - Corrected registration flow so citizens are not automatically logged in upon sign-up; registrations now clear draft states and redirect to `/login?registered=true`, displaying a prominent green alert banner informing the user to log in with their newly created credentials.
- [x] **100MB Feed Media & Video Streaming Pipeline (`next.config.ts`, `posts.py`, `cloudinary_service.py`, `CreatePostModal.tsx`)** (@roicambe):
  - Configured Next.js 15/16 proxy body limit via `experimental: { proxyClientMaxBodySize: '100mb' }` in `next.config.ts`, preventing the dev proxy's 10MB default buffer limit from dropping connections (`socket hang up / ECONNRESET`) while adhering to Next.js 16 configuration schema.
  - Elevated backend multipart upload size limit in `POST /posts` from 20MB to 100MB.
  - Enhanced Cloudinary upload service with MIME-type and file-extension inspection, automatically assigning `resource_type="video"` without image crop transformations for video files.
  - Updated `CreatePostModal.tsx` file limit from 20MB to 100MB and refined validation feedback to display a clear, descriptive toast ("File Limit Exceeded - [filename] ([size] MB) exceeds the 100MB maximum limit") and robust 413/network truncation handling.
- [x] **Post Media Draft Not Saved on Unauthenticated Login Redirect Bugfix (`CreatePostModal.tsx`)** (@roicambe):
  - Fixed a bug where images and videos uploaded into the Create Post modal were silently dropped when an unauthenticated user was redirected to `/login`. Two code paths were missing `await set('lanes_draft_files', ...)`: (1) `handleSubmit`'s no-token branch that shows the auth prompt, and (2) the auth prompt "Go to Login" button's `onClick`. Both now persist all selected `File` objects to IndexedDB via `idb-keyval` before any navigation occurs, ensuring the files are fully restored alongside the text draft when the modal re-opens after successful login.
- [x] **Feed Post Draft & Media Persistence on Browser Refresh (`CreatePostModal.tsx`, `FeedPage.tsx`)** (@roicambe):
  - Fixed an issue where refreshing the feed page while composing a community post discarded attached photos/videos, chosen location tags, and typed content.
  - Implemented continuous auto-saving of post text, location tags, and coordinates to `localStorage` (with `sessionStorage` fallback), and synchronization of attached `File` objects to IndexedDB via `idb-keyval`.
  - Removed premature deletion of IndexedDB draft files on modal restore, preserving draft files across multiple page reloads until explicitly published or discarded.
  - Added composer session restore in `FeedPage.tsx` to automatically reopen the modal with all text, location metadata, and media previews intact when the user refreshes `/feed`.

### Capstone Phase 18: Intelligent Flood-Report Merging & Spatial Operations Redesign (🟡 IN PROGRESS)
- [x] **Edit Zone Effective Flood-Report Data** (`zoneEditDraftStorage.ts`, `OfficialZoneDrawer.tsx`, `admin.py`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Falls back from empty zone overrides to the linked report’s depth, severity, survey answers, and description; original report evidence is rendered separately as read-only media.
- [x] **Edit Zone Baseline Draft Guard & Geometry Editing** (`zoneEditDraftStorage.ts`, `LiveMapPage.tsx`, `OfficialZoneDrawer.tsx`, `useTerraDraw.ts`, `admin.py`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Prevented false **Edit Restored** sessions by comparing the local values and new media with the freshly fetched zone baseline. Unchanged legacy records are deleted silently.
  - Added road-centreline replacement and exact saved-polygon vertex editing to the existing Edit Zone workspace. Line updates regenerate the existing 25-metre routing barrier; area updates replace the saved polygon and clear obsolete road source geometry.
- [x] **Landing Flood Insights Map Handoff** (`LandingView.tsx`, `MapContext.tsx`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Routes the landing **View Flood Analytics** action to `/map?panel=analytics`.
  - Opens the existing responsive Flood Insights panel through the map's URL-driven panel state.
- [x] **Primary-Tab Selected-Item Fly-To Repair** (`LiveMapPage.tsx`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Keeps the Pending and Active tab selections independent while returning the map only to the currently selected item for the tab being opened.
  - Explicit card or map-feature deselection clears that target, so switching back leaves the map in its current location.
- [x] **Recency-Ordered Secondary Workspace Tabs & Close Repair** (`LiveMapPage.tsx`, `MergeWorkspacePanel.tsx`, `OfficialZoneDrawer.tsx`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Keeps Create Zone first and shows Merge/Edit handles only after their workspace has been opened; the most recently opened workspace moves directly below Create Zone.
  - Keeps inactive workspace components mounted while switching, preserving the active form, workflow, scroll position, and selected context; an explicit Merge Close or confirmed Edit discard removes its corresponding tab/session.
- [x] **Flood Report Draft Eligibility & Scoped Clear** (`FloodReportPanel.tsx`, `floodReportDraftStorage.ts`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Replaced broad field-presence persistence with selected-road-plus-substantive-detail eligibility; UI toggles, wizard progress, survey visibility, and typed-only locations no longer create a restorable report.
  - Added severity deselection and a compact scoped **Clear** dialog: neutral **Clear all** removes queued drafts, map geometry, media, and account-private storage; rightmost red **Clear this page** preserves work on the other page.
- [x] **Flood Report Empty-Draft Guard** (`FloodReportPanel.tsx`, `floodReportDraftStorage.ts`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Added one shared meaningful-work classifier to both autosave and restoration. Blank IndexedDB records are now silently removed, while real road, severity, text, media, survey, progress, or queued-report work remains account-private and recoverable after refresh or sign-in.
- [x] **Independent Create and Edit Zone Workspaces** (`LiveMapPage.tsx`, `CreateOfficialZonePanel.tsx`, `OfficialZoneDrawer.tsx`, `ActiveZonesPanel.tsx`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Replaced the shared Create/Edit drawer state with independent Create and selected-zone Edit sessions. Desktop now retains a non-overlapping Create → Edit → Merge bookmark stack, with only one Pane 2 workspace visible at a time.
  - Preserved the one shared `OfficialZoneDrawer` form and all existing validation, persistence, media, and API behavior. Switching workspaces relies on the existing account-private IndexedDB drafts rather than discarding another session. Mobile adds an Active Zones Create entry point and an in-drawer workspace switch action.
- [x] **Decision #16 Mixed-Topology Segmentation** (`carriageway_service.py`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Uses Valhalla edge shape indexes to split mixed Start/End routes by road identity and traversability. Caruncho/Urbano-style reports retain their full selected line but receive an opposite carriageway only on the independently verified matching run; a short graph-mapped Y merge is retained only when it reaches that run's matching endpoint, while cross-street connectors remain stripped.
- [x] **Feed Road-Focus Pulse Alignment** (`PostItem.tsx`, `mapGeoUtils.ts`, `MapCanvas.tsx`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Replaced Feed's bounding-box geometry focus with travelled-road midpoint calculation and centers paired `MultiLineString` carriageways between their two directions. The temporary MapLibre pulse marker now uses a center anchor, so the red ring aligns exactly with the focused road coordinate.
- [x] **User Reports Serialization & Admin Map Initialization Stability** (`backend/app/crud/__init__.py`, `LiveMapPage.tsx`, `useMergePreviewLayer.ts`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Resolved `500 Internal Server Error` on `GET /api/v1/reports/me` by re-exporting `get_flood_reports_by_user`, `archive_flood_report`, and `restore_flood_report` in `backend/app/crud/__init__.py`.
  - Fixed persistent `ApiError: Zone not found (404)` toast on admin sign-in by automatically purging stale IndexedDB zone edit drafts via `discardZoneEditDraft`.
  - Prevented runtime crashes (`Cannot read properties of undefined (reading 'getSource')`) in `useMergePreviewLayer` by verifying `map.getStyle()` before querying sources and adding defensive unmount guards.
- [x] **Flood Preview Loading UX, Direction Swap & Explicit Defaults** (`LoadingOverlay.tsx`, `FloodReportPanel.tsx`, `carriageway_service.py`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - Replaced the inline road-verification loading message with the reusable blocking loading overlay while retaining non-blocking success/fallback explanations after verification.
  - Restored the shared Start/End swap control, made both-sides coverage explicitly opt-in, and changed flood depth/severity to an unselected required state with no silent `low` fallback.
  - Runs Start→End and End→Start Valhalla requests concurrently to reduce preview latency without weakening Decision #16 validation.
- [x] **Pending-Report Aura Endpoint Overspill Repair** (`usePendingReportsLayer.ts`) ([@roicambe](https://github.com/roicambe) (Roi Cambe)):
  - The geometry-source repair prevents off-road extensions. The pending-report translucent severity aura retains its zoom threshold, selected emphasis, and intentionally rounded endpoints and turns to match Active Zones and the public preview. Existing live MapLibre layers are also updated after navigation or Fast Refresh.
- [x] **Decision #16 Authoritative Road Preview & Same-Side False-Positive Repair** (`carriageway_service.py`, `routes.py`, `MapContext.tsx`) (@roicambe):
  - Reproduced the Caruncho-area failure where two nearby anchors produced an 834m legal-driving loop that was then misclassified as a divided carriageway.
  - Centralized raw Start/End preview generation in the backend, evaluates both travel directions, rejects excessive detours, and falls back to the selected line without inventing an opposite road.
  - Returns only the validated Valhalla road shape; raw Start/End clicks never become saved sidewalk connector segments, and public marker positions derive from the snapped preview endpoints.
  - Suppresses the temporary raw straight connector while verification is loading, so public and admin maps render only the final authoritative road geometry.
  - The shared public/admin MapLibre preview hook now draws one final orange dashed road geometry only; public pins move to its snapped endpoints rather than relying on connector or terminal-cap overlays.
  - Hardened counterpart validation with length-weighted traversability, two-sided offset probes, exact normalized road identity, road class, distinct OSM way IDs, reverse direction, length, overlap, separation, and loop guards.
  - Shared validation status and explanations across the public Flood Report and admin road editors; official zone and merge flows use validated `MultiLineString` coverage only when a distinct carriageway is proven.
  - Rebuilds every submitted road line at persistence time and submits verified dual coverage for two-way reports, keeping public preview, PostGIS geometry, and Pending Report rendering on one road-only contract. Focused pytest carriageway and merge-integrity suites, Python compilation, TypeScript checking, and the production frontend build passed; external reverse-geocoding testing remains network-dependent and manual desktop/mobile road verification is pending.
- [x] **Persistent Edit Zone Workspace and Active-Line Persistence** (`zoneEditDraftStorage.ts`, `OfficialZoneDrawer.tsx`, `LiveMapPage.tsx`, `admin.py`) (@roicambe):
  - Added account-private, per-zone IndexedDB edit workspaces that restore unsaved zone metadata, survey selections, notes, and local media after collapse, reload, or sign-in; Cancel Edit explicitly discards only that local workspace, while Save clears it only after the metadata and media operations succeed.
  - Added `updated_at` conflict baselines. When a shared zone was saved more recently by another administrator, the current server version is shown instead of silently applying stale local edits.
  - Persisted `source_geometry` for administrator-created Line zones, allowing the existing active-zone map layer to render the dark road centreline over the buffered avoidance polygon after a reload. Drawn area modes remain polygon-buffer-only.
  - Added authenticated `GET /admin/zones/{id}` and `POST /admin/zones/{id}/media` endpoints, plus migrations `2a4c8e91d605` and `0d5f7a6b4c11`. Repaired a migration-history mismatch without deleting zone rows; TypeScript, backend compilation, Alembic head verification, and production build passed. Developer-led UI verification remains pending.
- [x] **Account-Private, Editable Draft Workspaces (`floodReportDraftStorage.ts`, `zoneDraftStorage.ts`, `FloodReportPanel.tsx`, `OfficialZoneDrawer.tsx`)** (@roicambe):
  - Replaced device-wide draft queues with versioned IndexedDB records isolated by authenticated commuter or administrator identity; sign-out and account changes clear in-memory state before the next account is hydrated.
  - Saving a Flood Report or Create Zone draft now moves every active value into that draft and resets the form. Saved Drafts provides consistent back, edit, delete, discard-all, and batch-submit/publish controls.
  - Editing temporarily removes a selected draft, restores its route or Terra Draw shape, fields, notes, and media, then replaces the original on save; cancellation restores the untouched queue item. Create Zone submits media per queued zone instead of sharing the active form's files.
  - Successful submission clears persisted workspace only after all queued items succeed; failed submissions preserve drafts for recovery. TypeScript, production build, and whitespace checks passed; focused lint retains pre-existing rule violations in legacy map/panel components, and desktop/mobile manual verification remains pending.
- [x] **Create Zone Interaction Restoration & Resumable Drawer Session** (`AdminFloodMapInteraction.tsx`, `LiveMapPage.tsx`, `OfficialZoneDrawer.tsx`) (@roicambe):
  - Restored the shared MapContext Start/End map-picking flow for the admin line editor: crosshair cursor, automatic Start-to-End progression, persistent markers, and the public-map orange dashed route preview.
  - Preserved Create Zone state through its account-private draft workspace when the docked drawer is collapsed or another workspace is opened, avoiding concurrent MapContext editors while retaining the spatial mode, geometry, attributes, media, description, and draft-cart items on reopen.
  - Paused Terra Draw interaction and restored the normal map cursor while collapsed; shape geometry remains available when the drawer is reopened. The two-direction option is now limited to line geometries.
- [x] **Feature-Based Official Avoidance Zone Drawer (`OfficialZoneDrawer.tsx`, `zones/`)** (@roicambe):
  - Modularized `CreateOfficialZonePanel.tsx` from a 1,000+ line monolith into single-responsibility subcomponents: `GeometryModeSelector.tsx`, `RoadSegmentPicker.tsx`, and `DraftZoneCart.tsx`.
  - Reorganized into a clean 5-tier structure matching `FloodReportPanel.tsx`: 1. Spatial Geometry $\rightarrow$ 2. Hazard Attributes $\rightarrow$ 3. Survey (Passable Vehicles & Hidden Hazards) $\rightarrow$ 4. Photos & Videos $\rightarrow$ 5. Description.
  - Replaced manual severity buttons with an 8-tile visual depth gauge auto-deriving severity, and removed non-standard avoidance buffer width sliders.
  - Converted `POST /admin/zones` to multipart `FormData` with streaming Cloudinary uploads, persisting `media_urls` on `FloodAvoidanceZone` via Alembic migration `33ec62de236d`.
- [x] **Intelligent Multi-Factor Merge Candidate Engine (`merge_service.py`)** (@roicambe):
  - Engineered spatial corridor buffer calculation (`ST_Buffer(geom, 25m)`), intersection calculation (`ST_Intersection`), and Jaccard overlap ratio metrics.
  - Sourced Decision #16 Valhalla edge traces (`trace_road_attributes`) to group reports by true OpenStreetMap `way_id`, road classification firewall (preventing highway-service road merges), and azimuth alignment.
  - Implemented Linear Referencing synthesis: projected multi-user start/end coordinates onto road centerlines via `ST_LineLocatePoint` and sliced continuous merged lines via `ST_LineSubstring`.
  - Implemented multi-factor scoring (0-100) with explainable reasons, crowd consensus badge (score $\ge 80$), and automated conflict detection (severity, depth, passable vehicles).
- [x] **Decision #16 Decoupled Carriageway Service (`carriageway_service.py`)** (@roicambe):
  - Extracted Decision #16 bidirectional logic out of `valhalla_service.py` into a dedicated modular service (`find_opposite_carriageway`, `_shift_coords_perpendicular`, `decode_polyline6`).
  - Preserved backward compatibility by re-exporting methods through `valhalla_service.py`.
- [x] **Transactional Multi-Report Merge & Official Zone Creation (`admin.py`)** (@roicambe):
  - Created `GET /api/v1/admin/reports/merge-candidates?report_id={id}` and `POST /api/v1/admin/reports/merge`.
  - Supported creating brand new `FloodAvoidanceZone` entities or merging into existing active zones, applying user overrides (`passable_vehicles_override`, `hidden_hazards_override`, `merge_rationale`).
  - Preserved original crowdsourced reports, credited +5 Trust Score to each unique reporter, broadcasted real-time SSE event, and recorded audit trails.
  - Guaranteed 100% Community Feed post immutability (`community_posts` remain completely untouched when reports are merged or approved).
- [x] **Interactive Merge Workspace Interface & Live Map Resolution (`MergeWorkspacePanel.tsx`)** (@roicambe):
  - Replaced legacy duplicate grouping with explicit **Review Merge Suggestions** entry. Normal report focus is neutral and never blocks standalone approval.
  - Delivered a four-step workflow: Candidates, Compare, Edit Zone, and Confirm. Candidate inclusion is always explicit; recommendations and conflicts are recalculated from the selected reports only.
  - Added responsive field comparison, reusable road/Terra Draw geometry editing, map previews for primary/candidate/proposed geometry, recoverable query states, and a full-width mobile map/form switch.
  - Candidate evidence now lives inside its related report card, with a prominent checkbox selection control rather than a detached action button.
  - The Create Zone and Review Merge edge tabs act as contextual drawer handles: Review Merge appears only after a session starts, remains available after collapse, and retains its state until the focused primary report changes or the merge completes.
  - Manual desktop/mobile workflow and submission verification remains pending with the developer.
- [x] **Dual-Pane Master-Detail Sidebar / Slide-Out Drawer (`MergeWorkspacePanel.tsx`)** (@roicambe):
  - Implemented secondary slide-out drawer docking seamlessly alongside `PendingReportsPanel`, keeping the MapLibre canvas unblocked.
  - Designed the contextual four-step workflow: 1. Candidate Selection $\rightarrow$ 2. Compare $\rightarrow$ 3. Edit Zone $\rightarrow$ 4. Confirm.
  - Built `ReportComparisonCard.tsx`, `ReportComparisonMatrix.tsx`, `ConflictResolutionNotice.tsx`, and `MergeExplanationBanner.tsx`.
  - Integrated `useMergePreviewLayer.ts` to render vibrant multi-color candidate geometries alongside the primary report and proposed dashed merged geometry on the map.
- [x] **1 Zone = 1 Incident Draft Cart Pattern & Field Streamlining (`CreateOfficialZonePanel.tsx`, `ZoneDataEditorForm.tsx`)** (@roicambe):
  - Refactored zone drafting to ensure each official zone corresponds to exactly one incident with its own severity, depth, and survey attributes.
  - Enabled batching multiple official zones sequentially via a draft cart before atomic submission.
  - Streamlined flood zone creation and merging by removing manual zone naming (relying on clear location descriptions and real-world hazard conditions) and redundant scheduled status toggles (ensuring created flood hazard zones are automatically active `is_active: true`).
- [x] **Docked Secondary Drawer Architecture for CreateOfficialZonePanel (`CreateOfficialZonePanel.tsx`, `LiveMapPage.tsx`, `ActiveZonesPanel.tsx`)** (@roicambe):
  - Converted `CreateOfficialZonePanel` from a floating draggable card overlay into a docked secondary drawer (Pane 2) alongside the left sidebar (`md:w-[420px] xl:w-[460px] h-full bg-white border-r border-slate-200`), fully unifying it with the Dual-Pane Master-Detail architectural pattern established by `MergeWorkspacePanel`.
  - Lifted `MapProvider` to wrap the root layout of `LiveMapPage`, ensuring seamless shared MapContext across both drawers and the map canvas without nested providers.
  - Eliminated duplicate "+ Create Official Zone" and "New Zone" buttons across `ActiveZonesPanel` and `LiveMapPage` headers to maintain a single, intuitive point of interaction.
  - Implemented the physical "Drawer Pull Handle in Your Hands" edge toggle matching user sketch:
    - **Closed Handle (Pane 1 Edge)**: Sits at `top-3.5` on the right border of Pane 1, featuring a blue `Plus` icon badge, clear vertical typography (`CREATE ZONE`), and `ChevronRight`.
    - **Open Handle (Pane 2 Edge)**: Travels smoothly to the outer front edge of Pane 2 (`-right-9 top-3.5`), styled in dark slate with `ChevronLeft`, vertical `CLOSE DRAWER` typography, and smooth hover interaction to push the drawer shut.
    - **Smooth Drawer Slide Animation**: Powered by Framer Motion `<AnimatePresence>` with cubic-bezier easing (`[0.32, 0.72, 0, 1]`) from `width: 0` to `420px`/`460px`, paired with a continuous 35ms MapLibre canvas resize loop to ensure the WebGL viewport smoothly adjusts without jarring jumps.
  - Maintained full mobile PWA responsiveness (full-screen slide-over drawer on mobile viewports; docked side-by-side pane on desktop), dynamic map container resize tracking via `ResizeObserver`, and centered floating drawing instruction banner.
- [ ] **Automated Pytest & Integration Verification (`test_flood_report_merging.py`)** (@roicambe):
  - The suite covers candidate identification, multi-factor scoring, conflict detection, merge behavior, and feed post immutability. Its result is not recorded as passing here because pytest is unavailable in the current local environment; execute it in the configured backend test environment before closing Phase 18.

### Capstone Phase 16: Admin Map Controls & Component Standardization (🟢 COMPLETED)
- [x] **Universal MapLibre Preview Architecture (`useFloodMapPreview.ts`)** (@antigravity):
  - Extracted duplicated `flyTo` camera panning, orange/red MapLibre pins, and dynamic bidirectional orange-dashed preview layer logic into a single shared custom hook.
  - Sourced the preview hook directly into both `MapCanvas.tsx` (Commuter Flood Report) and `CreateOfficialZonePanel.tsx` (DRRMO Admin Zone), enforcing strict parity between public and admin interactions.
- [x] **TerraDraw Map Event Capture-Phase Override** (@antigravity):
  - Bypassed TerraDraw's strict `stopPropagation()` map click interception by attaching a native `{ capture: true }` event listener directly to the underlying canvas, allowing "Choose on Map" logic to receive map clicks without breaking the drawing engine.
  - Automatically advances "Choose on Map" logic from origin to destination selection on click, creating a seamless two-click location picking experience.
- [x] **Enforced Cursor Aesthetics & Input Refinement** (@antigravity):
  - Overrode TerraDraw's internal `mousemove` pointer hijacking by forcibly setting `cursor: crosshair !important` on both the canvas and its container whenever picking mode is active.
  - Stripped theme-specific orange border rings from generic `LocationInputGroup.tsx` inputs to maintain clean UI independence across components.

### Capstone Phase 15: Automated Street, Barangay & City Reverse-Geocoding for Flood Reports (🟢 COMPLETED)
- [x] **Multi-Provider Structured Reverse Geocoding Engine** (@roicambe):
  - Refactored `geocoding_service.py` to extract structured `ParsedLocation` models containing clean `street`, `barangay`, and `city` attributes alongside full formatted addresses.
  - Implemented OpenStreetMap Nominatim zoom-17 reverse lookup with automated fallback to Photon (Komoot) and hardened `User-Agent` headers against bot blocks.
  - Added clean prefix normalization (`_clean_barangay_name`) stripping redundant "Brgy.", "Barangay", and punctuation variations.
- [x] **Multi-Geometry Representative Coordinate Extraction** (@roicambe):
  - Engineered `extract_representative_coordinates` in `report_service.py` supporting `Point`, `LineString`, `MultiLineString`, and `Polygon` geometries by computing topological midpoints across multi-vertex road segments.
- [x] **Database Schema & PostGIS City Column Migration** (@roicambe):
  - Added indexed `city: Mapped[Optional[str]]` (VARCHAR 100) column to `flood_reports` via clean Alembic migration `a66a677fa71a_add_city_to_flood_reports.py`.
  - Updated Pydantic schemas (`FloodReportBase`, `FloodReportCreate`, `FloodReportResponse`) and CRUD layer (`app/crud/report.py`) to persist and return `barangay` and `city`.
- [x] **Historical Database Report Backfill** (@roicambe):
  - Developed and executed `backend/scripts/backfill_report_locations.py`, successfully updating all 13 existing database flood reports with accurate streets (e.g. C. Raymundo Ave, E. Rodriguez Jr. Ave, Dr. Sixto Antonio Ave, A. Mabini St), barangays (Maybunga, Ugong, Kapasigan, Rosario), and city (Pasig).
- [x] **Frontend Moderation & Reporting Synchronization** (@roicambe):
  - Updated `FloodReportPanel.tsx` to forward autocomplete street labels as server-side location hints.
  - Updated `adminApi.ts`, `ReportDetailsModal.tsx`, and `PendingReportsPanel.tsx` to dynamically render `{report.barangay ? \`Brgy. ${report.barangay}, ${report.city || "Pasig"}\` : (report.city || "Pasig City")}` and explicit road segment names.
- [x] **Community Feed Post Location Refinement & Deduplication** (@roicambe):
  - Streamlined `PostItem.tsx` by eliminating redundant secondary blue text location buttons positioned below the severity badge.
  - Consolidated header location display with red pin fallback (`post.location_tag || post.report?.human_readable_location || (post.report?.barangay ? \`Brgy. ${post.report.barangay}\` : null)`), smoothly flying to map coordinates on click.
  - Preserved primary "View on Map" action button in the bottom interaction bar exclusively for shared flood reports (`post.report?.geometry && onViewMap`).
  - Added optional `barangay` and `city` properties to `FeedPost.report` in `frontend/src/features/feed/feedApi.ts`.
- [x] **Automated Test Suite Verification** (@roicambe):
  - Added unit and integration tests in `backend/tests/test_report_geocoding.py` testing prefix cleaning, coordinate extraction, async reverse geocoding, and automated DB report location persistence.

### Capstone Phase 14: Route Focus, Saved Places & Map Polyline Engine (🟢 COMPLETED)
- [x] **Map-Click Input Protection & Two-Click UX** (@roicambe):
  - Added synchronous `isPickingRef.current` guards in `MapCanvas.tsx` preventing map clicks and panning from accidentally overwriting focused location input text fields.
  - Streamlined "Choose on Map": selecting origin automatically advances target focus to destination (`activePoint = "end"`), enabling single-click destination placement on the map.
- [x] **Sequential Saved Places Recalculation** (@roicambe):
  - Refactored `handleSelectSavedPlace` in `RoutePanel.tsx` so that selecting a saved place when both start and destination are already filled updates Start first and shifts focus to Destination, allowing a second click to set Destination and immediately calculate the route.
- [x] **Resilient MapLibre Route Polyline & Gradient Engine** (@roicambe):
  - Replaced fragile `map.isStyleLoaded()` checks with `map.getStyle()`, preventing route drawing from being permanently dropped when background tiles or live flood zone feeds (15s polling) are in-flight.
  - Added persistent `map.on("style.load")` listener ensuring route polylines are restored across 3D terrain toggles and map style switches.
  - Added reliable `"line-color": "#2563eb"` fallback with `"line-gradient"` interpolation when intersecting flood zones.
  - Added automatic camera `map.fitBounds()` with device-aware padding framing the calculated route and pins in view.
- [x] **Sign-Out Memory Cleanup & RoutePanel Auth Guarding** (@roicambe):
  - Added `else { setSavedPlaces([]); }` cleanup in `GlobalMap.tsx` so saved places in context and their map markers are wiped immediately upon sign-out.
  - Guarded saved places quick chips with `isAuthenticated` in `RoutePanel.tsx` across both mobile and desktop viewports.
- [x] **PostGIS Coordinate Persistence** (@roicambe):
  - Added nullable `location_lat` and `location_lng` (Float) columns to `community_posts` with Alembic migration `84c00c5d976b_add_lat_lng_to_community_posts.py`.
  - Updated SQLAlchemy models, Pydantic schemas, and CRUD layers (`backend/app/crud/post.py`) to accurately ingest, store, and return geographic coordinates.
- [x] **Clickable Location Pin Header Navigation** (@roicambe):
  - Streamlined `PostItem.tsx` header location tags: made the red pin location tag directly clickable to trigger a camera fly-to on `/map`.
  - Eliminated redundant blue location badges and duplicate "View on Map" buttons for non-flood community posts.
- [x] **340px Sidebar Viewport Alignment & ResizeObserver Engine** (@roicambe):
  - Added native `ResizeObserver` to `BaseMap.tsx` watching the map container to instantly synchronize MapLibre dimensions with layout mutations.
  - Added layout reflow synchronization in `MapCanvas.tsx` to center coordinates precisely in the visible map area, resolving the 170px rightward offset caused by the fixed desktop routing panel.
- [x] **Resilient Post Draft Hydration Across Auth Redirection** (@roicambe):
  - Fixed post draft persistence in `CreatePostModal.tsx` so typed descriptions, attached media, and picked locations survive across login and signup redirects (`/auth/login?redirect=...`).
  - Resolved draft auto-append and deletion bugs, and prevented default city bounds fit from competing with specific coordinate navigation.

### Capstone Phase 12: Saved Places Camera Synchronization & Navigation UX (🟢 COMPLETED)
- [x] **Camera Transition & Visual Indicator Synchronization** (@roicambe):
  - Aligned saved place camera focus transitions to match hazard zones (zoom 16, 1500ms duration, easing curve).
  - Wired `fly-to-location` custom events to `MapCanvas.tsx` with a high-visibility 3-second pulsing red circular marker.
- [x] **Saved Places Panel Activation & Zero-Caret Fix** (@roicambe):
  - Updated community feed saved place quick pills to open the Saved Places panel directly instead of erroneously setting origin routing pins.
  - Eliminated browser text insertion carets on saved place clicks using `select-none` and `caret-transparent`.
- [x] **Custom Scrollbar Styling & Pin Order Integrity** (@roicambe):
  - Added custom slim scrollbar styles to `LeftSidebar.tsx` that smoothly appear on hover.
  - Fixed a backend bug in `crud/saved_place.py` where `pin_order` was unintentionally overwritten during place metadata updates.
- [x] **Secure Cross-Platform Environment Encryption** (@roicambe):
  - Encrypted `backend/.env` with `@dotenvx/dotenvx` and consolidated pull workflow and encryption key setup instructions into `README.md`.

### Capstone Phase 11: Community Feed Emergency Hotline Directory (🟢 COMPLETED)
- [x] **Cached Hotline Aggregation** (@roicambe):
  - Added public `GET /api/v1/hotlines/` and `GET /api/v1/hotlines/full` endpoints.
  - Scrapes national emergency contacts and Pasig government contacts with one-hour server-side TTL caching.
- [x] **Feed Emergency Contact UX** (@roicambe):
  - Replaced static emergency entries with API-backed priority hotline cards.
  - Added expandable phone numbers, `tel:` links, loading/unavailable states, and a lazy-loaded national/Pasig/barangay directory modal.

### Capstone Phase 10: Spatial Operations Live Map & Hover Interaction Engine (🟢 COMPLETED)
- [x] **Multi-Geometry Layer Normalization** (@roicambe):
  - Fixed layer geometry filtering in `usePendingReportsLayer.ts` and `useFloodZonesLayer.ts` to support `MultiLineString` and `Polygon`/`MultiPolygon` (matching PostGIS bidirectional and merged hazard geometries).
  - Added dedicated `all-pending-reports-polygon-layer` with opacity steps matching design system standards.
- [x] **Zero-Flicker 400ms Hover Dwell Timer** (@roicambe):
  - Implemented `pendingHoverIdRef` to prevent mouse movements from resetting the dwell countdown while hovering within the same zone.
  - Eliminated map auto-panning (`map.panBy`) on hover to guarantee stationary, reliable inspection without cursor disengagement.
- [x] **Ceiling Collision & Smart Anchor Positioning** (@roicambe):
  - Added a 420px vertical clearance threshold to prevent badges from clipping into top navigation bars.
  - Implemented automatic anchor flipping to `top` (rendering downwards into open map space) when hovering near the upper viewport, and dynamic tip tinting to match the header severity color.
- [x] **Two-Row FloodZonePopup & Vehicle Chips** (@roicambe):
  - Redesigned `FloodZonePopup.tsx` with a clean two-row header: Severity + Status Badge on Row 1, full-width `Reported [Date]` on Row 2.
  - Rendered `passable_vehicles` as independent rounded badge chips rather than comma-delimited strings with awkward line wraps.
  - Removed container borders and set `background: transparent` on MapLibre popup content in `globals.css` to eliminate subpixel white hairlines.
- [x] **Report Details Modal Coordinate Safety** (@roicambe):
  - Safeguarded `ReportDetailsModal.tsx` against MultiLineString and Polygon geometries, preventing `.toFixed` runtime crashes when clicking the "Info" button.
- [x] **Lenis Smooth Scroll Scoping** (@roicambe):
  - Restricted Lenis smooth scrolling exclusively to Landing and About views, restoring native performant scrolling across the Admin Dashboard, Auth forms, and User Profile.
- [x] **MMDA Vehicle Passability Technical Audit** (@roicambe):
  - Authoritative reference document created in `docs/guides/vehicle-passability.md` mapping the 8 MMDA flood gauge levels to PostGIS severity zones and routing vehicle profiles.

### Capstone Phase 9: State Persistence & Resilient Offline Hydration (🟢 COMPLETED)
- [x] **Map Viewport Persistence** (@roicambe): Saved map center, zoom, pitch, and bearing to `localStorage` via `moveend` event listeners in `BaseMap.tsx` so users on poor connections recover their exact view on refresh.
- [x] **Draft Cart IndexedDB Hydration** (@roicambe): Integrated `idb-keyval` to safely persist drafted photo/video binaries and JSON draft arrays across hard browser reloads.
- [x] **Form Auto-Hydration** (@roicambe): Added robust `localStorage` sync to `FloodReportPanel.tsx` and `CreateOfficialZonePanel.tsx` to restore active form input text, checkboxes, and wizard steps automatically.
- [x] **Panel Memory & Collision Logic** (@roicambe): Saved `activePanel`, `isAnalyticsOpen`, and `lastOpenedLeftPanel` states to ensure stacked left-side panels (Analytics & Saved Places) remember their z-index and expansion states upon reload.
- [x] **MapLibre Auto-Recovery & Hot Reload Fixes** (@roicambe): Guarded layer mounting with `!map.isStyleLoaded()` to prevent MapLibre crash loops and fixed Fast Refresh dependency errors.

### Capstone Phase 7: Intelligent Bidirectional Flood Reporting — Hybrid Carriageway Detection (🟢 COMPLETED)
- [x] **Replaced CSS `line-offset` hack with real opposite-carriageway detection** (@roicambe):
  - Identified root cause: `line-offset: -8px` was purely cosmetic and placed the second line in the median of wide divided roads, not on the actual opposite carriageway.
  - Evaluated and rejected standard reverse routing (`/route` B→A) due to U-turn loop problem — the Valhalla engine generates legal driving routes, not parallel lines.
  - Evaluated and rejected fixed geometric offsets — variable road widths (3m narrow streets vs. 30m expressways) make any single offset value unreliable.
- [x] **Implemented Traversability-Aware Hybrid Detection Strategy** (`valhalla_service.py`):
  - **Traversability Inspection:** First traces the original coordinates via Valhalla `/trace_attributes` to check the `traversability` metric. Instantly classifies as `NARROW_TWO_WAY` if `both` is returned, aborting the search to save processing.
  - **Dynamic Offset Search:** If the road is `forward` (one-way or divided), it shifts coordinates perpendicularly to the left using a dynamic loop of increasing offsets: **5m, 10m, 15m, 20m, 30m**.
  - **Map Matching & Validation:** Reverses the shifted coordinates and snaps to the nearest road. Strictly compares matched edge names against the original road name to prevent false snapping to neighboring side-streets.
  - **Backend Name Extraction Fix:** Modified the validation to extract the original road name natively from the first Valhalla trace (bypassing the frontend which sends `null`). This fixed a critical bypass bug where the offset logic snapped to unnamed parking lots (Caruncho Ave) or completely different streets (C Santos St) because the firewall was unintentionally disabled.
- [x] **PostGIS GeometryCollection Storage** (`report_service.py`, `admin.py`):
  - Bidirectional reports now store `{ type: "GeometryCollection", geometries: [original_line, opposite_line] }` in `flood_reports.geometry`.
  - Admin approval updated to use `ST_ConvexHull(ST_Collect(ST_Buffer(line1), ST_Buffer(line2)))` — creating one accurate polygon that wraps both carriageways.
- [x] **New `POST /reports/preview-bidirectional` endpoint** (`reports.py`):
  - Accepts the original route coordinates and returns both `original` and `opposite` GeoJSON LineStrings.
  - Returns a strict `road_type` classification (`NARROW_TWO_WAY`, `DIVIDED_CARRIAGEWAY`, `TRUE_ONE_WAY`, `UNMAPPED`).
- [x] **Frontend real-time dual-line preview & Toasts** (`MapContext.tsx`, `MapCanvas.tsx`):
  - Added `floodOppositeGeometry` state to `MapContext`.
  - Parses `road_type` from the API. If `NARROW_TWO_WAY` or `TRUE_ONE_WAY` is returned despite the user checking "Affects both sides", the UI dispatches an informational toast and cancels the second line drawing.
- [x] **Map auto-recovery crash fix** (`useFloodZonesLayer.ts`):
  - Added `!map.getStyle()` safety guard to prevent `Cannot read properties of undefined (reading 'getSource')` crash during MapLibre style auto-recovery.

### Capstone Phase 8: Multi-Report "Draft Cart" Batch Submission (🟢 COMPLETED)
- [x] **Client-Side Draft Cart Implementation** (@roicambe):
  - Created `DraftReport` interface and `draftReports` global state in `MapContext.tsx`.
  - Updated `MapCanvas.tsx` to reactively render drafted reports as dashed purple (`#8b5cf6`) dashed lines alongside active lines.
- [x] **FloodReportPanel UI Overhaul (Commuters)**:
  - Added a "Draft Cart" list visualizing drafted street names and severities with a "Remove" button.
  - Implemented an "Add Another Road" secondary action button that stashes the current form into `draftReports` and resets the panel for the next road.
  - Refactored `handleSubmit` to iterate over `draftReports` with `Promise.all` and concurrently submit all reports, circumventing the need for a complex bulk backend endpoint.
- [x] **CreateOfficialZonePanel Overhaul (Admins)**:
  - Mirrored the draft cart UI logic for DRRMO Admins.
  - Extended the logic to support both `Line` (routed) and `Polygon` (drawn via TerraDraw) modes simultaneously in the same draft payload.
  - Added TerraDraw `drawRef.current.clear()` auto-reset upon stashing a draft.

### Capstone Phase 6: Official DRRMO Zone Creation & Terra Draw Vector Engine (🟢 COMPLETED)

- [x] **Migration from `mapbox-gl-draw` to `terra-draw`**:
  - Completely purged legacy `mapbox-gl-draw` and unmaintained circle/rectangle plugins.
  - Eliminated all Next.js Node.js module mocks (`fs`, `os`, `path` browser fallbacks in Webpack & `package.json`).
  - Integrated `terra-draw` alongside `terra-draw-maplibre-gl-adapter` for clean WebGL drawing without unmount leaks or React Strict Mode crashes.
- [x] **Interactive Multi-Geometry Drawing Toolbar**:
  - Implemented 5 shape modes in `CreateOfficialZonePanel.tsx`: **Line** (road segment), **Polygon**, **Freehand** (smooth pencil sketch), **Rectangle**, and **Circle**.
  - Defaulted to non-drawing `Line` mode to prevent unintentional map drawing triggers upon opening or expanding the panel.
  - Positioned floating drawing instructions as a sleek, bottom-centered overlay directly over the map canvas.
- [x] **Line Mode Alignment & Map Pin Synchronization**:
  - Unified Line selection with `FloodReportPanel.tsx` using Orange (`#f97316`) Start and Dark Red (`#991b1b`) End pins.
  - Enabled direct click-to-pick on the map canvas with crosshair cursor feedback and automatic step advancement.
  - Added live dashed road segment preview layer (`#f97316`) rendered along computed Valhalla road geometry.

### Capstone Phase 5: Multi-Engine Routing & Offline Architecture (🟢 COMPLETED)
- [x] **Triple-Path Routing Engine Architecture**:
  - **Valhalla HTTP (Online Primary)**: Integrated self-hosted Valhalla engine (`valhalla_service.py`) supporting dynamic `exclude_polygons` flood avoidance, multi-profile clearance routing (High Clearance, Low Clearance, Motorcycle, Walk), and multiple route alternatives (`alternates=2`).
  - **OpenRouteService (Online Secondary/Cloud)**: Integrated OpenRouteService API (`ors_service.py`) with geojson parsing and polygon-avoidance fallback for on-demand cloud routing.
  - **Valhalla WASM (Offline Client-Side)**: Custom Valhalla Core routing engine (`valhallaCore.ts`) executing WebAssembly worker off the main thread with IndexedDB tile mounting for 100% offline routing during severe connectivity loss.
- [x] **Fixed Left Sidebar Route Planner**:
  - Converted floating route window into a permanent 340px fixed left sidebar adhering to "Anti Box-in-a-Box" design principles.
  - Added dynamic routing engine switcher (`Valhalla` vs `OpenRouteService`).
  - Integrated `OfflineManager` directly into the sidebar footer.
  - Converted route calculation loading state to an inline non-blocking spinner (`variant="inline"`).
- [x] **Turn-by-Turn Navigation & Map Interactive Highlighting**:
  - Rendered step-by-step navigation instructions with directional maneuver icons, road names, and per-step distances.
  - Implemented interactive segment hover highlighting: hovering over any instruction highlights that road segment on the MapLibre canvas with a vibrant cyan glow.
  - Implemented click-to-focus: clicking a step smoothly flies the map camera to that maneuver segment midpoint.
- [x] **Data Synchronization & IndexedDB Storage**:
  - **Live Sync:** Server-Sent Events (SSE) listener in `sync.py` to stream `FloodAvoidanceZone` polygons into IndexedDB while the app is open.
  - Fixed polygon schema serialization for real-time broadcasts.

- [x] **3D Map Terrain & Seamless Zoom Visibility**:
  - Integrated AWS `terrarium-dem` S3 raster tiles for 3D elevation meshes in MapLibre GL JS v5.
  - Implemented `MapStylePickerControl` allowing commuters to swap between 5 dynamic vector basemap styles (Streets, Dark, Roads, Satellite, OSM).
  - Fixed polygon disappearance during perspective tilting by removing layer-level `minzoom`/`maxzoom` culling and replacing it with shader-level zoom-based opacity step expressions (`["step", ["zoom"]]`). Geometries remain stable across extreme pitch and zoom angles.
  - Upgraded Map Canvas UI with a new Toggle3DControl and ZoomLevelControl (with Pitch/P telemetry).

- [x] **Spatial Operations Persistence, Map Controls Uniformity & Centralized Camera Engine**:
  - **Persistent Layout in Admin Panel (`AdminLayout.tsx`)**: Mounted `<LiveMapPage />` persistently inside `AdminLayout` with zero unmount overhead, eliminating map reloads, tile re-downloads, and spinners when toggling between Reports, Dashboard, and Live Map.
  - **Unified Geometry Centroid & Camera Utilities (`mapGeoUtils.ts`)**: Built `flyToFeature()` and `flyToCoordinates()` with automatic midpoint calculation for Points, LineStrings, and Polygon buffers, enforcing a consistent 45° inspection angle, zoom 16, and 1400ms duration across Reports Moderation, Live Map URL queries, and direct map clicks.
  - **Deselection Camera Guards**: Guarded `ActiveZonesPanel.tsx`, `usePendingReportsLayer.ts`, and `useFloodZonesLayer.ts` so `flyTo` transitions only trigger upon item selection, preventing unwanted zooming/panning when deselecting.
  - **Pasig Boundary & Mask Fix**: Restored boundary and dark mask rendering in `useCityBoundaries.ts` by handling asynchronous MapLibre v5 style swaps during terrain initialization.
  - **Standardized Severity Badges**: Unified 4-tier color coding across all admin moderation cards, modals, and dropdowns (`low`: Lime `#84cc16`, `medium`: Amber `#eab308`, `high`: Orange `#f97316`, `extreme`: Red `#ef4444`).
  - **Default Global Map Top-Down Orientation**: Configured default `pitch: 0` for initial map instantiations.

## Recently Completed
- [x] **UI/UX & Scrolling Polish**:
  - Global Lenis smooth scrolling optimization (resolved transition glitches, ensured universal coverage across About, Profile, Feed, and Landing).
  - Refined mobile glassmorphism and reduced opacity on Login/Registration cards.
  - Adjusted landing page typography and responsive text scaling for improved legibility.
- [x] **Reports Page & Spatial Operations Integration**: Fully integrated the Reports Page with the Live Map. Added master-detail rich view for reports (including images/videos) and bidirectional "View on Map" / "Info" linking.
- [x] **MapLibre Rendering Stability**: Refactored `useFloodZonesLayer` to use `.setData()` and bypass strict `isStyleLoaded` checks, fixing the silent deadlock where layers wouldn't render during vector tile downloads.
- [x] **Spatial Operations Selection Fix**: Ensured clicking the main active zone wrapper card correctly un-sets any focused `selectedContributorId`, returning the map view to the primary merged polygon.
- [x] **Saved Places Feature**: Integrated "Saved Places" with map picking, saved places feed integration, mobile drawer support, custom emoji saving, and database persistence.
- [x] **Progressive Web App (PWA) & UI Fixes** (Installability banner, offline fallback, comment UI overhaul, safe area paddings)
- [x] **Documentation Update**: AGENTS.md and DESIGN.md updated with latest architecture.
- [x] Implement Comments Section for community feed (Threaded quote replies, mention parsing, pin/edit, dynamic focus-within input forms)
- [x] Implement Photon API Reverse Geocoding on backend to extract and save 'barangay' for approved reports
- [x] Create /api/v1/analytics/heatmap and /api/v1/analytics/stats endpoints
- [x] Build /analytics (public) and /admin/analytics pages with MapLibre Heatmap layer and data tables
- [x] Design Decision: Reverse geocoding via Photon is used to resolve barangays dynamically without storing heavy shapefiles
- [x] **Security & Local Networks**: Refactored real-time updates from WebSockets to SSE, applied `slowapi` rate limiting, restricted CORS, and implemented frontend route guards for future APK compatibility.
- [x] **UI/UX Refinements**: 
  - Extracted Login to a standalone page to prepare for future profile customization UI.
  - Fixed map white screen issue occurring after user logout.
  - Removed hover effects from Admin Dashboard severity charts for cleaner UX.
- [x] **Data Integrity**: Ensured specific flood depth strings (e.g., "Half-Knee") are successfully passed from the frontend and explicitly saved into the PostgreSQL `FloodReport` and `FloodAvoidanceZone` records.
- [x] **User Metrics & Profile Page**: 
  - Track metrics and build the frontend Profile UI for users.
  - *Backend Implementation:* Added `reports_submitted`, `reports_approved`, `reports_rejected`, `accuracy_rate`, `trust_score` columns to `profile.py`. Added endpoints `/api/v1/reports/me` and `/api/v1/posts/me` for user activity history. Added address schemas support for profile updating.

  - *Logic:* Trust score starts at 50. +5 for every approved report (cap 100), -10 for rejected (min 0). Accuracy = Approved / (Approved + Rejected).
  - *Frontend Implementation:* Built `ProfileView.tsx` with metrics cards, user details, tabs for "My Reports" and "My Posts", and a robust PSGC-integrated `EditProfileForm` component.
- [x] **Rich Community Posts on Profile Page**:
  - Reused `PostItem` from the feed to bring media galleries, upvotes, comments, and map linking to the user's Profile View.
  - Implemented dynamic scroll-to-stick sidebar logic for the profile metrics pane.
  - Redesigned profile tab navigation to a sleek hypertext style with a bottom-border active indicator.
- [x] **Auth Flow & Security Upgrade (Identity-First)**:
  - Completely restructured the registration flow to be "Identity-First" (Email -> OTP -> Username/Password -> Profile -> Address).
  - Decoupled OTP validation from account creation using new `/api/v1/auth/request-signup-otp` and `/verify-signup-otp` backend endpoints.
  - Seamless automatic login upon successful registration; removed the standalone `/verify` page completely.
  - Added modern "Sign in with Google" UI buttons to the Login and Registration forms.
- [x] **Profile & Feed UI/UX Polish**:
  - Implemented seamless 3-column "Feed Morph" mode for viewing posts inside the Profile page without route switching.
  - Added sticky frosted-glass "Back to Feed" / "Close" buttons for deep comment scrolling.
  - Dynamically hide the mobile notification bell when reading full posts.
  - Fixed full-width cover photo container layout on Profile page.
  - Updated design guidelines to formally ban "Box-in-a-Box Syndrome" for flatter, breathable UI.
- [x] **Dynamic Panel Stacking & Smooth Animations**:
  - Implemented dynamic global Z-indexing engine in `MapContext` allowing windows to pop to the front on-click or on-open (similar to OS windows/browser tabs).
  - Perfected panel dodging choreography: Swapped bouncy spring physics for predictable ease-in-out tween animations. Panels now smoothly collapse (250ms), slide (300ms), and enter with synchronized delays to prevent overlapping or jittering.
  - Fixed Save Place icon selector layout using smart CSS Grid to ensure perfectly distributed rows without trailing white space.
- [x] **Modular Map Architecture & Admin Live Map Overhaul**:
  - Created standalone, unopinionated `<BaseMap>` component (`src/shared/ui/BaseMap.tsx`) for clean map canvas instantiation.
  - Built pluggable layer hooks: `useCityBoundaries` (Pasig/Philippines borders & dark mask) and `useFloodZonesLayer` (active flood polygons, road glows, popups).
  - Merged Admin Live Map & Zones into a split-screen interface powered by `<BaseMap>`.
  - Fixed flood polygon rendering bug: Removed restrictive road-based polygon filter so exact flood polygons are rendered for all active hazard reports.
  - Standardized 4-tier severity color scale: `low` (Lime `#84cc16`), `medium` (Amber `#eab308`), `high` (Orange `#f97316`), `extreme` (Red `#ef4444`).
- [x] **Flood Zone Popup Redesign & Metadata Integration**:
  - Overhauled `FloodZonePopup.tsx` with dynamic severity-matched header background, vehicle passability survey results, reporter identity with role badges (e.g. DRRMO Officer, Admin, Moderator, Commuter), and reported flood depth indicators (e.g. Gutter, Half Knee, Tire).
  - Switched map hover/click interactions dynamically: hover trigger on desktop vs. tap trigger on touch/mobile devices.
  - Added full reporter metadata (`reporter_name`, `reporter_role`, `report_text`, `vehicles_passable`, `hazards_hidden`, `depth_estimate`) to backend `FloodAvoidanceZone` models and schemas.
- [x] **Database Sanitization Script**:
  - Created `backend/scripts/clear_db.py` to truncate all flood reports, avoidance zones, community posts, comments, notifications, and user profiles while safely preserving system roles and the default admin account.
- [x] **Admin Analytics & Live Map Integration**:
  - Merged the standalone Analytics dashboard into the Admin Live Map & Zones page. Removed the `/admin/analytics` route and sidebar entry.
  - Added an Analytics MapLibre control button to the bottom-right of the map to toggle the floating insights panel and activate the heatmap layer.
  - Added a dedicated "Export to CSV" button in the top-right corner of the map canvas for exporting barangay and street flood statistics.
  - Stacked bottom-right map controls in exact order: Analytics (top), Navigation/Zoom (middle), Top View (bottom).
  - Refactored AdminSidebar to expand as an overlay drawer so map canvases and floating panels remain completely stationary during navigation.

- [x] **OTP Verification Lifecycle, Progressive Cooldown & Zero-Click UX**:
  - Implemented progressive cooldown tiers for OTP requests (1 min -> 3 mins -> 5 mins) to prevent gateway abuse while allowing enough time to check spam folders.
  - Implemented sliding grace window retaining up to 3 unexpired active codes for delayed network/mobile deliveries.
  - Added attempt throttling (up to 5 incorrect guesses) with a 5-minute brute-force lockout.
  - Upgraded frontend to zero-click automatic verification upon entering/pasting the 6th digit, with automatic input clearing on error.
  - Redesigned OTP view with 6 interactive pin boxes, inline verification indicator, and clean bottom navigation actions (Change Email & Resend Code).
  - Integrated official LANES CDN brand header into Resend transactional email templates without downloadable attachments.
  - Created automated Pytest suite in `backend/tests/test_otp_lifecycle.py` verifying cooldowns, grace periods, and lockout rules.

### Phase 2: Spatial Moderation, 1:N Deduplication & Fluid Spatial Hub (🟢 COMPLETED)
- [x] **Backend — 1:N Relational Schema Migration**:
  - Inverted the foreign key constraint by moving `zone_id` onto `FloodReport` (`ondelete="SET NULL"`) and adding `curated_by_admin_id` to `FloodAvoidanceZone`.
  - Executed Alembic migration `e89a3df04c63_phase2_spatial_dedup_1_to_n.py`.
- [x] **Backend — Spatial Moderation & Proximity Lookup**:
  - Implemented `POST /api/v1/admin/reports/{id}/approve` supporting both `"CREATE_NEW"` and `"MERGE"` zone actions with automatic PostGIS buffer geometry calculation.
  - Implemented `GET /api/v1/admin/zones/nearby` with PostGIS `ST_DWithin` and `ST_Distance` returning nearby active zones within 500m.
  - Implemented `GET /api/v1/admin/reports/by-location` to group overlapping pending reports by street.
- [x] **Backend — Communal Trust Score Crediting**:
  - Updated approval & merge logic to iterate through all linked reports to award verified trust scores (`+5`) and increment `reports_verified` for every unique contributor.
  - Passed automated test suite `backend/tests/test_spatial_merging.py` (100% passing).
- [x] **Backend & Frontend — Multi-Reporter Contributor Serialization**:
  - Added `contributors` list to `FloodAvoidanceZoneResponse` and `ZoneContributorResponse` schema serializing each merged contributor's name, role, trust score, raw text, timestamp, and original PostGIS geometry.
- [x] **Frontend — Shared Fluid UI Design System**:
  - Created standardized animated `Tabs.tsx` with `segmented`, `underline`, and `pills` variants and hidden overflow wrappers to eliminate horizontal scrollbar flicker.
  - Standardized tab design across Profile, Live Map, Reports, User Registry, and Archive pages.
- [x] **Frontend — Edge-to-Edge Spatial Workspace & Viewport Persistence**:
  - Refactored `AdminLayout.tsx` and `LiveMapPage.tsx` to remove outer margins/padding (`p-0` on `/admin/map`) for a full-bleed interactive map canvas adhering to Anti Box-in-a-Box rules.
  - Implemented whole-Pasig-City bounding box auto-fitting (`[121.0515, 14.5338]` to `[121.1112, 14.6235]`) on first visit.
  - Implemented persistent camera viewport tracking via `localStorage` restoring exact pan/zoom coordinates across admin page navigation.
  - Guarded MapLibre layer hooks against async style switching and OSM fallback loading.
- [x] **Frontend — Shared Map Styling Architecture & Strict Zoom Thresholds**:
  - Created centralized tokens in `mapStyles.ts` and `mapGeoUtils.ts`.
  - Zoom $\le 14$: Crisp city-overview circle map pins with darker contrast borders.
  - Zoom $> 14$: Street-level transparent avoidance buffer auras and solid natural-color road lines with zero outline borders.
  - Added live compact `ZoomLevelControl` indicator in `BaseMap.tsx`.
- [x] **Frontend — Multi-Reporter Contributor Accordion & Single-Report Map Focus**:
  - Interactive inline drawer in `ActiveZonesPanel.tsx` with distinct user cards, avatar initials, primary/merged badges, and hover animations.
  - Clicking any contributor temporarily hides the merged parent avoidance zone and dynamically displays ONLY that contributor's original individual report geometry on the map.
  - Synchronized smooth 45° angled 3D camera transitions (`zoom: 16`, `pitch: 45`, `duration: 1500ms`) across sidebar and map clicks.

### Capstone Phase 4: Admin Panel & Report Moderation (🟢 COMPLETED)
- [x] **Active Zones Full View**: Show timeline, reporter details, and actions (View, Edit, Deactivate, Archive).
- [x] **Admin Dashboard Charts**: 
  - Pie Chart: Flood Severity Distribution.
  - Line Chart: Reports over time (Dynamic: Last 7 Days, Month, Year).
  - Bar Graph: Top 5 Most Flooded Barangays.

### Capstone Phase 3: Community Feed & Notifications (🟢 COMPLETED)
- [x] **Report Hazard Button**: Jump straight to the Flood Report Panel.
- [x] **Create Post Button**: Allows users to post text/photos to the community feed with an optional location tag.
- [x] **In-App Notification Center**: Global Bell Icon for comments, likes, and critical system alerts pinned to the top.

### Capstone Phase 2: Map & Routing Engine (🟢 COMPLETED)
- [x] **Vehicle Profiles**: Implement clearance-based routing labels:
  - *4-Wheel High Clearance* (SUVs, Pickups)
  - *4-Wheel Low Clearance* (Sedans, Hatchbacks)
  - *2-Wheels* (Motorcycles, Bicycles)
  - *Pedestrian* (Walking)
- [x] **Route Metrics**: Display "Safety %" and "Flood Risk" directly on alternative route banners.
- [x] **Flood Timelines**: Show when a flood was reported and approved directly on the map popup.
- [x] **Weather & Chart Legend**: Add a sleek UI guide/legend near the forecast chart to explain what the weather icons, rain percentages, and volume numbers mean to everyday users.
- [x] **AI Weather Insights**: Integrate OpenRouter API (`openrouter/free`) into the backend to dynamically generate educational, conversational interpretations of raw weather forecast data.

### Capstone Phase 1: Home Page & Onboarding (🟢 COMPLETED)
- [x] **Dynamic Weather Widget**: Integrate Open-Meteo API with Meteocons (reads from user profile location, defaults to Pasig).
- [x] **Daily Stats**: Show the number of *verified* flood reports for the current day.
- [x] **Site Visitors**: Display a metric for total active/historical site visitors.
- [x] **Flood Status Legend**: Add a clear breakdown of White, Yellow, Orange, and Red on the home page.

### Phase 1: Audit Trail Synchronization & Full Coverage (🟢 COMPLETED)
- [x] **Backend — Role Management Auditing**:
  - Add `create_audit_log` call to `POST /api/v1/roles` (`CREATE_ROLE`) logging `role_name` and initial `permissions`.
  - Add `create_audit_log` call to `PUT /api/v1/roles/{role_id}` (`UPDATE_ROLE`) logging previous vs. new permissions and name.
  - Add `create_audit_log` call to `DELETE /api/v1/roles/{role_id}` (`DELETE_ROLE`) capturing target role ID and name.
  - Add `create_audit_log` call to `POST /api/v1/roles/{role_id}/clone` (`CLONE_ROLE`) capturing source role ID and cloned role name.
  - Pass `Request` object into each endpoint function to extract `client_ip` via `request.client.host`.
- [x] **Backend — Archive & Soft-Delete Auditing**:
  - Dispatch explicit audit events (`ARCHIVE_REPORT`, `RESTORE_REPORT`, `ARCHIVE_ZONE`, `RESTORE_ZONE`) when flood reports or zones are archived/soft-deleted or restored.
- [x] **Frontend — Badge & Filter Synchronization**:
  - Update `ACTION_BADGES` mapping with styling and human-readable labels for:
    - `UPDATE_ZONE`, `CREATE_USER`, `UPDATE_USER_ROLE`, `CREATE_ROLE`, `UPDATE_ROLE`, `DELETE_ROLE`, `CLONE_ROLE`, `EXPORT_DATA`, `UPDATE_SETTINGS`, `ARCHIVE_REPORT`, `RESTORE_REPORT`, `ARCHIVE_ZONE`, `RESTORE_ZONE`
  - Update the `Filter Activity` `<Select />` options list to include these actions so admins can easily filter the log table.
