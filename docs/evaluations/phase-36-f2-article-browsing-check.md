# Phase 36: F2 article browsing verification

> **Last Updated:** October 02, 2026, 8:00 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

F2 is implemented and verified locally. `/admin/news` opens Articles, reads saved evidence through authenticated FastAPI endpoints, and opens Source / Extracted Facts / Processing History. Overview, Results, Sources, staff decisions and public alerts remain later stages. With explicit developer approval, applied the existing local extraction migration. No production deployment, model/migration definition change, dependency addition or public-state write was performed.

## Read contracts and provenance

- `GET /api/v1/admin/news/articles`: server-owned literal title/excerpt search, publisher/body/processing filters, stable ordering and bounded pagination (12 by default, maximum 50). Lists all saved article review states, not only pending evidence. Cards omit full bodies and report the newest recorded run's status.
- `GET /api/v1/admin/news/articles/{id}`: current article plus the newest twenty saved runs, total history count and their immutable captured inputs. Selecting an older run displays that run's own source text/publication date, not the current article body. The read does not recompute extraction.
- Both endpoints enforce existing staff dependencies, return 404 for missing articles and visible 503 storage errors without private connection details. Unknown observation times, retrieval failures, missing bodies, empty results and failed runs remain explicit.

## Automated verification

The focused backend regression run passes **33 tests** across `test_news_browsing.py`, `test_news_saved_extraction.py` and `test_news_processing.py`. New cases verify 401/403 access, literal wildcard search, deterministic pagination, all saved review states, latest-run filtering, retained bodies with retrieval errors, immutable input linkage, bounded twenty-run history, sanitized storage errors and zero writes during reads.

Article Playwright checks pass on desktop Chromium and mobile Chromium. They cover all detail tabs, switching current/older captures, missing observation times, unresolved placement, no-claims/failed/missing-body states, list/detail retry, preserving server filters/page/scroll/focus after closing, returning across page tabs, Escape and keyboard focus containment. Narrow 320px and landscape 844px layouts keep the dialog and close controls within the viewport. Screenshots were visually inspected. New feature/test ESLint and full TypeScript checks pass. Existing AdminLayout lint errors remain documented in BUG-080.

## Real publisher evidence

Used [Philstar's September 9 flood list](https://www.philstar.com/nation/2026/09/09/2555106/list-flooded-metro-manila-areas-september-9), visibly published **September 9, 2026, 5:03 PM Philippine time**. Its actual body was fetched with the existing approved-publisher service, saved in a separate verification SQLite database, captured/enqueued through the existing worker and processed in rules-only mode. One completed run contains **28 candidate claims**. Claim counts include incidental mentions and are not validated flood-site or zone counts.

The new browsing service exported the exact persisted list/detail responses. Ten Playwright article checks rendered these responses and checked the actual captured body, publication time and stored extraction on both screen sizes, with controlled API/session fixtures. Subsequently saved the same actual capture to LANES local PostgreSQL as article **#3**, captured input **#1**, completed extraction run **#1**. The existing article #2 was retained; the local article count increased from one to two. The earlier AMP-path diagnostic returned 29 claims from a different capture; no equivalence or accuracy claim is made between those captures.

Two additional live browser checks used a short-lived JWT for an existing active local staff account, the running Next.js frontend and actual FastAPI/PostgreSQL reads, without mocked news responses. Desktop 1440×900 and mobile 390×844 received HTTP 200 from both article endpoints and verified the saved body, September 9 publication time, 28 claims, processing history, Escape dismissal and opener focus. Both recorded zero news mutations and zero page errors; their screenshots were visually inspected. The verification token was temporary and was not committed. The verification backend runs with lifespan jobs disabled, avoiding startup seeding and retention cleanup during this check.

The article is historical and outside the seven-day discovery window. It is not a current flood alert. The six configured feeds parsed successfully during discovery but produced zero eligible candidates. Fresh automatic collection acceptance remains open. This manually selected historical capture has no fabricated feed provenance. The bounded worker only processed article #3; it does not invoke public report/event/zone writers or routing activation.

For the optional browser replay, set `NEWS_ARTICLE_PAGE_FIXTURE` and `NEWS_ARTICLE_DETAIL_FIXTURE` to the exported JSON response files, then run `npx playwright test tests/news-articles.spec.ts --workers=1`. `PLAYWRIGHT_CHROME_PATH` can select an installed Chromium executable. These local artifacts and article bodies are outside the repository and are not committed.

## Local runtime recovery and remaining rollout

Docker initially failed on inaccessible runtime socket reparse points. After the developer requested another attempt, preserved/recreated both its runtime and Secrets Engine socket directories. The engine and existing PostgreSQL/Valhalla containers now start; PostgreSQL queries succeed and database contents are retained. BUG-081 is resolved. This matches the reported [Docker parent-directory workaround](https://github.com/docker/desktop-feedback/issues/554).

The local database initially remained at `a83c1d4e7b92` and lacked `news_article_versions` and `news_extraction_runs`. The developer explicitly approved applying existing migration `f29b6c8d104e`; `alembic upgrade head` succeeded and the database now reports that revision. Live PostgreSQL-backed F2 article browsing passes on both screen sizes. Production already has the extraction migration but must receive the two new read endpoints before a deployed frontend can use them. Production rollout and F3 Results remain open.
