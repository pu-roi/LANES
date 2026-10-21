# Shared Spatial Operations queues — local acceptance

Date: October 21, 2026 (Asia/Manila). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Branch: `roi-branch`.

## Delivered behavior

Active Only groups original zone geometry across user-report, news and official sources when every pair has complete, unambiguous matching normalized road/city evidence and is within 50 m. Valid saved source geometry takes precedence; otherwise valid linked report geometries are combined. Missing/conflicting locations or unavailable original geometry stay separate. This supersedes the initial polygon-based 500 m/50 m acceptance below. There is no zone creation-time cutoff. Existing active/expiry eligibility and simulation clocks apply. Needs Review retains its existing original-report proximity, two-hour rule and separate news cards.

Both tabs share card/filter presentation. Group inspection preserves individual zone evidence, provenance, contributors, updates, map focus, editing and confirmed deactivation. Bulk selection applies to displayed eligible records, with actions available in the mobile panel. History remains individual detailed entries. Grouping precedes filtering and pagination and performs no lifecycle, geometry or routing writes.

## Verification recorded in this implementation session

| Checks | Result | Coverage |
| --- | --- | --- |
| Queue/review unit and HTTP regressions | 48 passed | Distance boundaries, fallback/missing metadata, complete-link chains, source separation, search through all linked evidence, filters retaining groups, pagination, identity, authorization and visible storage failures |
| Native PostGIS and expiry-policy regressions | 25 passed | Four new native queue checks plus 21 existing expiry checks; existing migration chain to head in a fresh disposable local database; read-only geometry/lifecycle preservation, active/expired/history state, paused expiry, original news provenance and query counts independent of card count |
| Browser acceptance | 34 distinct checks passed | Desktop/mobile Chromium, including 320 px width, grouped cards, filters, back navigation/focus, member pagination, page-scoped selection, explicit bulk request IDs and cancel/confirm, vanished groups, report-to-zone handoffs, source/forecast details, contributor/public-update behavior and edit-draft/save/version regressions |
| TypeScript | Passed | `npx tsc --noEmit --incremental false` |
| Focused lint | Passed | Shared/new queue components, API client, Needs Review adapter and new browser suite |
| Existing LiveMap lint baseline | Unchanged | 12 existing errors before and after; no introduced error signatures |
| Whitespace/dependencies/schema | Passed | `git diff --check`; existing Python/Node dependencies only; SQLAlchemy models and Alembic definitions unchanged |

Backend commands, from `backend/` with the repository environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_zone_queue.py tests/test_spatial_review_grouping.py tests/test_spatial_review.py -q
# Set LANES_SETTINGS_TEST_DATABASE_URL to an empty disposable local database named lanes_settings_test_*.
.\.venv\Scripts\python.exe -m pytest tests/test_zone_queue_postgres.py tests/test_pasig_ml_expiry.py -q
```

Native acceptance created an owned local database, applied the existing Alembic chain through the established fixture, ran the checks, then removed that database. No shared or production database was migrated.

The 34 distinct browser checks comprise 18 passing shared-queue/review cases, a 12-check follow-up (including the two bulk cases corrected below), and four edit-draft/save/version checks. The suites are `zone-queue.spec.ts`, selected Spatial Operations cases in `spatial-review.spec.ts`, moderation handoffs in `flood-moderation-map.spec.ts`, and forecast/history cases in `flood-review-suggestions.spec.ts`. Detailed local screenshots/traces remain in ignored `frontend/test-results/` acceptance directories rather than being published as user data.

## Corrections and limits

Early browser runs used incorrect selectors for the existing custom Select and legacy confirmation modal; these were corrected to match their actual controls. Concurrent output-directory use and UI edits during early runs disrupted traces/navigation; the clean acceptance runs used separate output directories and stable UI. One initial native preservation assertion compared an in-memory geometry encoding with the persisted encoding; the test now captures persisted values before exercising the readers. Final counts above include passing scenarios only, not failed/repeated attempts.

This is local acceptance with constructed browser and database fixtures. It does not establish real-device/provider acceptance or a hosted deployment. Git publication is authorized only to `roi-branch`; no production deployment, worker activation, schema or dependency change is included.

## Follow-up: group card map focus — October 21, 2026, 03:58 AM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Clicking or pressing Enter on an Active Only card opens inspection and immediately fits the map to server-provided WGS84 bounds of all members, independent of filters/member pagination. Mobile opens the map and **Back to zones** returns to the inspected records. Individual-zone actions and page-scoped selection remain available. Missing bounds leave inspection open and show an explicit map error. No grouping thresholds, eligibility, stored geometry, routing, models, migrations or dependencies changed. This follow-up remains local and uncommitted.

Follow-up checks (separate from the original acceptance counts above):

- **50 passed**: queue/review unit and HTTP regressions, including complete group bounds and unavailable/out-of-range bounds.
- **4 passed**: native PostGIS queue acceptance, including WGS84 extent, existing migrations to head in an owned disposable database, read-only preservation and batched reads. The database was removed afterward.
- **16 passed**: selected `zone-queue.spec.ts` and `spatial-review.spec.ts` desktop/mobile checks, including pointer/Enter activation, 320 px map/return navigation, missing-bound errors, queue restoration, member pagination, contributors and confirmed bulk actions. The first browser launch attempt found port 3000 unavailable; after starting an owned development server, the complete run passed. Final output is in ignored `frontend/test-results/zone-card-flight-ready/`.
- TypeScript and focused ESLint pass; LiveMap retains its 12 baseline errors with no introduced signatures. `git diff --check` passes.
- Desktop and 320 px mobile map-focus screenshots were inspected. Browser fixtures mock provider/map data; this does not establish live map-provider or physical-device acceptance.

## Follow-up: Active Zones labels and wide touch layout — October 21, 2026, 02:11 PM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Active Zones now uses zone terminology for loading, history, accessible search, refresh/retry, returning from a group and surfaced reader errors. Needs Review retains its queue wording. Internal endpoint/cache names remain compatible.

Spatial Operations separates width-driven `isCompactLayout` from map `isTouchDevice`. Wide mouse/touch both retain the sidebar and map; narrow screens retain the existing list/map navigation. This fixes the 1920×1080 touch-emulation reproduction (previously 1864 px sidebar instead of 460 px). The test inspection helper also uses width for whether it must return from the mobile map. Existing landscape review assertions now expect a split layout at 844 px and exercise full-screen map switching while narrow.

Final follow-up verification: **16 backend tests pass** (`tests/test_zone_queue.py`); **23 browser checks pass**, with one desktop mobile-only skip. The zone suite passes 16 checks in `frontend/test-results/active-zones-label-layout/`; final Needs Review, merge and landscape regression passes seven checks in `frontend/test-results/spatial-width-final/`. Earlier seven passing regression checks preceded the additional visual correction and are not counted twice. TypeScript and focused lint pass. LiveMap lint comparison is 12 errors at HEAD/11 current with no introduced signatures; full-project lint remains subject to its existing findings. `git diff --check` passes. Browser coverage includes group filters/pagination, individual selection and bulk confirmations, loading/error/history labels, pointer/Enter flight, missing bounds, mouse/touch 1920 px inspection, 767/768 boundary and 320 px map return. Screenshots use fictional API and map data; no real zone writes, physical-device or live-provider acceptance is claimed. No SQLAlchemy model, migration, dependency, grouping, expiry or routing change; no commit/push.

Visual follow-up: the first landscape merge screenshot exposed a clipped secondary workspace despite interaction tests passing. At 768–1023 px, the primary sidebar now hides while a secondary workspace is open, leaving the workspace beside the map. The landscape test explicitly checks the entire drawer bounds and publish control against the viewport; final acceptance uses the corrected layout.

## Follow-up: original geometry and matching roads — October 21, 2026

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Active Only now requires complete matching road/city evidence and original geometries within 50 m for every pair. Valid saved source geometry takes precedence; otherwise valid linked report geometries are combined. Missing/conflicting locations or unavailable original geometry stay separate. Full saved polygons still determine group camera bounds. Source categories, active eligibility, no time cutoff, filtering/pagination, history and individual actions are retained. Needs Review grouping and shared mechanics are unchanged.

- **58 portable queue/review checks pass**, including 50 m boundaries, overlapping different roads/cities, missing/conflicting evidence, short segments inside long ones, source precedence/report unions, polygon padding, chain prevention, filters/counts, history, map bounds and staff authorization.
- **28 native PostGIS/expiry checks pass**, including seven queue checks and the 21 existing expiry checks. The existing migration chain ran to head only in a fresh owned local database, which was removed afterward. Batched geometry reads, saved source precedence, original 77.5 m versus buffered 27.5 m gaps, contributors/provenance and read-only lifecycle preservation are covered.
- A transaction explicitly marked read-only verifies saved zones **69 and 70** resolve to separate singleton groups. Geometry/source hashes, update timestamps, active flags and expiry remain unchanged. The optional local test profile has no matching saved records; the normal encrypted backend profile supplied this example verification.
- TypeScript and focused UI/API/test lint pass. No model, migration, dependency, stored zone, routing, commit or push changes. The existing Shapely dependency supplies geometry union operations.
- **76 distinct browser checks pass**, with two layout-specific skips. The broad `zone-queue.spec.ts` / `spatial-review.spec.ts` run passed 74, skipped two and failed two; the desktop loading-timeout case passed separately in `active-zone-original-retry`. The mobile related-report test contained an obsolete 844 px mobile-switch expectation; it now checks switching at 320 px and split view at 844 px. Its first concurrent rerun hit initial loading; the final isolated run passed in `active-zone-review-landscape-final`. Passing reruns are counted once per distinct case. Screenshots and traces remain under ignored `frontend/test-results/active-zone-original-geometry/` and focused retry directories. Desktop wide-touch and 320 px filter screenshots were inspected. Provider/map data is mocked; physical-device and hosted-provider acceptance is not claimed.
