# Phase 36: Needs Review queue and placement inspection

> **Last Updated:** October 04, 2026, 3:24 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local inspection implementation; news decisions and automatic publication remain unfinished.

## October 4 automatic plotting readiness audit

**Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe). The developer requested read-only investigation, then authorized documentation synchronization before further implementation. This section records current source behavior and the checks run in that investigation; it does not overwrite earlier delivery or release evidence.

### Pipeline and map findings

- `process_saved_news` calls captured-body rules-only extraction. Shared extraction attaches OSM `road_placement` and exact NOAH/section-matched Pasig `placement_preview`, then saves the immutable result. It does not call `NewsAutoIngestionService` or independent auditing. The separate activation prototype requires checked evidence and `verified_segment` geometry; its existence is not a connected public lifecycle.
- F5 source/placement inspection exists on desktop/mobile. News candidates use blue dashed centerlines and start without a selected candidate; selection is inspection only. User-report Needs Review uses translucent auras. Active road zones use a solid source centerline plus the persisted translucent operational polygon. That polygon participates in routing; pending pixel-width auras do not establish a real flooded corridor. Complete fields alone cannot authorize a zone.
- Reviewed citizen-report growth supports cross-barangay/connected-road extensions, evidence-only corroboration and separate sections within an event. It preserves prior supported coverage/core and original evidence. This does not establish automatic multi-barangay news placement: the current OSM provider has city polygons but rejects named barangays with `missing_valid_barangay_boundary`.
- Current source admission and analytical OSM/NOAH assets cover Metro Manila. The original user-confirmed product goal is the entire Philippines. Matching Pasig DRRMO rows apply only in Pasig; this checkpoint changes no geographic filter or coverage asset.

### Local C. Raymundo probe

The constructed claim names **C. Raymundo Avenue, Pasig**, with a short synthetic flood sentence and no source article or resolved observation time. Current local providers return 25 OSM sections. Exact NOAH overlap plus matching DRRMO context yields `predicted_candidate`, reason `unique_ranked_prediction_not_verified_flood_extent`, candidate `osm:123442003-4003002153`, retaining all 25 alternatives. Twelve candidate/history associations are returned; those are not distinct flood-event counts. Adding `canonical_barangay=Rosario` returns `unresolved`, reason `missing_valid_barangay_boundary`.

The probe explicitly returns `read_only=true` and `may_affect_routing=false`. Earlier NOAH-only audits found tied sections; their inputs did not include the same current section-matched historical evidence. This probe neither validates a real article nor identifies current flood extent/depth/width or establishes operational activation. The bundled historical CSV contains 726 rows for 2020–2025.

### Focused verification

Commands ran from `backend/` during the preceding investigation:

```powershell
./venv/Scripts/python.exe -m pytest tests/test_news_placement_preview.py tests/test_news_road_placement.py tests/test_news_auto_ingestion.py -q -k 'not preview_endpoint_auth_identity_and_no_database_writes'
./venv/Scripts/python.exe -m pytest tests/test_spatial_review_grouping.py tests/test_flood_zone_growth.py::test_report_extent_proposal_retains_branches_and_extensions -q
```

The selections pass **55 + 15 = 70 checks**. The first explicitly deselects one database-backed preview endpoint case; grouping fixtures use isolated SQLite where needed, and the selected extent case does not invoke the native growth transaction fixture. Existing multipart and SQLite datetime deprecation warnings remain. No native PostGIS growth transaction, actual auditor, browser visual check or live production release was reverified. Temporary fixtures/caches are not publication state. No live report/event/zone writes or application/schema/dependency changes occurred.

### Eight-record audit and next task

| Authoritative record | Outcome |
| --- | --- |
| Task plan | Correct stale F4b/v6 summary; record local F5/v10 state and unchecked backend publication-readiness work. |
| Progress tracker | Prepend this investigation/documentation checkpoint; retain older milestone results and acceptance limits. |
| Feature reference | Update existing news feature descriptions; do not create a new flagship feature. |
| System documentation | Reconcile shared extraction, F5 inspection and pending public lifecycle; retain current two-layer geometry roles. |
| Tech stack | Existing local v10/dependency/asset notes remain accurate; no library or manifest change. |
| Database design plan | Existing JSONB preview compatibility and multi-location event/zone storage notes remain accurate; no new schema or migration. |
| Bug log | Existing BUG-096 covers reviewed cross-boundary growth; automatic placement/lifecycle gaps stay open in the plans without duplicating that issue. |
| Architectural decisions | Existing automatic/exception boundaries remain unchanged; no architectural pivot warrants a new entry. |

This investigation identified backend readiness as the next task: assess durable claim/publication/zone identity and reuse of existing event/report storage; specify affected geometry and authoritative boundaries; identify independent-auditor and matching analytical-asset release requirements; propose concrete transactions and APIs before implementation. The subsequent [publication readiness assessment](phase-36-publication-readiness-audit.md) completes that investigation with a five-table proposal; schema/expiry approval and implementation remain pending. F6 news actions and F7 commuter visibility then share those contracts and existing renderers. The [active checklist](../task_plan.md#phase-36-automatic-news-publication-readiness--assessment-complete-approval-pending) retains implementation tasks as unchecked.

Documentation validation checks relative file targets and new section anchors, current-status wording, single timestamp blocks and `git diff --check`. SHA-256 comparison confirms existing frontend edits, package manifests and the four audited unchanged core records remain byte-identical to the pre-update checkpoint.

Documentation synchronization preserves existing uncommitted Primary Panel/filter/test edits. This audit does not claim commit/push, migration execution, deployment, nationwide operation or new desktop/mobile acceptance.

## Checkpoint and scope

The developer requested the existing work be pushed before implementation. Checkpoint `d435f02` was committed and successfully pushed to `origin/roi-branch`. It includes the earlier article corrections, read-only placement backend and the shared checkout's feed/location work. The current Needs Review changes are subsequent local work, not part of that pushed checkpoint.

The accepted F5 interface replaces Pending Reports with **Needs Review** and retains **Active Zones**, with **All / User Reports / News Claims** filters. Current news exceptions are inspected within Spatial Operations. Fully eligible news claims retain the intended automatic publication path; staff approval is not required for every news claim. This inspection delivery does not implement F6 decisions or F7 automatic alerts/zones.

## Backend behavior

- Admin-protected `GET /api/v1/admin/review/items` combines eligible identities in SQL, then groups related pending user reports in the backend before card sorting/pagination. It accepts `source=all|user_reports|news_claims`, `page`, and `page_size` (default 20, maximum 100). `total`/`pages` count cards; `item_total` and source badges count individual reports/claims. Keys are `user_report:<id>` and `news_claim:<run_id>:<claim_index>`; claim index zero is valid.
- `GET /api/v1/admin/review/items/{key}` returns preserved source-specific evidence with `is_current_review`. Older records remain inspectable but are labeled outside the current queue. News actions remain unavailable. Invalid identifiers return 422, missing evidence 404, and SQL storage failures 503 rather than a false empty queue.
- Pending, non-archived user reports retain their existing moderation APIs. News reads use each article's newest recorded processing attempt; a newer failed/pending attempt cannot expose an older success as current. Only successful readable artifacts with recorded `flagged_review` decisions qualify. Approved, suppressed, forecast, negated, caption/context-only and historical claims are excluded.
- The news queue reuses the existing 12-hour evidence window. Old publication or explicit old observation clocks cannot be revived by reprocessing. Missing observation times remain explicit exceptions on recent articles. Missing publication clocks use only recent first-discovery time to bound queue inclusion; this never establishes flood observation time or publication eligibility. Future publication clocks remain outside the current queue.
- Queue reads perform no external fetch, auditor call or publication write. Current placement is fetched separately through the existing limited, immutable-evidence preview API when a claim is opened. No SQLAlchemy models, Alembic revisions or dependencies changed.

## Frontend behavior

`NeedsReviewPanel` keeps the filtered queue mounted while inspecting an item, restoring scroll and focus on Back to queue. User report inspection retains Info, Approve, Reject and Review Merge Suggestions; approval/rejection failures are surfaced, and successful moderation refreshes the combined queue. Existing report handoff parameters remain compatible.

`NewsReviewEvidence` shows server-provided facts, source sentence, uncertainties, original full text, placement alternatives, exact NOAH scenario overlaps, Pasig section-matched records and source revisions. Candidate selection is a visual inspection only; no initial candidate is selected even when the backend ranking proposes one. Unresolved geometry produces text-only evidence, and unavailable sources/truncated alternatives are explicit. Placement reads have no polling, automatic retries or focus refetches.

`useNewsPlacementLayer` owns an isolated GeoJSON source and dashed blue centerlines, with darker/thicker highlighting of the inspected candidate. It creates no buffer/polygon/point or routing geometry. It rebuilds after style changes and removes its source/layer when inspection closes, a drawing workspace resumes, another primary tab opens, or navigation leaves Spatial Operations. Active zone severity centerlines/polygons are unchanged. Current Create/Merge/Edit sessions remain mounted when news inspection collapses them.

Desktop keeps evidence beside the persistent map. Mobile has Map/Evidence switching, Back to queue, safe-area/bottom-navigation clearance and 44px inspection controls. The workspace breakpoint is aligned to 768px and coarse-pointer landscape avoids the previous desktop-class override of mobile switching.

## Verification

- 17 new backend cases pass, covering staff protection, source identities, mixed pagination/counts, latest-run failures, historical/suppressed exclusion, current/missing clocks, preserved detail, storage failures, native PostgreSQL SQL compilation and no writes.
- The final combined review/news-results/placement/processing/routing selection passes all 82 checks in one run. Fixtures use isolated SQLite evidence and a minimal non-spatial report table. Native PostgreSQL query compilation is checked; actual PostGIS execution and a real authenticated mixed-source API check remain unverified because the local integration services are unavailable.
- Frontend TypeScript and lint for the new review components, modified pending-report panel, news API types and browser tests pass. LiveMapPage retains the checkpoint's 15 lint errors/14 warnings; no new lint errors were added.
- The final combined Playwright run for `spatial-review.spec.ts`, `news-intelligence.spec.ts` and `news-articles.spec.ts` passes 37 cases, with five expected skips (two live captured-article checks require integration credentials; three cases apply to only one viewport project). Coverage includes both sources, independent candidate selection, source text, user-report controls, Create draft preservation, narrow/landscape switching, unavailable/unresolved/rate-limited/error states and existing News Intelligence behavior. Rendered canvas checks verify suggestions survive style reload and disappear on Back to queue.
- An existing Source Article assertion was scoped to its Reported location region because the same missing-fact text now appears in two fields. An earlier mobile unavailable-source run timed out before its queue row appeared; two focused repeats and the final combined run pass. No product cause was established for that earlier timeout.
- Browser verification uses mocked staff/API responses and a minimal mocked basemap style. It does not establish real news publication, production source availability or deployed acceptance. Screenshots and traces are under ignored `frontend/test-results/`.

Reproduction commands, from the corresponding backend/frontend directories:

```powershell
# backend
./venv/Scripts/python.exe -m pytest tests/test_spatial_review.py tests/test_news_results.py tests/test_news_placement_preview.py tests/test_news_processing.py tests/test_flood_routing_policy.py -q -p no:cacheprovider --tb=short
# frontend
npx tsc --noEmit
npx eslint src/features/admin/review src/features/admin/components/PendingReportsPanel.tsx src/features/news/newsApi.ts tests/spatial-review.spec.ts tests/news-articles.spec.ts
$env:PLAYWRIGHT_CHROME_PATH='C:/Program Files/Google/Chrome/Application/chrome.exe'
npx playwright test tests/spatial-review.spec.ts tests/news-intelligence.spec.ts tests/news-articles.spec.ts --workers=1 --output=test-results/final-review
```

## Remaining acceptance

Obtain developer visual acceptance and execute the real authenticated mixed-source API/PostGIS check when the integration services are available. Review reads require the matching backend update; the existing deployed API has not been updated by this task. Provision analytical assets for the eventual matching API/collector release. Durable news decision/identity/correction/expiry/publication contracts remain separate gates. No historical news was reprocessed or activated during this task.

## October 4 follow-up: related cards and source styling

The developer's screenshots show three nearby Dr. Sixto Antonio reports repeated as plain individual rows. Investigated `merge_service.find_merge_candidates`: its existing engine uses normalized road identity/OSM ways, an approximately 500 m prefilter, corridor overlap, locality, temporal scoring and explicit conflict review. Calling it from a polled list would also trace roads and synthesize geometry. The display grouping therefore reuses `normalize_road_name` and conservative proximity/time/locality checks without invoking the merge engine's tracing, synthesis or writes.

- A group requires the same normalized road and known city, matching barangays when both are known, usable geometry and every pair within 500 m and two hours. Native PostgreSQL transforms geometry to UTM 51N metres before comparisons. Missing geometry/locality, different roads, distant reports and widely separated report times stay separate. User grouping uses report creation time; this does not establish flood onset or shared incident identity. Complete-link checks prevent chaining along a long avenue. News claims remain individual source cards; unresolved suggestions cannot establish shared incident identity.
- Groups use a stable oldest-report-ID anchor, with ordering by the latest member's report time. Each member retains its identity, evidence, severity, depth and existing actions. Root payloads include at most three member previews. Protected `GET /api/v1/admin/review/groups/{key}/members` paginates larger groups (20 by default, maximum 100). Grouping is computed before card pagination, so individual-row page boundaries cannot split a group. Refresh/moderation also invalidates member reads.
- `ReviewQueueCard` uses light blue user cards and light violet news cards, source icons/text, severity/depth chips, timestamps and expandable related counts. Expanding compares original reports; selecting one opens its existing detail. Back restores expansion and focus. Desktop/mobile, 44px member controls and existing bottom-navigation clearance are preserved. No automatic database merge, consensus decision, geometry activation or routing change occurs.
- Final backend selection: **95 passed**, including the 13 new grouping cases, role checks for member reads, 25-member pagination with conflicting measurements, conservative exclusions, anti-chain bounds and native projection SQL compilation. TypeScript and scoped lint pass. Current Spatial Operations browser checks: **18 distinct passing cases**, with two viewport-specific skips, across the corrected main run and focused follow-up. They cover source colors, group expansion, member-specific actions/focus, lazy 25-member pagination and visible failed-member retry, plus the existing map/draft/error flows. Initial browser attempts had no dev server (`ERR_CONNECTION_REFUSED`); starting the frontend resolved that. The group-detail assertion was then scoped to its evidence region because the hidden mounted queue retains the same report title.
- Screenshot review confirmed both source styles and the expanded mobile layout. Evidence is under ignored `frontend/test-results/grouped-review-verified/` and `grouped-review-focused/`. These use mocked staff/API responses and basemap styles. Native PostGIS execution and actual authenticated report grouping remain unverified; no live database writes occurred.
- To group before pagination, reads inspect compact identities for the current queue and location/geometry/time metadata for pending user reports; only selected card/member bodies are fetched. Very large pending queues have not been load-tested. The full corridor/class/conflict checks still belong to the actual manual merge workflow. No dependency, SQLAlchemy model or Alembic revision changed; restart the backend to load the changed response and new member route.

## October 4 follow-up: related reports inside details

The developer retained the queue styling and requested related reports inside the opened report instead of a queue dropdown. The intervening primary-panel redesign was undone; Active Zones and the original report presentation remain unchanged.

`ReviewQueueCard` now always opens evidence and keeps only a related-count badge. `RelatedReviewReports` renders a plain list below the user report, reusing backend grouping and the protected member route. Selecting a member loads its original evidence/actions and map focus. Back restores focus to the original queue card. Large groups load only when details open and retain their member page when switching reports. Failed member reads have an explicit retry. News and standalone user cards do not inherit a previous group's list. This is display navigation, with no automatic merge or changed matching rules.

Verification: TypeScript/scoped ESLint and 18 browser cases pass, with two viewport-specific skips. Checks cover no queue dropdown, related member navigation, queue focus restoration, retained large-group pages, explicit retry, source separation and narrow/landscape Map/Evidence switching. Desktop/mobile screenshots were inspected under ignored `frontend/test-results/related-in-detail/`. Staff/API responses and basemap styles are mocked; native integration remains unverified. No backend, schema, migration or dependency changes were required.

## October 4 follow-up: consistent related-report layout

The developer's screenshot shows the main report using the original report layout while related rows use compact text links, including a duplicate of the selected report. Related rows now reuse `PendingReportsPanel` with the same source background, severity/depth badges, timestamp, source text/location, Info and own-record moderation controls. The selected report appears only once at the top; choosing another report swaps the primary evidence and retains the member page.

Each visible related record uses the existing protected `GET /admin/review/items/{key}` and shared detail cache, rather than constructing a report from incomplete preview metadata. Reads are bounded to the current member page (maximum 20), with explicit per-record loading/error/retry. Current-queue status gates actions for each record. Approval/rejection of a different report keeps the primary detail open. Queue grouping/styling, Active Zones, backend rules and schemas are unchanged.

Verification: TypeScript and scoped ESLint pass. Across the main and focused runs, 22 distinct browser cases pass with two viewport skips, including matching full report controls, no selected-row duplicate, correct related Info identity, own-ID approval while preserving the primary detail, per-report failure/retry, pagination, queue focus and narrow/landscape navigation. Approval is mocked; no live moderation or database write occurred. Native API/PostGIS integration remains unverified. Desktop/mobile screenshots are under ignored `frontend/test-results/related-report-layout/` and `related-report-actions/`. No dependency, model or migration change.

## October 4 follow-up: selected-report group resolution

The developer's screenshots show reciprocal #2/#4 relations but both reports appearing under #3 after map selection. The retained `NeedsReviewPanel.openedGroup` was updated only by queue-card clicks; map selection changed the selected identity while leaving the previous card's group attached. The protected member read also accepted only the group's oldest-ID anchor.

Removed retained group state and resolve current membership from the selected identity through the protected member endpoint. The backend accepts any current member, returning its canonical group key and reason. Each query is cached by selected identity and page. Singleton groups hide the related section; failed reads expose retry. Existing full-report controls, styling, pagination and grouping/merge policy remain. In the screenshots #3 is labeled Rosario while #2/#4 are Maybunga; known different barangays fail the current locality check even when geographically nearby. This does not establish actual incident identity or justify automatic merging.

Verification: **31 backend checks pass**, including endpoint reads for #2/#4's shared group, separate nearby Rosario #3, non-anchor 25-member pagination and existing staff guards/read-only checks. TypeScript and scoped ESLint pass. **26 desktop/mobile browser cases pass**, with two viewport-specific skips. Both viewports cover actual rendered map clicks and external Moderation Center handoffs after another queue group has been opened, as well as existing moderation, pagination and retry flows. APIs/staff and basemap are mocked. Evidence is under ignored `frontend/test-results/selected-report-group/`.

A guarded read-only attempt against loopback `lanes_news_test` timed out before report records could be fetched. Actual stored road/locality metadata, exact distances and native PostGIS/API membership therefore remain unverified. No live database or moderation write, dependency, SQLAlchemy model or Alembic revision changed. Restart the local backend to load the updated member response and refresh the frontend.

## October 4 follow-up: cross-boundary growth scope

The developer noted that growing floods can cross streets/barangays and asked whether multi-location storage and zone extension had already been considered. Reviewed Phase 33 progress, the active task plan and `flood-event-history-design.md`: its `flood_event_locations` design explicitly supports multi-road and cross-barangay events. Current `models/report.py` implements one event with many locations, reports and zones. `flood_event_service._record_report_location_rows` records a supporting report's road, barangay and city, and `link_supporting_report` invokes it. This basic capacity does not require a new location table.

Static source findings:

- Display grouping currently rejects known differing barangays/normalized roads; actual pending-report merge scoring allows different barangays. Proximity alone does not establish common incident identity.
- `find_merge_candidates` reads nearby pending reports, not active zone candidates. Its docstring overstates that scope.
- `/zones/{zone_id}/merge-pending` approves and links reports as supporting evidence without changing zone geometry.
- `/reports/merge` targeting an existing zone replaces its boundary with submitted `final.geometry`. The workspace starts that geometry from the primary report; selecting an existing zone does not automatically preserve or add its previous boundary. An administrator can submit a complete expanded boundary, but that preservation is not guaranteed by selecting the destination.
- Line synthesis chooses the longest input line and projects report endpoints onto it. The result is bounded by that baseline and is not a reliable general extension/branching-road algorithm. Active zones currently use Polygon boundaries, while events can own multiple zones; disconnected flood sections should not be bridged automatically into a filled hull.

Recommended next scope: backend-owned cross-boundary report/active-zone discovery, compatible incident-time/evidence checks, explicit corroboration versus extension, preserved supported old coverage and road-core geometry, multiple affected places via existing event locations, and separate per-section zones when conditions/geometry require them. A later update to an ongoing event should not be rejected solely because its original report is more than two hours old. Keep original reports and change history; preserve current routing eligibility. UP NOAH/Pasig DRRMO context cannot alone prove current flooding of intervening sections. Required checks include unrelated nearby incidents, cross-barangay growth, connected/branching roads, late growth, different local depths, retained coverage, repeat requests and desktop/mobile review.

Recorded as [BUG-096](../others/bug-log.md#bug-096-cross-boundary-flood-growth-lacks-a-consistent-review-and-extension-workflow) and unchecked follow-up tasks. This is a source/design review with documentation updates only: no application/schema changes, tests, live database operation or verified #2/#3 geographic match. The previous 31 backend/26 browser checks validate the stale-selection fix, not this proposed growth behavior.

## October 4 cross-boundary growth implementation

Implemented locally on `roi-branch` after authorization. The preceding scope section records the earlier source audit; its pending statements describe that checkpoint.

- **Related evidence:** different barangays no longer exclude pending user reports. Production grouping uses projected geometry, pairwise report creation times within two hours, 500 m for the same normalized road/city and 50 m for other road/city combinations. Missing road/city/geometry stays separate. Complete-link grouping prevents a chain from joining distant endpoints. News claims remain independently reviewed.
- **Existing events:** merge suggestions now include the nearest twenty active event-owned zones within 500 m, excluding inactive/expired zones and ended events. An event's original age is not a fixed two-hour lifetime. These are review candidates; shared incident/affected extent still requires an admin decision. Existing OSM/corridor/name/time scoring remains for pending-report candidates; a nearby crossing-road section within 50 m/two hours can be surfaced for review.
- **Three explicit actions:** `extend` unions the supported old polygon and road core with the reviewed new section; `corroborate` retains the old boundary and operational conditions; `add_section` creates a distinct zone/conditions under the existing event. Multiple road/barangay/city location rows are recorded by the existing event service. Original reports and Community Feed posts are preserved. A report may update an existing event without needing another pending report.
- **Coverage integrity:** secured read-only `POST /api/v1/admin/reports/merge-preview` and publication share `compose_reviewed_coverage`. All submitted road branches are retained, buffered in UTM 51N, and previewed as the final polygon. Points, empty/invalid shapes and disconnected combined boundaries are rejected. No convex hull invents a flooded intervening area. The submitted reviewed core remains separate from the buffered preview, avoiding double buffering. Legacy single-report approval also retains old coverage; batch merge remains evidence-only and now rejects expired targets.
- **Atomic history:** ordered report locks, target/event locks, report outcomes, event locations/timeline and merge audit are saved together. Repeat publication returns the existing association instead of another zone/outcome. A simulated audit failure rolls back coverage and report approval.
- **UI:** reused shared Button/toast and existing ZoneDataEditorForm; retained the existing queue/detail styling. Nearby zone selection, action choice and server coverage errors/retry appear in the existing merge workspace. Confirmation distinguishes evidence-only linking from operational edits. Successful publication invalidates map, review and event caches.

Verification: **46 distinct backend checks** pass across the rollback-isolated native PostGIS growth/API tests and existing review/grouping tests. Includes actual local JWT/staff reads, unauthorized/Commuter rejection, old active-event discovery, cross-barangay growth, branch retention, separate per-section depths, retained old coverage/core, preview-versus-published GeoJSON parity, original post preservation, idempotent outcomes and atomic rollback. The full review/growth run passed 45 checks before adding the native authenticated read case; the final two targeted authenticated/legacy checks pass. Native fixtures use the guarded loopback `lanes_news_test` database and an outer rollback, not the cloud database or user reports.

**34 distinct desktop/mobile browser checks pass**, with two expected viewport-specific skips. The eight new action/failure cases pass; existing review regressions pass after correcting the rendered-pixel click test to target the largest report-colored component rather than averaging palette-control pixels. TypeScript and scoped component/test lint pass. `adminApi.ts` retains six pre-existing `no-explicit-any` lint violations outside this change. Browser action tests mock API/basemap responses; native request tests separately exercise the actual server/database. Screenshot review exposed the mobile fixed drawer being clipped behind the admin sidebar. The merge drawer now uses the map content bounds on mobile/coarse-pointer layouts, and its Map button remains available in landscape. Narrow/landscape screenshots and control-bound assertions pass; the final focused browser run passed eleven checks with one expected viewport skip (included in the distinct totals above).

No SQLAlchemy model, Alembic migration or package change was required (Shapely is already pinned). The native test database is at revision `c5a7e9d2104f`; no schema upgrade was introduced. Actual screenshot reports #2/#3/#4 are absent from this dedicated test database, so their exact distances and shared incident remain unverified. Developer visual acceptance and production rollout remain pending; the reviewed bundle is prepared for the authorized `roi-branch` checkpoint. Automatic news publication/lifecycle and durable news exception decisions remain separate unfinished scope. UP NOAH/Pasig DRRMO context does not prove current flood continuity.

During verification, Docker Desktop startup failed on stale Windows socket reparse points in the ingest and Secrets Engine runtime directories. Stopped Docker's processes, preserved timestamped copies of only those runtime directories, recreated them and restarted Desktop; existing PostGIS and Valhalla containers are running. No factory reset, database/volume deletion or WSL shutdown was performed. This matches the reported [Docker socket workaround](https://github.com/docker/desktop-feedback/issues/554).

Author: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## October 4 senior-planner checkpoint audit

Audited the eight authoritative records against the actual changed files and prior verification. Updated task/progress, the existing Spatial Operations feature section, system/API behavior, stack compatibility, database compatibility and BUG-096. `decisions.md` remains unchanged because this reuses the established service/frontend architecture and event model. Refreshed the master evaluation index and F5 plan; native user-review verification is distinguished from pending native news placement and developer acceptance. Original checkpoint/test history remains intact.

Confirmed active identity Roi Cambe and branch `roi-branch`; fetch showed zero local/remote divergence before this commit. No model, migration, requirement, package or lockfile diff exists. The pre-push guarded local `alembic upgrade head` completed successfully without introducing a revision. Existing declared dependencies cover new imports; private runtime configuration, screenshots, test output and Docker runtime backups remain outside the commit. Prior verification remains applicable: 46 distinct backend checks, 34 distinct desktop/mobile browser checks (two expected skips), TypeScript and scoped lint. The checkpoint includes the earlier combined Needs Review implementation and its related-report fixes plus reviewed flood growth; it does not deploy the system or complete automatic news decisions/publication.

The user authorized shutdown only after documentation and branch push complete. Power-off is an operational follow-up, not an application change. ([@roicambe](https://github.com/roicambe) (Roi Cambe))


## October 4 Primary Panel search and detail consistency

**Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe). **Scope:** retain the existing Spatial Operations design and source colors; improve queue organization/context, useful details and shared action sizing. Implementation was initially local on `roi-branch`; the subsequent request authorizes its documentation audit and branch checkpoint push. Deployment and developer visual acceptance remain separate.

### Behavior and boundaries

- Protected queue reads add bounded `q`, city, barangay and severity inputs. Search is case-insensitive/all-word literal matching across title, road, city, barangay, evidence and review reason. Severity `unknown` covers unassessed evidence, including news claims without an assessment.
- Grouping precedes filtering. Every supplied criterion must match one member; any matching member returns the entire group and its canonical anchor, including members in different roads/cities/barangays. Filtering does not rewrite membership or moderation targets. Pagination/counts apply to matching full groups. Source totals remain global; filtered `item_total` includes all records in those returned groups, not just matching members.
- Facets come from the source-wide eligible queue rather than a single page or the current text/severity match. Barangays belong to the selected city; city aliases use the existing locality normalization. Empty results remain clearable. City changes reset barangay; selected locations remain visible after source switching. Search debounces 300 ms and filters survive opening/back navigation.
- Server cards summarize all members' roads/areas, severity/depth diversity and latest queue time. Road/area text is bounded to three names with a remainder count; card depth badges show three distinct values and point to details for more. Individual evidence remains authoritative. News and user cards retain violet/blue styling and no member dropdown.
- `FloodRecordSummary` supplies the common flat record layout, severity/depth badges, full date/time, location, fact rows and action slot. Pending evidence adds existing reporter/trust, reported vehicles/hazards and attachment count. Active zones expose existing effective conditions, primary report, expiry and admin notes. `ZoneContributors` reuses the same presentation, preserving original facts and inspect/restore map selection.
- `SpatialPanelButton` delegates to the existing shared Button `size="sm"`: desktop action height is 32 px, narrow/coarse-pointer minimum is 44 px. Shared Input/Select and Pagination remain in use; main scroll containers retain CSS-variable/safe-area bottom padding. The rest of the admin panel, map plotting, grouping distances and merge publication logic are unchanged.

### Verification

- `dotenvx run -f .env.test.local -f .env -- .\venv\Scripts\python.exe -m pytest tests/test_spatial_review.py tests/test_spatial_review_grouping.py -q`: **33 passed**. Includes matching the final record in a 300-record backlog before pagination, intact cross-city groups, canonical member reads, simultaneous per-member filters, city alias matching, facet stability, literal percent search, invalid lengths/severities, auth and storage errors. Uses isolated SQLite fixtures and PostgreSQL SQL compilation; no fresh native database integration run for these filters.
- Existing Spatial Operations Playwright suite: 32 passes and two expected viewport skips initially; two empty-page timeouts during active edits pass in isolated reruns. Four new desktop/mobile filter/detail/zone cases pass after correcting test selectors for the existing generic Modal and its independent bulk-action Cancel button. **38 distinct browser cases pass**, with two expected skips. New fixtures mock staff/API data and basemap; this does not establish production/native data acceptance.
- New browser checks verify complete group presentation, request parameters, source counts, clear/zero-result states, city resetting barangay, selected facets after source switching, retained filters after back navigation, 32/44 px action heights, own-zone edit/deactivate confirmation, contributor inspection/restoration and zero writes during inspection. 320 px narrow and 844×390 touch landscape are checked. Screenshots are kept under ignored `frontend/test-results/primary-panel-*` output directories and visually inspected.
- TypeScript and scoped ESLint pass; `git diff --check` passes. No package/lockfile, SQLAlchemy model or Alembic migration changes. Existing merge-mode browser regressions continue to pass; no live reports/zones were published or deactivated.

### Senior-planner audit

Audited all eight authoritative records. Updated task plan, reverse-chronological progress, existing Feature 7, system documentation and BUG-097. Tech stack/dependency, architectural decisions and database-design records remain accurate and unchanged because this refinement uses existing technologies/tables and no architectural pivot. Updated this existing evaluation and its catalog description. Developer visual acceptance and the previously unfinished news exception decisions/automatic publication remain open; this task does not close those milestones.


## October 4 Primary Panel push audit

**Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe). The developer requested the senior-planner audit/update and push to `roi-branch` after the Primary Panel implementation.

Read the skill, repository instructions and design; confirmed Roi Cambe's Git identity and active `roi-branch`. Audited all eight authoritative records, existing evaluation/catalog and Priority 5 plan. Updated task/progress tracking, existing Feature 7 context, screen/API/component documentation and BUG-097. Kept architectural decisions unchanged because there is no architectural pivot. Recorded existing-dependency and existing-storage compatibility in the stack/database records, and synchronized the F5 plan with implemented search/facets/shared details while keeping acceptance and news publication milestones open.

Prior verification applies to the unchanged implementation: 33 backend checks, 38 distinct desktop/mobile browser cases passing across the original run and focused reruns, two expected viewport skips, TypeScript and scoped ESLint. No additional application changes or test claims are introduced by this documentation-only follow-up. Fetch found zero local/remote divergence before the checkpoint.

The pre-push attempt validated a loopback-only `lanes_news_test` target and invoked `alembic upgrade head`, but could not complete because Docker Desktop's Linux engine/PostGIS was not running. The attempt returned a database connection timeout; checked for remaining task-owned Alembic processes. No fresh migration success is claimed, and no cloud database was used. The checkpoint changes no SQLAlchemy models, Alembic revisions, requirements, packages or lockfiles; the last verified schema remains `c5a7e9d2104f`. Pulling these UI/read-contract changes introduces no new migration or installation step. Screenshots, private environment files and test output remain outside the checkpoint. Production deployment and developer visual acceptance remain pending.


## October 4 city-first barangay filter

**Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe). The developer accepted requiring a city before choosing a barangay. `NeedsReviewPanel` disables Barangay and displays “Select a city first” when City is All cities. Selecting a city enables the existing server-scoped barangay options; changing city clears barangay and clearing filters disables it again. The shared `Select` adds optional native disabled support with a muted trigger and no interactive dropdown while disabled; other callers retain the default enabled behavior.

The existing queue/filter Playwright flow passes on desktop and mobile (**2 passed**), including the disabled/placeholder initial and reset states, enabling after city selection, Cainta showing San Andres and excluding Rosario, retained groups/back navigation and 320 px/touch-landscape overflow checks. TypeScript and scoped ESLint pass; the mobile screenshot was visually inspected. No backend, model, migration or dependency change; source/filter/grouping policy remains as documented. This follow-up remains local after checkpoint `615feae`.
