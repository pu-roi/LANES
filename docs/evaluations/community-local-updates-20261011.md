# Community Feed Local Updates — October 11, 2026

Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 11, 11:30 AM live follow-up:** the loading failure is resolved; live desktop/mobile use the endpoint successfully and show no qualifying recent articles. Earlier local-only release statements below describe the initial implementation.

**October 11 noon coverage correction:** the developer selected commuter news (weather, traffic, road closures, transport disruptions and safety advisories). The flood-only descriptions below are the initial implementation, superseded by the commuter coverage section at the end.

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

## Live loading failure and traffic repair — October 11, 11:30 AM PHT

The developer reported “Couldn’t load local news” on the live feed. `https://navlanes.live/api/v1/news/local-updates?limit=5` returned HTTP 404 while the existing alerts endpoint returned 200. Public OpenAPI lacked the new route. Cloud Run `lanes-api` in project `lanes-project-508809`, region `asia-east1`, still sent 100% traffic to October 10 recovery revision `lanes-api-00069-fey`.

Cloud Build `cac64f6f-4027-431b-abc0-7cba056678b4` succeeded for main commit `9ab8979118871c4a466bd78aeba5af4ff646c2f4`, which includes Local Updates commit `ff67bdf`. Its newer revision `lanes-api-00064-kjc` was ready but received no traffic. Revision numbers are not chronological here; the new revision was created October 11 at 1:55 AM PHT. Both news/expiry jobs already use the new commit image.

Added temporary tag `local-updates-check` to the new revision, verified healthy database connectivity and HTTP 200 with `items: []`, then explicitly promoted that revision to 100%. Removed the temporary tag after acceptance; old recovery revision/tag remains available. No new build, image, migration, database write, policy save, scheduler change, AI call or worker execution was required for this traffic repair.

Actual production verification:

- Public site `/api/v1/news/local-updates?limit=5`: **200**, empty items with current `as_of`; a healthy empty result, not a claim that there is no flooding.
- Cloud API `/health`: **200**, database connected. Existing public alerts: **200**. Unauthenticated staff collection: **401**.
- Unmocked Chromium at 1440×1000 and 390×844: actual news request **200**, visible “No recent local flood news is available.”, no Local Updates error. Mobile expanded through the real summary control. Both card screenshots were inspected.

Durable prevention in `cloudbuild.yaml`: prepare the API with `--no-traffic` and unique `--revision-suffix=build-$BUILD_ID`; after the existing migration and both worker deployments, use `--to-revisions=lanes-api-build-$BUILD_ID=100`. This avoids preserved manual rollback pins and targets the exact build rather than a potentially different latest revision. Existing gcloud help confirms naming/no-traffic semantics. YAML parsing and assertions verify the preparation flags, final exact revision promotion and preceding worker steps. A new Cloud Build execution of this configuration has not been performed. No new application tests, package imports or SQLAlchemy/Alembic changes were needed for this deployment-only fix.

Author: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Commuter news coverage — October 11 noon PHT

The developer rejected the flood-only empty widget and explicitly chose relevant commuter news outside flooding. Both admission and the reader previously required observed Metro Manila flooding. Changing the empty-state text alone would not collect any useful articles.

`local_news_relevance.py` admits weather forecasts/advisories, traffic changes/road closures, rail/bus/jeepney operations, safety/class-suspension and local service advisories supported by a current body sentence naming Metro Manila or a specific Metro rail line. A Manila dateline or weather-office address is not local impact. Broad national weather leads may be fetched within the bounded commuter budget, but the body must actually include Metro Manila. General politics, sports, entertainment, stock trading and non-local reports do not fill the widget. The original strict observed-flood admission remains separate.

The approved GMA source now also uses its official Metro, weather, transportation and Walang Pasok RSS endpoints, found on [GMA's own feed listing](https://www.gmanetwork.com/news/rss/) and verified by actual parsed responses. No new publisher/source identity was enabled. Date/domain/readable-body checks remain in place. Up to 14 additional non-flood bodies are fetched per run, at most four per feed; they cannot exhaust the existing flood-location probe budget. Publisher fallback keeps one primary feed per source within its existing five-probe budget, preserving independent publisher coverage after adding the supplemental feeds.

Commuter stories are saved in existing article/provenance tables with the existing string `review_state` set to `local_update`. They never enqueue immutable flood extraction runs. Collection labels them excluded from flood reports, so they do not become unprocessed flood attention. A later body with real flood observations can enter normal pending processing; rejected/suppressed articles are not revived. Duplicate URLs/GUIDs and unchanged bodies retain feed provenance without reclassifying local-only stories. Failed refreshed bodies are marked unavailable, and the public reader checks the newest saved body. No SQLAlchemy model or migration change is involved.

Shared `LocalUpdates.tsx` describes weather/traffic/transport/safety coverage and uses the generic “No recent local updates are available.” only when no qualifying recent collected story exists. Publisher/date/source links and request/refresh/cache/offline behavior are unchanged.

Verification:

- 143 targeted backend tests pass across local-news/discovery/processing/collection correction/browsing/telemetry. Includes no-flood commuter reads, national forecast local body, nonlocal/dateline exclusion, no new extraction, duplicate/unchanged capture, valid flood promotion without moderation reset, failed refresh and separate fetch budgets.
- TypeScript and scoped ESLint pass. All ten existing desktop/mobile Chromium cases pass using a non-flood MRT service story; initial execution found the local server stopped, so the normal development server was started and the suite rerun.
- Actual approved-source collection through the configured database: six feeds parsed, **ten new commuter articles**, **zero flood candidates**, extraction runs **84 before/84 after**. Shared collection settings were already enabled and selected sources were respected. No audit, publication, map activation or schedule change occurred.
- Actual local API and unmocked desktop 1440×1000/mobile 390×844 each return **200 with five articles**. Both card screenshots were inspected. An initial mobile probe failed during Uvicorn test-file reload; restart without reload and both reads pass.
- Latest five include the October 11 Philstar weather forecast, today's La Naval traffic advisory, two GMA forecasts and a local Maynilad service notice. Article dates remain publication dates; the headline mentioning other regions qualifies because the actual body includes Metro Manila.

Cloud API/workers/frontend release is in progress. No new packages or schema changes require migration work.

Author: [@roicambe](https://github.com/roicambe) (Roi Cambe).
