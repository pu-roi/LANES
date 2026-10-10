# Community Feed Local Updates — October 11, 2026

Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Delivered behavior

Replace the two static Local Updates headlines with up to five recent collected news articles. The developer selected collected articles with publisher, publication date and original-source link, without waiting for recorded extraction or public-alert approval.

Public `GET /api/v1/news/local-updates?limit=5` returns only article ID, title, publisher label, approved HTTPS source URL, publication timestamp and response `as_of`. The limit is bounded to 1–10. The CRUD reader inspects at most 200 newest candidates published within seven days, with deterministic publication/ID ordering. It excludes missing/error/oversized bodies, missing/future/old publication dates and rejected/suppressed articles. The service checks enabled verified publisher identity/domain and reuses discovery's preliminary body-grounded Metro Manila flood-observation screen. It checks the current saved body rather than an older successful extraction. It performs no source fetch, external AI audit, durable extraction, publication or zone write. Full bodies and staff diagnostics are not exposed.

`LocalUpdates.tsx` is shared by desktop `RightSidebar.tsx` and the mobile/tablet expandable card above the feed composer in `FeedPage.tsx`. Dates use the existing Manila formatter. The list refreshes every minute while foregrounded, supports manual refresh and reconnect, and has loading, empty, failure/retry, offline and cached-on-failure states. Original source links open in a new tab. Article dates do not claim current flood confirmation. The desktop sidebar also remains shared with profile post inspection.

## Verification

- `backend/venv/Scripts/python.exe -m pytest tests/test_local_news.py -q`: **24 passed**. Includes public API/limit validation, exact public-field allowlist, SELECT-only reads, no extraction runs, source/domain/credential checks, recency/body/relevance exclusions, newest-body correction and publication ordering, safe 503 errors.
- `npx tsc --noEmit`: passed.
- Scoped ESLint for `LocalUpdates.tsx`, `localNewsApi.ts`, and `local-updates.spec.ts`: passed.
- `npx playwright test tests/local-updates.spec.ts --workers=1`: **10 passed** across desktop Chromium and mobile Chromium. Covers source/publisher/date display, layout bounds, empty state, retry, failed-refresh cache, refresh to empty and offline state.
- Desktop/mobile screenshots from the populated fixture were visually inspected. The compact desktop footer was adjusted to keep refresh beside the timestamp. An initial two-worker run passed eight scenarios but two checks timed out before any client query while the development page was hydrating; the final single-worker run with a bounded 45-second hydration allowance passed all ten.
- At October 11, 1:39:52 AM PHT, the actual configured PostgreSQL reader returned `items: []` in an explicitly read-only transaction followed by rollback. There are no recent qualifying articles to show in that snapshot. No artificial story or source timestamp was written to fill the list.
- The normal local backend was not listening during the first HTTP probe. Started it with the existing dotenvx/Uvicorn development command on port 8000. Actual `GET /api/v1/news/local-updates` returned HTTP 200 and an empty list at 1:41:44 AM PHT. Unmocked `/feed` desktop (1280×800) and mobile (390×844) browser checks each received HTTP 200 from the new endpoint and displayed the expected empty state; both screenshots were visually inspected. Cloud deployment was not performed.

## Scope and remaining work

This is collected Metro Manila flood news, not GPS-personalized news or a new broad commuter-news classifier. Drainage projects and bridge/traffic notices remain subject to the existing collector's narrower flood-observation rules. The 200-candidate cap intentionally bounds public read work; this endpoint is a latest-headlines widget, not a full article archive. Local Updates does not require a published claim and does not affect routing. Public map News Alerts and Admin News Intelligence are unchanged. No schema, migration, dependency, collector schedule or cloud deployment change was made. Existing backend/frontend release steps are needed to deploy the new endpoint/UI together.

## Planner and pre-push audit — October 11, 1:44 AM PHT

Reviewed all eight core records against the final implementation. Progress, task plan, existing Community Feed feature section, screen/component/API documentation and BUG-140 are synchronized; README catalogs this evaluation. Tech stack, architecture decisions and database design require no new entry: existing FastAPI/Pydantic/SQLAlchemy/TanStack Query/Lucide/pytest/Playwright packages cover all imports, and SQLAlchemy models and Alembic migrations are unchanged. New Pydantic response contracts do not change the database schema, so no migration is introduced or run for this feature.

Reviewed the public endpoint and response allowlist using the Security skill. This deliberately public metadata read exposes no account-specific data, full article bodies, staff diagnostics or lifecycle controls. Approved source/domain checks, bounded query/body sizes, safe 503 responses and visible frontend retry/offline states remain enforced. Authentication/CORS configuration is unchanged. Prior 24 backend/10 responsive checks, TypeScript/scoped lint and unmocked local HTTP/browser acceptance still apply; no implementation changes followed those checks. The current saved-data empty result is documented without claiming a new live article or a cloud release.

Publication target is `roi-branch`, authorized by the developer. Documentation distinguishes Git publication from backend/frontend deployment and leaves wider commuter-news collection and changes to News Intelligence/public map alerts as follow-up work. Author: [@roicambe](https://github.com/roicambe) (Roi Cambe).

Staged audit checked 18 intended files and eight added relative documentation links with no missing targets, embedded-credential matches or private/runtime artifacts. Python source syntax parses successfully; no models/migrations or dependency manifests changed. Removed extra blank lines at the end of seven new source/test files under the already-applied API/UI/Test skills; this formatting-only cleanup does not change verified behavior.
