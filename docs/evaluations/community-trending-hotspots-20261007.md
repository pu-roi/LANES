# Community Trending Hotspots verification

> **Last Updated:** October 08, 2026, 12:01 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Implemented behavior

The community feed's desktop sidebar and mobile navigation share `TrendingHotspots.tsx`. Fixed example places/counts are replaced by public GET `/api/v1/feed/hotspots?limit=3`; the accepted limit is 1–10. The FastAPI service owns the time-window decision and parameterized PostGIS aggregation. The response includes place coordinates, post/contributor counts, latest activity, selected `window_hours`, and `as_of`.

- Search the last 24 hours first. Keep that window whenever at least one place qualifies, without filling remaining positions with older places.
- Only when that result is empty, search 48 hours. Stop there even if empty; automatically return to 24 hours when fresh activity qualifies.
- Require at least two distinct active contributors per location. Each person's latest qualifying activity contributes a recency weight with a six-hour half-life; repeated posts increase the displayed count without multiplying that person's ranking contribution.
- Match case/whitespace-normalized location labels and approximately 500 m spatial clusters. The radius is 500 projected metres in EPSG:3857, approximately 484 ground metres around Metro Manila. Different aliases are not automatically merged.
- Exclude future/older-than-window posts, hidden/deleted posts, inactive/deleted accounts, missing/invalid locations, and private/rejected/deleted linked reports. Linked reports must themselves be within the selected window; resharing older evidence cannot reset its original age.
- Display the selected window, honest empty content, visible errors and Retry. Refresh every minute and through existing feed query invalidations. Failures propagate as errors rather than triggering an age fallback.

Loading skeleton bars, empty-message padding, compact location rows and the blue retry action follow existing sidebar patterns. Long names use ellipsis while accessible link text/title retain full names. Loading status is available to screen readers; animations respect reduced motion. Mobile selection closes the navigation drawer and opens the location on the map.

## Verification

The final implementation passes **nine native PostgreSQL/PostGIS checks** in `backend/tests/test_trending_hotspots_postgres.py`. Existing Alembic migrations reach head in a fresh, uniquely named loopback database; the runner removes that database after completion. Application/cloud databases are not changed. Coverage includes ranking and repeated-author protection, spatial clustering, 24/48-hour boundaries, future timestamps, partial-list preference, fallback eligibility/privacy, returning to 24 hours, public response fields and limit validation.

The final implementation passes **ten Chromium browser checks** in `frontend/tests/trending-hotspots.spec.ts` across desktop and mobile projects. They cover map navigation, empty results after searching 48 hours, failure/retry, minute refresh, correct fallback labels and returning to 24 hours after new activity. The existing bounds check waits for the mobile drawer animation before measuring its position. Desktop/mobile populated and fallback screenshots were inspected; loading/empty/error screenshots were also inspected during the preceding UI consistency pass.

- Frontend: `npx playwright test tests/trending-hotspots.spec.ts --workers=1`.
- Frontend: `npx tsc --noEmit` and scoped ESLint pass.
- Backend: run `python -m pytest tests/test_trending_hotspots_postgres.py -q` with `LANES_HOTSPOTS_TEST_DATABASE_URL` pointing to an empty disposable loopback database named `lanes_hotspots_test_*`. The fixture refuses nonempty databases and applies existing migrations. Allocate and remove the disposable database outside the test fixture.
- `git diff --check` passes. No SQLAlchemy model, Alembic definition, dependency or operational routing policy changed.

## Documentation and release scope

The eight authoritative records were audited. Task plan/progress, the existing Community Feed feature section, screen/API documentation and BUG-120 reflect the current behavior. Database documentation records unchanged storage and migration acceptance. Tech stack and architectural decisions need no changes because this feature uses existing libraries and architecture. This evaluation is indexed in `docs/README.md`.

This is community discussion activity, not confirmation of present flooding or severity. Aggregation uses posts rather than votes/comments or semantic place-alias resolution. Production traffic/performance and matching backend/frontend deployment remain separate acceptance steps. No seven-day fallback is implemented.

## Research informing the bounded fallback

[Google Trends documentation](https://support.google.com/trends/answer/3076011?hl=en) exposes 24-hour, 48-hour and seven-day views and distinguishes active/ended trends. [Reddit's official sorting documentation](https://support.reddithelp.com/hc/en-us/articles/19695706914196-What-filters-and-sorts-are-available) distinguishes recent Hot activity from Top popularity. The automatic 24-to-48-hour policy is a LANES product decision; these sources do not prescribe it.
