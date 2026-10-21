# Spatial Operations and Flood History — performance plan

> **Last Updated:** October 21, 2026, 08:43 PM Asia/Manila
> **Status:** Approved and implemented locally; scale/visual acceptance remains qualified by the measurements below.
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Branch:** `roi-branch`; preserve all existing uncommitted work. No commit or push included.

## 1. Scope and confirmed choices

Implementation and verification are recorded in the [scale acceptance report](../evaluations/spatial-history-scale-20261021/README.md). The implementation preserves legacy reads while moving staff browsing to independent paged cards, viewport chunks and paged inspection collections. The 10,000-zone dense grouping benchmark still exceeds the provisional warm p95 target; local service timings do not establish end-to-end production latency acceptance.

This plan covers both **Spatial Operations → Active Zones** (Active Only, All History, group inspection and operational map reads) and **Flood History & Analytics → Flood Events** (cards, map and individual inspection). Analytics aggregation and exports remain regression boundaries and receive bounded SQL aggregation where needed for the scale checks.

The user confirmed that Flood Events must cover **all matching history**, replacing the interface's 250-record ceiling. This means complete server-side filtering/counts and access to every matching record, not downloading every record or polygon on initial load. Keep 20 cards per page and the existing shared `Pagination` presentation.

Keep Active Zones' complete, unambiguous matching road/city requirement, original-geometry distance ≤50 m, complete-link membership, deterministic lowest-ID anchors/order, cross-source provenance, active/expiry policy and no creation-time cutoff. Missing/conflicting metadata or unavailable original geometry stays separate. Group before filtering/pagination, and preserve full saved-polygon camera bounds. **Needs Review grouping and moderation remain unchanged.**

Preserve individual actions, contributors/evidence, map handoffs, selection/back navigation, mobile List default and 320 px usability. Keep historical saved polygons, severity-weighted concentration meaning, existing heatmap renderer/colors and zoom 13–15 fade. This initiative does not redesign heatmap colors or change stored geometry, routing or lifecycle.

## 2. Evidence and interpretation

Read-only backend HTTP measurements against the current remote database, excluding normal authorization and browser rendering overhead:

| Read | Data statements | Observed time |
|---|---:|---:|
| Needs Review, four items | 2 | 0.14–0.31 s |
| Active Zones cards, ten zones | 4 | 1.56–2.66 s |
| Active Zones map, ten zones | 36 | 1.97–5.52 s |
| Active group inspection, one member | 14 | 12.05 s, one observation |
| Historical map, 56 events | 7 | 0.49–0.70 s |
| Historical first 20-card page | 8 | 0.45–0.69 s |
| Historical analytics, 56 events | 4 | 0.23–0.37 s |
| Historical detail, one zone/report | 17 | 1.62 s |

Five linked news rows transfer approximately 1,430.9 KiB of extraction results plus 31.2 KiB of decision snapshots from PostgreSQL to the backend. The grouping read needs only a subset. A metadata query's client duration was 3,940.4 ms, while its `EXPLAIN ANALYZE` execution time was 0.416 ms. The plan measurement excludes network delivery and, by default, output conversion: the entire difference cannot be attributed to network latency alone.

Active grouping pair checks currently take about 0.1–0.2 ms with ten zones, but the implementation can approach quadratic comparisons as eligible data grows. The current frontend also requests grouping independently for the badge, cards and membership; Active Zones remounts when switching tabs. History browsing is already batched, but still obtains overlapping map/card projections and enumerates the bounded event-ID set before paging.

The frontend stopped listening on port 3000 during the last investigation, so live rendering costs were not measured. Frontend request/remount findings are code-confirmed; browser profiling remains an acceptance task.

## 3. Phase A — remove current unnecessary reads

1. Replace whole-document selection in `crud/zone_queue.py` with SQL JSON projections for the selected claim's canonical road/city/barangay and the exact public fields consumed by grouping, summaries and search. Preserve revision ordering, missing evidence and source classification. Do not transfer complete extraction results to select one claim in Python. Keep full evidence saved and available through inspection.
2. Consolidate batched zone response construction across operational map/member reads. Batch reports, surveys, reporter profile/role and news information; assemble response values explicitly so serialization does not call database-backed ORM properties. Preserve existing `/reports/active-zones` response fields for its other consumers.
3. Keep card/map summaries separate from contributor/media/evidence details. Bound collection reads to the displayed page or selected item. Avoid both per-row queries and a single join that multiplies reports, news and contributors into duplicate rows.
4. Share zone count/card query ownership and query-key definitions. Reuse queue counts when available. When the Active Zones panel is inactive and the badge still needs a refresh, use a lightweight authenticated eligible-zone count read; do not build groups just to count eligible zones.
5. Coordinate refreshes: one active visible observer per logical read, fresh cached data on tab return, mutation/SSE invalidation for affected keys, and no hidden-queue polling during inspection. Retain the 15-second visible Active Zones freshness requirement, expiry correctness and resume/reconnect recovery. `staleTime` alone does not disable interval polling.

**Gate:** Same response behavior and saved-example grouping, substantially smaller database result bytes, bounded SQL counts without per-zone growth, and no duplicate equivalent full queue requests.

## 4. Phase B — make grouping practical with thousands of zones

1. Partition reliable candidates by the existing normalized road/city pair; handle ineligible metadata as singletons immediately.
2. Use the installed Shapely 2.1.2 spatial index to narrow candidates by projected original geometry, followed by the exact ≤50 m distance check. Do not substitute center-point distance, outer avoidance polygons, approximate snapping or nearest-neighbor-only selection.
3. Preserve ascending-ID greedy assignment and complete-link checks against every relevant member. Sort candidate IDs explicitly; spatial index traversal order must not affect anchors or membership. Avoid constructing an all-pairs distance matrix or an unbounded pair cache.
4. Use the same implementation for cards and membership resolution. Keep grouping before filters/pages; do not independently group each page or viewport. Missing original geometry remains inspectable.
5. Compare the optimized results with the current implementation on randomized small datasets and adversarial overlap/chain cases. Benchmark dense same-road buckets separately: an index does not guarantee subquadratic behavior when nearly every geometry overlaps.

Cross-request backend caching is not required for the first implementation. First make uncached reads efficient and remove duplicate frontend work. If measured scale targets still require a group cache, add a separately reviewed bounded design covering expiry deadlines, configuration/zone/evidence changes, concurrent misses and multiple workers; an indefinite in-process cache is not acceptable.

### Operational map reads

- Add an authenticated `GET /admin/zones/map` read for the Spatial Operations map, with validated viewport bounds, a bounded chunk size and continuation cursor. Return lightweight eligible-zone features and global eligible bounds/counts; do not download every active zone and contributor just to draw the visible map.
- Preserve the existing inner road geometry, outer saved polygon styling, severity/depth and source labels. Fetch selected-zone evidence/details on inspection, including contributors and individual actions. Keep `/reports/active-zones` compatible for existing public consumers while applying the batched construction improvements there.
- Fetch all intersecting features through continuation reads without a dataset-wide truncation. Cancel obsolete viewport requests and keep selected-zone overlays separate. Grouping still considers all eligible zones before filters/pages and is never limited by the viewport.
- Resolve explicit map handoffs/zone IDs through an authorized detail/member read, then focus and load that viewport. Do not treat an ID absent from the current viewport source as a missing or inactive zone. Preserve inactive-history focus and existing camera bounds as well.
- Include dense/complex viewport cases in the same browser/response-byte acceptance gate as the historical map. A public-map redesign is outside this plan.

## 5. Phase C — complete historical browsing without a 250-record download

### Cards and counts

- Add an authenticated `GET /admin/flood-events/records` browsing read. Apply all existing history filters, including multiple-place filtering, in SQL before counts and paging.
- Return 20 lightweight card summaries plus exact `total`, `page`, `pages` and `page_size`. Card summaries include location summaries and zone/evidence/reporter counts; omit polygon and heatmap collections. Keep the existing shared pagination control.
- Order by `verified_at DESC, id DESC`. Resolve a map-selected event's containing page with an SQL rank/count operation, not by retrieving every matching ID into Python. An item outside the current filters must be explained rather than silently changing filters.
- Start with indexed SQL page-number pagination to preserve existing navigation. Benchmark deep pages explicitly; cursor navigation is a later option if measured offset costs require it, not an unannounced UI change.
- Preserve the existing bounded `/history` endpoint for legacy consumers. The new interface uses the complete browsing read and reports accurate full-result totals, including zero and unmapped results.

### Map

- Add an authenticated `GET /admin/flood-events/map` read with the same shared filter builder, validated viewport and zoom inputs. Return separate global matching counts/bounds and viewport display data. List paging never limits map coverage.
- Compute global bounds in PostgreSQL over valid matching footprints. Fit all matching mapped history initially and on filter changes; subsequent viewport requests preserve manual camera movement. Empty/unmapped records remain in the list and have explicit counts.
- At overview zooms, aggregate representative points from **all matching valid zones within the requested viewport**, independently of card pages, into a bounded, zoom-dependent display grid in PostgreSQL. Sum existing severity weights and retain represented-zone counts. Global matching counts/bounds remain separate from viewport counts. Aggregate display points must be based on real representative points; they do not describe flood boundaries or distinct-event frequency. Never silently limit the overview to the first 250 events or invent event/zone IDs for multi-record aggregates.
- Keep the shared heatmap renderer and existing colors/fade. Aggregation is a display approximation and needs before/after visual acceptance; it must not broaden the meaning to verified inundation extent. Include the number of represented zones in the map metadata/legend.
- At detailed zooms, fetch exact saved polygons intersecting the viewport in bounded, cursor-paginated chunks. Include every intersecting zone through continuation reads; abort obsolete requests and prevent old responses from replacing newer filter/viewport data. Never silently drop records when a chunk is full.
- Maintain the 14–15 heatmap/polygon overlap and selected event/zone/report overlays. A selected historical item resolves its complete exact geometry independently of current card or map pages.
- Bound response bytes and geometry work, not just the number of records. Do not simplify stored geometry. If pathological dense/complex views fail browser budgets, report that result and review a vector-tile/display-detail extension before claiming scale acceptance.

### Detail and Analytics

- Batch individual history inspection metrics, zones, reports and news reads. Preserve history tabs, contributor evidence and map handoffs.
- Exercise one event/zone with thousands of child records. Where child collections exceed a page, provide authenticated paginated collection reads and reuse shared pagination; no silent truncation or inaccessible evidence. Preserve legacy detail consumers and provide complete counts in the overview.
- Debounce text filters using the existing 300 ms pattern; apply selects/dates immediately and propagate cancellation signals. Cards load independently of map success, with separate errors/retry states.
- Mount the historical map when first needed; retain it while switching views within the workspace to avoid repeated initialization. Add an opt-out from offline routing-worker preload for history while preserving the routing maps' existing default.
- Keep distinct-event Analytics/count calculations in SQL aggregates over the full filtered history. Exports must continue covering their full matching set independently of card/map pages.

## 6. Verification and provisional performance targets

Use owned disposable PostGIS databases with existing migrations, never production test writes. Seed 1,000 and 10,000 zones/events and include multi-source evidence, large extraction JSON, repeated links to one extraction, overlapping and distant same-road geometries, chains, missing/conflicting evidence, expiry toggles, complex polygons, and a single event/zone with many children.

Record SQL statement counts, database result bytes, API bytes, query execution versus transfer/conversion, grouping comparisons/CPU/memory, and p50/p95 endpoint and browser times. Measure cold and warm cases, filtered/unfiltered reads, first/deep pages, map bounds/chunks and concurrent observers. Use production frontend builds for latency acceptance, with desktop and 320 px/mobile checks. Report infrastructure and network conditions; local development rebuild time is separate.

Provisional acceptance targets for the agreed benchmark environment:

| Measure | Proposed target |
|---|---|
| 20-card queue/history page and ordinary inspection | Warm p95 ≤1 s; cold p95 ≤2 s |
| Initial visible map data | p95 ≤2 s after viewport/filter selection |
| First usable cards in browser | p95 ≤2 s desktop; ≤3 s mobile |
| Query count | Bounded by read/page/chunk, not one query per item; budget each route and include auth separately |
| Unnecessary extraction transfer | No complete extraction documents in grouping/card SQL results |
| Coverage | Every matching historical event is reachable; map metadata/overview covers all matching valid zones |

Targets are proposed acceptance criteria, not measurements or latency guarantees. Tighten route-specific query/byte budgets after the scale baseline. Cold-cache and dense overlap failures must be disclosed; a cache-hit-only result does not pass.

Regression gates: Needs Review/moderation suites, exact Active Zones memberships/anchors/sorting, 50 m boundary, filtering without split groups, source labels, expiry/configuration changes, full-polygon bounds, shared styling/pagination, all operational and bulk actions, historical detail/map handoffs, public/admin maps, Analytics and exports. Browsing must perform no writes. Verify public/staff authorization and no cross-user cache leakage. Run relevant pytest/Playwright, TypeScript and focused lint.

## 7. Files and boundaries

Expected backend areas: `crud/zone_queue.py`, spatial grouping/zone queue services, explicit news/zone projection reads, history service/read schemas and thin staff route handlers. Expected frontend areas: `LiveMapPage`, `ActiveZonesPanel`, shared query definitions/API clients, Flood Event records/map/detail components and optional `BaseMap` preload configuration. Presentation stays in React; business rules, filtering/counts/grouping and map aggregation stay in FastAPI/PostGIS.

No SQLAlchemy model changes, migrations, new dependencies, Redis, infrastructure changes, commit or push are included. If a new index/schema change is actually needed, present it for the user's explicit approval before creating a migration. Preserve all existing uncommitted work. Implementation and outstanding acceptance gates are tracked in `docs/task_plan.md` and the linked scale report; delivered code does not imply that all latency targets passed.

## 8. Research supporting the approach

- [Microsoft: excessive fetching](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/extraneous-fetching/) and [many small I/O calls](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/chatty-io/).
- [SQLAlchemy: batched relationship loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html).
- [PostgreSQL: select JSON fields](https://www.postgresql.org/docs/current/functions-json.html), [EXPLAIN measurement caveats](https://www.postgresql.org/docs/current/using-explain.html) and [stable paging/offset costs](https://www.postgresql.org/docs/current/queries-limit.html).
- [Shapely 2.1.2: spatial candidate indexing and overlap limitations](https://shapely.readthedocs.io/en/2.1.2/strtree.html).
- [TanStack Query: freshness and independent interval polling](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults).
- [Amazon: cache expiration, coalescing and cache-outage tradeoffs](https://aws.amazon.com/builders-library/caching-challenges-and-strategies/).
- [Google SRE: latency distributions](https://sre.google/sre-book/monitoring-distributed-systems/) and [web startup work](https://web.dev/articles/reduce-javascript-payloads-with-code-splitting).
