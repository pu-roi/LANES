# LANES documentation

> **Last Updated:** October 11, 2026, 1:43 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Community Feed Local Updates:** recent collected flood articles now replace sample news in the desktop sidebar and shared mobile/tablet expandable card. Public article metadata does not depend on alert publication. [Implementation, filtering, 24 backend/10 responsive checks and release limits](evaluations/community-local-updates-20261011.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

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

- [Cross-location flood prediction research](research/cross-location-flood-prediction.md) — literature-backed regionalization, partial pooling, transfer learning and ensembles; current model/dataset audit, recommended depth-aware AFT investigation, uncertainty limits and staged integration/acceptance. Research and a separate local comparison are delivered; primary model selection remains pending.

- [Research documentation follow-up notes](research/chapter1-3-revision-notes.md) — scope alignment, authentic Chapter III result boundary, and items to revisit after system features are implemented and evaluated; working notes only.

- [Flood-duration dataset source register](research/flood-duration-data-sources.md) — report citations, earlier-source acquisition inventory and recent public-study/simulation metadata; distinguishes reviewed/obtained/admitted status and contribution limits.

- [Metro Manila flood-duration literature review](research/metro-manila-flood-duration-rrl.md) — official Pasig consultation durations, recent August 2026 wet/clear chronologies, contemporary MMDA access leads, local studies, shared ML candidates and data-sufficiency limits.

- [Automatic flood expiry and duration research](research/flood-expiry-and-duration-research.md) — Pasig CSV/workbook audit, NOAH/Google/PAGASA/weather datasets, geographic limits, censoring-aware model comparison and documentation requirements.

- [Routing engine research](<research/Routing Engine Research.md>) — research context; use the current [tech stack](tech-stack.md) and [decisions](decisions.md) for adopted architecture.
- [Capstone defense reviewer](capstone/capstone_defense_reviewer.md)
- [Capstone defense Q&A and suggestions](capstone/capstone_defense_qna_suggestions.md)

`others/` also contains local, Git-ignored working notes. Those notes are outside the shared documentation index.
