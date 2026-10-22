# Phase C3b — RSS admission, native readers and downstream integration

> **Last Updated:** October 21, 2026, 12:35 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: controlled local C3b acceptance passed.** The backend now connects admitted RSS bodies to native captures, one supervised NER session, saved evidence, intended-method readers and the existing downstream gates. Scheduled production processing remains legacy; this does not ship the frontend or authorize cloud changes. [Aggregate](summary.json) · [Roadmap](../../task_plan.md#phase-c--connect-automatic-article-processing) · [Integration contract](../../plans/rss-ner-integration-contract.md).

## Implemented behavior

RSS parsing retains the selected original publication wording and whether it supplied a timezone. Native capture binds that proof to the exact article input; normalized timestamps cannot manufacture missing provenance. Equivalent RFC/ISO dates from duplicate feeds retain the first matching explicit proof. Failed refreshes preserve the earlier complete body and its evidence. Changed bodies, corrections and revised proof produce immutable captures rather than overwriting history.

Native admission preserves publisher, selection, locality, age, retrieval/redirect, completeness, size and duplicate protections. It admits potentially relevant readable bodies without requiring the old location extractor to recognize a road first. Preliminary shortlisting is not independent flood verification. Forecasts, prevention stories, captions, historical reports, negation and non-local evidence remain ineligible for verified current publication. The collector retains its existing commuter budget of 14 per run/four per feed; the contract's earlier two-per-feed wording was corrected to the implementation, without changing policy.

Native capture preserves the exact parser-produced Unicode body, including whitespace; legacy body normalization stays unchanged. Readable minimum length is still 120 characters and the exact input maximum remains 100,000 characters. Original neural mentions, effective mentions, ordered repairs, grouped and unresolved facts, qualifiers, temporal roles and provenance remain intact. Depth/time extraction is rule based. No model, tokenizer or qualified location/grouping rules changed.

Saved results include a bounded, independently recomputable `ner-result-read-v1` projection. SQL readers filter/count/page the intended method and pipeline, including native-only joint, collective and LOCAL_AREA groups without inventing per-road claims. A newer pending/failed run does not revive older main-list cards. Details retain exact evidence and actual linked lifecycle records; extraction completion alone never means publication. Unsupported older inspection-only shapes fail visibly rather than being silently upgraded. Unknown confidence stays null through placement/preview consumers.

Existing active-admin authorization protects reads, including the additive `/api/v1/admin/news/results/{run_id}/groups/{group_id}` route. GETs never collect, infer or write. The internal reader-context dependency defaults to legacy, so native selection is explicitly injected for controlled acceptance. Existing frontend types and screens have not been changed.

Native evaluation uses independently trusted assets and `source-ner-v1`, not agreement with the old recognizer. Placement and publication remain downstream, with existing geometry, freshness, conflict, expiry, access and citizen-moderation gates. Only representable supported single-target observations enter compatibility claims. Native-only groups remain inspectable; this delivery does not qualify new joint-target geometry or automatically publish those groups. Missing supported observation time remains review-only.

Correction reconciliation also runs at version level when a new native result has no compatibility claims or fails. It appends an idempotent maintenance/review decision to already-linked cases, preserving earlier evidence and expiry; absence, failure or a zero-claim result cannot clear a road. Newer native runs of any status prevent stale older-run publication. Existing clearance/zone regressions pass; no broader clearance capability is claimed.

## Budgets and isolation

The separate `scripts.run_news_ner_pipeline` entrypoint requires Linux, test configuration and the actual owned `lanes_p3_verify_*` database. Defaults/scheduler remain unchanged. It authenticates assets before collection/claims and exposes bounded stage summaries/errors. There is no fallback or hidden model restart.

Full invocation budget is 580 seconds: discovery has at most 120 seconds including preparation, downstream reserves 100 seconds and finalization ten. Extraction retains its 450-second ceiling but also stops at the remaining downstream reserve. Each article retains 125 seconds, including completion/cleanup reserves; startup/request remain at most 60 seconds, cleanup five, lease 300. Scoped synchronous timers never overlap the subprocess supervisor timer; SQL/lock/connection waits are bounded. Less than 125 seconds of extraction time stops before authentication/capture/claiming additional work.

## Software and retained-output verification

**754 distinct tests pass, with zero failures/errors/skips.** Consolidation deduplicates identical class/name cases across targeted reruns. Tests cover RSS safeguards/provenance/corrections, exact whitespace/offsets, native/legacy identity and history, source-checking/tampering, all temporal roles, native-only groups, nullable confidence, SQL filters/pagination, protected read-only APIs, current-run selection, positive fictional text publication, missing-time rejection, zero-claim correction review, source/configuration pauses, budget/deadline failures and existing extraction/evaluation/source/publication/zone/weather/cadence regressions. Software inference uses fictional workers.

The unchanged retained replay separately reconciles **355 saved outputs, 352 prediction records, all 53 reviewed predictions, 788 cached inputs and 407 saved graphs** without neural inference. Its largest native result is 8,203,832 bytes under the unchanged 8,388,608-byte bound. All 17 retained compatibility claims remain review-only because observation time is unresolved. This is preservation evidence, not a new accuracy score.

The unchanged migration chain reaches head in owned disposable PostGIS. Immutable-history triggers remain enabled: per-case databases clone an empty migrated template rather than truncating protected tables. Existing migrations/models/dependencies are unchanged by C3b.

## One controlled real-model attempt

The final frozen acceptance image derives from the authenticated qualified image and packages allowlisted code/assets only. **1,085 source bindings** match the current application/test/qualification files. Expected predictions stay outside worker access. The internal Docker network connects only the worker and disposable PostGIS; assets/code are read-only, inference receives no database credentials and real socket denial remains verified. Eight fictional subprocess failure/isolation probes and a Linux full-pipeline preflight pass before real inference.

The one authorized one-CPU/three-GiB attempt completes all ten retained inputs in one model session. **Eight inputs are admitted through mocked RSS; two pre-existing short fictional capture controls enter processing directly.** Those two are 26/49 characters and correctly fail the unchanged RSS minimum. The six retained articles, reviewed article and three fictional stress cases are all processed without padding, truncation or minimum-size bypass. Mocked feeds establish software integration, not live publisher availability or original RSS membership.

All **4,483 neural spans**, including the **53 reviewed predictions**, match authenticated saved predictions exactly. Independent host verification recomputes proposals, graph, projection, placement/read output and fresh saved-history bindings from original mentions for the actual captures, with **zero additional neural requests**. Duplicate delivery makes zero additional inference calls. Four native cards are readable; three source/evaluation records are saved. Retained publication is explicitly paused: zero publication decisions, alerts or zones are created. Positive publication is tested separately with fictional supported evidence in software and Linux preflight; historical material never becomes a current alert.

| Measured gate | Result | Limit |
|---|---:|---:|
| Full worker-container peak, including normalization/JSONB | 2,492.09 MiB | Below 2,688 MiB |
| Main RSS-to-downstream invocation | 75.772 s | 580 s |
| Worker verification including duplicate invocation | 77.376 s | 580 s |
| Longest complete article operation | 62.723 s | 125 s |
| Cold model readiness | 2.362 s | 60 s |
| Longest inference request | 14.745 s | 60 s |
| Model shutdown/reaping | 0.309 s | 5 s |
| Model starts / requests / reaps | 1 / 10 / 1 | One sequential session |

Docker confirms one CPU, 3,221,225,472-byte memory and equal total swap cap. Measurements cover the actual worker orchestration/model/normalization/persistence container, with PostGIS separate. They establish local full-path compatibility; Cloud Run performance, credentials, asset delivery and isolation remain release verification.

## Failed preparation and preservation

Earlier software preparation failures remain recorded: incomplete HTTP fixture headers, isolated auditor configuration, immutable-table cleanup refusal, stale legacy error expectations, malformed settings fixtures and Windows parameter-name length. They were corrected without changing `.env`, weakening history protections, tuning model/rules or rerunning neural inference. The one isolated source regression rerun used a fresh disposable database and explicit test configuration.

The first Linux package omitted a late-imported native-reader CRUD module. Preflight stopped with its failure receipt, before real inference. A second explicitly frozen package adds that module to the allowlist; application code is unchanged between these two freezes. It passes preflight, eight fault probes and the single neural attempt. No neural retry/resource escalation or post-result application change occurred.

All **3,639 pre-existing receipt files** match their original hashes, including failed one-/two-GiB and passing three-GiB runtime qualifications, schema/C1/C2/C3a and CLI-fix history. Current C3b source differences have separate snapshots/manifests. The final freeze SHA-256 is `edd02adbf42a205c9a7b49823694c7cb416a96e9d6162e56268995e6067b3a7f`.

A private PostgreSQL custom-format dump preserves the acceptance JSONB/history. All five owned containers are stopped with PID zero and the owned internal network is removed. Source texts, predictions, models, credentials, raw logs and dumps stay private in ignored `rss-ner-phase-c3b-20261020-v1` / `rss-ner-phase-c3b-20261021-v2` artifacts. Only aggregates are published here.

## Completion and remaining gates

C3b closes the controlled local Phase C integration gate. A01–A07/A19 admission/correction behavior, A08–A18 evidence/projection/time/method behavior, A20 ownership/failures, A21 backend readers and A22 downstream safety are covered by focused and retained regressions; A23 schema compatibility remains the separately completed schema checkpoint. A21 frontend/browser acceptance is Phase E, not claimed here.

| Contract scenarios | Verification evidence |
|---|---|
| A01–A05 body-only places, exclusions, known corrections and commuter distinction | `test_news_ner_collection.py`, existing discovery regressions and C2 affirmative-body/source-context tests |
| A06 retrieval denial, short/large/incomplete bodies | Native retrieval-protection parametrization, existing fetch regressions and the two actual short-RSS rejections |
| A07 duplicates, conditional refresh and unchanged capture | Discovery/queue regressions, equivalent-clock proof test and zero extra requests in real duplicate delivery |
| A08 Unicode, exact whitespace and repeated occurrences | Native capture whitespace tests, C2 offset/tamper tests and retained/real output recomputation |
| A09–A14 targets, depth qualifiers, administrative scope, time roles and status/access | C2 durable/source tests, 355-output retained replay, native-only group tests and missing-observation-time rejection |
| A15–A18 method readers, tampering, old-recognizer misses and failed/latest native-only outcomes | C1/C2 regressions and native reader, operational tampering, count/current-run and no-observation tests |
| A19 corrections without usable claims | Changed/failed refresh, idempotent zero-claim reconciliation and stale-publication-after-new-failure tests |
| A20 concurrency, failures, leases and history | C1/C3a persistence regressions, CLI/bootstrap checks, Linux timers and eight fictional subprocess probes |
| A21 backend cards/counts/filters/pages/details | Native SQL pagination/search/condition, collection-count, exact-detail and protected read-only API tests; browser behavior remains Phase E |
| A22 source/placement/publication/expiry/moderation gates | Positive fictional native text publication, missing-time rejection, existing lifecycle/storage/source regressions and publication-paused historical real run |
| A23 mode migration and mixed compatibility | Unchanged migration head plus existing schema/storage/queue regressions; separately approved schema report remains authoritative for rollback/lock checks; no production migration applied |

**Next is Phase D monitoring/error classification**, including source-selection health, truthful counters/wording, retrieval versus eligibility and the dated cloud partial-attempt finding. Phase E then connects the existing shared-component admin interface, followed by Phase F's 403 investigation. Existing 60/15/30-minute policy tests pass and cloud settings are untouched. The last-inspected one-GiB cloud job is not qualified by this three-GiB local result. Production mode selection, shared migration application, approved resources/deployment and actual Cloud Run verification remain explicit release gates. Prior unresolved facts, reference holds and language/training limitations remain open without new research/retraining scope.
