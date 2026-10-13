# Community feed filtering acceptance — October 11, 2026

Author: Jace H. Bellen (repository author list; Git author `Jace`, branch `jace-branch`), with Codex. GitHub handle is not recorded in the inspected Git configuration. Local acceptance is complete and branch publication was requested; no deployment is claimed. See the [combined publication audit](jace-moderation-feed-publication-20261011.md).

## Behavior and API contract

**October 14 correction:** The approval-only visibility rule recorded below was a regression against immediate community sharing. Explicitly shared pending reports now appear publicly with Awaiting review; official map zones retain their approval workflow. Rejected/private/archived and hidden/deleted content remains excluded. See the [repair and current verification](../others/bug-log.md#resolved-locally-flood-report-community-sharing-waited-for-map-approval). The October 11 checks below remain historical results.

The existing `GET /api/v1/feed` filters the complete eligible dataset before ordering, counting and pagination. Standalone public posts remain available. Linked reports must be approved, explicitly public and not archived; hidden/deleted posts are excluded from the Community feed. My Posts and owned detail access retain the author's authorized unpublished access. No report creation, approval, rejection or event lifecycle writes were changed.

| Query | Values and default |
| --- | --- |
| `tab` | `recent` (default), `nearby` |
| `sort` | `newest` (default), `oldest`; publication `created_at`, then ID in the same direction |
| `date_range` | `all` (default), `today`, `24h`, `3d`, `7d`; Today starts at UTC midnight, others are rolling windows |
| `flood_status` | `all` (default), `active`, `resolved` |
| `severity` | Omitted by default; existing `low`, `medium`, `high`, `extreme` report classifications |
| `radius` | Omitted: existing automatic 5-to-15 km Nearby discovery. Explicit positive radius up to 15 km is strict; UI offers 1, 3, 5 and 10 km |
| `lat`, `lng` | Paired, validated coordinates; existing GPS/profile/saved-place reference and PostGIS geography calculations |
| `skip`, `limit` | Existing offset pagination with validation; UI pages contain 20 posts |
| `time_window_hours` | Optional legacy rolling-hour constraint, 1–8760; no automatic fallback outside its window |

Active Floods reuse the public map's zone predicate, including configured expiry and simulation-clock rules. Resolved Reports require the existing ended event status and no currently active linked zone. Expiry alone is not asserted as proof of resolved flood conditions. Restoring an ended event's zone can leave the event flag ended in the existing workflow; current map eligibility wins so Active and Resolved results cannot overlap.

Filters, tab and page are represented in the URL, and all filters participate in the user-scoped query cache key. Changing a filter or tab resets pagination while preserving the other selected filters. Hard refresh, minute polling and existing SSE invalidation preserve the selected query. Vote rollback targets its original cache, even if the user changes filters before the request finishes. Empty combinations offer Reset Filters; failed requests remain visible. The shared filter panel supports desktop and mobile, and pagination respects the existing bottom-navigation/safe-area variable.

No SQLAlchemy models, migrations, dependencies or approval workflows changed. Optional source/passability/verification/location-text filters were deferred: the core request is supported without inventing classifications or expanding unrelated workflows. Existing Local Updates/sidebar news remain independent of Community post filters.

## Validation

- Backend: **51 checks passed** across filter, ordering/homepage, feed interaction, notification and profile privacy suites. New PostGIS fixtures use an outer rollback transaction against a local database; no test rows are retained.
- Browser: **30 checks passed** on desktop/mobile across the new filter suite and existing homepage/feed ordering regressions. Scenarios cover all date options, oldest/newest ordering, combinations, paging, refresh, votes, reset, radius, missing location and errors.
- TypeScript and focused filter/API/test lint pass. FeedPage retains the same **six errors and four warnings** as its Git baseline, with the same lint-rule sequence; no blanket lint success is claimed.
- Desktop/mobile filter-panel screenshots were inspected for readable controls and viewport fit. Browser API responses are mocked; backend tests exercise real PostGIS. Live production acceptance is outside this task.

Commands: `python -m pytest tests/test_community_feed_filters.py tests/test_feed_priority.py tests/test_home_stats_feed_ordering.py tests/test_feed_voting.py tests/test_report_notifications.py tests/test_profile_privacy.py -q`; `npx playwright test tests/community-feed-filters.spec.ts tests/home-stats-feed-ordering.spec.ts --workers=1 --max-failures=2`; `npx tsc --noEmit`; `npx eslint src/features/feed/components/CommunityFeedFilters.tsx src/features/feed/feedApi.ts tests/community-feed-filters.spec.ts`.
