# LANES Bug Fix Log & Issue Tracker

> **Last Updated:** October 09, 2026, 12:05 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

### [BUG-130] Valid cross-barangay citizen zones have no automatic simulation

- **Status:** Resolved locally; matching API/frontend deployment remains pending.
- **Severity:** Medium — approved Zone #18 could not exercise the subsidence model.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Zone #18 in San Nicolas/Santo Tomas displayed boundary ambiguity and missing observation time. It was fully inside Pasig, but the adapter required one barangay and supported only official-registration recording proxies.
- **Root cause:** Single-identity resolution/preview scope plus a missing approved-citizen source-time path. Report #16 has immutable submission audit #164 with `observed_at=null`, valid road geometry, and matching approval #166; submission time cannot become an observed onset.
- **Solution:** Require complete Pasig parent containment, retain all intersected names and validate every identity for the shared model. Derive a separately labeled submission simulation from unchanged qualified source/approval records; stop on conflicts, invalid clocks, edits, later evidence, closure or unsupported age. Existing Overview distinguishes source types automatically.
- **Files/verification:** Zone prediction CRUD/schema/service, subsidence request/response/scope service, existing Overview/API types/calculation component and focused tests. Seventy-seven backend/model/location and twelve responsive checks pass; real Zone #18 ASGI read in a read-only transaction preserves observation, geometry, status and expiry and yields a stable forecast. [Acceptance](../evaluations/zone18-submission-simulation-20261008.md). No model fit, SQL schema, dependency or cloud release change.

### [BUG-129] Local Docker startup blocks disposable PostGIS verification

- **Status:** Investigating — preserved/recreated runtime socket folders; controlled restart still reproduces the socket failure. Docker is stopped. Native database checks remain blocked pending host recovery.
- **Severity:** Low — local verification environment; deployed LANES is independent of this Docker instance.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Starting Docker for calculation-response spatial/API verification fails while renaming `sailor-ingest.sock` to `.stale`, with Windows reporting the file cannot be accessed. The user supplied the same Desktop error twice.
- **Root cause evidence:** The symptom matches [Docker's reported Windows stale AF_UNIX socket issue](https://github.com/docker/desktop-feedback/issues/554). After the first runtime-directory recovery, logs also report a WSL timeout mounting the existing data disk. A deeper host/filesystem cause is not verified.
- **Strategy/result:** Validate explicit absolute socket-directory targets and confirm Desktop/backend stopped, then preserve the two runtime parents under sibling backup names. No VM disk, container volume, WSL registration or application data is removed. Desktop force-stop and Docker-distribution termination succeed; the subsequent start again fails. Leave Docker closed and recommend a Windows restart before further startup diagnostics.
- **Files/verification:** No LANES source change is made for this environment issue. Backup locations and exact blocked checks are recorded in the [calculation walkthrough evaluation](../evaluations/calculation-details-walkthrough-20261008.md#local-docker-interruption). Mathematical/API-unit and browser verification continue separately; native acceptance is not claimed.

### [BUG-128] Incomplete automatic prediction locality and unsupported feature-effect claims

- **October 9 planner disposition:** Keep In Progress for demonstrated local accuracy. [Decision 26](../decisions.md#26-cross-location-learning-as-a-source-bound-research-comparison) records the delivered partial-pooling comparison and its incomplete/mixed holdouts; version-control publication does not resolve the evidence/calibration or Docker/release gaps. [@roicambe](https://github.com/roicambe) (Roi Cambe)

- **Cross-location follow-up:** Fixed-prior depth/location AFT, purged comparisons and an automatic source-bound research panel are implemented locally. Thirty-six records still share three summaries; partial/mixed or unsupported tests do not establish improvement. BUG-128 remains In Progress for learned local accuracy. 131 backend/model/API checks and 24 responsive cases verify behaviour, not field accuracy. [Results](../evaluations/cross-location-duration-20261008/README.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

- **Status:** In Progress — locality coverage resolved locally; source-feature capture/evaluation and future LANES evidence collection/export implemented. Learned street-specific model improvement remains open because tested candidates fail comparative selection.
- **Severity:** Medium - ten missing locality polygons prevented automatic detection; adding unqualified features would not establish accuracy.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Prediction reused a 20-record OSM catalog and shared intercept-only duration pattern, including on new streets.
- **Root cause:** Missing/unclosed OSM administrative relations and source-parent constraints; actual training has three subsidence/two transport summaries and no qualified street drainage/terrain/rainfall effect histories. Many depth pairs are unchanged and source/availability uncertainty persists.
- **Solution:** Validate a separate complete 30-record OCHA/HDX COD source-parent partition with current PSGC crosswalk, without weakening news footprint gates. Freeze source/versioned input snapshots and expose bounded current context in existing read-only details. Compare whole-summary/episode feature models and retain baselines when they perform worse. The developer-selected future LANES reporting/review path now captures public updates and owner follow-ups with bounded private source export; qualified independent wet/outcome episodes still need to accumulate before a better model can be selected. Never generate observed dry labels or guessed hydraulic capacity.
- **Files/verification:** flood_location/flood_feature services; private context endpoint and audit hooks; COD range extractor/catalog builder/runtime assets; source feature evaluator; existing Overview details/API. 256 comprehensive backend/model and 38 responsive workflows pass, with TypeScript/lint, asset verification and two real Zone #17 flows; the final run includes precision and future-source/export cases. [Evaluation](../evaluations/pasig-location-feature-models-20261008/README.md). No package/schema/operational expiry/status/routing/deployment change.

### [BUG-127] Prediction UI required hypothetical inputs instead of resolving zone evidence

- **Status:** Resolved locally for automatic UI/registration simulation. Independent model accuracy and operational forecast-to-Unconfirmed/public retention remain open.
- **Severity:** Low - rejected test controls did not fulfill the automatic prediction workflow.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Overview required hypothetical barangay/time inputs and an acknowledgment checkbox; Zone #17 had no displayed result.
- **Root cause:** The initial saved-suggestion adapter was report-bound, followed by a hypothetical test form. The live record had no qualified observation clock; its Ugong location was outside the four-location subsidence cohort. Collection coverage, training cohort, prediction transfer and boundary geometry had been conflated.
- **Solution:** Remove test/save/checkbox controls. Resolve the authoritative polygon, select qualified linked same-zone/event citizen/current news evidence, and keep nearby reports candidate-only. Enable explicitly labeled pooled experimental transfer; provide a separate simulation from an unchanged recent official registration audit when actual observation time is absent. Keep unknown observation time, source admission and operational expiry unchanged. Freeze issuance anchors so refresh cannot move the forecast indefinitely.
- **Current files / verification:** zone_prediction schema/CRUD/service/private GET; subsidence scope/status contracts; separate passability kernel target/service/artifact/API/trainer; existing Overview/component/API integration. Recorded verification: 127 focused backend checks, 34 desktop/mobile workflows, two real Zone #17 flows, TypeScript/scoped lint. #17's audit #140 simulation shows around 5:13 PM PHT on October 8; this is a saved verification observation, not a newly measured outcome. [Acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md#october-8-pooled-research-transfer-transport-target-and-automatic-registration-simulation).
- **Data correction:** Annual/main wet union covers 30 barangays; main/overlay named wet claims cover 21. Ugong has eight annual, seven main wet, three overlay wet and one passability projection. Actual subsidence cohort remains four locations/37 projections/three summaries; the separate passability fit uses seven locations/nine projections/two summaries. Experimental transfer across 30 identities and the 20-polygon catalog are distinct. No dry labels are imputed. [Coverage audit](../evaluations/pasig-barangay-coverage-20261008/README.md).
- **History:** Initial report-bound/saved suggestion and rejected hypothetical test controls were superseded. Initial automatic-adapter verification recorded 69 backend/30 responsive cases; later model/simulation acceptance above is the current checkpoint. No SQL/schema/package, public routing/status/expiry write or deployment is claimed.

### [BUG-126] Structured owner follow-up uses rejected React state/ref patterns

- **Status:** Resolved and verified locally.
- **Severity:** Low — scoped lint rejected the existing implementation; no failed production submission is claimed.
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Verification of the previously untested owner flow found `set-state-in-effect` and `refs` lint errors in timezone initialization and retry-button rendering.
- **Root cause:** Device timezone was copied into state synchronously during an effect, while rendered retry text inspected `attempt.current` directly.
- **Solution:** Read device timezone when opening the follow-up panel; track retry display state explicitly while retaining the immutable request in an event-handler ref. Draft changes reset both. No default observation clock is introduced.
- **Files / verification:** `frontend/src/features/flood-followups/FollowupSubmission.tsx`, `frontend/tests/flood-review-suggestions.spec.ts`. Owner timed-entry/same-UUID failure-retry scenarios pass on desktop/mobile, as part of sixteen responsive scenarios. TypeScript and scoped lint pass with zero errors and one unrelated existing moderation warning. [Acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md).

### [BUG-125] Active Zone details diverge from Needs Review and do not hand off selected community evidence

- **Status:** Resolved and verified locally; release pending.
- **Severity:** Medium.
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Active Info showed sparse raw vehicle values and duplicated notes, while Needs Review used structured flood facts. Opening Edit from community updates carried only the official zone, with no selected evidence reference. Existing stale draft restoration silently removed older local edits.
- **RCA:** Separate renderers/formatters, legacy report_text prioritizing admin_notes, no selected-update/editor contract, independent non-atomic zone/audit commits, and an automatic stale-draft deletion branch.
- **Solution:** Shared facts and source projection, independent update list/detail/comparison, backend-selected patch, explicit incorporation, retained stale draft inspection, expected-version lock and atomic save/provenance. Reviewed/dismissed states remain independent; whole-zone clearance requires scope assessment. Separate media failure reports partial success.
- **Files:** shared FloodFacts/RecordDetailsDialog/floodSurvey, ActiveZoneDetails/ZoneObservationReview/ZoneGeometryComparison, ActiveZonesPanel/LiveMapPage, existing OfficialZoneDrawer/draft storage, zone_update schema/CRUD/service/endpoint, zone_editor_service and admin zone GET/PUT projection.
- **Verification:** 39 native observation/editor/growth checks and 14 distinct desktop/mobile scenarios pass across recorded runs; TypeScript passes. Mobile editor rail placement and a visible selected-update review badge were checked after fixes. [Responsive and release acceptance](../evaluations/flood-zone-community-updates-20261008.md#admin-comparison-follow-up-october-8).

### [BUG-124] Blocked WebGL initialization crashes the map page

- **Status:** Application recovery fixed and verified locally; browser/device GPU availability remains external.
- **Severity:** High - browser refusal of a WebGL context surfaced as an uncaught Next.js runtime error instead of a usable page.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** MapLibre construction throws Failed to initialize WebGL with status Web page caused context loss and was blocked. Changing map styles still requires the same graphics context.
- **Root cause:** BaseMap did not catch constructor failure or present context loss. Cleanup already removed initialized maps, but the immediate effect still allocated an extra development Strict Mode context. The browser's underlying resource/block reason cannot be established from the error alone.
- **Solution:** Schedule creation on a cancellable animation frame, catch failed construction and remove partial canvas DOM, show Map unavailable/Retry map without automatic graphics retry loops, handle context loss and clear the error after a restored render, suspend style retries while lost and clear delayed compass/resize work on cleanup. Map/report state is not reset by the recovery screen.
- **Files / validation:** `frontend/src/shared/ui/map/BaseMap.tsx`, `frontend/tests/webgl-recovery.spec.ts`. Four desktop/mobile checks reproduce browser refusal, verify one initial allocation under Strict Mode, handle failed/successful manual retries with no page errors and recover a real simulated lost context. Two flood-zone popup regressions also pass. TypeScript/whitespace checks pass; BaseMap's eight lint errors/seven warnings equal HEAD baseline. No package/model/migration changes and no deployment. [Details](../evaluations/cloud-performance-20261007.md#october-8-webgl-recovery).

### [BUG-123] Public update interface diverged from Report Flood

- **Status:** Reworked locally; provider/device/release verification pending.
- **Severity:** Medium — separate panel/inconsistent controls and missing editable extent prevented the requested reporting workflow.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Updates used a separate panel, then a shared shell with a survey dropdown, three attachment actions, time/spot/depth-unsure fields and no editable road anchors. Mobile autocomplete could place suggestions outside the viewport.
- **Root cause:** Update presentation/state was built independently of the original reporting fields; original survey/location interactions were not reused. Portal placement measured input bounds before mobile keyboard/sheet movement and sat below sheets.
- **Solution:** One Report Flood shell, shared depth/media/description and Take Survey/separate survey view; original large picker plus one camera action; remove extra controls; authenticate original road context and allow editing through the existing location/map preview workflow. Server rebuilds proposed extent into private audit evidence, without operational edits or fabricated observation clocks. Dropdown tracks open input bounds, chooses viewport space and sits above sheets. Independent road/form state preserves original report drafts.
- **Files / verification:** `FloodReportPanel`, `FloodReportFields`, `ZoneUpdateForm`, `useFloodMedia`, `useZoneRoadPreview`, `MapContext`, `GlobalMap`, `MapCanvas`, shared `LocationAutocomplete`, `zone_update` schema/API/service and staff `ActiveZoneDetails`; native and responsive tests. Sixteen native checks pass; [acceptance](../evaluations/flood-zone-community-updates-20261008.md) records browser/provider/release evidence. No model/migration/package change.

- **Guest-screen follow-up:** Both modes now render the exact original `FloodReportLoginGate` (badge, heading, message, spacing, button); signed-out updates show no zone header/return link or extra desktop close button. The selected zone/condition remains encoded in login return. Two desktop/mobile parity checks compare markup/dimensions, plus two signed-in upload regression checks; TypeScript/scoped lint pass.

- **Header return follow-up:** Move the body return link to a compact New report header action. Existing ConfirmDialog warns about losing the current update fields/files, with Keep editing and Discard. Cancel retains edits; confirmation restores the unrelated unfinished report. Tests check header alignment/full title, 320px warning bounds, cancellation/media retention and original draft restoration; guest parity remains. Popup confirmation wording is short enough for narrow screens.

### [BUG-122] Unwanted observation-time field in Report Flood

- **Status:** Removed and verified locally; release pending.
- **Severity:** Low — unexpected extra field disrupts the existing public report interface.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** The new-report panel displays “When did you observe this flood? (Optional)” above road selection, although the developer wants the existing workflow preserved.
- **Root cause:** Commit `f04108c` added observation-time collection/state/draft submission for conservative citizen automatic approval on October 7; this was separate from the current Active Zone update panel.
- **Solution:** Remove that field and new-report timestamp handling, including submission from older queued drafts. Preserve backend observation support and policy; reports lacking explicit observed time remain for staff review. Update-only observation time remains in the current zone observation form.
- **Files modified / verification:** `FloodReportPanel.tsx`, `floodReportDraftStorage.ts`, `MapContext.tsx`, `tests/citizen-observation.spec.ts`. Six desktop/mobile browser checks pass for legacy drafts, multipart timestamp omission, backend feedback and existing report media. Shared-panel consolidation is recommended separately, not claimed delivered.

### [BUG-121] Existing-zone reader uses an undefined update request

- **Status:** Fixed and verified locally; matching release pending.
- **Severity:** Medium — reading an existing zone can fail and block refreshed details/edit recovery.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** An authenticated staff GET to `/admin/zones/{zone_id}` for an existing zone reaches a reference to `body.is_active`, although the reader accepts no request body.
- **Root cause:** An ended-event reactivation guard is placed in `get_zone`; `body` is only defined in the separate `update_zone` handler.
- **Solution:** Remove the undefined request check from GET and enforce ended-event reactivation protection in PUT. Native authenticated HTTP acceptance verifies existing-zone reads alongside private observation endpoints.
- **Files modified / verification:** `backend/app/api/v1/endpoints/admin.py`, `backend/tests/test_zone_updates.py`. Ten native checks and eight desktop/mobile browser checks pass for the integrated update feature. Visual acceptance also corrected its popup footer height and mobile sheet stacking/safe-area positioning. The broader legacy Create/Edit upload/description gaps remain unmodified. [Acceptance](../evaluations/flood-zone-community-updates-20261008.md).

### [BUG-120] Community Trending Hotspots displayed fixed example places

- **Status:** Fixed and verified locally; deployment pending.
- **Severity:** Medium — fixed counts/places falsely suggested current community activity.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** Open the desktop feed sidebar or mobile navigation; España, Taft and EDSA-Kamuning always appeared with the same counts even when the feed had no current activity.
- **Root cause:** Both layouts contained duplicated hardcoded labels, counts and map coordinates, with no backend ranking or freshness policy.
- **Solution:** Parameterized public aggregation of named/located posts with a default 24-hour window and bounded 48-hour fallback only if nothing qualifies, two distinct contributors, per-author latest activity weight with a six-hour half-life, and deterministic top-three ordering. Match normalized case/whitespace labels and PostGIS proximity (500 projected metres in EPSG:3857, approximately 484 ground metres around Metro Manila). Use a representative saved report point or post coordinates for map links. Public pending and approved shares count as community activity, without asserting flood confirmation. Deleted/hidden/private/rejected content, old report reshares, inactive/deleted accounts and missing/invalid locations do not count. Different aliases are not automatically merged.
- **Files:** `backend/app/api/v1/endpoints/feed.py`, `schemas/feed.py`, new `services/trending_hotspots_service.py`, `crud/trending_hotspots.py`; `frontend/src/features/feed/feedApi.ts`, new `components/TrendingHotspots.tsx`, `LeftSidebar.tsx`, `FeedPage.tsx`; native PostGIS and responsive Playwright tests.
- **Verification:** 13 focused backend checks pass after applying existing Alembic migrations to a fresh disposable PostgreSQL/PostGIS database; TypeScript and focused lint pass. Eight Chromium Playwright checks pass across desktop and iPhone-sized mobile viewports, covering navigation, empty/error/retry states and automatic expiry refresh; both screenshots reviewed. No SQLAlchemy model, migration or dependency addition.

- **Sidebar design follow-up:** Align loading/empty states with Saved Places and compact list rows/actions across desktop/mobile; remove the technical ranking footer. Eight browser checks and TypeScript/scoped lint pass; screenshots reviewed. The existing navigation check now waits for the mobile drawer animation before measuring bounds.

- **Final acceptance record:** [Community hotspots verification](../evaluations/community-trending-hotspots-20261007.md) records the final nine native/ten browser checks, unchanged schema/dependencies and release limits.

- **Bounded freshness follow-up:** The selected window is returned by the backend and displayed by both sidebar layouts. One qualifying place prevents older filler; fallback excludes posts/report sources beyond 48 hours, preserves privacy and distinct-author protections, and returns to 24 hours when fresh activity qualifies. Nine native PostGIS/API checks and ten desktop/mobile browser checks pass, plus TypeScript/scoped lint. Existing migrations apply in the generated local database, which is removed after acceptance; no model/migration/dependency changes.

### [BUG-119] System Settings saved unused values and could fail after persisting

- **Status:** Fixed and verified locally; matching production release remains pending.
- **Severity:** Medium — stored settings could be ineffective or a save could fail after changing values.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Problem:** The four legacy controls had no runtime consumers. Legacy saving committed before an incorrectly called audit function, so an error could follow a persisted change.
- **Resolution:** Typed shared policy replaces legacy writes. Known keys/ranges and capabilities are checked; advisory serialization plus revision conflicts protects edits. Settings, revision and audit share one transaction. The response is constructed before commit, so response assembly errors also roll back. Legacy rows/read access remain for history. Mobile/desktop drafts survive save errors and edit conflicts. [Verification](../evaluations/functional-system-settings-20261007.md).

- **Pre-push verification:** The fresh 174 native settings/lifecycle/growth checks pass with existing migrations in removed disposable PostGIS databases. Changes include `backend/app/api/v1/endpoints/settings.py`, `backend/app/services/configuration_service.py`, `backend/app/schemas/configuration.py`, settings-consuming worker/zone/report services and `frontend/src/features/admin/SystemSettingsPage.tsx`. No new production release is claimed. [Audit](../evaluations/pasig-subsidence-validation-20261007/README.md#senior-planner-pre-push-checkpoint).

### October 7: Docker socket startup recovery repeated during settings verification

The ingest socket failure recurred, followed by a second stale Secrets Engine socket. Only recognized crashed Docker processes were stopped. Zero-byte runtime socket directories were moved to recoverable backups, then recreated. `lanes_postgis_db` and `lanes_valhalla` returned to running state; databases, volumes and application data were preserved. Backups are recorded in the [settings verification](../evaluations/functional-system-settings-20261007.md). This is a workaround for the [reported Docker Desktop startup defect](https://github.com/docker/desktop-feedback/issues/554), not a permanent Docker fix. [@roicambe](https://github.com/roicambe) (Roi Cambe)

### [BUG-118] Private follow-up evidence leaks through the generic audit feed

- **Status:** Resolved in local code; actual API/privacy acceptance and deployment pending.
- **Severity:** High — non-Commuter staff without Reports permission could otherwise read private citizen/staff follow-up evidence.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Independent source/security review of the new follow-up workflow found `/admin/audit-logs` returns generic `metadata_json` under a dependency that excludes only Commuter. The new dedicated follow-up routes correctly restrict evidence, but the generic reader could bypass that capability boundary.

#### 2. Root Cause Analysis

Follow-up observations/reviews reuse the existing append-only audit JSON pattern. Generic `get_audit_logs` previously selected every action type without excluding private feature records.

#### 3. Solution & Architectural Strategy

Exclude `FLOOD_FOLLOWUP_OBSERVATION` and `FLOOD_FOLLOWUP_REVIEW` from the generic audit query before action filters, count and pagination. Even an explicit action filter cannot retrieve those records there. Ownership/Reports-capability checked follow-up reads remain the sole evidence interface, with no-store responses. No source record is deleted or redacted in persistence.

#### 4. Files Modified / Verification

`backend/app/crud/audit.py` uses the centralized follow-up action constants and preserves unrelated/legacy-null action behavior. An independent reviewer re-read the fix and found the source-level access path closed; Python syntax/diff checks pass. Actual API/database privacy tests were not requested/run. [Implementation and limits](../evaluations/structured-flood-followups-20261007.md).

### [BUG-117] Live free auditor times out at the normal worker deadline

- **Status:** Investigating availability; fail-closed behavior verified, current-article acceptance pending.
- **Severity:** Medium — eligible current news can be deferred to review instead of automatic publication.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The October 7 live-news audit verified `openrouter/free` configuration, then made one historical synthetic probe at the default 20-second worker deadline. It returned `probe_failed`, `unavailable`, `auditor_timeout`, and no HTTP status. Earlier successful synthetic responses do not establish consistent availability.

#### 2. Root Cause Analysis (RCA)

The client deadline elapsed before a usable response. The specific provider/network/server cause is unverified; production has no claim evaluations with which to measure current-article failure rates. This is distinct from BUG-114's repaired quote-offset formatting defect.

#### 3. Solution & Architectural Strategy

Retain required independent confirmation and failure-to-review behavior. Measure availability/latency with representative current articles before declaring unattended activation accepted. No paid fallback, persistence-timeout change, safety-gate relaxation or repeated synthetic probe was used.

#### 4. Files Modified / What Changed

No application/provider configuration change. Record the safe probe result, acceptance tasks and verification limits in `docs/evaluations/news-live-operational-audit-20261007.md`, `docs/task_plan.md` and `docs/progress.md`. The synthetic probe has no database/publication access. [Audit](../evaluations/news-live-operational-audit-20261007.md).

### [BUG-116] Sync database work scales with clients; weather blocks the API loop

- **Status:** Fixed and deployed; 37 backend/16 desktop-mobile regressions and real API/public smoke checks pass. Sustained load/physical-device speedup remain unverified.
- **Severity:** Medium for responsiveness and load growth.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The second performance audit found one flood DB query per SSE client every 15 seconds and blocking Open-Meteo calls inside async weather handlers. Offline engine warm-up also started alongside first map rendering. The small live request sample had a first-wave 1.27–1.31-second cluster, with later active-zone reads at 13–16 ms; it is not a controlled user-speedup benchmark.

#### 2. Root Cause Analysis (RCA)

Independent client polling repeats the same read/serialization. A synchronous weather SDK blocks the async event loop, so unrelated requests share its wait. Offline warm-up competes for startup resources even though it can wait until the map appears.

#### 3. Solution & Architectural Strategy

Use one shared DB-backed poll per worker with 100 reserved subscriptions, latest-result queues and idle/shutdown cleanup; retain init/update/unavailable behavior and independent routing safety reads. Run current/forecast handlers in FastAPI's worker pool. Schedule offline warm-up after render/idle with a timeout and older-browser timer fallback.

#### 4. Files Modified / What Changed

`services/flood_sync_service.py`, `endpoints/sync.py`, application lifespan, weather current/forecast signatures, `BaseMap.tsx`, snapshot/broker/weather tests and desktop/mobile map performance tests. No new schema/library/auth or cloud capacity change. [Research, tests and release details](../evaluations/cloud-performance-20261007.md#second-pass-shared-polling-and-responsive-weather-handlers).

### [BUG-115] Cold starts, redundant flood refreshes and blocking route searches

- **Status:** API/job/frontend fixes deployed and browser smoke checks passed; next scheduled discovery-run memory and sustained/physical-device acceptance remain unverified.
- **Severity:** Medium for interactive latency; High for separate discovery-job memory failures.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The developer reported a slower newer version. Cloud logs showed 18–21-second API startup waits, duplicate flood-refresh paths and two 512-MiB discovery-job memory-limit failures. Production browser tests also exposed full-page reloads on reconnect that cleared open news panels.

#### 2. Root Cause Analysis (RCA)

Scale-to-zero, synchronous Valhalla/database waits in asynchronous routing, repeated empty exclusions, unchanged SSE snapshots triggering HTTP refetches alongside 15-second map polling, eager hidden map work and the PWA plugin's default online reload. Database/API/frontend metrics did not justify general resource upgrades under observed traffic.

#### 3. Solution & Architectural Strategy

Keep one API instance warm and give discovery 1 GiB. Offload synchronous waits and overlap at most two searches; preserve all flood gates and wait for in-flight calls before fallback. Send changed snapshots with keepalives, retain offline data on failed reads, use a 60-second map fallback, defer initial map/panels and keep PWA state during reconnect.

#### 4. Files Modified / What Changed

Backend routing, sync and retention services/endpoints; providers, live-sync hook, map/admin polling, GlobalMap, feed coordinate navigation, PWA configuration, Cloud Build and focused tests. **32 backend and 14 distinct desktop/mobile browser tests**, frontend build/type/lint and public desktop/mobile smoke checks passed. Exact rollout and browser results are maintained in the [evaluation](../evaluations/cloud-performance-20261007.md); next scheduled news-run RAM and physical phones remain unverified.


This document records bugs, regressions, and unintended system behaviors that have been investigated, are pending resolution, or have been resolved in LANES. Each entry documents the bug context, root cause analysis, resolution strategy, and exact files modified to ensure a clear audit trail.

---

### [BUG-114] Free-auditor quote positions fail exact article grounding

- **Status:** Repaired and verified locally with exact-source options; broader real-article/deployment acceptance remains pending.
- **Severity:** Medium - a returned structured audit can fail before eligible news publication.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

After a twenty-second timeout, a sixty-second synthetic probe received structured evidence with positions that did not match its quotes in the article. The validator correctly rejected it with `audit_evidence_offset_mismatch`.

#### 2. Root Cause Analysis (RCA)

The prompt required the model to count Python character positions. This introduces a formatting burden even when quotes are available in immutable text. The discarded response does not establish the exact counting mistake; exact source validation remains required.

#### 3. Solution & Architectural Strategy

Calculate bounded exact quote/start/end options on the server and instruct the independent model to select/copy them. Keep full article context, strict immutable-substring checks and existing fact/status/time/identity gates. Prompt v2 changes the evaluation fingerprint. Return only safe numeric HTTP status for transport failures; never raw provider messages or automatic paid fallback.

#### 4. Files Modified / What Changed

`news_claim_auditor.py`, internal `news_audit.py` result metadata, `scripts/check_news_auditor.py` and representative tests. **170 distinct checks pass**, including native evaluation/policy/history. Live synthetic free probes validate at both sixty and twenty seconds and remain historical review; Linux image/offline asset checks pass. No dependency/model/migration/cloud write or new UI design. [Evidence](../evaluations/phase-36-auditor-evidence-options-20261007.md).

### [BUG-113] NOAH analytical tiles are absent from the API/job image

- **Status:** Resolved and verified locally; matching cloud rollout remains pending.
- **Severity:** High - automatic estimated road placement lacks a required runtime input.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Local placement uses the approximately 90 MB NOAH catalog, while an image built from `backend` cannot access ignored root `data/noah-placement`. The rendered public hazard overlay does not supply those analytical vectors.

#### 2. Root Cause Analysis (RCA)

The catalog default points outside the Docker build context. Existing runtime bundling contains OSM/history/boundaries but not NOAH; deployment therefore cannot reproduce local placement.

#### 3. Solution & Architectural Strategy

Preserve the checked bounded catalog in `backend/runtime_data/noah-placement`, retain ODbL attribution and manifest hashes, and verify all declared tiles plus qualified parent coverage during Docker build. Local defaults use the bundle; Docker sets `/data/noah-placement`; explicit configuration overrides remain. No modeled polygon becomes current evidence merely because packaging passes.

#### 4. Files Modified / What Changed

`noah_vector_catalog_service.py`, `backend/Dockerfile`, runtime README/bundle, `.gitattributes`, packaging/verifier scripts and focused fixtures. **188 focused tests**, final Linux image build and offline asset verification pass. No new dependency/model/migration or deployed cloud change. [Evidence](../evaluations/phase-36-news-runtime-packaging-20261007.md).

### [BUG-112] News-created road zones omit the existing solid road core

- **Status:** Resolved locally for automatic estimated road corridors; catalog-only polygons require separately supported road geometry.
- **Severity:** Medium — active road-zone presentation cannot display both expected layers.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

News activation persists an operational polygon, but an active road zone needs the existing solid centerline plus transparent outer area on both public and staff maps. Source tracing shows news activation supplies only the area.

#### 2. Root Cause Analysis (RCA)

`activate_operational_footprint` constructs `FloodAvoidanceZoneCreate` without source_geometry or a road report. `FloodAvoidanceZone.report_geometry` resolves source_geometry or primary-report geometry. `useFloodZonesLayer` creates the solid-core feature only for LineString/MultiLineString report_geometry; its polygon feature uses the transparent fill.

#### 3. Solution & Architectural Strategy

Bind accepted bounded news road linework to the operational area and persist it through existing source_geometry where supported. Keep exact component ownership/containment and disconnected spans. Reuse existing mapStyles/useFloodZonesLayer on both screen sizes. Complete placement-to-activation acceptance separately; a preview ranking alone is not field-verified geometry. No schema/model change is part of this audit.

#### 4. Files Modified / What Changed

`news_estimated_road_service.py` derives each accepted component and its road line; `news_publication_service.py` persists the core through existing source_geometry and rechecks it on refresh. Safe public/staff news projection and existing popup/summary facts expose source/time/status/basis. Shared paints remain unchanged. Native storage/HTTP/routing checks and actual desktop/mobile core/aura pixel tests pass. No model/migration or new design. Arbitrary catalog polygons do not acquire invented centerlines. [Verification](../evaluations/phase-36-estimated-road-zone-integration-20261006.md).

### [BUG-111] Scheduled news command stops before publication and footprint activation

- **Status:** Resolved locally; release/current-source provisioning remains pending.
- **Severity:** High — saved flood claims never reach operational activation through the configured command.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The local Cloud Build news-job command selected `--discover --process`, which performs durable extraction only. The explicit publication pipeline did not call the footprint activation helper. Repeated stateless batches could also revisit completed handoffs instead of later claims.

#### 2. Root Cause Analysis (RCA)

The configured command and service handoffs predated the publication/footprint contracts. Seed batching included already-bound and empty extraction runs; activation had no worker-stage caller.

#### 3. Solution & Architectural Strategy

Add opt-in discovery `--pipeline`, prepared local job args, restart seeding filters and an exact approved-catalog activation stage after publication/expiry. Keep activation atomic and revision/evidence guarded; staff choices remain protected. Scan bounded catalog candidates past failures while limiting successful activations. Sanitized errors appear in summaries and CLI exit status. Missing catalog is normal text-only fallback; invalid configured catalog is an error. No real source is provisioned and no deployed job was changed.

#### 4. Files Modified / What Changed

New `backend/app/services/news_footprint_worker_service.py`; existing pipeline/evaluation/publication services; discovery and pipeline CLIs; local `cloudbuild.yaml`; worker/native lifecycle/pipeline/CLI tests and guarded verification runner. **456 distinct checks pass** overall. No schema or dependency changes. [Verification](../evaluations/phase-36-automatic-footprint-worker.md).

### [BUG-110] Operational shape validation is treated as verified incident evidence

- **Status:** Resolved locally; **398 distinct checks pass**. Actual current source provisioning and map integration remain open; worker connection is verified in [the subsequent worker checkpoint](../evaluations/phase-36-automatic-footprint-worker.md).
- **Severity:** High — arbitrary source labels and partial locality overlap previously authorized operational geometry.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

A valid polygon partly outside its reported locality passed with a nonempty arbitrary source label; shape acceptance was not proof of a current affected footprint.

#### 2. Root Cause Analysis (RCA)

The optional parent predicate used intersection; provenance checked only string presence and coordinate bounds substituted for explicit CRS. No trusted exact current article/claim/incident approval or component binding existed, and newer observations could renew old geometry.

#### 3. Solution & Architectural Strategy

Separate shape validation from server approval. Resolve qualified locality assets and require full coverage, explicit SRID and all valid disconnected parts. Bind exact current evidence to an operator-approved catalog record or stored active/capable staff review. Client labels/checksums and modeled geometry cannot approve a zone. Preview/save share gates; relinks verify article/incident/component/metadata ownership. Unsupported renewal becomes an alert with a private reason and withdraws unsupported old links; immutable history stays intact. No real current catalog is provisioned.

#### 4. Files Modified / What Changed

`backend/app/services/operational_footprint_service.py`, new `operational_footprint_evidence_service.py` and `news_permissions.py`, `news_publication_service.py`, `news_road_placement_service.py`, publication schema/API/dependencies, geometry/catalog/road/native lifecycle tests and the guarded runner. Sixty added targeted checks cover geometry limits/coverage/provenance, catalog integrity and native incident/actor/preview/refresh/relink rejection. No SQLAlchemy models or Alembic definitions changed. [Verification](../evaluations/phase-36-trusted-footprint-contract.md); [original reproduction](../evaluations/phase-36-integration-audit-20261005/README.md).

### [BUG-109] Correcting an active news case to retain its own zone deactivates that zone

- **Status:** Resolved locally; **289 distinct checks pass** across the repair and related regressions.
- **Severity:** High — operational map/routing/lifecycle behavior differs from accepted news evidence.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

An audited same-case correction appended an active-zone supported link but immediately deactivated its retained zone and truncated expiry.

#### 2. Root Cause Analysis (RCA)

`_withdraw_support` excluded `previous.case_id` rather than the prior decision, ignoring the newly current support revision. Retained active labels consequently pointed to inactive coverage.

#### 3. Solution & Architectural Strategy

Exclude only the previous decision ID, retaining current-revision, active-state, unexpired linked support from any case. Preserve original expiry on retention/retry; reject expired target zones. Final withdrawal ends solely news-supported coverage and its final event without deleting history. Existing independent news/citizen and manual-owner exemptions remain intact.

#### 4. Files Modified / What Changed

`backend/app/services/news_publication_service.py` and native lifecycle tests. Six retained-support final-state cases, replacement, concurrency, two rollback cases and expired-zone rejection pass; existing shared-source/citizen coverage regression also passes. [Repair verification](../evaluations/phase-36-zone-metadata-support-repair.md); [original reproduction](../evaluations/phase-36-integration-audit-20261005/README.md).

### [BUG-108] News-created zones lose accepted flood depth and severity

- **Status:** Resolved locally; **289 distinct checks pass** across the repair and related regressions.
- **Severity:** High — operational map/routing/lifecycle behavior differs from accepted news evidence.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

A waist-depth claim created a high/waist event but its zone read medium/null. Native public-zone verification also found polygon contributor geometry failed response validation.

#### 2. Root Cause Analysis (RCA)

Creation populated event peaks without existing zone override fields. Routing reads zone metadata. `ZoneContributorResponse` permitted PolygonGeometry but omitted Polygon EWKB decoding.

#### 3. Solution & Architectural Strategy

A shared news-only validator supplies supported depth/severity and independently confirmed access metadata to every created component via existing fields. Unknown depth and passable-all activation reject; unknown access stays unset. Explicit vehicle prohibitions can only tighten depth policy, without inferring other allowed classes or pedestrian closure. Decode valid contributor polygons through the existing parser.

#### 4. Files Modified / What Changed

`backend/app/services/news_publication_service.py`, `backend/app/services/flood_routing_policy.py`, `backend/app/schemas/report.py`, native lifecycle tests and the preserved runner. Sixteen MultiPolygon metadata cases, five real public API/native vehicle-policy matrices and five measurement/access rejections pass. No SQLAlchemy model/migration or new request-level override field. [Repair verification](../evaluations/phase-36-zone-metadata-support-repair.md); [original reproduction](../evaluations/phase-36-integration-audit-20261005/README.md).

### [BUG-107] Operational activation fails decoding its stored independent audit

- **Status:** Resolved locally; both original regressions and 23 added guard/retry/transaction checks pass. BUG-108/109 are subsequently repaired; BUG-110 is subsequently repaired locally; operational integration still depends on actual current source provisioning and worker/map acceptance.
- **Severity:** High — activation and refresh could not complete on the approved database.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Fresh migration/pytest reproduced an AttributeError after invalid strict audit decoding was swallowed. After repairing decoding, native tests exposed an unsupported decision operation and insertion of refresh support links before the referenced active decision existed.

#### 2. Root Cause Analysis (RCA)

`activate_operational_footprint` used strict Python-object validation for stored JSON instead of `_load`'s strict JSON path. It omitted current evidence/revision checks and hashed only the source label. The approved operation check rejects `activate_zone`; the existing link trigger requires the active decision before support insertion.

#### 3. Solution & Architectural Strategy

Reuse `_load`, reject malformed/missing/stale evidence safely, validate source/policy/claim/depth/passability/historical observation identity, require expected revision and recheck under incident-then-case locks. Bind the request to geometry/checksum/parent/actor/policy/revision; exact retries return the original decision without resetting expiry. Record private geometry attribution in existing JSONB. Use approved evaluate/correct operations and append the refresh decision before its links within the outer transaction. Provenance attribution does not resolve BUG-110 source trust.

#### 4. Files Modified / What Changed

`backend/app/services/news_publication_service.py`, `backend/app/schemas/news_publication.py`, `backend/tests/test_news_publication_lifecycle_postgres.py`, the disposable verification runner and synchronized records. No SQLAlchemy model, migration definition or dependency change. **103 targeted + 133 auditor/evaluation + four event = 240 distinct passing checks**. [Repair evidence](../evaluations/phase-36-bug107-activation-repair.md); [original reproduction](../evaluations/phase-36-integration-audit-20261005/README.md).

### [BUG-106] Shared Select menu opens outside the available viewport

- **Status:** Resolved; staff desktop/mobile checks and four existing filter/Active Zone regressions pass.
- **Severity:** Medium — staff cannot reliably choose audited evidence or decisions near the screen bottom.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Actual browser verification of the new staff decision controls found that the shared portal dropdown extended below the visible screen instead of remaining reachable. Small/mobile viewports and lower form controls reproduce it.

#### 2. Root Cause Analysis (RCA)

The fixed portal always opened below the trigger and did not constrain its option-list height/position to available visual viewport space.

#### 3. Solution & Architectural Strategy

Measure visual viewport bounds and respond to viewport scroll/resize; choose upward opening when needed, cap menu height and keep horizontal bounds visible. Preserve the existing shared component, backend-owned options and independent report/zone behavior.

#### 4. Files Modified / What Changed

- `frontend/src/shared/ui/forms/Select.tsx`: viewport-aware dropdown flipping, bounds and height.
- `frontend/tests/news-decisions.spec.ts`: staff decision/evidence flows on desktop/mobile.
- Existing location-filter/Active Zone checks verify the shared-control/style behavior still works. [Lifecycle verification](../evaluations/phase-36-news-publication-lifecycle.md).

### [BUG-105] Correcting original wet evidence can roll back a newer matched observation

- **Status:** Resolved locally; two native lifecycle regressions pass in the final checkpoint.
- **Severity:** High — current alert depth/status and observation expiry can regress to superseded evidence.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

After a newer qualified wet report refreshes a stable alert, correcting the original evidence on that same case could restore the older observation/depth. The same rollback remained possible after an administrative review transition.

#### 2. Root Cause Analysis (RCA)

The case/evaluation identity and clearance barrier were valid, but correction did not compare the proposed wet observation to prior append-only wet decisions. Current-state filtering can lose that newer observation after withdrawal/reopening.

#### 3. Solution & Architectural Strategy

`_wet_supersedes` consults same-article, exact-qualified-incident active wet history and blocks an older wet observation. Both automatic publication and shared preview/final correction apply the history barrier. Newer source evidence remains traceable and its accepted clock cannot be rolled back by an older correction.

#### 4. Files Modified / What Changed

- `backend/app/services/news_publication_service.py`: historical newer-wet query used at automatic and staff write gates.
- `backend/tests/test_news_publication_lifecycle_postgres.py`: immediate same-case correction and correction after administrative rejection.
- [Lifecycle verification](../evaluations/phase-36-news-publication-lifecycle.md): all 21 native lifecycle checks.

### [BUG-104] Staff correction bypasses stable-case continuity after observation refresh

- **Status:** Fixed locally; final native regression checkpoint recorded in the lifecycle evaluation.
- **Severity:** High — duplicate or superseded Active source alerts can survive a correction path.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

An automatic newer qualified observation refreshes the stable target alert while its immutable source stays bound to a separate evidence case. Correcting that separate source case using the already-consumed evaluation could publish a second Active alert. Preview and final correction also differed in supersession checks.

#### 2. Root Cause Analysis (RCA)

Staff correction checked its source/case and current audit but did not use the incident serialization, evaluation-consumption and same-lineage continuity gates applied to automatic publication. `allowed_actions` only guides the interface and is not a write-boundary authorization check.

#### 3. Solution & Architectural Strategy

Share correction continuity/supersession validation between preview and final submission. Reject an evaluation consumed on another case and conflicting same-lineage public cases. Acquire incident advisory lock before the target case lock; retain expected revision and globally unique request identity. Staff clearance now hashes the complete validated request body, so changing any payload field under a reused UUID returns identity conflict. Supported evidence remains immutable; a retry cannot create another decision or extend expiry.

#### 4. Files Modified / What Changed

- `backend/app/services/news_publication_service.py`: `_correction_checks`, incident-before-case ordering and shared preview/final gates.
- `backend/tests/test_news_publication_lifecycle_postgres.py`: native separate-case refresh/correction regressions.
- [Lifecycle verification](../evaluations/phase-36-news-publication-lifecycle.md): final scope and checkpoint.

### [BUG-103] Administrative review choices erase a matched-clearance barrier

- **Status:** Fixed locally; final native regression checkpoint recorded in the lifecycle evaluation.
- **Severity:** High — recently cleared flooding could be republished from an older wet observation.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Publish a supported wet observation, record a newer matched clearance, then reopen/reject/defer the case. While the old wet observation is still inside its two-hour horizon, a correction or separate replay could make it Active again despite the preserved clearance evidence.

#### 2. Root Cause Analysis (RCA)

Supersession checked only the latest decision. Nonpublic review decisions carry no observation clock and replace the latest clear operation, hiding its clock from automatic and staff correction guards.

#### 3. Solution & Architectural Strategy

`_clearance_supersedes` checks immutable historical clearance for the same article lineage and exact qualified incident identity. Wet evidence at/before that observed clearance remains superseded after any later administrative choice. Both automatic publication and shared preview/final correction use this barrier; no clearance history is rewritten.

#### 4. Files Modified / What Changed

- `backend/app/services/news_publication_service.py`: historical matched-clearance query and automatic/staff supersession gates.
- `backend/tests/test_news_publication_lifecycle_postgres.py`: clear → reopen/reject/defer → old-wet correction regressions.
- [Lifecycle verification](../evaluations/phase-36-news-publication-lifecycle.md): final native checks and operational limitations.

### [BUG-102] Git newline normalization breaks SHA-bound research replay

- **Status:** Pre-push byte-preservation repair; staged manifest verification is required before commit.
- **Severity:** High — a fresh checkout can fail recorded input/output provenance despite equivalent displayed CSV values.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The pre-push audit found 17 SHA-bound research files whose working bytes would be changed by Git newline normalization. Recorded dataset manifests and replay builders validate exact bytes, so normalized staged files would fail after cloning.

#### 2. Root Cause Analysis (RCA)

`core.autocrlf=true` normalizes text into Git blobs while manifests hash the original working files. Existing source-capture protection did not cover all derived CSV/JSON inputs, the three hashed collector/builder scripts or the hashed target plan.

#### 3. Solution & Architectural Strategy

Extend `.gitattributes` with `-text` for the dated research CSV/JSON bundles and specifically hashed scripts/target plan. Renormalize only the affected research files into their verified original bytes, then compare staged Git blob hashes with all 30 manifest input/output/builder checks before commit. Preserve source evidence and logical data: 819 wet observations, 37 conditional projections and zero training admission remain unchanged.

#### 4. Files Modified / What Changed

- `.gitattributes`: explicit byte-preservation patterns for hashed research artifacts.
- Existing dated Pasig research inputs: stage their original verified bytes instead of newline-normalized equivalents; no row/value or label-admission change.
- Qualification/follow-up evaluation notes record the reproducibility constraint. Commit/push outcome is reported separately after Git completes.

### [BUG-101] City aliases escape as barangays and news previews hide hazard gaps

- **Status:** Code/preview defects, C5/Pasig route coverage and twenty-barangay Pasig community preview provisioning resolved locally; omitted administrative areas and operational footprints remain pending.
- **Severity:** High — blocks qualified locality placement and misrepresents disconnected modeled road pieces.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

`C5 in Pasig City` could set canonical barangay to `City of Pasig`. Named barangays had no supported polygon loader. Placement returned whole candidate centerlines and NOAH lengths; the blue dashed map treatment could not express separate modeled intersections.

#### 2. Root Cause Analysis (RCA)

A shared alias map includes cities and barangays; normalization returned alias targets without validating level/parent. OSM also tokenized C5 and C-5 differently, and the article city could be misread as an ungrounded landmark. Barangay metadata was rejected unconditionally in the OSM provider. NOAH intersections were reduced to lengths, and the preview hook rendered candidate centerlines.

#### 3. Solution & Architectural Strategy

Validate aliases against actual barangays/exact parents; retain qualified barangay context. Load reviewed checksummed polygons and clip only within supported administrative geometry. Return source-identified disconnected intersection fragments and dissolved modeled display geometry without bridging gaps. Reuse shared pending aura styles, with reported depth controlling severity and unknown depth staying neutral. Preserve read-only/current-flood/routing gates and prior extraction history; new processing identity is v11.

**Earlier source-coverage probe (before route-relation enrichment):** C5/C-5 aliases now match, but all 85 indexed ways under those names lie outside the checked Pasig polygon. The constructed city-only C5 probe therefore returns `named_road_sections_not_found`; the Ugong probe returns `missing_valid_barangay_boundary`. Reviewed OSM alias/road coverage and real polygon assets must be provisioned before these cases resolve. A separate constructed C. Raymundo probe produced 25 candidates/141 modeled fragments, with disconnected display geometry on 13 candidates; this establishes preview behavior, not current flood confirmation or routing eligibility.

**Subsequent coverage repair:** the same September 27 PBF now contributes explicit C5 road-route relations 417210/14448353, resolving 45 Pasig member ways and 14 ambiguous sections without renaming original roads. Read-only asset checks, parent mismatch reasons and immutable provisioning tooling are delivered; the later same-snapshot OSM community review packages twenty Pasig polygons including Ugong with explicit automated-review and ODbL provenance. Ten barangays remain omitted; no human/official/legal/field extent is claimed. GeoRisk requires a token and the old Pasig atlas lacks Ugong/has parent/licensing limits, so neither alternative was installed. The C5/Ugong probe has thirteen clipped candidates/250 modeled fragments, eleven disconnected previews and zero linework outside Ugong; no operational footprint is claimed. [Current verification](../evaluations/phase-36-independent-evaluation-and-spatial-coverage.md).

#### 4. Files Modified / What Changed

- Backend: `philippine_location_service.py`, `taglish_extraction_service.py`, new `barangay_boundary_service.py`/`placement_geometry_service.py`, road matching/context/placement/NOAH services, extraction/placement Pydantic contracts and processing version.
- Coverage follow-up: `backend/scripts/build_news_osm_catalog.py`, bundled `runtime_data/osm/roads.json.gz`/`manifest.json`/README, `news_road_placement_service.py` and `barangay_boundary_service.py`; new `scripts/audit_news_spatial_assets.py`/`provision_news_barangay_catalog.py`/`build_news_barangay_catalog.py`, `runtime_data/barangay/` catalog/review/provisioning receipts and spatial-asset tests preserve explicit relation provenance, safe coverage failures and immutable provisioning.
- Frontend: `reviewApi.ts`, `useNewsPlacementLayer.ts`, `NewsReviewEvidence.tsx`; browser fixtures now carry disconnected preview geometry.
- Tests: extraction, new `test_barangay_placement.py`, placement regressions and existing spatial browser flows. 226 backend checks and 14 browser cases pass; TypeScript/lint pass. [Evaluation](../evaluations/phase-36-disconnected-news-placement.md).

### [BUG-100] Local Docker startup fails on stale Windows Unix sockets

- **Status:** Local startup recovered; upstream cause and recurrence prevention unverified.
- **Severity:** High — blocks native PostGIS/migration verification.
- **Author/Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7, 6:29 PM recurrence:** Starting Docker for the live-news audit reproduced the user-reported `sailor-ingest.sock` access/rename failure. Stop identified crashed Docker processes, verify their exit, preserve both inspected socket directories as `run.lanes-audit-backup-20261007-182011` and `docker-secrets-engine.lanes-audit-backup-20261007-182011`, recreate the runtime directories and start once. Engine 29.8.0 and the original PostGIS/Valhalla containers resume; 131 native lifecycle tests then pass in a separate disposable database. No original volume/database reset; recurrence prevention remains unverified. [Audit](../evaluations/news-live-operational-audit-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Docker Desktop 4.91.0 failed to start with Windows file-access errors when renaming `Docker/run/sailor-ingest.sock`, then `docker-secrets-engine/engine.sock`. Restarting only the second folder encountered a new stale ingest socket left by the preceding failed launch. Database/Valhalla services were initially unavailable.

#### 2. Root Cause Analysis (RCA)

Local runtime entries were zero-byte Archive/ReparsePoint socket objects. Docker's startup could not rename them. Exact kernel/filesystem cause is not established; the symptom and multi-listener sequence match a first-hand [Docker issue](https://github.com/docker/desktop-feedback/issues/554). This is an environment failure, not a LANES schema or service defect.

#### 3. Solution & Architectural Strategy

Stop Docker Desktop with its CLI and verify Desktop/backend processes exit. Verify exact absolute target directories and that their parents are ordinary directories. Preserve both socket directories under unique backup names, recreate both runtime folders, and launch once. The existing PostGIS and Valhalla containers then appeared in `docker ps`; 60 focused backend/storage checks passed. No factory reset, uninstall, Docker volumes/data removal, WSL distro deletion, cloud action or secret-content read. Backup socket objects remain preserved; a permanent upstream fix is not claimed.

#### 4. Files Modified / What Changed

No LANES application file was changed to repair Docker. Runtime folders `C:/Users/roicambe/AppData/Local/Docker/run` and `C:/Users/roicambe/AppData/Local/docker-secrets-engine` were recreated. Preserved backups: `run.stale-20261005-8c9d325c`, `run.stale-20261005-d134ed73` beneath `Docker`; `docker-secrets-engine.stale-20261005-dddafe6a` and `docker-secrets-engine.stale-20261005-12fd9ecd` beneath Local AppData. [Storage and recovery evaluation](../evaluations/phase-36-news-publication-storage.md).

---

### [BUG-099] Offline duration pilot mishandles spaced list numbering and conflicting alternate units

- **Status:** Resolved for captured official-page formats in collector v3, with separate offline replay and source qualification. Original v2 snapshots and reviewed v1 overlays remain preserved.
- **Severity:** Research data-quality defect; no application writes
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
- **Evidence / cause:** The August 29, 2026 20:30 source contains `5 . Caliwag St.`; the old numbered-item pattern missed the location and reused the preceding pending row for its depth. Alternate values such as `12.7 cm (6 inches)` were reduced to the first unit without an inconsistency flag.
- **Change:** `backend/scripts/collect_flood_duration_pilot.py` v2 accepts spaced numbering, compares alternate units with a conservative 0.25 cm tolerance, preserves raw values and leaves conflicting canonical depths blank. Unsupported later bullet lists become explicit review exceptions. Original captures remain immutable.
- **Evidence after rebuild:** Caliwag is present under its own location; 16 unit-disagreement rows, 14 unsupported bullets and two same-clock depth-conflict entries are retained in the expanded pilot. Saved source text and selected derived records were inspected. No automated tests were added or run. See [pilot report](../evaluations/flood-duration-pilot-20261004/README.md).

#### October 5 source-qualification follow-up

**Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

1. **Problem:** A. Policarpio's consistent 2–3 in / 5.08–7.62 cm range was falsely flagged and its San Joaquin heading lost. Fourteen 20 cm / 8 in rounded pairs were withheld by the strict tolerance. Two Metroville 10.64cm / 4 in disagreements were missed. Wet evidence remains supported in each case.
2. **Root cause:** `depth_bounds` reads only the first scalar in a repeated-unit metric range; heading extraction requires Brgy/Barangay prefixes; the alternate-unit detector's `\bcm\b` misses digit-adjacent `10.64cm`. The 0.25 cm tolerance classifies a plausible 0.32 cm whole-number conversion rounding as disagreement. Source Kabutihan 12.7 cm / 6 in remains an actual unresolved conflict.
3. **Strategy/status:** Preserve original parser outputs/captures and apply explicit reviewed feature overrides in a separate versioned qualification layer: A. Policarpio range/barangay restored, 14 source-reported metric features tagged with rounding uncertainty, three genuine unresolved unit conflicts blank in qualified numeric fields. These evidence-specific overrides do not repair the general collector parser or establish model outcomes. General extraction repair was pending at this v1 review; the v3 repair below now addresses the captured formats.
4. **Files changed:** new `backend/scripts/qualify_pasig_duration_data.py`, `docs/evaluations/pasig-duration-qualification-20261005/review_rules.json`, derived review CSVs/manifest/report and synchronized plan/progress/index. Original collector, capture files and base CSVs are unchanged. [Qualification evidence](../evaluations/pasig-duration-qualification-20261005/README.md#observation-corrections-and-unresolved-features). No application tests, new dependency, schema or training change.

---

#### October 5 general collector repair and follow-up integration

1. **Observed cause:** Repeated-unit ranges and numeric-adjacent unit tokens were mishandled; the San Joaquin/plain Sta. Lucia headings and singular foot were missed. No-space `4.Rosario` could reuse an emitted Morales row; repeated punctuation `29..` needed preservation. Maybunga source qualifiers polluted the canonical name. Whole-centimeter rounding needed a separate uncertainty category.
2. **Resolution:** Collector v3 handles supported ranges/units/headings/numbered formats, canonical qualifiers and pending-row reuse; preserves raw evidence and blanks genuine conflicting numerical conversions. Add offline `--source-bundle` replay and standard-library `--skip-figures`; original captures/outputs remain untouched. The merged builder preserves old raw fields, exposes parser overlays, labels 68 new qualitative depths correctly and follows existing timeline/snapshot hash conventions.
3. **Evidence:** Original replay retains all 398 claim identities/location/evidence/clocks and 37 bounds, with 33 exceptions. Eight new captures produce 352 unique source-verified wet observations, no false duplicates and supported multi-clock frames. Independent review plus the builder checks original 467 rows, 35 source identities and 70 artifact hashes. No automated tests, dependencies, application schema or runtime changes.
4. **Files:** `backend/scripts/collect_flood_duration_pilot.py`, new `backend/scripts/build_pasig_duration_followup.py`, and [versioned exports/source-review report](../evaluations/pasig-duration-followup-20261005/README.md). **Resolver:** ([@roicambe](https://github.com/roicambe) (Roi Cambe))


### [BUG-098] Dormant news auditor uses the wrong credential provider and omits article context

- **Status:** Resolved locally for independent auditing and leased evaluation; live provider/model acceptance and automatic publication remain pending.
- **Severity:** High when connected to automatic publication; completed extraction remains independent.
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The old independent audit could send a Google credential to OpenRouter, inspect only one sentence and accept a positive response without structured place/time confirmation. It missed article-wide clearance/conflict evidence. Original reproduction used mocked transport; no live credential/request or publication was performed.

#### 2. Root Cause Analysis (RCA)

`HybridExtractionService.audit_claim_with_llm` selected `OPENROUTER_API_KEY or GEMINI_API_KEY`, always used the OpenRouter endpoint and omitted complete immutable article context. The legacy result lacked explicit place/time evidence. The dormant ingestion prototype also lacks durable publication identity/finite expiry and remains unsuitable for live activation.

#### 3. Solution & Architectural Strategy

Delegate hybrid auditing to a dedicated adapter with explicitly configured provider/model/config revision, provider-specific credential transport and no credential fallback. Send complete bounded immutable article evidence beneath trusted instructions, validate strict place/status/time/depth/access dimensions and exact quote offsets, and keep modeled placement/status predictions out of independent evidence. Unavailable, malformed, conflicting and unsupported responses remain safe review/failure outcomes.

Bind completed extraction using immutable input/claim hashes and ordinal identity, then evaluate through separate bounded seed/evaluate commands under leased ownership in the approved tables. External requests occur after lease commit; retries/config revision recovery preserve immutable failed history. Recheck freshness/admission at completion, surface safe errors and create no decisions, reports, zones or routing effects. [Verification](../evaluations/phase-36-independent-evaluation-and-spatial-coverage.md), [operator guide](../guides/news-claim-evaluation.md).

#### 4. Files Modified / What Changed

- `backend/app/services/news_claim_auditor.py`, `backend/app/schemas/news_audit.py`: provider adapter and strict independent evidence contract.
- `backend/app/services/hybrid_extraction_service.py`, `backend/app/schemas/news_extraction.py`: safe delegation/projection; extraction stays independent.
- `backend/app/crud/news_evaluation.py`, `backend/app/services/news_evaluation_service.py`, `backend/scripts/evaluate_news_claims.py`: immutable source binding, leased evaluation and explicit bounded handoff.
- Auditor/evaluation/hybrid/passability/native PostgreSQL regressions exercise transport, evidence, concurrency, lost leases, retries/config recovery, admission and no public/domain writes. No new schema/dependency, endpoint, frontend integration or deployment.

---

### [BUG-097] Primary Panel duplicates report/zone presentation and omits group context

- **Status:** Resolved locally; developer visual acceptance pending
- **Severity:** Low (administrator context and UI consistency)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Needs Review cards emphasize the anchor road but do not summarize grouped cities/barangays, conflicting severity/depth or latest evidence. The Primary Panel lacks location/search organization for large queues. Pending evidence and published zones use separate detail layouts and inconsistent button heights.

#### 2. Root Cause Analysis (RCA)

Queue previews previously hydrate only three members and expose no all-member location/condition summaries or search facets. Report and zone panels duplicate badge, fact and action markup, with unconditional 44 px report actions versus 28 px zone actions. The unused legacy pending-panel trust selector implies filtering that is not implemented.

#### 3. Solution & Architectural Strategy

Read existing queue facts in the backend, group under the unchanged spatial/time policy, match all criteria against any one member, retain complete canonical groups and paginate afterwards. Return city-scoped facets and all-member summaries, keeping global source counts distinct from filtered card/record counts. Reuse existing locality normalization for city aliases. The UI preserves source colors and the detail-based Related reports list, shares a flat record summary, removes unused legacy frontend filter controls, and uses shared small buttons with 44 px touch minimums. Contributor map inspection/restore is keyboard-accessible; report actions still target each original report.

#### 4. Files Modified / What Changed

- `backend/app/crud/spatial_review.py`, `schemas/spatial_review.py`, `services/spatial_review_service.py`, `api/v1/endpoints/admin_review.py`: existing-data summaries, validated protected filters, facet and count contracts; no model/migration/publication writes.
- `frontend/src/features/admin/components/FloodRecordSummary.tsx`, `ZoneContributors.tsx`, `PendingReportsPanel.tsx`, `ActiveZonesPanel.tsx`: shared presentation, useful facts and compact/touch-aware actions.
- `frontend/src/features/admin/review/{NeedsReviewPanel,ReviewQueueCard,RelatedReviewReports,NewsReviewEvidence}.tsx`, `reviewApi.ts`: filters, contextual cards and consistent action sizing.
- `backend/tests/test_spatial_review.py`, `frontend/tests/spatial-review.spec.ts`: 300-record search, intact cross-boundary groups, validation/zero results, filter retention, narrow/landscape bounds and independent zone actions.

[Verification](../evaluations/phase-36-needs-review-inspection.md#october-4-primary-panel-search-and-detail-consistency).

### [BUG-096] Cross-boundary flood growth lacks a consistent review and extension workflow

- **Status:** Resolved in the reviewed roi-branch checkpoint; developer acceptance and production rollout pending
- **Severity:** Medium (candidate visibility and preservation of existing zone coverage)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The developer identified that an expanding flood can cross streets/barangays and may need to extend an existing zone. Current display grouping excludes known different barangays and different normalized road names. Existing merge actions do not consistently mean geographic extension.

#### 2. Root Cause Analysis (RCA)

The inspection grouper uses administrative/road labels as hard conditions, while actual merge suggestions award locality points rather than imposing a barangay boundary. `find_merge_candidates` queries nearby pending reports, not active zones, despite its broader docstring. `/zones/{id}/merge-pending` links supporting evidence without changing coverage. `/reports/merge` assigns the submitted final polygon to the target zone; selecting an existing destination does not itself union its old boundary into that payload. `MergeWorkspacePanel` initializes the final geometry from the primary report. Road synthesis projects endpoints onto the longest submitted line, which cannot reliably extend past that baseline or represent connected branches.

This is primarily a workflow/geometry gap: `FloodEvent.locations`, `reports` and `zones` already support multiple affected places and sections, and `link_supporting_report` records each report's road/barangay/city. The Phase 33 design explicitly supports multi-road/cross-barangay incidents.

#### 3. Solution & Architectural Strategy

Implemented server-owned boundary-crossing review without automatic incident merging. Same-road/same-city grouping allows 500 m; different roads/cities use 50 m; pairwise report time remains two hours and complete-link grouping prevents chains. Active event-owned zones within 500 m are suggested independently of the original event age. The admin explicitly chooses extension, evidence-only corroboration, or a separate section of the same event. Shared PostGIS preview/publication unions existing coverage and road cores during extension, buffers all reviewed road branches in projected metres, rejects points/invalid/disconnected coverage, and preserves original evidence. Legacy approval also preserves old coverage; batch merge remains corroboration only. Publication, moderation outcomes and audit commit together. Existing event location/zone tables handle multiple places and different per-section conditions; no schema/dependency change.

#### 4. Files Investigated / What Changed

- Changed `services/spatial_review_grouping.py`, `services/merge_service.py`, new `services/flood_zone_growth_service.py`, `api/v1/endpoints/admin.py`, `crud/audit.py`, request/response schemas, frontend `adminApi.ts`, `MergeWorkspacePanel.tsx` and the mobile drawer placement in `LiveMapPage.tsx`.
- Added native local PostGIS/API rollback-isolated growth tests and desktop/mobile review-action regressions. Existing database containers were restored after Docker runtime socket failures; no volumes or databases were reset.
- Verification and remaining limits: [implementation evaluation](../evaluations/phase-36-needs-review-inspection.md#october-4-cross-boundary-growth-implementation). Actual report #2/#3 coordinates/incident membership are not present in the dedicated test database and remain unverified.


### [BUG-095] Map selection retains another queue card's related reports

- **Status:** Resolved locally; native database verification pending
- **Severity:** Medium (incorrect report relationships in inspection)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Selecting #2 or #4 shows the other report, but selecting #3 on the map can show both #2 and #4. The screenshots label #3 Rosario and #2/#4 Maybunga.

#### 2. Root Cause Analysis (RCA)

`NeedsReviewPanel.openedGroup` changed only when a queue card was clicked. `LiveMapPage.selectQueueReportFromMap` selected new evidence without updating that group. The previous card's members therefore remained below an unrelated report. The member endpoint also resolved only the oldest-ID group anchor, preventing direct lookup by another selected member.

#### 3. Solution & Architectural Strategy

Remove retained card membership from the panel. Query the protected member endpoint by the selected report's identity; the backend resolves that identity's current group and returns its canonical key and grouping reason. Hide the related section for singleton groups, preserve pagination and individual actions, and retain existing locality/distance/time rules. Known different barangays remain separate even when nearby; this fix does not change merge eligibility. Regression verification is recorded in the [evaluation](../evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-selected-report-group-resolution). A guarded read-only attempt against the dedicated local PostGIS test database timed out; exact real distances and live membership remain unverified.

#### 4. Files Modified / What Changed

- `backend/app/services/spatial_review_service.py`, `schemas/spatial_review.py`: resolve members by any current identity and return the server grouping reason; no database model/migration change.
- `frontend/src/features/admin/review/NeedsReviewPanel.tsx`, `RelatedReviewReports.tsx`, `reviewApi.ts`: selected-identity member query, no retained queue-group fallback, singleton hiding and explicit read failure/retry.
- `backend/tests/test_spatial_review_grouping.py`, `frontend/tests/spatial-review.spec.ts`: reciprocal lookup, different-barangay exclusion, non-anchor pagination and map/external selection regressions.

### [BUG-094] Needs Review flattens related reports and lacks source card styling

- **Status:** Resolved locally; actual database grouping/developer acceptance pending
- **Severity:** Medium (queue readability and repeated location rows)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Developer screenshots show three nearby Dr. Sixto Antonio reports as separate plain rows. User and news sources have text labels but little visual separation compared with existing report details.

#### 2. Root Cause Analysis (RCA)

The combined reader originally paginated individual identities, and its row renderer omitted the previous report card's background/measurement presentation. Grouping only the returned frontend page would split related reports at page boundaries. Calling the full merge engine on each polled card would also perform road tracing and geometry synthesis.

#### 3. Solution & Architectural Strategy

Group eligible pending user metadata in the backend before card pagination, reusing merge road normalization and conservative same-locality, pairwise 500 m/two-hour rules. Keep all original evidence and conflicts. Distinguish light blue user groups and light violet independent news cards; open report details for the related list and individual actions, and paginate larger member sets through a protected read. The developer requested the queue dropdown be removed; related reports now appear inside evidence. Actual merges remain explicit. 95 backend checks and 18 distinct current browser checks pass; TypeScript/scoped lint pass. [Evidence](../evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-related-cards-and-source-styling).

The subsequent related-detail presentation originally used compact links and duplicated the selected report. The developer requested the existing full report layout throughout. Related members now use protected full-detail reads and the same `PendingReportsPanel`, with individual actions and no duplicated selected row. Approving/rejecting another member preserves the current detail. [Follow-up](../evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-consistent-related-report-layout).

#### 4. Files Modified / What Changed

- `backend/app/crud/spatial_review.py`, `services/spatial_review_grouping.py`, `services/spatial_review_service.py`, `schemas/spatial_review.py`, `api/v1/endpoints/admin_review.py`: compact metadata, grouped card/member contracts, projected geometry and bounded evidence reads; no schema/migration writes.
- `frontend/src/features/admin/review/ReviewQueueCard.tsx`, `NeedsReviewPanel.tsx`, `reviewApi.ts`, `LiveMapPage.tsx`: source styles, measurements, expansion, error/focus preservation and moderation cache refresh.
- `backend/tests/test_spatial_review.py`, `test_spatial_review_grouping.py`, `frontend/tests/spatial-review.spec.ts`: auth, exclusions, anti-chain bounds, conflicting measurements, pagination and desktop/mobile coverage.

### [BUG-093] Spatial Operations mobile map switching fails in touch landscape

- **Status:** Resolved locally; developer visual acceptance pending
- **Severity:** Medium (map and evidence workspace visibility)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

During Needs Review integration, touch landscape could display both the sidebar and map, or hide the return control despite selecting the mobile map workspace. Narrow layouts also required explicit overflow checks.

#### 2. Root Cause Analysis (RCA)

The JavaScript mobile test included coarse pointers and a 640px breakpoint, while Tailwind desktop classes started at 768px. Unconditional `md:flex` and `md:hidden` overrode mobile visibility on landscape touch devices.

#### 3. Solution & Architectural Strategy

Align the viewport threshold to 768px and use the same responsive state for the primary sidebar/map and mobile controls. Preserve the mounted map and drawing sessions. Browser checks cover a 320px evidence viewport, 844×390 touch landscape switching, and desktop inspection. [Verification](../evaluations/phase-36-needs-review-inspection.md).

#### 4. Files Modified / What Changed

- `frontend/src/features/admin/LiveMapPage.tsx`: consistent responsive layout, Map/Evidence visibility and 44px controls.
- `frontend/tests/spatial-review.spec.ts`: narrow/landscape overflow and workspace-switching coverage.

### [BUG-092] News details overstate depth and attach unrelated province labels

- **Status:** Resolved locally in v9/v1.7; production release pending
- **Severity:** High for misleading source/location facts
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The four-article re-audit found gutter-only observations displayed as measured numbers, an approximate depth displayed as exact, two explicit generally passable corridors displayed as unstated, four Metro Manila roads labeled with unrelated provinces and clearance clocks labeled as flooding observations.

#### 2. Root Cause Analysis (RCA)

Presentation preferred normalized gauges to raw measurements. No claim value represented general passability without vehicle classes. Geometry ranking preserved a homonym's province after accepting a different grounded parent city. Time labels used observation kind without considering cleared condition or the source's by bound.

#### 3. Solution & Architectural Strategy

Prefer raw reported depth with legacy formatted fallback. Add delegated/approved `passable_unspecified`, bounded same-paragraph evidence and an explicit no-closure guard. Derive parent province/island together from grounded city/PSGC. Label resolved clearance observations by status and bound. Preserve previous snapshots/runs, exclusion policy and unknown facts. 595 tests and final 38-detail database/API parity pass. Caption-provenance explanations remain an open refinement, with no caption promotion. [Audit](../evaluations/phase-36-four-article-source-audit.md).

#### 4. Files Modified / What Changed

- `backend/app/services/news_presentation_service.py`, `backend/app/schemas/news_presentation.py`: source depth, passability, clearance and exclusion labels.
- `backend/app/schemas/news_extraction.py`, `taglish_extraction_service.py`, `hybrid_extraction_service.py`: unspecified vehicle passability and safety guard.
- `backend/app/services/nationwide_geometry_service.py`: grounded parent-field consistency.
- `backend/app/crud/news_processing.py`: v9 identity; extractor is v1.7.
- New depth-presentation, generic-passability and geometry-parent tests; existing summary expectation updated to source wording. Affected core records, evaluation and runbook synchronized. No model/migration/dependency or frontend source changed.

### [BUG-091] Collection timing and unchanged RSS can miss current publisher updates

- **Status:** Investigating; refresh policy and production schedule unchanged
- **Severity:** High for the intended near-real-time news workflow
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

An article may change from flooded to subsided while RSS title/excerpt/publication remain identical. Discovery reuses stored text or receives no entries on HTTP 304. It never sees the edit. Production Scheduler inspection confirms collection every three hours; minute-scale extraction retry due times do not start a worker themselves.

#### 2. Root Cause Analysis (RCA)

RSS metadata/checkpoints are used as article-body freshness signals. There is no independent bounded body revisit or publisher retrieval-retry queue. Scheduler launch retries differ from extraction and publisher retry. News itself can also lag actual conditions.

#### 3. Solution & Architectural Strategy

Document actual timing and distinguish retry from refresh. The developer questioned the hourly/24-hour proposal; it remains unapproved. Agree on discovery/update latency, publisher request limits, retry bounds and stale-observation behavior before changing code or production scheduling. [Evidence](../evaluations/phase-36-news-workflow-follow-up.md#freshness-investigation-open-unchanged).

#### 4. Files Modified / What Changed

Evaluation, task plan and system/progress records only for this timing finding. Read-only `gcloud scheduler` list/describe inspection; no scheduler, source registry or retrieval interval changed.

### [BUG-090] Existing news workflow mixes facts and drops publisher corrections

- **Status:** Resolved locally in v8/v1.6; production release pending
- **Severity:** High (stale/misleading flood facts and hidden retrieval issues)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Caution became unrestricted passability; independently conjoined roads shared the wrong depth/clock; bare narrative retained a list time. Successful publisher denials or changed-city corrections were rejected and left older active evidence current. Failed refreshes with newer pending/failed extraction, or after a denial, disappeared from Collection attention. UI exposed a permanently empty filter and omitted structured passability from details.

#### 2. Root Cause Analysis (RCA)

Claim enum lacked caution; conjunction/list rules lacked independent-predicate scope. New-article admission rules were also applied to existing publisher corrections. Failed-refresh visibility considered only current/latest evidence, ignoring credible history. Frontend options/facts lagged backend behavior.

#### 3. Solution & Architectural Strategy

Use the explicitly approved caution category with source provenance and a no-automatic-closure guard. Preserve independently stated road facts while keeping shared qualifiers/subjects together. Version successful corrections and retain immutable old history; keep new irrelevant stories excluded. Use current-or-history recognition for failed fetch diagnostics and Collection attention without reviving old main rows. Add backend-owned passability labels and remove the dead UI option. All 452 related backend tests, TypeScript, scoped lint and 33-site private API/source checks pass. No database migration, dependency, deployment or current-zone creation. [Evaluation](../evaluations/phase-36-news-workflow-follow-up.md).

#### 4. Files Modified / What Changed

- `taglish_extraction_service.py`, `schemas/news_extraction.py`, `hybrid_extraction_service.py`, `crud/news_processing.py`: scoped facts, explicit caution/guard and v8/v1.6 identity.
- `news_discovery_service.py`, `crud/news_collection.py`: existing corrections, credible-history diagnostics and attention state.
- `schemas/news_presentation.py`, `news_presentation_service.py`, frontend `newsApi.ts`, `NewsResultDialog.tsx`, `NewsCollectionDrawer.tsx`: server passability labels, shared responsive details and selectable statuses.
- New passability/correction/Collection tests; extended September 9 tests and source-supported caution expectations. Affected evaluation/core/runbook records are synchronized.

### [BUG-089] Multi-location September 9 reports lose sites and scoped facts

- **Status:** Resolved locally in v7/v1.5; production release pending
- **Severity:** High (missing observations and incorrect temporal/context attribution)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Three September 9 reporting bodies expose an omitted depthless list road, missing Blumentritt, missed singular vehicle-passability wording, unresolved afternoon clocks in a morning-published/afternoon-updated article, and missing road/barangay separation. Regression review also finds forecast/drill headings lost on measured rows and list clocks leaking into short independent narrative roads. The local test server loses its socket on Windows auto-reload and leaves an empty API served at the local address.

#### 2. Root Cause Analysis (RCA)

Street, qualifier and passability rules omit source forms; row-local evidence ignores a credible list introduction. Clock anchoring only knows original publication. List scope lacks inherited non-observation flags and treats short finite-verb narrative as telegraphic entries. The local reload child fails while reconstructing its inherited socket.

#### 3. Solution & Architectural Strategy

Retain exact source offsets and contiguous list provenance; validate barangays against parent-city PSGC; parse coordinated roads and explicit singular passability. Use the approved narrow GMA-only matching publication/update header without changing publication or schema. Carry disqualifying context through rows, reset at independent narrative, and leave unsupported facts unknown. Version to v7/v1.5 and retain immutable earlier runs. Disable auto-reload only in the private replay launcher; restart explicitly after edits. All 410 related tests and 33 audited source locations pass. Actual authenticated API/frontend proxy details match. Browser verification is separately blocked by saved permission policy. [Evaluation](../evaluations/phase-36-september9-production-day-replay.md).

#### 4. Files Modified / What Changed

- `backend/app/services/taglish_extraction_service.py`: road/PSGC/passability parsing, scoped evidence, observation anchor and narrative/non-observation boundaries.
- `backend/app/services/news_evidence_policy.py`: affirmative affected-road/area wording shared by SQL and readers.
- `backend/app/crud/news_processing.py`: v7 identity.
- `backend/scripts/replay_september9_news.py`: guarded captured-body/reconstructed-RSS replay, private persistence and idempotence verification.
- `backend/tests/test_news_september9_extraction.py`, `test_news_september9_replay.py`, `test_news_temporal_scope.py`: conservative attribution, update/header guards, history/isolation and temporal scope regressions.
- `backend/start-local-news-test.ps1`: stable loopback worker without Windows auto-reload.
- Evaluation, local guide and affected core records: exact evidence, source audit and remaining acceptance/recommendations. No schema, dependency, frontend or production change.

### [BUG-088] City summaries appear as additional flood sites beside street details

- **Status:** Resolved locally in v6/v1.4; production release pending
- **Severity:** Medium (redundant admin flood cards and confusing missing-street details)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The September 24 replay shows a broad Mandaluyong card followed by the specific Boni/F. Ortigas report, and a broad Quezon City summary beside East/Aurora reports. Seven readable mentions appear to be seven separate flood sites; the broad cards have no street or observation clock.

#### 2. Root Cause Analysis (RCA)

Same-sentence city qualifiers were already marked context only. Standalone summaries in another paragraph remained separate observations because extraction lacked reconciliation across the article. Streets were correctly extracted; their city summaries were counted again.

#### 3. Solution & Architectural Strategy

Reconcile city summaries against credible specific observations in that same resolved city after per-sentence extraction. Retain summaries as `location_context_only`, preserving original evidence/offsets and each street's facts. Keep city-only reports, different cities, explicit different times and cases where the specific evidence is speculative, caption-only, ambiguous or conflicting. Version the correction and reprocess into a new immutable local run. Actual authenticated API/browser show five street cards and zero attention items; 224 related backend tests pass. Production data/releases remain unchanged.

#### 4. Files Modified / What Changed

Updated `taglish_extraction_service.py` reconciliation/extractor version, `crud/news_processing.py` pipeline identity, local seeder expectations and replay regressions. Existing SQL readability/Collection gates exclude context without new frontend filtering, models, migrations or dependencies. Updated the existing evaluation/runbook and core documentation. The known local backend stalled during auto-reload and was restarted using its guarded loopback launcher before real page verification.

### [BUG-087] Docker runtime socket errors block the private local replay

- **Status:** Resolved on this computer; no factory reset
- **Severity:** High (local PostgreSQL unavailable; testing blocked)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Docker Desktop 4.91.0 could not rename `sailor-ingest.sock`, then Secrets Engine `engine.sock`, with Windows error 1920. The Linux engine pipe was unavailable. Separately, the original historical replay used isolated in-memory storage, so the normal page had no saved test article.

#### 2. Root Cause Analysis (RCA)

Windows could not access Docker's runtime socket objects. Resolving only one directory permitted startup to reach another failed socket; each failed start left additional unusable objects. The precise underlying OS/Docker cause is not established. The empty LANES page was a storage-scope mismatch, not evidence that successful extraction had been saved to its database.

#### 3. Solution & Architectural Strategy

Stop Docker completely, preserve both socket directories as recoverable backups and start with fresh runtime directories. The original containers/volumes resumed. Create separate `lanes_news_test`, apply existing migrations, seed the actual historical evidence using existing processing services and run local frontend/backend with ignored environment overrides. Authenticating against the separate local database makes seven locations/five roads visible. Replays are idempotent and create no zones. All 29 focused tests pass. Production and the original local database remain preserved. [Operational details](../guides/local-news-replay.md).

#### 4. Files Modified / What Changed

Added `backend/scripts/seed_local_news_replay.py`, `backend/tests/test_local_news_replay.py`, loopback launchers in backend/frontend, ignored `backend/.env.test.local` and ignored captured source data. Added the local replay guide and updated evaluation/progress/task/system references. Runtime directory backups remain outside the repository. No SQLAlchemy model, Alembic migration or dependency was introduced.

### [BUG-086] Genuine September 24 flooding loses body paragraphs and per-road facts

- **Status:** Resolved locally; v5 release pending
- **Severity:** High (missed actual flooding and incorrect place/clearance attribution)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Replay the September 24 Daily Tribune flood event, published September 25. Regular retrieval produced only 182 characters and no flood claims. AMP retrieval exposed missing compound depths/intersections, false Manila agency-name matches, wrong city attribution, missed clearance times/states, lost adjacent passability and duplicate qualifiers. A regression additionally exposed Roxas Boulevard's unrelated barangay PSGC code.

#### 2. Root Cause Analysis (RCA)

The publisher streams its body after the article closes. Road/measurement/time patterns omit ordinary narrative forms. City context persists from an earlier paragraph and raw-name PSGC resolution can survive an explicit road parent-city override. Qualifier mentions were counted as independent sites or questionable claims. Existing tests did not cover this reporting structure.

#### 3. Solution & Architectural Strategy

Read only Tribune reporting containers; retain exact offsets and road qualifiers/directions; parse compound measurements and cleared/receded states. Resolve a sole recent explicit weekday through aware publication time while refusing ambiguous dates. Attach passability only to one immediately preceding road in the same paragraph. Use the explicit road parent-city PSGC code. Preserve context qualifiers without main/attention counts. v5/v1.3 preserve prior runs on later release. All 373 related tests pass (one disposable PostgreSQL migration skip), plus 19 PostgreSQL policy and 11 real-claim comparisons. No production writes/deployment or schema change. [Full evaluation](../evaluations/phase-36-september24-historical-replay.md).

#### 4. Files Modified / What Changed

- `backend/app/services/news_discovery_service.py`: streamed publisher body adapter.
- `backend/app/services/taglish_extraction_service.py`: evidence attribution, compounds, narrative road relations/directions, clocks, passability, qualifiers and PSGC identity.
- `backend/app/services/news_evidence_policy.py`: affirmative cleared/receded evidence.
- `backend/app/services/news_presentation_service.py`, `backend/app/crud/news_results.py`, `backend/app/crud/news_collection.py`: context explanations and matching SQL counts.
- `backend/app/crud/news_processing.py`: v5 pipeline identity.
- `backend/scripts/replay_september24_news.py`, `backend/scripts/audit_news_display.py`: real/offline replay and read-only PostgreSQL parity checks.
- `backend/tests/test_news_september24_replay.py`: 17 replay regression cases.

### [BUG-085] News Intelligence displays foreign floods and prevention projects as flood observations

- **Status:** Resolved and deployed, including the strict v4 collection follow-up
- **Severity:** High (misleading main-list content; unsafe input for planned automatic plotting)
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The developer reports foreign flood and flood-control content on News Intelligence. Read-only inspection of the configured database confirms 24 saved articles and nine local main-list claims: five QC prevention-project claims, three Bangkok claims, and one UP-PGH infrastructure-purpose claim. Pure local rules reproduce the extraction errors. The deployed API also returns 404 for the current frontend's `/api/v1/admin/news/results` route.

#### 2. Root Cause Analysis (RCA)

Explicit flood-control phrase suppression misses purpose/prevention and habitual descriptions. Main-list SQL and summary screening lack a Metro Manila grounding gate. Generic `interior` is incorrectly resolved to a Philippine barangay; captured publisher/related-content fragments add noise. Shortlisting changes do not invalidate existing stored artifacts. API/collector use the older `news-osm-20261002-v4-expat` image, while local reading code uses a later route. Scheduled rules/OSM services are used; optional LLM auditing remains disconnected. See the [full investigation](../evaluations/phase-36-news-content-quality-investigation.md).

#### 3. Solution & Architectural Strategy

**Collection follow-up (October 3):** block new unreadable bodies from candidate admission; require affirmative actual flooding instead of a bare topic word; screen forecasts, simulations, drills and habitual descriptions; exclude caption-only legacy claims. Completed zero-qualified extractions and unverified legacy leads now have an explicit `excluded` status outside default attention, preserving article/run history. All 341 backend tests, 15 PostgreSQL checks, TypeScript and 15 deployed desktop/mobile cases pass (API/session mocked). Matching v4 API/collector/frontend releases and saved/normal executions succeeded. Additional changes: `news_evidence_policy.py`, discovery/processing/extraction services, Collection CRUD/schemas/labels, `NewsCollectionDrawer.tsx`, `newsApi.ts`, read-only audit and article-screening/Collection/telemetry/Playwright tests. No model/schema/dependency changes.

Implemented shared observation/scope classification, real positive/negative regressions and a readable-body gate even for local RSS headlines. Main-list/Collection SQL screen evidence before counts and pagination; historical detail explains exclusions. Prevention and habitual flooding no longer establish active observations; generic interior/market words require a named spatial mention. Versioned processing preserves earlier artifacts. All 306 backend tests and eight read-only PostgreSQL checks pass; the nine false rows are excluded from the same 24 articles. The approved production migration, reprocessing and synchronized release succeeded.

#### 4. Files Modified / What Changed

**Release verified:** API `00048-xc7`, the same collector digest and Firebase frontend `build-2026-10-03-001` are live. Migration and corrective/normal collector executions succeed. Ten new v3 runs preserve 20 earlier runs and all 24 articles. Eight final PostgreSQL checks and 13 deployed desktop/mobile asset checks pass (API/session mocked). See [production evidence](../evaluations/phase-36-news-content-quality-investigation.md#completed-production-release).

- `backend/scripts/audit_news_display.py`: bounded read-only stored-claim trace and optional pure local rules comparison; no hybrid/HTTP/external AI calls or database commits.
- Investigation, documentation index, task plan and progress: record evidence, deployment mismatch and revised immediate priority.
- `news_evidence_policy.py`, Taglish extraction, discovery, results CRUD and presentation: shared evidence/geography gates and body-bypass correction; pipeline/extractor version bump.
- Extraction, discovery/results and desktop/mobile tests: real false-positive passages, positive retention, pagination/history parity and subpixel precision.
- Backend Docker/Firebase upload ignores: exclude environment credentials and local frontend artifacts from release uploads.
- No new schema or dependency was introduced by the content correction; the release uses the separately approved telemetry migration.

### [BUG-084] Windows Application Control blocks osmium during pipeline verification

- **Status:** Runtime import coupling resolved; Windows native PBF-reader restriction remains
- **Severity:** Low residual limitation (raw-PBF tooling on this Windows host)
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The October 3 automatic-plan audit ran five focused backend suites: 81 checks passed and 26 failed while importing the installed `osmium` native extension. This prevents confirming collection/processing/OSM regressions in the current local environment; it does not establish a production failure.

#### 2. Root Cause Analysis (RCA)

All 26 failures in the concise normal-access run report `DLL load failed while importing _osmium: An Application Control policy has blocked this file.` `article_road_match_service.py` imports `osmium`, and the operational road provider imports that matcher. Initial sandbox temporary-directory access errors disappeared on normal-access reruns, but the native-module policy block remained. No evidence identifies why Windows started rejecting this dependency or attributes it to telemetry code.

Read-only Windows Code Integrity event inspection confirms events 3033 and 3077 at October 3, 2:08:46 AM Philippine time. The process is Codex's bundled Python runtime; the rejected file is `backend/venv/Lib/site-packages/osmium/_osmium.cp312-win_amd64.pyd`. Windows reports that it does not meet Enterprise signing-level requirements (policy ID `0283ac0f-fff1-49ae-ada1-8a933130cad6`). This establishes an enforced native-extension signing-policy rejection during this invocation, not 26 independent application assertion failures. The log does not establish when/why the policy or trust decision changed, or whether another authorized runtime would have the same outcome.

#### 3. Solution & Architectural Strategy

The runtime provider already reads a validated JSON catalog and only needs the pure road graph/geometry routines. `article_road_match_service.py` unnecessarily loaded the native PBF parser at module import. Moved the existing native import and handler definition inside `load_bounded_osm_roads`, after bounding-box validation. The raw reader still requires the real dependency and propagates its import error; no substitute parser, fake geometry, suppressed errors or security-policy changes were introduced.

Post-fix verification: **140 passed**, including all original 107 checks plus road-placement, road-matching and NOAH-ranking checks. A fresh-process regression rejects all `osmium` imports, confirms the runtime catalog provider imports normally, and confirms raw-PBF reading still requires its native reader. Existing dependencies and schemas are unchanged. Local signature inspection reports the extension is unsigned; the blocking policy GUID is the built-in Smart App Control policy identified in [Microsoft's policy registry](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/inbox-appcontrol-policies). Raw-PBF tooling still needs a dependency accepted by the applicable policy; [Microsoft recommends valid publisher signing](https://support.microsoft.com/en-us/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions).

#### 4. Files Modified / What Changed

- `backend/app/services/article_road_match_service.py`: loads the native parser only for raw-PBF reading, retaining its existing filtering and bounded-reader behavior.
- `backend/tests/test_article_road_match_service.py`: adds the fresh-process native-dependency isolation regression.
- Evaluation, task/progress, feature/system references and documentation index: record the runtime fix, 140 passing checks and remaining raw-PBF restriction. No schema, dependency, UI or security-policy changes.

### [BUG-083] Source Article save date appears inconsistent with processing history

- **Status:** Resolved investigation; displayed dates verified correct for the reported article
- **Severity:** Low (date meaning is unclear; no timestamp corruption found)
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The BusinessWorld article "Thousands huddle in Bangkok shelters as Thai flood damages seen at $320 million" shows publication September 28, 2026, 5:09 PM and Saved in LANES September 28, 6:00 PM, while extraction history shows October 2. The developer questioned whether the save date was working.

#### 2. Root Cause Analysis (RCA)

Read-only queries against the dotenvx-configured database identify article #12. Its publication is `2026-09-28T09:09:39Z`; article and feed provenance independently record first collection at `2026-09-28T10:00:34.180964Z`. Immutable version #4 was created October 2 at 1:22 PM Philippine time. Runs #4 and #14 completed October 2 at 1:22 PM and 2:19 PM. Collection and extraction occurred on different days. The fallback local database contains different articles; it is not the database supplying this screenshot.

#### 3. Solution & Architectural Strategy

The result-detail service returns the article's `first_seen_at` as `saved_at`; article detail agrees. Executing the actual frontend `newsDate` formatter returns September 28 5:09 PM publication, September 28 6:00 PM first save and October 2 2:19 PM processing. UTC-to-Philippine formatting is correct. The save date means first collection, not extraction or copying into a local database. No timestamp correction is needed. A future wording refinement can use "First collected in LANES" to make this distinction explicit; no UI change is claimed in this investigation.

#### 4. Files Modified / What Changed

- `docs/others/bug-log.md`: records the reported article, stored evidence and formatter verification.
- No application, schema, dependency or stored data changes. All database queries used `SET TRANSACTION READ ONLY`; no browser or service was started.

### [BUG-082] Portalled Select escapes the news drawer's keyboard containment

- **Status:** Code fix implemented; developer keyboard/browser acceptance pending
- **Severity:** Low (keyboard interaction in the new drawer)
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Static review of Collection status finds that the shared Select renders options outside the drawer DOM. Escape reaches the enclosing dialog, and its focus trap excludes the option buttons.

#### 2. Root Cause Analysis

Select has no dropdown Escape handler; RecordDetailsDialog gathers focusable controls only beneath its own DOM ref. The portalled options are missing from that set.

#### 3. Solution & Architectural Strategy

Shared Select handles Escape in capture phase while open, closes only its dropdown and returns focus to its trigger. RecordDetailsDialog includes options for its own open shared Select in the focus cycle. Expanded state and a trigger marker identify the open control. TypeScript/lint and updated keyboard fixture cover the code contract; browser checks are prohibited by the developer, so interactive acceptance remains manual.

#### 4. Files Modified / What Changed

- frontend/src/shared/ui/forms/Select.tsx: Escape handling, trigger focus and expanded-state marker.
- frontend/src/shared/ui/feedback/RecordDetailsDialog.tsx: portalled option focus containment.
- frontend/tests/news-articles.spec.ts: dropdown Escape keeps the collection drawer open; fixture updated but not browser-executed.

### [BUG-081] Local Docker runtime cannot start the PostgreSQL engine

- **Status:** Resolved; Docker engine and existing PostgreSQL container recovered
- **Severity:** Medium (local development environment unavailable)
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

During F2 verification, configured local PostgreSQL returns an OperationalError and Docker has no Linux engine pipe. Docker Desktop starts but exits its engine initialization before the LANES database is available.

#### 2. Root Cause Analysis

The Docker backend first fails to rename `sailor-ingest.sock` in its runtime directory. After that directory is recreated, startup reports the same error against the separate Secrets Engine `engine.sock`. Their special reparse points return Windows error 1920, "The file cannot be accessed by the system," during individual inspection/deletion attempts. This matches the reported [Docker startup issue](https://github.com/docker/desktop-feedback/issues/554); the exact underlying Windows cause remains unverified.

#### 3. Solution & Architectural Strategy

Individual socket cleanup fails, but parent directory moves succeed. With Docker stopped, preserved `%LOCALAPPDATA%/Docker/run` and `%LOCALAPPDATA%/docker-secrets-engine` in timestamped quarantine directories and recreated clean runtime directories. The Secrets Engine directory was verified to contain only its two socket files. Docker then starts successfully; the existing PostgreSQL and Valhalla containers are running and PostgreSQL queries succeed. Container/database data was retained. The local database initially remained at `a83c1d4e7b92`; after separate explicit developer approval, existing extraction migration `f29b6c8d104e` applied successfully. Live authenticated F2 article/detail reads pass on desktop/mobile. No factory reset or model/migration definition change was needed.

#### 4. Files Modified / What Changed

- `docs/others/bug-log.md` and the F2 evaluation record the environment limitation.
- No Docker configuration, database model, migration or application authentication source was modified for this issue.

### [BUG-080] Existing AdminLayout fails current ESLint rules

- **Status:** Investigating; confirmed present in HEAD before F1
- **Severity:** Low (lint verification limitation; no demonstrated access regression)
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Running ESLint on the F1 changed-file set reports three errors in `frontend/src/features/admin/AdminLayout.tsx`: one `react-hooks/set-state-in-effect` error and two `@typescript-eslint/no-explicit-any` errors. New News Intelligence route/feature/test files pass lint; AdminSidebar has only its existing avatar-image warning. TypeScript and mocked desktop/mobile access/navigation checks pass.

#### 2. Root Cause Analysis

The existing mount effect calls `setIsMounted(true)` synchronously, and both existing role checks cast `user as any`. All three statements were verified in HEAD. F1 changes only the layout's responsive padding; these lint errors were not introduced by News Intelligence.

#### 3. Solution & Architectural Strategy

Address the mount/hydration pattern and typed session role access in a dedicated follow-up, preserving existing loading, redirect, staff roles and persistent-map behavior. Do not suppress rules or rewrite authentication while adjusting F1 presentation. No fix is claimed here.

#### 4. Files Modified / What Changed

- `docs/others/bug-log.md`: records the existing lint limitation.
- F1 source edits in `AdminLayout.tsx` affect padding only; its mount and role code is unchanged.

### [BUG-079] Linux OSM runtime lacked libexpat

- **Status:** Resolved; corrected Linux import, durable processing, and historical article matching verified
- **Severity:** High (new map-aware processing could not import its native reader)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The initial Priority 4 image passed API health but its production placement probe failed before processing with `ImportError: libexpat.so.1`. Windows-based matching tests had passed. Priority 3 extraction did not import the OSM reader and remained unaffected.

#### 2. Root Cause Analysis (RCA)

The declared `osmium` Linux wheel requires Debian's `libexpat1` runtime library. The slim backend image did not install it. API health does not execute the map-provider import, so it could not detect this native-library gap.

#### 3. Solution & Architectural Strategy

Restored traffic to verified API revision `lanes-api-00045-spg` and restored the Priority 3 collector image while rebuilding with `libexpat1`. Production placement/storage/idempotency verification must pass before this fix is closed. No schema rollback or public-data deletion is involved.

The corrected image is now active at API revision `lanes-api-00047-59t`. Production execution `lanes-news-discovery-lmvj5` passes native import, catalog validation, ten persisted map-aware runs, repeat idempotency, unchanged public counts, and actual historical GMA span matching. No failure remains open for this dependency.

#### 4. Files Modified / What Changed

`backend/Dockerfile` adds `libexpat1` to the existing apt installation; the Python package remains declared in `backend/requirements.txt`. Evaluation and tech-stack records capture the platform-specific release verification.

### [BUG-078] Fallback API fixture occasionally generated a future publication

- **Status:** Resolved; focused broad suite passes 135 cases
- **Severity:** Low (test clock/setup error; production future-date guard remains intact)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

One fallback API test intermittently expected a retrieved article but its fake publisher feed was rejected as future-dated. The first Priority 4 broad run had 133 passes and this one failure.

#### 2. Root Cause Analysis (RCA)

The fake feed sampled `datetime.now()` after the lookup had already captured its reference clock. Depending on clock resolution, its publication was slightly in the future. Its TestClient also unnecessarily booted database seeding/retention against the configured local database despite supplying a dedicated SQLite session.

#### 3. Solution & Architectural Strategy

The simulated feed publication now precedes lookup by one second, and the endpoint fixture uses an isolated no-op lifespan. Authentication, fallback retrieval, preserved original evidence, and table assertions stay intact. Production future-date validation was not changed.

#### 4. Files Modified / What Changed

`backend/tests/test_news_discovery.py` corrects only the fixture clock and startup isolation.

### [BUG-077] Backend container omitted extraction reference datasets

- **Status:** Resolved; production reference checksums verified
- **Severity:** High (location/history resolution differed from development)
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Production release preparation found that the extractor reads administrative and Pasig history CSVs from repository `data/`, while the backend-only image omitted that directory. Development tests saw local files, masking the runtime packaging gap.

#### 2. Root Cause Analysis (RCA)

Inside `/app`, both reference services resolve their repository data directory to `/data`. The prior Dockerfile copied only the backend context and `.dockerignore` excluded backend `data/`; absent files leave the providers empty. This is a packaging defect, not proof that earlier local article evaluations were wrong.

#### 3. Solution & Architectural Strategy

Bundle the three reviewed CSV snapshots in `backend/runtime_data/` and explicitly copy them to `/data`. Production SHA-256 verification matches all three development source files; the location service loads all 30 Pasig barangays. The release also enables the approved worker after migration. Ten RSS-linked backlog bodies now produce typed, source-linked stored results, with no duplicate or public flood writes. Historical rows remain context rather than live evidence.

#### 4. Files Modified / What Changed

`backend/Dockerfile` adds the reference copy; `backend/runtime_data/` holds the three snapshots and refresh/build instructions; `.gcloudignore` excludes backend environment files; `cloudbuild.yaml` selects bounded collector processing. Existing evaluation/progress/task/system/feature records document the release. No reference service, model, migration definition, or runtime dependency changed.

### [BUG-076] Full backend tests lack isolated database and auth fixtures

- **Status:** Investigated; pre-existing test infrastructure gap; remediation pending
- **Severity:** Medium (prevents a trustworthy all-suite integration result; no new runtime regression established)
- **Date Reported / Updated:** October 02, 2026
- **Author / Investigator:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The new-branch review collects 398 cases, but some older integration modules use configured shared database sessions/live providers, install auth overrides at import time, or request a nonexistent `db` fixture. Running them with the isolated news/authorization tests could contaminate dependency state or write to an unintended database. The review therefore explicitly separates these cases and does not claim a full-suite pass.

#### 2. Root Cause Analysis (RCA)

`tests/conftest.py` exposes `db_session` from the application SessionLocal rather than an isolated test database. `test_auth_endpoints.py` requests `db`, which that conftest does not define. `test_audit_trail.py`, `test_flood_report_merging.py`, `test_spatial_archive.py`, and `test_spatial_merging.py` mutate shared app auth overrides during collection without universal per-case cleanup. Other legacy tests call SessionLocal/live geocoding directly. All these files are unchanged from roi-branch; this was not introduced by the new worker.

#### 3. Solution & Architectural Strategy

Pending: add a guarded disposable PostgreSQL/PostGIS harness, restore auth/dependency/limiter state per test, mock external providers, and resolve fixture naming while preserving every failing test. First validate against the baseline and then the new revision; distinguish old test failures from feature regressions. The current review validates 371 distinct cases and explicitly leaves twenty-three database/live cases plus four guarded PostgreSQL cases unverified in this run. The earlier migration/four-PostgreSQL verification remains documented separately.

#### 4. Files Modified / What Changed

- No production or test runtime file changed during this investigation.
- Existing evaluation, task/progress, and this issue record document the evidence, affected pre-existing test files, and remaining integration acceptance.

**Later pre-push mitigation (October 2):** Running selected legacy modules in separate processes against a guarded disposable PostgreSQL/PostGIS database passes existing flood-event (4), profile/password (1), OTP (1), archive (2), saved-place (1), and login-limit (1) cases. Four queue cases also pass. An explicit-ID seed sequence error was corrected in disposable setup, not application code. This improves confidence to 385 distinct validated cases but does not repair universal fixture isolation or claim full-suite coverage; thirteen legacy/live cases remain open. See [verification](../evaluations/phase-36-open-article-fallback-check.md#additional-pre-push-verification--october-2). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### [BUG-075] Flood-control discussions were classified as active flooding

- **Status:** Resolved locally; 13 focused and 207 combined regressions pass; one real administrative body rejected as flood evidence; broad live validation/deployment pending
- **Severity:** High (policy discussion could create a false flood candidate)
- **Date Reported / Updated:** October 02, 2026
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

A constructed report discussing flood control projects in Taguig yielded an active, body-grounded local flood claim despite having no flood observation. Project height measurements and rising funding could also become depth/status evidence. The preview remained review-only; no public zone was written.

#### 2. Root Cause Analysis (RCA)

The active-word expression matched `flood` inside infrastructure/program phrases. Generic depth and condition rules then interpreted administrative wording as physical flood evidence, allowing unknown-scope discovery probes to accept the story.

#### 3. Solution & Architectural Strategy

Mask flood-control/mitigation/prevention/management/protection and anti-flood phrases only when checking evidence words; retain original source text and offsets. Exclude policy-only sentences and clauses before extracting measurements or borrowing another clause's flood evidence. Preserve explicit flood-depth gauges and genuine water observations in mixed-topic articles. Regression development caught and repaired an overly broad first guard that suppressed knee-deep water beside a flood-control mention. Metadata-local headlines may remain review leads; policy text cannot become observations. No schema or dependency change.

#### 4. Files Modified / What Changed

- `backend/app/services/taglish_extraction_service.py`: Shared evidence-word masking and policy-only sentence/clause guards with explicit-gauge preservation.
- `backend/tests/test_taglish_extraction.py`: Twelve cases for administrative terms, project dimensions, metadata-only input, mixed actual floods, clause boundaries, and source offsets.
- `backend/tests/test_news_discovery.py`: Real RSS/body parsing through mock HTTP rejects an unknown-scope policy story with a visible no-local-claim notice.
- Existing evaluation, task/progress, feature/system reference, and RSS plan: Record local repair, fresh empty live shortlist, successful manual live negative after a permitted approval retry, and deferred Priority 3.

### [BUG-074] Later flood updates were blanket conflicts and same-URL revisions reused old bodies

**Later scope correction:** The broad Priority 3 hold is superseded. Priority 2 comparison repairs pass controlled tests; live matching remains unverified. Durable grouping/retry and zone updates are later integration requirements. The developer authorized saved-extraction preparation, with durable storage pending explicit schema approval.

- **Status:** Resolved locally with 141 combined regression tests; live update verification and deployment pending
- **Severity:** High (updates could be rejected or an old body relabeled as a newer version)
- **Date Reported / Updated:** October 02, 2026
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Knee-deep flooding followed by a later chest-deep observation was treated as a depth conflict; observed clearance was also flagged as conflicting. Feed retrieval could choose older coverage before newer reports. A same-URL publication revision with unchanged wording reused the stored body; a failed fetch could keep old text while updating its metadata/date.

#### 2. Root Cause Analysis (RCA)

Comparison used depth/status differences and article-wide time lists rather than per-city/road observation order. Alternate feed selection stopped at the first three matches. Cached-body reuse checked title/summary fingerprint but ignored publication revisions. Persistence relabeled old text after failed refresh, and duplicate provenance could repeat that metadata update.

#### 3. Solution & Architectural Strategy

Compare latest explicit observations per city-qualified road, distinguish later changes/clearance from older/stale observations and genuine simultaneous conflicts, expose segment and recurrence ambiguity, and retain missing verification. Choose newest eligible alternate publications across bounded feeds and newest-first probes within discovery feeds. Refresh same-URL publication revisions, preserve successful body/date on failure, surface errors, and prevent older feed overwrites. Retained errored bodies cannot activate even with cached approval. The authenticated fallback can inspect them. No schema or dependency change; no production extraction wiring. Unchanged-feed retries, durable versions/grouping, and live acceptance remain open; Priority 3 is held.

#### 4. Files Modified / What Changed

- `backend/app/services/news_open_search_service.py`: newest alternate selection and per-road observation decisions.
- `backend/app/schemas/news_candidate.py`: typed `road_updates` response.
- `backend/app/services/news_discovery_service.py`, `backend/app/crud/news.py`: publication refresh, ordering, older-version rejection, retained snapshot/error handling.
- `backend/app/services/news_auto_ingestion_service.py`: failed-refresh body and activation guards.
- `backend/app/api/v1/endpoints/admin_news.py`: protected fallback eligibility for retained errored bodies.
- `backend/tests/test_news_open_search.py`, `backend/tests/test_news_discovery.py`, `backend/tests/test_news_auto_ingestion.py`: update ordering, bounded freshness, revision persistence, fallback auth, and no-write regression coverage.
- [Fallback evaluation](../evaluations/phase-36-open-article-fallback-check.md), task plan, progress, existing flagship Feature 1, system documentation, RSS plan, and tech stack: synchronized scope, validation, and hold.

### [BUG-073] Feed location filtering discarded body-only Metro Manila flood reports

- **Status:** Resolved locally with controlled coverage; live flood-candidate verification and deployment pending
- **Severity:** Medium (local flood reports could be skipped before retrieval)
- **Date Reported / Updated:** October 01, 2026
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

A headline such as “Several roads flooded” was discarded if its feed summary omitted the city, even when its article body explicitly reported a Pasig flooded road. Alternate-report retrieval exposed bodies but supplied no structured comparison or copied-body warning.

#### 2. Root Cause Analysis (RCA)

Discovery used only flood/place regexes on feed metadata. Alternate retrieval labeled all accessible bodies as review leads without comparing source-linked dates, city-qualified roads, or duplicate content. Duplicate feed processing could also save an unaccepted lead if acceptance and seen-request state were conflated.

#### 3. Solution & Architectural Strategy

Prioritize metadata-local leads and permit five additional unknown-scope article probes per run. Require an extracted body-grounded local flood claim; skip explicit non-local city/province metadata and future-dated entries. Return notices for unresolved/blocked/out-of-scope/budget outcomes. Track accepted URLs separately from seen requests, preserving rejected scope through duplicates and accepted cached-body reuse. Alternate review compares specific places, city-qualified roads, dates, depth/status, and normalized body hashes. Every overlap remains unverified; copied bodies do not count as independent evidence. No DB schema, dependencies, external auditor, or activation path changed.

#### 4. Files Modified / What Changed

- `backend/app/services/news_discovery_service.py`: bounded body-location probes, extracted scope, future-date checks, notices, and accepted/seen duplicate handling.
- `backend/app/services/news_open_search_service.py`: structured event-review clues and duplicate-body warning.
- `backend/app/schemas/news_candidate.py`, `backend/app/api/v1/endpoints/admin_news.py`: typed run notices and alternate event-review serialization through staff-authenticated routes.
- `backend/scripts/run_news_discovery.py`: CLI notices and alternate review output.
- `backend/tests/test_news_discovery.py`, `backend/tests/test_news_open_search.py`: body-only locations, incidental weather clues, run-wide budget, duplicates/repeats, city-qualified roads, dates/depth/status, and copied bodies.
- [Fallback evaluation](../evaluations/phase-36-open-article-fallback-check.md): controlled results and remaining live limitations.

### [BUG-072] Inquirer RSS HTML character references broke XML parsing

- **Status:** Resolved locally; all six configured feeds parsed live; deployment pending
- **Severity:** Medium (one configured publisher's feed was excluded before discovery)
- **Date Reported / Updated:** October 01, 2026
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The ordinary LANES client received HTTP 200 from Inquirer's configured full feed but returned `Invalid feed XML` and no entries. The failure response also discarded the received HTTP status, making this data-format error resemble a connection failure. A valid empty feed could additionally cause the discovery CLI to report failure.

#### 2. Root Cause Analysis (RCA)

The RSS used undeclared HTML character names (`hellip`, `nbsp`, and `rsquo`) outside CDATA. ElementTree rejected an undefined entity at line 92, column 54. The feed probe's exception branch always set HTTP status to null, and the discovery success check omitted the healthy `empty` status. These problems are distinct from the original article's Cloudflare challenge.

#### 3. Solution & Architectural Strategy

Convert only standard HTML named characters outside CDATA to numeric XML references. Preserve XML's predefined escapes and CDATA; reject unknown custom entities, DTD declarations, and oversized normalized data. Retain HTTP status for parsing errors, explicitly reject HTML/challenge responses, and treat valid empty feeds as healthy. A final live run parsed all six feeds, including 20 Inquirer entries, without feed errors. The combined discovery, fallback, ingestion, and hybrid suite passed 107 tests. Article-page recovery remains unverified.

#### 4. Files Modified / What Changed

- `backend/app/services/news_feed_service.py`: bounded known-character normalization, CDATA/XML escaping preservation, retained parse-error HTTP status, and HTML/challenge diagnostics.
- `backend/scripts/run_news_discovery.py`: healthy empty-feed outcome and read-only extraction diagnostics.
- `backend/app/services/news_discovery_service.py`: shared collection-to-rules extraction diagnostic with per-candidate errors and no ingestion calls.
- `backend/tests/test_news_discovery.py`: live-failure regressions, custom-entity rejection, controlled RSS/body/extraction flow, no DB/auditor calls, and honest empty/blocked/error outcomes.
- [Fallback evaluation](../evaluations/phase-36-open-article-fallback-check.md): live measurements and remaining integration boundaries.

### [BUG-071] Staff index lookup timed out before slow TLS could finish

- **Status:** Resolved locally with regression coverage; deployment and successful live automatic recovery pending
- **Severity:** Medium (fallback could time out before receiving a provider response)
- **Date Reported / Updated:** October 01, 2026
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

After the original Inquirer article returned a Cloudflare challenge, GDELT checks returned throttling or connection timeouts. Cooldowns suppressed repeat requests but did not identify where connection time was spent.

#### 2. Root Cause Analysis (RCA)

Local tracing completed TCP in 0.41 seconds and TLS at 8.83 seconds; a read-only Cloud Run diagnostic completed TCP in 0.19 seconds and TLS at 11.05 seconds. TLS alone exceeded the staff client's 3-second connect timeout and, in Cloud Run, a 10-second diagnostic budget. The completed connections returned HTTP 429 with the provider's five-second request-spacing notice. The cause of the slow handshake and the exact provider rate-limit bucket remain unknown; these are separate from Inquirer's Cloudflare challenge.

#### 3. Solution & Architectural Strategy

Override only GDELT requests with a 15-second connect / 20-second read timeout, retain per-process pacing/cooldowns, and reject malformed provider result shapes. Add optional place/date queries and independent approved-publisher feed shortlisting for recent originals, followed by the existing bounded body parser. Keep event review mandatory and preserve visible failures and original evidence. Add a read-only diagnostic mode to the existing collector script. The combined suite passes 87 tests, including recovery from simulated GDELT 429 through an RSS feed and unchanged database originals. Live provider throttling persists; no live automatic recovery is claimed.

#### 4. Files Modified / What Changed

- `backend/app/services/news_open_search_service.py`: provider timeout, response validation, place/date search, approved recent-feed fallback, and accurate unavailable-body status.
- `backend/app/api/v1/endpoints/admin_news.py`: publication context and independent feed fallback in retrieval mode.
- `backend/app/schemas/news_candidate.py`: feed lead publication timestamp, separate from index-seen time.
- `backend/scripts/run_news_discovery.py`: read-only open-leads diagnostic, safe network timing/status summaries, and truthful exit status.
- `backend/tests/test_news_open_search.py`, `backend/tests/test_news_discovery.py`: timeout override, malformed payload, date/place filtering, feed recovery, API serialization, and no-write checks.
- [Fallback evaluation](../evaluations/phase-36-open-article-fallback-check.md): local/Cloud Run traces and remaining live limits.

### [BUG-070] GDELT lookups lacked shared pacing and cooldowns

- **Status:** Request handling repaired locally; live provider success remains unverified
- **Severity:** Medium (repeated or concurrent staff lookups could amplify provider throttling)
- **Date Reported / Updated:** October 01, 2026
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Live GDELT checks returned HTTP 429. Separate lookups could repeat searches without a provider-wide interval or shared cooldown. A successful title search could also immediately issue a phrase search. The observed external 429's original cause is unconfirmed.

#### 2. Root Cause Analysis (RCA)

The staff route's per-client limit did not coordinate individual upstream queries across concurrent calls. The service had no success cache, failure cooldown state, or Retry-After parsing.

#### 3. Solution & Architectural Strategy

Use a single in-flight query gate per process, a 10-second gap, a bounded 10-minute cache, and exponential cooldowns starting at 60 seconds. Respect longer Retry-After seconds/dates, recognize HTTP-200 throttle notices, and expose structured wait metadata. Long waits return immediately and no failed query is automatically retried. A real HTTP 429 plus an immediate repeat generated one outbound request total. This does not coordinate multiple processes/replicas or clear external limits.

#### 4. Files Modified / What Changed

- `backend/app/services/news_open_search_service.py`: pacing, cache, cooldowns, and provider failure handling.
- `backend/app/schemas/news_candidate.py`: optional `retry_after_seconds`.
- `backend/app/api/v1/endpoints/admin_news.py`: Retry-After response header.
- `backend/tests/test_news_open_search.py`, `backend/tests/test_news_discovery.py`: concurrency, timing, cache, backoff, HTTP-date, failure, and response metadata regressions.
- [Fallback evaluation](../evaluations/phase-36-open-article-fallback-check.md): verification and process-scope limits.

### [BUG-069] Malformed indexed article URLs crashed the staff lookup

- **Status:** Resolved locally with regression coverage
- **Severity:** Medium (external search metadata could fail the lookup)
- **Date Reported / Updated:** October 01, 2026
- **Author / Resolver:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

A GDELT-style result containing `https://[invalid/flood` raised an uncaught `ValueError`. Invalid/nonstandard ports could also survive lead validation. Live checks additionally returned HTTP 429, which the response labeled only as `HTTPStatusError`.

#### 2. Root Cause Analysis (RCA)

Article identity parsing ran outside the provider-error handler and did not catch URL parsing failures or validate the port. Provider failures used only the exception class, and a failed title search could still immediately trigger an excerpt search.

#### 3. Solution & Architectural Strategy

Skip malformed URLs and nonstandard ports, retain valid results, return HTTP status codes without provider body text, and stop immediate phrase searches after failed title requests. Alternate bodies remain separate and require event review. HTTP 429 availability remains an operational limitation, not a resolved provider issue.

#### 4. Files Modified / What Changed

- `backend/app/services/news_open_search_service.py`: URL validation and failure handling.
- `backend/tests/test_news_open_search.py`: malformed URL, malformed/oversized response, disabled-source, and 429 regressions.
- `backend/tests/test_news_discovery.py`: retrieval-option response and unchanged stored original integration checks.
- [Fallback evaluation](../evaluations/phase-36-open-article-fallback-check.md): offline and live verification details.

### [BUG-068] Mobile flood report media selection did not attach picked files

- **Status**: Resolved in code; physical-device verification pending
- **Severity**: High (user-selected report evidence could be omitted)
- **Date Reported / Updated**: September 30, 2026
- **Affected Area**: `/map` flood report panel and report media upload API
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

On a small screen, selecting a photo or video in the flood report panel could leave the attachment list empty. A separate server failure path could submit the report without a selected media file if Cloudinary rejected it.

#### 2. Root Cause Analysis (RCA)

The file input's `onChange` scheduled a React state updater that read `e.target.files`, then immediately cleared the input value. By the time the updater ran, the live `FileList` could already be empty. The control also depended on a `display:none` input activated by a label, which is less reliable for native mobile pickers. On the server, `upload_image` returned `None` on failure, and the reports endpoint silently skipped that file before creating the report.

#### 3. Solution & Architectural Strategy

Copy selected `File` objects before resetting the input, and make the native input cover the upload control while remaining visually transparent. If a requested upload fails, return HTTP 502 before creating the report; the panel displays that error. Preserve the same control on desktop and mobile.

#### 4. Files Modified / What Changed

`frontend/src/features/hazards/FloodReportPanel.tsx`: direct picker target, stable file snapshot, and visible submission error. `backend/app/api/v1/endpoints/reports.py`: reject missing upload URLs. `frontend/tests/flood-report-media.spec.ts`: desktop and mobile viewport photo/video attachment regression. `backend/tests/test_report_media_upload.py`: failed-upload rejection. Both browser viewport checks and the backend regression pass; a physical mobile picker has not been tested.

---

### [BUG-067] Route Planner returned too few alternatives and Walking appeared vehicle-like

- **Status**: Code resolved; live street verification pending
- **Severity**: Medium
- **Date Reported / Updated**: September 30, 2026
- **Affected Area**: Online Valhalla and ORS routing
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Selecting Walking could show a road-like detour, and fewer than four route cards appeared even when four distinct candidates were available.

#### 2. Root Cause Analysis (RCA)

Both providers were queried only with their default fastest costing. Walking already used `pedestrian` / `foot-walking`, so the specific observed street could also reflect legal pedestrian tags, disconnected footpaths, or graph data. The ranker appended only one extra card after its category picks, so it could stop below four. Valhalla also accepted an optional vehicle heading for Walking.

#### 3. Solution & Architectural Strategy

Request fastest and shortest candidate sets from either provider using the same flood-exclusion passes. Keep pedestrian-specific profiles, omit vehicle heading for Walking, and fill the four-card limit from distinct eligible candidates. Never bypass pedestrian access tags or fabricate routes. Verify the reported street against live provider outputs and OSM tags when coordinates are available.

#### 4. Files Modified / What Changed

`backend/app/services/valhalla_service.py`, `ors_service.py`, `routing_service.py`, `flood_routing_policy.py`: provider preferences, shared candidate search, and four-card ranking. `backend/tests/test_routing_service.py`, `test_flood_routing_policy.py`: walking requests, both preference passes, and four-card regression coverage. Routing guide and system records were synchronized.

---

### [BUG-066] Historical PNA Replay Lost Its Test-Only Source After Registry Cleanup

- **Status**: Source mapping repaired; current live replay blocked by PNA HTTP 500
- **Severity**: Medium (historical acceptance evidence cannot currently be refreshed)
- **Date Reported / Updated**: September 28, 2026
- **Affected Area**: Phase 36 read-only article simulation
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

After the runtime RSS registry was reduced to six active publishers, `simulate_phase36_articles.py` stopped two fixed historical PNA cases with `Publisher domain not registered`. The current PNA article endpoints also returned HTTP 500 when fetched after the mapping repair.

#### 2. Root Cause Analysis (RCA)

The replay script reused the live RSS source registry as its entire domain allowlist. PNA was removed from that registry because it is not an active feed, although two fixed historical acceptance cases still depend on its article domain. The HTTP 500 responses originate from current publisher requests; the script cannot recover their article bodies from them.

#### 3. Solution & Architectural Strategy

Add a disabled, feedless PNA source only inside the historical replay script. It still requires the existing approved-domain article fetcher and cannot affect scheduled discovery. Preserve the two PNA cases as unverified on this run until their publisher pages respond or an authorized saved full body is available; do not count prior 16/16 and 8/8 results as a current pass.

#### 4. Files Modified / What Changed

- `backend/scripts/simulate_phase36_articles.py`: Add fixed historical PNA domain mapping without enabling a runtime RSS source.
- `docs/evaluations/phase-36-publisher-body-and-pagination-audit.md`, `docs/task_plan.md`, `docs/others/bug-log.md`: Record the current replay results and open availability limit.

---

### [BUG-065] Full GMA Body Exposed Cross-Section Fact Leakage and Publisher Widget Claims

- **Status**: Checked GMA text-extraction errors repaired; publisher-wide pagination and Inquirer full-body access remain open
- **Severity**: High (a later city can inherit another city's time or an incidental place can be misread)
- **Date Reported / Updated**: September 28, 2026
- **Affected Area**: Phase 36 article parsing and Taglish extraction
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The complete GMA page initially mapped “Valley 2 in Barangay” to a false two-inch depth, missed named junction/bridge sites, omitted reported vehicle restrictions, carried a Quezon City or Manila clock into later city sections, and treated zero-visibility weather and a photo credit as place claims. The parsed `<main>` also contains related stories and embedded social/widget text. The Inquirer source refuses the registered fetcher with HTTP 403.

#### 2. Root Cause Analysis (RCA)

An ambiguous-depth pattern accepted bare `in` as inches; landmark matching did not cover Junction, Bridge, or numbered Valley names; vehicle rules did not cover these ordinary English/Tagalog phrasings. Any paragraph containing an `as of` flood statement could set a section-wide clock even if it reported one named site. In the July GMA status list, suffixless road names were split into city matches, list headings leaked into later narrative, and grouping by exact spelling missed `España`/`Espana`. The generic HTML parser included a GMA related-story widget. Inquirer's 403 is an upstream access refusal, not evidence of an empty article.

#### 3. Solution & Architectural Strategy

Remove bare `in` depth matching; keep human-height descriptions as raw ambiguous depth. Extract the named landmarks and vehicle restrictions; skip zero-visibility and `Courtesy:` lines. Exclude the GMA `mrect_related_content_holder` widget in HTML parsing while preserving the following reporting text. Keep suffixless list sites together, scope grouped city/time to list boundaries, and treat recorded flooding in an earlier advisory as an observation rather than a forecast. Resolve `Maynila` as Manila for embedded road evidence. Compare same bounded road claims accent-insensitively and regardless of article order for review marking. Current live replays produce 27 review-only claims for August 29 and 26 review/suppressed claims for July 10; the original 51-site check still matches 27/27, 16/16, and 8/8, and 64 focused tests pass. Publisher-wide pagination/completeness and an accessible Inquirer body remain needed before Gate 1 closure.

#### 4. Files Modified / What Changed

- `backend/app/services/taglish_extraction_service.py`, `backend/tests/test_taglish_extraction.py`: list-site boundaries, city and time scope, alias matching, advisory observation, and contradiction regressions.
- `backend/app/services/news_discovery_service.py`, `backend/tests/test_news_discovery.py`: exclude GMA's related-story container without cutting subsequent reporting text.
- `docs/evaluations/phase-36-three-article-check.md`, `docs/task_plan.md`, `docs/progress.md`, `docs/others/bug-log.md`: source-level evidence and open limits.

---

### [BUG-064] Long Article Bodies Were Silently Truncated

- **Status**: Silent cutoff, sampled publisher body defects, and a Rappler rolling-updates pagination miss repaired; unseen pagination and Inquirer access remain open
- **Severity**: High (a late flood update could be omitted while the article appears complete)
- **Date Reported / Updated**: September 28, 2026
- **Affected Area**: Phase 36 article fetching and full-body extraction
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

`fetch_article_text` silently returned only the first 30,000 characters of parsed article text. A report, correction, or subsidence statement later in a long page would not reach the extractor, yet the result had no incomplete-body error. A later five-entry-per-source audit also found a Rappler rolling-updates page where the first 4,353 parsed characters were accepted despite a `?next=2` continuation.

#### 2. Root Cause Analysis (RCA)

The parsed text was sliced with `[:30_000]` after the HTML response had already been read. The three audited articles are shorter than that limit, so their 51-site checks did not expose this general hole. The fetcher also only followed HTTP redirects, not publisher pagination links. Its same-article continuation matcher recognized numeric `page` queries and paths but not Rappler's numeric `next` query. In the current-source audit, Philstar's `sports_article_writeup` appeared outside `<article>` and `<main>`, so the generic parser returned no text. Rappler and BusinessWorld put story text within narrower containers than `<main>`, which admitted unrelated page content.

#### 3. Solution & Architectural Strategy

Return the complete parsed text within a 100,000-character processing bound. If it exceeds that bound, return an explicit error and no article body so downstream processing cannot mistake a prefix for the whole story. Detect HTML `rel=next` and common same-article `?page=2`, `?next=2`, `/page/2`, or `/2` links and mark those articles incomplete rather than processing page one alone. Require publisher story-body containers for Rappler and BusinessWorld, extract Philstar's write-up container, and omit sampled related-story widgets. Philstar's `lazy_section.php?page=1` link loads a different story and is not a continuation. A ten-position-per-source follow-up found 50 accessible article responses: 49 supplied accepted text and the Rappler rolling-updates page remained incomplete, linking onward even after page 32. This does not prove all templates or pagination schemes; unrecognized multi-page articles remain a risk. The Inquirer feed returned 200, while ten article requests returned Cloudflare `cf-mitigated: challenge` 403 responses, including one repeated URL. The collector records an explicit publisher-challenge error and accepts no full Inquirer body. See the [publisher audit](../evaluations/phase-36-publisher-body-and-pagination-audit.md).

#### 4. Files Modified / What Changed

- `backend/app/services/news_discovery_service.py`, `backend/tests/test_news_discovery.py`: Remove silent truncation, narrow publisher containers, skip related blocks, and test incomplete-body and continuation cases, including Rappler's `next` query pattern.
- `docs/task_plan.md`, `docs/progress.md`, `docs/others/bug-log.md`, `docs/evaluations/phase-36-publisher-body-and-pagination-audit.md`: Record the sampled results and open pagination/Inquirer limits.

---

### [BUG-063] Explicit News Observation Clocks Lacked Dates

- **Status**: Bounded explicit-clock resolution repaired; ambiguous dates and automatic activation remain in review
- **Severity**: High (freshness cannot be verified for automatic routing)
- **Date Reported / Updated**: September 28, 2026
- **Affected Area**: Phase 36 Taglish event-time extraction and hybrid activation gate
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The extractor keeps strings such as `as of 4:30 p.m.` and classifies some as observations, but `event_time_resolved` remains `None`. The activation gate requires a timezone-aware resolved observation time, so normal extracted claims cannot satisfy that prerequisite.

#### 2. Root Cause Analysis (RCA)

`extract_event_time_from_text` returned the raw match and `None` rather than combining the explicit clock time with a justified source date and timezone. The article's publication time is not itself a flood observation or onset time.

#### 3. Solution & Architectural Strategy

The extractor now resolves only explicit `as of` observation clocks against a timezone-aware publication time in Asia/Manila, within a 12-hour bound. It handles a nearby previous-day midnight rollover and leaves explicit other dates, stale clocks, missing or naive publication timestamps, and report-only clocks unresolved. A read-only August GMA replay resolved the named road observation clocks and left an embedded post with an explicit calendar date unresolved. This enables the time field to pass its prerequisite for suitable claims but does not satisfy the independent audit, exact geometry, current-source, or article-completeness gates for automatic activation.

#### 4. Files Modified / What Changed

- `backend/app/services/taglish_extraction_service.py`, `backend/tests/test_taglish_extraction.py`: Add bounded observation time resolution and regressions for same-day, midnight, stale, explicit-date, naive publication, and report-only cases.
- `docs/task_plan.md`, `docs/progress.md`, `docs/evaluations/phase-36-three-article-check.md`, `docs/others/bug-log.md`: Record the delivered prerequisite and remaining limits.

---

### [BUG-062] Article Context Produced Incidental Flood Claims and Unreconciled Updates

- **Status**: In progress; real newer-first clearing case checked, wider source evaluation pending
- **Severity**: High (incorrect place evidence or stale active claim could mislead future automatic placement)
- **Date Reported / Updated**: September 28, 2026
- **Affected Area**: Phase 36 Taglish extraction and hybrid activation decision
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The three-article simulation included photo-caption, dateline-city, and rainfall-warning places among extracted claims. A later clearing update for the same road section did not mark its earlier active claim as conflicting.

#### 2. Root Cause Analysis (RCA)

The sentence extractor treated every recognized place in a news body as a candidate, including editorial context and weather measurements. Claims were evaluated independently, with no same-section check for later subsidence or negation.

#### 3. Solution & Architectural Strategy

Preserve pre-dateline flood-road captions as `photo_caption_only` review evidence; do not let them approve a zone without independent confirmation. Metadata-only leads are likewise review-only. Skip explicit photo credits, dateline place labels, and rainfall-only sentences without a flood observation. Mark a repeated city plus bounded road/landmark section when one statement says it cleared, regardless of article order; the action gate then requires review. Do not infer a resolved observation time or a whole-road closure. The initial connection errors came from process-only proxy variables pointing to `127.0.0.1:9`, not the publishers or user network. A publisher-backed rerun after removing those variables matched all 51 cited list sites while preserving the PNA lead photo claim as review-only. A separate July 10 GMA article verifies newer-first clearing markers on Taft Avenue and España/Maceda; its text-level road/city and grouped-time errors were repaired under BUG-065.

#### 4. Files Modified / What Changed

- `backend/app/services/taglish_extraction_service.py`, `backend/app/services/hybrid_extraction_service.py`: filter incidental context, link same-section contradictory updates, and block approval of those earlier claims.
- `backend/tests/test_taglish_extraction.py`, `backend/tests/test_news_auto_ingestion.py`: verify filtering, segment isolation, caption review isolation, and the decision gate; five targeted and 65 focused tests passed.
- `docs/evaluations/phase-36-new-article-service-simulation.md`, `docs/task_plan.md`, `docs/progress.md`, `docs/others/bug-log.md`: record the publisher-backed 51-site result, proxy cause, and remaining contradictory-update evaluation.

---

### [BUG-061] Full-Article Flood Lists Lost Locations and Their Parent Context

- **Status**: Resolved for three audited articles; incidental-claim filtering and broader evaluation pending
- **Severity**: High (missing or mislocated evidence would undermine automatic placement)
- **Date Reported / Updated**: September 28, 2026
- **Affected Area**: Phase 36 article fetch, Taglish extraction, PSGC hierarchy, and location ranking
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The read-only service simulation omitted named flood sites or lost their main road, cross street, parent city/barangay, report time, vehicle status, or travel direction in three Metro Manila articles. A count of extracted claims included incidental places and did not measure list completeness.

#### 2. Root Cause Analysis (RCA)

HTML list boundaries were flattened; periods in `p.m` and `cor.` split one entry; generic road suffix matching missed suffixless road names and mistook crossing roads or landmarks for separate reports. Article/list headings did not scope city, barangay, time, and passability. The PSGC resolver sometimes preferred an unrelated province or substring city match, and geometry ranking overwrote an already qualified barangay parent.

#### 3. Solution & Architectural Strategy

Preserve list boundaries and add source-evidence-linked road relation, service-road, landmark, numbered-site, direction, grouped advisory, and bullet-time parsing. Prefer explicit city-qualified PSGC matches and carry the qualified barangay into location ranking. The 51 manually checked entries are now a tracked expected-facts fixture; a live read-only rerun matched all 27/16/8 entries and the focused suite passed 73/73. This does not prove unseen-article recall or verified coordinates. Incidental photo/weather claims and spatial verification remain Phase 36 work.

#### 4. Files Modified / What Changed

- `backend/app/services/news_discovery_service.py`, `backend/app/services/taglish_extraction_service.py`, `backend/app/services/philippine_location_service.py`, `backend/app/services/nationwide_geometry_service.py`: Preserve article structure, link named sites to main roads, retain scoped facts, and resolve administrative parents from the right city.
- `backend/tests/test_news_discovery.py`, `backend/tests/test_taglish_extraction.py`, `backend/tests/test_nationwide_geometry.py`, `backend/tests/test_phase36_article_simulation.py`, `backend/tests/fixtures/phase36_expected_sites.json`, `backend/scripts/simulate_phase36_articles.py`: Add regressions, the read-only full-article simulation, and expected-site checks. The focused suite passes 73/73 tests.
- `docs/evaluations/phase-36-new-article-service-simulation.md`, `docs/task_plan.md`, `docs/progress.md`, `docs/others/bug-log.md`: Record source comparison, automated acceptance results, limits, and next Gate 1/Gate 3 tasks.

---

### [BUG-060] News Claim Could Treat Preview Geometry and Fallback Audit as Approval Evidence
- **Status**: Code safeguard applied; automated verification pending
- **Severity**: High (public routing impact if dormant ingestion were connected)
- **Date Reported / Updated**: September 27, 2026
- **Affected Area**: Phase 36 hybrid extraction, location ranking, and news ingestion
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The dormant news ingestion path could treat generated polygons and an `auto_approved` label as sufficient to create a public Flood Report, Event, and avoidance zone. The label could be assigned without an independent audit or recent observation; a `0.98` score was assigned only afterward.

#### 2. Root Cause Analysis (RCA)

Offline coordinates generated suggestion geometry but also set `is_auto_approvable`. The fallback auditor returned `is_confirmed=True` when the external model was unavailable. The ingestion service trusted `action_type` and supplied a default `knee` depth and Pasig city on missing data.

#### 3. Solution & Architectural Strategy

Tag geometry provenance and keep current polygons as previews. Require explicit independent confirmation and recent observation/publication before any approval decision. Reevaluate all gates at the public-write boundary so an exact verified claim can activate automatically while stale or forged labels cannot. Remove synthetic confidence, depth, and city defaults. The current geometry provider cannot produce a verified affected segment; integrate LiPAD/UP NOAH spatial context and road-segment matching, then connect the collector. The focused discovery/extraction/geometry/ingestion suite passes 70/70 tests; the broader Gate 2 prerequisite and zero-write acceptance checks remain pending.

#### 4. Files Modified / What Changed

- `backend/app/schemas/news_extraction.py`, `backend/app/services/nationwide_geometry_service.py`, `backend/app/services/hybrid_extraction_service.py`, `backend/app/services/news_auto_ingestion_service.py`: Added provenance, fail-closed audit/decision gates, attached audit results, and an independent write-boundary reevaluation.
- `backend/tests/test_hybrid_extraction_service.py`, `backend/tests/test_nationwide_geometry.py`, `backend/tests/test_news_auto_ingestion.py`: Updated expected review outcomes and added failed-prerequisite and forged-label cases.
- `docs/plans/news-activation-safety-gates.md`, `docs/task_plan.md`, `docs/progress.md`, `docs/feature-reference.md`, and `docs/others/system-documentation.md`: Recorded rollout boundary and current Gate 2 status.

---

### [BUG-059] Staff News API Test Used a Missing Local PostgreSQL Database
- **Status**: Resolved
- **Severity**: Low (test isolation)
- **Date Reported / Resolved**: September 27, 2026
- **Affected Area**: Backend news API automated test
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The staff news API test timed out when posting a manual candidate on a machine without local PostgreSQL. The other focused backend tests passed; this did not establish a production Cloud SQL fault.

#### 2. Root Cause Analysis (RCA)

The test overrode staff authentication but left `get_db` pointing at the development default `localhost:5432`. Its manual-candidate request therefore depended on a running external database.

#### 3. Solution & Architectural Strategy

Override `get_db` with an in-memory SQLite session using `StaticPool`, create only the news tables, and remove the overrides after the test. The focused endpoint test now passes without a local or cloud database.

#### 4. Files Modified / What Changed

- `backend/tests/test_news_discovery.py`: Isolated the protected source/manual-candidate test from external PostgreSQL; confirmed `1 passed`.

---

### [BUG-058] Real 2026 Flood Articles Lose Place Spans, Time, or List Locations
- **Status**: Partially resolved (Manila Bulletin and checked GMA full-page replays pass their text checks; Inquirer full body, pagination, and geometry remain open)
- **Severity**: High (would affect map suggestions if connected)
- **Date Reported**: September 27, 2026
- **Affected Area**: Phase 36 Taglish extraction and nationwide location resolution
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Three short August 2026 publisher passages produced malformed road names, a false City of Calamba match for Calamba Street in Quezon City, missing city context on road claims, and a broken `p.m.` timestamp. A full-body replay of the Manila Bulletin article also found seven missed named passable roads and 11 unstructured barangay mentions. Exact source-linked evidence is in [the three-article check](../evaluations/phase-36-three-article-check.md).

#### 2. Root Cause Analysis (RCA)

The generic case-insensitive road regex swallowed leading words and dropped hyphenated prefixes; the city matcher treated a cross-street name as a city. Sentence splitting broke `p.m.` and the parser did not retain road segments or local-area phrases. Numeric depth was previously treated as ambiguous even when it exactly matched the configured gauge. A unit abbreviation also mistook `Sitio 6 in Catmon` for six inches. The list parser handled an impassable-road list but ignored the separate passable-road and unnamed-street lists, so one article was incompletely represented.

#### 3. Solution & Architectural Strategy

The checked passages and full Manila Bulletin reporting body now have source-linked expected facts. A full-body regression checks 26 named-location and 11 broad-area claims, per-list passability, shared range depth, offsets, and the unresolved `Santulan` spelling. The later GMA full-page and update-order replays are documented under BUG-065; the Inquirer full body, publisher pagination, and verified geometry remain Gate 1/2 work. Keep article-to-zone processing disconnected until those gates pass.

#### 4. Files Modified / What Changed

- `backend/app/services/taglish_extraction_service.py`, `backend/app/schemas/news_extraction.py`, and `backend/tests/test_taglish_extraction.py`: Repaired the checked cases, added per-claim passability, and covered the full Manila Bulletin body structure. Tests pass 22/22 focused and 41/41 across extraction, location service, and news discovery.
- `docs/evaluations/phase-36-three-article-check.md`, `docs/task_plan.md`, and `docs/progress.md`: Recorded the developer-reviewed expected facts, results, and remaining full-article evaluation.

---

### [BUG-057] All Timestamps Displayed 8 Hours Behind Philippine Local Time (UTC Naive Datetime Misinterpretation)
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 22, 2026
- **Affected Area**: Backend / Frontend / Timestamps / Timezone Handling (All Modules)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Flood reports, avoidance zones, audit log entries, user profiles, flood event records, and all other timestamp fields across the platform displayed times that were exactly 8 hours behind the actual Philippine local time (UTC+8 / Asia/Manila). For example, a flood report submitted at 10:00 AM Philippine Standard Time (PST) appeared in the Pending Reports Panel, Active Zones Panel, Flood Event Records, Audit Trail, and FloodZone Popup as 2:00 AM.

#### 2. Root Cause Analysis (RCA)

A two-layer timezone misinterpretation chain:

1. **Backend — Naive UTC Storage Without `Z` Suffix**: All SQLAlchemy models used `default=datetime.utcnow` to store creation and update timestamps in the PostgreSQL database as naive UTC `datetime` objects (no `tzinfo`). When Pydantic serialized these into JSON for the API response, it produced strings in the format `"2026-09-22T02:54:00"` — an ISO 8601 string **without** any timezone indicator (`Z` or `+HH:MM`).

2. **Frontend — JavaScript `new Date()` Local-Time Interpretation**: Per the ECMA-262 specification, when `new Date()` parses an ISO date-time string that lacks a UTC offset suffix, it treats the string as **local time**, not UTC. In Philippine browsers (Asia/Manila, UTC+8), `new Date("2026-09-22T02:54:00")` is interpreted as 2:54 AM Philippine local time (which equals 6:54 PM UTC the day before), producing a display that is 8 hours behind the stored UTC value. All `toLocaleDateString`, `Intl.DateTimeFormat`, and `new Date()` calls in every date-displaying component were affected.

#### 3. Solution & Architectural Strategy

**Two-pronged fix — backend serializer + frontend parser utility:**

1. **Backend `serialize_utc_datetime` Centralised Helper** (`backend/app/schemas/common.py`): Created a shared `serialize_utc_datetime(dt)` function that appends `"Z"` to any naive `datetime` ISO string (no `tzinfo`), and leaves timezone-aware datetimes unchanged. This causes FastAPI/Pydantic to emit `"2026-09-22T02:54:00Z"`, unambiguously signaling UTC to all downstream consumers.

2. **Schema-Wide `@field_serializer` Application**: Applied `@field_serializer` decorators calling `serialize_utc_datetime` to every `datetime` field across all Pydantic response schemas: `FloodReportResponse`, `FloodAvoidanceZoneResponse`, `ZoneContributorResponse`, `NearbyZoneResponse`, `MergeCandidateItem`, `AuditLogResponse`, `FloodEventResponse`, `FloodEventTimelineEntry`, `RoleResponse`, `SavedPlaceResponse`, `UserResponse`, and all related schemas in `backend/app/schemas/__init__.py`.

3. **Frontend `parseUtcDate` Utility** (`frontend/src/lib/utils.ts`): Added `parseUtcDate(input)` — a safe date parser that checks whether the input string contains a `Z` or explicit `+/-HH:MM` offset. If absent, it appends `"Z"` before passing to `new Date()`, guaranteeing the browser always treats the timestamp as UTC. Existing `formatCommentTime` was updated to use `parseUtcDate` internally.

4. **Component-Wide Frontend Update**: Every component that rendered timestamps from API responses was updated to use `parseUtcDate` before passing to `new Date()`, `Intl.DateTimeFormat`, or `toLocaleDateString`, ensuring correct UTC→Asia/Manila conversion for display.

#### 4. Files Modified / What Changed

- `backend/app/schemas/common.py`: Added `serialize_utc_datetime(dt)` helper function.
- `backend/app/schemas/report.py`: Added `@field_serializer` for `FloodReportResponse`, `FloodAvoidanceZoneResponse`, `ZoneContributorResponse`, `NearbyZoneResponse`, `MergeCandidateItem` datetime fields.
- `backend/app/schemas/audit.py`: Added `@field_serializer` for `AuditLogResponse.created_at`.
- `backend/app/schemas/flood_event.py`: Added `@field_serializer` for `FloodEventResponse` and `FloodEventTimelineEntry` datetime fields.
- `backend/app/schemas/role.py`: Added `@field_serializer` for `RoleResponse` datetime fields.
- `backend/app/schemas/saved_place.py`: Added `@field_serializer` for `SavedPlaceResponse` datetime fields.
- `backend/app/schemas/user.py`: Added `@field_serializer` for `UserResponse` datetime fields.
- `backend/app/schemas/__init__.py`: Re-exported `serialize_utc_datetime` from the schemas package.
- `backend/app/api/v1/endpoints/admin.py`: Replaced inline `datetime.now()` / `datetime.utcnow()` usages with `serialize_utc_datetime`-compatible defaults in admin zone creation.
- `frontend/src/lib/utils.ts`: Added `parseUtcDate()` utility and updated `formatCommentTime` to use it.
- `frontend/src/features/admin/AuditTrailPage.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/admin/components/ActiveZonesPanel.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/admin/components/MergeReportsModal.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/admin/components/PendingReportsPanel.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/admin/components/merge/ReportComparisonCard.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/admin/components/merge/ReportComparisonMatrix.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/flood-history/FloodEventDetailModal.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/flood-history/FloodEventDetailsTabs.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/flood-history/FloodEventRecords.tsx`: Updated `formatDate` to use `parseUtcDate`.
- `frontend/src/features/map/components/FloodZonePopup.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/features/profile/ProfileView.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/shared/ui/feedback/FloodReportDetailsModal.tsx`: Updated date display to use `parseUtcDate`.
- `frontend/src/shared/ui/feedback/FloodZoneDetailsModal.tsx`: Updated date display to use `parseUtcDate`.
- `backend/tests/test_datetime_timezone_serialization.py`: [NEW] Added automated Pytest suite verifying `serialize_utc_datetime` outputs ISO strings with `Z` suffix for naive datetimes and preserves offsets for aware datetimes.

---

### [BUG-056] Mobile Map Panels Rendered Incorrectly from Feed Navigation and Allowed Re-Opening of Dismissed Report Panels
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 22, 2026
- **Affected Area**: Mobile Navigation / Global Map Panels / Saved Places / Flood Reporting
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

On mobile/small screens:
1. When navigating from the Community Feed drawer menu by tapping "Add a Place" (`/map?panel=saveplace&tab=add`), the Flood Report panel opened instead of (or rendered directly over) the Save Place panel.
2. After submitting a flood report or sliding down/dismissing the report panel on mobile and navigating to another view, returning to the map page caused the Flood Report panel to re-open automatically.

#### 2. Root Cause Analysis (RCA)

- **Panel Mutual Exclusivity**: `setIsSavePlacePanelOpen(true)` in `MapContext.tsx` closed Analytics, but failed to call `setIsReportPanelOpenState(false)` and did not set `activePanelState("save_place")`. Because `FloodReportPanel` was rendered after `SavePlacePanel` in `GlobalMap.tsx` with identical fixed positioning and `z-40`, the flood report panel completely occluded the save place panel.
- **Persistent URL Query Parameters**: Navigating with `?action=report` was never sanitized upon closing or successfully submitting a report. When returning to the map, `searchParams.get("action") === "report"` re-triggered the `useEffect` in `GlobalMap.tsx`, opening the report panel repeatedly.
- **Mobile Dismissal & Gesture Limitations**: In `Panel.tsx`, the header close button (`X`) was wrapped in `{!isMobile && ...}`, leaving mobile bottom-sheets with no dedicated close button. Additionally, `onDragEnd` required an excessive drag threshold (`offset.y > 60`) without velocity checking, causing quick swipe-down dismiss gestures to bounce back open instead of triggering `onClose()`.
- **Client Media Query Mount Lag**: `useMediaQuery` initialized its boolean match state to `false`, causing temporary flash-evaluations of mobile components as desktop layouts during initial client hydration.

#### 3. Solution & Architectural Strategy

- Enforced strict mutual exclusivity in `MapContext.tsx`: opening Save Place now explicitly closes Flood Report and Analytics while switching `activePanel` to `"save_place"`.
- Synchronized query parameter handling in `GlobalMap.tsx` and `SavePlacePanel.tsx` for `panel=saveplace`, and added URL query parameter cleanup via `router.replace('/map', { scroll: false })` whenever `action=report` or `panel=saveplace` panels are dismissed or submitted.
- Bound mobile `FloodReportPanel` rendering strictly to `isOpen={isMobile ? (isReportPanelOpen && activePanel === "flood") : true}`.
- Added a dedicated mobile header close button in `Panel.tsx` and enabled velocity-based drag dismissal (`offset.y > 60 || velocity.y > 250`).
- Updated `useMediaQuery` to initialize synchronously from `window.matchMedia(query).matches` on the client.

#### 4. Files Modified / What Changed

- `frontend/src/features/map/MapContext.tsx`: Updated `setIsSavePlacePanelOpen` and `setIsReportPanelOpen` to guarantee mutual exclusivity and `activePanel` state transitions.
- `frontend/src/features/map/GlobalMap.tsx`: Handled `panel=saveplace`, cleaned up `action=report` on close, and restricted mobile `FloodReportPanel` `isOpen` to `activePanel === "flood"`.
- `frontend/src/features/places/SavePlacePanel.tsx`: Connected `setActivePanel` state and cleaned `panel=saveplace` URL search param on panel close.
- `frontend/src/shared/ui/layout/Panel.tsx`: Added mobile close (`X`) button and velocity-aware swipe-down dismissal.
- `frontend/src/hooks/useMediaQuery.ts`: Synchronized initial match state on client and added standard media query change listeners.

---

### [BUG-055] Cloud SQL Flood Events Can Outlive Their Origin Evidence
- **Status**: Investigating
- **Severity**: High
- **Date Reported**: September 22, 2026
- **Affected Area**: Cloud SQL / Flood Event Lifecycle / Flood History & Analytics
- **Author / Investigator**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Flood History shows active Flood Events #6 and #8 with zero linked reports and zero official zones, despite timeline entries that reference reports/zones #30/#22 and #36/#25. The event detail is accurate about the current links, but it exposes records that no longer meet the product rule that every Flood Event retains an origin report and an active event retains an official zone.

#### 2. Root Cause Analysis (RCA)

Read-only Cloud SQL inspection confirmed that the referenced reports and zones no longer exist, while the events and their `flood_event_timeline_entries.snapshot_json` references remain. `snapshot_json` is a historical display snapshot rather than a foreign-key relationship. The deployed `flood_reports.event_id` and `flood_avoidance_zones.event_id` links are nullable, so they do not require an event to retain evidence or a zone. The direct official-zone path can also create an event with no administrator-origin report.

#### 3. Solution & Architectural Strategy

Before any schema change, classify the existing orphaned events with staff. A missing source record must be explicitly rebuilt as an administrator-origin report/zone or the event must be ended/marked invalid; no automated process may invent or silently relink evidence. Then introduce a normalized origin/supporting report relationship with one origin per event, restrict deletion of linked evidence, and enforce the active-event/active-zone invariant transactionally with deferred database validation where cross-row constraints are needed.

#### 4. Files Modified / What Changed

- `docs/others/database-design-plan.md`: Added the observed Cloud SQL state, the current nullable-link limitation, and the proposed migration-safe integrity design.
- `docs/task_plan.md`, `docs/progress.md`, `docs/others/system-documentation.md`: Marked Phase 33 integrity remediation as pending and documented the staff-facing limitation.

---

### [BUG-054] Site Visitor Counter Reported Page Loads Rather Than Reliable Visitors
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Landing Page / Admin Dashboard Analytics
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The landing-page visitor number was a single mutable counter. It trusted a boolean browser flag, had no daily trend, could not deduplicate signed-in users across devices, and offered no distinction between a legitimate visible browser and a known automated client.

#### 2. Root Cause Analysis (RCA)

`visitor_counts` stored only an accumulated integer. The browser set its local “visited” flag before knowing whether the counter request succeeded, while the server had no pseudonymous identifier or time dimension with which to deduplicate activity.

#### 3. Solution & Architectural Strategy

Added first-party daily visitor measurement. The browser creates one UUID in local storage only after it becomes visible; FastAPI immediately HMAC-hashes it and stores only the hash, date, timestamps, and an optional account reference. Aggregate reads count an account once across browsers when known, otherwise a browser hash once. Known bot user agents are rejected and rate limiting protects the intake endpoint. No IP address, location, browser fingerprint, or raw UUID is persisted.

#### 4. Files Modified / What Changed

- `backend/app/models/audit.py`, `services/visitor_analytics_service.py`, and migration `c9f3e7a6b210`: introduced indexed, daily pseudonymous visitor records and aggregate queries.
- `backend/app/api/v1/endpoints/public.py`, `admin.py`, and typed visitor schemas: added public recording/read behavior and a protected visitor-trend endpoint.
- `frontend/src/features/landing/HomeStats.tsx`, `features/admin/DashboardPage.tsx`, and `features/admin/adminApi.ts`: use the new tracker and show a responsive 30-day administrator chart.
- `backend/tests/test_visitor_analytics.py`, `test_visitor_analytics_authorization.py`: cover identifier hashing, bot filtering, and route authorization.

---

### [BUG-053] Flood History Workspace Drifted from the Admin Visual System
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Admin Panel / Flood History & Analytics
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Flood History & Analytics used raw selects, inputs, native date fields, and an independently styled mobile switcher. Its cards and chart typography were noticeably larger than the Admin Dashboard, and non-severity charts introduced conflicting teal and indigo accents. The first shared-date-picker pass also placed visible labels above only the two date fields, causing those controls to drop below the rest of the desktop filter row.

#### 2. Root Cause Analysis (RCA)

The Phase 33 workspace was delivered incrementally around its protected data behavior without a final pass against the shared UI library and the Admin Dashboard graph treatment.

#### 3. Solution & Architectural Strategy

Replaced the filter and view controls with shared components, exposed an accessible label on the reusable shared `Select`, and made chart cards more compact. Non-severity charts now share the dashboard's primary blue, subtle dashed grids, and dark tooltips; severity colors remain semantic. The shared `DatePicker` now accepts an in-field empty display and accessible label, so the From/To controls are identifiable without increasing their grid-row height.

#### 4. Files Modified / What Changed

- `frontend/src/features/flood-history/FloodEventAnalytics.tsx`, `FloodEventRecords.tsx`, `FloodEventVisualizations.tsx`: standardized controls, compacted the dashboard, and aligned visual tokens.
- `frontend/src/shared/ui/forms/Select.tsx`, `DatePicker.tsx`: added optional accessible labels; DatePicker also supports compact in-field empty text for aligned date-range controls.
- `frontend/tests/flood-history.spec.ts`: updated the records-filter smoke test for the shared-select interaction.

---

### [BUG-052] Repeated Flood Moderation Map Review Did Not Re-focus the Report
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Moderation Center / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Reviewing a Flood Report could fail after returning from Spatial Operations, and approved/rejected moderation records were not available to the pending-only map query.

#### 2. Root Cause Analysis (RCA)

The map cached an identical focus URL and only searched its pending-report dataset.

#### 3. Solution & Architectural Strategy

Each handoff has a fresh review token. Spatial Operations retrieves the exact admin-authorized report, renders only that report, and clears active-zone data while focused.

#### 4. Files Modified / What Changed

- `backend/app/api/v1/endpoints/admin.py`, `frontend/src/features/admin/adminApi.ts`, `frontend/src/features/admin/LiveMapPage.tsx`, `frontend/src/features/admin/components/FloodModerationQueue.tsx`

---

### [BUG-051] Admin-Created Accounts Encounter 404 Not Found on Profile Edit & Missing Admin Profile Management
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Backend / User Profile / Admin Panel / Identity Lifecycle
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When an account was created via the Admin Panel's Account Registry modal (`POST /api/v1/admin/users`) (such as user `roicambe`), visiting their profile and attempting to update profile details failed with `404 Not Found` (`Profile not found`). Furthermore, Super Admins (restricted from public routes by `NavigationWrapper.tsx`) had no interface within the Admin Panel to edit their personal information, manage their avatar, or update their password.

#### 2. Root Cause Analysis (RCA)
1. **Uninstantiated Profile Model**: The admin user creation handler in `backend/app/api/v1/endpoints/admin.py` called `crud.create_user()`, which only inserted a row into the `users` table without initializing a row in the `profiles` table.
2. **Missing Self-Healing Fallback**: `PATCH /api/v1/users/me/profile` assumed `current_user.profile` always existed, raising `HTTPException(404, detail="Profile not found")`. Avatar upload and delete endpoints had the same limitation.
3. **Database Not-Null Constraints**: The PostgreSQL `profiles` table schema specifies `NOT NULL` for `first_name` and `last_name`. Any naive fallback creation without default string values caused a `psycopg.errors.NotNullViolation`.
4. **Admin Route Separation**: Because Super Admins are restricted from public routes like `/profile`, administrative staff needed an integrated profile management hub directly within the Admin Panel (`/admin/*`).

#### 3. Solution & Architectural Strategy
1. **Auto-Provisioning on Creation**: Updated `create_admin_user` in `admin.py` to automatically instantiate and commit `models.Profile(user_id=new_user.id, first_name=new_user.username, last_name="", display_full_name=True, is_public=True)`.
2. **Self-Healing Token & Profile Handlers**:
   - Updated `POST /api/v1/auth/test-token` to detect missing profiles and auto-provision them on session validation, instantaneously healing existing accounts like `roicambe`.
   - Added self-healing fallback to `PATCH /api/v1/users/me/profile`, `POST /api/v1/users/me/avatar`, and `DELETE /api/v1/users/me/avatar` with proper `first_name=current_user.username` defaults.
3. **Native Admin Profile Management**:
   - Created `AdminProfilePage.tsx` at `/admin/profile` mirroring the public profile design (custom cover color banner with color picker, avatar upload/view/remove, and personal/address info via `EditProfileForm`).
   - Added password change capability (`PUT /api/v1/users/me/password`) with current password verification and live `<PasswordStrength>` validation.
   - Updated `AdminSidebar.tsx` with a staff user profile link card in the footer showing avatar, name, and staff role.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Auto-provisioned `Profile` on admin user creation.
- `backend/app/api/v1/endpoints/auth.py`: Auto-heal missing profile in `test-token` endpoint.
- `backend/app/api/v1/endpoints/users.py`: Self-healing fallback in profile/avatar endpoints; added `PUT /api/v1/users/me/password`.
- `backend/app/schemas/user.py` & `backend/app/schemas/__init__.py`: Added `PasswordChangeRequest` schema.
- `backend/tests/test_admin_profile.py`: Pytest suite verifying self-healing and password change.
- `frontend/src/features/admin/AdminProfilePage.tsx`: Dedicated admin profile page component.
- `frontend/src/app/admin/profile/page.tsx`: Page route for `/admin/profile`.
- `frontend/src/features/navigation/AdminSidebar.tsx`: Profile link card in sidebar footer.
- `frontend/src/features/admin/AdminLayout.tsx`: Zero padding for `/admin/profile` layout.
- `frontend/src/hooks/useProfile.ts`: Added `changePassword` mutation.

---

### [BUG-050] Unique Constraint Collision When Re-creating Soft-Deleted User Accounts & Unhandled 500 Banner
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Backend / Admin / Database / User Lifecycle
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When an administrator attempted to create a new user account in the User Registry (`POST /api/v1/admin/users`) with an email or username that belonged to a previously soft-deleted/archived user, the backend crashed with an unhandled `500 Internal Server Error` (`psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "ix_users_email"`), and the frontend showed a red inline banner `"Operation Refused - Internal Server Error"`.

#### 2. Root Cause Analysis (RCA)
1. Soft-deletion in LANES sets `deleted_at = datetime.utcnow()` without physically deleting the user row in PostgreSQL to preserve activity history.
2. The `users` table has global `UNIQUE` indexes on `email` (`ix_users_email`) and `username` (`ix_users_username`).
3. The user creation handler checked `crud.get_user_by_email()`, which only queries active accounts (`deleted_at IS NULL`). When the new user record was inserted, PostgreSQL rejected the duplicate key.
4. The endpoint lacked an `IntegrityError` rollback handler, causing FastAPI to throw an unhandled 500 error.
5. In the frontend `UsersPage.tsx`, mutation failures triggered a raw inline error banner instead of utilizing the shared toast system (`useToast`).

#### 3. Solution & Architectural Strategy
1. **Archive Purge & Recreation**: Updated `create_admin_user` in `admin.py` to identify any soft-deleted records holding the clean email or username and purge them via `crud.hard_delete_user()` before inserting the new user.
2. **Safe Commit & Conflict Handling**: Wrapped database commits in a `try...except IntegrityError` block with `db.rollback()`, returning a structured `409 Conflict` if duplicate values occur.
3. **Shared Toast UI**: Removed the inline `Operation Refused` alert banner in `UsersPage.tsx` and connected all user mutation callbacks to `toast.success` and `toast.error`.
4. **Archive Management**: Added `restoreUser` (`POST /api/v1/admin/users/{user_id}/restore`) and `hardDeleteUser` (`DELETE /api/v1/admin/users/{user_id}/permanent`) endpoints.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Added stale archive purge, `IntegrityError` rollback, and user restore/permanent delete endpoints.
- `frontend/src/features/admin/adminApi.ts`: Added `restoreUser` and `hardDeleteUser` API callers.
- `frontend/src/features/admin/UsersPage.tsx`: Removed inline `Operation Refused` banner and wired mutations to `useToast`.

---

### [BUG-049] Rejected Flood Reports Did Not Notify Their Submitter
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 20, 2026
- **Affected Area**: Backend / Notifications / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Rejecting a Flood Report removed it from the live moderation queue but did not create an in-app notification, leaving the reporter without a decision in the existing notification bell.

#### 2. Root Cause Analysis (RCA)

The structured rejection service wrote the report state and staff moderation outcome only; unlike Community Post moderation, it did not add a `Notification` in the same transaction.

#### 3. Solution & Architectural Strategy

The rejection service now creates a `SYSTEM` notification atomically with the outcome and trust update. It includes the selected rejection reason but deliberately excludes the internal staff note from both the message and payload.

#### 4. Files Modified / What Changed

- `backend/app/services/flood_event_service.py`: Adds the reporter notification to the rejection transaction.
- `frontend/src/features/admin/components/RejectFloodReportModal.tsx`: Explains the user-notification and staff-note privacy behavior before confirmation.
- `backend/tests/test_spatial_archive.py`: Verifies the notification payload and privacy boundary.

---

## 📋 Bug Resolution Format Standard

When adding entries to this log, use the following structure:

```markdown
### [BUG-XXX] Short Title of the Issue
- **Status**: [Resolved | In Progress | Investigating]
- **Severity**: [Critical | High | Medium | Low]
- **Date Reported / Resolved**: Month DD, YYYY
- **Affected Area**: [Frontend / Backend / Auth / Map / Database / Routing]
- **Author / Resolver**: [@username](https://github.com/username) (Full Name)

#### 1. Problem Description
Detailed description of the unexpected behavior, user steps to reproduce, and visual/operational symptoms.

#### 2. Root Cause Analysis (RCA)
Why the bug happened. Technical explanation of component state, lifecycle, race condition, or API mismatch.

#### 3. Solution & Architectural Strategy
How the issue was addressed, why this approach was selected, and how edge cases are safeguarded.

#### 4. Files Modified / What Changed
- `path/to/file1.ext`: Specific changes made.
- `path/to/file2.ext`: Specific changes made.
```

---

## 🗂️ Bug Log Entries

### [BUG-048] ReferenceError `isTouchDevice is not defined` on Admin Map Zone & Pending Report Hover/Click
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 19, 2026
- **Affected Area**: Frontend / Map Engine / Admin Portal
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When navigating to `/admin/map` and hovering over or clicking a pending flood report or avoidance zone on the MapLibre canvas, the client application threw an uncaught runtime exception in the browser console:
```text
[browser] Uncaught ReferenceError: isTouchDevice is not defined
    at usePendingReportsLayer.useEffect.handlePopupOpen (src\features\map\hooks\usePendingReportsLayer.ts:309:78)
    at usePendingReportsLayer.useEffect.handleMouseEnterOrMove (src\features\map\hooks\usePendingReportsLayer.ts:347:9)
```
This crashed popup rendering for pending reports and prevented administrators from inspecting report details directly on the spatial map.

#### 2. Root Cause Analysis (RCA)
1. **Missing Parameter in Hook Signature**: In `usePendingReportsLayer.ts`, popup rendering logic was adapted from `useFloodZonesLayer.ts` to render `FloodZonePopup` and handle hover/click timers. However, `isTouchDevice` was referenced in the hook without being declared in the function arguments or initialized in scope.
2. **Missing Touch Propagation in Admin Map**: `LiveMapPage.tsx` was computing `isMobile` via `useMediaQuery("(max-width: 640px), (pointer: coarse)")`, but passed hardcoded `false` into `useFloodZonesLayer` and did not pass touch state to `usePendingReportsLayer`.

#### 3. Solution & Architectural Strategy
1. **Parametric Touch Support**: Added `isTouchDevice: boolean = false` to `usePendingReportsLayer` parameter list and its `useEffect` dependency array.
2. **Touch-Aware Hover & Click Protocol**: Updated `handleMouseEnterOrMove`, `handleMouseLeave`, and `handleLayerClick` inside `usePendingReportsLayer.ts` to disable hover dwell timers on touch devices while cleanly opening the popup on click/tap, mirroring `useFloodZonesLayer.ts`.
3. **Propagate Responsive State**: Passed `isMobile` from `useMediaQuery` into both `useFloodZonesLayer` and `usePendingReportsLayer` in `LiveMapPage.tsx`.

#### 4. Files Modified / What Changed
- `frontend/src/features/map/hooks/usePendingReportsLayer.ts`: Added `isTouchDevice` parameter, touch-aware event listeners, and robust popup cleanup.
- `frontend/src/features/admin/LiveMapPage.tsx`: Connected `isMobile` to `useFloodZonesLayer` and `usePendingReportsLayer`.

---

### [BUG-047] Community Feed Voting Desynchronization, Incomplete Flip Delta & Full Feed Re-fetch Lag
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 19, 2026
- **Affected Area**: Frontend / Backend / Community Feed / Interaction Engine
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When commuters upvoted or downvoted posts on the Community Feed, several issues occurred:
1. **Network Lag / Feed Jitter**: The voting action relied on query invalidation (`invalidateQueries(['feed'])`), triggering a heavy 50-post re-fetch over the network before the UI count updated.
2. **Count Desynchronization on Flipped Votes**: Clicking Downvote while previously Upvoted (or vice versa) produced incorrect visual delta counts because the client only decremented by 1 rather than applying a net flip delta ($\pm 2$).
3. **Missing Response Payload**: The `POST /feed/{post_id}/vote` endpoint only returned a generic status message rather than the new authoritative upvote/downvote/net_score state, preventing authoritative client cache synchronization.

#### 2. Root Cause Analysis (RCA)
1. **Lack of Optimistic Cache Mutators**: Vote mutations did not implement `onMutate` optimistic updates on TanStack Query caches, forcing the UI to wait for network roundtrips.
2. **Absence of Dedicated Vote Response Schema**: Backend only returned `{ "status": "success", "message": "Vote recorded" }`, leaving clients with no authoritative post vote counters unless a full re-fetch occurred.

#### 3. Solution & Architectural Strategy
1. **Optimistic Tri-State Vote Calculation**: Implemented `onMutate` hooks across `FeedPage.tsx`, `PostDetailPage.tsx`, and `ProfileView.tsx` that instantly calculate new scores in 0ms (fresh vote $\pm 1$, flip $\pm 2$, cancel vote) and rollback on error.
2. **Authoritative Vote Response**: Created `VoteResponse` Pydantic model and updated `crud/interaction.py` to return the new exact `upvotes`, `downvotes`, `net_score`, and `user_interaction` in `POST /feed/{post_id}/vote`.
3. **Reddit-Style Compact Pill**: Consolidated disjointed counters into a unified `▲ Net Score ▼` pill badge with active color coding and hover breakdown.

#### 4. Files Modified / What Changed
- `backend/app/schemas/feed.py`: Added `VoteResponse` schema.
- `backend/app/crud/interaction.py`: Added `get_post_vote_summary` function.
- `backend/app/api/v1/endpoints/feed.py`: Updated vote endpoint to return `VoteResponse`.
- `frontend/src/features/feed/feedApi.ts`: Updated `votePost` return type.
- `frontend/src/features/feed/PostItem.tsx`: Implemented unified `▲ Net Score ▼` pill badge.
- `frontend/src/features/feed/FeedPage.tsx`: Added optimistic vote mutations.
- `frontend/src/features/feed/PostDetailPage.tsx`: Added optimistic vote mutations for detail view.
- `frontend/src/features/profile/ProfileView.tsx`: Added optimistic vote mutations for profile feed tabs.
- `backend/tests/test_feed_voting.py`: Added automated schema and response tests.

### [BUG-046] Mixed Content Browser Blocking on HTTPS Due to Trailing Slash Redirection and Missing Proxy Headers
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 19, 2026
- **Affected Area**: Frontend / Backend / Networking & Deployment (Cloud Run)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On production (`https://navlanes.live`), navigating to `/admin/dashboard` or `/admin/map` triggered repeated console errors:
```
Mixed Content: The page at 'https://navlanes.live/admin/dashboard' was loaded over HTTPS, but requested an insecure resource 'http://lanes-api-557679867071.asia-east1.run.app/api/v1/notifications?skip=0&limit=20'. This request has been blocked; the content must be served over HTTPS.
```
This caused the notification bell component to fail fetching unread notifications and flooded the browser console.

#### 2. Root Cause Analysis (RCA)
1. **Frontend Trailing Slash Inconsistency**: The root `layout.tsx` mounts `NotificationBell`, which calls `getNotifications(0, 20)`. In `frontend/src/features/notifications/notificationsApi.ts`, the fetch URL was formulated with a trailing slash before query parameters (`/notifications/?skip=${skip}&limit=${limit}`).
2. **FastAPI Trailing Slash Normalization**: In `backend/app/api/v1/endpoints/notifications.py`, the route was registered as `@router.get("")`. When receiving a request with a trailing slash (`/notifications/?...`), Starlette issued an automatic `HTTP 307 Temporary Redirect` to canonicalize the route to `/notifications?...`.
3. **Missing Reverse Proxy Protocol Propagation**: Google Cloud Run terminates SSL/TLS at its edge load balancer and forwards plain HTTP internally to port 8080. Because Uvicorn was running without `--proxy-headers --forwarded-allow-ips "*"` and without `ProxyHeadersMiddleware`, FastAPI was unaware that the client connection originated over HTTPS. Consequently, FastAPI generated the redirect `Location` header using `http://` instead of `https://`.
4. **Mixed Active Content Blocking**: Browsers strictly disallow HTTPS pages from following or executing active fetch/XHR requests to insecure HTTP endpoints, causing the browser to block the notification request immediately.

#### 3. Solution & Architectural Strategy
1. **Eliminated Unnecessary Client-Side Redirect**: Updated `getNotifications` in `notificationsApi.ts` to call `/notifications?skip=${skip}&limit=${limit}` directly without the redundant trailing slash. This prevents the 307 roundtrip altogether, optimizing latency.
2. **Dual Route Registration for Resilience**: Added `@router.get("/", response_model=NotificationPaginatedResponse, include_in_schema=False)` to `backend/app/api/v1/endpoints/notifications.py` so that requests sent either with or without trailing slashes resolve directly with `200 OK` without triggering redirects.
3. **Proxy Header & Protocol Forwarding Enforcement**:
   - Updated `backend/Dockerfile` CMD to execute Uvicorn with `--proxy-headers --forwarded-allow-ips '*'`.
   - Injected `ProxyHeadersMiddleware` into the FastAPI application in `backend/app/main.py` so FastAPI recognizes `X-Forwarded-Proto: https` from reverse proxies (Google Cloud Run / Envoy) and ensures any system-generated redirect retains the HTTPS scheme.

#### 4. Files Modified / What Changed
- `frontend/src/features/notifications/notificationsApi.ts`: Removed the trailing slash before query parameters in `getNotifications`.
- `backend/app/api/v1/endpoints/notifications.py`: Added `@router.get("/")` alias route to avoid 307 trailing slash redirects.
- `backend/Dockerfile`: Added `--proxy-headers --forwarded-allow-ips '*'` to Uvicorn command.
- `backend/app/main.py`: Added `ProxyHeadersMiddleware` with trusted hosts wildcard.

### [BUG-045] Cloud Build Trigger Failure Under Custom Service Account Due to Missing Logging Configuration
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: CI/CD / Google Cloud Build / Infrastructure
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When executing automated Google Cloud Build workflows (`cloudbuild.yaml`) triggered on git commit pushes, builds utilizing a custom/user-managed Google Cloud service account failed immediately at initiation with the error:
`generic::invalid_argument: if 'serviceAccount' is specified, the build must specify a Cloud Storage bucket for logging or specify logging option CLOUD_LOGGING_ONLY`.

#### 2. Root Cause Analysis (RCA)
By default, Google Cloud Build attempts to stream logs to default Google-managed Cloud Storage buckets. When builds are configured with a custom service account for least-privilege security access rather than the default compute service account, Google Cloud requires an explicit build option designating whether build logs should stream to a dedicated storage bucket or directly to Google Cloud Logging.

#### 3. Solution & Architectural Strategy
Configured `options: logging: CLOUD_LOGGING_ONLY` in the root configuration block of `cloudbuild.yaml`. This routes all build logs directly into Google Cloud Logging without mandating external storage bucket provisioning while ensuring build invocations under custom service accounts succeed seamlessly.

#### 4. Files Modified / What Changed
- `cloudbuild.yaml`: Added `options: logging: CLOUD_LOGGING_ONLY`.

### [BUG-044] Archived Avoidance Zone Media (Photos & Videos) Missing in Archive Center Zone Details Modal
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Backend / Admin Archive Center / Zone Details
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When administrators inspected deactivated or expired flood avoidance zones in the Archive Center (`/admin/archive` -> **Spatial Data** -> **Archived Zones**) by clicking the view/details action icon, the `ZoneDetailsModal` displayed hazard attributes, coordinates, and metadata, but completely lacked any attached media (photos and videos), even when the avoidance zone was created with direct media uploads or originated from citizen flood reports with photographic evidence. In contrast, `ReportDetailsModal` in the adjacent Archived Reports tab rendered evidence thumbnails.

#### 2. Root Cause Analysis (RCA)
1. **Frontend Omission**: `ZoneDetailsModal.tsx` was built with attribute sections (Hazard & Severity, Timing & Lifecycle, Location & Coordinates, Operational Notes) but omitted a media gallery section and never parsed `media_urls` or `report_media_urls`.
2. **Backend Aggregation Limitation**: In `backend/app/api/v1/endpoints/admin.py`, the internal helper `_attach_report_media` only inspected `zone.primary_report.media_urls` rather than aggregating across all associated child reports in `zone.reports`.
3. **Lazy Loading Exclusion**: In `backend/app/crud/report.py`, `get_all_avoidance_zones_filtered` did not include eager loading (`selectinload(models.FloodAvoidanceZone.reports)`) or author profile loading for avoidance zones, risking detached instance queries or empty child collections when assembling media lists.

#### 3. Solution & Architectural Strategy
1. **Aggregated Media Serialization**: Updated `_attach_report_media` in `admin.py` to aggregate media URLs from all linked reports (`zone.reports`) alongside the zone's direct `media_urls`, preserving source attribution tags (`"Zone"` vs `"Report"`).
2. **Eager Loading in CRUD**: Enhanced `get_all_avoidance_zones_filtered` in `crud/report.py` to eagerly load `reports`, `user`, and `profile` via `selectinload`.
3. **Attached Media & Evidence Gallery**: Built an **Attached Media & Evidence** gallery in `ZoneDetailsModal.tsx` supporting:
   - Dynamic photo and video thumbnail previews with video indicator badges (`Video` Lucide badge).
   - Source provenance tags indicating whether media was directly attached to the official zone or contributed by an associated field report.
   - Click-to-preview functionality opening full-resolution media in a secure new browser tab.
   - Empty state fallback showing a camera icon with "No attached photos or video evidence for this zone."
4. **ArchivePage Media Prop Forwarding**: Passed `onOpenMedia={(url) => window.open(url, '_blank')}` to `ReportDetailsModal` in `ArchivePage.tsx` for cross-modal interaction parity.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Updated `_attach_report_media` to aggregate media from all linked reports and combine with zone media.
- `backend/app/crud/report.py`: Added `selectinload` for `reports`, `user`, and `profile` in `get_all_avoidance_zones_filtered`.
- `frontend/src/features/archive/components/ZoneDetailsModal.tsx`: Added Attached Media & Evidence gallery with photo/video preview, badges, and source tags.
- `frontend/src/features/archive/ArchivePage.tsx`: Connected `onOpenMedia` handler on `ReportDetailsModal`.

### [BUG-043] Archive Center Archived Posts 500 Error on 'Profile' Object Has No Attribute 'full_name'
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Backend / Admin Archive Center / Post Serialization
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When browsing `/admin/archive` and navigating to the "Archived Posts" tab (or toggling between "Deleted Posts" and "Hidden Posts"), the backend terminal reported repeated `500 Internal Server Error` exceptions with the message:
```text
AttributeError: 'Profile' object has no attribute 'full_name'
Unhandled Exception on GET /api/v1/admin/posts/archived: 'Profile' object has no attribute 'full_name'
```
This caused the archived posts table to fail to load records whenever any archived or hidden post had an author or remover with an existing user profile.

#### 2. Root Cause Analysis (RCA)
In `backend/app/api/v1/endpoints/admin.py`, the serialization block in `get_archived_community_posts` and `restore_archived_post` attempted to resolve author and moderator names using `post.user.profile.full_name`, `post.deleted_by.profile.full_name`, and `post.hidden_by.profile.full_name`.
However, the `Profile` SQLAlchemy model (`backend/app/models/profile.py`) stores names as separate `first_name` and `last_name` columns; it does not contain a `full_name` column or property. Accessing the non-existent attribute raised an unhandled `AttributeError`, aborting the request with HTTP 500.

#### 3. Solution & Architectural Strategy
Created a centralized helper function `_get_user_display_name(user: Optional[models.User], fallback: Optional[str] = "Unknown") -> Optional[str]` that safely inspects `user.profile` and constructs the full name via `f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip()`. If the profile or names are empty, it gracefully falls back to `user.username`, and ultimately to the supplied fallback string or `None`. Replaced all direct `.full_name` attribute accesses across the post archive endpoints.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Added `_get_user_display_name` helper and replaced all `profile.full_name` property accesses in `get_archived_community_posts` and `restore_archived_post`.

### [BUG-042] Profile Page Settings "Hide Profile Picture" Lag & Inoperative Camera Action Options
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Profile / Photo Management / React Query Cache
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On the `/profile` page:
1. Toggling "Hide Profile Picture" in the Settings tab exhibited UI lag or appeared unresponsive because the change was not updated optimistically in React Query state, resulting in switch bounce.
2. Clicking the camera icon on the user avatar opened a dropdown with three options ("View Profile Picture", "Change Profile Picture", "Hide Profile Picture"). All three options were non-functional dummy buttons that merely closed the dropdown menu without executing any action.
3. The "Hide Profile Picture" option was redundantly duplicated inside both the camera button dropdown and the Settings tab.

#### 2. Root Cause Analysis (RCA)
1. In `useProfile.ts`, `updateProfileMutation` only called `queryClient.invalidateQueries({ queryKey: ['auth-user'] })` in `onSuccess` without optimistic state updates (`onMutate`) or immediate `setQueryData` cache synchronization. As a result, the UI had to wait for an asynchronous background refetch over HTTP to re-render, creating visual delays and apparent switch failure.
2. In `ProfileView.tsx`, the camera dropdown items ("View Profile Picture" and "Change Profile Picture") were placeholder buttons executing only `setShowAvatarMenu(false)`. No image viewer modal or file upload pipeline existed.
3. "Hide Profile Picture" was unnecessarily placed in the camera button dropdown when the official switch is centralized under Profile Settings.

#### 3. Solution & Architectural Strategy
1. **Optimistic Updates & Immediate Cache Synchronization**: Enhanced `useProfile.ts` with `onMutate` to immediately write updated profile state into `['auth-user']` with automatic rollback on failure, and `onSuccess` to synchronize `['auth-user']`, `['my-posts']`, and `['posts']`.
2. **View Profile Picture Modal**: Built a dedicated preview modal in `ProfileView.tsx` showing the high-resolution avatar, username, handle, and a privacy status badge ("Hidden from public") when enabled, along with action shortcuts. Also made clicking the avatar in the header directly open this modal.
3. **Change Profile Picture Pipeline**: Implemented file input triggering with image format verification (JPEG, PNG, WebP) and a 10MB size guard, uploading directly to Cloudinary via backend endpoint `POST /api/v1/users/me/avatar`.
4. **Remove Picture Capability**: Added a "Remove Picture" action allowing users to revert to the default initials avatar via `DELETE /api/v1/users/me/avatar`.
5. **Redundant Option Excision**: Removed "Hide Profile Picture" from the camera dropdown per design requirements. Added outside-click dismissal to `showAvatarMenu`.

#### 4. Files Modified / What Changed
- `frontend/src/features/profile/ProfileView.tsx`: Implemented View Profile Picture Modal, file selection handler, avatar dropdown cleanup, and outside-click handler.
- `frontend/src/hooks/useProfile.ts`: Added optimistic updates, cache synchronization, and `uploadAvatar`/`removeAvatar` mutations.
- `backend/app/api/v1/endpoints/users.py`: Added `POST /me/avatar` and `DELETE /me/avatar` endpoints with MIME type validation.

### [BUG-041] Database Connection Pool Exhaustion (QueuePool limit 20 overflow 10 reached) Caused by Persistent Streaming SSE Endpoints
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Backend / Database Pooling / Server-Sent Events (SSE) / LiveSync
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On the production Cloud Run backend service (`lanes-api`), continuous client streaming calls to `/api/v1/sync` and `/api/v1/sse` resulted in severe database connection pool exhaustion errors:
`sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached, connection timed out, timeout 30.00`.
Subsequent API requests across the entire platform failed with HTTP 500 until the container restarted.

#### 2. Root Cause Analysis (RCA)
1. In FastAPI endpoints `sse.py` and `sync.py`, the database session dependency (`db: Session = Depends(get_db)`) was injected directly at the endpoint signature level.
2. In FastAPI generator-based streaming responses (`StreamingResponse`), dependency cleanup (`get_db()`'s `yield` context manager) does not close or return the database connection to the SQLAlchemy `QueuePool` until the generator is closed.
3. Because SSE connections are long-lived and persistent, each connected client held an exclusive PostgreSQL connection check-out indefinitely. Once more than 30 clients connected, the pool (size 20 + overflow 10) was completely starved, blocking all other endpoints.

#### 3. Solution & Architectural Strategy
1. **Removed Session Dependency from Streaming Signatures**: Removed `db: Session = Depends(get_db)` from the long-lived streaming endpoints in `sse.py` and `sync.py`.
2. **Ephemeral Sessions Per Event/Poll**: Refactored the internal event generator loops to instantiate short-lived worker sessions (`with SessionLocal() as session:`) strictly for the duration of the query snapshot, immediately closing and returning the connection to the pool between polling intervals.
3. **Database Pool Configuration Hardening**: Tuned `pool_size`, `max_overflow`, and `pool_pre_ping=True` in `database.py` to ensure resilient recycling under high concurrency.
4. **Client-Side Reconnect Resilience**: In `useLiveSync.ts` and `useSSE.ts`, added exponential backoff, visibility-based pause/resume, and proper unmount aborts to avoid reconnect storms.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/sync.py`: Refactored streaming generator to use ephemeral database sessions.
- `backend/app/api/v1/endpoints/sse.py`: Removed long-lived DB dependency injection from streaming generator.
- `backend/app/core/database.py`: Hardened pool size, overflow limits, and pre-ping connectivity tests.
- `frontend/src/hooks/useLiveSync.ts`: Added tab visibility awareness and resilient backoff.
- `frontend/src/hooks/useSSE.ts`: Added connection teardown cleanup.

### [BUG-040] AI Weather Insights Failed with 500 on Production Domain Due to Hardcoded Relative Fetch and Build-Time Rewrite Mismatch
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Production Cloud Infrastructure / Weather Insights
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On the production deployment (`https://navlanes.live`), opening the AI Weather Insights modal on the landing page failed with `500 Internal Server Error`, while the local dev environment and direct Cloud Run endpoint (`https://lanes-api-557679867071.asia-east1.run.app/api/v1/weather/insights`) responded with `200 OK`.

#### 2. Root Cause Analysis (RCA)
1. In `WeatherInsightsModal.tsx`, the API request hardcoded a relative URL path (`fetch('/api/v1/weather/insights')`) rather than using `process.env.NEXT_PUBLIC_API_URL`.
2. On Firebase App Hosting, the browser sent the request to the Next.js frontend container (`https://navlanes.live/api/v1/weather/insights`) instead of the Cloud Run API.
3. In `frontend/apphosting.yaml`, `BACKEND_URL` only had `RUNTIME` availability. During `next build`, Next.js rewrites in `next.config.ts` evaluated `process.env.BACKEND_URL` as undefined, falling back to `http://127.0.0.1:8000`. Because no backend runs inside the App Hosting container, Next.js server proxies failed and returned `500 Internal Server Error`.

#### 3. Solution & Architectural Strategy
1. Standardized `WeatherInsightsModal.tsx` to read `process.env.NEXT_PUBLIC_API_URL || '/api/v1'` matching `ForecastChart.tsx`, `apiClient.ts`, and auth components. The browser now calls the live Cloud Run backend gateway directly.
2. Added `BUILD` availability to `BACKEND_URL` in `apphosting.yaml` so any server-side Next.js rewrites correctly resolve `https://lanes-api-557679867071.asia-east1.run.app` at build time.

#### 4. Files Modified / What Changed
- `frontend/src/features/landing/WeatherInsightsModal.tsx`: Updated fetch call to use `NEXT_PUBLIC_API_URL`.
- `frontend/apphosting.yaml`: Added `BUILD` availability to `BACKEND_URL`.

### [BUG-039] TerraDraw Source Collision ("td-polygon already exists") and Perpetual Map Style Reload Loop in Edit Flood Zone
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Map / Admin Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In `/admin/map`, when an administrator opened an existing road flood zone (e.g. Zone #1) and switched Spatial Geometry to Polygon mode, clicking on the map did not draw vertices and the instruction banner did not appear. The browser console reported `Failed to initialize TerraDraw: Error: Source "td-polygon" already exists`. Simultaneously, the map style entered an infinite background reload loop every 40–120 seconds due to MapTiler 403 Forbidden errors, wiping active layers and disrupting drawing interactions.

#### 2. Root Cause Analysis (RCA)
1. **Competing TerraDraw Instances**: Both CreateOfficialZonePanel (Pane 1) and EditOfficialZonePanel (Pane 2) were mounted simultaneously in `LiveMapPage.tsx`. In `OfficialZoneDrawer.tsx`, `useTerraDraw` was called with `isEnabled: true` hardcoded instead of `isEnabled: isOpen`. Pane 1 claimed `td-polygon` on `mapInstance`, so when Pane 2 mounted upon clicking "Edit", `draw.start()` threw `Source "td-polygon" already exists`, leaving `drawRef.current` null and the drawing tool uninitialized.
2. **Missing Mode Sync Dependency**: In `useTerraDraw.ts`, the mode sync effect did not depend on `drawInstance`. When TerraDraw finished asynchronous initialization after the component had already switched to `polygon`, the mode sync effect did not re-fire, leaving TerraDraw in `static` mode with `isDrawingMode` as false.
3. **Unbounded Retries on 403**: In `BaseMap.tsx`, `schedulePrimaryRetry` continually attempted to reapply the primary MapTiler style without checking whether the failure was a permanent authorization error (401/403).

#### 3. Solution & Architectural Strategy
1. **Instance Gating**: Gated `useTerraDraw` with `isEnabled: isOpen` so only the currently active, visible drawer connects TerraDraw to the map.
2. **Robust Cleanup**: Hardened `removeStaleTerraDrawArtifacts` to purge all `td-*` layers (outline, markers, fills) and sources (`td-polygon`, `td-linestring`, `td-point`) in proper detachment order before adapter creation and upon drawer unmount.
3. **Immediate Mode Activation**: Applied active mode immediately upon `draw.start()` and added `drawInstance` to mode sync dependencies so the crosshair cursor and instruction banner activate directly.
4. **Permanent Auth Throttling**: Added `isPermanentAuthError` detection in `BaseMap.tsx` to halt automated retries on 401/403 or invalid keys, preventing background style reload loops.
5. **Visual-Readiness Optimization**: Uses the first MapLibre render after `style.load` as the usability signal rather than waiting for all font glyph ranges. DNS/TLS preconnect and production PWA caching reduce cold connection work and accelerate later visits.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx`: Changed `isEnabled` to `isOpen` in `useTerraDraw` and added drawing restoration from `polygonSessionCacheRef` when `drawInstance` becomes ready.
- `frontend/src/features/admin/components/zones/hooks/useTerraDraw.ts`: Hardened layer/source cleanup in `removeStaleTerraDrawArtifacts`, set mode directly on start, and included `drawInstance` in mode sync dependencies.
- `frontend/src/shared/ui/map/BaseMap.tsx`: Throttled retries and halted automated style reload loop on permanent 401/403 errors.
- `frontend/src/app/layout.tsx`, `frontend/next.config.ts`: Added MapTiler connection hints and runtime caching for styles, glyphs, sprites, and tiles.
- `frontend/src/features/admin/LiveMapPage.tsx`: Isolated active zone layer so only the reference line represents the zone during editing.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Added `showMarkers` prop to hide pins in polygon mode while keeping the reference line.
- `frontend/src/features/map/MapContext.tsx`: Exposed `floodShowMarkers` state and setter.
- `frontend/src/features/admin/components/AdminFloodMapInteraction.tsx`: Forwarded `floodShowMarkers` to preview hook.
- `frontend/src/features/map/MapCanvas.tsx`: Forwarded `floodShowMarkers` to preview hook.

### [BUG-038] MapTiler Recovery and TerraDraw Could Retain Stale Map State
- **Status**: Resolved in code / manual verification pending
- **Severity**: High
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Map / Admin Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After an initial MapTiler-to-OSM fallback, successful MapTiler retries could continue to log `primary_retry_timeout`. Separately, reopening an Admin polygon workspace could fail with `Source "td-polygon" already exists`.

#### 2. Root Cause Analysis (RCA)
The fallback detector checked generic/nonexistent OSM identifiers, while MapTiler styles may also define a generic `osm` source. TerraDraw's deferred `style.load` initialization could run after React cleanup and leave its adapter layers/sources on the current MapLibre style.

#### 3. Solution & Architectural Strategy
The fallback style now uses LANES-specific source/layer identifiers and validates the actual active style before accepting a retry. TerraDraw cancels the deferred listener during cleanup and removes only its known stale adapter artifacts before creating its single replacement instance.

#### 4. Files Modified / What Changed
- `frontend/src/shared/ui/map/BaseMap.tsx`: Added LANES-specific OSM fallback identity and reliable active-style matching.
- `frontend/src/features/admin/components/zones/hooks/useTerraDraw.ts`: Added deferred-listener cleanup and safe stale TerraDraw artifact removal.

### [BUG-037] MapTiler Startup Timeout Recreated the Map and Prevented Automatic Detailed-Style Restoration
- **Status**: Resolved in code / manual verification pending
- **Severity**: Medium
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Map / PWA
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On `/map`, MapTiler could wait through a 2-second network preflight and an 8-second style watchdog before switching to OSM. Repeated retries destroyed and recreated the WebGL map, producing noisy browser logs and delaying access to a usable map. The fallback status could also overlap desktop map controls.

#### 2. Root Cause Analysis (RCA)
The map lifecycle treated MapTiler availability as a blocking preflight and recreated `MapLibre.Map` for each recovery attempt. After replacing the initial timed-out MapTiler style with OSM, the lifecycle did not mark that first successful fallback style as complete; later MapTiler `style.load` events were therefore ignored, even when the browser had successfully retrieved the style and tiles.

#### 3. Solution & Architectural Strategy
Removed the preflight and recreation loop. One MapLibre instance now starts with MapTiler and switches in place to OSM after 1.5 seconds or a confirmed MapTiler resource error. Attempt IDs, timer cleanup, and redacted structured diagnostics protect against stale callbacks. OSM is immediately usable; MapTiler retries on the `online` event and exponential backoff, with a six-second recovery window. Completing OSM marks the lifecycle ready for a later successful MapTiler `style.load`; existing feature hooks restore layers after each style replacement. The recovery notice is fixed to the viewport, constrained responsively, and placed below the desktop floating navigation.

#### 4. Files Modified / What Changed
- `frontend/src/shared/ui/map/BaseMap.tsx`: Implemented one-instance startup/fallback/retry lifecycle, diagnostics, lifecycle-completion guard, and responsive recovery notice.
- `frontend/src/features/map/MapCanvas.tsx`: Removed the unused duplicate hardcoded MapTiler style state.
- `frontend/apphosting.yaml`, `frontend/.env.local`: Centralized browser style configuration under `NEXT_PUBLIC_MAPTILER_KEY`; production configuration references the `maptiler-api-key` App Hosting secret.

---

### [BUG-036] Live Sync SSE Stream Exhausts SQLAlchemy Connection Pool Causing Cascading 500 & Apparent CORS Errors
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Database / SSE / Sync / CORS
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In production, all public API requests (`/api/v1/public/stats`, `/api/v1/feed`, `/api/v1/reports/active-zones`) began hanging for 30 seconds and failing with `HTTP 500 Internal Server Error: QueuePool limit of size 20 overflow 10 reached, connection timed out, timeout 30.00`. In web browsers, these failed requests appeared as `Access to fetch at ... has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource`.

#### 2. Root Cause Analysis (RCA)
1. **Connection Leak in SSE Streaming Endpoint**: The `/api/v1/sync/stream` endpoint had `db: Session = Depends(get_db)`. In FastAPI, dependencies provided via `Depends(get_db)` remain checked out for the entire lifetime of the HTTP connection. Because `EventSourceResponse` runs an infinite polling loop (`while True: await asyncio.sleep(10)`), each connected client held an active PostgreSQL database connection indefinitely. As soon as ~30 clients connected (or reconnects triggered), the entire connection pool was exhausted.
2. **Cascading Reconnect Storm**: When connections timed out, the SSE generator threw an unhandled exception, closing the stream. The frontend's `EventSource` automatically reconnected, requesting another connection and exacerbating the deadlock.
3. **CORS Masking of 500 Errors**: Starlette's raw `ServerErrorMiddleware` catches unhandled exceptions and outputs a plain `text/plain` 500 response without passing through `CORSMiddleware`. Browsers blocked reading the 500 error response due to missing `Access-Control-Allow-Origin` headers, making server database timeouts masquerade as CORS errors in developer tools.

#### 3. Solution & Architectural Strategy
1. **Short-Lived Sessions in Background Worker**: Removed `db: Session = Depends(get_db)` from `/api/v1/sync/stream`. Created `_get_active_floods_safe()` using `with SessionLocal() as db:` wrapped in `try/finally: db.close()`. Executed it using `await asyncio.to_thread(_get_active_floods_safe)` so that database checkouts only last milliseconds and 0 connections are held during the 10-second SSE idle sleep.
2. **Graceful Exception Fallback**: If a database blip occurs during live sync, `_get_active_floods_safe()` catches the exception and returns empty results rather than crashing the client's SSE connection and triggering reconnect storms.
3. **Calibrated Engine Pool**: Added `pool_timeout=10` to `create_engine` (reduced from 30s) and increased pool limits (`pool_size=25`, `max_overflow=20`) to prevent requests from hanging indefinitely during spikes.
4. **Global Exception Handler**: Added `@app.exception_handler(Exception)` in `backend/app/main.py` returning `JSONResponse(status_code=500)` so that uncaught server errors always pass through `CORSMiddleware` and supply proper CORS headers to the client.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/sync.py`: Removed `Depends(get_db)` from streaming route; decoupled queries into short-lived thread-pool sessions.
- `backend/app/core/database.py`: Added `pool_timeout=10` and tuned pool size to fail fast and accommodate burst traffic.
- `backend/app/main.py`: Added global `Exception` handler returning `JSONResponse` with CORS headers.

---

### [BUG-035] Flood-Routing Providers Return Inconsistent and Non-Route-Specific Safety Results
- **Status**: Resolved in code / Cloud verification pending
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Routing / Valhalla / OpenRouteService / Route Planner
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Valhalla and ORS do not currently apply the same flood passability rules or return trustworthy per-route flood metadata. A user can receive a blocked direct ORS route alongside safe routes, while the equivalent Valhalla path is suppressed. Cautious pedestrian and high-clearance routing is only partially represented by Valhalla and absent from ORS. The active route cards therefore cannot consistently explain vehicle safety, danger, or ranking.

#### 2. Root Cause Analysis (RCA)
1. Both provider services independently query and classify active flood polygons instead of consuming one policy result.
2. `valhalla_service.py` submits `avoid_polygons`, although the Valhalla route API documents `exclude_polygons`; its direct-route risk assessment assumes every active orange/yellow zone was intersected.
3. `ors_service.py` uses only binary `avoid_polygons`, inserts an always-blocked direct route, and labels all surviving routes 100% safe without measuring their intersections.
4. There is no centralized post-route PostGIS intersection evaluator, common exposure score, deterministic category ranker, or parity test suite. The current focused routing tests also contain stale `httpx.post` mocks (6 passed, 4 failed).

#### 3. Solution & Architectural Strategy
Implemented a typed FastAPI flood-routing policy and active-zone loader as the sole source of business decisions. Valhalla receives documented `exclude_polygons`; ORS receives GeoJSON `options.avoid_polygons`; both produce raw candidates only. The shared evaluator intersects each candidate geometry with authoritative active-zone geometry, attaches deterministic exposure/safety metadata, rejects impassable routes, deduplicates overlaps, and assigns up to four distinct Fastest/Safest/Balanced/Alternative cards. Walking through Orange is a strongly cautioned 40% fallback; vehicles remain blocked and Red remains blocked for every public profile. A blocked baseline is returned only as a non-selectable explanation when it was the fastest raw choice. Offline cached zones now carry server-authored per-profile restriction metadata and legacy metadata is treated conservatively.

#### 4. Files Modified / What Changed
- `backend/app/services/flood_routing_policy.py`, `routing_service.py`: Added shared policy, authoritative-zone evaluation, exposure scoring, deduplication, and deterministic ranking.
- `backend/app/services/valhalla_service.py`, `ors_service.py`, `report_service.py`: Converted current route flow to provider adapters, corrected polygon payloads, and synchronized offline restriction metadata.
- `backend/app/schemas/route.py`, `backend/tests/test_flood_routing_policy.py`, `backend/tests/test_routing_service.py`: Extended the contract and added/updated focused coverage (20 passing tests).
- `frontend/src/features/routing/routingApi.ts`, `RoutePanel.tsx`, `MapContext.tsx`, `workers/valhallaCore.ts`: Render route categories/exposure and a non-selectable blocked explanation on responsive layouts; keep offline routing fail-closed.
- `frontend/src/features/landing/FloodLegend.tsx`, `frontend/src/features/hazards/FloodReportPanel.tsx`: Corrected Medium-water passability wording.
- `docs/task_plan.md`, `docs/others/routing-logic.md`, `docs/others/vehicle-passability.md`, `docs/others/system-documentation.md`: Updated the policy and verification record.

### [BUG-034] Admin Login Redirection Routing to /feed Instead of /admin/dashboard
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Authentication / Client-Side Routing / Role-Based Access Control
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When logging in with an administrative account (e.g., `Super Admin`, `DRRM Officer`, `Moderator`), users were erroneously redirected to the `/feed` page (or `/feed?openPostModal=true`) instead of the admin dashboard (`/admin/dashboard`).

#### 2. Root Cause Analysis (RCA)
1. In `LoginForm.tsx`, `useGoogleAuth.ts`, and `login/page.tsx`, URL redirection (`redirectTo`) and guest post intent (`lanes_post_intent` stored in `sessionStorage` when unauthenticated users interacted with "Create Post" in the feed) were evaluated before checking user role (`isAdminRole`).
2. If `redirectTo` pointed to `/feed` or `/login?redirect=%2Ffeed`, or if `lanes_post_intent` was persisted in `sessionStorage`, the login process dispatched `router.push(redirectTo)` or `router.push('/feed?openPostModal=true')` immediately, bypassing the admin dashboard redirection logic entirely.
3. In `NavigationWrapper.tsx`, route guards only checked exact equality for `Super Admin` and lacked normalized coverage for other staff/admin roles, allowing admins to remain on or be directed to commuter pages.

#### 3. Solution & Architectural Strategy
1. **Admin-First Priority**: Inverted the navigation decision tree across `LoginForm.tsx`, `login/page.tsx`, and `useGoogleAuth.ts` so that `isAdminRole` is evaluated before any commuter post intent or public redirect targets.
2. **Post Intent Clearing**: When an admin account logs in, `sessionStorage.removeItem("lanes_post_intent")` is immediately invoked to purge any guest commuter draft intents.
3. **Target Routing**: If an admin account logs in with an explicit admin destination (`redirectTo.startsWith("/admin")`), they navigate directly to that sub-route; otherwise, they default to `/admin/dashboard`.
4. **Hardened Route Guards**: Updated `NavigationWrapper.tsx` to ensure any non-staff user attempting to access `/admin` is ejected to `/`, while `Super Admin` accounts visiting public routes are forwarded to `/admin/dashboard`.

#### 4. Files Modified / What Changed
- `frontend/src/features/auth/LoginForm.tsx`: Prioritized `isAdminRole` in post-login navigation, cleaned up session post intents, and routed non-admin deep-links appropriately.
- `frontend/src/app/(auth)/login/page.tsx`: Aligned the `useEffect` auth redirection logic so authenticated admin sessions navigate directly to `/admin/dashboard`.
- `frontend/src/features/auth/hooks/useGoogleAuth.ts`: Updated Google OAuth completion navigation to enforce the same admin-first routing priority.
- `frontend/src/features/navigation/NavigationWrapper.tsx`: Hardened role checks to recognize staff accounts and enforce route boundaries.

---

### [BUG-033] Forgot Password Link on Login Form Was an Inert Anchor Tag
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Backend / Authentication / Password Recovery
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The "Forgot password?" link on the login form was an inert `<a href="#">` element with no backend password recovery endpoints or verification workflow.

#### 2. Root Cause Analysis (RCA)
No password reset endpoints or client-side recovery views had been created. The platform required a secure, OTP-verified reset flow adhering to strict anti-enumeration and brute-force protection standards.

#### 3. Solution & Architectural Strategy
1. **Backend Endpoints & Cryptographic Security**:
   - `POST /api/v1/auth/forgot-password/request-otp`: Checks user status and resend cooldown eligibility; returns a generic success response to prevent email enumeration.
   - `POST /api/v1/auth/forgot-password/verify-otp`: Validates the 6-digit OTP against active codes and mints a signed 15-minute `reset_token` (JWT with `scope: "password_reset"`).
   - `POST /api/v1/auth/forgot-password/reset`: Validates the JWT signature and scope, enforces password complexity, updates `user.hashed_password`, purges OTP records, and logs `PASSWORD_RESET_SUCCESS`.
2. **Branded Email Notification**: Created `send_password_reset_email_async` delivering a clean, hosted-branding HTML email via Resend with single-use OTP code and expiry warnings.
3. **Consistent UI Experience**:
   - Created `ForgotPasswordForm` featuring a pixel-for-pixel consistent design with the registration flow: identical 6-box OTP inputs, auto-advance, clipboard paste support, progressive resend timer, `<PasswordStrength>` validation meter, and hold-to-view eye icons.
   - Integrated in-place transition into `LoginForm` preserving the split-screen Agnes background shell on desktop and mobile.
   - Added `/forgot-password` route redirection to `/login?forgot=true`.

#### 4. Files Modified / What Changed
- `backend/app/core/security.py`: Added `create_password_reset_token` and `verify_password_reset_token`.
- `backend/app/schemas/auth.py` & `backend/app/schemas/__init__.py`: Added password reset request/verify/confirm schemas.
- `backend/app/crud/user.py` & `backend/app/crud/__init__.py`: Added `update_user_password`.
- `backend/app/services/email_service.py`: Added `send_password_reset_email_async`.
- `backend/app/services/auth_service.py`: Added `generate_and_send_password_reset_otp`.
- `backend/app/api/v1/endpoints/auth.py`: Added `forgot-password/request-otp`, `verify-otp`, and `reset` endpoints with rate limiting.
- `backend/tests/test_forgot_password.py`: Unit test suite (7 tests) covering anti-enumeration, token forgery protection, and complexity rules.
- `frontend/src/features/auth/api/authClient.ts`: Added forgot password API calls.
- `frontend/src/features/auth/components/ForgotPasswordForm.tsx`: Created 4-phase animated recovery form.
- `frontend/src/features/auth/LoginForm.tsx`: Wired "Forgot password?" button to toggle recovery mode in-place.
- `frontend/src/app/(auth)/login/page.tsx`: Added dynamic header and view state binding.
- `frontend/src/app/(auth)/forgot-password/page.tsx`: Added fallback route redirecting to `/login?forgot=true`.

### [BUG-032] Google Sign-In and Registration Buttons Were Inert Placeholders
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Backend / Authentication / OAuth
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The "Sign in with Google" and "Sign up with Google" buttons on the Login and Registration forms were static UI placeholders that displayed an "Under Development" toast rather than executing an OAuth authentication flow.

#### 2. Root Cause Analysis (RCA)
Google OAuth 2.0 Web Client credentials had not yet been integrated into the system, and the backend lacked an endpoint to verify Google ID tokens / OAuth access tokens and authenticate or register users.

#### 3. Solution & Architectural Strategy
1. **Google Identity Services Integration**: Created `useGoogleAuth` hook using Google's modern GIS library (`accounts.google.com/gsi/client`) and `initTokenClient` for popup-blocker-free custom button authorization.
2. **Backend OAuth Gateway**: Added `POST /api/v1/auth/google` with rate limiting and audience verification (`GOOGLE_CLIENT_ID`) protecting against token substitution attacks.
3. **Intent-Specific Auth Flow (Strict Login vs Auto-Fill Signup)**:
   - **Login Mode**: When signing in from `/login`, unregistered Google accounts are rejected with HTTP 404 (`"No registered account found with this Google email. Please sign up first."`) displayed via a standard error toast.
   - **Register Mode**: Clicking "Sign up with Google" on `/register` fetches the user's verified Google profile and auto-populates their email, first name, last name, avatar, and suggested username, skipping redundant email OTP verification and password creation. The user completes their birthdate, contact number, and address before the account is provisioned.
4. **Environment Configuration**: Encrypted `GOOGLE_CLIENT_ID` in `backend/.env` and `NEXT_PUBLIC_GOOGLE_CLIENT_ID` in `frontend/.env.local` using `@dotenvx/dotenvx`, documented in `.env.example` and `apphosting.yaml`.

#### 4. Files Modified / What Changed
- `backend/app/core/config.py`: Added `GOOGLE_CLIENT_ID` to backend settings.
- `backend/app/schemas/auth.py` & `backend/app/schemas/__init__.py`: Added `GoogleAuthRequest` and `GoogleAuthResponse`.
- `backend/app/services/auth_service.py`: Added `verify_google_token` and `authenticate_or_register_google_user` supporting `login` and `register` modes with Profile and Address provisioning.
- `backend/app/api/v1/endpoints/auth.py`: Added `POST /auth/google` route.
- `backend/tests/test_google_auth.py`: Unit tests verifying audience checks, token verification, and unregistered user rejection.
- `frontend/src/features/auth/api/authClient.ts`: Added `loginWithGoogle` API method.
- `frontend/src/features/auth/hooks/useGoogleAuth.ts`: Created GIS OAuth hook with `signInWithGoogle` and `getGoogleUserProfile`.
- `frontend/src/features/auth/LoginForm.tsx`: Wired "Sign in with Google" button with error toast handling.
- `frontend/src/features/auth/components/RegisterForm.tsx`: Wired "Sign up with Google" auto-fill flow, step validation bypass, and connected Google account badge.
- `frontend/apphosting.yaml` & `backend/.env.example`: Documented Google Client ID.

### [BUG-031] Valhalla Production Route Requests Targeted an Absent Local Container
- **Status**: Resolved in code / Pending Cloud rollout
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Routing / Cloud Run
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The deployed `POST /api/v1/reports/route` request returned HTTP 503 when Valhalla was selected.

#### 2. Root Cause Analysis (RCA)
Cloud Run ran only FastAPI while `VALHALLA_URL` retained the local Docker address `http://localhost:8002`; no Valhalla process exists in that container.

#### 3. Solution & Architectural Strategy
Added a private Cloud Run Valhalla deployment flow backed by versioned Cloud Storage tiles, authenticated FastAPI-to-Valhalla calls, and automatic ORS fallback only for Valhalla availability failures.

#### 4. Files Modified / What Changed
- `infrastructure/valhalla/`: Reproducible artifact build and private-service deployment assets.
- `backend/app/services/routing_service.py`: Provider fallback and response metadata.
- `frontend/src/features/routing/RoutePanel.tsx`: Matching desktop/mobile fallback explanation.

### [BUG-030] Production Fallback Credentials Are Present in the Backend Code Path
- **Status**: Investigating
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Authentication / Cloud Run Configuration
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The Cloud Run image deliberately excludes `backend/.env`, but the backend accepts a source-controlled fallback JWT signing secret when `SECRET_KEY` is missing. Its startup routine can also seed a predictable `admin/admin` account when the roles table is empty. This makes a missing or incorrectly injected Cloud Run secret a critical production security failure.

#### 2. Root Cause Analysis (RCA)
`backend/app/core/config.py` defines a concrete default `SECRET_KEY`, and `backend/app/main.py` creates the default administrator in the lifespan routine. Neither behavior is guarded by a production-environment check. The repository deployment files do not define the Cloud Run `SECRET_KEY` injection, so the codebase cannot verify that the secure runtime setting overrides the fallback.

#### 3. Solution & Architectural Strategy
Provision a unique `SECRET_KEY` as a Cloud Run secret and fail startup outside local development when it is absent. Remove production default-admin seeding; bootstrap an administrator with an explicit one-time deployment command or a securely supplied, rotated credential. Confirm the active Cloud Run revision has the secret before considering the deployment secure.

#### 4. Files Modified / What Changed
- `docs/others/bug-log.md`: Recorded the production credentials investigation and required remediation.
- `backend/app/core/config.py`: Requires environment-aware secret validation.
- `backend/app/main.py`: Requires production-safe administrator bootstrap behavior.

### [BUG-029] Weather Insights Uses a Build-Time Backend Rewrite Without a Build-Time Destination
- **Status**: Investigating
- **Severity**: High
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Firebase App Hosting / Production API Routing
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The weather-insights modal sends its request to the relative URL `/api/v1/weather/insights`, unlike the rest of the production client, which uses `NEXT_PUBLIC_API_URL` to call Cloud Run directly. In Firebase App Hosting, the relative request depends on the Next.js rewrite in `frontend/next.config.ts`. That rewrite can be compiled with its localhost fallback rather than the Cloud Run URL, causing only the **Generate AI Insights** action to fail in production while weather and other direct API calls continue to work.

#### 2. Root Cause Analysis (RCA)
`frontend/next.config.ts` constructs the rewrite destination from `process.env.BACKEND_URL`, with `http://127.0.0.1:8000` as its fallback. `frontend/apphosting.yaml` supplies `BACKEND_URL` only at `RUNTIME`; it does not make the value available during `BUILD`. Next.js resolves rewrite configuration while generating its build artifacts, so the deployment configuration does not guarantee that the production rewrite target is embedded in the build.

#### 3. Solution & Architectural Strategy
Use a single production API-resolution path. The preferred minimal fix is to update `WeatherInsightsModal.tsx` to use `NEXT_PUBLIC_API_URL` (with `/api/v1` as the local fallback), matching the other browser-side calls and avoiding a Next.js proxy hop. Alternatively, add `BUILD` availability to `BACKEND_URL` and retain the rewrite. After either change, run the production build and test the modal request against the deployed Cloud Run endpoint.

#### 4. Files Modified / What Changed
- `docs/others/bug-log.md`: Recorded the investigated production routing issue and remediation options.
- `frontend/src/features/landing/WeatherInsightsModal.tsx`: Requires the API URL resolution correction.
- `frontend/apphosting.yaml`: Requires `BACKEND_URL` build availability only if retaining the rewrite approach.

### [BUG-028] Cloud Run FastAPI Backend CORS Rejection on Firebase App Hosting Domains (*.hosted.app)
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 16, 2026
- **Affected Area**: Backend / Infrastructure / CORS / Firebase App Hosting
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Upon deploying the frontend Next.js application to Firebase App Hosting at `https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app`, opening the site in a browser triggered immediate cascading client-side network failures across all initial API fetches (`/weather/current`, `/weather/forecast`, `/reports/active-zones`, `/public/stats`) and streaming Server-Sent Events endpoints (`/sse/stream`, `/sync/stream`). The browser console logged:
`Access to fetch at 'https://lanes-api-557679867071.asia-east1.run.app/api/v1/...' from origin 'https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`

#### 2. Root Cause Analysis (RCA)
In `backend/app/main.py`, FastAPI's `CORSMiddleware` configured `allow_origin_regex` to match only:
`r"^(https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000|https://.*\.vercel\.app|https://.*\.navlanes\.live)$"`
Firebase App Hosting generates production and preview web domains ending with `.hosted.app`, `.web.app`, or `.firebaseapp.com`. Because none of these domains were included in either `origins` or `allow_origin_regex`, preflight `OPTIONS` and standard cross-origin `GET`/`POST` requests were rejected by Starlette's CORS filter without sending `Access-Control-Allow-Origin`.

#### 3. Solution & Architectural Strategy
Updated `allow_origin_regex` in `backend/app/main.py` to:
`r"^(https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000|https://.*\.vercel\.app|https://.*\.navlanes\.live|https://.*\.hosted\.app|https://.*\.web\.app|https://.*\.firebaseapp\.com)$"`
This securely permits all valid Firebase App Hosting rollouts and custom Firebase domains while maintaining strict origin sandboxing against arbitrary external domains.

#### 4. Files Modified / What Changed
- `backend/app/main.py`: Updated `allow_origin_regex` in `CORSMiddleware` to include `https://.*\.hosted\.app`, `https://.*\.web\.app`, and `https://.*\.firebaseapp\.com`.

### [BUG-027] Profile "Display Full Name" Setting Ignored in Community Feed and Comment Sections
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 14, 2026
- **Affected Area**: Backend / Frontend / Privacy & Community Feed / PostGIS SQL / REST API
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In the Profile Settings tab, users can toggle the **"Display Full Name"** preference (`Profile.display_full_name`), which promises to show their real full name on posts and profile instead of their username handle. However, the Community Feed post cards, single-post detail pages, and comment sections continued to strictly display `User.username`. In addition, client-side author checks for post pinning and comment editing compared string values of `author_name === username`, which broke when full names were used.

#### 2. Root Cause Analysis (RCA)
1. In `backend/app/crud/feed.py`, the feed query expressions for `get_feed_posts` and `get_feed_post` hardcoded `func.coalesce(User.username, text("'Unknown'")).label("author_name")` without evaluating `Profile.display_full_name` or concatenating `Profile.first_name` and `Profile.last_name`.
2. In `backend/app/api/v1/endpoints/comments.py`, comment responses hardcoded `c.user.username` for `author_name` instead of inspecting the author's profile privacy preferences.
3. In `frontend/src/features/feed/PostDetailPage.tsx`, author ownership permissions (`isPostAuthor` and `isOwn`) checked `(post as any).author_name === user.username` instead of matching primary keys (`user.id === post.user_id` / `user.id === comment.user_id`).

#### 3. Solution & Architectural Strategy
1. **Server-Side Privacy Resolution (`api-agent` + `security-agent`)**: Added `get_user_display_name(user)` helper in `backend/app/crud/user.py`. In `feed.py`, constructed a SQL `case()` expression that dynamically concatenates `first_name` and `last_name` when `display_full_name` is true (or default) and falls back strictly to `User.username` without exposing personal names to unprivileged queries.
2. **Comment Profile Eager Loading**: Updated `get_comments` to eager-load `joinedload(Comment.user).joinedload(User.profile)` to avoid N+1 queries, returning resolved `author_name` and `author_avatar`.
3. **Primary Key Ownership Verification (`ui-agent`)**: Updated `PostDetailPage.tsx` and `feedApi.ts` to include `user_id` on comment responses and evaluate ownership via numeric user IDs. Added author avatar rendering support to comment cards.

#### 4. Files Modified / What Changed
- `backend/app/crud/user.py`: Added `get_user_display_name` helper function.
- `backend/app/crud/feed.py`: Applied SQL `author_name_expr` conditional expression in `get_feed_posts` and `get_feed_post`.
- `backend/app/api/v1/endpoints/comments.py`: Eager loaded profiles and resolved `author_name` / `author_avatar` in comment builders.
- `backend/app/api/v1/endpoints/posts.py`: Updated post author fallback to use `get_user_display_name`.
- `frontend/src/features/feed/feedApi.ts`: Added `user_id` and `author_avatar` to `CommentResponse`.
- `frontend/src/features/feed/PostDetailPage.tsx`: Fixed `isPostAuthor` and `isOwn` logic to compare user IDs; added comment avatar support.

### [BUG-026] Mobile Layout Inset and Horizontal Margin Overflow in Profile Subtabs
- **Status**: Resolved
- **Severity**: Low
- **Date Reported / Resolved**: September 14, 2026
- **Affected Area**: Frontend / UI / Mobile Responsiveness (PWA)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On compact mobile screens (e.g., iPhone SE 375px, iPhone 12 390px), the Profile page's Posts and Reports tabs rendered with redundant nested horizontal padding (`px-4 sm:px-0`), creating visible left/right borders and shrinking usable card width.

#### 2. Root Cause Analysis (RCA)
Inner tab containers in `ProfileView.tsx` wrapped post and report item lists in an extra mobile padding block, causing double-margin inset on viewports under 640px.

#### 3. Solution & Architectural Strategy
Removed redundant mobile wrapper padding classes on the Posts and Reports subtab views in `ProfileView.tsx`, enabling seamless full-width card layout on mobile devices while preserving proper responsive gutters on desktop screens.

#### 4. Files Modified / What Changed
- `frontend/src/features/profile/ProfileView.tsx`: Flattened mobile margin hierarchy for profile subtabs.

### [BUG-025] Unauthenticated Navigation Tab Click Diverted to Profile Instead of Current View
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 14, 2026
- **Affected Area**: Frontend / Navigation / Authentication Flow
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When an unauthenticated commuter was exploring the Community Feed (`/feed`) or a specific post (`/feed/[id]`) and clicked the Profile navigation item to sign in, completing authentication always redirected them to `/profile` rather than returning them to the feed context they were browsing.

#### 2. Root Cause Analysis (RCA)
`FloatingNav.tsx` and `MobileNav.tsx` used hardcoded navigation handlers that routed unauthenticated users directly to `/login?redirect=/profile` regardless of their active page.

#### 3. Solution & Architectural Strategy
Updated navigation triggers to check the current `pathname` and preserve the active URL or return path in query parameters, allowing post-login redirection to gracefully return the user to their prior context.

#### 4. Files Modified / What Changed
- `frontend/src/features/navigation/FloatingNav.tsx`: Contextual auth redirect handling.
- `frontend/src/features/navigation/MobileNav.tsx`: Contextual auth redirect handling.

### [BUG-024] Community Sharing Helper Text Contradicted Actual Publication Timing
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Frontend / Backend / Flood Reports / Community Feed
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After a commuter selected **Share in Community Feed**, the submitted flood report appeared in the feed immediately, but the panel said that sharing would occur only after administrator approval. A second legacy publication branch also remained in the approval endpoint.

#### 2. Root Cause Analysis (RCA)
`process_new_report` had already made report submission the publication owner. `FloodReportPanel` retained pre-change wording, while `approve_report` retained an obsolete fallback that duplicated responsibility for the same lifecycle.

#### 3. Solution & Architectural Strategy
Community publication now has one owner: report submission. Map-zone approval remains exclusively responsible for official spatial activation. The helper text explicitly distinguishes immediate public sharing from later map approval.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Removes the obsolete approval-time Community Post creation branch.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: States the immediate feed-publication and separate map-approval behavior.
- `docs/task_plan.md`, `docs/progress.md`, and `docs/others/system-documentation.md`: Synchronize the documented workflow.

### [BUG-023] Flood Polygon Fetch Failure During Route Calculation Due to Property Join
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Backend / Routing / Flood Avoidance / PostGIS / Valhalla / ORS
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
During route calculation (`POST /api/v1/reports/route` / `calculate_flood_safe_route`), the backend logged a database warning:
`Warning: Failed to fetch flood polygons ((psycopg.ProgrammingError) cannot adapt type 'property' using placeholder '%s' (format: AUTO) [SQL: SELECT ST_AsGeoJSON(flood_avoidance_zones.geometry) AS geojson, flood_reports.severity AS flood_reports_severity FROM flood_avoidance_zones JOIN flood_reports ON flood_reports.id = %(id_1)s::INTEGER ...]). Bypassing flood avoidance.`
As a result of this database error, active flood avoidance polygons failed to load, causing route calculations to bypass flood detour zones.

#### 2. Root Cause Analysis (RCA)
Following the 1:N spatial deduplication schema migration, `FloodAvoidanceZone` no longer has a physical `report_id` database column; instead, `report_id` was implemented as a Python `@property` dynamically resolving to the primary report's ID (`self.primary_report.id`), while the foreign key moved to `flood_reports.zone_id`.
In `backend/app/services/valhalla_service.py` and `backend/app/services/ors_service.py`, `get_active_flood_polygons` attempted an SQL join:
`models.FloodAvoidanceZone.report_id == models.FloodReport.id`.
SQLAlchemy evaluated `models.FloodAvoidanceZone.report_id` as the Python `property` descriptor object rather than an ORM Column / InstrumentedAttribute, passing `<property object>` as parameter `%(id_1)s` to psycopg and throwing a `psycopg.ProgrammingError`.
Furthermore, performing an inner join against `flood_reports` would drop admin-curated avoidance zones with no direct report and duplicate multi-report zones.

#### 3. Solution & Architectural Strategy
Refactored `get_active_flood_polygons` in both `valhalla_service.py` and `ors_service.py` to query `FloodAvoidanceZone` and its PostGIS GeoJSON geometry directly without an inner join.
Zone severities are evaluated using the model's authoritative `.severity` property, which correctly respects administrator severity overrides, prioritizes the highest severity across merged reports, and falls back to default values for standalone curated zones.

#### 4. Files Modified / What Changed
- `backend/app/services/valhalla_service.py`: Replaced the invalid SQL join with a direct `FloodAvoidanceZone` geometry query and `.severity` property classification.
- `backend/app/services/ors_service.py`: Synchronized `get_active_flood_polygons` to query `FloodAvoidanceZone` directly and use `.severity`.
- `docs/others/bug-log.md`: Documented root cause analysis and resolution for BUG-023.

---

### [BUG-022] Registration Success Was Shown Twice on Login
- **Status**: Resolved
- **Severity**: Low
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Frontend / Authentication
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After a successful registration, the Login page showed both the global **Account Created** toast and an identical green success banner above the credentials fields.

#### 2. Root Cause Analysis (RCA)
`RegisterForm` displays the toast before redirecting to `/login?registered=true`; `LoginForm` also rendered a static banner from the same query parameter.

#### 3. Solution & Architectural Strategy
The static Login banner was removed. The redirect keeps the `registered=true` compatibility parameter, while the single global toast remains the registration confirmation.

#### 4. Files Modified / What Changed
- `frontend/src/features/auth/LoginForm.tsx`: Removes only the duplicate post-registration banner.

### [BUG-021] Edit Zone Reopened Without an Actual Edit and Could Not Change Geometry
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Frontend / Backend / Admin Map / IndexedDB Drafts / PostGIS
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Opening an active zone wrote a local copy of its unchanged server values. On a later sign-in, that copy opened the amber Edit Zone workspace and displayed **Edit Restored** despite no work having been started. Edit Zone also exposed no Spatial Geometry section, preventing an administrator from correcting an active road centreline or saved area boundary.

#### 2. Root Cause Analysis (RCA)
The edit-draft lifecycle treated every saved IndexedDB record as meaningful and had no comparison to the fetched server version. The secured update request accepted only metadata overrides, even though Create Zone already supported routed lines and Terra Draw area geometry.

#### 3. Solution & Architectural Strategy
Edit drafts now use a versioned snapshot of the exact fetched baseline, then compare normalized editable values and selected media against that snapshot. This prevents the previous polygon-versus-source-line mismatch from classifying an untouched legacy record as an edit; incompatible v1 records are removed silently. An inactive Create Zone workspace is also barred from reading or saving shared MapContext anchors while Edit Zone is active, preventing it from creating a false Create draft. Only a genuine change resumes the edit workspace and produces the restore toast. Edit Zone now shares Create Zone's Line, Polygon, Freehand, Rectangle, and Circle controls. Road replacements preserve a source centreline and regenerate the existing 25-metre avoidance polygon; area replacements persist their exact edited polygon and remove obsolete road source geometry. Existing areas reopen as editable polygons because the database intentionally stores the final polygon, not a drawing-tool label.

**Follow-up data mapping repair:** Edit Zone now uses its effective zone response values—administrator override when present, otherwise the linked public report’s severity, depth, survey, and description. Original report media is returned separately as read-only evidence, so it remains preserved and cannot be confused with newly uploaded zone media.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/components/zones/zoneEditDraftStorage.ts`: Adds normalized edit-baseline comparison helpers.
- `frontend/src/features/admin/LiveMapPage.tsx`: Validates an edit draft against the freshly fetched zone before opening Pane 2.
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx` and `hooks/useTerraDraw.ts`: Adds editable geometry controls and Terra Draw vertex selection to Edit Zone.
- `frontend/src/features/admin/adminApi.ts`, `backend/app/schemas/report.py`, and `backend/app/api/v1/endpoints/admin.py`: Accept and securely persist supported edit geometry without a migration.
- `backend/tests/test_zone_edit_geometry_schema.py`: Covers line and polygon update payload validation.

### [BUG-020] Landing Flood Analytics Action Opened a Separate Page Instead of the Map Panel
- **Status**: Resolved
- **Severity**: Low
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Landing Page / Map Analytics
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Selecting **View Flood Analytics** from the landing page opened `/analytics` rather than the commuter map with Flood Insights visible.

#### 2. Root Cause Analysis (RCA)
The landing action used the standalone analytics route, while the map's URL-driven panel contract handled only the `saveplace` panel value.

#### 3. Solution & Architectural Strategy
The action now navigates to `/map?panel=analytics`. `MapContext` recognizes that panel value and opens the existing Flood Insights panel through its standard state setter, preserving map-panel layout, stacking, and responsive behavior.

#### 4. Files Modified / What Changed
- `frontend/src/features/landing/LandingView.tsx`: Routes the action to the map with the analytics panel signal.
- `frontend/src/features/map/MapContext.tsx`: Opens Flood Insights for `panel=analytics`.
- `docs/others/system-documentation.md`, `docs/task_plan.md`, `docs/progress.md`: Records the corrected landing-to-map flow.

---

### [BUG-019] Primary Map Tabs Must Fly Only to Currently Selected Items
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Admin Map / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After an administrator selected a Pending Report or Active Zone and then toggled its card or map feature off, the map still flew back to that item after returning to its primary tab.

#### 2. Root Cause Analysis (RCA)
The first repair added separate last-target IDs. That made deselected items continue to qualify for tab-switch navigation even though they were no longer selected.

#### 3. Solution & Architectural Strategy
Pending and Active selections remain independent, but tab-switch navigation now reads only `selectedReportId` or `selectedZoneId`. A selected item flies into view when its tab is reopened; toggling that same card or map feature off sets its selection to `null`, so the next tab switch leaves the map unchanged.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Restores a tab's currently selected item on return and prevents deselected items from triggering map movement.
- `docs/others/system-documentation.md`, `docs/task_plan.md`, `docs/progress.md`: Records the independent per-tab fly-to memory.

---

### [BUG-018] Secondary Workspace Tabs Used a Fixed Order and Did Not Close
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Admin Map / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On `/admin/map`, the secondary drawer handles always followed a hard-coded Create → Edit → Merge sequence. A Merge or Edit workspace could remain as a collapsed handle after its Close action, so the visible stack did not reflect opened workspaces or the most recently opened one.

#### 2. Root Cause Analysis (RCA)
Each drawer render path positioned its handles with fixed offsets. Close handlers only hid a drawer in some paths, retaining the Merge report or Edit zone session that caused a stale placeholder to remain. Inactive workspace components were also unmounted, losing in-progress view state when switching tabs.

#### 3. Solution & Architectural Strategy
`LiveMapPage` now maintains a shared most-recent-first Merge/Edit workspace order. Create Zone stays permanently first; only sessions the administrator opened are rendered, and reopening Merge or Edit moves it directly below Create Zone. Switching keeps the workspace component mounted so its in-progress state and scroll position remain available. Explicit Close clears the matching session and its ordering entry. The Edit drawer has the same visible Close control on desktop and mobile; its existing discard confirmation continues to protect unsaved edits.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Adds recency-based workspace ordering, preserves inactive workspace mounts, and clears Merge/Edit sessions on close.
- `frontend/src/features/admin/components/merge/MergeWorkspacePanel.tsx`: Keeps an inactive opened Merge workspace mounted until it is explicitly closed.
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx`: Keeps inactive zone workspaces mounted and exposes the Edit Close control at every viewport size.
- `docs/others/system-documentation.md`, `docs/task_plan.md`, `docs/progress.md`: Records the corrected workspace-tab behavior.

---

### [BUG-017] Flood Report Saved Accidental UI-Only Drafts
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Flood Report Panel / IndexedDB Drafts
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
An accidental severity selection could be saved and restored as a Flood Report draft. The panel’s `Clear locations` action also left survey answers, media, sharing state, preview geometry, queued reports, and other report values behind.

#### 2. Root Cause Analysis (RCA)
Draft eligibility accepted any populated field, while the clear control only reset location inputs. UI-only values and incomplete interactions therefore looked like recoverable report work.

#### 3. Solution & Architectural Strategy
Draft eligibility now requires at least one selected road endpoint plus substantive report content (severity, survey answer, description, or media); queued reports remain recoverable. Two-way coverage, sharing, wizard state, survey visibility, and unselected location text cannot create a draft. Severity tiles now toggle off. **Clear** presents a compact, no-wrap choice row: neutral **Clear all** followed by the rightmost red **Clear this page**, which preserves work on the other report page.

#### 4. Files Modified / What Changed
- `frontend/src/features/hazards/floodReportDraftStorage.ts`: Separates meaningful draft eligibility from any local panel state.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Adds toggleable severity and scoped/full Clear handlers.
- `frontend/src/shared/ui/feedback/ConfirmDialog.tsx`: Supports the compact optional third action used by the Flood Report Clear dialog.
- `docs/others/bug-log.md`, `docs/task_plan.md`, `docs/progress.md`, `docs/others/system-documentation.md`: Records the corrected Flood Report draft contract.

---

### [BUG-016] Empty Flood Report Draft Triggered a False Restore Message
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Flood Report Panel / IndexedDB Drafts
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After sign-in, Flood Report could display “Draft Restored” even though the report panel contained no locations, severity, text, media, or queued report.

#### 2. Root Cause Analysis (RCA)
Flood Report persisted every hydrated form state, including an entirely empty active form. On startup it treated the presence of any account-private IndexedDB record as a successful draft restore and showed the toast without checking whether it contained report work.

#### 3. Solution & Architectural Strategy
A shared meaningful-draft check now gates both persistence and restoration. Empty records are deleted silently, never produce a restore message, and are not re-saved. The follow-up eligibility refinement in BUG-017 requires a selected road endpoint plus substantive report content for an active form, while queued reports remain recoverable.

#### 4. Files Modified / What Changed
- `frontend/src/features/hazards/floodReportDraftStorage.ts`: Adds the shared meaningful Flood Report draft classifier.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Removes empty persisted records before restore and deletes rather than saves an empty active form.

---

### [BUG-015] Feed Create Post Draft Lost Media Attachments and Location on Refresh
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Community Feed / Post Composer
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When composing a community post in `CreatePostModal` on `/feed`, attaching media (images or videos) and selecting a location tag/coordinates were held purely in volatile React state. Refreshing or reloading the page discarded the attached files and selected location. Furthermore, previously restored files were prematurely cleared from IndexedDB upon initial restore.

#### 2. Root Cause Analysis (RCA)
1. Media files in `selectedFiles` and location coordinates were only saved to storage on explicit button navigation actions ("Choose on Map" or clicking 'X' and choosing "Save Draft"), rather than continuously synchronizing state changes.
2. `CreatePostModal` called `del('lanes_draft_files')` immediately when loading files into React state on mount, erasing the persistent IndexedDB record. Subsequent browser refreshes therefore found no stored files.
3. `FeedPage` initialized `isCreateModalOpen` to `false` without checking whether a draft session was active before the page reload.

#### 3. Solution & Architectural Strategy
1. **Continuous Draft Synchronization**: Added reactive synchronization effects that automatically persist text content, location tags, and coordinates to `localStorage` (with `sessionStorage` fallback) and attached `File[]` objects to IndexedDB via `idb-keyval`.
2. **Preserve Draft Until Terminal Action**: Removed premature deletion on mount. Draft storage is now only cleared when the user successfully publishes a post (`createMutation.onSuccess`) or explicitly clicks **"Discard Post"**.
3. **Session Restoration on Refresh**: `FeedPage` checks for an active composing session on mount and restores the open modal state alongside the draft content, location tag/coordinates, and all attached media files (re-generating object preview URLs).

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/CreatePostModal.tsx`: Implements continuous auto-save for content, location, and IndexedDB media files, eliminates premature IndexedDB deletion, merges `initialFiles` on mount, and ensures clean draft disposal on post or discard.
- `frontend/src/features/feed/FeedPage.tsx`: Restores composer modal state if user reloads while composing, and syncs modal closure to draft storage.
- `docs/others/bug-log.md`: Documents BUG-015 root causes and resolution.

---

### [BUG-014] Edit Zone Replaced the Create Zone Workspace Bookmark
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Admin Map / Spatial Operations Workspace
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On `/admin/map`, selecting **Edit** from Active Zones passed the selected zone into the same secondary drawer state used by Create Zone. The lone blue Create Zone bookmark therefore changed into an amber Edit Zone bookmark, leaving the unfinished Create workspace inaccessible and making the control appear permanently renamed.

#### 2. Root Cause Analysis (RCA)
`LiveMapPage.tsx` represented both actions with `isCreateZoneDrawerOpen` and a mutable `editingZone`. The drawer title, color, form mode, and bookmark were all derived from that one state pair. This conflated two independent admin sessions even though `OfficialZoneDrawer` already supports separate create and per-zone edit draft persistence.

#### 3. Solution & Architectural Strategy
Create and Edit now have independent visibility sessions. Create keeps its blue bookmark and account-private draft; Edit keeps its selected zone and amber bookmark. Only one Pane 2 drawer is visible at once, while switching preserves the other workspace through the existing IndexedDB draft mechanism. Merge Review remains an independent third session. Desktop bookmarks now use non-overlapping stacked offsets: Create, Edit, then Merge. Mobile exposes Create from Active Zones and provides a workspace switch action in the shared drawer header.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Separates Create/Edit drawer state, preserves sessions while switching, and renders distinct blue, amber, and merge bookmarks.
- `frontend/src/features/admin/components/CreateOfficialZonePanel.tsx`: Forwards optional mobile workspace-switch controls to the shared drawer.
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx`: Adds the mobile-only workspace switch action without duplicating the form or changing APIs.
- `frontend/src/features/admin/components/ActiveZonesPanel.tsx`: Exposes a mobile Create Zone entry point.

---

### [BUG-013] Mixed Road Topology Was Classified as One Whole Route
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Flood Report / Decision #16 Carriageway Detection
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
A report spanning Caruncho Avenue and Urbano Velasco Avenue showed only one orange line, or previously could produce a misleading counterpart, because its Start/End range crossed one-way and two-way map sections. The valid opposite carriageway exists only for the appropriate Urbano Velasco run.

#### 2. Root Cause Analysis (RCA)
The service evaluated the entire Valhalla route as one unit and chose its dominant traversability. For the reproduced coordinates, Valhalla edges identify Caruncho as one-way, Urbano Velasco as one-way, then Urbano Velasco as two-way. One whole-route counterpart search cannot represent that topology safely.

#### 3. Solution & Architectural Strategy
The trace request now includes Valhalla edge `begin_shape_index` and `end_shape_index`. The service splits the snapped route whenever road identity or traversability changes, classifies each run independently, and searches for an opposite carriageway only for eligible runs. Before validation, a map-matched candidate is reduced to its longest contiguous component that is actually parallel and laterally separated from the selected run. A short terminal transition is restored only when the graph-mapped geometry reaches the matching endpoint of that original road run, which represents a genuine Y merge; unrelated cross-street or detached connectors remain removed. For split routes only, the valid component can cover 50%+ of the run with a 3.5m lateral tolerance for six-decimal polyline rounding. The final preview keeps the original full line and adds only the verified counterpart section.

#### 4. Files Modified / What Changed
- `backend/app/services/carriageway_service.py`: Requests edge shape indexes, applies per-run carriageway classification, and retains only endpoint-attached graph-mapped Y transitions from otherwise trimmed counterparts.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Renders the original and verified counterpart through independent MapLibre sources/layers so a short nearby line cannot be lost when the map style reloads.
- `backend/tests/test_carriageway_service.py`: Covers road-identity/traversability splits, connector removal, and the mixed-run partial-counterpart threshold.
- `docs/decisions.md`: Updates Decision #16 to prohibit dominant whole-route topology classification and scopes the partial-run tolerance.

---

### [BUG-012] Feed View-on-Map Pulse Was Offset from Road Coverage
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Community Feed / Map Focus Indicator
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Clicking a Flood Report location or **View on Map** in the Community Feed opened `/map`, but the temporary red pulsing circle could sit above or beside the reported road. Curved segments and two-carriageway reports made the misalignment especially visible.

#### 2. Root Cause Analysis (RCA)
`PostItem.tsx` reduced every road geometry to the midpoint of its bounding box. That mathematical point is often off a curved line and does not correctly represent paired carriageways. The `fly-to-location` MapLibre marker also used the default bottom anchor, which placed the visual pulse above its supplied geographic coordinate.

#### 3. Solution & Architectural Strategy
The shared map geometry utility now finds a LineString's midpoint by travelled road distance. For a `MultiLineString`, it calculates each carriageway's travelled-distance midpoint and uses their length-weighted average, producing the expected center between paired directions. The Feed shares that utility for both map entry points, and the pulse marker uses a center anchor so the animation's visual center exactly matches the fly-to coordinate.

#### 4. Files Modified / What Changed
- `frontend/src/features/map/mapGeoUtils.ts`: Added road-length and dual-carriageway coverage midpoint calculation.
- `frontend/src/features/feed/PostItem.tsx`: Replaced its duplicate bounding-box midpoint logic with the shared utility.
- `frontend/src/features/feed/feedApi.ts`: Recognizes `MultiLineString` report geometry from the API.
- `frontend/src/features/map/MapCanvas.tsx`: Center-anchors `fly-to-location` pulse markers.

---

### [BUG-011] Public Road Preview Saved Raw Sidewalk Connectors
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Public Flood Report / Routing / Pending Reports
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
An orange public road preview could look acceptable beneath its Start/End pins, but the same pending report later appeared to extend toward a sidewalk or nearby building in the admin map. The severity aura exposed geometry that was not actually on the road.

#### 2. Root Cause Analysis (RCA)
The authoritative route service first found a valid Valhalla-snapped road line, then prepended and appended the user's raw clicked coordinates to make the dashed preview visibly meet the pins. For ordinary reports, that combined line was stored directly. For bidirectional reports, the frontend submitted only the original line and persistence independently rebuilt coverage, allowing the public preview and stored geometry to drift.

#### 3. Solution & Architectural Strategy
Raw clicks are now input anchors only. The preview service returns only the snapped road line, and public markers move to its endpoints after verification. Flood Report submits the full validated dual coverage when available; the backend still rebuilds every submitted road segment before storage, using the first validated road line for authoritative classification. Pending Reports continues to render stored geometry directly, which is now road-only for newly created reports.

#### 4. Files Modified / What Changed
- `backend/app/services/carriageway_service.py`: Removed raw-anchor connector vertices from authoritative preview output.
- `backend/app/services/report_service.py`: Rebuilds both single and bidirectional submitted road geometry before persistence.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Submits validated `MultiLineString` coverage when an opposite carriageway was confirmed.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Places visible public Start/End markers on the validated road endpoints.
- `backend/tests/test_carriageway_service.py`: Replaced connector expectations with road-only preview and persistence regression coverage.

---

### [BUG-010] Pending Report Aura Extends Beyond Validated Road Endpoints
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Admin Map / Pending Reports
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
At street level, pending public flood reports could appear to spill from the correctly aligned road into adjacent buildings or lots. The problem was most visible at either end of a report segment as a large transparent severity-colored bulb, giving the impression that the report geometry was not aligned with the map.

#### 2. Root Cause Analysis (RCA)
The pending layer correctly rendered the persisted validated report geometry without recalculating a route. However, its 24px aura (32px when selected) used MapLibre's `round` line cap. A round cap extends past each geometry endpoint by half the line width, so the visual aura exceeded the saved road segment even though its coordinates were correct.

The initial layout correction applied only when the custom MapLibre layer was first created. Because the global map instance survives panel navigation and development Fast Refresh, an already-created layer could retain its old `round` cap while its GeoJSON source refreshed normally. This made the fixed code appear ineffective for current reports.

#### 3. Solution & Architectural Strategy
The geometry-source repair in BUG-011 removes the actual off-road connector cause. Pending Reports intentionally use MapLibre `round` caps and rounded joins again, matching the rounded endpoint treatment of Active Zones and the public orange preview. The hook reapplies this layout to existing live layers after navigation or Fast Refresh. Approved-zone rendering remains unchanged, using its server-created transparent buffer with a dark road core.

#### 4. Files Modified / What Changed
- `frontend/src/features/map/hooks/usePendingReportsLayer.ts`: Restored intentional rounded endpoint caps and rounded joins for the pending road aura, and synchronizes that layout on existing live layers.

---

### [BUG-009] Admin Live Map Crashing on Login: Stale Edit Draft 404 & MapLibre getSource Timing
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Admin Live Map & Map Layer Hooks)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Upon logging into the administrator account and accessing `/admin/map` or `/admin/dashboard`, two distinct errors broke the map interface:
1. An error toast popped up saying *"Unable to resume your saved Edit Zone draft"*, with console output: `Failed to resume Edit Zone draft ApiError: Zone not found` triggered by `GET /api/v1/admin/zones/18 -> 404`.
2. A runtime exception was thrown: `Uncaught TypeError: Cannot read properties of undefined (reading 'getSource') at useMergePreviewLayer.useEffect (src/features/map/hooks/useMergePreviewLayer.ts:32:32)` during map initialization and MapTiler auto-recovery attempts.

#### 2. Root Cause Analysis (RCA)
1. **Stale Draft 404:** The admin client's IndexedDB draft storage retained an unfinished zone edit draft referencing zone ID `18`. Since Zone #18 had been deleted or reset in the database, the startup hook `findLatestZoneEditDraft` repeatedly attempted to fetch it and threw an unhandled 404 error toast on every single page load without ever discarding the invalid draft.
2. **MapLibre Style Readiness Timing:** During map startup or style recovery (e.g. MapTiler style timeout triggering `BaseMap` auto-recovery), MapLibre's internal `map.style` is temporarily `undefined`. `useMergePreviewLayer` executed `map.getSource(sourceId)` immediately at the top of its `useEffect` without verifying `map.getStyle()`, causing MapLibre's internal `this.style.getSource(id)` call to crash. In addition, the hook's unmount cleanup lacked defensive guards when tearing down layers on a destroyed map instance.

#### 3. Solution & Architectural Strategy
1. In `LiveMapPage.tsx`, updated the draft resuming effect to catch HTTP `404 Not Found` when requesting `getZone(draft.zoneId)`. On 404, it immediately calls `discardZoneEditDraft(createZoneDraftUserId, draft.zoneId)` to cleanly purge the obsolete draft from IndexedDB and silently ignores the missing zone without firing an alarmist toast.
2. In `useMergePreviewLayer.ts`, added `if (!map || !isLoaded || typeof map.getStyle !== "function" || !map.getStyle()) return;` before any MapLibre source or layer calls. Wrapped source retrieval and unmount cleanup in safe `try/catch` blocks.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Imported `discardZoneEditDraft` and purged stale drafts on 404 errors.
- `frontend/src/features/map/hooks/useMergePreviewLayer.ts`: Added `map.getStyle()` readiness guards and defensive cleanup handling.

---

### [BUG-008] User Reports Fetch 500 Error via Unexported get_flood_reports_by_user in CRUD Index
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Backend (Reports API & CRUD Module)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When a user (such as `roicambe`) submitted a flood report, the report was successfully inserted into PostgreSQL (`Report #1`). However, visiting the user's Profile or viewing submitted reports triggered an HTTP `500 Internal Server Error` on `GET /api/v1/reports/me`.

#### 2. Root Cause Analysis (RCA)
In `backend/app/api/v1/endpoints/reports.py`, the `read_my_reports` endpoint calls `crud.get_flood_reports_by_user(db=db, user_id=current_user.id)`. However, `backend/app/crud/__init__.py` did not import or expose `get_flood_reports_by_user` from `app.crud.report`. This resulted in an unhandled `AttributeError: module 'app.crud' has no attribute 'get_flood_reports_by_user'`, which the endpoint caught and converted into a `500 Internal Server Error: Database is offline`.

#### 3. Solution & Architectural Strategy
Updated `backend/app/crud/__init__.py` to import and expose `get_flood_reports_by_user`, along with other report and user management functions (`archive_flood_report`, `restore_flood_report`, `create_user_with_profile`, `update_user_role`), ensuring complete API module access.

#### 4. Files Modified / What Changed
- `backend/app/crud/__init__.py`: Added `get_flood_reports_by_user`, `archive_flood_report`, `restore_flood_report`, `create_user_with_profile`, and `update_user_role` to module exports.

---

### [BUG-007] Flood Preview Wait Has Weak Feedback and Report Controls Use Incorrect Defaults
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend / Map / Routing
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After the Decision #16 correctness repair, road verification could visibly pause while only a small loading text was shown. The Flood Report Start/End direction-swap button was absent, the first severity tile was selected automatically, and two-way coverage needed to be explicitly confirmed as opt-in.

#### 2. Root Cause Analysis (RCA)
The panel rendered `floodPreviewMessage` as ordinary status text for every preview state and did not use the existing shared loading overlay. `LocationInputGroup` retained swap support, but Flood Report no longer supplied its `canSwap` and `onSwap` properties. Local form initialization and reset paths hardcoded `visualOption` to `gutter`, with submission logic silently falling back to `low`. The backend also waited for its two independent directional route requests sequentially.

#### 3. Solution & Architectural Strategy
Flood Report now uses the shared accessible blocking overlay during verification on mobile and desktop, then shows the ordinary status explanation only after loading. The shared swap control exchanges coordinates and labels and triggers fresh validation. Bidirectional coverage remains false unless the user checks it. Severity begins empty, is required before advancing or saving, and has no implicit low-severity conversion. Directional route requests run concurrently while all validation rules remain unchanged.

#### 4. Files Modified / What Changed
- `frontend/src/shared/ui/feedback/LoadingOverlay.tsx`: Added reusable blocking behavior and accessible status semantics.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Integrated the loading screen, restored direction swapping, and enforced explicit two-way and severity choices.
- `backend/app/services/carriageway_service.py`: Executes independent forward/reverse Valhalla route checks concurrently.
- `backend/tests/test_carriageway_service.py`: Made directional-route regression mocking deterministic under concurrent execution.

---

### [BUG-006] Bidirectional Flood Preview Draws a Same-Side Parallel Line or Legal-Driving Loop
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend / Backend / Map / Routing
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
With “Affects both sides of the road (2-way)” enabled, narrow roads could display a second dashed orange line on the same side or a hooked loop through nearby streets instead of the real opposite carriageway. The Caruncho-area reproduction turned a short pair of anchors into an 834m legal-driving route.

A follow-up regression showed the corrected dashed route stopping visibly before its orange Start marker. The pin represented the raw selected anchor, while Valhalla returned a valid road snap several metres farther along the road.

After exact endpoint connectors were added, the apparent gap could still reappear only after loading completed even though the returned coordinate matched the marker.

A further UX regression briefly drew a raw straight orange connector between the selected pins during verification, then replaced it with the mapped road shape. This made the preview look broken before the final result was ready.

#### 2. Root Cause Analysis (RCA)
`MapContext.tsx` first requested an ordinary traffic-law-aware route and passed that complete result into Decision #16. When anchor direction conflicted with mapped traffic flow, Valhalla legally detoured around neighboring roads. The carriageway service then used raw edge counts, searched only the left side, and accepted name similarity without proving distinct OSM way identity, lateral separation, overlap, or comparable length. A snap back onto the original road could therefore be labeled `DIVIDED_CARRIAGEWAY`.

The hardened service correctly limited endpoint snaps to 35 metres, but returned the snapped polyline unchanged. Because markers intentionally remained at the user’s raw anchors, accepted snap distance appeared as a gap between the marker and dashed coverage.

The remaining post-loading symptom was a MapLibre rendering artifact: changing from the temporary two-point line to the longer verified polyline recalculated `line-dasharray` phase. The endpoint could fall inside the pattern’s transparent interval, visually hiding the final portion despite correct geometry.

`MapContext.tsx` explicitly placed that temporary two-point geometry in shared preview state as soon as both anchors existed. The loading overlay covered the panel but not the map, so users could see an unverified straight route before Valhalla completed.

#### 3. Solution & Architectural Strategy
The backend now owns road-preview generation from raw anchors, evaluates both directions, rejects excessive detours, and uses length-weighted topology classification. Divided-road searches probe both sides and require road identity/class, distinct way IDs, opposing direction, parallelism, comparable length, longitudinal overlap, safe separation, and no loop. Narrow two-way roads intentionally render one mapped centerline. Ambiguous or unavailable graph data returns one conservative line with an explanation.

For a route that already passes endpoint-snap and loop validation, the backend now selects the candidate with the best combined endpoint fidelity and retains its snapped road vertices while adding short connectors to the exact Start and End anchors. Preview and persisted operational geometry therefore agree and visually meet both pins.

The shared preview hook additionally renders solid orange terminal caps for first/last segments no longer than 40 metres. These caps sit above the dashed layer and below the existing markers, while the road body remains dashed on both mobile and desktop maps.

Shared preview state is now cleared while an authoritative request is in flight. The Start and End pins remain visible with the loading overlay, and the orange route is rendered only after the service returns its final validated or conservative fallback geometry. API failures leave the map clear and keep the existing panel error feedback.

The earlier raw-anchor connector and solid terminal-cap workaround is superseded by BUG-011: raw clicks are no longer geometry vertices, and pins move to the verified road endpoints instead.

#### 4. Files Modified / What Changed
- `backend/app/services/carriageway_service.py`: Added authoritative segment selection, conservative classification, two-sided probing, strict candidate validation, endpoint-fidelity ranking, and exact pin connectors.
- `backend/app/services/report_service.py`: Repeats raw-anchor validation before persistence so client geometry cannot create an unverified `MultiLineString`.
- `backend/app/api/v1/endpoints/routes.py`: Expanded the backward-compatible preview contract for raw anchors, coverage geometry, validation status, and explanation.
- `frontend/src/features/map/MapContext.tsx`: Removed the general-route preview chain and centralized shared preview status and geometry.
- `frontend/src/features/map/MapContext.tsx`: Removed the temporary raw straight-line fallback during loading so shared public/admin maps never animate from an unverified connector to the final road shape.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Initially added terminal-cap rendering; BUG-011 removed that workaround in favor of a single road-only dashed geometry and snapped visible pins.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Added responsive inline road-verification feedback.
- `frontend/src/features/admin/components/zones/`: Reused the same feedback and persisted validated dual-carriageway geometry for official zones.
- `backend/tests/test_carriageway_service.py`: Added focused regression coverage for narrow, divided, one-way, ambiguous, same-side, unrelated-road, loop, outage, concurrency, and exact pin endpoint cases.

---

### [BUG-005] Feed Post Creation 500 Error / Socket Hangup While Post Is Persisted in Database
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Backend (Feed API & Post Creation Serialization)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When submitting a community post containing media, video, and location, the UI reported an error (or socket hang up / 500 Internal Server Error). However, refreshing the feed revealed that the post was actually saved to the database and displayed properly.

#### 2. Root Cause Analysis (RCA)
- In `backend/app/api/v1/endpoints/posts.py`, the `create_post` endpoint committed the post and uploaded media to Cloudinary successfully.
- However, when returning the response, it manually spread `**post.__dict__` into a dictionary without the computed relational fields (`upvotes`, `downvotes`, `comment_count`, `report`, or clean Pydantic schema serialization). SQLAlchemy ORM internal state attributes (`_sa_instance_state`) inside `post.__dict__` interfered with FastAPI's `response_model=CommunityPostResponse` serialization, triggering a `ResponseValidationError` (HTTP 500) during output marshaling after the database transaction had already committed.

#### 3. Solution & Architectural Strategy
- Updated `create_post` in `backend/app/api/v1/endpoints/posts.py` to immediately retrieve the created post via `crud_feed.get_feed_post(db, post.id, user_id=current_user.id)` (or return an explicit, clean dictionary matching `CommunityPostResponse`), guaranteeing full consistency with the rest of the feed endpoints and avoiding raw ORM dict leaks.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/posts.py`: Used `crud_feed.get_feed_post` to format and return the newly created post with sanitized attributes.

---

### [BUG-004] Community Feed "View on Map" Pin Click Missing Coordinates Fly-To and Pulsing Ring
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Map & Feed Integration)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When viewing a post on `/feed` (or post detail or user profile) with an attached location, clicking the location button (`View on Map`) navigated to `/map`, but the map did not fly to the target coordinates or display the temporary red pulsing indicator ring.

#### 2. Root Cause Analysis (RCA)
- The click handlers originally invoked `router.push('/map?lat=${lat}&lng=${lng}&zoom=16')`.
- `MapCanvas` is a persistent root-level component across route changes. When transitioning from `/feed` to `/map`, Next.js App Router client transitions and `MapCanvas`'s `searchParams` hook did not reliably trigger the `useEffect([searchParams, isLoaded])` hook if the parameters were swallowed or unobserved during client route switching.
- However, `MapCanvas` already possessed a dedicated, robust `fly-to-location` window event listener (with built-in map camera animation and temporary animated pulsing DOM marker).

#### 3. Solution & Architectural Strategy
- Updated all "View on Map" click handlers to transition cleanly to `/map` and dispatch the `fly-to-location` custom event with coordinates and zoom level after a slight frame delay (150ms) to ensure layout readiness.
- Removed reliance on URL search parameters for ephemeral map focusing.

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/FeedPage.tsx`: Dispatches `fly-to-location` event with `{ latitude: lat, longitude: lng, zoom: 16 }` upon location badge click.
- `frontend/src/features/feed/PostDetailPage.tsx`: Updated `onViewMap` handler to dispatch `fly-to-location`.
- `frontend/src/features/profile/ProfileView.tsx`: Updated `handleViewMap` handler to dispatch `fly-to-location`.

---

### [BUG-003] Location Re-Selection in Create Post Modal Failing After Removal
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Create Post Modal / Map Picker)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In the `/feed` Create Post modal, attaching a location via "Choose on Map" worked on the first attempt. However, if the user removed the location and attempted to select a location a second, third, or fourth time, the location would no longer attach or populate until the entire modal was closed and reopened.

#### 2. Root Cause Analysis (RCA)
- State synchronization in the modal's location picker was retaining stale closure flags or unreset picking mode state when removing the active location tag.
- The map interaction listener was either still detached or held onto stale coordinates/unmounted event references without resetting picker readiness.

#### 3. Solution & Architectural Strategy
- Reset both coordinates state, location name state, and picker activation flags upon removing the location badge.
- Re-initialized the location selector hook lifecycle so subsequent "Choose on Map" triggers always mount fresh event listeners.

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/CreatePostModal.tsx`: Reset location picker state and re-armed map pick handlers upon location removal.

---

### [BUG-002] Logout UI Freezing / Requiring Manual Page Refresh
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend / Auth State
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When clicking "Log Out", the application UI appeared frozen or stuck on the current view. Only upon manually refreshing the browser did the session reflect that the user had indeed been logged out.

#### 2. Root Cause Analysis (RCA)
- The logout handler cleared tokens in `localStorage` but did not actively purge or reset React Query cache (`queryClient.clear()` / `queryClient.resetQueries()`) or notify dependent UI contexts.
- Components continued reading cached user data from memory, creating an apparent freeze until full browser reload reinitialized memory state.

#### 3. Solution & Architectural Strategy
- Updated authentication store / hook logout procedure to immediately invalidate and clear the QueryClient cache, reset user state to `null`, and trigger proper client routing back to `/login` or `/` without requiring manual page reloads.

#### 4. Files Modified / What Changed
- `frontend/src/features/auth/useAuth.ts`: Added reactive cache clearance and immediate navigation on logout.

---

### [BUG-001] Drafted Media Lost After Login Redirection in Create Post Modal
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Feed / Create Post & Auth Recovery)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Unauthenticated users composing a post in `/feed` who attached images or videos and wrote text were prompted to log in. Upon authenticating and returning to `/feed`, only the text description was restored from draft; all uploaded images and video files were discarded.

#### 2. Root Cause Analysis (RCA)
- Drafts were stored in `localStorage`, which only supports serializable strings.
- Uploaded media objects were `File` or `Blob` instances which cannot be serialized cleanly into JSON strings; attempt to serialize them resulted in empty objects `{}` or dropped keys.

#### 3. Solution & Architectural Strategy
- Integrated browser-persistent storage (IndexedDB or cached base64/blob storage) for drafted post media files before auth redirect, restoring both description and files when the modal re-opens post-login.

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/CreatePostModal.tsx`: Implemented persistent draft recovery for media files.
