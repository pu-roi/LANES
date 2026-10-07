# LANES — Progress Tracker

> Tracking completed milestones, delivered features, and past sprints.
> **Last Updated:** October 08, 2026, 12:01 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

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
- [x] Execute one 60-second free synthetic retry. The provider responded, but invalid evidence offsets were rejected (`audit_evidence_offset_mismatch`). No database/public writes or deployment. This is a diagnosed reliability gap, not successful live acceptance. [Evidence](evaluations/phase-36-news-runtime-packaging-20261007.md#october-7-live-timeout-follow-up). [@roicambe](https://github.com/roicambe) (Roi Cambe)

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
