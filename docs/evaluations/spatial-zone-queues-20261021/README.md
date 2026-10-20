# Shared Spatial Operations queues — local acceptance

Date: October 21, 2026 (Asia/Manila). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Branch: `roi-branch`.

## Delivered behavior

Active Only groups saved zone polygons across user-report, news and official sources. Every pair must qualify: 500 m with unambiguous matching normalized road/city evidence, otherwise 50 m, including missing metadata. There is no zone creation-time cutoff. Existing active/expiry eligibility and simulation clocks apply. Needs Review retains its two-hour rule and separate news cards.

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
