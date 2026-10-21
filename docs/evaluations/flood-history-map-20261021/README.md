# Flood Event Records map consistency — local acceptance

Date: October 21, 2026, 04:29 AM Asia/Manila. Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Branch: `roi-branch`.

## Saved-zone camera-only follow-up — October 21, 2026, 09:08 PM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Official history → View zone on map now only frames the saved zone. It does not change selected-event state or add focus geometry to the blue overlay source. Existing report-evidence focus remains available.

TypeScript and focused lint pass. Four targeted Chromium checks pass (desktop and mobile, including 320 px): camera movement, identical base source/paint, empty focus source, style reload, report evidence geometry, report-to-zone transition, repeated button presses after manual panning, no overflow and no flood-data writes. Command: `npx playwright test tests/flood-history-map.spec.ts --grep "individual historical zone|style reload restores" --workers=1 --output=test-results/zone-camera-acceptance`. Initial diagnostics included map-startup timeouts under concurrent checks and a test baseline captured at overview zoom before detailed polygons loaded; the tests now wait for client-rendered Analytics and the records heading before interacting with maps, and for detailed polygons before comparing unchanged styling. A diagnostic readiness locator was narrowed to the metric because the chart legend repeats its text; the final four-check run passes. No backend, stored geometry, routing, dependency, commit or push changes.

## Loading performance follow-up — October 21, 2026, 05:20 PM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). The frontend proxy 500 was reproduced while port 3000 listened and port 8000 refused connections. The existing backend was started using the normal encrypted `.env`, without changing environment files or ports. An unauthenticated proxy check then returned the expected 401, confirming connectivity without bypassing staff authorization.

Separate in-process HTTP verification used a read-only database transaction and an isolated test dependency override, without application lifespan jobs or real authentication tokens. Local measurements: the old three-event read used 45 SQL statements / 3.65 s; the new `summary=true` read returned all 56 saved events in seven statements / 1.31 s; the 20-card page used eight statements / 0.51 s. A legacy three-event response still returns HTTP 200, now with 11 statements / 0.73 s. These measurements are illustrative and do not guarantee latency on other databases.

Final compatibility check: the exact original `/api/v1/admin/flood-events/history?status_filter=all&limit=250` URL also returns HTTP 200 with all 56 saved events, using 53 SQL statements / 6.34 s for its full legacy evidence payload. No INSERT/UPDATE/DELETE statements occur. The interface uses the faster summary projection instead.

`flood_history_records` batches event counts, locations and zone/report reads. Map/cards opt into summaries so browsing skips contributor/media/user/news property reads; full inspection and legacy array clients retain their contracts. Fresh queries are reused for 30 seconds and obsolete filter reads are cancelled. Rendering, filtering, pagination and heatmap styling are unchanged.

Verification: **29 targeted backend checks pass**, including a native HTTP query-count test with 1 versus 25 events, approved/deleted evidence counts, unchanged metrics, summary geometry, paged responses, authorization, retryable database errors and read-only browsing. Existing migrations run only on an owned empty local database, removed afterward. **Four existing lifecycle-service checks pass**. TypeScript and focused lint pass. **17 desktop/mobile browser checks pass**, with one desktop skip for a mobile-only test; coverage includes 320 px, summary requests, shared pagination, off-page map focus, detail handoffs, filters, errors/retry and exports. Command: `npx playwright test tests/flood-history.spec.ts tests/flood-history-map.spec.ts --workers=1 --output=test-results/flood-history-speed`.

## Delivered behavior

Equal desktop map/list widths after the gutter; unchanged mobile List default and Map switch. Historical polygons draw without selection, frame all displayed footprints initially/on filter changes, and use Needs Review's shared borderless translucent severity fill. No road core is invented. Individual zone/report focus remains separate. Public/admin/history share one heatmap renderer with the original colors and zoom 13–15 fade; polygons appear from 14 and heatmap disappears at 15.

The card list now pages through the same bounded history set using shared `Pagination`, with a maximum of 20 events per page. Full filtered map coverage is independent of the card page. See the pagination follow-up below; heatmap styling remains unchanged.

History's existing staff endpoint adds typed GeoJSON `heatmap_features` per event. Backend geometry conversion emits one point on each valid saved polygon, using event peak severity weights 1/2/3/5. Visible events supply both polygons and heatmap; no public report feed is substituted. Missing/invalid footprints remain inspectable records. There are no lifecycle, geometry, routing, schema migration or dependency changes.

## Verification

- **72 backend checks pass:** 71 portable history/authorization/queue/review checks and one native PostGIS history check. Polygon holes, multipart handling, invalid/missing/nonpolygon/out-of-range geometry, shared weights and record serialization are covered. Native acceptance applies the existing migrations to head in an owned disposable local database, verifies filtered records/points and absence of writes, then removes the database. No shared database is migrated.
- TypeScript and focused lint pass for history code, shared heatmap hook and browser helpers. ESLint comparison against HEAD: LiveMap 12 baseline/11 current errors, MapCanvas 11/9, pending-report hook 7/7 and map styling 5/5; no new error signatures. Existing unrelated diagnostics remain; full-project lint is not clean.
- **23 distinct browser checks pass**, with one desktop mobile-only skip. A stable combined run passes 21 checks across history-map, existing flood-history controls, public/admin shared heatmap and selected Needs Review/Active Zone regression; a separate two-check run verifies individual zone and supporting-report map focus on desktop/mobile. Coverage includes equal widths, initial bounds, filtered data, zoom 14/15 rendered layers, selected details, style recovery and visible failures, mobile/320 px switching, empty/unmapped records and heatmap closure. Desktop and mobile/320 px screenshots were inspected using mocked base-map/provider data. Output directories: ignored `frontend/test-results/history-map-acceptance/` and `history-map-individual-handoffs/`.

## Card pagination follow-up — October 21, 2026, 04:50 PM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). The existing history endpoint supports opt-in `page`, `page_size` (1–20) and `focus_event_id`, preserving its array response without `page`. `multiple_places` moves the existing recurrence criterion to SQL before paging/limiting. Both map and list retain the 250-record ceiling and stable verified-time/ID ordering; no endpoint, stored data, migration or dependency is added.

- **25 portable checks pass**, covering geometry/weights, authorization (including paginated reads) and paging validation. Two native-only checks skip in this portable invocation and pass in the separate native run.
- **Two native PostGIS checks pass**, covering 20-card bounds, stable ties, final/clamped/focused pages, filters and multiple-place criteria, empty results, retained legacy reads, limit handling and read-only geometry/lifecycle preservation. Existing migrations apply to head only in an owned empty test database, removed afterward.
- **17 desktop/mobile Chromium browser checks pass**, with one desktop skip for the mobile-only Map/List interaction. Tests exercise 20/20/5 card pages, disabled last-page controls, filter reset, map feature/camera preservation, actual off-page map clicks, detail return, failed-page retry, 320 px layout and existing map/style/detail regressions. Output: ignored `frontend/test-results/flood-history-pagination/`.
- TypeScript and focused lint pass. An initial fixture generic-inference diagnostic for null geometry was corrected. A separate 250-record/13-page layout check passes at 1920, 1024, 768 and 320 px; actual shared footer screenshots at 1024 and 320 px were inspected. Output: ignored `frontend/test-results/history-pagination-widths/`.

The shared pagination component itself, heatmap rendering/colors, routing, exports, database models and existing uncommitted work are preserved. No commit or push.

## Limits and preservation

Browser API/provider fixtures are fictional and produce no flood-data writes. Auth validation POSTs are session reads and excluded from the write assertion. First diagnostic runs corrected a test helper selecting Spatial Operations' persistent background canvas, a zoom test centered between widely separated fixtures, and a missing Analytics stats fixture. New suites explicitly select Chromium, matching the existing spatial-review/history suites; earlier device-default browser diagnostics are not counted as Chromium acceptance. Passing final runs are recorded separately from diagnostic failures. This is not physical-device or live-provider/deployment acceptance.

The pre-existing uncommitted Active Zone group-card map-focus changes are retained. No commit, push, production deployment, new model, migration or package is included.

## Reproduction commands

From `backend/` with the repository virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_flood_history_heatmap.py tests/test_flood_history_authorization.py tests/test_zone_queue.py tests/test_spatial_review_grouping.py tests/test_spatial_review.py -q
# Use an empty owned disposable local lanes_settings_test_* database for the native fixture.
.\.venv\Scripts\python.exe -m pytest tests/test_flood_history_map_postgres.py -q
```

From `frontend/`, with the development frontend on port 3000 and fictional Playwright API fixtures:

```powershell
npx playwright test tests/flood-history-map.spec.ts tests/shared-heatmap.spec.ts tests/flood-history.spec.ts tests/spatial-review.spec.ts --grep "initial footprints|style reload restores|320 px switching|Analytics retains shared|Flood History|mixed queue keeps|related reports open|active zones share report" --workers=1
npx playwright test tests/flood-history-map.spec.ts --grep "individual historical zone" --workers=1
npx tsc --noEmit --incremental false
```

The owned temporary development server is stopped after acceptance so port 3000 is available for the existing VS Code tasks.
