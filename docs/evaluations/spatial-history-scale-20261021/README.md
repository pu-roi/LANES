# Spatial Operations and complete Flood Events browsing

> **Last Updated:** October 21, 2026, 08:43 PM Asia/Manila
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Branch:** `roi-branch`; local changes only, no commit or push.

## Implementation

- Grouping/card SQL projects only the selected news claim's location and public summary fields. Full extraction documents remain stored. Explicit eager serialization batches reports, surveys, profiles, roles and news instead of invoking lazy per-zone news properties.
- Active grouping partitions normalized road/city pairs, prunes candidates with the installed Shapely STRtree and retains exact original-geometry distance ≤50 m, complete-link assignment, ascending IDs, anchors, expiry, filters and full-polygon camera bounds. Binary geometry decoding and normalization reuse are bounded to one request. Identical immutable geometries and a bounding-box diagonal proof avoid quadratic pair checks for repeated/short geometries; other dense long geometries can still require many exact comparisons. Needs Review is unchanged.
- Staff cards use `/admin/flood-events/records`, exact SQL totals and stable 20-card pages across all matching history. Focus resolves its page by SQL preceding-row count. Cards omit polygon, heatmap and contributor collections and preview at most three locations; inspection exposes all locations.
- Staff maps use `/admin/zones/map` and `/admin/flood-events/map`. Global bounds/counts are separate from viewport reads. Exact polygons continue by ascending ID in chunks of at most 250 without truncating coverage. The overview aggregates all matching viewport representative points into at most 4,096 cells, summing severity weights and represented-zone counts without invented event identities. Existing colors, fade and operational inner/outer layers remain.
- Inspection overview and paged report/zone/timeline/location/contributor reads retain existing actions and full counts. Legacy endpoints and their limits remain available. Analytics aggregates the full filtered history in SQL; exports remain independent of browsing pages.
- Shared query definitions deduplicate equivalent zone detail/contributor reads. Active freshness is 15 s, history 30 s, hidden queues/maps stop polling, text filters debounce 300 ms, and obsolete requests receive abort signals. Cards are independent of map failures. Historical records/map bundles load when needed; initialized maps survive Analytics/Events and mobile Map/List switches, while hidden queries pause. History skips routing-worker preload. Exports use the latest visible text even during the debounce window.
- Stable feature IDs permit incremental MapLibre updates for appended chunks; viewport replacements and selection reordering replace the source to preserve draw order. Repeated debug logs were removed. This reduces redundant transfer to the map worker; the results below do not establish a dense-mobile latency improvement.

## Native scale measurements

Windows, Intel Core i5-1135G7 (8 logical processors), approximately 15.8 GiB RAM, Python 3.12 environment, local PostgreSQL/PostGIS. Fresh disposable databases named `lanes_settings_test_accept_*` receive existing migrations and are removed in `finally`. No production fixture writes. Bulk fixtures run `ANALYZE` before timing to give the planner normal table statistics. No backend response cache, Redis, new indexes, model changes or dependencies.

Dataset: 1,000 / 10,000 events, saved polygons, original road segments and linked reports. A deliberately dense same-road bucket groups all zones. Separate tests cover randomized/adversarial grouping, missing/conflicting evidence, chains, expiry, holes/multipart/invalid geometry, a multi-megabyte extraction and large paged evidence. These tests are not a representative city-wide distribution or exhaustive complex-geometry memory benchmark.

Service-call seconds, 20 repeated samples per warm operation (p95 is the 19th sorted sample). These include SQL and Python processing but exclude normal HTTP authorization, network JSON delivery and browser rendering. They are not end-to-end API SLOs. The browser suite began during the later run; the host was not otherwise isolated.

| Records | Read | Warm p50 | Warm p95 |
|---:|---|---:|---:|
| 1,000 | Historical 20-card deep page | 0.0181 | 0.0278 |
| 1,000 | Active grouped cards | 0.0994 | 0.1358 |
| 1,000 | First 250 historical polygons | 0.0376 | 0.0658 |
| 10,000 | Historical page 500 | 0.0273 | 0.0421 |
| 10,000 | Active grouped cards | 1.2829 | **1.6377** |
| 10,000 | First 250 historical polygons | 0.2254 | 0.3406 |

First service observations: 1,000 cards page 1/deep 0.0375/0.0260 s and grouping 0.1500 s; 10,000 cards page 1/deep 0.0385/0.0371 s and grouping 1.3899 s. These are single observations, not cold-cache p95. An earlier run under concurrent build/browser load produced grouping p95 7.7354 s (1,000) / 3.0090 s (10,000) and a redundant historical map query p95 26.1396 s (10,000). The redundant join was subsequently removed. Do not discard these load sensitivity findings or treat warm results as cold acceptance.

A later functional pass measured uncompressed Pydantic JSON sizes:

| Records | 20 history cards | 250 operational zones | 250 historical polygons | Dense aggregated overview |
|---:|---:|---:|---:|---:|
| 1,000 | 10,511 B | 160,670 B | 55,890 B | 266 B |
| 10,000 | 10,563 B | 161,388 B | 57,388 B | 269 B |

The card test enforces at most seven data statements independent of dataset size. Every matching zone is retrieved through continuation pages, every history record remains reachable, aggregation preserves total weights/represented counts, and observed browsing statements contain no INSERT/UPDATE/DELETE. The large extraction test verifies the selected claim ordinal and a grouping metadata representation under 10 KB; representation size is not PostgreSQL wire bytes.

A subsequent 19-test native run passed in 165.20 s, with concurrent host/browser activity. Its 10,000-record warm p50/p95 was cards 0.0312/0.0433 s, grouping 1.5156/1.7334 s and historical first chunk 0.2166/0.3288 s. The 1,000-record warm p50/p95 was cards 0.0403/0.1352 s, grouping 0.2560/0.7241 s and first chunk 0.0713/0.3901 s. First 1,000-record page/deep observations rose to 1.6213/2.8542 s under load; this variability prevents cold/concurrent acceptance.

Separate `tracemalloc`-instrumented grouping calls measured Python peak heap 2,567,861 B (1,000) / 26,950,658 B (10,000), with process CPU 1.0938/8.5781 s. Profiling adds substantial overhead; these CPU samples are not the uninstrumented latency distribution. Python heap excludes GEOS native allocations and database/browser memory.

## Saved-data read-only recheck

An in-process HTTP client used a saved staff identity and an explicitly read-only transaction against the existing database. Dependency overrides omit normal authentication cost. These are single observations, with no production fixture writes:

| Read | Data statements | Seconds | Uncompressed HTTP bytes |
|---|---:|---:|---:|
| Active count | 2 | 0.6746 | 12 |
| Active grouped cards | 4 | 0.2320 | 6,458 |
| Group containing zone 69 | 15 | 0.7740 | 3,368 |
| Historical 20-card page | 7 | 0.2625 | 19,300 |
| Global historical map summary | 3 | 0.1370 | 199 |

Saved zones 69 and 70 resolve to separate single-member groups; direct grouping took 0.3647 s. Geometry, stored activity and expiry values compare unchanged before/after the reads.

A final read-only operational viewport returns all ten saved zones, including user-report and news sources, in 0.3362 s / 26,392 uncompressed bytes. Its source projection explicitly casts report source to text before combining derived news/official/other labels; those labels are not database report-enum members. A native repeated-news fixture also checks this viewport path.

## Production browser stress

Real production Next.js 16.2.9 bundles and MapLibre run in bundled Chromium, desktop and the iPhone profile at 320 px. Fictional HTTP routes mirror bounded transport; timing includes fixture generation and browser/test transport, not a live database-backed end-to-end deployment. These are single observations, not p95. Before incremental updates, desktop 10,000-zone completion was 28.205 s; the dense mobile run timed out with 6,750 shapes observed.

After incremental updates, the broad run produced:

| Profile | Zones | First cards | First map | Complete viewport | JS heap at end |
|---|---:|---:|---:|---:|---:|
| Desktop | 1,000 | 1.850 s | 7.737 s | 24.883 s | 22,854,580 B |
| Desktop | 10,000 | 8.437 s | 12.957 s | 45.484 s | 30,038,448 B |
| 320 px mobile | 1,000 | 2.789 s | 9.137 s | 14.283 s | 30,261,308 B |
| 320 px mobile | 10,000 | — | — | **Failed 120 s continuation/render wait** | — |

The mobile timeout observed 6,000 shapes at its last successful sample. Its trace contains 35 map requests: continuation reads remain in progress rather than an API limit discarding the remainder. Some fulfilled fixture requests take 2–35 s under host/test/browser backpressure; this does not isolate a production database bottleneck. Do not raise the timeout or count this as a pass. Desktop 10,000-zone browser ScriptDuration/TaskDuration was 4.323/43.254 s; 1,000-zone desktop 1.537/15.256 s and mobile 1.467/15.027 s. These Chromium metrics include the inspected page and test activity, not just rendering.

The final lazy-bundle/retained-workspace changes pass the focused reruns below. Dense 10,000-zone mobile, cold/concurrent end-to-end p95 and visual approximation acceptance remain open regardless of ordinary interaction passes.

After lazy loading, single 1,000-zone observations improved to desktop cards/first-map/full-data 1.475/2.239/4.726 s and mobile 2.615/3.017/6.682 s. Desktop ScriptDuration/TaskDuration was 1.029/5.668 s (32,845,612 B JS heap), mobile 1.000/7.640 s (28,463,312 B heap). These are new observations, not a controlled attribution of improvement or p95 acceptance. A final isolated 10,000-zone mobile run still failed the same 120-second wait, reaching 9,500 observed shapes; the failing test and timeout remain intact.

## Verification and remaining gates

Final targeted portable run: **71 pass** (grouping/review/heatmap/authorization), including 1,000/10,000 identical long/short geometry cases; randomized grouping matches the previous complete-link implementation. Another portable regression run had 44 passes and one auditor configuration failure when launched without decrypting the existing environment; the failed check passes under the normal dotenvx environment. Together, 116 distinct portable checks pass across these runs.

**19 targeted native checks pass**, including full continuation coverage, paging beyond 250, SQL Analytics parity/exports, authorization, weights, no browsing writes and 1,000-report inspection. Two strengthened fixture reruns pass: repeated links to a 3 MB extraction still transfer only selected fields; severity/counts include report 1,000 although its collection preview has 20 entries. All owned databases were removed; one failed cleanup connection was retried successfully against the exact owned name.

The broader operational-settings native run recorded 39 passes, two failures and three setup errors. Local database connection timeouts/disconnects affected approval/fixtures. A scheduler assertion expects only processing/publication paused stages while the existing implementation returns five paused stages; that code/test is outside this change. These failures are disclosed rather than represented as a clean full native suite.

Production browser verification: the incremental-map run has **39 passes and one dense-mobile stress failure**. Shared pagination, 600-record reachability, filters, styles, map focus, details, contributor pages beyond 20, individual/bulk actions, source evidence, public/admin heatmaps and desktop/320 px layout pass. Earlier three history failures were corrected and pass in follow-up runs: missing collection fixtures, deferred-map request expectations and malformed-response guards. Eight focused Needs Review/Active Zone browser regressions also pass. Latest workspace-retention, lazy-start and visibility rerun receipts are recorded at completion.

The lazy/retention receipt run has 14 passes and two selector failures: retaining hidden Analytics DOM makes a substring `getByLabel("Barangay")` ambiguous. The selector now uses its exact accessible name, and all eight final workspace/filter/map checks pass. A final six-check production rerun also passes, including an explicit assertion that pagination stays in the viewport after paging. Both desktop and mobile retain their initialized canvas and manual camera. Pagination retains previous cards during requests to avoid collapsing the list and moving the controls out of view. Loading remains visible while map continuation is outstanding; the legend identifies global matching mapped counts separately from viewport display data.

Visual checks use fictional data and a neutral basemap: [desktop browsing](images/pagination-desktop.png), [320 px browsing](images/pagination-320px.png). The artifacts verify layout, not acceptance of concentration approximation or real geographic appearance.

Production builds (including TypeScript) and focused ESLint pass. Existing unrelated lint debt remains: `LiveMapPage` has 10 errors versus 12 at HEAD; `BaseMap` retains its eight existing `any` errors. No new errors are claimed resolved by suppressing rules. `git diff --check` passes with normal repository line-ending handling.

**Acceptance is not unconditional:** the 10,000-zone grouping warm p95 exceeds 1 s. Cold-cache and ordinary-inspection p95, real-network concurrent HTTP/browser p95, 1,000/10,000-zone operational-map browser budgets, complete PostgreSQL wire bytes and pathological geometry/native-memory budgets have not been established. Overview aggregation changes the approximation and still requires human visual acceptance. No production performance guarantee or heatmap redesign is claimed.

Local services were restored to frontend development mode on 3000 and backend reload mode on 8000. A non-PTY backend reload process exited after a file change during restoration, briefly producing proxy 500s. The backend was relaunched in a PTY using the existing environment; a timestamp-only reload preserved source contents and recovered both protected reads through port 3000. Unauthenticated probes return the expected 401, not a proxy failure. No environment or task configuration was changed by this implementation.

No schema/index migration is justified or performed by these results. Any further caching/infrastructure/index proposal requires a separate review under the approved plan.
