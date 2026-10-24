# LANES - Full System Documentation

> **Last Updated:** October 25, 2026, 2:47 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 25 source publication boundary

[@roicambe](https://github.com/roicambe) (Roi Cambe). The combined `roi-branch` checkpoint includes the existing reviewed-placement readers/services, field-verification notices, News Automation responsive layout, accessible background map-refresh status and configured fixed-expiry correction. Documentation of previous hosted releases remains dated evidence; this source publication performs no new deployment or database operation. Current Report Flood submissions still lack the explicit observation required by automatic approval. [Full audit](../evaluations/roi-publication-audit-20261025.md).

## System Settings expiry and citizen approval — October 25 local correction

[@roicambe](https://github.com/roicambe) (Roi Cambe). `SystemSettingsPage.tsx` keeps the existing responsive tabs and controls while explaining fixed retention with ML off and the current Report Flood form's lack of explicit observation time. Citizen automatic approval still requires that observation plus its existing eligibility/corroboration rules; its enabled setting does not override them.

`pasig_ml_expiry_service.py` policy v4 assigns configured per-depth retention from original activation to untimed fixed decisions. The cache includes retention durations and migrates older active null decisions; inactive v1–v3 forecasts remain readable. Existing saved/manual timers and automatic-expiry pause remain. Existing zone details `expires_at`, private expiry-policy `deadline`, worker and shared desktop/mobile details components expose/apply the saved deadline without new endpoints, model fields or migrations. [Investigation and verification](../evaluations/settings-expiry-citizen-approval-20261025.md). No production rollout is included.


## Philstar reviewed pin placement — live

[@roicambe](https://github.com/roicambe) (Roi Cambe). The explicit manual `philstar-reviewed-pins-v1` policy in `news_philstar_pin_service.py` binds only article 274/source 573/result 401/groups 5/7 and the developer coordinates. Ground-level named OSM blocks, 15-metre maximum pin snapping, up-to-25-metre arms, exact NOAH scenarios and full rounded EPSG:32651 buffers produce estimated road zones. Source-reported barangays remain separate from mapped community boundaries; a coordinate does not prove the article's exact junction or measured flood extent.

Zones/events **92/93** append to existing JSONB/audit structures without schema or endpoint additions. Readers and the existing protected placement GET return saved reviewed road/core/aura; original extraction is unchanged. Exact preview/baseline/asset/application binding, locks, preservation and receipt reuse prevent duplicates or reactivation. Existing historical presentation routing/statistical exclusions and final-deactivation-to-history remain. API `lanes-api-philstar-pins-20261025-v2` is live; frontend field-badge source remains unpushed. Active total is 17; nine of ten accepted Philstar observations are plotted, with Talipapa skipped. [Execution evidence](../evaluations/philstar-reviewed-pins-20261025.md).

## News Intelligence per-field verification presentation — local

[@roicambe](https://github.com/roicambe) (Roi Cambe). Flooded Areas cards (`NewsResults.tsx`) and Flood Details (`NewsResultDialog.tsx`) reuse `NewsVerificationNotice.tsx`. The existing GET response's `NewsFloodSummary` adds `verification_status`, `verification_issues` (field, label, state, code, reason) and `placement_is_estimate`. FastAPI's pure `news_verification_presentation.py` computes review needs from saved evidence; the frontend only displays wrapping field chips and an accessible explanation disclosure. Water level/depth share one field. Legacy/unassessed responses show unavailable status; absence of a warning is not a Verified certification.

Existing source detail composition recovers the complete native claim before assessment, so a lightweight DTO omitting a road phrase does not hide its verification need. Saved Philstar corrections identify the existing plotted estimate without altering raw extraction or geometry. No route, auth rule, table/column, migration, provider execution or automation behavior changed. This source is local, not deployed. [Validation](../evaluations/news-verification-badges-20261025.md).

## Reviewed Philstar street roles and uncut corner buffers

[@roicambe](https://github.com/roicambe) (Roi Cambe). The explicit `philstar-reviewed-street-corner-v1` correction follows developer-reviewed Don Jose, Palali, Banawe, Tabayoc and Ubay arms from Amoranto. Don Jose/Scout Alcaraz and G. Araneta/Kitanlad retain their own primary roads. Arms stop at 25 m or the next junction/end; checked OSM identity/grade/locality and all three NOAH scenarios support the cores. Full EPSG:32651 rounded `ST_Buffer` auras use the configured staff-road margin without clipping to administrative/model boundaries. These are display estimates, not measured flood width/extent.

Zones/events 83/84/85/88/89 retain identity, source facts and active state; 90/91 add the distinct Don Jose/Amoranto and Ubay observations. Append-only correction receipts retain old/new geometry; latest effective historical metadata projects reviewed street labels and exact source excerpts while original result 401 remains unchanged. The existing authenticated placement endpoint returns saved corrected core/aura for news map handoffs. History reference selection uses the latest import per source/group, without erasing other source references or changing final-deactivation behavior. Existing APIs/models, routing/statistical exclusions, paused automation and disabled expiry remain. Checked serving API: `lanes-api-philstar-streets-20261024-v3`. [Evidence](../evaluations/philstar-street-correction-20261024.md).

## Source-bound junction estimates in existing news/maps/history

[@roicambe](https://github.com/roicambe) (Roi Cambe). `news_junction_estimate_service.py` supports opt-in `source-junction-noah-v1` through the existing manual Philstar output worker. The policy binds article 274/source 573/result 401, the shared OSM node/crossing, checked locality and NOAH assets, preserving source depth/access. All three modeled scenarios cover both adjoining sections equally; no more susceptible side is inferred. A 25 m application display window intersected with NOAH retains dry gaps/holes and source road cores, with full city containment and barangay identity validation. The radius is not source-measured extent.

Palali event/zone **88** and Tabayoc **89** are saved; Ubay overlap with 83 and Don Jose conflict with 84 are retained without mutation. Existing authenticated readers show the same source observations and new active polygons. The same events enter unified history only after final manual deactivation, rehearsed on the restored disposable database. No endpoint/schema or serving API deployment was needed. Existing records, stopped budget, paused automation and disabled expiry are preserved. [Checks and limits](../evaluations/philstar-noah-junctions-20261024.md).

## Active Zones refresh feedback follow-up

[@roicambe](https://github.com/roicambe) (Roi Cambe). `ActiveFloodMapStatus.tsx` uses a screen-reader-only status during background refresh with retained features, removing the visible row and its spacing. Initial loading and authoritative-empty messages remain visible; failures still expose alerts, stale-data context and Retry. Both desktop and compact map layouts use the shared component. No API or stored-data change. Source is local; deployment is pending. [Verification](../evaluations/active-zone-visibility-20261024.md#routine-refresh-label-follow-up).

## News Automation monitoring and source publication

[@roicambe](https://github.com/roicambe) (Roi Cambe). The existing Overview panel keeps the local card/accordion layout, read-only 15-second polling, error/retry states and completion-driven query invalidation. `frontend/src/features/news/NewsAutomationPanel.tsx` shows source-rule versus provider-backed audit mode, actual response model, recovery time, failure phase/elapsed time, quota uncertainty, dynamic weather provider count, server-provided coverage, and expandable bulletin issue/validity evidence. The weather section and pipeline stages retain accessible labels for desktop/mobile inspection. `frontend/src/app/layout.tsx` and app/public icon assets provide browser/PWA icon metadata. These frontend edits are source-only in this publication.

`GET /api/v1/admin/news/results/{run_id}/groups/{group_id}` accepts existing `g…`, `resolved-n…` and bounded `resolved-v44-<24 hex>` identities while keeping staff authentication and malformed-ID rejection. The deployed reader retains GMA 388/Tribune 397 and selects Philstar 401. No endpoint, schema or public API is added. [Audit](../evaluations/roi-publication-audit-20261024.md).

## Philstar source, map and history behavior

Saved Philstar article **274/source 573** completed trained NER **398**, Gemini **399**, and authenticated zero-provider finalization **401**. **10 source-checked observations** appear in News Intelligence; **zones 83–85** plot NS Amoranto/Banawe, Don Jose/Sct Alcaraz, and G Araneta/Kitanlad. All use the supported **September 9, 4:30 PM Philippine-time** heading. Seven accepted observations remain unplotted: four ambiguous section matches and three without a canonical road. The 61 targets retain 10 accepted, 19 unresolved and 32 unsupported outcomes; captions, warnings, subsidence context and secondary crossings are not active observations. The approved **US$1.50 cumulative cap** was sufficient: complete maximum reservation **US$1.3426523**; final conservative cumulative estimate **US$1.0215894** (not invoice charges). Serving API **`lanes-api-philstar-20261024-v2`**, protected API checks, desktop/mobile News Intelligence, selected/public map colors and history checks pass. **447 runtime and 78 mandatory disposable-PostGIS checks pass**, including repeated migration upgrade. All original rows across 41 tables remain intact; GMA 388, Tribune 397 and zones 77–82 are preserved. The stopped 62-attempt ledger, paused automation, disabled expiry and unrelated frontend edits are preserved. The same Philstar events enter unified history after their final polygon is manually deactivated, rehearsed only on a restored disposable database. No live polygon was deactivated. [Evidence](../evaluations/philstar-saved-article-20261024.md).

## Active Zones overview and map recovery

[@roicambe](https://github.com/roicambe) (Roi Cambe). The shared GeoJSON updater now preserves severity colors, feature identities and evidence during selection. Active Zones frames all mapped active floods on overview entry/return, retains last-loaded shapes during viewport refreshes, surfaces persistent retryable failures, and restores layers after style/terrain changes. Compact coordinate handoffs wait for the visible canvas. **72 desktop/mobile functional cases pass**, plus desktop 1,000/10,000-zone scale checks; TypeScript passes and scoped lint adds no diagnostics over the 20 existing errors. Four unrelated frontend edits and concurrent unrelated changes remain untouched. Source publication is included in this `roi-branch` push; frontend deployment remains pending. [Behavior and test record](../evaluations/active-zone-visibility-20261024.md).

## Current Tribune map and time state

[@roicambe](https://github.com/roicambe) (Roi Cambe). Correction **397** records the developer-reviewed shared **September 24, 4:34 PM** time. New zones **81, 82** plot Quirino/Guazon and Gov. Pascual/Sitio 6 alongside preserved Boni 80 and GMA 77–79. Serving API `lanes-api-tribune-time-20261024-v1`, protected checks and hosted desktop/mobile news/maps pass. 401 CI tests and 45 required PostGIS checks pass; original data, stopped ledger, paused automation and four unrelated frontend edits remain intact. Future timestamp-free active reports have a recorded publication-time fallback; explicit individual clocks and supported shared scope retain precedence. [Evidence](../evaluations/tribune-reviewed-time-20261024.md). Source follow-up is published in [PR #143](https://github.com/pu-roi/LANES/pull/143); main integration remains pending.

## Source publication status

Source/CI changes are published on `roi-branch` in [PR #143](https://github.com/pu-roi/LANES/pull/143); reviewed main integration remains pending. The deployed API and database are unchanged by this publication.

## Current news list behavior after Tribune context repair

[@roicambe](https://github.com/roicambe) (Roi Cambe). API `lanes-api-tribune-context-20261024-v6` selects correction 395. The existing Flooded Areas list excludes `subsided` rows in backend SQL before native/legacy counts, publishers and pagination; the existing collection's location counts agree. Authenticated source/run/group inspection retains cleared evidence. Six current listed observations are the three GMA roads plus Boni, Quirino and Gov. Pascual. The latter two retain unknown exact observation times and no polygons; no clock is borrowed from Boni. Four active zones and unified-history event 76 are unchanged. No endpoint, response shape, screen or control is added. [Acceptance](../evaluations/tribune-context-repair-20261024.md).


## Tribune selected-source processing and lifecycle — October 24

[@roicambe](https://github.com/roicambe) (Roi Cambe). The opt-in Tribune worker reuses article 25/source 568 without RSS. Raw NER 390, paid correction 391 and zero-provider finalized correction 392 remain separately inspectable. Existing News Intelligence readers select the approved correction while retaining the original GMA pipelines. No new route, response field or UI control is added. The selected output policy saves only qualified active event/zone/location/timeline and claim/evaluation records; Tribune instances wait outside all history readers until the final linked polygon is deactivated. Ended instances retain source-date/evidence/geometry inspection in unified history, without real statistics or routing eligibility. GMA's existing dataset exclusion remains unchanged. The serving API is `lanes-api-tribune-20261024-v3`; active Tribune event/zone 80 joins unchanged GMA 77–79. Hosted/local desktop/mobile and candidate/serving acceptance pass; source integration remains uncommitted. Final acceptance is recorded in [the evaluation](../evaluations/tribune-pilot-20261024.md).



Current detail-reader follow-up: `lanes-api-history-details-20261024-v1` fixes optional JSON-null media counting without schema/UI/dependency changes. Mandatory disposable PostGIS and protected database-expected inspection checks pass; hosted desktop/mobile event 76 opens correctly. PR #142/main integration is complete; exact-commit build d52b144e-2809-4f3c-b941-5d378c21bc33 passes and the existing main trigger is enabled. That checked main build precedes the manually accepted Tribune release above. [Evidence](../evaluations/event76-inspection-20261024.md).

## Earlier packaged-reader recovery checkpoint — October 24

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). The serving API is `lanes-api-reader-recovery-20261024-v1`; the manually invoked qualified worker remains v30. A missing reader file in the automatic image caused 503s without deleting data. The restored normal image packages the authenticated saved-reader manifest and fails startup on a missing/invalid required reader or wrong database binding. Protected canary checks gate traffic promotion. Automatic backend deployment remains disabled until the repaired configuration is reviewed/merged into `main`. API release readiness does not execute RSS or replace worker specifications. No screen, endpoint path, public response shape or schema was added by this recovery. [Recovery](../evaluations/news-reader-recovery-20261024.md) · [Operator procedure](../guides/news-reader-release.md).

| Existing screen | Current verified behavior |
|---|---|
| News Intelligence → Flooded Areas | Three correction-388 observations: Rizal Ave Extn, Tañong F. Sevilla Blvd. (Bayan), Marcos Highway Underloop; gutter deep, Sep 9 at 2:47 PM, all vehicles passable |
| News Flood Details | Selected observation summary, supported time/depth/access and source evidence; raw NER and immutable inputs remain in Source Article/Processing History; desktop/mobile scrolling verified |
| Collection Status / Source Article | Corrected article 47 with original 140/native 569 and its retained clean-capture processing history; no repeat of the incorrect 137/574 capture chain |
| Spatial Operations / public Active Zones | Active presentation event/zone pairs 77–79; connected-road OSM/NOAH estimates, separately attributed user coordinate hints, unknown measured depth retained |
| Flood History, analytics and exports | Presentation incidents excluded; unrelated ended event 76 retained; five incorrect test archives 71–75 were removed under the scoped cleanup |

The three-article pilot is only partially complete: Tribune 25 and Philstar 274 remain pending. Scheduled news/publication remains paused; both expiry switches are OFF and the old seed job is inert. These deliberately active presentation instances are excluded from ordinary routing and real occurrence/duration statistics. Earlier dated sections below record prior deployments and blockers rather than current serving state.

## Connected-road active projection — current GMA release

Three corrected GMA active presentation event/zone pairs **77–79** are saved and served through API `lanes-api-reader-recovery-20261024-v1`; the qualified manual worker remains **v30**. They are linked directly to article **47**, source **140/native 569**, unchanged correction **388**. Rizal Avenue Extension, Tañong F. Sevilla Boulevard and the ground-level Marcos Highway Underloop qualify under opt-in `connected-road-noah-v1`. Administrative names disambiguate roads without clipping geometry. Source observations remain gutter deep, September 9 at 2:47 PM, passable to all vehicles, with measured inches/metres unknown. These instances have no ended counterpart and are excluded from Flood History, historical analytics/exports and routing; unrelated history event 76 is preserved. No frontend components, visible labels, layouts, routes or public response fields were added. `news_connected_road_service.py` handles authenticated road/NOAH placement; `news_gma_active_outputs.py` performs authorized atomic persistence; `news_presentation_source_facts.py` supplies exact saved depth to existing readers. Existing response revalidation retains unknown source measurements for this dataset. [Evidence](../evaluations/gma-connected-road-20261023.md).


## Earlier v27 GMA data and active-only output checkpoint

API/manual worker **v27** retains the existing frontend and public API shapes. Article 47/current correction 388 still supplies three accurate News Intelligence observations. The user-authorized old 137/574 capture chain and event/zone pairs 71–75 were removed after backup/rehearsal; Collection Status retains the corrected article and its six clean-capture runs. All unrelated data, including manual history event/zone 76, is preserved.

New manual `gma-active-preview` / `gma-active-apply` operations bind the exact source/run/target database/release/assets and stopped ledger, with zero provider calls. Active-only instances, if qualified, use existing internal demonstration metadata with direct source lineage, no ended counterpart, no new UI label and exclusion from history/statistics/ordinary routing. The **actual cloud preview remains unresolved for all three locations**; no apply authority was issued and no active output exists. Historical map and analytics retain only event 76. [Verification and recovery](../evaluations/gma-active-cleanup-20261023.md).

## Earlier GMA News Intelligence checkpoint — three accepted locations

API/manual worker v26 and the private local saved-reader context select **completed correction 388** from original source 140/native 569 and immutable NER 382. Existing Flooded Areas cards/details show Rizal Ave Extn, Tañong F. Sevilla Blvd. (Bayan) and Marcos Highway Underloop with source-supported gutter depth, Sep 9 at 2:47 PM and passability. Inline San Agustin context remains in internal evidence/history; raw responses and original labels are preserved. F. Sevilla's quoted section is retained with unknown canonical barangay. No UI, route, public response shape or schema changes.

No GMA history/event/polygon/active-instance writes occurred. Existing admin-created/deactivated event 76 remains in normal history, with old superseded news archives excluded. Ledger stopped at 42 attempts / US$0.7524937; news automation paused, expiry OFF and old seed disabled. [Actual verification and review stop](../evaluations/gma-three-location-completion-20261023.md).


## Earlier manual news verification checkpoint (October 23 evening)

The versioned v3 plain-list city-heading parser is deployed in manual worker v24. Serving API remains v23 and local readers still select two accepted run-384 observations. Correction 386 failed on an unexpected duplicate-locality observation, so the third request was not sent and no new accepted cards/history/active polygons were released. Existing pages, UI, public API shapes, schema and source bodies are unchanged. The ledger is stopped at 41 attempts / US$0.748841; automation paused, expiry OFF. [Exact implementation, retained response and recovery](../evaluations/gma-city-heading-20261023.md).


## Earlier clean-source GMA database checkpoint (October 23)

The API/manual worker v23 serves two accepted observations from source 140/native 569/correction 384. Source Article and selected Flood Details match the current publisher capture. Five old event/zone pairs remain immutable evidence, with versioned `news_source_superseded` timeline markers excluded by current history/cards/maps/analytics/exports; direct current-history inspection rejects them. There are **zero replacement historical polygons and zero active zones**, because locality/road qualification is unresolved. Reader compatibility and local connection identity are preserved; frontend unchanged. [Verification and exact limitations](../evaluations/gma-source-correction-20261023.md).

## Flood Details/source-version repair — original deployment checkpoint

`NewsResultDialog` renders the selected backend summary, raw depth/shared scope, reported locality, observation time, condition/passability and exact field-specific quotes. It no longer places the entire `NativeExtractionEvidence` report in Flood Details. Source Article displays the current collected publisher body and retrieval time, warning on a different extraction input; `NewsExtractionRecordView` retains raw NER and the exact run-version body. Collection defaults to its current article; explicit history selection remains version-bound. `NewsSourceArticle` strips decorative play bullets only for presentation. Shared `RecordDetailsPanels` preserves desktop/mobile scroll ownership. Existing admin GET details gain additive `source_review` metadata; native details also expose validated `supporting_passages` and `depth_scope`, with the same authentication and no writes/network retrieval. API v20/frontend build 2026-10-23-002 and worker source guard v21 are deployed. The five old GMA observations/events remain preserved and need source reprocessing; see [source investigation](../evaluations/news-source-review-20261023.md).

## Earlier personal credential attempt — personal key not selected

All three cloud Gemini consumers remain pinned to Secret Manager version 2. New version 3 contains the supplied personal credential, verified in memory, but one native-resolution smoke request returned HTTP 400. The worker bindings were restored and no API canary, weather request or promotion followed. Before/after database/configuration fingerprints match; models/images/resources and public interfaces remain unchanged. News remains paused, seed disabled, automatic expiry and Pasig ML expiry OFF. [Attempt and recovery](../evaluations/gemini-key-rotation-20261022/README.md). Earlier cloud-release paragraphs retain their original HTTP 402 checkpoint; the latest failed credential attempt does not establish its cause or successful billing/authentication.

## Earlier cloud correction release — initial provider qualification checkpoint

API revision `lanes-api-gemini-20261022-v4` serves 100% of backend traffic with matching derived/raw saved readers. Unscheduled job `lanes-news-verified` runs one CPU/3 GiB, 600 seconds, one task and zero retries, defaulting to read-only preflight. `news_verified_cloud.py` checks code/assets/Cloud SQL/schema/reader identity and paused settings. The existing Gemini secret binding is preserved. Seven software contracts pass on Cloud Run; the one authorized real request returns HTTP 402, so provider correction remains unqualified. General provider execution is disabled; future resolve-only writes require exact target/input/assets/model authority and at most two parent run IDs. No article seeding, frontend artifact, schema or dependency change. All database fingerprints remain unchanged and existing news pauses/disabled seed persist. [Release evidence and rollback](../evaluations/ner-gemini-cloud-release-20261022/README.md).

## Authorized maintenance reset — October 22 checkpoint

On October 22, 2026, the user explicitly approved clearing all flood records and extracted news output while retaining accounts/community/source articles. Existing screens now return their normal empty states; Collection status retains 174 articles, backed by 224 immutable versions. Community posts retain content/media/timestamps/history; 34 report links were detached before reports were removed. All public API response contracts and frontend source remain unchanged. `flood_data_reset.py` is a maintenance-only transactional service with no HTTP/startup/scheduler integration. Exact target/snapshot checks, fingerprints, explicit deletes, rollback and restoration of four deletion-protection triggers preserve unrelated records and FK enforcement. No new migration/dependency.

Public API ingress/traffic/template are restored unchanged; expiry scheduling is enabled. News scheduler and collection/processing/publication remain paused; historical seed remains disabled. The source NER model is unchanged, but all previous live extraction IDs are gone; new Gemini handoff work must recreate NER output from retained full articles. [Reset acceptance/recovery](../evaluations/flood-data-reset-20261022/README.md).

## NER → Gemini correction and saved-reader selection

The backend supports an explicitly invoked Gemini resolution stage after raw NER. It sends the complete original body, publication metadata, native/unassigned facts and backend-numbered quote choices; strict JSON corrections are checked against their cited source, locality and time role before becoming claims. The existing `GEMINI_API_KEY` is reused. A separate native run on the same article version stores response/parent identity in existing JSON, preserving original NER runs and their graph. Existing evaluation, historical interpretation, saved readers and publication consume independently recomputed derived facts. Missing/ambiguous evidence remains unresolved; normal spatial/lifecycle guards still apply.

`resolve_news_native.py` preflight performs no API request or DB write and emits a hash-pinned resolve-only authority plus `saved-native-read-context-v2`. The latter names the derived pipeline and approved raw fallback versions, keeping unprocessed native articles visible without concealing a failed or pending later verification. Protected endpoints and response shapes are unchanged; saved-result reads never invoke Gemini. The manual command creates no event/report/zone/publication. The disposable native pipeline has explicit verification flags for downstream qualification. No new database schema, dependency or frontend change. Guarded hosted rollout is complete; successful provider compatibility, populated results and the screenshot-specific replay remain pending. [Operator guide](../guides/ner-gemini-verification.md).

## News Flood Details scroll ownership

The local frontend repair in `NewsResultDialog.tsx` passes `scrollable={false}` to `RecordDetailsPanels` for Flood Details, so the flow dialog owns vertical scrolling. Source Article still uses the fixed panel layout with independent article/history scroll areas and the existing mobile pane switch. This removes nested overflow/overscroll trapping without changing visible content, labels or styling. Regression: `frontend/tests/news-details-scroll.spec.ts`, desktop wheel and 320 px mobile touch with fictional API transport. Hosted deployment is pending; this change does not alter saved extraction or observation-time interpretation.

## Current shared Part 2A integration

The existing protected News Intelligence endpoints now select each article's latest selected native attempt, including failed/pending status, alongside legacy-only articles. Server-side result filtering, counts and pagination use a mixed native/legacy SQL query. Older runs remain in article history. Historical processing persists compatible read projections even for unresolved and zero-zone results; reader requests never invoke extraction.

The manually invoked, unscheduled historical job registers full original eligible articles and saves qualified outputs directly as ended events with inactive zones. It does not traverse active publication or create citizen reports. Exact ended citizen matches receive append-only news lineage; original lifecycle/report/geometry fields remain protected. The existing history cards/maps/analytics/exports query database records; no new frontend fields or components were introduced by this execution. [Release and acceptance](../evaluations/news-history-shared-execution-20261022/README.md). Earlier local-only execution limits below are retained snapshots.

## Part 2A — retained news evidence in existing Flood History

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). The existing map/list and View Event dialog stay unified. Overview displays separate News sources with original publisher/title/link/publication, source observation precision, excerpt, road/city, raw/normalized depth, condition/passability, saved extraction and available geometry provenance. The existing News Article dialog opens the exact retained run/version; absent original evidence is an explicit error, never a fallback to latest text. Citizen Reports keep their tab and counts. Errors/Retry retain cached evidence; nested article Escape preserves the parent event dialog.

Authenticated inspection supports `/api/v1/admin/flood-events/{id}/inspection/news_sources?page=1` with the existing bounded page envelope. Projections add origin (`news`, `user`, `mixed`, `unknown`), article/evidence counts, source occurrence/observation precision and closure/duration basis. Retained decision links/import groups are independent of current publication state; inactive history does not reuse Active source projections. Source-based SQL/Python filters, analytics and exports agree; administrative times remain separate. Internal inspection accepts registered general datasets as well as frozen September provenance; there is no dataset selector.

General source inventory/registration/preparation commands are in the [operator guide](../guides/historical-news-preparation.md#part-2a--general-source-inventory-and-archive-preparation). New captures use existing local_update scheduling exclusion; processing/output authorities stay separate. Date-only new archives use a labeled next-day Philippine endpoint without inventing a start hour; assumptions are excluded from observed durations. No table/model/migration/dependency added. [Qualification and remaining shared execution gate](../evaluations/news-history-part2a-20261022/README.md).

## Automatic source-article capture correction

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). `services/news_discovery_service.py` selects GMA's actual standard/AMP reporting body rather than the outer page. It retains explicit publisher time evidence and list boundaries and rejects unavailable reporting bodies. Source Article dialogs continue rendering the selected immutable input with their existing design; GET requests do not fetch or recapture content. A changed successful capture gets a new saved version/run through the existing collector; blocked refreshes retain prior text and expose their retrieval error. Article 47 was separately corrected with explicit user authorization as publisher version 140/completed rules-only run 140; readers select the new body, and processing history retains the earlier morning input. No RSS schedule, frontend contract or database schema changed. [Verification and approved article 47 correction](../evaluations/news-publisher-body-capture-20261022/README.md).

## Phase 1 — connected local historical news workflow

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Existing screens consume saved evidence; GET requests never collect articles, run inference or publish. Native results carry `result_kind`, nullable `claim_index` and stable `group_id`; group inspection uses `/api/v1/admin/news/results/{run_id}/groups/{group_id}`. `NativeExtractionEvidence` displays original neural locations, labeled rule repairs, scoped and unassigned facts, source excerpts and separate extraction/geometry outcomes, including zero-zone sources.

The separate `materialize_news_historical_outputs.py` command authenticates completed runs, source settings, current assets, target and explicit dataset/session/output policy. Preflight is database-enforced read-only; apply is restricted to disposable local targets. Versioned completed historical evaluations and `historical_import` timeline metadata reuse existing tables without manufacturing publication decisions. Frozen matching archives retain lifecycle/geometry/dates; disagreement is review-only. Demos use separate event/zone identities and never reactivate on repeats.

Public active-zone, Spatial Operations queue/map/detail and history responses include validated historical metadata and server-authored `affects_routing`. Per the user’s later correction, no visible demonstration label or extra badge/modal notice is rendered. The established presentation retains source dates; internal metadata preserves observation precision and estimated OSM/NOAH provenance. They form separate queue groups and are excluded from online routing and cached offline exclusions. Existing authenticated deactivation retains designation/evidence/geometry and records actual administrative action time.

Per the later user amendment, Flood History & Analytics uses the original unified history and normal filters across records, analytics, maps/heatmaps, pagination, inspection and exports. The added Historical dataset selector is removed. Old dataset query parameters are discarded while preserving event deep links; backend dataset/session provenance remains internal. SQL and Python use supported source dates for imports, explicit unknown dates and separate administrative timestamps. Demo instances add no real occurrences. Imported administrative/assumed intervals do not enter observed-duration statistics. Original unknown endpoints remain unknown; a labeled two-hour assumption is allowed only for supported exact instants without sourced closure.

Saved native reads use a separately hash-pinned `saved-native-read-context-v1` descriptor (`LANES_NEWS_NATIVE_READ_CONTEXT` and its canonical SHA256); scheduled RSS processing selection is unchanged. See the [operator guide](../guides/historical-news-preparation.md#phase-1--saved-output-materialization-and-reading). Preserve existing visual design on future tasks unless the user explicitly requests a design change.

## E1 — controlled historical origin policy and interpretation

The existing historical operator CLI now accepts paired `--target-policy`/`--target-policy-sha256` arguments. Default behavior stays disposable-only. `services/news_historical_policy.py` authenticates canonical policy content against E0/current application/assets/target/workload. The existing native worker's typed authorization path checks connected target and exact native inputs at transaction boundaries; ordinary callers remain restricted. No HTTP endpoint or frontend control was added.

`services/news_historical_interpretation.py` separately verifies saved results and builds `historical-source-interpretation-v1` receipts. It retains source-bound instant/date/unknown time precision and native-only/unassigned facts, applies historical temporal admission separately from unchanged live source checks and calls existing placement preview through `HistoricalPlacementContext`. Qualification never authorizes publication. Processing/qualification statuses and bounded counts are distinct; full evidence is private in append-only hash-named receipts. Adapter work has its own 60-second bound. [345 passing local checks](../evaluations/news-historical-e1-20261022/README.md). E2 geometry/persistence, E3–E4 visible screens and E5–E6 hosted qualification/execution remain pending. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## E1.2 — frozen-input operator preflight and processing

`scripts.run_news_historical_processing` delegates complete E0 authentication, execution identity and orchestration to `services/news_historical_processing.py`; `crud/news_historical_processing.py` owns bounded readonly inspection and capture/run persistence. The command requires parent/current-asset hashes, explicit database-name confirmation and private receipts. Preflight verifies readonly mode, immutable source/schema/settings and runtime prerequisites without claims/inference/writes. Process retains the existing disposable guard plus loopback/no-query constraints; cloud processing is blocked before connection. No HTTP endpoint or UI control was added.

`crud/news_processing.enqueue_input_snapshot` shares conflict-safe version/run insertion with ordinary enqueue, preserving its pending-article guard for normal capture. Historical mode supplies already authenticated captures without changing current article/review state. Optional `run_ids` in the existing native worker bypasses general capture and uses exact pending-only, non-exhausted claims; the default worker behavior is unchanged. Existing deadlines/owned completion/cancellation/cleanup remain in force. Completed evidence is verified/reused; failed/retry/foreign processing leases stay unchanged. Execution manifests record intentional application-identity deltas separately from the frozen E0 parent. [227-check result and boundaries](../evaluations/news-historical-command-e12-20261022/README.md). No historical source-date adapter, event/zone/publication output, actual cloud execution or real September inference has been delivered by this step. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## E1.1 — expiry maintenance during invalid auditor configuration

`news_publication_service.process_news_expiry` is shared by normal publication and the legacy pipeline's auditor-configuration failure path. It maintains existing due cases without an auditor/policy, preserving configuration/case locks, expiry toggles, scoped/effective deadlines and idempotent decisions. `run_news_pipeline` rethrows the same bounded auditor error with an internal maintenance summary; `news_scheduler_service` records separate maintenance counts/health and a failing pipeline cycle without advancing overall success. SQL/unexpected maintenance failures remain bounded and separate. No new HTTP endpoint, UI control, schema or deployment. Expiry OFF leaves cases/zones untouched. [82-check result](../evaluations/news-maintenance-e11-20261022/README.md). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## E0 — private September input preparation

`scripts.prepare_news_historical_inputs` delegates bounded, repeatable-read/read-only SQL to `crud/news_historical_preparation.py` and exact source/native capture preparation to `services/news_historical_preparation.py`. It authenticates pinned existing article versions and history, checks model/runtime/spatial asset identities without loading the model, and writes an ignored local manifest/inventory/two-capture/receipt package. Its deterministic session and explicit primary/backup/archive dispositions prepare future E1–E2 processing. Repeat execution verifies identical evidence without overwriting it. Missing original publication proof stays unknown; legacy polygons do not qualify neural results. There is no new HTTP endpoint, UI control, inference call or database mutation. [Operator guide](../guides/historical-news-preparation.md) · [27-check delivery](../evaluations/news-historical-e0-20261021/README.md). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Scalable staff spatial and historical browsing

Staff read routes in `api/v1/endpoints/admin_browse.py` require `get_current_active_admin`. `spatial_browse_service.py` owns filters/counts, card projections, viewport geometry, overview cells and paged inspection. Legacy history/detail and public active-zone endpoints retain their contracts.

| Read | Contract |
|---|---|
| `/admin/zones/count` | Eligible active-zone count without grouping. |
| `/admin/zones/map` | Global summary (`summary_only=true`) or validated `bbox` viewport with ascending-ID `cursor`, at most 250 zones and `next_cursor`. Operational polygon and original road core remain separate. |
| `/admin/flood-events/records` | Full SQL-filtered history, exact totals, 20 summaries per page, `verified_at DESC, id DESC`, optional `focus_event_id` page resolution. No geometry/evidence collections. |
| `/admin/flood-events/map` | Shared history filters; global counts/bounds separately from viewport counts. Below 14: at most 4,096 severity-weighted overview cells. At 14–15: cells plus cursor-paged exact polygons. At/above 15: polygons. Optional `event_id` summary resolves focus independently of viewport. |
| `/admin/flood-events/{id}/inspection` | Bounded incident overview with complete counts; evidence collections are loaded independently. |
| `/admin/flood-events/{id}/inspection/{collection}` | `reports`, `zones`, `timeline` or `locations`, 20 per page with complete totals. |
| `/admin/zones/{id}/contributors` | 20 original reports per page; optional `focus_report_id` resolves its page. |

Existing queue/member routes and `/admin/zones/{id}` accept opt-in `summary=true` for bounded contributor previews and complete aggregate counts/severity. Omission retains legacy detailed behavior. Metadata SQL selects only required claim/public fields; inspection retains complete saved evidence. Request-local bounded geometry/normalization reuse never caches eligibility across reads.

`useStaffMapData` coordinates summary/viewport queries, aborts obsolete reads and follows all continuation cursors. Cards load independently. `zoneQueueApi` owns equivalent detail/contributor query definitions and shared spatial invalidation; mutations and live-sync updates invalidate active/history/Analytics reads. Active queries are fresh for 15 seconds; history for 30 seconds. Queue polling pauses during inspection. Text filters debounce 300 ms; select/date filters apply immediately. Mobile history initializes its map on first use and retains it across view switches. `BaseMap.preloadRouting` defaults true; history sets false.

`syncGeoJSONSource` uses stable feature IDs and MapLibre incremental updates for appended chunks, avoiding repeated transfer of the entire loaded collection to the worker. Full source replacement preserves intentional selection draw order, viewport replacement and style recovery. Existing shared fill/core/heatmap paint tokens remain unchanged. Shared `Pagination` controls list and evidence pages at desktop and 320 px widths.

Overview cells sum weights and represented-zone counts and contain no individual event identities. They approximate concentration, not inundation boundaries or distinct-event frequency. Dense viewport and cold/concurrent performance limits, benchmark conditions and visual acceptance are recorded in the [scale report](../evaluations/spatial-history-scale-20261021/README.md). No schema/index/dependency changes. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Flood Event history browsing projection

The existing staff-only `GET /admin/flood-events/history` accepts optional `summary=true`. `flood_history_records` in `flood_event_service.py` batches locations, zones, linked report severity/depth and aggregate evidence/reporter/eligible-zone counts. Summary zones include saved geometry, severity/depth, lifecycle timestamps and stored activity, without loading contributor, media or reporter details. Omit `summary` to retain the legacy detailed zone contract; `/admin/flood-events/{id}/history-detail` remains the evidence inspection read. SQL read failures return a retryable 503 without exposing database details.

Legacy consumers retain the bounded `/history` summary mode. The staff `FloodEventRecords` interface now uses the complete `/records` and independent `/map` reads described above. Local startup still uses frontend 3000, backend 8000 and `/api/v1`; an absent backend listener produces a proxy error and cannot be repaired by changing map styling. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Spatial Operations — viewport layout and zone terminology

`LiveMapPage` uses `isCompactLayout` from `(max-width: 767px)` for sidebar width, map/list switching, drawer layout and fly-to visibility. It independently retains `isTouchDevice` for active-zone, pending-report and news-placement tap/popup behavior. Touch emulation or touch-capable hardware at desktop widths therefore keeps the 420 px sidebar (460 px from xl) beside the map. Below 768 px, the existing full-width mobile list/map switch remains. Between 768 and 1023 px, opening a merge/create/edit workspace hides the primary sidebar so the workspace fits beside the map; the primary sidebar returns when the workspace closes.

Active Zones uses zone terminology throughout loading, history, search accessibility, refresh/retry, group back navigation and error messages. Needs Review still uses queue terminology. The internal `/admin/zones/queue` read API and cache identifiers remain compatible; no data grouping or eligibility logic changes. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Local environment ownership — October 21, 2026

Normal frontend startup uses dotenvx with encrypted `frontend/.env.local`; `.env.keys` remains the private decryption file. The browser API base stays `/api/v1`, while Next's existing proxy defaults to backend `http://127.0.0.1:8000`. The redundant ignored `.env.development.local` override is removed. Backend normal startup still uses its encrypted `.env` and private key. Backend `.env.test.local` and `.env.mcp.local` are referenced optional replay/MCP profiles, while `.example` files are setup templates.

VS Code's default build is **Start LANES Dev Server** (frontend 3000/backend 8000). Local Plotting remains an explicit task; its ignored launcher sets `BACKEND_URL` to 8003 solely for the child frontend and restores the previous process value. It does not create frontend environment files. Existing running mismatched frontends are rejected by its saved-zone check; cleanup does not start replay or change stored flood data. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Flood Event Records map — October 21, 2026

The page's Analytics/Flood Events navigation uses shared `Tabs` with `variant="underline"` and standard content-width buttons, padding and typography, matching Moderation Center, Users and Settings. It supplies no `fullWidth` or `tabClassName` overrides; narrow screens use the shared horizontal scrolling behavior. The existing tab state, icons and feature panels are retained.

The Flood Events workspace under `/admin/flood-history` uses equal desktop grid tracks (half the space after the gutter each), retaining the default mobile List and explicit Map switch. `HistoricalEventsMap` loads saved Polygon/MultiPolygon footprints immediately and fits all displayed valid footprints initially and after filters; selecting an event or an explicit zone/report handoff focuses that evidence. Geometry/filter identity prevents background reads or unrelated rerenders from resetting manual camera movement. Resize observation handles a map becoming visible on mobile.

`FloodEventRecords` uses shared `Pagination` below the card list, with at most 20 cards per page, counts, disabled controls during fetch and visible retry. Filters reset the page and list scroll; map selection requests the page containing that event, while closing details retains the current page. The independently cached map query retains the full filtered history window, so card pagination neither drops map features nor reframes the camera.

The staff-only `GET /admin/flood-events/history` retains its array response when `page` is omitted. Opting into `page>=1` returns `FloodEventHistoryPage` (`items`, `total`, `page`, `pages`, `page_size`); `page_size` defaults to 20 and is restricted to 1–20. Both reads use the existing `limit` of at most 250 and deterministic verified-time/ID descending order. Optional `focus_event_id` resolves the containing page within that filtered window; optional `multiple_places=true` applies the existing non-city-place recurrence criterion in SQL before pagination and limiting. Analytics/exports retain their existing behavior. No new endpoint or database schema is introduced.

- Historical footprints reuse `PENDING_REPORT_POLYGON_AURA_PAINT` with Needs Review: canonical severity colors, borderless translucent fill at zoom 14+, stronger selected fill, no solid road core or overview pins. Saved-zone map handoffs only frame the camera, preserving existing selection and polygon styling. Supporting-report detail focus retains a separate blue overlay.
- `useFloodHeatmapLayer` supplies public `MapCanvas`, Spatial Operations and history with the same density colors, weight expression, intensity/radius and zoom 13–15 opacity fade. History uses namespaced sources; heatmap-only below 14, overlapping footprint/fade from 14 to 15 and footprints alone at 15+. Layer/source cleanup and style reload restoration are shared; failures surface to users.
- The staff-only history GET adds typed `heatmap_features` per event: one GeoJSON Point on each valid saved zone polygon, properties `event_id`, `zone_id`, `weight`. Points are calculated in a backend service from already-loaded zones; peak event severity supplies weights 1/2/3/5 for low/medium/high/extreme, shared with public Analytics. No extra per-zone reads or external calls. History zone serialization tolerates missing/invalid persisted footprints and multipart geometry; unmapped records remain inspectable.
- Heatmap and polygons follow the full filtered records independently of the displayed card page, including existing location recurrence filtering and the 250-record limit. The legend calls this severity-weighted historical zone concentration, not distinct-event frequency. It never reads the public report heatmap feed or changes routing, stored geometry, event lifecycle, filters, exports or authorization.

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). [Verification and limits](../evaluations/flood-history-map-20261021/README.md).

## Shared Spatial Operations queues — October 21, 2026

`/admin/map` shares `SpatialGroupCard` and `SpatialQueueFilters` between Needs Review and Active Zones. Active Only shows backend-grouped zone cards; clicking or pressing Enter on one immediately fits the map to the full group and loads individual zone records. Mobile opens the map with **Back to zones** returning to those records. Back to zones restores filters, page, scroll and opening focus. Search, source, city/barangay and severity filters match one zone's evidence and retain its entire group. Source/category counts refer to individual zones, while card counts/pagination refer to groups. All History retains individual detailed entries with the same filters.

- Staff GET `/api/v1/admin/zones/queue`: `active_only`, `source=all|user_reports|news|official|other`, `q`, `city`, `barangay`, `severity`, `page`, `page_size` (default 20, maximum 100). Returns card summaries, full history entries when requested, source counts, location facets, member/card totals and pagination. Each summary includes nullable WGS84 `bounds=[west,south,east,north]`, calculated from all group members before pagination for display-only camera focus. Missing bounds show a visible map error while inspection remains available; no saved geometry is changed.
- Staff GET `/api/v1/admin/zones/groups/{zone_id}/members`: resolves membership from any active zone ID. With no `page`, opens the page containing that member; explicit pages support normal browsing. Returns the existing zone-detail contract, current group anchor/reason and pagination.
- Active membership requires complete, unambiguous matching normalized road/city evidence and original geometry within 50 m for every pair. `queue_metadata` batch-loads source and report geometry projected to UTM 51N. Valid saved `source_geometry` takes precedence; otherwise valid linked report geometries are combined. Missing/conflicting location metadata or unavailable original geometry produces individual cards; expanded avoidance polygons never supply grouping proximity. Full saved polygon bounds still supply map focus. Sources may mix when evidence qualifies; no creation-time cutoff applies. Lowest member ID anchors the group; newest creation time orders cards. Active eligibility reuses `avoidance_zones_query`, including paused expiry policy and simulation clocks.
- Shared `spatial_grouping` supplies geometry conversion and complete-link grouping; Needs Review keeps its existing two-hour rule, required road/city metadata and separate news cards. All grouping remains read-only and occurs before filtering/pagination; no merged geometry, lifecycle or routing state is written.
- `ActiveZoneRecords` preserves Info, evidence/source/estimate provenance, contributors, updates, View on map, Edit and Deactivate. Checkboxes and Select all on this page apply to displayed eligible records only. Explicit bulk actions are also available in the panel on mobile; opening a group selects nothing. History response activity reflects backend eligibility so expired zones cannot be selected for deactivation.
- Queue/member reads poll every 15 seconds while active; zone mutations invalidate the shared `adminZones` query prefix. Storage errors, retries and vanished membership are visible. Existing zone APIs remain available; no SQLAlchemy model, migration or package addition.

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Locally verified; git publication is limited to `roi-branch`, with no deployment. [Acceptance and limits](../evaluations/spatial-zone-queues-20261021/README.md).

## Chris frontend integration — October 21, 2026

- Registration, Contact and Footer open Privacy Policy / Terms of Service through `features/legal/LegalNoticeTrigger.tsx` and the shared `RecordDetailsDialog`. Legal content scrolls inside the dialog; Escape closes it, and focus returns to the opening control, including touch activation.
- `/admin/map`: Active Zones **View on map** selects the zone, opens the mobile map when necessary, resizes it and focuses its geometry. Missing or invalid geometry produces a visible error.
- `/admin/flood-history`: the workspace buttons are **Analytics** and **Flood Events**. The event detail dialog mounts into `document.body` above the page stacking context. Shared Tabs renders buttons on this page; test selectors follow its actual accessible roles.
- `/map`: Saved Places starts with pins hidden. Its visibility control shows all saved pins; selecting a place shows that pin and focuses the map. Closing the saved-place panel or opening another exclusive panel clears the selection; logout clears the saved-place state and pins. On mobile, selecting a route instruction retains its segment highlight while collapsing the panel, and selecting the flood end returns to the report panel.
- `/feed` retains Roi's continuous pagination, filters and navigation refresh while the mobile drawer has independent scrolling and bottom navigation clearance. `/profile` removes duplicate bottom padding while retaining the layout's navigation clearance.

The existing API, database and NER contracts are unchanged. Backend/expiry VS Code tasks now load `.env.local` before `.env`; only synthetic environment loading was tested, with no worker launch. [Integration verification](../evaluations/chris-integration-20261021/README.md). Integration owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Phase D — saved health and bounded worker history

Existing active-admin GET `/api/v1/admin/news/sources` now reads saved DB health and settings through a thin route/service/CRUD boundary. It retains `enabled` and adds `registry_eligible`, `selected_for_collection`, `collection_active`, per-feed `feed_health` and publisher `body_counts`. Feed health uses `not_recorded`/`ok`/`error`, timestamps and bounded codes, without probing sources.

Collection GET adds optional `retrieval=available|missing|error` and independent overview `retrieval_counts`. Use `status=all` to locate excluded retrieval problems; status/search/publisher/retrieval filters intersect. Native intended-method selection and saved evidence remain intact. Feed-history responses add `articles_saved_or_seen` while preserving `candidates_saved`. Monitoring adds `collection_to_alert_delay_reason=not_computed`.

Automation/configuration runtime retains `last_cycle` and adds `recent_cycles` (last ten). Summaries include bounded stage outcomes/errors and nullable Cloud Run execution/task/attempt identity. No table/migration is introduced. Status remains readable when auditor configuration is invalid, with explicit audit failure; storage errors stay 503. Scheduled-worker output preserves collection/retry details and normal exits/cadence.

These are backend contracts only: existing frontend labels/badges, inspector/cards and polling remain Phase E. [Verification and cloud finding disposition](../evaluations/rss-ner-monitoring-20261021/README.md). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**Earlier checkpoints below are historical.**

## C3b — controlled native pipeline and saved-result APIs

`news_ner_durable.pipeline.run_native_news_pipeline` and the separate Linux `scripts.run_news_ner_pipeline` connect RSS admission/corrections, exact native captures/publication evidence, supervised extraction, saved read projections, placement, native source evaluation and existing publication/reconciliation. They require test configuration and an actual `lanes_p3_verify_*` database; scheduled production defaults remain legacy. Budgets are 580-second invocation, at most 120-second discovery, 100-second downstream/ten-second final reserves, and the existing 450/125/300 extraction/article/lease ceilings.

Existing admin result/article/collection readers accept an internally supplied intended-method context. That dependency defaults to legacy; there is no public processing switch. `NewsResultPage` items distinguish legacy claims and native groups. Native projection counts/filters/pagination are SQL-backed, preserve null confidence and show a joint/collective observation once. A newer failed/pending intended run hides older main-list results. Missing historical operational evidence remains unsupported rather than silently repaired.

The additive active-admin GET `/api/v1/admin/news/results/{run_id}/groups/{group_id}` binds exact saved group evidence. Group/claim details expose actual linked lifecycle records without inferring publication from extraction. Existing claim/placement routes and role checks remain. GETs perform no collection, inference or writes. No frontend UI/types change is included; frontend consumption is Phase E.

Zero-claim/new-failure correction reconciliation appends review to linked cases without clearing/refreshing old flooding from absence. Source checks use `source-ner-v1` and trusted native evidence; existing geometry/freshness/expiry/conflict gates remain. [754-check and controlled real-runtime report](../evaluations/rss-ner-rss-integration-20261021/README.md). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**Earlier checkpoints below are historical.**

## C3a — internal native worker, no new route

`news_ner_durable.processing.process_native_saved_news` authenticates assets, captures native input, claims explicit native/pipeline leases, lazily starts one sequential Linux subprocess, normalizes through C2 and commits owned results. Scoped CPU/SQL budgets include normalization and persistence. `scripts.run_news_ner_processing` is a thin test/disposable-only entrypoint; it never evaluates, places or publishes, and returns bounded errors/interrupt exit 130. Existing scheduled/legacy workers and HTTP authorization/routes are unchanged. Saved history uses C1 serialization; no card/native-reader activation. [251 checks and one actual local run](../evaluations/rss-ner-native-worker-20261020/README.md).

**Earlier checkpoints below are historical.**

## Phase C2 — projection/source library, no route activation

`news_ner_durable.adapter.build_native_result` binds native input, saved original predictions and independently authenticated assets, preserving complete graph/provenance. `verify_saved_result` recomputes exact extraction content while permitting separately gated placement enrichment. `source_check.check_native_source(s)` provides distinct `source-ner-v1` audits without the old recognizer. Errors are bounded; valid native-only results have reasons. [Contract, behavior and verification](../evaluations/rss-ner-native-projection-20261020/README.md). Existing routes, authorization, scheduled evaluator and default legacy writers are unchanged; intended-method/current-native readers and runtime/RSS wiring remain C3.

**Earlier checkpoints below are historical.**

## Phase C1 saved-run compatibility — existing admin routes

`news_candidate.NewsExtractionRunSummary` dispatches persisted `rules_only` versus `ner_rules_v1` through `schemas/news_ner_result.py`. Existing article-detail and candidate-processing GETs preserve the native graph, grouped evidence, proposals/abstentions, source/provenance/projection metadata and null confidence without inference or writes. Unsupported/mismatched saved versions return bounded HTTP 409 through `services/news_saved_run_service.py`. Existing authentication/role dependencies remain unchanged.

No frontend change or new route is delivered. Existing scalar result list/detail/placement consumers exclude or explicitly reject native data until projection/cards qualify. Backend native history remains inspectable; completed native runs stay Needs checking in collection attention. Native group routes, frontend method types/inspector and intended-method selection remain pending. Default writers remain legacy. [93-check verification](../evaluations/rss-ner-method-boundary-20261020/README.md).

**Earlier checkpoints below are historical.**

## Local extraction-only NER preview

The current pipeline is v19 neural locations → v40 proposals → v44 combined repairs → unchanged `lanes-context-association-v42` grouping. The shared `news_ner/location_pipeline.py` adapter serves worker and host validation; original predictions and ordered rule changes remain separate, and host recomputation rejects chain/graph mismatches. V1 endpoint/response fields and source URL are retained. Provenance identifies both location stages and the combined method. [V46 outcome](../evaluations/flood-ner-backend-location-v46-20261020/README.md): 1,281 tests, full cached parity and one real-worker API request pass, with independent preservation/isolation/cleanup verification. Flag remains off; admin-panel display is next.

The response's `source.canonical_url` is the saved article link, copied from the same immutable snapshot as its request hash. A [real saved-article review](../evaluations/flood-ner-saved-article-review-20261019/README.md) confirms the database/API handoff and exposes full-article extraction gaps; connection success is separate from semantic correctness.

`POST /api/v1/admin/news/articles/{article_id}/ner-preview` is an active-admin, default-disabled local backend endpoint. It reads an already saved body and returns exact-source grouped location/depth/time/status/access evidence, original neural mentions, separate rule proposals, unresolved fields and model/runtime provenance. The router is `backend/app/api/v1/endpoints/admin_news_ner.py`; orchestration is in `backend/app/services/news_ner_preview_service.py`, with an inference-only `news_ner/` package and dedicated `news_ner_preview.py` schemas. [Guide](../guides/ner-backend-preview.md) · [Verification](../evaluations/flood-ner-backend-preview-20261019/README.md).

This adds no frontend screen, database table/run/history, placement, map or automatic-processing change. It runs on the local API host through the qualified isolated Linux Docker worker and rejects production environments. The four preview settings default to off/unconfigured. Observation/report/publication time does not establish onset; subsided evidence is retained without implementing plotting/history policy. Existing rules-only extraction remains separate. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier checkpoints below are historical.**

**Current Gate 3 status:** Improvement preparation is complete; additional-dataset readiness/admission remains open. Development has 244 drafts (179 candidates / 65 holds); isolated test curation has 56 prospective entries, zero admitted independent test records and no seal. Resolve coverage, reference/language, source-use, historical-overlap and the single development tokenizer-alignment failure before corpus admission/export or further training. Original 400-sample results and model roles remain frozen. [Readiness report](../evaluations/flood-ner-additional-dataset-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Historical qualification-review checkpoint:

**Gate 3 qualification review complete; operational qualification remains open:** Codex reads all **60 held-out passages / 22 articles**, records **120 original/A seed 0 assessments** and accounts for all **391 FP/FN events**. Fourteen passages retain AI reference/convention questions; no label, offset, score or model choice changes. Original seed 0 remains primary (**63.12 test F1**) and A seed 0 exploratory (**67.72**). All 42 event-count slices and preservation checks pass. Next prepare the remaining Gate 3 qualification specification (reference-scope addendum, constructed regression matrix and bounded CPU/Linux/failure/performance plan) before Gate 4 integration. No inference, training or test rerun occurs in this review. [Review](../evaluations/flood-ner-model-qualification-20261016/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Offline tool locations:** backend/training/flood_ner/cli.py exposes export-qualified-corpus, prepare-experiment, compare-validation, freeze-test-experiment and evaluate-test. Preparation/registry/manual-training/study helpers produce independent research runs; heldout_test.py and heldout_test_worker.py freeze and evaluate the fixed original/A roster once. The test freeze uses selected-checkpoint/model, original seed 2's separate recovery, exact tokenizer/model/input/code bindings and an exclusive attempt marker before inference. Validation-only guards remain unchanged. No endpoint, screen, public schema or operational DB write is added. Private logs, requests, predictions and offset errors stay ignored; public reports contain metadata. [Tooling instructions](../../backend/training/flood_ner/README.md).

**Historical GPU preflight review fix:** Timeout handling now preserves partial stdout/stderr for either worker and includes the logs in the failed report hashes. Four regression scenarios reproduced the defect before repair; all 126 focused tests now pass. Previous GPU qualification evidence is preserved; no dependencies, model weights, news admission or schema changed. [Fix verification](../evaluations/flood-ner-gpu-timeout-fix-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical RTX desktop GPU-preparation checkpoint:** Actual RTX 3060 Ti 8 GB / driver 610.47 verified. Isolated Python 3.11.17, spaCy 3.7.5, CuPy 13.6.0 and Torch 2.11.0+cu128 pass native inference, six-class constructed updates at batch sizes 1/4/8 and saved-model CPU replay. 122 focused tests pass; 73 installed packages are compatible. All 23 original model files verify unchanged. No news-model processing, admission, production or schema change. [Results](../evaluations/flood-ner-desktop-gpu-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Offline module `training.flood_ner.gpu_preflight` verifies the pinned artifact and fixed constructed probes, then runs separate isolated GPU/CPU workers. `gpu_worker.py` configures task-local CUDA DLLs, records training/memory, saves a temporary six-class model and checks CPU replay. This adds no endpoint, screen, database access or deployment integration.

**Earlier inventory-only desktop preparation:** Standalone `desktop_inventory.py --output <new ignored directory>` collects local OS/RAM/driver/GPU metadata without SQL, FastAPI, source admission, model loading or news inference. That earlier inventory identified the MX330 laptop; subsequent RTX 3060 Ti desktop qualification is recorded above. Deployed NER integration remains pending. Publisher correspondence is an optional source-use clarification route, not a new endpoint or universal prerequisite. [Guide](../guides/ner-desktop-preflight.md).

**Academic-use proposal validation:** Offline academic_proposal.py validates a new proposal format without modifying the earlier academic-review format. It adds no CLI, API, screen or operational write. Actual project decisions and source admission remain separate; all 400/40 original records are unchanged. [Report](../evaluations/flood-ner-academic-proposals-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical October 15 publication checkpoint:** The corrected 400-sample/139-article AI silver cohort and 40 contextual v3 pairs remain frozen. Constructed tokenizer qualification, versioned correction/packaging tools and three academic-use AI reviews are complete. Adviser guidance is researcher-reported: private research/training only; the ethics framework is unspecified. Drive backup is verified and owner-only across 22 checked items. Three academic-use decisions remain unresolved; retention is undecided and is not itself a training prohibition. The next task is the supported academic-use basis and article-exception decisions, followed by separate admission, news-cohort tokenizer qualification and desktop GPU preparation. Fresh focused verification passes 664 tests (94.60 seconds); no new dependency, database migration, training or production change. [Publication checks](../evaluations/flood-ner-publication-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Academic-use review:** The evidence-only academic_use.py helper checks hash/Unicode clause pointers, publisher/source coverage and unresolved decision boundaries. It adds no CLI command, endpoint, application screen or operational write. Three reviews are complete; source admission remains unresolved. [Report](../evaluations/flood-ner-academic-use-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Annotation-correction checkpoint:** Corrected three location records and one contextual pair in a new revision: 400 AI silver samples from 139 articles, 1,497 location spans and 40 contextual v3 pairs. Passage/source text, identities, reporting groups, 280/60/60 partitions and ten retained pilots are unchanged; every hard quota passes. The corrected organized package has 606 verified files plus its manifest and a byte-identical replay. 638 focused NER/location tests pass; the historical 666-test result is a different selection. All fifteen source-use outcomes remain unresolved; training admission, DocBin export and distribution readiness remain zero. Earlier cohorts, contextual v2, packages, model/tokenizer artifacts and checkpoints are preserved. [Results](../evaluations/flood-ner-annotation-correction-20261015/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Offline qualification diagnostics:** backend/training/flood_ner/qualification.py and qualify-cohort inspect frozen annotations/captures, model/policy evidence hashes, slice support and source-use holds. They write only ignored research diagnostics; no model loading, admission, endpoint, application screen or operational record is added. [Report](../evaluations/flood-ner-qualification-20261014/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Offline 400-sample preparation:** [Corpus report](../evaluations/flood-ner-corpus-400-20261014/README.md) records the backend training CLI build-cohort and configurable verify-news target, with 400 silver records, grouped research partitions and explicit export holds. Full text remains in ignored artifacts; metadata/method notes are documentation only. No endpoint, application screen, operational record or runtime NER is added. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**AI annotation pilot:** Twelve research-only passages have source-exact location labels and separate rich reference drafts, with actual AI teacher/review provenance. [Evidence](../evaluations/flood-ner-ai-pilot-20261014/README.md). Explicit export --profile location-only-v1 limits the training vocabulary to six place labels while retaining existing source/group/split gates. This is offline serialization/annotation work; no operational parser, endpoint, UI, database schema or trained model is introduced. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Editorial/manual-annotation preparation:** Offline review-passages validates source-bound editorial decisions and emits ignored contiguous context blocks plus metadata. [Paper-aligned review](../evaluations/flood-ner-editorial-20261014/README.md) records 100 AI-assisted full-body reviews, a twelve-source manual pilot shortlist and the 400-total/280–60–60 study target. All source admission, annotation and split counts remain zero. This command adds no API, screen, operational ingestion, database schema or trained inference behavior. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Candidate review corrections:** Offline preparation now binds candidate/article identities, preserves source-review notes and retains required/per-passage review holds. [Conditional readiness audit](../evaluations/flood-ner-readiness-review-20261014/README.md). No endpoint, UI, SQL schema, operational record, NER inference or deployment change; preparation remains pending semantic review. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Draft passage preparation:** Offline prepare-pilot now proposes research-only context windows and metadata/group review queues after checking the source register. [Initial readiness packet](../evaluations/flood-ner-readiness-20261014/README.md). No annotation labels, public endpoints/screens or operational database records are created. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Completed-work review:** [Offline NER audit](../evaluations/flood-ner-review-20261014/README.md) strengthens preparation source checks, malformed-input reporting, immutable reference capture and export split/group guards. Existing register evidence remains valid; 362 checks pass. No route, endpoint, UI, database or operational parser changed in this review. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Historical-source preparation:** Offline collect-news/import-browser-news/verify-news/capture-wikipedia commands now provide the [100-article research register](../evaluations/flood-news-corpus-100-20261014/README.md). Captures and supporting Wikipedia revisions create no operational flood records or zones. This expansion adds no API, screen, schema or production NER behavior. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Local NER preparation and extraction update:** backend/training/flood_ner/ is offline tooling with no public endpoint or operational database dependency. It supplies capture/inventory, annotation validation, read-only location inspection and DocBin export; production NER inference remains pending. The developer-authorized temporal follow-up changes taglish_extraction_service.py to stop inherited clocks at independent paragraphs, retaining adjacent city-led continuations and existing guards. news_processing.py versions new work as rules-spatial-preview-v21; old histories remain intact. [Local verification, source coverage and limitations](../evaluations/flood-ner-milestone1-20261014/README.md). No route/UI/schema change or deployment. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest verified production release:** Main 5c6da28 / PR #136 passed 285 Linux release checks, existing migrations and the release worker. Matching API/news/expiry and frontend rollouts are live. The natural 11:30 PM Scheduler delivery completed collection with zero LLM requests; shared 15/30/60-minute due slots fix the skipped risk tick. Automatic expiry remains disabled at the operator's request for the historical video demonstration. [Deployment evidence](../evaluations/news-autonomy-fixes-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Pending roi-branch Community Feed changes:** The existing FeedPage working copy adds a mobile local-updates modal, appended feed pagination and swipe navigation, while retaining desktop pagination/sidebar presentation. These edits are included in the requested branch save; they are separate from PR #136 and are not established as deployed by the news release evidence. Mobile load-more currently logs request failures without a user-facing message; retain this as an open UI issue. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current news runtime:** source_rules integrates into existing audit/evaluation/publication interfaces; measurement-first policy uses original immutable facts. Public excerpts retain saved evidence under the existing 700-character bound without decorative play bullets or composed summaries. Normal production ignores local historical scenario clocks. Deployment runs source-mode regression tests and a real news job before exact API revision promotion. [Evidence](../evaluations/news-source-validation-20261013/README.md).

**Earlier PR #134 rollout checkpoint:** PR #134 merged the focused source-mode implementation into main at 420b38f, excluding MCP/framework upgrades. Complete September 24/9 scheduled-worker/public-API timelines pass with zero inference, initial 19-inch and later 10-inch Santo Domingo publication, duplicate safety and final expiry. Fresh coordinated Cloud Build and frontend rollout are currently running. [Evidence](../evaluations/news-source-validation-20261013/README.md).

**Source-mode v2 follow-up:** Public report details use saved extraction evidence under the existing 700-character bound, with decorative publisher play markers removed and no composed ellipsis summary. Existing See more works on mobile/desktop. Numeric depth precedence is enforced by the shared extractor; source validation no longer rejects paired verbal differences. The replay enters through the actual scheduled worker with only publisher responses/clock substituted. Production API/news/expiry v2 need no ChatGPT agent or LLM. [Evidence](../evaluations/news-source-validation-20261013/README.md#measurement-precedence-and-scheduled-worker-follow-up).

**News source validation release:** New backend news_source_validation_service.py is selected through the existing auditor/evaluation interfaces with provider source_rules. It makes no HTTP model/quota requests and produces exact-source compatibility DTOs. NewsAuditDiagnostics adds validation_mode; the existing NewsAutomationPanel locally shows NLP + source checks without quota UI. Existing public map/alert endpoints retain their contracts and label estimated geometry. List excerpts show the applicable row/depth/parent while saved extraction stays immutable. Private historical replay script/launcher selects a guarded loopback database and database-bound scenario file; production ignores it. API/news/expiry share the focused image, and production JWT uses a private Secret Manager binding. [Acceptance](../evaluations/news-source-validation-20261013/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Production controller enabled (October 13):** POST /api/v1/internal/news-scheduler/tick now receives the existing Scheduler every 15 minutes with exact Google OIDC machine identity/audience. Cloud API configuration revision lanes-api-00081-n4x has the three scheduler audience/account/job variables and narrow dispatch/reconciliation IAM. Controller selects 60/15/30-minute collection. One HTTP 200 delivery and successful worker completion verified; provider qualification remains separate. [Evidence](../evaluations/news-adaptive-scheduler-release-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**ChatGPT qualification implementation:** app/services/chatgpt_plan_qualification.py uses the fixed public /v1/responses transport and existing strict source validation, without DB access. scripts/qualify_chatgpt_news.py reads frozen captured fixtures and writes only a bounded private experiment ledger/stream artifacts. Real authorization/model discovery pass; an actual eight-claim response yields review/invalid, so no worker/provider integration is enabled. No new public API route. [Evidence](../evaluations/chatgpt-news-live-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Local implementation update:** Protected /api/v1/internal/mcp-review read/bundle/preview interfaces and the separate five-tool /mcp gateway exist locally, disabled pending real account binding. A separate loopback-only scripts.chatgpt_plan_signin process provides local GET /, GET /status, POST /connect and GET /auth/callback. These routes are not exposed by the production API or ngrok. It verifies OpenAI account/plan permission and saves encrypted local credentials; no LANES registration, DB writes or inference. [Runbook](../guides/chatgpt-plan-local-signin.md), [measured state](../evaluations/chatgpt-plan-signin-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier gateway research:** Recommendation remains a separate HTTP gateway calling a fixed set of protected LANES reads, later shared validation preview. Do not import app.main (seeding/retention lifecycle) or auto-export all admin routes. Auth helpers still need LANES capability/actor mapping; OAuth proxy deployments require durable encrypted token storage and stable keys. Actual source and endpoints remain unchanged. [Comparison](../research/lanes-mcp-library-selection-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier MCP planning status:** There is no MCP endpoint, external audit upload route or ChatGPT connection in the current system. Existing saved article/result detail reads are reusable, while protected OAuth/account binding and shared strict preview validation need additive interfaces. Generic admin checks reject Commuter; the existing news capability reader/writer checks are the stronger boundary for new tools. No UI/publication/provider behavior changed. [Proposed flow](../plans/lanes-mcp-chatgpt-review.md), [code findings](../research/lanes-mcp-chatgpt-feasibility-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest provider research:** Active application configuration remains Gemini; Groq only ran isolated captured-evidence experiments. No public UI, API endpoint or worker behavior changed. Gemini daily quota is proved; Groq requires explicit runtime integration and smaller paced batches. [Results](../evaluations/gemini-groq-live-trials-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 13 combined news/weather integration:** Existing protected news-automation DTO fields consume Gemini-native metadata and configuration-scoped circuit state. Gemini uses existing settings JSON key `news_audit_gemini_quota_v1`, retaining OpenRouter `news_audit_quota_v1`; allowance counters stay unknown. News policy includes explicit schema profile/adapter revision. Permanent request rejection blocks that configuration for 60 minutes. Weather retains its independent public Gemini response/cache/cooldown service and safe responsive error handling. No new route/schema/publication gate. Latest live news receipt is 429 at 3/12; this source integration does not release production. [Merge acceptance](../evaluations/gemini-repair-integration-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Included existing feed presentation edits:** `FeedPage` retains its live sort/date summary as screen-reader-only text; `RightSidebar` uses increased desktop spacing/padding; `LocalUpdates` uses the same increased card padding on desktop and the mobile/tablet card. Existing filter behavior, accessibility text, backend reader and API contracts remain unchanged. These prior local edits are included in the developer-requested all-changes roi-branch push. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Public weather insights (October 13, local roi-branch repair):** Existing POST `/weather/insights` delegates to `weather_insights_service.py` and typed `weather_insights.py` contracts. Gemini credentials remain backend-only; response fields remain insights/model. Bounded output/cache/cooldown and safe status/Retry-After replace raw OpenRouter payloads. `WeatherInsightsModal` surfaces an unavailable message, retains chart legend, disables missing-forecast generation and fits fixed desktop/mobile viewport bounds. No endpoint/schema/dependency addition; hosted UI remains unchanged pending release. [Verification](../evaluations/gemini-weather-followup-20261013.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Final-code verification:** Current final-code verification passes **507 combined backend/native checks**. A fresh v20 September 24 normal-worker replay completes five checkpoints/five locations/eleven negative decisions without audits or zones, and unchanged input remains idempotent. Current-code 3004/8004 desktop/mobile preview checks display September 24 first, then preserved v19 September 9 data (33 locations/three ended events/zero active zones). Actual account GET at 01:34 PHT remains 50/50/0; cooldown through 02:04 PHT. The developer skipped V11 live qualification and a fresh eligible Santo Domingo target replay; these remain unverified. Git publication to `roi-branch` is authorized; merged TypeScript/news lint and 46 responsive cases across main/follow-up runs pass. Primary feed/profile edits are preserved. No cloud deployment. [Completion audit](../evaluations/news-reliability-goal-20261012.md#final-code-completion-audit-and-latest-isolated-checks). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**News reliability diagnostics/coverage (October 13, local):** Existing authenticated GET `/api/v1/admin/news/automation` adds optional model recovery time, transport phase/subtype/elapsed time/actual model and qualified/expected/missing boundary counts. `NewsAutomationPanel` renders them inside existing expandable diagnostics on desktop/mobile; reads remain local/GET-only and never probe the provider. Evaluation JSON stores bounded credential-free transport observations; existing `SystemSetting` stores account quota and at most eight model circuits. A scoped HTTP client, six-request/six-minute budgets and zero-attempt deferrals preserve evidence deadlines/leases. Compact v11/v4 auditing keeps exact backend-owned offsets/hashes and rejects wrong occurrences. The default `barangay-ncr` registry verifies leaf hashes/paths/provenance, with 1,524 records and 186 documented gaps. Pipeline v20/corridors-v7 preserves original WGS84 road vertices and conservatively constructs only newly computed intersection points, retaining strict parent/buffer/core predicates. Unknown free allowance pauses dispatch for sixty real-clock seconds without attempts; longer provider cooldowns and evidence maintenance remain. The requested manual chat source review is separate from worker approvals; no API integration was added. Public flood endpoints, SQL schemas/migrations and dependencies are unchanged. Actual ordered replay/preview and remaining target disagreement: [evaluation](../evaluations/news-reliability-goal-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**News Intelligence audit diagnostics (October 12, local):** Existing protected `GET /api/v1/admin/news/automation` optionally returns server-derived audit state, quota/cooldown timestamps, safe HTTP/error information and request/claim counts. `NewsAutomationPanel` displays them inside Overview's existing expandable diagnostics, with unknown counters shown as “Not recorded”; desktop/mobile layouts and current tabs/location labels are preserved. Reading status does not start collection or call the provider. The worker groups eight locally eligible same-version claims but stores individual evaluation results; persistent quota deferrals retain original expiry and consume no attempts. [Plan](../plans/news-batch-auditing.md), [verification/separate port-3004 preview](../evaluations/news-batch-audit-20261012/README.md). No cloud rollout. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 12 news capture/extraction repair (local):** Existing collection revisits original article URLs using saved reviewed feed provenance after thirty minutes, with twenty oldest captures per cycle across sources; RSS 304/empty results do not imply an unchanged article body. Original body versions remain immutable and failed refreshes surface existing retrieval errors. Rules extraction v17 scopes city observation clocks and depth headings to the matching road list, retains numbered address rows, and stops local facts at city/narrative boundaries. Original source text/offsets and existing publication/audit/placement/history gates remain intact. 271 focused checks and final scheduled-worker replays verify capture/context repairs, but real audit rate limits/HTTP errors prevent operational plotting. No endpoint, frontend, schema, dependency or cloud change. [Evidence](../evaluations/news-scheduled-historical-workflow-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 12 integration acceptance:** Jace's report/moderation/feed/homepage additions below coexist with Roi's two-view News Intelligence and adaptive scheduling. Shared `FloodReportDetailsModal.tsx` now mounts dialog presentation in a body portal at the existing `z-[100]` modal layer, using hydration-safe server/client snapshots. This prevents the admin sidebar obscuring mobile details; Flood History panel presentation remains inline. Both screen sizes, foreground hit testing and owner-notification hydration pass in the final rerun. [Integration record](../evaluations/roi-team-integration-20261012.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**News Intelligence layout (October 11, local):** `NewsIntelligencePage.tsx` defaults to **Overview**, with shared underline `Tabs` linked to accessible panels. `NewsAutomationPanel.tsx` uses flat cards for status, pipeline switches, recent counts and weather health. **Weather details** and **Run details and diagnostics** start collapsed; compact warnings remain visible. **Flooded Areas** contains existing `NewsResults` search, filters, cards and Info/source/history. Results load on opening that tab; mounted panels retain filters and automation polling continues across switches, refreshing cards after completed cycles. Collection status, Sources & feeds and Spatial Operations remain available in both views. Source links, freshness, advisory clocks, sampled coverage and diagnostics remain accessible. Shared `layout/Tabs.tsx` opts into tab/panel semantics and arrow/Home/End navigation when `ariaLabel` is supplied. [Responsive acceptance](../evaluations/news-intelligence-tabs-20261011/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Automatic news scheduling (October 11, local):** `features/news/NewsAutomationPanel.tsx` on News Intelligence shows worker progress/completed-cycle counts plus weather provider health, source links, advisory clocks, sampled localities, adaptive interval/reason, due time, controller freshness, dispatch errors and counters on desktop/mobile. Browser polling/Refresh uses only protected GET `/api/v1/admin/news/automation`; completed cycles invalidate flood-card results. `features/admin/SystemSettingsPage.tsx` removes interval selection and explains automatic 60/15/30-minute policy while keeping stage switches. Legacy interval DTO/storage stays compatible and submitted changes are ignored. New POST `/api/v1/internal/news-scheduler/tick` uses `core/news_scheduler_auth.py` Google OIDC identity, distinct from user JWT/RBAC. `news_weather_controller_service` checks providers/due work and uses `news_job_dispatch_service` for reserved Cloud Run starts; `crud/news_weather.py` persists its own existing SystemSetting JSON record. GET reads never check weather or start jobs. No SQL model/migration. Matching cloud activation remains pending. [Contract](../plans/news-weather-scheduling.md), [verification](../evaluations/news-weather-scheduling-20261011/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 11 news backend/local screen acceptance:** `locality_number_service.py` supplies shared comparison keys while extraction preserves full numbered locality text/offsets. `news_locality_anchor_service.py` grounds complete unique place references against original checked-city OSM nodes/aliases; `news_road_placement_service.py` selects nearby junction-bounded candidates and `news_placement_preview_service.py` recomputes their provenance before existing NOAH ranking. New optional typed locality evidence uses existing saved JSON; absent evidence retains legacy claim hashes. No route, endpoint, SQL schema, frontend component or product-label change. The existing `/map` News alerts panel shows Gov. Pascual **Active zone · Estimated road corridor** with its original 8-inch depth, passability, observation clock and source link. Public backend/frontend zone reads and admin-authenticated `/admin/flood-events/history` find local Zones/Events **58/59/60**. The snapshot uses backend 8003 on frontend 3000, with the existing September scenario clock; shared deployment and clearance-history gaps remain separate. [Verification](../evaluations/news-shared-context-and-history-20261011.md#source-locality-to-road-repair-and-gov-pascual-acceptance). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Runtime testing handoff:** [Expected behavior and acceptance steps](../guides/pasig-recession-observation-collection.md#what-to-expect-when-running-the-system) cover approval/source qualification, shared-location inference, primary saved calculations, fixed fallback, original issuance, pause and scheduled Unconfirmed expiry. The p90 expiry policy and workflow test results do not validate depth-sensitive road-clearance accuracy. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Hosted screen status:** App Hosting rollout 005 now serves the selected saved forecast and calculation at Admin map → Active Zones → Info. Actual #50/#37/#36 desktop/mobile flows and expanded calculations pass. The previously pushed feed navigation spacing is also live, verified at four widths. Earlier local-only UI checkpoints below are historical. No API endpoint, schema or model change accompanies this frontend release. [Acceptance](../evaluations/pasig-subsidence-v3-acceptance-20261011.md#hosted-ui-continuation--october-11-425-pm-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Offline dataset entry point:** `python -m scripts.build_recession_dataset` reads complete existing staff follow-up export pages plus optional explicit episode-review rules through `recession_dataset_service.py`. It emits sanitized conditional research bounds and blockers, keeping test data and production admission separate. No new HTTP route/UI flow, DB write or runtime fit. [File contract](../guides/pasig-recession-observation-collection.md#offline-pairing-and-qualification) and [live collection readiness](../evaluations/pasig-recession-collection-readiness-20261011/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 11 current Pasig workflow:** `GET /api/v1/admin/zones/{zone_id}/expiry-policy` exposes the saved selected calculation, method, city/barangays, frozen depth/basis, original issuance, p10/p50/p90 and optional `activation_retention` fallback basis. Staff permissions and no-store apply. `ZoneExpiryPolicy.tsx` and its shared query hook supply local and hosted Info's primary saved forecast; `CaseReviewSuggestion.tsx` loads the separately labelled pooled research preview in calculation details, and `CrossLocationComparison.tsx` remains a read-only secondary comparison. Historical forecasts remain inspectable. Errors/retry, experimental/proxy and pooled depth-independent labels are retained on desktop/mobile. Hosted rollout 005 and matching API/both cloud workers are deployed. [Acceptance](../evaluations/pasig-subsidence-v3-acceptance-20261011.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Report locality flow:** Geocoder point suggestions and final server-validated OSM road/report geometry resolve administrative identity through `report_locality_service.py` and the reviewed 30-barangay COD/PSGC provider. Submitted labels remain in observation audits. Existing label corrections append immutable `RECONCILE_REPORT_LOCALITY` metadata, preserve geometry/source edit and observation clocks, and are accepted by source snapshot guards only with matching non-label identity. They cannot accept pending clearance or turn simulations into training data. No route or form field was added. Policy v3 retries negative eligibility after 60 seconds; successful forecasts stay anchored. With no ML result or retained deadline, eligible Pasig records receive configured evidence retention from original activation, ending Unconfirmed rather than predicting observed clearance.

**Pasig coverage and abstention:** Eligible Pasig polygons can use the shared Pasig model even when their barangay has no local historical outcomes. This is not guaranteed inference for every record. Unverified location, missing observation time without an accepted registration/submission proxy, incompatible depth snapshots, changed/review-pending evidence or unavailable model assets can still produce an explicit unavailable/fixed-fallback state. A saved operational forecast remains visible after expiry even when the current research preview is inactive or stale. Expiry means Unconfirmed, not observed flood clearance; p90 is an experimental policy estimate, not calibrated certainty. [Evidence](../evaluations/pasig-ml-automatic-expiry-20261010.md#documentation-and-pre-push-audit). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 10, 9:15 PM recovery accepted:** policy v2 recovers immutable original forecasts after late initialization without bypassing current source/review gates. #17/#18 are now inactive with original p90 deadlines October 9, 7:25:02 AM / October 10, 5:04:13 AM (PHT); event timelines say Unconfirmed. #19/#20/#21 retain their deadlines. Production API `lanes-api-00069-fey` serves 100% traffic; cloud jobs use the matching recovery image and minute scheduling is enabled. The local map exposes saved p10/p50/p90 forecasts at Active Zones → All History → Info, verified on actual desktop/mobile records. 106 backend checks, 10 responsive fixtures and four actual Info workflows pass. Accuracy remains experimental; cloud frontend release is separate. [Acceptance](../evaluations/pasig-ml-automatic-expiry-20261010.md#legacy-recovery-and-saved-ui-acceptance--october-10-915-pm). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 10, 8:36 PM: Pasig ML expiry is operational locally and in the shared cloud worker.** API revision `lanes-api-00067-zox` serves 100% of cloud traffic. Independent job `lanes-zone-expiry` runs every minute; the matching news worker also completed successfully. Cloud inference reproduced saved deadlines for pooled zones 19/20 and cross-location zone 21 exactly. Fixed fallback, global pause, source preservation and Unconfirmed expiry remain explicit. Local controls are available on port 3000; the cloud frontend was not released in this scope. Scientific accuracy remains unverified. [386 backend/10 responsive checks and live cloud verification](../evaluations/pasig-ml-automatic-expiry-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Entry points:** System Settings > Evidence expiry > Use ML expiry for Pasig; Spatial Operations > Flood Zone Details > Automatic zone expiry; private `GET /api/v1/admin/zones/{zone_id}/expiry-policy`. Normal startup groups include LANES: Zone Expiry Worker.

**October 10 automatic expiry control (local):** System Settings → Evidence expiry uses the shared Checkbox and existing versioned configuration endpoint for `automatic_expiry_enabled` (default true). OFF pauses scheduled zone/news expiry and deadline-based active visibility across public/Admin/news/routing/event counts/zone matching, preserving original deadlines and source content; manual withdrawal/deactivation/qualified clearance still apply. ON applies original deadlines again. No inactive-record resurrection or research-freshness override. The flag is stored atomically in the existing configuration JSON envelope, preserving legacy nested settings compatibility; matching workers must be rolled out to honor it. Actual port-3000 desktop/mobile controls and 51 targeted/186 native/18 unique responsive scenarios pass. Shared cloud policy is unchanged; no schema/dependency changes. Cloud #23 was already deactivated at 6:00:29 PM, so earlier visibility statements below are historical. [Files, timer/ML distinction and verification](../evaluations/automatic-expiry-toggle-20261010.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Connected source-fidelity correction:** Automatic cloud **Zone #23**, original article #25/run #66/case #2/decision #22, is created by actual capture/extraction/auditor/publication/footprint services and shown with Active Zones 17–21 on normal backend 8000/frontend 3000. Original source excerpt/title/link, observation and expiry survive unchanged; shared map hook/popup remain the renderer. Incorrect official #22 was deactivated after source/geometry verification; other 18 zone responses are unchanged. `local_news_scenario_service.py` reads an ignored database-bound development configuration and supplies per-record clocks to public/Admin/news/routing/expiry readers. Production ignores it; no schema/dependency change or source retiming. `reconstruct_connected_news.py` is an explicit operator command, available through **LANES: Reconstruct Connected Boni**. Admin main timestamp uses news observation. Actual desktop/mobile and 117 targeted/160 native lifecycle checks pass; developer acceptance remains pending. [Evidence](../evaluations/news-boni-corridor-reconstruction-20261010.md#connected-source-fidelity-correction).

**Current reconstruction:** Original Boni is persisted Zone #56 in the guarded historical session. Existing public/Admin zone APIs return the same polygon, original multiline core, expiry and Daily Tribune details; consumer-aware Spatial Review excludes the resolved reprocessed claim. Existing `useFloodZonesLayer`/`FloodZonePopup` own both maps' painting and interactions; no separate news renderer was added. `news_road_corridor_service.py` groups supported source carriageways; estimated-road and publication services validate/dissolve/persist them. VS Code **Start LANES Reconstruction** uses port 3000 with private backend 8001 at September 24, 4:39 PM, with unchanged 4:34 PM observation and 6:34 PM expiry. Normal backend 8000/data remain separate; session-scoped token/cache keys preserve normal state on the same frontend origin. **LANES: Use Current Data** and a reload restore normal data. Actual desktop/mobile public/Admin verification passes; developer acceptance is pending. [Exact files and evidence](../evaluations/news-boni-corridor-reconstruction-20261010.md).

The early-morning snapshots below are historical and superseded by this persisted-zone checkpoint.

**Shutdown handoff / visible-zone status:** The September 24 reconstruction has not produced a Boni map polygon. Its text-only alert is an observation publication, and its Spatial Review item is a geometry-resolution case. Both private persisted map readers have zero active zone IDs; normal port 3000 retains manual zones 17/18. Do not describe switching to port 3001 as revealing the missing zone. Placement resolution and a successful real-service rerun remain required. [Evidence](../evaluations/news-reconstruction-activation-fixes-20261010.md#shutdown-handoff-and-acceptance-status).

**Final reconstruction review check:** The private launcher supplies publication admission to the existing `spatial_review.review_rows` query separately from observation freshness. Current geometry-review decisions supply queue explanations. Actual port-3001 proxy verification returns one Boni Needs Review item, five extracted roads and one text alert; public/Admin active-zone IDs both remain empty pending section resolution. [Verification](../evaluations/news-reconstruction-activation-fixes-20261010.md).

**October 10 reconstruction update:** Existing News Intelligence/persisted map APIs now use verified `daily-tribune` capture identity. Successful source refresh creates a new immutable input; verified `passable_all` flooding can create an Active polygon with `All vehicles` metadata. Historical replay separates publication admission from observation freshness, records the context in policy/evaluation/decision JSON, and refuses shared/normal databases. No new route, SQLAlchemy model or migration. Actual Boni currently appears as a text-only news alert and placement-review case; it has no active polygon. [Files and verification](../evaluations/news-reconstruction-activation-fixes-20261010.md).

**October 10 persisted simulation:** New frontend/backend launchers serve port 3001/8001. Explicit mode routes all API/auth/SSE to the guarded private backend; shared active-zone renderer reads persisted records without a placement overlay. Backend aligns public zones, paginated Admin filters, news projections, Spatial Review and routing/SSE to one frozen clock. Normal port-3000 data remains separate. [Implementation and verification](../evaluations/news-persisted-simulation-session-20261010.md).

**Latest October 10 overlap correction:** `NewsPlacementPreview.display_zone` is null for unresolved/incomplete placement and contains only the resolved candidate core/halo otherwise. The public adapter does not draw old combined-alternative responses. Admin Needs Review starts without candidate geometry and displays only the explicitly inspected candidate using shared review paint. Clearing inspection removes it. Public camera bounds exclude unresolved alternatives. Actual Boni remains Needs Review with four candidates and no published zone; it is no longer painted as one Active-style corridor. [Implementation and evidence](../evaluations/news-placement-alternatives-20261010.md). This supersedes the all-candidate appearance notes below.

**October 10 requested automatic-plot two-layer appearance:** `NewsPlacementPreview.display_zone` contains backend-built `core_geometry` and `aura_geometry`, with original candidate membership. `news_placement_display_service.py` reuses normalized centerlines and dissolves their staff-default decorative 25-m buffer into one halo. `MapCanvas.tsx` selects `activeAppearance` on the shared news adapter; it supplies both existing zone geometry inputs and exact Active core/polygon paint. Source/review status is carried explicitly through `is_pending`; the decorative halo does not become routing/evidence/publication geometry. Admin Needs Review remains aura-only. The loopback saved-snapshot launcher supplies the same fields; missing geometry is surfaced by the normal toast. [Verification](../evaluations/news-shared-map-renderer-20261009.md#october-10-requested-solid-inner-line-and-transparent-outer-area). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 9 shared-renderer correction (supersedes the initial Phase 1 description below):** `admin/review/useNewsPlacementLayer.ts` is now only an evidence/display adapter into `map/hooks/useFloodZonesLayer.ts`. The shared hook owns painting, zoom-14 visibility/hit testing, desktop hover/fly-only click, mobile tap/close/reopen and measured popup anchoring. Active mode uses the existing polygon aura/solid core; review mode uses canonical pending aura. `news_placement_display_service.py` supplies response-only `display_sections` by unioning coincident linework and merging exact endpoints without snapping or filling gaps. Candidate evidence remains unchanged. The saved loopback snapshot applies this service and returns four candidates/three parts, still Needs Review; no real Boni Active Zone or staff list entry is created. [Correction/acceptance](../evaluations/news-shared-map-renderer-20261009.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 9 automatic news map Phase 1 UI checkpoint:** `admin/review/useNewsPlacementLayer.ts` now renders preview geometry with stable sources/layers and zoom-scaled pending aura tokens from `mapStyles.ts`. It reuses `map/components/FloodZonePopup.tsx` for desktop hover/click and mobile tap, with explicit Needs Review, reported source/depth/passability/time and unresolved carriageway content. `NewsReviewEvidence.tsx` enriches optional `PlacementEnvelope.source` from already-loaded article metadata; `MapCanvas.tsx` supplies the existing snapshot title/link. `LiveMapPage.tsx` supplies touch mode. Shared `mapPopupUtils.ts` also serves the existing active hook; candidate popups measure content height and reposition after rendering/camera movement. Initial public overview includes current zones, but selected focus excludes unrelated context. Actual active news remains on the existing core/polygon/list path. Seventeen responsive checks and read-only original Boni hover/focus pass; current source activation/admin parity and semantic road grouping remain deferred. [Verification](../evaluations/news-map-ui-phase1-20261009.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current additive simulation on port 3000:** `getApiBaseUrl` and live SSE preserve the normal connected backend. Only the additional `/news/simulation` snapshot uses the development proxy to guarded loopback backend 8001. The developer explicitly requested adding the past event without removing existing work: original captured coverage is now Cloud SQL article 25/run 61, processed through normal capture/extraction and scoped evaluation. Snapshot projection reuses the resulting backend artifact and correct connected run identity. Existing zones 17/18 are unchanged; public camera includes their geometry alongside the four transparent Boni review candidates. The unrequested simulation status box is removed from map, News Intelligence and shared desktop/mobile news-alert content. Existing toast reports preview/request failures, and optional snapshot failure does not block the news-results reader. No report-panel/schema change, source-gate override, active simulation polygon, routing block or model prediction is produced. [Current steps](../guides/local-news-replay.md#current-port-3000-simulation-session).

**October 9 zone-only simulation scope:** No flood report panel work. The guarded replay's `--at`/`--timeline` uses the simulation date as the present and withholds future article HTML/metadata. Backend `get_active_avoidance_zones(db, now=...)` accepts explicit aware simulation time; normal endpoints retain database time. Actual September 24 checkpoints create no zones and do not reach prediction. Subsidence is read through `/admin/zones/{id}/subsidence-prediction`, rendered by shared `features/flood-followups/CaseReviewSuggestion.tsx`; existing cloud zones calculate labeled registration/submission proxies in read-only service checks. Current news prediction adapter excludes estimated road corridors and the model scope remains Pasig. No rendered acceptance or complete actual-news chain is asserted. [Evidence](../evaluations/september24-plotting-simulation-20261009.md#september-24-as-the-simulated-present-zone-and-subsidence-checks).

**October 9 public coordinate handoff correction:** Shared `MapCanvas.tsx` removes `lat/lng/zoom` from history after applying the delayed camera action. Next search synchronization previously could trigger cleanup and cancel that timer, leaving the map at its stored overview. TypeScript and browser-free ordering checks pass at two fixture widths; physical mobile/desktop rendering is pending. The actual-source September 24 collector/pipeline replay produces zero eligible zones; earlier invented zone 55 is archived. [Evidence](../evaluations/september24-plotting-simulation-20261009.md#latest-correction-actual-source-collector-and-pipeline-replay).

**October 9 saved-news map handoff:** Shared `NewsResultDialog.tsx` adds **Inspect placement on map**, navigating to `/admin/map?review_news=<run_id>:<claim_index>`. `LiveMapPage.tsx` validates the initial identity and opens existing news inspection/layers. The backend continues to return archive/current-queue status and action eligibility; no publication or queue gate changes. The private September 24 preview uses port 3001 (frontend pages from 3000, API from private 8001), with five saved roads, four modeled Boni suggestions and no active historical zone. [Operating steps and limits](../guides/local-news-replay.md#october-9-september-24-manual-map-inspection).

**October 9 news backend acceptance:** Existing discovery/extraction, OSM/NOAH placement, automatic publication and `/api/v1/reports/active-zones` handlers pass near/corner article simulations on disposable PostGIS. Responses retain polygon aura geometry, source road-core geometry and safe news attribution. No UI/endpoint contract change or new browser check is made; publisher/assets/audit are fixtures and real-news/map acceptance remains open. [Verification](../evaluations/news-auto-plotting-backend-test-20261009.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Current automatic prediction workflow — October 8

**October 9 planner audit:** The four private zone prediction/context/evidence readers and existing desktop/mobile Overview match the source-bound contract in [Decision 26](../decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison). Primary selection and operational lifecycle are unchanged; matching API/frontend release remains pending. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Cross-location comparison:** `CrossLocationComparison.tsx` loads lazily in calculation details on both layouts and refreshes while open. GET `/api/v1/admin/zones/{zone_id}/cross-location-prediction` uses the same router → `cross_location_prediction_service.py` → existing zone eligibility and exact action/table/target-bound source CRUD. Both Reports+Zones capability and no-store apply. It returns separate conditional quantiles, frozen depth, actual/null clocks, support/uncertainty and explicit abstention/error/retry; primary baseline/status/expiry/routing are unchanged. [Results](../evaluations/cross-location-duration-20261008/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Approved-citizen/cross-barangay continuation:** Whole footprints inside Pasig can return `location_policy=pooled_pasig_multi_barangay`, retaining all names; positive overlap does not admit a footprint extending outside the city. The existing zone prediction GET now includes optional `submission_simulation` plus submission/report/approval audit IDs. Qualifying original road-validation/geometry/owner and current event/approval/version/clocks are checked, with later evidence stopping the proxy. The simulation starts from immutable submission recording and anchors issuance to the approval audit, while `reference` remains null. Existing Overview and calculation details label report submission versus admin registration explicitly; no new input/page/bubble/Moderation control. [Acceptance](../evaluations/zone18-submission-simulation-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Calculation walkthrough continuation:** The existing View calculation details disclosure explains three steps: choose the real observation or explicitly labeled registration proxy, apply the fitted lognormal AFT formula, then add the returned remaining duration to the fixed forecast anchor. The backend returns optional versioned calculation metadata with exact coefficients, elapsed age, conditional percentile/normal score and returned total/remaining durations; React formats those values without fitting or recalculating a prediction. Source records/checksum stay accessible in a separate disclosure. Earlier/middle/later dates are model percentiles, not measured road dryness or established accuracy. [Verification](../evaluations/calculation-details-walkthrough-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

The existing **Spatial Operations → Active Zones → Info → Overview** mounts `frontend/src/features/flood-followups/CaseReviewSuggestion.tsx` through `ActiveZoneDetails.tsx`, immediately below the zone timestamps/status. It fetches the summary on entry and once per minute; calculation details lazily load source context with visible loading/error/retry states. Forecast dates stay anchored to the accepted evidence availability or original registration proxy, rather than advancing on refresh. Desktop and mobile use the same existing details workflow.

| Private endpoint (full `/api/v1` path) | Backend owner | Contract |
| --- | --- | --- |
| GET `/api/v1/admin/zones/{zone_id}/cross-location-prediction` | Same router → `services/cross_location_prediction_service.py` | Separate source-bound depth/location research comparison; frozen inputs, prior uncertainty and explicit abstention. Primary baseline remains selected. |
| GET `/api/v1/admin/zones/{zone_id}/subsidence-prediction` | `endpoints/flood_review_suggestion.py` → `services/zone_prediction_service.py` | Automatic location/reference selection, experimental median/interval and explicit unavailable states. A qualified unchanged official registration can supply a separately labeled simulation when actual observation time is unknown. |
| GET `/api/v1/admin/zones/{zone_id}/prediction-features` | Same router/service → `services/flood_feature_service.py` | Current source-labeled terrain/rainfall context, capture clock and missing/error states. Inspection does not make these inputs active fitted predictors. |
| GET `/api/v1/admin/zones/{zone_id}/model-evidence?limit=50&before_id=...` | `endpoints/zone_update.py` → `services/zone_update_service.py` | Future public-update sources, frozen features, independent reviews and qualification blockers; keyset pagination limited to 100. Owner follow-up snapshots remain in their existing private owner/staff/export contracts. |

All four endpoints require an authenticated active non-Commuter staff identity with both Reports and Zones view/full capability, return `Cache-Control: no-store`, and make no zone status/expiry/routing or training-admission write. The source export excludes usernames, free text, media URLs and request UUIDs; it retains internal source/reviewer IDs for independent-review provenance.

The backend resolves full zone geometry with `services/flood_location_service.py` and the checksummed **30-barangay** COD catalog under `backend/runtime_data/flood-location/`. New street names need not occur in training data. Outside/invalid/cross-boundary ambiguity is explicit; nearby report candidates are not automatically borrowed as same-event observations. The separate **20-barangay** OSM/NOAH news-placement catalog and operational flood-footprint gates remain unchanged.

At the developer's choice, future LANES reports/reviews build the independent dataset. Citizen observations, official create/edit actions, public condition updates and owner follow-ups freeze versioned inputs in existing private audit JSON. Actual observation time remains null if absent; registration/submission/capture time is not substituted as observed onset. Public claims retain spot/proposed-road scope, and an independent source review does not certify whole-zone dryness or automatic model admission. Normal writes use available cached environmental data or an explicit missing state, without waiting on providers or backfilling historical records.

The selected subsidence/passability baselines remain experimental pooled models; the worse feature candidates remain unselected. **Forecast-to-Unconfirmed, retained public-zone updates, vehicle-aware uncertainty behavior and matching deployment are still pending.** The public bubble only has the accepted Active/Unconfirmed/Cleared status badge change; no prediction content or test inputs are added. Moderation Center retains its report-outcome scope. [Acceptance](../evaluations/pasig-location-feature-models-20261008/README.md), [remaining tasks](../task_plan.md#current-ml-checkpoint-and-next-task). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 research model/simulation continuation (local):** Existing Overview automatically reads zone prediction with explicit pooled-transfer warnings and optional registration_simulation from a matching unchanged CREATE_OFFICIAL_ZONE audit. Real observation reference remains unknown; the audit proxy is never backfilled. Issuance anchors prevent refresh from moving forecasts. Existing duration-model/preview gain training-cohort versus 30-location transfer metadata; authenticated no-store GET `/admin/news/passability-model` and POST `/admin/news/passability-preview` use `flood_passability_prediction_service.py`, the shared mathematical kernel and runtime `passability_aft.json`, trained from nine reviewed transport projections/seven barangays/two summaries. No extra UI input/page/tab, physical dry/passability declaration or zone expiry/status write. Original routing colors/vehicle restrictions remain; green/low permits light vehicles, yellow/medium blocks them under current policy. Real #17 automatic simulation, 127 backend and 34 responsive checks pass. [Acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Initial October 8 automatic adapter (superseded scope checkpoint):** `ActiveZoneDetails.tsx` passes zone ID to `CaseReviewSuggestion.tsx`; Overview reads GET `/admin/zones/{zone_id}/subsidence-prediction` automatically and every minute. The zone_prediction schema/CRUD/service resolve the whole polygon through reviewed boundaries and select qualified timed same-zone/event citizen/current linked news evidence. Nearby pending reports use the shared 500 m radius as candidates only. Compact median/interval/clocks and read-only details replace hypothetical fields, checkbox and save controls. Missing/old clocks, scope/correspondence conflict, later updates and inactive/expired evidence have explicit states/errors/retry. Both Reports/Zones read permissions are required; no-store, no DB/expiry/status/routing writes. At this initial checkpoint Zone #17 resolved to Ugong but lacked timed/cohort inputs; the later pooled-transfer registration simulation above now displays a result while its actual observation clock remains unknown. Existing case-suggestion APIs remain; queues/controls are unmounted. [Acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md#automatic-zone-prediction--october-8-correction). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 bubble badge only:** The existing status badge displays the supplied news status (Active/Unconfirmed/Cleared), defaulting to Active for existing active-zone records. All other bubble content, styling and controls remain unchanged. TypeScript and the two existing desktop/mobile map scenarios pass. Backend retained-state delivery is unchanged and remains separate work. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier October 8 case-linked ML review assistant (superseded UI checkpoint):** `features/flood-followups/CaseReviewSuggestion.tsx` is mounted in Active Zone Overview directly below the existing timestamps; linked citizen cases load the compact experimental prediction summary automatically, and unlinked zones show unavailable. The saved median/remaining-time/interval summary and inline evidence details pass 54 distinct desktop/mobile scenarios across runs; live official/news/manual-zone prediction coverage is not implemented. `ReviewSuggestionQueue.tsx` and `FollowupReviewQueue.tsx` are currently unmounted: the developer rejected both sections and per-report ML controls in Moderation Center, whose original report-outcome filters/cards/Info/Review on Map are restored. Separate staff follow-up review access remains unfinished; a standalone ML list is outside the accepted Overview UI scope. Backend `flood_review_suggestion` schema/CRUD/service/endpoint modules expose staff Reports read/full GET `/api/v1/admin/reports/{report_id}/review-suggestion`, full-only POST at the same path and bounded GET `/api/v1/admin/flood-review-suggestions?limit=25&before_id=...&actionable_only=true`. Server selection preserves explicitly observed wet references and immutable saved model/evidence inputs, with abstention and no-store/UUID retry/permission/privacy guards. Later public zone observations remain review signals, including untimed updates; no original observation time is inferred. Local owner follow-up/staff review/export and case integration now pass 119 backend and 16 desktop/mobile scenarios, with TypeScript/scoped lint. Model/public status/expiry/routing/schema/dependencies are unchanged; deployment/pilot/physical PWA remain pending. [Acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 admin zone evidence review (local):** ActiveZoneDetails Overview and Needs Review share FloodFacts/FloodSeverityBadge and canonical/legacy survey formatting. Zone details separate operational notes from original_report_text, show known location/direction/source/contributor and separate media, with fixed shared RecordDetailsDialog actions. Community updates remain one record per submission; desktop sticky list and mobile list-to-detail show individual ZoneObservationReview comparison, location/geometry/survey/media and review/application history. ZoneGeometryComparison draws the official boundary and submitted road without a second WebGL map. POST `/admin/zones/{zone_id}/updates/{update_id}/editor` validates explicit field selection and returns an editor patch/current version. Existing OfficialZoneDrawer preserves drafts until Incorporate confirmation and returns through Back to zones; stale drafts stay inspectable until explicit replacement. PUT delegates to zone_editor_service with full zones permission, version guard, row locking, existing buffering/event lifecycle and atomic UPDATE_ZONE provenance for actually changed selected facts. Only a saved edit displays application; review remains independent. No public report field, SQLAlchemy model, Alembic definition or package addition. [Acceptance](../evaluations/flood-zone-community-updates-20261008.md#admin-comparison-follow-up-october-8). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 publication audit:** Final code and documentation use one public Report Flood panel, original guest login, shared report fields, editable witness road proposals and a confirmed New report header action. Private zone evidence remains exclusively in Spatial Operations Active Zones. Shared WebGL recovery is documented separately. Sixteen native and twenty-two responsive browser scenarios pass across task runs; migration/dependency checks require no definitions change. User-authorized branch publication is prepared; production/device/provider release remains open. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 update return action (local):** `FloodReportPanel` now supplies a signed-in New report header action through shared Panel headerActions; it stops drag/collapse propagation and opens the existing ConfirmDialog. Keep editing retains current update fields/media. Discard exits update mode, releases its media previews and restores the independent unfinished flood report. Dialog state is scoped to the selected update key, and the action is disabled while submission runs. The old body return button is removed; guest login UI stays identical. Desktop/mobile and 320px header/dialog checks, guest parity and TypeScript pass. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 WebGL recovery (local):** Shared BaseMap defers map allocation until a cancellable animation frame so Strict Mode can dispose its first effect without a graphics context. Browser-denied construction shows a responsive Map unavailable screen with Retry map and clears partial DOM; context loss pauses detailed-style retries and allows native restoration to clear the message after rendering. Manual retry reruns only the map lifecycle and retains surrounding forms. Delayed compass/load/resize tasks are guarded/cancelled on disposal. Six desktop/mobile checks and TypeScript pass; no new package/API/database/deployment. [Verification](../evaluations/cloud-performance-20261007.md#october-8-webgl-recovery). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 guest report parity (local):** `FloodReportLoginGate.tsx` is the original Report Flood login markup shared directly by both modes in `FloodReportPanel`. The body-only `ZoneUpdateForm` mounts after authentication; guest mode has the identical Login Required presentation and no selected-zone banner. Header controls also match the original. Update login redirects retain zone/condition. Two responsive markup/dimension parity checks and two signed-in upload regressions pass, with TypeScript/scoped lint. [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 8 unified Report Flood panel (local):** `GlobalMap` owns one `FloodReportPanel`; `MapContext` holds selected-zone mode and independent update road anchors. `ZoneUpdateForm` is body-only. `FloodReportFields` and `useFloodMedia` share depth, description, original Take Survey/separate survey view and attachment handling. Update mode adds one Open camera button beside the original large picker and accepts edited start/end, direction and validated map preview; no separate update panel/time/spot/depth-unsure controls remain. `useZoneRoadPreview` shares the existing road-preview API between form/map. Mobile map confirmation preserves the mounted form; the shared LocationAutocomplete follows keyboard/sheet movement within viewport bounds. New-report drafts remain separate, and the removed ordinary-report time is never sent from old drafts.

`GET /api/v1/zones/{id}/update-context` supplies authenticated active-zone road endpoints when stored centreline geometry exists. Multipart POST `/zones/{id}/updates` accepts proposed endpoints; the server rebuilds the road proposal, stores it in existing audit JSON and leaves operational geometry unchanged. Missing observation time is null, separate from submission time. Info/count and per-zone community evidence remain solely in Active Zones; details include proposed endpoints/road verification for existing Edit/Deactivate and explicit review. Staff capability checks, no-store responses and private audit exclusion remain. Sixteen native checks pass; browser verification/release limits are recorded in [acceptance](../evaluations/flood-zone-community-updates-20261008.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 Functional System Settings (local):** `/admin/settings` now edits four operational groups and shows recorded stage health. `GET/PUT /api/v1/admin/settings/configuration` return typed settings, revision, update metadata, supported options and read-only runtime status; capability `settings=view/full` is enforced. Legacy GET remains compatible; legacy PUT returns 410. Citizen multipart submission accepts optional timezone-aware `observed_at`; older clients remain in review. Automatic approval is labelled in staff moderation and records provenance/policy in existing audit/timeline history. Fixed-tick worker cadence is database controlled. Matching production rollout remains pending. [Verification](../evaluations/functional-system-settings-20261007.md), [operator guide](../guides/system-settings-rollout.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 structured Pasig follow-ups (local):** `features/flood-followups/FollowupSubmission.tsx` integrates owner observations into Profile/Reports; `FollowupReviewQueue.tsx` adds staff review and JSON page export to Flood Report moderation on narrow/wide screens. `api/v1/endpoints/flood_followup.py` exposes authenticated owner GET/POST `/reports/{report_id}/follow-ups`, Reports-capability staff GET `/admin/flood-follow-ups`, POST `/admin/flood-follow-ups/{followup_id}/review` and GET `/admin/flood-follow-ups/export`. New schema/CRUD/service modules use existing append-only audit JSON and sanitized existing event timelines; no model/migration change. Keep source observation/availability/submission/review clocks and immutable place fingerprints separate. Full report permission and a different reviewer are required for acceptance; records do not modify expiry/status/routing/reputation or grant training admission. General audit reads exclude private follow-up actions (BUG-118). TypeScript/AST and source review pass; actual DB/API/browser/PWA acceptance and deployment are pending. [Evaluation](../evaluations/structured-flood-followups-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 duration research API:** `GET /api/v1/admin/news/duration-model` and `POST /api/v1/admin/news/duration-preview` use `api/v1/endpoints/flood_duration.py`, `schemas/flood_subsidence.py`, `services/flood_subsidence_prediction_service.py` and the interval AFT kernel. Both require authenticated staff report-read capability and no-store responses. Preview inputs are hypothetical, require timezone-aware first-recorded-wet/issuance clocks and explicit research/continuity assumptions, and can abstain on unsupported scope. The packaged conditional research model learns no depth/location effects, remains deployment-ineligible and cannot alter zones, expiry, clearance or routing. No UI, model-table or migration changes. The subsequent continuation passes 17 duration API/service checks (isolated HTTP router, actual permission dependencies and real application route registration), plus 45 numerical/model checks; deployed HTTP/browser acceptance remains open. [Validation](../evaluations/pasig-subsidence-validation-20261007/README.md). [Experiment](../evaluations/pasig-duration-model-20261007/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 second performance pass:** `services/flood_sync_service.py` runs one authoritative DB poll/serialization per 15-second cycle per API worker for all `/sync/stream` subscribers. Each queue retains only the latest snapshot; stable ordering avoids false updates, failed reads retain the existing unavailable signal, and idle/shutdown releases polling state. Routing reads do not use this snapshot cache. Current/forecast weather endpoints use synchronous FastAPI handlers so provider I/O runs in the thread pool; AI insights remains asynchronous. `BaseMap` warms offline routing after rendering via browser idle scheduling with a two-second timeout/500-ms older-browser fallback; offline route calls still initialize on demand. [Verification](../evaluations/cloud-performance-20261007.md#second-pass-shared-polling-and-responsive-weather-handlers). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 performance behavior:** Initial Home/Feed visits defer the global map; opened map context persists across commuter navigation, with hidden map polling paused. Analytics/save-place panels load on demand. Feed location navigation carries URL coordinates as well as the existing event. Public/staff map zone polling falls back every 60 seconds; actual changed sync snapshots invalidate immediately, and public news keeps independent 30-second status polling. Failed sync reads preserve offline data and surface errors. Production network reconnect refreshes data without a full-page reload. Routing/retention synchronous waits run off the API event loop; flood eligibility and endpoint/auth contracts are unchanged. [Verification](../evaluations/cloud-performance-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 exact-source auditor update:** `news_claim_auditor` supplies bounded `evidence_options` to both provider transports, preserving full immutable article context and strict quote/place/time/depth/access gates. `check_news_auditor` now includes safe numeric `provider_http_status` on HTTP failures. Successful synthetic free probes at 60 and 20 seconds remain historical review; no screen/route/UI changed. [Verification](../evaluations/phase-36-auditor-evidence-options-20261007.md), [release steps](../guides/news-zone-release-checklist.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 timeout diagnostic:** `scripts.check_news_auditor --probe --timeout-seconds 60` overrides only the single synthetic probe; valid bounds are 1-120 seconds. HTTP and whole-response limits agree. Regular worker requests still use 20 seconds; no persistent setting or frontend/endpoint changed. One live retry returned invalid evidence offsets and was rejected. [Current result](../evaluations/phase-36-news-runtime-packaging-20261007.md#october-7-live-timeout-follow-up-earlier-diagnosis). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 operator/runtime checkpoint:** `scripts.package_news_noah_assets` copies an already checked catalog into a new versioned snapshot. `scripts.verify_news_runtime_assets` checks the bundled analytical assets during Docker build and supports network-free inspection. `scripts.check_news_auditor` checks settings by default; explicit `--probe` tests one synthetic free-router response without database access. Existing map screens/components are unchanged by packaging. [Exact local/Google Cloud/Firebase steps](../guides/news-zone-release-checklist.md), [verification](../evaluations/phase-36-news-runtime-packaging-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 6 estimated news-road integration (current):** Qualified current independently audited news can now activate a uniquely grounded OSM/NOAH estimated road corridor automatically. The existing 25 m road-zone margin is routing/display policy, not measured water width. Recomputed server assets, locality containment, disconnected components, source centerlines and unchanged lifecycle gates are required. Unresolved placement enters Needs Review; unchanged reviewed asset revisions are skipped on later sweeps so they cannot starve later claims. Existing public/staff layers, details and shared components are reused on desktop/mobile. Safe article/observation/status/basis projections and map cache invalidation are connected. Matching runtime assets/release and real-article/PWA acceptance remain open. [Verification](../evaluations/phase-36-estimated-road-zone-integration-20261006.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 5 automatic footprint worker (earlier checkpoint):** BUG-107–BUG-110 repairs and the automatic worker connection are complete locally. Saved extraction → independent evaluation → publication/refresh/clearance/expiry → exact approved footprint activation now share the explicit pipeline; the discovery CLI has an opt-in full-pipeline mode and the local Cloud Build job command uses it for a future release. **456 distinct checks pass**: 258 targeted, 194 related and four event regressions across 21 suites. No real current footprint catalog is provisioned and no cloud job was changed or executed. Desktop/mobile geometry/attribution controls, actual source provisioning, full live map/routing and staging/PWA acceptance remain pending. No model/migration/dependency or frontend change. [Verification](../evaluations/phase-36-automatic-footprint-worker.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Operational staff API contract:** `/api/v1/admin/news/claims/{case_id}/decision-preview` passes the authenticated writer ID to the service; preview and save repeat stored active/capable actor and current evidence/geometry checks. Geometry requests require `operational_footprint_srid=4326`; existing-zone IDs additionally require exact incident/component ownership and matching metadata. Private provenance stays in history snapshots and is omitted from public projections. Frontend geometry fields/controls remain pending; the automatic worker now supports exact approved catalog records and server-recomputed estimated road corridors. [Contract/runbook](../evaluations/phase-36-trusted-footprint-contract.md).

**Shared Select viewport repair:** `shared/ui/forms/Select.tsx` measures the visual viewport, opens upward when bottom space is insufficient and caps its scrollable option list/position. Staff news evidence controls remain reachable on desktop/mobile; existing queue locality filters and Active Zone styles/actions pass regression checks. No eligibility logic moved into the frontend.

**Current routes/components:** public `GET /api/v1/news/alerts` (page/page_size) and `/alerts/{case_id}` return safe source-alert projections only. Staff `GET /api/v1/admin/news/claims/{case_id}` and `/history`, `POST /decisions` and `/decision-preview` enforce active session plus server reports capability (`view/full` read, `full` write; Commuter denied). `NewsDecisionControls` uses audited evidence and expected revision/UUID, separates public corrections from internal reasons, previews server effect and retains uncertain drafts. `NewsAlertsPanel`/`usePublicNewsAlerts` share desktop/mobile source views, 30-second polling/focus/reconnect and explicit last-downloaded offline/error states; no client calculates flood eligibility. `news_pipeline_service` and `scripts.run_news_pipeline` provide the explicit bounded saved-article handoff.


**Earlier storage-only stage:** local inspection and five-table schema were delivered before the publication/lifecycle follow-up above. The historical checkpoints below describe that sequence; current alert APIs and controls are now connected, while operational geometry/routing activation and deployed acceptance remain open.

**October 5 backend evaluation handoff:** separate bounded `scripts.evaluate_news_claims --seed` and `--evaluate` commands bind eligible completed extraction and audit due work. No new HTTP endpoint, frontend control, extraction worker coupling or public map/routing write. Strict provider evidence stores immutable article/claim identity and structured place/status/time/depth/access evidence; finite leases, safe errors, retries and completion freshness are backend-owned. Current placement reads use the rebuilt explicit-C5-relation catalog and twenty-barangay Pasig OSM community polygons. C5/Ugong now clips to supported preview geometry. The placement/extraction response adds `barangay_osm_relation_id`, `barangay_source_url` and `barangay_source_classification`; ambiguous sections and remaining missing barangays stay explicit. These additive provenance fields do not add a frontend screen/control or public decision. [Guide](../guides/news-claim-evaluation.md), [verification](../evaluations/phase-36-independent-evaluation-and-spatial-coverage.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Primary Panel organization (local):** Needs Review retains its blue user/violet news queue cards. Its search covers report/title, location, city, barangay, evidence and review reason; optional City/Barangay/Severity controls use the existing shared Input/Select. Protected `GET /admin/review/items` accepts `q` (120 characters), `city`, `barangay` (100 each), and `severity=low|medium|high|extreme|unknown` in addition to source/page/page_size. The server groups first, matches any member satisfying all filters, keeps the entire canonical group, then paginates. Source badges remain unfiltered totals; `item_total` counts records in matching full groups, and `total` counts matching cards. Source-wide city facets remain available on empty searches; barangays are scoped to the chosen city. City aliases use the existing locality normalization. Cards receive server summaries for roads/areas, all severity levels and depth levels, related count, evidence and latest report time. Filters survive opening/back navigation and city changes reset barangay. Barangay is disabled with “Select a city first” until a city is selected; Clear filters disables it again. The shared Select has an optional native disabled trigger and suppresses its dropdown while disabled. `components/FloodRecordSummary` shares flat headers, severity/depth badges, timestamps, locations, fact rows and action spacing between `PendingReportsPanel`, `ActiveZonesPanel` and `ZoneContributors`. Reports expose reporter/trust, reported vehicle access/hazards and attachment count through existing detail facts; zones expose effective conditions, expiry, primary report and notes. Contributor expansion and map focus remain, with keyboard-accessible inspect/restore buttons. `SpatialPanelButton` wraps the existing shared Button: 32 px desktop small actions and 44 px narrow/coarse-pointer targets. Narrow/landscape overflow and safe-area scroll padding are verified. No model/migration/dependency or merge/geometry rule change. [Verification](../evaluations/phase-36-needs-review-inspection.md#october-4-primary-panel-search-and-detail-consistency).

**Reviewed flood growth (local):** Pending evidence can be reviewed across barangay/street boundaries. The backend uses pairwise geometry/time criteria and exposes nearby active event-owned zone targets; proximity is a review suggestion, not proof of one flood. `POST /admin/reports/merge-preview` is protected/read-only and composes the same coverage as publication. `/reports/merge` accepts `extend` (default; union supported old coverage/core with the reviewed section), `corroborate` (retain boundary/conditions), or `add_section` (new zone/conditions in the same event). Submitted line/multiline sections are buffered in UTM 51N; disconnected boundaries require a separate section or explicitly reviewed continuous extent. Legacy approval preserves old coverage; batch merge only links evidence. Original reports/posts are preserved, event locations record each supporting road/barangay/city, and merge/audit commit atomically. No model/migration/dependency changes. [Verification](../evaluations/phase-36-needs-review-inspection.md#october-4-cross-boundary-growth-implementation).

**Related report layout:** `RelatedReviewReports` now loads each visible member through the protected detail read and reuses `PendingReportsPanel`. Related rows use the same report badges, time, location, Info and moderation controls as the main report, without a duplicate selected row. Per-member read failures expose retry; records outside the current queue are inspection-only. Approving/rejecting a different report preserves the primary detail. The existing queue styling remains; the later Primary Panel refinement above also shares the flat record presentation with Active Zones. [Verification](../evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-consistent-related-report-layout).

**Selected-report membership:** The member read accepts any current report identity and resolves its group in the backend, returning the canonical anchor key and grouping reason. `NeedsReviewPanel` no longer retains the last queue card's group; member query caches use the selected identity and member page. Map selection and external handoffs therefore cannot inherit another card's related reports. Singleton groups hide the related section. Boundary-crossing grouping now follows the spatial/time policy above; barangay names alone do not exclude review. [Regression verification](../evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-selected-report-group-resolution).

**Local v11 placement:** the protected news placement GET adds `modeled_fragments`, `preview_geometry`, `fragment_status`, backend `reported_severity` and barangay catalog provenance. Each fragment retains stable ID, geometry and scenario/class/source hashes; the modeled envelope preserves gaps. Reviewed polygon loading validates PSGC parents and clips candidate roads; missing real polygons remain explicit coverage failures. The existing route remains protected/read-only; the reviewed five-table publication migration is a separate storage delivery, with no runtime decision/public write connection. [Placement verification](../evaluations/phase-36-disconnected-news-placement.md), [storage checkpoint](../evaluations/phase-36-news-publication-storage.md#october-5-pre-push-checkpoint). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Local Spatial Operations inspection:** `/admin/map` now labels its first tab Needs Review and keeps Active Zones. All/User Reports/News Claims filters consume protected `GET /api/v1/admin/review/items`; `GET /items/{key}` provides source-specific preserved evidence and current-queue membership. `GET /api/v1/admin/review/groups/{key}/members` paginates related user reports. Backend `spatial_review_grouping` reuses merge road normalization with pairwise two-hour complete-link checks (500 m on the same road/city, 50 m otherwise) before card pagination; report counts remain distinct from card counts. New admin feature components are `review/NeedsReviewPanel`, `ReviewQueueCard`, `RelatedReviewReports`, `NewsReviewEvidence`, `reviewApi` and `useNewsPlacementLayer`. Light blue user group cards open individual evidence with a plain Related reports list inside the detail view; the queue has no member dropdown; light violet news cards remain separate. Desktop evidence remains beside the map; mobile switches Map/Evidence, including narrow/landscape layouts. News placement now draws separate backend `preview_geometry` road pieces using the shared transparent review aura, with reported-depth colors or neutral gray. Whole candidate centerlines remain evidence, not a substituted flood extent. Selection creates no buffer, public zone or routing effect. Report moderation and independent Create/Merge/Edit sessions remain. SQL/service/API layers use existing report/extraction storage with no migration; news decisions/publication remain unfinished. [Verification](../evaluations/phase-36-needs-review-inspection.md).

**Previous v10 backend placement checkpoint:** captured extraction adds `placement_preview` with exact NOAH scenario/class overlaps, section-matched Pasig DRRMO rows, OSM/source checksums and alternatives. `GET /api/v1/admin/news/results/{run_id}/{claim_index}/placement` is rate-limited/admin-protected and computes current placement from immutable evidence without network, auditor or database/public writes. New providers: `news_placement_preview_service.py`, `noah_vector_catalog_service.py`; contracts: `schemas/news_placement.py`; builder: `scripts/build_noah_placement_catalog.py`. External assets use `LANES_NEWS_NOAH_DIR`. That checkpoint changed no UI/lifecycle; the subsequent local inspection UI is described above. 550 distinct backend checks passed (one skip). [Verification](../evaluations/phase-36-backend-placement-preview.md).

**Latest local v9/v1.7:** `summary.water_level` prefers source wording over normalized gauges; `passable_unspecified` renders **Passable; vehicle types not specified** and cannot authorize closure. Clearance clocks preserve subsided status and the reported **by** bound. Road/landmark province and island follow grounded city/PSGC, removing unrelated homonym provinces. The existing shared responsive UI consumes server labels without frontend business rules or source changes. Four complete source bodies, 38 database/detail records and both actual API/proxy readers agree; 595 backend checks pass. Prior v8 notes below are history. No production release or visual acceptance is implied. [Audit](../evaluations/phase-36-four-article-source-audit.md).

**Current local v8/v1.6 workflow:** existing publisher corrections supersede current inputs even when revised body/RSS denies or removes local flood evidence; previous inputs/runs stay immutable and newest readers hide unsupported claims. Collection uses credible history only to preserve retrieval-error visibility, never to restore older main results. Approved `passable_with_caution` has an explicit no-closure guard; server `NewsFloodSummary.passability` supplies the Road passability label rendered by `NewsResultDialog` in its shared responsive grid. The dead no-locations Collection option is removed with legacy enum compatibility retained. Independent road predicates retain separate facts. All 452 backend tests, TypeScript and scoped lint pass; private API retains 33 sites and 20 caution records. Inspected production collection remains every three hours, with no new refresh policy or deployment. [Follow-up](../evaluations/phase-36-news-workflow-follow-up.md).

**September 9 local v7/v1.5:** three captured publisher bodies produce 33 readable location records through reconstructed RSS discovery and existing durable processing/SQL reading. Extraction preserves validated road/barangay identity, contiguous list evidence, each row's own depth and scoped observation clocks. A narrowly approved GMA matching publication/update header can anchor later same-day observations while original publication remains unchanged. Forecast/drill/negated/history/prevention list context remains excluded; independent narrative ends list inheritance. Real authenticated API/frontend proxy list and detail evidence pass, with 410 related tests. Final visual verification remains blocked by saved browser permission. Collection retains three September 9 articles needing checks alongside the ready September 24 article; no historical zone/report creation. The private launcher now requires explicit restart after backend changes rather than Windows auto-reload. No new API/model/UI/dependency; production release pending. [Evaluation](../evaluations/phase-36-september9-production-day-replay.md).

**Article-level city context (local v6/v1.4):** `mark_city_summaries_as_context` reconciles completed rule extraction within one article. Credible streets/landmarks/barangays in the same resolved city make redundant broad city observations context only. Caption-only, ambiguous, speculative, negated and conflicting specific claims cannot hide a city-only observation; distinct explicit times remain separate. Existing SQL reader/Collection gates honor the context flag before pagination/counts. Source sentences, offsets and per-street facts remain stored. The local replay now has five readable street cards, zero attention items and two immutable extraction runs; no new API, model, migration or frontend filtering. Production release remains pending.

**News details location fields:** `NewsResultDialog` supplies a flat Reported location section through the optional `locationDetails` slot in shared `FloodLocationSummary`, between the location heading and measurements. It displays existing detail claim fields `canonical_road`, `canonical_barangay`, `road_segment_raw` and `local_area_raw`; a missing road says **Not specified for this mention**. City remains in the summary heading/area. No extraction, cross-claim inference, API/model change or verified geometry is implied. Existing callers keep their layout without the slot. Desktop/mobile live replay and existing modal regression checks pass; local frontend change, not deployed.

**Local page verification:** `backend/start-local-news-test.ps1` loads ignored `.env.test.local` before the shared encrypted cloud config and verifies a dedicated loopback `lanes_news_test` target. `frontend/start-local-news-test.ps1` uses the existing API proxy; both bind to loopback. `scripts.seed_local_news_replay` stores actual historical evidence through existing services. Authenticated real API/browser checks confirm five main-list road locations, original dates, Boni evidence/source and zero Collection attention items. No new route, response field, UI component or model is introduced. [Runbook](../guides/local-news-replay.md).

**Local v5 replay correction (not deployed):** server extraction preserves narrative road intersections/directions, compound measurements, original observation/clearance clocks and parent-city PSGC identity. `location_context_only` qualifiers remain in evidence history but count toward neither main-list flood locations nor Collection questionable mentions. A genuine isolated historical article has five road sites plus two broad summaries, is `ready` with zero attention items, and does not create reports/zones. Production v4 history is unchanged. [Replay evidence](../evaluations/phase-36-september24-historical-replay.md).

**Strict actual-flood collection follow-up released:** backend body admission and main-list SQL require affirmative Metro Manila flooding evidence; newly unreadable articles remain discovery diagnostics rather than candidates. GET `/api/v1/admin/news/collection?status=excluded` exposes unsupported legacy history, while default attention excludes it. `NewsCollectionDrawer` and `newsApi.ts` render the backend's excluded status on desktop/mobile. v4/v1.2 preserve immutable evidence. API `00049-q25`, the matching collector and Firebase frontend `build-2026-10-03-002` are live. All 341 backend tests, 15 PostgreSQL checks and 15 deployed desktop/mobile cases pass (mocked API/session); saved/normal executions succeed. No database schema change. [Evidence](../evaluations/phase-36-news-content-quality-investigation.md#v4-backend-release-verification).


**News evidence correction released (October 3):** shared backend prevention/habitual and Metro Manila rules qualify every readable collector body and main-list/Collection counts before pagination. Local headlines cannot bypass body evidence. Excluded artifacts retain source/history with an explanatory reason. Corrected processing is versioned (`rules-psgc-osm-2026-10-03-v3`, extractor `taglish-rules-v1.1`). API `00048-xc7`, the matching collector and Firebase frontend `build-2026-10-03-001` are live. Approved migration and corrective/normal collector executions succeed; ten new runs preserve 20 earlier runs and 24 articles. All 306 backend checks, eight PostgreSQL checks and 13 deployed desktop/mobile asset checks pass (API/session mocked). See [release evidence](../evaluations/phase-36-news-content-quality-investigation.md#completed-production-release).

**F4b durable monitoring:** GET `/api/v1/admin/news/monitoring` supplies current body totals, newest extraction counts and ten retrieval issues. GET `/monitoring/discovery` and `/monitoring/fallback` use `news_telemetry.py` CRUD/schemas and `news_telemetry_service.py` for protected, bounded history reads with sanitized 503s. `NewsSourcesDrawer` Pipeline mounts lazy `NewsTelemetryHistory` sections with independent pagination/refresh, feed counters and alternate lead metadata; shared dialog/buttons preserve responsive/keyboard behavior. `news_discovery_service` records staff and collector runs; `news_fallback_service` captures stable input before retrieval. Fallback inspection records an attempt; history refresh is GET-only and does no external retrieval. The four approved telemetry tables are migrated locally and in production to `c5a7e9d2104f`; automated deployed desktop/mobile checks pass, while developer visual acceptance remains open. Delay is unavailable until durable publication exists. See [verification](../evaluations/phase-36-f4b-monitoring-check.md).

The staff news `open-leads` endpoint accepts `retrieve_articles=true` to fetch up to three approved alternate publisher bodies. Each result includes its publisher ID, fetch timestamp, text or error, and a same-event review status. It now persists operational lookup/lead metadata, while alternate article bodies remain response-only and do not create flood evidence, publication or activation. Index-seen dates are not publication/observation dates.

**October 2 production checkpoint (historical):** Priorities 3 and 4 were deployed with migration `f29b6c8d104e`, active API revision `lanes-api-00047-59t`, and collector `--discover --process --limit 50`. Shared extraction stores optional `RoadPlacementEvidence` under each claim in the existing JSONB result. The provider uses bundled `runtime_data/osm/` files, validates full checksums/boundaries/nodes, and performs no geometry HTTP requests or public writes. Ten backlog inputs retain old and map-aware results; repeats create no work. Production GMA historical span matching passes. Missing source/coverage/precise extent remains visible, and neither centerlines nor historical map data authorize a closure. Fresh incident acceptance and Priority 5 publication/review/correction/expiry remain open. See [release evidence](../evaluations/phase-36-reusable-road-match-check.md#production-release-verification).

**Intended automatic news flow:** RSS/discovery → server NLP/NER → bounded OSM road placement with analytical UP NOAH vectors and matching Pasig DRRMO history → automatic source-labeled alerts and gated expiring zones → commuter map/routing. Routine eligible news claims bypass staff approval; Needs Review handles exceptions and corrections. Existing user-report moderation retains its current workflow. Local NOAH/DRRMO previews and F5 inspection are implemented. Independent auditing, durable publication/lifecycle and exact catalog/estimated-road activation are implemented locally. Estimates remain labeled and never become measured footprints. Existing F5 transparent previews and public/staff active core/aura rendering are retained; matching rollout, real-event/PWA acceptance and optional geometry editor handoffs remain pending.

**OSM runtime dependency isolation:** `NewsRoadPlacementProvider` reads the validated JSON catalog and imports pure graph/geometry routines from `article_road_match_service.py`. Native `osmium` loading is now confined to `load_bounded_osm_roads`, preserving the raw-PBF parser while allowing runtime extraction/catalog placement without that native import. All 140 focused regressions pass. Raw-PBF tools retain the separate local Windows restriction; no API/UI/schema/dependency change. See [verification](../evaluations/phase-36-automatic-plan-alignment-audit.md#verification-recovery-runtime-dependency-isolation).

The local-status and unchanged-scheduling statements in the earlier preparation notes below describe the pre-release state and are superseded by this production verification.

**Priority 5 reading/monitoring state — implemented alongside local F5 inspection; full manual acceptance pending:** `/admin/news` retains its thin route/loading/error boundary and session/persistent-map shell. NewsIntelligencePage renders one NewsResults list with Collection status and Sources & feeds controls. NewsResultDialog has Flood Details / Source Article tabs; NewsSourceArticle shows title/publisher, original publication and LANES-save dates, full text and lazy collection details. NewsCollectionDrawer uses the shared RecordDetailsDialog drawer variant, lists server-classified article states and opens source text within the same focus-managed surface. NewsProcessingDetails loads bounded immutable history within Source Article's desktop right pane or mobile Processing history view; collection article inspection keeps lazy More details. Shared FloodLocationSummary/FloodDetailMetric/Tabs/TabContentPanel/Card/Button/Input/Select/Pagination/Skeleton remain reused. The existing Spatial Operations report modal uses the same metric tile. Responsive single/two-column facts, full-height mobile drawer, safe areas and 44px actions are implemented; manual visual acceptance remains pending. No browser or development server was started. Older standalone article components are retained as earlier implementation files but are no longer mounted by this route. See [verification](../evaluations/phase-36-f3-result-browsing-check.md).

**Frontend-only Info refinement:** NewsResultDialog now uses RecordDetailsDialog's opt-in wide/panels layout and shared RecordDetailsPanels for independently scrolling desktop article/history sections inside Source Article. Mobile switches between Article and Processing history inside Source Article; Flood Details shows only flood facts and evidence. Panel history loads when Source Article opens and shares the existing article query; Collection status keeps lazy More details history. Shared RecordTimeline is used by NewsProcessingDetails and Flood History's incident timeline. NewsSourceArticle's opt-in reader presentation uses plain date metadata, avoids the redundant excerpt when full text is available and opens that text by default; collection inspection retains its existing default. Shared panels give the article more width. History has a sticky heading and compact status/date/count rows with errors surfaced. NewsProcessingDetails invokes the Info parent's record-inspection callback instead of expanding output in the sidebar. NewsExtractionRecordView inspects one immutable run with Mentions / Article / Technical tabs in the full-width dialog body, using the existing article query and explicit unavailable/error/retry states. The underlying article/history pane remains mounted but hidden, preserving scroll/expanded state; Back restores focus to the original record action. Full article text is directly visible in reader mode; optional collection metadata remains expandable. Other shared-dialog defaults remain unchanged. TypeScript/lint pass; visual desktop/mobile acceptance remains manual. No backend or database changes were made for this refinement.

**F4a source monitoring:** NewsSourcesDrawer opens from the same page using shared RecordDetailsDialog/Tabs/Button/Skeleton. Publishers and Feed checks render existing authenticated GET /admin/news/sources and /admin/news/feeds payloads. Feed checks load on selection; cached reads and Refresh saved status do not probe, collect or mutate. Saved timestamps/errors stay distinct, missing clocks are explicit and an old successful fetch never clears a displayed recorded error. Full-height responsive drawer, safe areas, 44px actions, focus/escape and visible errors/retry/empty states are reused. No backend/schema/dependency change. Discovery totals, blocked-body/fallback history and collection-to-alert delay are unavailable from these reads.

**F2 staff read API:** `GET /api/v1/admin/news/articles` returns cards, counts, publisher options and server pagination; accepts page/page_size, literal title/excerpt search, publisher, body state, latest recorded processing state and recently-seen/publication ordering. `GET /api/v1/admin/news/articles/{id}` returns the current article, newest twenty recorded runs, total history count and matching immutable inputs. Both use existing staff dependencies; storage failures return 503 and missing IDs return 404. The thin handlers call `news_browsing_service.py`, backed by `crud/news_browsing.py` and typed `schemas/news_browsing.py`. Reads neither mutate evidence nor execute extraction. These new reads must be released alongside the frontend before production use.

**F3 staff read API:** `GET /api/v1/admin/news/results` SQL-paginates readable reported locations from each article's newest recorded run, with scope `latest_reported_locations`, server search/publisher/condition/placement/order filters and stable run/ordinal keys. Older completed runs, and results with a newer pending/failed attempt, are excluded from the main list. `GET /api/v1/admin/news/results/{run_id}/{claim_index}` remains a historical artifact lookup with immutable input/provenance. `GET /api/v1/admin/news/collection` supplies server-classified saved articles, global status counts, publishers and literal search/status/publisher pagination; attention excludes ready articles and all retains access to every saved article. Collection reads use news_collection_service/crud/news_collection and typed news_collection contracts. Existing staff dependencies and sanitized 503/404/422 handling apply. No durable review identities or lifecycle writes are added; production release remains pending.

**News fact presentation:** Server summaries prefer source-reported road_segment_raw/local_area_raw over broad raw names, preserving road context. Results expose snapshot captured_at and original article saved_at; article details retain per-run flood_summaries. Derived reading_status/reading_reason explain conservative screening: usable place/evidence, affirmative condition/depth/closure evidence, no forecast/negation/historical flags and no metadata-only/errors. Unknown depth or time alone does not exclude an otherwise reported flood. SQL and Python predicates agree on tested PostgreSQL cases; map uncertainty remains distinct from evidence screening. This is a read policy, not a persisted staff decision. Unknown clocks remain null, formatted in Asia/Manila without publication-time substitution. Models, migrations and stored artifacts are unchanged.

The continued Priority 2 check repaired flood-control program/project text being interpreted as active flood evidence. Shared Taglish extraction excludes policy-only sentences/clauses, preserves genuine explicit flood gauges in mixed-topic reports, and retains source evidence offsets. Body-only location probes reject the constructed administrative story. Metadata-local policy headlines may still arrive as review leads, without extracted flood observations. Thirteen focused cases and 207 combined regressions pass. Both six-feed diagnostics parsed 95 entries with no eligible candidate. A real manually selected Philstar administrative body yielded no qualifying flood observation; the initial approval-review error cleared on one permitted retry without changing approval settings. These changes remain local; live automatically discovered positive matching is unverified.

Saved extraction previews provide staff-only `GET /api/v1/admin/news/candidates/{article_id}/extraction` (3/minute). `NewsSavedExtractionSummary` returns real article ID/URL, stable input fingerprint, `read_only=true`, `extraction_mode=rules_only`, typed claims or a visible error. Missing IDs return 404; unauthenticated/commuter access returns 401/403. Saved/discovered previews share `_extract_article_inputs` in `news_discovery_service.py`. The CLI `--extract-saved --dry-run --limit 50` reads pending evidence through existing CRUD, bounds batches at 200, and exits nonzero on processing/storage failures. Empty work returns `no_candidates`; JSON contains structured results. Missing/errored/oversized bodies never enter extraction, and per-input failures retain later outputs. Previews do not perform HTTP retrieval, audit, ingestion, SQL writes, or evidence/review/public changes. Input identity excludes fetch time and canonicalizes equivalent publication offsets. Durable processing is implemented separately through the approved two-table worker; deployed scheduling is unchanged.

Publication revisions on the same article URL trigger a body refresh even when title/summary are unchanged. Older feed revisions cannot overwrite newer stored evidence. Failed refreshes preserve the last successful body and its original metadata/publication date, while surfacing `article_error`; duplicate provenance cannot relabel that body. The dormant ingestion service treats an errored body as unavailable and rejects public activation even if a cached claim action says `auto_approved`. This is a refresh-safety repair, not production ingestion wiring. Successful pending revisions update the current article row; the approved local worker separately preserves immutable prior/current inputs and handles pending extraction after unchanged feeds. These new paths are not yet deployed.

GDELT requests share a per-process gate with one in-flight query, a 10-second gap, and a 10-minute success cache bounded to 32 query results. Throttling and transient failures return `retry_after_seconds` plus a `Retry-After` header rather than sleeping through a long cooldown or retrying immediately. Cooldowns start at 60 seconds and grow to 15 minutes; a longer provider `Retry-After` is respected. HTTP-200 plain-text throttle notices also enter cooldown. Cached results can remain available during another query's cooldown. State resets on process restart and is not shared across Cloud Run replicas.

GDELT queries override the endpoint client's timeout with 15-second connect / 20-second read budgets, following measured TLS handshakes of 8–11 seconds. With `retrieve_articles=true`, a successful title/phrase lookup without an alternate can additionally search Metro Manila place/flood terms within two days of the original publication, bounded to the last 90 days. Provider failures stop further index queries. If no approved index alternate exists, the backend independently probes at most five enabled, verified alternate publisher feeds for originals published within seven days; flood/place matches with publication times within two days become unverified leads. Alternate bodies remain capped at three. Feed leads expose their own `published_at`, with no fabricated index-seen time. No recovered body returns `alternate_article_unavailable`; successful retrieval still requires event review, and provider errors remain visible.

The existing `scripts.run_news_discovery --open-leads` mode runs the lookup without opening a database session. `--trace-network` reports TCP/TLS elapsed times, HTTP status, and public host without headers, credentials, or article bodies. With `--retrieve-articles`, an unavailable body returns exit code 1 even if index links exist. This diagnostic is separate from `--discover` and does not enable scheduled fallback.

`scripts.run_news_discovery --discover --dry-run --extract` exercises collection and the actual hybrid extractor in rules-only mode, without database sessions, external audits, or ingestion calls. It exposes claim actions/places/depth/time/provenance, per-article errors, and explicit no-candidate outcomes; non-dry-run extraction is rejected. The feed parser normalizes known HTML character names outside CDATA into numeric XML references while preserving XML escapes and rejecting DTD/custom entities. Received HTTP status is retained for XML parse failures; HTML/challenge responses are explicit failures. A healthy empty feed is not a network failure. This source change is not deployed.

Priority 2 adds `notices` (source ID, article URL, reason) to staff run responses and CLI discovery output. Five extra article probes per run can resolve location from body-only flood claims; known non-local city/province metadata and future timestamps are excluded. Local leads precede unknown-scope probes, ordered newest first within each feed. Notices are not a durable processing queue. Alternate `event_review.road_updates` records per-city/road previous and alternate observation times, depths, conditions, and a decision. Later observations can propose depth/status changes or clearance; older observations do not replace newer ones. Same-time disagreement, ambiguous states, different segments, and recurrence after clearance require review. Twelve-hour freshness applies to update proposals, and index/publication time is never substituted for observation time. Every proposal retains missing-original-body and unverified-segment/incident evidence. Copied bodies remain flagged, and original evidence/public zones stay untouched by the lookup. A stored body with a refresh error can use the protected fallback; an error-free full body still returns 409.

> **Stack:** Next.js 18 (App Router) | FastAPI | PostgreSQL + PostGIS | Valhalla / OpenRouteService
> This document maps every screen, component file, backend endpoint, and database table in the system.

---

## Table of Contents

1. [Global Layout & Navigation](#1-global-layout--navigation)
2. [Landing Page (/)](#2-landing-page-)
3. [Map Page (/map)](#3-map-page-map)
4. [Community Feed (/feed)](#4-community-feed-feed)
5. [Post Detail (/feed/id)](#5-post-detail-feedid)
6. [Profile Page (/profile)](#6-profile-page-profile)
7. [Auth Pages (/login, /register, /verify)](#7-auth-pages)
8. [About Page (/about)](#8-about-page-about)
9. [Analytics Page (/analytics)](#9-analytics-page-analytics)
10. [Admin Panel (/admin/*)](#10-admin-panel-admin)
11. [Backend API Reference](#11-backend-api-reference)
12. [Database Tables Reference](#12-database-tables-reference)
13. [Entity Relationship Summary](#13-entity-relationship-summary)
14. [Production Cloud Deployment Architecture](#14-production-cloud-deployment-architecture)

---


## 1. Global Layout & Navigation

These files are **always present** regardless of which page you are on.

### Always-Visible Files

| File | Location | What It Does |
|------|----------|--------------|
| `layout.tsx` | `src/app/layout.tsx` | Root HTML shell. Sets fonts (Open Sans, Roboto Mono), imports global CSS and MapLibre CSS, wraps every page in `QueryProvider`, `NavigationWrapper`, and `AppProviders`. |
| `globals.css` | `src/app/globals.css` | Global Tailwind base layer + custom MapLibre control overrides. |
| `NavigationWrapper.tsx` | `src/features/navigation/NavigationWrapper.tsx` | Route guard layer. Redirects unauthenticated users away from protected routes (`/profile`, `/report`, `/feed/create`). Redirects Super Admins to `/admin`. Shows a loading spinner overlay during redirects. |
| `FloatingNav.tsx` | `src/features/navigation/FloatingNav.tsx` | The pill-shaped floating top navigation bar (desktop only). Contains the LANES logo, links to Home / Feed / Map / Profile, an Admin shortcut (for non-Commuter staff), and a Log Out button. Always centered on the full viewport regardless of page. |
| `MobileNav.tsx` | `src/features/navigation/MobileNav.tsx` | Fixed bottom tab bar visible only on mobile. Same links as FloatingNav but icon-only with labels. |
| `OfflineBanner.tsx` | `src/features/offline/OfflineBanner.tsx` | A slim red banner that appears at the very top of the page when the browser loses internet connectivity. |
| `NotificationBell.tsx` | `src/features/notifications/NotificationBell.tsx` | A floating bell icon (bottom-right corner, desktop) with the existing mobile notification interface and unread badge. Shows interaction/post warnings and distinguishable Under Review, Approved and Rejected report SYSTEM notifications. Report references fetch owner-only details via `/reports/me/{report_id}`; missing references surface errors. Read mutation checks recipient ownership. The report-detail portal mounts only after client hydration and when details exist; existing refresh mechanisms remain. |
| `GlobalMap.tsx` | `src/features/map/GlobalMap.tsx` | Mounts the map instance globally via `providers.tsx` so it persists across all page navigations. Manages which map panels are open (Route, Analytics, Save Place, Flood Report, Offline Manager). |
| `providers.tsx` | `src/app/providers.tsx` | Wraps children with `MapContextProvider` and mounts `GlobalMap`. This is why the map is always rendered even when visiting non-map pages. |

---

## 2. Landing Page (/)

**Route file:** `src/app/page.tsx` → renders `<LandingView />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `LandingHero.tsx` | `src/features/landing/LandingHero.tsx` — Full-screen responsive landing hero featuring animated headline typography, system value propositions, quick navigation action buttons to Live Map and Community Feed, and real-time community flood statistics. |
| `LandingView.tsx` | `src/features/landing/LandingView.tsx` — The entire landing page layout. Contains the hero section (headline, CTA buttons), stats row, features grid, how-it-works steps, and footer. Also tracks page visits by calling the `/public/visit` backend endpoint on mount. |
| `HomeStats.tsx` | `src/features/landing/HomeStats.tsx` — Displays today's active map zones created on the UTC date and total visitors. Fetches `/public/stats`, polls every minute and refreshes through existing SSE/flood synchronization. The backend reuses active-zone expiry rules and counts each zone once. Visitor telemetry uses `/public/visits`; failures preserve the independently fetched statistics and show an error. |
| `WeatherWidget.tsx` | `src/features/landing/WeatherWidget.tsx` — A compact weather card showing current temperature, humidity, and a short description for Metro Manila. Fetches from the backend `/weather/current` endpoint. |
| `ForecastChart.tsx` | `src/features/landing/ForecastChart.tsx` — A 7-day rainfall/temperature forecast chart (Recharts line chart) displayed below the weather widget. |
| `FloodGauge.tsx` | `src/features/landing/FloodGauge.tsx` — Split-view interactive MMDA vehicle clearance rules and depth gauge container. Coordinates hover/tap state between the depth table and the SVG human silhouette, with responsive dual-screen layout and mobile auto-scroll. |
| `FloodGaugeTable.tsx` | `src/features/landing/FloodGaugeTable.tsx` — Interactive MMDA flood classification table with 8 canonical depth tiers (`gutter`..`neck`), severity indicators, dual-unit measurements (`inches` and `meters`), and animated expandable vehicle accessibility badges (`PATV`, `NPLV`, `NPATV`). |
| `FloodGaugeSilhouette.tsx` | `src/features/landing/FloodGaugeSilhouette.tsx` — Gender-neutral inline SVG human silhouette calibrated to 165 cm (5'5") reference height according to DOST-FNRI adult standards. Dynamically animates rising water levels via Framer Motion springs, vertical centimeter ruler ticks, water surface line, and depth measurement bubbles. |
| `FloodLegend.tsx` | `src/features/landing/FloodLegend.tsx` — A lightweight 4-card fallback legend card explaining flood severity colors (Low / Medium / High / Extreme) with MMDA vehicle clearance thresholds. |

### Hidden Until Interaction

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `WeatherInsightsModal.tsx` | `src/features/landing/WeatherInsightsModal.tsx` — Click the **"See Full Forecast"** button on the weather widget | Full-screen modal with detailed hourly and 7-day weather forecast, rain probability bar charts, wind speed data, and AI-generated commute recommendations powered by OpenRouter (`/weather/insights`). Calls backend directly via `NEXT_PUBLIC_API_URL`. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/public/visit` | Increments the visitor counter in the DB |
| `GET /api/v1/public/stats` | Returns total reports, verified zones, visitor count |
| `GET /api/v1/weather/current` | Current weather for Metro Manila |
| `GET /api/v1/weather/forecast` | 7-day weather forecast data |
| `GET /api/v1/weather/insights` | AI-generated commuter flood risk insights & weather advisory via OpenRouter |

---

## 3. Map Page (/map)

**Route file:** `src/app/map/page.tsx` → renders `<MapPage />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `MapCanvas.tsx` | `src/features/map/MapCanvas.tsx` — The full-screen MapLibre GL map canvas. Renders 3D terrain, Pasig city boundary, active flood avoidance zones (color-coded polygons), user location dot, alternative route polylines, saved places, and center-anchored pulsing red focus markers. Features resilient `map.getStyle()` layer mounting, `style.load` re-render listeners, auto camera `fitBounds` framing, container resize observer alignment for sidebar offsets, and parses `?lat=&lng=&zoom=` for smooth camera fly-to. |
| `useNoahHazardLayer.ts` | `src/features/map/hooks/useNoahHazardLayer.ts` — Displays one Metro Manila UP NOAH rainfall scenario as a transparent, terrain-draped map image beneath labels and operational zones. The source images are generated by `backend/scripts/export_noah_hazard_overlay.py` from the local 5-, 25-, and 100-year archives; they are display assets, not spatial analysis inputs. The layer reloads after map style changes, and failed image loads raise a toast. On `/map`, the selector appears above Saved Places on desktop or in a short drawer from the mobile `+` menu, only in 3D. No scenario is selected on entry to 3D; returning to 2D clears the display. The legend says the colors show modeled hazard, not live flooding. |
| `BaseMap.tsx` | `src/shared/ui/map/BaseMap.tsx` — Low-level MapLibre wrapper that owns one WebGL map instance, resize observation, and `onMapInit`/`onMapLoad` callbacks. It begins with MapTiler when configured, treats the first rendered frame after `style.load` as usable, and falls back to a LANES-identified OSM raster style only on a MapTiler resource error or exhausted 1.5-second budget. It retries MapTiler on reconnect/backoff. `style.load` preserves LANES-owned layers after each style replacement. A compact viewport-anchored status remains clear of the desktop floating navigation and wraps on smaller screens; document-level connection hints and production PWA caching accelerate MapTiler repeat visits. |
| `RoutePanel.tsx` | `src/features/routing/RoutePanel.tsx` — The left sidebar on desktop (collapsible on mobile). Contains the travel profile selector (including **Bike/Motorcycle**), start/destination inputs with focus guards and smart two-click "Choose on Map" advance, authenticated saved places chips with Start/End-preserving recalculation, and up to four navigable route cards categorized as Fastest, Safest, Balanced, and Alternative. Cards render route-specific flood exposure; a rejected fastest baseline is explanation-only, never selectable. |
| `FloodReportPanel.tsx` | `src/features/hazards/FloodReportPanel.tsx` — The responsive incident reporting panel (opens from FAB or top CTA). Step one accepts raw Start/End selections, then submits the verified road-only line or dual-carriageway coverage returned by the shared preview; it never persists a raw sidewalk-to-road connector. When **Share in Community Feed** is checked, a public Community Post is created immediately, including while the report is pending; pending posts show Awaiting review, while map-zone visibility follows the separate approval workflow. The photo/video picker uses a direct native input and copies selected files before resetting it, so attachment chips remain visible on mobile and desktop; submission errors surface in the panel, and failed uploads prevent report creation. Account-private drafts restore only when an active report has a selected road endpoint plus severity, survey data, description, or media; queued reports remain recoverable. UI-only toggles, wizard state, survey visibility, and typed-but-unselected locations never restore a draft. Severity tiles are unselected by default and toggle off when reselected; opt-in two-way coverage is unchecked by default. The compact **Clear** dialog offers neutral **Clear all** (removes previews, queued drafts, media, and the persisted account draft) plus rightmost red **Clear this page** (preserves work on the other page). `useFloodMapPreview.ts` renders each validated carriageway in its own MapLibre source/layer so close parallel geometry remains visible through a style reload. |
| `OfflineManager.tsx` | `src/features/offline/OfflineManager.tsx` — The "Offline Routing — Ready for offline use" status indicator at the bottom of the RoutePanel. Shows whether the offline tile cache and Valhalla routing data are downloaded and ready. |
| `MapPickerMobileOverlay.tsx` | `src/features/map/MapPickerMobileOverlay.tsx` — A translucent overlay with a centered crosshair that appears on mobile when the user taps a location input, letting them drag the map to pin a point. |
| `useFloodMapPreview.ts` | `src/features/map/hooks/useFloodMapPreview.ts` — A shared custom hook for Start/End marker management and the bidirectional orange-dashed route preview. It renders only final snapped geometry returned by server verification, then positions the visible pins at that road geometry's endpoints. While verification is pending, the selected pins remain without a misleading straight connector. |
| `usePendingReportsLayer.ts` | `src/features/map/hooks/usePendingReportsLayer.ts` — Renders pending public reports as their existing transparent, severity-colored road aura at street-level zoom. Its endpoints and turns are intentionally rounded, matching Active Zone and public-preview road coverage. |
| `AdminFloodMapInteraction.tsx` | `src/features/admin/components/AdminFloodMapInteraction.tsx` — Admin `/admin/map` bridge between MapLibre and `MapContext`; owns Create Zone map clicks, crosshair cursor state, Start-to-End progression, and the shared preview lifecycle. |

### Hidden Until Interaction (Map Panels)

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `SavePlacePanel.tsx` | `src/features/places/SavePlacePanel.tsx` — Click the ❤️ (heart) icon in the right floating controls | A panel for saving a custom named location (Home, Work, School, etc.) with an icon picker and address field. Saves to the backend. |
| `AnalyticsPanel.tsx` | `src/features/analytics/AnalyticsPanel.tsx` — Click the 📊 (chart) icon in the right floating controls, or select **View Flood Analytics** on the landing page | A floating panel showing flood report analytics: active zone count, severity breakdown, and recent activity feed. The landing action opens `/map?panel=analytics`; `MapContext` consumes this signal and opens Flood Insights on arrival. |
| `LocationAutocomplete.tsx` | `src/shared/ui/LocationAutocomplete.tsx` — Typing in the Start or Destination input inside RoutePanel | A dropdown of geocoded place name suggestions powered by Nominatim via the backend. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/reports/zones` | Fetches all active flood avoidance zone polygons to render on the map |
| `POST /api/v1/reports/` | Submits a new flood report from the FloodReportPanel form |
| `POST /api/v1/reports/preview-bidirectional` | Builds an authoritative road preview from raw Start/End anchors. Valid routes retain only their Valhalla-snapped road vertices; the raw selections are input anchors and never become returned or saved connector geometry. Edge shape indexes split mixed road/topology runs before carriageway validation; a map-matched counterpart is trimmed to its longest genuinely parallel component. A short graph-mapped Y merge may be retained only when it connects the matching original-road endpoint, while cross-street or detached junction connectors cannot enter coverage. A verified opposite line therefore applies only to its matching run. Returns the original line, an optional graph-validated opposite carriageway, combined coverage geometry, road classification, validation status, and user-facing explanation. The `/routes/preview-bidirectional` controller remains the canonical implementation. |
| `POST /api/v1/reports/route` (also `/api/v1/routes` and `/api/v1/routes/route`) | Loads authoritative active PostGIS zones once, obtains both fastest and shortest Valhalla or ORS candidates with hard/cautious avoidance, evaluates each actual geometry under one server-side policy, removes ineligible paths, and returns up to four distinct categorized routes plus an optional non-selectable blocked-baseline explanation. Walking uses pedestrian graph access and has no vehicle heading constraint. The provider may return fewer than four distinct legal routes. |
| `GET /api/v1/geocode/autocomplete?q=...` | Returns place name suggestions for location inputs |
| `GET /api/v1/geocode/reverse?lat=&lon=` | Converts a map tap coordinate to a human-readable address |
| `POST /api/v1/users/me/saved-places` | Saves a bookmarked location |
| `GET /api/v1/users/me/saved-places` | Loads saved places to show as quick-access shortcuts in RoutePanel |

---

## 4. Community Feed (/feed)

**October 14 immediate-sharing repair (local):** `/reports` saves an opted-in CommunityPost together with the report and owner notification. Community Feed and public post detail expose explicitly shared pending/approved reports immediately; `PostItem.tsx` labels pending cards Awaiting review on desktop/mobile. Map-zone eligibility continues to use the existing approval workflow. Private, rejected, archived, hidden and deleted content remains excluded, and Active/Resolved filters still require the persisted zone/event lifecycle. `FloodReportPanel.tsx` refreshes Feed/My Posts caches after submission. Share failures roll back the submission and reach the existing error toast. No models, migrations or dependencies changed. [Bug and verification](bug-log.md#resolved-locally-flood-report-community-sharing-waited-for-map-approval). [@roicambe](https://github.com/roicambe) (Roi Cambe).

**October 11 local filtering update:** The existing feed now defaults to newest publication and All Time. Compact `components/CommunityFeedFilters.tsx` controls add oldest/newest, UTC Today/24-hour/3-day/7-day windows, public approved active/ended report status, four existing severity values and strict optional 1/3/5/10 km Nearby radii. `community_feed_service.py` preserves profile/saved-place fallback and auto-only 5-to-15 km expansion; `crud/feed.py` applies public visibility and all filters before stable timestamp/ID sorting, totals and pagination. URL/query keys preserve filters and page across refresh/tabs/SSE/polling; changing filters resets the page. My Posts retains owner access to unpublished content; other readers cannot retrieve linked non-public reports. No models, migrations or dependencies changed. [Acceptance](../evaluations/community-feed-filters-20261011.md). Jace H. Bellen (Git author Jace; jace-branch), with Codex.

**Route file:** `src/app/feed/page.tsx` → renders `<FeedPage />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `FeedPage.tsx` | `src/features/feed/FeedPage.tsx` — The main three-column feed layout. Center column shows the continuous scrollable list of standalone `PostItem` cards (`useInfiniteQuery` infinite stream across desktop and mobile without traditional numbered pagination) separated by clean whitespace (`space-y-3 sm:space-y-4`) with responsive mobile edge margins (`px-3 sm:px-0 pt-3 sm:pt-4`), composer placeholder (`"What's happening?"` on mobile vs `"What's happening in your area?"` on desktop), continuous sentinel auto-fetching with fallback "Load more posts" button, and standalone loading/empty cards. Left and right sidebars are pinned on desktop. Navigation Feed button reloads and smoothly returns to the top of the feed. |
| `FeedLayout` | `src/app/feed/layout.tsx` — Full-width shell with a 24-pixel outer gutter from 1280 pixels and 16 pixels on smaller non-mobile screens. Navigation sits near the left edge; a responsive grid gives the feed its own centered column capped at 720 pixels and reserves 376 pixels for the large-screen updates panel. Local preview verified; production remains on rollout 004. |
| `LeftSidebar.tsx` | `src/features/feed/LeftSidebar.tsx` — Desktop navigation, shared recent Trending Hotspots, saved places and emergency hotlines. Width is 280 pixels from 1280 pixels and 256 pixels on tablets. The same hotspot component appears in the existing mobile navigation drawer in `FeedPage.tsx`. |
| `RightSidebar.tsx` | `src/features/feed/RightSidebar.tsx` — 376-pixel right panel with 16-pixel side padding (344-pixel cards), from the 1280-pixel breakpoint, with Current Weather, API-backed Local Updates and Top Reporters. Its thin scrollbar is transparent until hover/focus; the labeled panel accepts keyboard focus and contains wheel scrolling. Below 1280 pixels, Local Updates is available above the feed composer through the shared expandable card. |
| `LocalUpdates.tsx` | `src/features/news/LocalUpdates.tsx` — Shared recent Metro Manila commuter/flood-news list with publisher, publication date and original article link; loading/empty/retry/offline/cache states, foreground minute refresh and manual refresh. Uses `localNewsApi.ts` → public `GET /api/v1/news/local-updates`. |
| `PostItem.tsx` | `src/features/feed/PostItem.tsx` | An independent, standalone card in the feed (`bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100`). Shows author avatar/name/role, post text, attached media carousel, responsive flood severity badge (compact on mobile, detailed on desktop), standalone `ArrowBigUp`/`ArrowBigDown` voting buttons with active fills, comment count, and responsive single-row action bar (compact map/share labels on iPhone SE/12). Provides a dropdown menu with soft-deletion support: author self-deletion prompts a standard confirmation dialog, while staff/admin removal triggers an **Administrative Post Removal** modal prompting for violation category and notes. Dispatches an in-app `SYSTEM` notification to the post author explaining the decision, logs an `ADMIN_DELETE_POST` audit record, and updates the feed via SSE. Its interactive location badge and flood-report **View on Map** action focus the road-length midpoint of the saved report geometry; paired carriageways focus their shared center. |
| `EmergencyHotlinesCard.tsx` | `src/features/feed/components/EmergencyHotlinesCard.tsx` — API-backed priority emergency contacts with expandable numbers, direct `tel:` links, loading/unavailable states, and a full-directory trigger. Rendered in the feed sidebar layout. |

`components/TrendingHotspots.tsx` shares `feedApi.getTrendingHotspots` and React Query key `["feed", "hotspots"]` across desktop/mobile. It refreshes every 60 seconds, on window focus when stale, and on existing feed mutation invalidations. It displays post counts, map links and a community-activity caption showing the backend-selected 24-hour or 48-hour window with results. The server widens to 48 hours only when the 24-hour result is empty, keeps the same contributor/privacy/recency rules, and returns an honest 48-hour empty state when neither window qualifies. Loading uses the same two gray skeleton bars as Saved Places, with screen-reader status and reduced-motion support; empty content uses the same muted text/padding. Compact rows use circular location icons and ellipsis for long labels; the full location/count remains in the accessible link text and title. Failures show a visible error and blue sidebar-style retry action. One shared component keeps desktop/mobile states consistent. [Final acceptance](../evaluations/community-trending-hotspots-20261007.md).

### Hidden Until Interaction

**Local Updates live status (October 11, 12:33 PM):** API revision `lanes-api-build-86a78939-ca6d-4bce-9d18-db533a8e1c23` serves 100% traffic; API and both jobs use commit `429dd19`. Initial commuter frontend rollout `build-2026-10-11-002` uses that commit; the first sidebar rollout `build-2026-10-11-003` is verified at six live widths, and current rollout `build-2026-10-11-004` from `37f59e1` delivers the wider 376-pixel panel and 344-pixel cards, verified live on desktop/tablet/mobile. Actual live desktop/mobile return HTTP 200 and show five weather/traffic/service stories with publisher/date/source links. The successful root Cloud Build exercises the migration, both worker deployments and exact build-revision promotion. [Live verification](../evaluations/community-local-updates-20261011.md#commuter-news-live-release--october-11-1210-pm-pht).

**Local Updates data:** `api/v1/endpoints/local_news.py` → `services/local_news_service.py` → `crud/local_news.py`, with unchanged public DTOs in `schemas/local_news.py`. The latest five eligible articles (limit 1–10) come from at most 200 candidates published within seven days. `local_news_relevance.py` checks current body sentences for supported Metro Manila commuter topics or reuses the strict flood observation screen. Publisher datelines/weather-office locations alone do not establish impact. The existing scheduled collector saves non-flood commuter bodies in `news_articles` with `review_state="local_update"`; they remain outside extraction and flood attention. Actual flood evidence can promote that state to pending without resetting staff rejection/suppression. Additional non-flood retrieval is capped at 14 per run/four per feed. GMA has five official feeds; source IDs, trust settings and schedules are unchanged. Public output remains metadata only. [Verification](../evaluations/community-local-updates-20261011.md#commuter-news-coverage--october-11-noon-pht).

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `CreatePostModal.tsx` | `src/features/feed/CreatePostModal.tsx` — Click **"Create Post"** or the **"+"** floating button | Full-screen modal with rich text area, drag-and-drop image & video upload (up to 100MB per file with explicit size validation toasts), address autocomplete or map crosshair location picking, coordinate persistence (`location_lat`, `location_lng`), and draft auto-saving that persists across auth redirects. Submits multipart payloads to `POST /api/v1/posts`. |
| `EmergencyDirectoryModal.tsx` | `src/features/feed/components/EmergencyDirectoryModal.tsx` — Click **"View All Hotlines"** | Lazily loaded national, Pasig city, and Pasig barangay hotline directory with tabbed sections, search, and phone links. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/feed/hotspots?limit=3` | Public recent place activity, server-ranked by distinct contributors and recency; limit 1–10, default 24-hour window with a bounded 48-hour fallback only when no place qualifies; `window_hours` reports the selected window even for empty results. Thin feed endpoint delegates to `trending_hotspots_service.py` and the PostGIS aggregation in `crud/trending_hotspots.py`. |
| `GET /api/v1/feed?tab=&sort=&date_range=&flood_status=&severity=&radius=&skip=&limit=` | Public community posts filtered before stable ordering/pagination; defaults newest and All Time. See [filter contract](../evaluations/community-feed-filters-20261011.md#behavior-and-api-contract). |
| `POST /api/v1/feed/posts` | Create a new community post |
| `DELETE /api/v1/posts/{id}` | Soft-deletes a post; supports optional `CommunityPostDeletePayload(reason, details)` when deleted by staff to deliver author notification and audit log |
| `POST /api/v1/feed/posts/{id}/interact` | Upvote or downvote a post |
| `PATCH /api/v1/posts/{id}` | Owner-only complete post update; writes an immutable before/after history version |
| `GET /api/v1/posts/{id}/history` | Public chronological edit-history entries for a post |
| `POST /api/v1/posts/{id}/reports` | Authenticated non-author submission of one private open moderation report |
| `GET /api/v1/hotlines/` | Loads cached national emergency hotlines for the sidebar card |
| `GET /api/v1/hotlines/full` | Lazily loads national, Pasig city, and Pasig barangay hotlines for the directory modal |

---

## 5. Post Detail (/feed/[id])

**Route file:** `src/app/feed/[id]/page.tsx` → renders `<PostDetailPage />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `PostDetailPage.tsx` | `src/features/feed/PostDetailPage.tsx` — Full expanded view of a single post. Shows all post content, attached media gallery, linked flood report details with severity badge (if any), and the full threaded comment section. Supports nested replies (up to 2 levels), inline upvote/downvote on each comment, comment pinning (for admins/moderators), and edit/delete for comment authors. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/feed/posts/{id}` | Full post data including flood report linkage |
| `GET /api/v1/comments/{post_id}` | All comments for the post (threaded) |
| `POST /api/v1/comments/{post_id}` | Submit a new top-level comment or reply |
| `PUT /api/v1/comments/{comment_id}` | Edit your own comment |
| `DELETE /api/v1/comments/{comment_id}` | Delete your own comment |
| `POST /api/v1/comments/{comment_id}/interact` | Upvote or downvote a comment |

---

## 6. Profile Page (/profile)

**Route file:** `src/app/profile/page.tsx` → renders `<ProfileView />`
**Requires authentication.** Redirects to `/login` if not logged in.

### Always Visible on Load

| File | What You See |
|------|-------------|
| `ProfileView.tsx` | `src/features/profile/ProfileView.tsx` — The full profile page split into tabs: **Personal Info** (name, contact, birthdate, address form), **Hazard Reports** (submitted user reports with severity and approval status), **Community Posts** (user's authored community feed posts rendered as standalone spaced cards with post count indicator badge and unboxed background styling), and **Settings** (instant optimistic privacy toggles for profile visibility, full name display, hide profile picture, secure password change with email OTP verification, and account Danger Zone for self-deletion with 30-day grace period). Includes an interactive avatar header with click-to-preview high-resolution modal, Cloudinary photo upload with loading spinner, and remove picture actions. |
| `PasswordOtpModal.tsx` | `src/features/profile/components/PasswordOtpModal.tsx` — Reusable security dialog with 6-box zero-click auto-submitting numeric OTP inputs, auto-focus, clipboard paste handling, resend countdown ticker, and inline verification errors for password update authorization. |
| `SavedRoutesList.tsx` | `src/features/profile/SavedRoutesList.tsx` — Sub-component inside ProfileView that lists the user's saved map places with their custom icons and addresses, and a delete button for each. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/users/me` | Load current user's full profile data |
| `PATCH /api/v1/users/me/profile` | Update profile fields and privacy toggles |
| `DELETE /api/v1/users/me` | Self-deactivate account with a 30-day recovery grace period |
| `POST /api/v1/users/me/avatar` | Upload and attach a profile picture to Cloudinary |
| `DELETE /api/v1/users/me/avatar` | Remove the custom profile picture and revert to initial avatar |
| `POST /api/v1/users/me/password/request-otp` | Validate current password and send 6-digit confirmation OTP to email |
| `PUT /api/v1/users/me/password` | Change password (requires current password and verified email OTP code) |
| `POST /api/v1/auth/request-otp` | Send OTP to email for re-verification |
| `POST /api/v1/auth/verify-otp` | Verify an OTP code |
| `GET /api/v1/users/me/places` | Load saved places list |
| `DELETE /api/v1/users/me/places/{id}` | Delete a saved place bookmark |


---

## 7. Auth Pages

### Login Page (/login)

| File | What You See |
|------|-------------|
| `LoginForm.tsx` | `src/features/auth/LoginForm.tsx` — Email + password fields, Google Sign-In button, "Forgot Password?" trigger, and a "Sign Up" redirect link. Displays a green success banner when redirected from registration with `?registered=true`. Prioritizes administrative roles (`Super Admin`, `DRRM Officer`, `Moderator`) to route directly to `/admin/dashboard` upon login while purging commuter session intents. For commuters, routes to `/map` or `/feed?openPostModal=true` if post intent is active. |

### Forgot Password Flow (/login?forgot=true or /forgot-password)

| File | What You See |
|------|-------------|
| `ForgotPasswordForm.tsx` | `src/features/auth/components/ForgotPasswordForm.tsx` — Pixel-consistent 3-step password recovery modal: Step 1 accepts user email and dispatches single-use OTP via Resend with progressive cooldown tiers (1m, 3m, 5m); Step 2 provides 6-box OTP entry with clipboard paste support and countdown timer; Step 3 provides new password entry with `<PasswordStrength>` meter, confirm password validation, and hold-to-view toggle. On submit, resets password and returns user to login. |

### Register Page (/register)

| File | What You See |
|------|-------------|
| `RegisterForm.tsx` | `src/features/auth/components/RegisterForm.tsx` — Multi-step registration wizard with identity-first email verification, OTP confirmation, password/profile entry, and PSGC address selection. Supports Google OAuth Sign-Up with automatic prefill of full name, email, and avatar, allowing citizens to complete only remaining required demographic fields before account activation. On final submit, calls `POST /api/v1/auth/register` (or `POST /api/v1/auth/google` with `mode: "register"`), clears registration drafts, and redirects to login. |

### Verify Page (/verify)

| File | What You See |
|------|-------------|
| OTP input page | Six-digit OTP code input. Calls `POST /api/v1/auth/verify-otp`. On success, the account becomes active and the user is redirected to `/map`. A "Resend Code" button calls `POST /api/v1/auth/request-otp`. |

### Backend Calls

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/auth/login` | Authenticates and returns a JWT access token |
| `POST /api/v1/auth/google` | Authenticates or registers users using verified Google OAuth ID tokens |
| `POST /api/v1/auth/register` | Creates a new user account and sends OTP via email |
| `POST /api/v1/auth/verify-otp` | Marks the account as active after OTP verification |
| `POST /api/v1/auth/request-otp` | Resend a new OTP to the email |
| `POST /api/v1/auth/forgot-password/request-otp` | Initiates self-service password recovery by sending a single-use OTP via Resend |
| `POST /api/v1/auth/forgot-password/verify-otp` | Verifies recovery OTP and returns a signed 15-minute `password_reset` JWT |
| `POST /api/v1/auth/forgot-password/reset` | Validates `password_reset` JWT and commits updated password hash |
| `POST /api/v1/auth/logout` | Invalidates the current JWT server-side |

---

## 8. About Page (/about)

**Route file:** `src/app/about/page.tsx`

Informational page describing the LANES project mission, authors, adviser, and system architecture. Features official communication channels and an interactive contact inquiry form.

### Always Visible on Load

| File | What You See |
|------|-------------|
| `ContactSection.tsx` | `src/features/about/ContactSection.tsx` — Direct contact card displaying official communication channels (`lanes@navlanes.live` with backup `navlanes.live@gmail.com`) with one-click copy support, and an interactive message inquiry form (Name, Email, Subject, Message) connected to Resend with client feedback states. |

### Backend Calls

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/public/contact` | Submits a contact inquiry with rate limiting (`5/min`) and dispatches transactional emails via Resend (`send_contact_email_async`) with direct reply-to headers |

---

## 9. Analytics Page (/analytics)

**Route file:** `src/app/analytics/page.tsx`

A public-facing data visualization dashboard. Shows flood report trends over time using Recharts charts. On this page, the map canvas switches to a read-only overview mode and the RoutePanel is hidden.

### Backend Calls

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/analytics/reports-over-time` | Time-series count of flood reports by day/week |
| `GET /api/v1/analytics/severity-distribution` | Count of reports grouped by severity level |
| `GET /api/v1/analytics/top-barangays` | The most frequently reported barangays |

---

## 10. Admin Panel (/admin/*)

**Requires authentication + a non-Commuter role.** All admin pages are wrapped in `AdminLayout.tsx` which renders the sidebar navigation and persistently mounts the Spatial Operations Live Map in the background to prevent map reloads during tab switches.

### Sub-pages

| Route | File | What It Does |
|-------|------|-------------|
| `/admin` | `AdminDashboard.tsx` | Entry landing — shows role-based nav links and a summary stats row (total users, reports, active zones). |
| `/admin/news` | `src/features/news/NewsIntelligencePage.tsx` | One server-filtered Flood Locations list with specific segment/intersection cards; Info has Flood Details / Source Article. Collection status opens a shared responsive drawer for failed/empty/questionable and all saved articles. More details retains immutable processing history. Newest recorded runs supply current cards; publication/save/flood clocks remain separate. Developer desktop/mobile acceptance pending; Sources & feeds monitoring is implemented, while public news publication remains unfinished. |
| `/admin/dashboard` | `DashboardPage.tsx` | Responsive overview cards for pending reports, active detours, today’s approvals, today’s Flood Report rejections, accounts, and privacy-preserving daily unique visitors. Features a unified 3-column bento layout organizing the 30-day visitor trend, reports over time, and severity breakdown in Row 1, with Top 5 Most Flooded Barangays, System Health Check, and Quick Administration Tasks aligned beside each other in Row 2. The rejection action opens the Flood Report Moderation workspace with rejected cases selected. |
| `/admin/map` | `LiveMapPage.tsx` | Full-screen admin map & spatial operations view (persistently mounted in `AdminLayout`). Pane 1 contains `PendingReportsPanel` and `ActiveZonesPanel`; Pane 2 shows one of Create Zone, Review Merge, or amber Edit Zone at a time. Pending Reports and Active Zones keep independent current selections. Returning to a tab flies to that tab's selected report or zone only; toggling the selected card or map feature off clears its selection and prevents a later tab switch from moving the map. Create and Edit are separate resumable sessions: the blue Create Zone bookmark retains its account-private draft, while the amber Edit Zone bookmark retains its selected zone and per-admin edit draft; neither replaces or discards the other. Create Zone is always the first desktop handle. Merge and Edit appear only after being opened and are arranged most-recent-first directly below it; switching keeps their component state and scroll position, while explicit Close removes the matching workspace rather than leaving a collapsed handle. The Edit close control is available on desktop and mobile and retains its discard confirmation. Review Merge remains independently resumable. On mobile, Active Zones exposes Create Zone and the shared drawer header can switch to the other available workspace. Normal report focus is neutral. **Review Merge Suggestions** starts a persistent merge session with explicit candidate checkboxes, in-card match evidence, a field comparison matrix, selected-only conflicts, reusable road/Terra Draw editing, confirmation, and primary/candidate/proposed map previews. `zoneDraftStorage.ts` restores Create Zone's active workspace and editable queued drafts. Edit Zone restores only a dirty per-admin draft after fetching the current zone; unchanged and legacy baseline copies are removed silently. It can replace a validated road centreline or reopen the final saved area polygon for Terra Draw vertex editing. A road update stores the new source line and regenerated 25-metre operational buffer; an area update stores the exact polygon and clears obsolete source geometry. It also includes `ReportDetailsModal`, the 400ms `FloodZonePopup` hover engine, and one shared `OfficialZoneDrawer` implementation with `GeometryModeSelector`, `RoadSegmentPicker`, `DraftZoneCart`, five aligned form sections, and Cloudinary media upload. |
| `/admin/users` | `UsersPage.tsx` | Searchable table of all registered users. Admin can filter by role, view trust scores, activate or deactivate accounts, and reassign roles. |
| `/admin/roles` | `RolesPage.tsx` | Role management. Create new roles with a granular permission matrix (view / manage / full per module). Edit or delete existing roles. |
| `/admin/data` | `DataManagementPage.tsx` | Data import/export tools. Upload flood report CSVs, export reports as JSON or CSV, and inspect raw PostGIS geometry for any record. |
| `/admin/audit` | `AuditTrailPage.tsx` | Chronological log of all admin actions — who did what, when, and on which record. Filterable by admin user, action type, and date range. |
| `/admin/moderation` | `ModerationCenterPage.tsx`, `components/FloodModerationQueue.tsx` | Staff-only tabbed Community Post and Flood Report tracking using the shared underline `Tabs` and shared `Pagination` components. Both Community Post Reports and Flood Report Moderation queues support clean 10-item page slicing, responsive dual-screen controls (mobile Previous/Next; desktop numbered with first/last jump), smooth scroll-to-top on page change, and filter/tab page resets. The Dashboard may deep-link to the Flood tab with rejected cases preselected. Flood cases show their outcome/context and filters, then provide a single **Review on Map** handoff; no spatial approval/rejection controls are duplicated here. The responsive action area remains clear of the mobile bottom navigation. |
| `/admin/flood-history` | `flood-history/page.tsx`, `features/flood-history/*` | Admin-only Flood History & Analytics has a server-calculated distinct-event planning dashboard plus a separate historical `BaseMap` source/layer set for Flood Event Records. Its responsive Recharts visuals include a verified-event/approved-report combination trend, severity doughnut, duration columns, recurrence rankings, and an accessible Philippine-time verification heatmap. The Overview clarifies distinct-event, ended-event, duration, recurrence, road, evidence, and timing definitions. Compact shared `Card`, `Button`, `Input`, `Select`, `DatePicker`, and `Tabs` components keep its filters, cards, controls, desktop/mobile map-list presentation, and blue-led non-severity graphs visually consistent with the Admin Dashboard. A protected record uses Overview, Official History, and Reports tabs: the first covers lifecycle, peak and affected places; the second covers official zones and timeline; and Reports is a responsive master-detail evidence review. On desktop, the report list remains visible while the existing shared report/evidence view slides into the right panel; on mobile, that shared view replaces the list with a Back to reports action. Event map actions frame the historical event; saved-zone actions only frame their existing footprint without changing selection or styling; source-report actions retain a separate evidence overlay on the same read-only historical map; they never navigate to live Spatial Operations or affect routing. Protected filters drive recurrence, roads, peak severity, official duration, and time-series analytics; authorized users can download filtered planning records or aggregate analytics as CSV/JSON without reporter identity, raw evidence, report geometry, or media. |
| `/admin/settings` | `SystemSettingsPage.tsx` | Versioned operational settings: staff road buffer, evidence expiry, citizen eligibility, news stages/publishers, saved stage health and read-only permission mode. |
| `/admin/archive` | `ArchivePage.tsx` | Centralized Archive Center with 30-day auto-purge retention lifecycle across three primary tabs: **Archived Users** (soft-deleted commuter accounts with 30-day countdown badge, restore action, and typed `"DELETE"` permanent purge), **Spatial Data** (dual sub-tabs for soft-deleted/rejected Flood Reports and deactivated/expired Avoidance Zones with detail inspection, Attached Media & Evidence photo/video gallery, reactivation, and typed `"DELETE"` permanent deletion), and **Archived Posts** (dual sub-tabs for Community Feed posts soft-deleted by authors/admins and posts hidden by moderators with full media/author inspection, feed restoration, and typed `"DELETE"` permanent deletion). Includes on-demand manual trigger to purge expired records. |
| `/admin/profile` | `AdminProfilePage.tsx` | Native Admin Profile hub matching public profile design. Super Admins, DRRM Officers, and Moderators can edit personal details, phone number, birthdate, and PSGC address, change account cover banner color, upload or remove avatar images, toggle privacy preferences ("Display Full Name", "Hide Profile Picture"), and securely change account passwords with live `<PasswordStrength>` validation and email OTP verification via `PasswordOtpModal`. Linked from the user profile card in the `AdminSidebar.tsx` footer. |

> **Flood Event lifecycle update (Phase 33):** `/admin/map` remains the only operational moderation workspace. `RejectFloodReportModal` requires a structured reason, keeps rejected evidence out of Archive Center, and notifies the submitting user through the existing bell without disclosing internal notes. Approving/merging a report or directly creating an official zone creates or links a verified Flood Event; server services calculate event metrics, record readable zone/severity timeline entries, and end the event when its final live zone ends. **Known Cloud SQL integrity issue ([BUG-055]):** active Events #6 and #8 currently retain timeline snapshots for missing reports/zones, so their historical detail correctly returns zero live links. Remediation is pending explicit schema/data approval; history remains read-only and does not reconstruct evidence in the UI.

### Backend Calls (Admin)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/admin/reports` | Paginated admin view of all reports with filters |
| `PUT /api/v1/admin/reports/{id}/approve` | Approve report, auto-generates flood avoidance zone polygon |
| `POST /api/v1/admin/reports/{id}/reject` | Reject report with a structured reason, moderation outcome, trust update, and reporter notification |
| `GET /api/v1/admin/flood-events` | Admin-only ordered list of verified Flood Events for the Flood History & Analytics entry surface |
| `GET /api/v1/admin/flood-events/history` | Admin-only filtered historical event records, including isolated historic zone geometry, locations, and server-calculated evidence metrics |
| `GET /api/v1/admin/flood-events/analytics` | Admin-only, filter-aware city-planning aggregation that counts distinct Flood Events once and returns recurrence, roads, peak severity, official-duration, time-series, and separate approved-report confidence metrics |
| `GET /api/v1/admin/flood-events/export` | Admin-only CSV/JSON export of filtered planning event records or aggregate analytics; default exports omit reporter identity, raw text, exact report geometry, and media |
| `GET /api/v1/admin/flood-events/{id}/history-detail` | Admin-only full historical Flood Event detail: event metrics, locations, event-owned zones, linked original reports, and readable incident timeline |
| `GET /api/v1/admin/flood-events/{id}/summary` | Admin-only server-calculated event duration, evidence, zone, location, peak, and status metrics |
| `GET /api/v1/admin/dashboard/visitors` | Admin-only 30-day first-party unique-visitor trend and current/lifetime aggregate totals; never returns visitor identifiers |
| `GET /api/v1/public/stats` | Public landing statistics, including the deduplicated first-party visitor total |
| `POST /api/v1/public/visits` | Records one visible browser’s daily visit from an opaque UUID after server-side HMAC hashing; known bots are rejected and no IP or fingerprint is stored |
| `POST /api/v1/admin/zones` | Create official flood avoidance zone (multipart `FormData` with JSON `body` and `media` files) |
| `GET /api/v1/admin/zones/{id}` | Retrieve the current shared zone before resuming an account-private Edit Zone draft |
| `PUT /api/v1/admin/zones/{id}` | Update existing avoidance zone metadata, depth, severity, passability, and notes |
| `POST /api/v1/admin/zones/{id}/media` | Append authenticated administrator evidence uploads to an existing zone |
| `GET /api/v1/admin/reports/merge-candidates` | Multi-factor spatial candidate scoring for report merging |
| `POST /api/v1/admin/reports/merge` | Multi-report merge into a new or existing avoidance zone |
| `GET /api/v1/admin/moderation/reports` | Staff-only list of open (or resolved) Community Post moderation cases, grouped by post |
| `POST /api/v1/admin/moderation/posts/{id}/resolve` | Atomically dismiss, warn, or soft-hide a Community Post and resolve all its open reports |
| `GET /api/v1/admin/moderation/flood-reports` | Admin-only Flood Report moderation cases with status, source, date, location, reporter, and rejection-reason filters; provides safe map-focus coordinates |
| `GET /api/v1/admin/reports/detail/{report_id}` | Admin-only full report read for a focused Spatial Operations review, including approved and rejected reports retained in moderation history |
| `GET /api/v1/reports/me/{report_id}` | Authenticated report-owner details for notification references; another user's or deleted report returns 404 |
| `GET /api/v1/admin/users` | All users with role and profile info |
| `PUT /api/v1/admin/users/{id}` | Update user role or active status |
| `POST /api/v1/admin/users/{id}/restore` | Restore a soft-deleted/archived user account and profile |
| `DELETE /api/v1/admin/users/{id}/permanent` | Permanently hard-delete a user account and profile |
| `POST /api/v1/admin/archive/purge-expired` | Manually execute 30-day auto-purge on expired archived users, posts, reports, and zones |
| `GET /api/v1/admin/roles` | All roles with their permission matrices |
| `POST /api/v1/admin/roles` | Create a new role |
| `PUT /api/v1/admin/roles/{id}` | Update role permissions |
| `DELETE /api/v1/admin/roles/{id}` | Delete a role |
| `GET /api/v1/admin/audit` | All audit log entries with filters |
| `GET /api/v1/admin/settings/configuration` | Typed settings/revision/options/runtime; requires `settings=view/full` |
| `PUT /api/v1/admin/settings/configuration` | Atomic revision-guarded save; requires `settings=full` |
| `GET /api/v1/admin/settings` | Compatible legacy rows; internal configuration/runtime keys are omitted |
| `PUT /api/v1/admin/settings` | Retired: returns 410 with reload guidance |
| `GET /api/v1/admin/zones` | All flood avoidance zones with PostGIS geometry |
| `POST /api/v1/admin/zones` | Manually create a new zone polygon |
| `PUT /api/v1/admin/zones/{id}` | Update zone geometry, status, or expiry |
| `DELETE /api/v1/admin/zones/{id}` | Permanently delete a zone |
| `POST /api/v1/admin/reports/{id}/restore` | Restore a genuinely soft-deleted flood report; rejected reports remain a durable moderation outcome |
| `POST /api/v1/users/me/password/request-otp` | Validate current password and dispatch 6-digit confirmation OTP to user email |
| `PUT /api/v1/users/me/password` | Verify current password and email OTP code, and update account password with password complexity validation |

**October 11 moderation handoff:** Flood Report Moderation Info loads the existing full admin report rather than assembling a partial summary object. Spatial Location's View on Map rechecks current status and carries `focus_report_id` with a repeat-navigation token. `/admin/map` independently resolves approved reports to Active Zones through their linked zone/contributor and pending reports to Needs Review; rejected evidence remains inspection-only. The shared detail dialog disables only its redundant View on Map Focus action for this caller. Missing report/zone information surfaces an error. Desktop/mobile use the existing map and detail components. [Publication audit](../evaluations/jace-moderation-feed-publication-20261011.md).

## 11. Backend API Reference

**Base URL:** `http://localhost:8000/api/v1`
**Framework:** FastAPI (Python) with SQLAlchemy 2.x ORM
**Authentication:** JWT Bearer tokens — stored in `localStorage` on the frontend, sent as `Authorization: Bearer <token>` header

### Endpoint File Map

| File | URL Prefix | Who Can Access |
|------|------------|----------------|
| `auth.py` | `/auth` | Public |
| `public.py` | `/public` | Public |
| `weather.py` | `/weather` | Public |
| `users.py` | `/users` | Authenticated users |
| `reports.py` | `/reports` | Authenticated users |
| `feed.py` | `/feed` | Authenticated users |
| `posts.py` | `/posts` | Authenticated users |
| `comments.py` | `/comments` | Authenticated users |
| `notifications.py` | `/notifications` | Authenticated users |
| `analytics.py` | `/analytics` | Public |
| `sse.py` | `/sse` | Authenticated users (EventSource) |
| `sync.py` | `/sync` | Authenticated users (offline support) |
| `hotlines.py` | `/hotlines` | Public |
| `admin.py` | `/admin` | Staff roles only (non-Commuter) |
| `news_alerts.py` | `/news/alerts` | Public safe source-alert list/detail; latest state, read-time expiry and bounded retention; no writes or private notes. |
| `admin_news_publication.py` | `/admin/news/claims` | Active staff reports view/full reads and full-only preview/decision writes; UUID/revision guards and private history. |
| `admin_news.py` | `/admin/news` | Staff-only source probes, feed health, pending candidates, collection, manual submission, and open leads. Saved extraction GET is read-only (3/minute). `GET /candidates/{article_id}/processing` lists the last 20 typed runs; POST enqueues/processes that candidate (3/minute), returns safe 409/503 failures and bounded outcomes. Lease tokens are never exposed. |
| `roles.py` | `/roles` | Staff roles only |
| `data.py` | `/data` | Staff roles only |
| `settings.py` | `/admin/settings` | Authenticated `settings=view/full`; writes require `full` |

### Key Backend Services

| Service | What It Does |
|---------|-------------|
| **Taglish Flood Extraction and Geometry Prototypes** | `taglish_extraction_service.py` uses deterministic rules and the nationwide PSGC reference to extract source-linked places, canonical depth, flood condition, and event time. `nationwide_geometry_service.py` ranks locations and generates preview polygons with provenance; it does not verify the affected road segment or use LiPAD/UP NOAH hazard layers. `article_road_match_service.py` is a separate read-only local-PBF matcher for explicit spans and a splitter for OSM between-intersection road sections; `noah_road_prediction_service.py` ranks supplied sections from article context, place-matched DRRMO support, and modeled NOAH overlap. The C. Raymundo road-only audit remains ambiguous. These research services are not connected to article ingestion or zone creation. `hybrid_extraction_service.py` adds an optional OpenRouter Gemini auditor; an unavailable auditor leaves active claims in the exception path. `NewsAutoIngestionService` reevaluates all approval gates at the public-write boundary, but the present geometry provider cannot satisfy them. calamanCy and Cloud Natural Language are not integrated. The remaining GMA/Inquirer full-article replay is paused; the scheduled collector does not invoke the extraction prototype. |
| **News source-alert lifecycle** | Immutable extraction/evaluation feeds independently audited, identity/policy/time-bound public decisions and safe readers. The deployed `news_pipeline_service.py` connects saved extraction, evaluation, publication/maintenance and `news_footprint_worker_service.py` activation. Exact approved footprints or uniquely grounded OSM/NOAH estimated corridors remain gated by the existing server-owned evidence/geometry/lifecycle contract. Dormant ingestion prototypes are not used; real-current-article acceptance remains unverified. |
| **RSS News Discovery** | Configured approved feeds use bounded RSS/Atom capture, conditional checkpoints and preserved article/input/extraction history. The deployed three-hour Cloud Run job uses `--discover --pipeline --limit 50`, connecting collection to saved extraction, independent auditing, publication/maintenance and gated footprint activation. Staff-triggered GDELT/alternate-body lookups preserve original article identity and do not themselves activate zones. A real current article completing the full public map/routing/lifecycle path and the next scheduled run's memory remain unverified. |
| **Routing Engine Proxy** | Uses Valhalla (primary) or OpenRouteService (secondary) only to generate candidates. The shared FastAPI flood policy evaluates candidate geometry against active `flood_avoidance_zones`, blocks medium exposure for light/Bike-Motorcycle and Red/Extreme exposure for every public profile; Orange/High is a strongly cautioned 40% fallback only for Walking. It ranks up to four distinct legal routes and reports deterministic exposure details. |
| **Zone Deduplication** | When a new flood report is approved near an existing active zone (within a configurable buffer distance), it is linked to that zone instead of creating a new duplicate polygon |
| **Trust Score Engine** | Automatically recalculates a user's `trust_score`, `accuracy_rate`, and report counters in `profiles` whenever one of their reports is approved or rejected |
| **Weather Proxy** | Current/forecast GET endpoints fetch and cache Open-Meteo data, normalize it for presentation and run synchronous provider I/O in FastAPI's thread pool. The separate asynchronous AI insights endpoint uses the configured free OpenRouter model. |
| **SSE Broadcaster & LiveSync** | Process-local event streams signal relevant cache invalidations. The separate `/sync/stream` shares one authoritative DB read/serialization per 15-second cycle per API worker, closes every worker-thread session immediately and retains only the latest snapshot per subscriber. Unchanged data sends keepalives; failed reads preserve offline data and surface unavailable status. Idle/shutdown cleanup releases subscriptions. Client map queries retain a 60-second fallback; dev/LAN URLs bypass the Next.js streaming proxy. |
| **Data Retention & Auto-Purge Service (`retention_service.py`)** | Daily background and on-demand cleanup permanently purge eligible soft-deleted records after 30 days. Periodic cleanup creates/uses/closes its session inside a worker thread so synchronous DB waits do not block the API loop. |
| **Hotline Aggregator** | Fetches and parses national and Pasig emergency contact pages, normalizes phone numbers for `tel:` links, and caches results for one hour |

---

## 12. Database Tables Reference

**Database:** PostgreSQL with PostGIS extension
**ORM:** SQLAlchemy 2.x + GeoAlchemy2 for spatial columns
**Migration tool:** Alembic

---

### News discovery evidence tables (migration `a83c1d4e7b92`)

These three tables were applied to development PostGIS and production Cloud SQL in the September 25 rollout. `news_feed_checkpoints` stores each feed URL, source ID, ETag, Last-Modified value, check/success times, and last error. `news_articles` keeps a unique canonical article URL, publisher source ID, title, excerpt, publication/fetch/seen times, optional public text or retrieval error, content fingerprint, and review state. `news_article_feed_entries` links each article to a source/feed URL/GUID with first/last seen times and optional JSONB metadata; the source, feed URL, and GUID combination is unique. The foreign key cascades only when a stored article is deleted. The current collector path does not create Flood Reports, Flood Events, or map zones.

---

### Durable extraction tables (migration `f29b6c8d104e`, not yet deployed)

`news_article_versions` stores immutable input snapshots keyed by article/hash, protected by an UPDATE-rejection trigger and RESTRICT foreign key. `news_extraction_runs` stores pipeline/mode-keyed typed artifacts, attempts, due times, token-owned leases, safe errors, and lifecycle timestamps. The [database contract](database-design-plan.md) records every field/constraint/index. Apply/rollback/apply and four database checks passed in disposable PostgreSQL/PostGIS. Collector processing is opt-in (`--discover --process`) or independent (`--process-saved`); both bound work at 200. No public report/event/zone writes or external audit calls occur.

### `roles`

Stores permission configurations for different staff types.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `name` | String(50), unique | Role label — e.g., "Commuter", "Moderator", "Super Admin" |
| `permissions` | JSON | Dictionary of module → permission level — e.g., `{"reports": "full", "zones": "view"}` |
| `is_template` | Boolean | Whether this is a built-in system template role |
| `created_at` | DateTime | Timestamp when the role was created |

---

### `users`

Core user accounts — one row per registered person.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `username` | String(50), unique | Public display handle |
| `email` | String(100), unique | Login email address |
| `hashed_password` | String(255) | Bcrypt-hashed password |
| `role_id` | FK → roles.id | The user's assigned role |
| `is_active` | Boolean | Whether the account is enabled (false = suspended or not yet verified) |
| `created_at` | DateTime | When the account was registered |
| `deleted_at` | DateTime, nullable | Soft-delete timestamp (null = account is live) |

---

### `profiles`

Extended personal details and community trust metrics. One-to-one with `users`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id, unique | The linked user account |
| `first_name` | String(100) | First name |
| `last_name` | String(100) | Last name |
| `middle_initial` | String(10), nullable | Middle initial |
| `suffix` | String(20), nullable | Name suffix — e.g., Jr., III |
| `contact_number` | String(20), nullable | Phone number |
| `birthdate` | Date, nullable | Date of birth |
| `avatar_url` | String(255), nullable | URL to the profile picture |
| `hide_profile_picture` | Boolean | Whether to hide avatar and display uppercase initial fallback (default: false) |
| `cover_color` | String(20) | Hex color for the profile page banner (default: `#3B82F6`) |
| `is_public` | Boolean | Whether the profile is visible to other users |
| `display_full_name` | Boolean | Whether to show full name or just username on posts |
| `trust_score` | Integer | Community trust score from 0–100 (default: 50) |
| `reports_submitted` | Integer | Total number of flood reports filed by this user |
| `reports_approved` | Integer | Number of their reports approved by admins |
| `reports_rejected` | Integer | Number of their reports rejected by admins |
| `accuracy_rate` | Float | Calculated as `(reports_approved / reports_submitted) × 100` |
| `updated_at` | DateTime | Last time the profile was updated |

---

### `addresses`

Residential address. One-to-one with `profiles`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `profile_id` | FK → profiles.id, unique | The linked profile |
| `house_number` | String(100), nullable | House or unit number |
| `street` | String(255), nullable | Street name |
| `barangay` | String(100) | Barangay name |
| `city_municipality` | String(100) | City or municipality |
| `province` | String(100) | Province |
| `postal_code` | String(20), nullable | Postal/ZIP code |
| `country` | String(100) | Country name (default: "Philippines") |

---

### `otp_verifications`

Temporary OTP codes for email verification. Records expire after 10 minutes.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `email` | String(100) | Email address the OTP was sent to |
| `otp_code` | String(255) | Bcrypt-hashed 6-digit code (never stored in plain text) |
| `expires_at` | DateTime | When the code expires (typically created_at + 10 minutes) |
| `attempts` | Integer | Number of wrong-guess attempts (lockout after 5) |
| `is_verified` | Boolean | Whether the code was successfully used |
| `created_at` | DateTime | When the OTP was generated |

---

### `flood_reports`

Incoming flood event reports from users or external scraped sources.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id, nullable | Reporter user (null if scraped from social media or seeded) |
| `raw_text` | String | Original report text, typically in Taglish |
| `source` | Enum | Origin: `twitter`, `facebook`, `direct_user`, or `manual_seeder` |
| `source_url` | String(500), nullable | Original URL if scraped from social media |
| `severity` | Enum | Flood level: `low`, `medium`, `high`, or `extreme` |
| `depth` | String(50), nullable | Estimated flood depth key (`gutter`, `knee`, etc.). Mapped dynamically to MMDA physical measurements (`depth_meters`, `depth_inches`, `depth_formatted`) in API responses without schema alterations |
| `status` | Enum | Moderation state: `pending`, `approved`, or `rejected` |
| `media_urls` | JSONB, nullable | Array of photo/video URLs attached to the report |
| `human_readable_location` | String(255), nullable | Geocoded address string for display purposes |
| `barangay` | String(100), nullable | Extracted barangay name (indexed for fast filtering) |
| `city` | String(100), nullable | Resolved city or municipality name (indexed for fast filtering) |
| `is_public` | Boolean | Whether this report appears in the community feed |
| `zone_id` | FK → flood_avoidance_zones.id, nullable | The avoidance zone this report was merged into (deduplication) |
| `geometry` | PostGIS GEOMETRY (SRID 4326), nullable | Point or LineString coordinates of the flood location |
| `created_at` | DateTime | When the report was submitted |
| `updated_at` | DateTime | Last modification time |
| `deleted_at` | DateTime, nullable | Soft-delete timestamp |
| `approved_at` | DateTime, nullable | Timestamp when an admin approved this report |

---

### `flood_report_locations`

Normalized location name tags extracted by NLP from flood report text. Many-to-one with `flood_reports` (3NF normalization).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `report_id` | FK → flood_reports.id | The parent flood report |
| `location_name` | String(100) | An extracted place name — e.g., "España Blvd", "Barangay 646" |

---

### `flood_report_surveys`

Survey answers submitted alongside a user-filed report. One-to-one with `flood_reports`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `report_id` | FK → flood_reports.id, unique | The parent flood report |
| `passable_vehicles` | String(500), nullable | Free-text answer — what vehicles can still pass? e.g., "motorcycles only" |
| `hidden_hazards` | Enum | Whether the reporter noticed hidden dangers: `yes`, `no`, or `unsure` |

---

### `flood_avoidance_zones`

Spatial polygon buffers generated around approved flood reports or curated directly by DRRMO administrators. Used by the routing engine to reroute traffic around flooded areas.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `name` | String(100), nullable | Descriptive operational name of the avoidance zone |
| `curated_by_admin_id` | FK → users.id, nullable | Admin who manually edited or created this zone (null if auto-generated) |
| `geometry` | PostGIS POLYGON (SRID 4326) | The actual closed polygon boundary of the avoidance area |
| `source_geometry` | PostGIS GEOMETRY, nullable | Original administrator-selected LineString or MultiLineString; used to render the active road core while `geometry` remains the routing buffer |
| `severity_override` | Enum, nullable | Overridden severity level (`low`, `medium`, `high`, `extreme`) |
| `depth_override` | String(50), nullable | Standard visual water depth gauge key (`gutter`, `knee`, etc.). Mapped dynamically to MMDA physical measurements (`depth_meters`, `depth_inches`, `depth_formatted`) in API responses without schema alterations |
| `passable_vehicles_override` | String(500), nullable | Comma-separated list of safe vehicle types |
| `hidden_hazards_override` | String(255), nullable | Presence of submerged dangers: `yes`, `no`, `unsure` |
| `admin_notes` | Text, nullable | Dispatch notes and operational instructions |
| `merge_rationale` | String(1000), nullable | Merge rationale summary |
| `media_urls` | JSONB, nullable | Photographic and video evidence URLs stored in Cloudinary |
| `is_active` | Boolean | Whether this zone is currently applied to route calculations |
| `created_at` | DateTime | When the zone was generated or created |
| `updated_at` | DateTime | Latest shared zone metadata update; used to protect Edit Zone drafts from overwriting a newer server version |
| `expires_at` | DateTime, nullable | Automatic expiry time (null = never expires automatically) |

---

### `saved_places`

Custom bookmarked map locations per user (Home, Work, School, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | The owner of this saved place |
| `name` | String(50) | Custom label — e.g., "Home", "Office", "School" |
| `icon` | String(50) | Icon identifier used for the map pin — e.g., "Home", "Briefcase", "Star" |
| `address` | String(255), nullable | Human-readable address string |
| `latitude` | Float | Latitude coordinate |
| `longitude` | Float | Longitude coordinate |
| `pin_order` | Integer, nullable | Custom order sequence for quick pills |
| `geometry` | PostGIS POINT (SRID 4326) | Spatial point for future proximity search queries |
| `created_at` | DateTime | When the place was bookmarked |

---

### `community_posts`

Posts in the community feed. Can be standalone or linked to a flood report.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | Post author |
| `flood_report_id` | FK → flood_reports.id, nullable | Linked flood report (if this post shares or discusses a report) |
| `content` | Text | Post body text |
| `media_urls` | JSONB, nullable | Array of attached image or video URLs |
| `location_tag` | String(255), nullable | Optional location label displayed on the post |
| `location_lat` | Float, nullable | Latitude coordinate for interactive map view / fly-to |
| `location_lng` | Float, nullable | Longitude coordinate for interactive map view / fly-to |
| `is_pinned` | Boolean | Pinned status flag |
| `pinned_at` | DateTime, nullable | Timestamp of pinning |
| `created_at` | DateTime | Post creation time |
| `updated_at` | DateTime | Last edit time |

### `community_post_edit_history`

Immutable before/after versions for Community Post edits. Each row belongs to one post and its author/editor, has a sequential per-post version number, and preserves content, media URLs, and location values as they existed before and after that edit.

---

### `comments`

Threaded comments on community feed posts.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | Comment author |
| `post_id` | FK → community_posts.id | The post this comment belongs to |
| `content` | String(250) | Comment text (max 250 characters) |
| `parent_id` | FK → comments.id, nullable | Parent comment ID for nested replies (null = top-level comment) |
| `upvotes` | Integer | Aggregated upvote count |
| `downvotes` | Integer | Aggregated downvote count |
| `created_at` | DateTime | When the comment was posted |
| `is_deleted` | Boolean | Whether the comment was soft-deleted (content replaced with "[deleted]") |
| `is_pinned` | Boolean | Whether an admin has pinned this comment to the top |
| `pinned_by` | String(150), nullable | Username of the admin who pinned it |
| `edited_at` | DateTime, nullable | Timestamp of the last edit |

---

### `post_interactions`

Upvote and downvote records for community posts. One record per user per post.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | User who interacted |
| `post_id` | FK → community_posts.id | The target post |
| `interaction_type` | Enum | `upvote` or `downvote` |
| `created_at` | DateTime | When the interaction was made |

---

### `comment_interactions`

Upvote and downvote records for comments. One record per user per comment.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | User who interacted |
| `comment_id` | FK → comments.id | The target comment |
| `interaction_type` | Enum | `upvote` or `downvote` |
| `created_at` | DateTime | When the interaction was made |

---

### `notifications`

In-app notification records pushed to users via SSE.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | The recipient of this notification |
| `type` | Enum | Notification category: `LIKE`, `COMMENT`, or `SYSTEM` |
| `message` | String(255) | Human-readable notification text shown in the dropdown |
| `payload` | JSONB | Extra data for deep-linking — e.g., `{"post_id": 42, "commenter": "juan"}` |
| `is_read` | Boolean | Whether the user has seen/dismissed this notification |
| `created_at` | DateTime | When the notification was created |

---

### `audit_logs`

Immutable trail of all admin actions for accountability and debugging.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `admin_id` | FK → users.id, nullable | Admin who performed the action (null if automated/system action) |
| `action_type` | String(50) | Category of action — e.g., `APPROVE_REPORT`, `UPDATE_ROLE`, `DELETE_USER` |
| `target_table` | String(50) | Which database table was affected — e.g., `flood_reports`, `users` |
| `target_id` | Integer, nullable | Primary key of the specific row that was affected |
| `metadata_json` | JSONB, nullable | Before/after snapshot or additional context data |
| `ip_address` | String(45), nullable | Admin's IP address at the time of action |
| `created_at` | DateTime | Exact timestamp of the action |

---

### `visitor_counts`

Legacy single-row landing counter retained only for historical database compatibility. The application no longer reads or updates it.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Always 1 (this table has exactly one row) |
| `total_visitors` | Integer | Cumulative count of landing page visits since deployment |

---

### `visitor_daily_visits`

First-party analytics rows used to calculate daily and lifetime unique visitors. A row is unique per UTC date and pseudonymous browser hash; it never stores raw browser IDs, IP addresses, fingerprints, or location.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Surrogate identifier |
| `visitor_hash` | String(64), indexed | HMAC-SHA256 of the browser-generated UUID; raw UUID is never persisted |
| `visit_date` | Date, indexed | UTC calendar day, unique with `visitor_hash` |
| `user_id` | FK → users.id, nullable | Optional signed-in account; aggregates collapse its browsers into one account visitor and becomes null if that user is deleted |
| `first_seen_at` / `last_seen_at` | DateTime | UTC activity timestamps for the day |

---

### `system_settings`

Key-value store for runtime-configurable system parameters editable by admins without code changes.

| Column | Type | Description |
|--------|------|-------------|
| `key` | String, PK | Setting identifier — e.g., `flood_zone_expiry_hours`, `min_report_trust_score` |
| `value` | JSONB | The setting value (any JSON type — number, string, array, object) |
| `last_updated_by` | FK → users.id, nullable | Admin who last changed this setting |
| `updated_at` | DateTime | Last update timestamp |

---

## 13. Entity Relationship Summary

```
roles ──< users ──< profiles ──< addresses
                │
                ├──< flood_reports ──< flood_report_locations
                │         │──< flood_report_surveys
                │         └──> flood_avoidance_zones (N reports → 1 zone)
                │
                ├──< community_posts ──< comments ──> (self-join: replies)
                │         │                └──< comment_interactions
                │         └──< post_interactions
                │
                ├──< saved_places
                ├──< notifications
                └──< audit_logs  (as admin actor)

otp_verifications  (standalone, keyed by email)
visitor_counts     (singleton table)
visitor_daily_visits ──> users (optional account attribution)
system_settings    (key-value store)
```

---

## 14. Production Cloud Deployment Architecture

The production environment operates across Google Cloud and Firebase within region `asia-east1` (Taiwan).

### Infrastructure Breakdown

| Component | Service | Configuration File | Role |
| :--- | :--- | :--- | :--- |
| **Frontend** | **Firebase App Hosting** | `frontend/apphosting.yaml`<br>`frontend/firebase.json` | Hosts Next.js SSR / App Router on Node.js 22 runtime. Builds via Google Cloud Build with injected build-time variables (`NEXT_PUBLIC_API_URL` pointing to Cloud Run backend). Production URL: `https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app`. |
| **Backend** | **Google Cloud Run** | `backend/Dockerfile` | Public FastAPI ASGI gateway. Binds to dynamic `$PORT` (8080), handles PostGIS and SSE, and calls private routing providers. Endpoint: `https://lanes-api-557679867071.asia-east1.run.app`. |
| **Online Router** | **Private Cloud Run Valhalla** | `infrastructure/valhalla/` | `lanes-valhalla` serves the Philippines graph with no public invoker. FastAPI supplies an ID token; Valhalla failures retry through ORS and the route response reports `engine_used` and `fallback_used`. |
| **CORS Policy** | **FastAPI CORSMiddleware** | `backend/app/main.py` | Dynamically authorizes local development (`localhost:3000`), production apex (`navlanes.live`), Vercel previews (`*.vercel.app`), and Firebase domains (`*.hosted.app`, `*.web.app`, `*.firebaseapp.com`). |
| **Secrets Mgmt** | **@dotenvx/dotenvx** | `backend/.env`<br>`backend/.env.keys` | Cross-platform AES-256 encrypted environment variables preventing credential leakage in git version control. |
| **CI/CD Pipeline** | **Google Cloud Build** | `cloudbuild.yaml` | Automates container image build (`gcr.io/$PROJECT_ID/github.com/pu-roi/lanes:$COMMIT_SHA`), executes database migrations via Cloud Run Job (`lanes-migration`), and deploys new revisions to `lanes-api` with `CLOUD_LOGGING_ONLY` audit logging. |
| **Database Migrations** | **Google Cloud Run Jobs** | `cloudbuild.yaml`<br>`backend/alembic/` | Serverless batch job (`lanes-migration`) executed synchronously (`--wait`) prior to web service rollout to apply Alembic migrations against production PostgreSQL. |
