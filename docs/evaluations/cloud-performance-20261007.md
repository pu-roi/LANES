# Cloud and application performance — October 7, 2026

> **Last Updated:** October 08, 2026, 02:28 AM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Scope and evidence

The developer authorized the performance recommendations and deployment. Work
started from clean `roi-branch`, base `c361b61`. No SQLAlchemy model, Alembic
migration, library, authentication rule or flood eligibility rule was changed.
Cloud-backed read-only `alembic current` and local `alembic heads` both returned
`d7e4b9a21c60`. No migration write was needed.

The earlier audit found database CPU peaking around 15% and memory around 41%
over 24 hours, with resource headroom in API/frontend services. API startup
metrics recorded approximately 18–21-second starts; ordinary active-zone reads
had a 60-ms median but outliers above 20 seconds. SSE request durations near
300 seconds are open stream lifetimes, not ordinary endpoint response latency.
The separately scheduled 512-MiB discovery job explicitly exhausted memory in
two October 6 executions. These are different failure modes.

## Implemented changes

- Cloud Run `lanes-api`: service-level minimum instances **1**, keeping the
  existing 1 CPU/1 GiB, concurrency and maximum-instance settings.
- Cloud Run `lanes-news-discovery`: **1 GiB**, retaining 1 CPU, existing secrets,
  schedule and `--discover --pipeline --limit 50` arguments. No manual live
  discovery/publication was triggered for this performance verification.
- `cloudbuild.yaml` records those settings for subsequent deployments.
- Routing moves synchronous database/Valhalla waits to worker threads. Provider
  search passes overlap with a limit of two per route request; repeated empty
  exclusions are omitted. Gathered results retain stable ordering. All in-flight
  passes finish before provider fallback. Existing safety evaluation still
  rejects blocked candidates and governs the same fastest/shortest alternatives.
- Retention creates/uses/closes its database session inside a worker thread so
  the startup purge cannot block SSE and ordinary API requests.
- Live flood sync sends full snapshots only on actual changes, with small
  keepalives otherwise. Failed initial reads do not falsely replace offline
  flood data with an empty list. The client also skips duplicate snapshots and
  recovers missed changes on reconnect, with user-visible sync failures.
- Public/staff map zone queries retain a **60-second** polling fallback and
  **15-second** stale window. SSE changes still invalidate immediately. The
  commuter map pauses polling while hidden; news alerts retain their existing
  **30-second** server-status polling independently of zone snapshots.
- Initial Home/Feed visits defer map initialization; once opened, map context
  and navigation listeners persist across commuter pages. Analytics/save-place
  panels load when opened. Feed navigation also carries coordinates in the URL
  so a first deferred map load cannot lose its target to a short event timer.
- Production PWA disables automatic full-page reload on network reconnect.
  React Query/SSE refresh data while keeping open panels and route inputs.

## Verification and rollout

- **32 focused backend tests passed**: routing, flood policy, retention and sync.
  Added checks cover overlapping provider calls with a responsive API loop,
  bounded concurrency, fallback after in-flight calls, duplicate exclusions,
  unchanged snapshots, genuine clearance and unavailable initial reads.
- Frontend TypeScript, targeted providers/live-sync/tests lint and production
  builds passed. **14 distinct browser regressions passed** across final runs:
  public news alerts, news-zone geometry/details/reconnect and map performance,
  each on desktop and mobile Chromium. The mobile project uses an iPhone-size
  viewport, not a physical phone. Desktop/mobile detail screenshots were reviewed.
- Cloud Build `63c0f391-25f2-4967-80ac-bf62d39686ce` succeeded, including the
  Docker build's checked spatial-asset verification. Image:
  `gcr.io/lanes-project-508809/github.com/pu-roi/lanes:perf-c361b61-20261007`,
  digest `sha256:904f740c59fcc51e7c88d3b1fa356a44f294ba9a14894c3c158cd53e7ea1833c`.
- API revision `lanes-api-00055-laz` passed preview health (database connected),
  three Valhalla route requests (HTTP 200, no fallback), and a real SSE stream
  (`init`, then `keepalive`). It was promoted to **100% traffic**; the temporary
  preview tag was removed. The discovery job uses the matching image and 1 GiB.
- Firebase App Hosting build/rollout `build-2026-10-06-002` reached **READY /
  SUCCEEDED**. Revision `lanes-frontend-build-2026-10-06-002` receives **100%
  traffic**. Public `https://navlanes.live/feed` and subsequent Map navigation
  passed on fresh desktop/mobile Chromium contexts: HTTP 200, no map canvas or
  zone fetch on initial Feed, rendered map with HTTP 200 zone data, one initial
  zone fetch and no extra fetch over an 18-second unchanged-SSE window, no
  horizontal overflow or page errors, and page state preserved across offline /
  online reconnect. The expected reconnect refresh fetched zones again.
- Change-scope security review preserved endpoint/session contracts and flood
  policy; no secret, dependency or schema change. `git diff --check` passed.
  The eight core documentation records were audited: dependency/database,
  flagship-feature and architecture-decision records need no new entry for these
  routine performance fixes; progress, plan, system behavior and bug log align.
- Same-coordinate route samples before this code rollout were **3.231, 0.149,
  0.131 seconds**; preview samples were **0.276, 0.115, 0.102 seconds**. These
  low-traffic samples differ in warm-up state and are not a controlled speedup
  benchmark. Tests establish concurrency and reduced redundant work; they do
  not establish throughput under production peak load.

## Second pass: shared polling and responsive weather handlers

The developer requested another investigation, internet research and further
implementation. The deployed first pass retained the expected deferred Feed map,
changed-snapshot behavior and reconnect preservation. Between 17:42 and 17:59 UTC,
the 13 logged ordinary API requests all returned HTTP 200, and the error query
returned no API error entries. Active-zone requests took 13–16 ms. Four initial
Feed-page requests clustered around 1.27–1.31 seconds, while later weather reads
took 13 ms. This small sample includes our smoke traffic and is not a peak-load
benchmark. Code inspection still found a synchronous weather provider executing
on the ASGI event loop and a separate database poll for every sync connection.

Research and selected changes:

- [FastAPI synchronous-provider guidance](https://fastapi.tiangolo.com/async/)
  supports regular `def` handlers when a provider exposes blocking I/O. Current
  and forecast endpoints now run through FastAPI's thread pool. The asynchronous
  AI insights endpoint is unchanged. A simulated blocked provider test proves
  an unrelated ASGI probe remains responsive for both weather endpoints.
- `services/flood_sync_service.py` shares one authoritative database read and
  serialization per 15-second polling cycle **per API worker**, rather than per
  client. Stable row/key ordering prevents spurious changes. It preserves the
  public init/update/keepalive contract, failed-read protection and the same
  periodic observation of job/other-instance writes. Subscriber capacity is
  reserved before response creation; a queue holds only the latest result,
  respecting [Python's bounded asyncio queue behavior](https://docs.python.org/3/library/asyncio-queue.html).
  Disconnect/idle/shutdown release subscriptions, discard stale cached state
  and stop polling when nobody listens. This cache is not used by navigation
  safety queries, which continue to read authoritative active zones.
- `BaseMap` warms the offline routing worker **after the map renders**, using
  idle time with a two-second timeout; browsers without idle scheduling use a
  500-ms timer. Direct offline route requests still initialize the worker on
  demand. [MDN's idle callback guidance](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestIdleCallback)
  supports deferring lower-priority work and supplying a timeout. Existing
  first-render fallback/style recovery and offline storage contracts remain.
- [TanStack defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)
  and [MapLibre optimization guidance](https://maplibre.org/maplibre-gl-js/docs/guides/large-data/)
  were reviewed. Existing stale windows, structural sharing, bounded polling
  and URL-backed boundary sources already match relevant guidance. No blanket
  cache extension or flood-geometry simplification was applied.
- [Cloud Run concurrency guidance](https://docs.cloud.google.com/run/docs/about-concurrency)
  describes shared instance resources and tradeoffs. This pass keeps existing
  CPU/RAM/concurrency/min/max policies: there is no controlled peak-load evidence
  supporting another specification increase or a concurrency retuning.

**Verification:** 37 focused backend tests passed, including 100 subscribers
sharing one read per cycle, stable row ordering, late subscription, capacity,
slow-client clearance, database failure/recovery, session closure, idle restart,
shutdown across event loops and nonblocking weather calls. These include the
first pass's routing/flood/retention/snapshot checks and are not added to its 32.
All **16 desktop/mobile Chromium browser tests passed** in one production-build
run; the new test verifies the offline wrapper remains unfetched until idle work
runs after map rendering. Frontend build/TypeScript and scoped test/hook lint
passed. No new dependency, SQLAlchemy model, migration or authentication change.

Second-pass rollout completed:

- Cloud Build `760f777b-485e-49bc-a8c0-cf3ec516be6e` succeeded. Image
  `gcr.io/lanes-project-508809/github.com/pu-roi/lanes:perf2-c361b61-20261007`,
  digest `sha256:f0f8b56dda780670f65c4607567f698061567774bf8353b82ed4730a674dda94`.
- Preview API revision `lanes-api-00057-cuf` passed connected-database health,
  real current/forecast responses, active-zone HTTP 200, Valhalla route HTTP 200
  without fallback, and three simultaneous sync streams receiving `init` then
  unchanged keepalives. It now receives **100% traffic**; the temporary preview
  tag was removed. Discovery uses the matching image with its existing 1 GiB,
  arguments and schedule. No discovery execution/publication was triggered.
- Firebase build/rollout `build-2026-10-06-003` reached **READY / SUCCEEDED**;
  `lanes-frontend-build-2026-10-06-003` receives **100% traffic**. Public fresh
  desktop/mobile Chromium checks passed: Feed HTTP 200 without hidden map/zone
  initialization, rendered Map with HTTP 200 zone reads, no extra zone read over
  18 seconds of unchanged sync, no horizontal overflow/page errors, and preserved
  page state with the expected zone refresh after offline/online reconnect.
- Public API health reports database connected; the new revision's error/5xx
  log query returned no entries at 2:04 AM. The verification window is short.
- Final diff checks pass. No dependency/schema/Firebase deployment-preference
  change; source remains uncommitted on `roi-branch`. The eight core records
  were re-audited, with progress/plan/system/bug-log updated; no new flagship
  capability, architectural pivot or database definition needs an entry.

To undo only this second pass, return API traffic to `lanes-api-00055-laz` and
select App Hosting build `build-2026-10-06-002`. If reverting the matching job
image, use the first-pass `perf-c361b61-20261007` image while retaining 1 GiB.
The next normal news schedule is **3:00 AM Asia/Manila** (every three hours);
its memory outcome remains unverified. A sustained load benchmark and the
developer's slowest real-device interaction are still needed before additional
capacity/concurrency tuning, geometry tiling or further client work is justified.

## Senior-planner pre-push checkpoint

At the developer's explicit request, all eight authoritative records were
reviewed before committing both performance passes to `roi-branch`. Progress,
task plan, system behavior and BUG-115/BUG-116 agree with the deployed releases
and the existing **37 backend / 16 desktop-mobile browser** verification. The
feature reference updates existing routing/signaling/worker sections without
adding a new flagship feature. The stack audit records existing dependencies and
resource policy; the database record now distinguishes the current deployed head
from earlier pending-upgrade checkpoints. Architecture decisions are unchanged:
these changes implement existing service/feature boundaries.

The audit corrected stale current-reference descriptions: public routing never
honors the legacy flood bypass, Open-Meteo is the weather provider, shared sync
polling is per worker, and matching news/API/job/frontend runtime packaging is
already deployed. Historical implementation/test checkpoints remain preserved.
Dependencies, lockfiles, models and migration definitions have no diff. A fresh
read-only cloud `alembic current` and local `alembic heads` both return
`d7e4b9a21c60 (head)`; no migration write is required. Documentation-only changes
do not require repeating the already passed code/browser checks.

The developer authorizes staging all reviewed changes, a Conventional Commit
and a normal push to `origin/roi-branch`. Git completion is verified and reported
after this checkpoint; earlier uncommitted-source statements describe deployment
snapshots, not a new release gate. Next scheduled job memory, real-current-article
acceptance, sustained load and physical-device behavior remain open.

## Limits and operational follow-up

Minimum instances and job memory can increase billing. Database, frontend and
Valhalla resource sizes were not increased. Physical phone/WebView testing,
sustained load, next scheduled news-run memory usage and real-article publication
acceptance are separate follow-up checks. A successful build/configuration does
not prove that the next news run stays below 1 GiB or that new article claims
qualify for publication. Source changes remain uncommitted until a requested
commit/push; deployment uses the tested local source snapshot.

Rollback: route API traffic to the prior revision `lanes-api-00051-9sd`; lower
service minimum with `gcloud run services update lanes-api --region=asia-east1
--min=0` only if the warm-instance policy is intentionally reversed. Returning
the discovery job to 512 MiB would reintroduce the observed memory-limit risk.
Frontend rollback: select prior App Hosting build `build-2026-10-06-001`
(`lanes-frontend-build-2026-10-06-001`) through the existing App Hosting rollout
controls. Keep the API/job configuration rollback separate from application code.


## October 8 WebGL recovery

The reported exception originates in MapLibre's graphics-context construction, not a MapTiler HTTP failure. Local installed `maplibre-gl` 5.24.0 throws when canvas context creation is denied. A map-style fallback still needs WebGL. Existing BaseMap cleanup removed live maps, but immediate mount effects allocated an extra context during development Strict Mode; this is a contributing allocation pattern, not proof of why the browser blocked the page.

BaseMap now defers creation to one cancellable animation frame, catches constructor failure and clears partial DOM, provides Map unavailable/Retry map with no automatic graphics retry loop, and pauses style timers during live context loss. It waits for an actual restored render before clearing the loss message. Disposal cancels compass/load/resize timers and prevents late map calls. Surrounding report forms remain mounted. No dependency/model/migration/API change or production release.

Four Playwright recovery checks pass across desktop Chromium and iPhone-sized mobile Chromium. Browser instrumentation reproduces the exact creation-error status and verifies one initial canvas allocation under development Strict Mode, failed and successful retries, cleared debris, no uncaught page errors, and actual WEBGL_lose_context loss/restoration. Two ordinary flood-zone popup checks pass on both viewports. TypeScript/diff whitespace checks pass; BaseMap retains its HEAD lint baseline of eight errors/seven warnings, and the new tests pass scoped lint. Screenshots of both recovery states were inspected. The tests use installed Chrome with software WebGL; physical GPU/driver block clearance cannot be guaranteed by application code. No push/deployment.

```powershell
$env:PLAYWRIGHT_CHROME_PATH='C:\Program Files\Google\Chrome\Application\chrome.exe'
npx playwright test tests/webgl-recovery.spec.ts --workers=1
npx playwright test tests/spatial-review.spec.ts -g 'public zone popup quick action' --workers=1
```

Evidence references: [MapLibre context events](https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/MapEventType/), [context attributes](https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/MapOptions/), and the installed library's `src/ui/map.ts` constructor/context-loss/remove lifecycle. [@roicambe](https://github.com/roicambe) (Roi Cambe)
