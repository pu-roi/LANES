# LANES - Full System Documentation

> **Last Updated:** October 04, 2026, 05:01 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Reviewed flood growth (local):** Pending evidence can be reviewed across barangay/street boundaries. The backend uses pairwise geometry/time criteria and exposes nearby active event-owned zone targets; proximity is a review suggestion, not proof of one flood. `POST /admin/reports/merge-preview` is protected/read-only and composes the same coverage as publication. `/reports/merge` accepts `extend` (default; union supported old coverage/core with the reviewed section), `corroborate` (retain boundary/conditions), or `add_section` (new zone/conditions in the same event). Submitted line/multiline sections are buffered in UTM 51N; disconnected boundaries require a separate section or explicitly reviewed continuous extent. Legacy approval preserves old coverage; batch merge only links evidence. Original reports/posts are preserved, event locations record each supporting road/barangay/city, and merge/audit commit atomically. No model/migration/dependency changes. [Verification](../evaluations/phase-36-needs-review-inspection.md#october-4-cross-boundary-growth-implementation).

**Related report layout:** `RelatedReviewReports` now loads each visible member through the protected detail read and reuses `PendingReportsPanel`. Related rows use the same report badges, time, location, Info and moderation controls as the main report, without a duplicate selected row. Per-member read failures expose retry; records outside the current queue are inspection-only. Approving/rejecting a different report preserves the primary detail. Existing queue and Active Zones styling remain. [Verification](../evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-consistent-related-report-layout).

**Selected-report membership:** The member read accepts any current report identity and resolves its group in the backend, returning the canonical anchor key and grouping reason. `NeedsReviewPanel` no longer retains the last queue card's group; member query caches use the selected identity and member page. Map selection and external handoffs therefore cannot inherit another card's related reports. Singleton groups hide the related section. Boundary-crossing grouping now follows the spatial/time policy above; barangay names alone do not exclude review. [Regression verification](../evaluations/phase-36-needs-review-inspection.md#october-4-follow-up-selected-report-group-resolution).

**Local Spatial Operations inspection:** `/admin/map` now labels its first tab Needs Review and keeps Active Zones. All/User Reports/News Claims filters consume protected `GET /api/v1/admin/review/items`; `GET /items/{key}` provides source-specific preserved evidence and current-queue membership. `GET /api/v1/admin/review/groups/{key}/members` paginates related user reports. Backend `spatial_review_grouping` reuses merge road normalization with pairwise two-hour complete-link checks (500 m on the same road/city, 50 m otherwise) before card pagination; report counts remain distinct from card counts. New admin feature components are `review/NeedsReviewPanel`, `ReviewQueueCard`, `RelatedReviewReports`, `NewsReviewEvidence`, `reviewApi` and `useNewsPlacementLayer`. Light blue user group cards open individual evidence with a plain Related reports list inside the detail view; the queue has no member dropdown; light violet news cards remain separate. Desktop evidence remains beside the map; mobile switches Map/Evidence, including narrow/landscape layouts. Candidate centerlines are isolated blue dashed suggestions with no initial selection, buffer, public zone or routing effect. Report moderation and independent Create/Merge/Edit sessions remain. SQL/service/API layers use existing report/extraction storage with no migration; news decisions/publication remain unfinished. [Verification](../evaluations/phase-36-needs-review-inspection.md).

**Previous v10 backend placement checkpoint:** captured extraction adds `placement_preview` with exact NOAH scenario/class overlaps, section-matched Pasig DRRMO rows, OSM/source checksums and alternatives. `GET /api/v1/admin/news/results/{run_id}/{claim_index}/placement` is rate-limited/admin-protected and computes current placement from immutable evidence without network, auditor or database/public writes. New providers: `news_placement_preview_service.py`, `noah_vector_catalog_service.py`; contracts: `schemas/news_placement.py`; builder: `scripts/build_noah_placement_catalog.py`. External assets use `LANES_NEWS_NOAH_DIR`. That checkpoint changed no UI/lifecycle; the subsequent local inspection UI is described above. 550 distinct backend checks passed (one skip). [Verification](../evaluations/phase-36-backend-placement-preview.md).

**Latest local v9/v1.7:** `summary.water_level` prefers source wording over normalized gauges; `passable_unspecified` renders **Passable; vehicle types not specified** and cannot authorize closure. Clearance clocks preserve subsided status and the reported **by** bound. Road/landmark province and island follow grounded city/PSGC, removing unrelated homonym provinces. The existing shared responsive UI consumes server labels without frontend business rules or source changes. Four complete source bodies, 38 database/detail records and both actual API/proxy readers agree; 595 backend checks pass. Prior v8 notes below are history. No production release or visual acceptance is implied. [Audit](../evaluations/phase-36-four-article-source-audit.md).

**Current local v8/v1.6 workflow:** existing publisher corrections supersede current inputs even when revised body/RSS denies or removes local flood evidence; previous inputs/runs stay immutable and newest readers hide unsupported claims. Collection uses credible history only to preserve retrieval-error visibility, never to restore older main results. Approved `passable_with_caution` has an explicit no-closure guard; server `NewsFloodSummary.passability` supplies the Road passability label rendered by `NewsResultDialog` in its shared responsive grid. The dead no-locations Collection option is removed with legacy enum compatibility retained. Independent road predicates retain separate facts. All 452 backend tests, TypeScript and scoped lint pass; private API retains 33 sites and 20 caution records. Inspected production collection remains every three hours, with no new refresh policy or deployment. [Follow-up](../evaluations/phase-36-news-workflow-follow-up.md).

**September 9 local v7/v1.5:** three captured publisher bodies produce 33 readable location records through reconstructed RSS discovery and existing durable processing/SQL reading. Extraction preserves validated road/barangay identity, contiguous list evidence, each row's own depth and scoped observation clocks. A narrowly approved GMA matching publication/update header can anchor later same-day observations while original publication remains unchanged. Forecast/drill/negated/history/prevention list context remains excluded; independent narrative ends list inheritance. Real authenticated API/frontend proxy list and detail evidence pass, with 410 related tests. Final visual verification remains blocked by saved browser permission. Collection retains three September 9 articles needing checks alongside the ready September 24 article; no historical zone/report creation. The private launcher now requires explicit restart after backend changes rather than Windows auto-reload. No new API/model/UI/dependency; production release pending. [Evaluation](../evaluations/phase-36-september9-production-day-replay.md).

**Article-level city context (local v6/v1.4):** `mark_city_summaries_as_context` reconciles completed rule extraction within one article. Credible streets/landmarks/barangays in the same resolved city make redundant broad city observations context only. Caption-only, ambiguous, speculative, negated and conflicting specific claims cannot hide a city-only observation; distinct explicit times remain separate. Existing SQL reader/Collection gates honor the context flag before pagination/counts. Source sentences, offsets and per-street facts remain stored. The local replay now has five readable street cards, zero attention items and two immutable extraction runs; no new API, model, migration or frontend filtering. Production release remains pending.

**News details location fields:** `NewsResultDialog` supplies a flat Reported location section through the optional `locationDetails` slot in shared `FloodLocationSummary`, between the location heading and measurements. It displays existing detail claim fields `canonical_road`, `canonical_barangay`, `road_segment_raw` and `local_area_raw`; a missing road says **Not specified for this mention**. City remains in the summary heading/area. No extraction, cross-claim inference, API/model change or verified geometry is implied. Existing callers keep their layout without the slot. Desktop/mobile live replay and existing modal regression checks pass; local frontend change, not deployed.

**Local page verification:** `backend/start-local-news-test.ps1` loads ignored `.env.test.local` before the shared encrypted cloud config and verifies a dedicated loopback `lanes_news_test` target. `frontend/start-local-news-test.ps1` uses the existing API proxy; both bind to loopback. `scripts.seed_local_news_replay` stores actual historical evidence through existing services. Authenticated real API/browser checks confirm five main-list road locations, original dates, Boni evidence/source and zero Collection attention items. No new route, response field, UI component or model is introduced. [Runbook](../guides/local-news-replay.md).

**Local v5 replay correction (not deployed):** server extraction preserves narrative road intersections/directions, compound measurements, original observation/clearance clocks and parent-city PSGC identity. `location_context_only` qualifiers remain in evidence history but count toward neither main-list flood locations nor Collection questionable mentions. A genuine isolated historical article has five road sites plus two broad summaries, is `ready` with zero attention items, and does not create reports/zones. Production v4 history is unchanged. [Replay evidence](../evaluations/phase-36-september24-historical-replay.md).

**Strict actual-flood collection follow-up released:** backend body admission and main-list SQL require affirmative Metro Manila flooding evidence; newly unreadable articles remain discovery diagnostics rather than candidates. GET `/api/v1/admin/news/collection?status=excluded` exposes unsupported legacy history, while default attention excludes it. `NewsCollectionDrawer` and `newsApi.ts` render the backend's excluded status on desktop/mobile. v4/v1.2 preserve immutable evidence. API `00049-q25`, the matching collector and Firebase frontend `build-2026-10-03-002` are live. All 341 backend tests, 15 PostgreSQL checks and 15 deployed desktop/mobile cases pass (mocked API/session); saved/normal executions succeed. No database schema change. [Evidence](../evaluations/phase-36-news-content-quality-investigation.md#v4-backend-release-verification).


**News evidence correction released (October 3):** shared backend prevention/habitual and Metro Manila rules qualify every readable collector body and main-list/Collection counts before pagination. Local headlines cannot bypass body evidence. Excluded artifacts retain source/history with an explanatory reason. Corrected processing is versioned (`rules-psgc-osm-2026-10-03-v3`, extractor `taglish-rules-v1.1`). API `00048-xc7`, the matching collector and Firebase frontend `build-2026-10-03-001` are live. Approved migration and corrective/normal collector executions succeed; ten new runs preserve 20 earlier runs and 24 articles. All 306 backend checks, eight PostgreSQL checks and 13 deployed desktop/mobile asset checks pass (API/session mocked). See [release evidence](../evaluations/phase-36-news-content-quality-investigation.md#completed-production-release).

**F4b durable monitoring:** GET `/api/v1/admin/news/monitoring` supplies current body totals, newest extraction counts and ten retrieval issues. GET `/monitoring/discovery` and `/monitoring/fallback` use `news_telemetry.py` CRUD/schemas and `news_telemetry_service.py` for protected, bounded history reads with sanitized 503s. `NewsSourcesDrawer` Pipeline mounts lazy `NewsTelemetryHistory` sections with independent pagination/refresh, feed counters and alternate lead metadata; shared dialog/buttons preserve responsive/keyboard behavior. `news_discovery_service` records staff and collector runs; `news_fallback_service` captures stable input before retrieval. Fallback inspection records an attempt; history refresh is GET-only and does no external retrieval. The four approved telemetry tables are migrated locally and in production to `c5a7e9d2104f`; automated deployed desktop/mobile checks pass, while developer visual acceptance remains open. Delay is unavailable until durable publication exists. See [verification](../evaluations/phase-36-f4b-monitoring-check.md).

The staff news `open-leads` endpoint accepts `retrieve_articles=true` to fetch up to three approved alternate publisher bodies. Each result includes its publisher ID, fetch timestamp, text or error, and a same-event review status. It now persists operational lookup/lead metadata, while alternate article bodies remain response-only and do not create flood evidence, publication or activation. Index-seen dates are not publication/observation dates.

**Current sequencing:** Priorities 3 and 4 are deployed with migration `f29b6c8d104e`, active API revision `lanes-api-00047-59t`, and collector `--discover --process --limit 50`. Shared extraction stores optional `RoadPlacementEvidence` under each claim in the existing JSONB result. The provider uses bundled `runtime_data/osm/` files, validates full checksums/boundaries/nodes, and performs no geometry HTTP requests or public writes. Ten backlog inputs retain old and map-aware results; repeats create no work. Production GMA historical span matching passes. Missing source/coverage/precise extent remains visible, and neither centerlines nor historical map data authorize a closure. Fresh incident acceptance and Priority 5 publication/review/correction/expiry remain open. See [release evidence](../evaluations/phase-36-reusable-road-match-check.md#production-release-verification).

**Intended automatic news flow:** RSS/discovery → server NLP/NER → bounded OSM road placement with analytical UP NOAH vectors and matching Pasig DRRMO history → automatic source-labeled alerts and gated expiring zones → commuter map/routing. Routine eligible news claims bypass staff approval; Needs Review handles exceptions and corrections. Existing user-report moderation retains its current workflow. Operational NOAH/DRRMO integration and automatic publication/activation remain pending; F5/F6 and F7 share the next runtime/lifecycle delivery bundle.

**OSM runtime dependency isolation:** `NewsRoadPlacementProvider` reads the validated JSON catalog and imports pure graph/geometry routines from `article_road_match_service.py`. Native `osmium` loading is now confined to `load_bounded_osm_roads`, preserving the raw-PBF parser while allowing runtime extraction/catalog placement without that native import. All 140 focused regressions pass. Raw-PBF tools retain the separate local Windows restriction; no API/UI/schema/dependency change. See [verification](../evaluations/phase-36-automatic-plan-alignment-audit.md#verification-recovery-runtime-dependency-isolation).

The local-status and unchanged-scheduling statements in the earlier preparation notes below describe the pre-release state and are superseded by this production verification.

**Priority 5 frontend state — F3 design accepted, F4b durable monitoring implemented; full manual acceptance pending:** `/admin/news` retains its thin route/loading/error boundary and session/persistent-map shell. NewsIntelligencePage renders one NewsResults list with Collection status and Sources & feeds controls. NewsResultDialog has Flood Details / Source Article tabs; NewsSourceArticle shows title/publisher, original publication and LANES-save dates, full text and lazy collection details. NewsCollectionDrawer uses the shared RecordDetailsDialog drawer variant, lists server-classified article states and opens source text within the same focus-managed surface. NewsProcessingDetails loads bounded immutable history within Source Article's desktop right pane or mobile Processing history view; collection article inspection keeps lazy More details. Shared FloodLocationSummary/FloodDetailMetric/Tabs/TabContentPanel/Card/Button/Input/Select/Pagination/Skeleton remain reused. The existing Spatial Operations report modal uses the same metric tile. Responsive single/two-column facts, full-height mobile drawer, safe areas and 44px actions are implemented; manual visual acceptance remains pending. No browser or development server was started. Older standalone article components are retained as earlier implementation files but are no longer mounted by this route. See [verification](../evaluations/phase-36-f3-result-browsing-check.md).

**Frontend-only Info refinement:** NewsResultDialog now uses RecordDetailsDialog's opt-in wide/panels layout and shared RecordDetailsPanels for independently scrolling desktop article/history sections inside Source Article. Mobile switches between Article and Processing history inside Source Article; Flood Details shows only flood facts and evidence. Panel history loads when Source Article opens and shares the existing article query; Collection status keeps lazy More details history. Shared RecordTimeline is used by NewsProcessingDetails and Flood History's incident timeline. NewsSourceArticle's opt-in reader presentation uses plain date metadata, avoids the redundant excerpt when full text is available and opens that text by default; collection inspection retains its existing default. Shared panels give the article more width. History has a sticky heading and compact status/date/count rows with errors surfaced. NewsProcessingDetails invokes the Info parent's record-inspection callback instead of expanding output in the sidebar. NewsExtractionRecordView inspects one immutable run with Mentions / Article / Technical tabs in the full-width dialog body, using the existing article query and explicit unavailable/error/retry states. The underlying article/history pane remains mounted but hidden, preserving scroll/expanded state; Back restores focus to the original record action. Full article text is directly visible in reader mode; optional collection metadata remains expandable. Other shared-dialog defaults remain unchanged. TypeScript/lint pass; visual desktop/mobile acceptance remains manual. No backend or database changes were made for this refinement.

**F4a source monitoring:** NewsSourcesDrawer opens from the same page using shared RecordDetailsDialog/Tabs/Button/Skeleton. Publishers and Feed checks render existing authenticated GET /admin/news/sources and /admin/news/feeds payloads. Feed checks load on selection; cached reads and Refresh saved status do not probe, collect or mutate. Saved timestamps/errors stay distinct, missing clocks are explicit and an old successful fetch never clears a displayed recorded error. Full-height responsive drawer, safe areas, 44px actions, focus/escape and visible errors/retry/empty states are reused. No backend/schema/dependency change. Discovery totals, blocked-body/fallback history and collection-to-alert delay are unavailable from these reads.

**F2 staff read API:** `GET /api/v1/admin/news/articles` returns cards, counts, publisher options and server pagination; accepts page/page_size, literal title/excerpt search, publisher, body state, latest recorded processing state and recently-seen/publication ordering. `GET /api/v1/admin/news/articles/{id}` returns the current article, newest twenty recorded runs, total history count and matching immutable inputs. Both use existing staff dependencies; storage failures return 503 and missing IDs return 404. The thin handlers call `news_browsing_service.py`, backed by `crud/news_browsing.py` and typed `schemas/news_browsing.py`. Reads neither mutate evidence nor execute extraction. These new reads must be released alongside the frontend before production use.

**F3 staff read API:** `GET /api/v1/admin/news/results` SQL-paginates readable reported locations from each article's newest recorded run, with scope `latest_reported_locations`, server search/publisher/condition/placement/order filters and stable run/ordinal keys. Older completed runs, and results with a newer pending/failed attempt, are excluded from the main list. `GET /api/v1/admin/news/results/{run_id}/{claim_index}` remains a historical artifact lookup with immutable input/provenance. `GET /api/v1/admin/news/collection` supplies server-classified saved articles, global status counts, publishers and literal search/status/publisher pagination; attention excludes ready articles and all retains access to every saved article. Collection reads use news_collection_service/crud/news_collection and typed news_collection contracts. Existing staff dependencies and sanitized 503/404/422 handling apply. No durable review identities or lifecycle writes are added; production release remains pending.

**News fact presentation:** Server summaries prefer source-reported road_segment_raw/local_area_raw over broad raw names, preserving road context. Results expose snapshot captured_at and original article saved_at; article details retain per-run flood_summaries. Derived reading_status/reading_reason explain conservative screening: usable place/evidence, affirmative condition/depth/closure evidence, no forecast/negation/historical flags and no metadata-only/errors. Unknown depth or time alone does not exclude an otherwise reported flood. SQL and Python predicates agree on tested PostgreSQL cases; map uncertainty remains distinct from evidence screening. This is a read policy, not a persisted staff decision. Unknown clocks remain null, formatted in Asia/Manila without publication-time substitution. Models, migrations and stored artifacts are unchanged.

The continued Priority 2 check repaired flood-control program/project text being interpreted as active flood evidence. Shared Taglish extraction excludes policy-only sentences/clauses, preserves genuine explicit flood gauges in mixed-topic reports, and retains source evidence offsets. Body-only location probes reject the constructed administrative story. Metadata-local policy headlines may still arrive as review leads, without extracted flood observations. Thirteen focused cases and 207 combined regressions pass. Both six-feed diagnostics parsed 95 entries with no eligible candidate. A real manually selected Philstar administrative body yielded no qualifying flood observation; the initial approval-review error cleared on one permitted retry without changing approval settings. These changes remain local; live automatically discovered positive matching is unverified.

Saved extraction previews provide staff-only `GET /api/v1/admin/news/candidates/{article_id}/extraction` (3/minute). `NewsSavedExtractionSummary` returns real article ID/URL, stable input fingerprint, `read_only=true`, `extraction_mode=rules_only`, typed claims or a visible error. Missing IDs return 404; unauthenticated/commuter access returns 401/403. Saved/discovered previews share `_extract_article_inputs` in `news_discovery_service.py`. The CLI `--extract-saved --dry-run --limit 50` reads pending evidence through existing CRUD, bounds batches at 200, and exits nonzero on processing/storage failures. Empty work returns `no_candidates`; JSON contains structured results. Missing/errored/oversized bodies never enter extraction, and per-input failures retain later outputs. Previews do not perform HTTP retrieval, audit, ingestion, SQL writes, or evidence/review/public changes. Input identity excludes fetch time and canonicalizes equivalent publication offsets. Durable processing is implemented separately through the approved two-table worker; deployed scheduling is unchanged.

Publication revisions on the same article URL trigger a body refresh even when title/summary are unchanged. Older feed revisions cannot overwrite newer stored evidence. Failed refreshes preserve the last successful body and its original metadata/publication date, while surfacing `article_error`; duplicate provenance cannot relabel that body. The dormant ingestion service treats an errored body as unavailable and rejects public activation even if a cached claim action says `auto_approved`. This is a refresh-safety repair, not production ingestion wiring. Successful pending revisions update the current article row; the approved local worker separately preserves immutable prior/current inputs and handles pending extraction after unchanged feeds. These new paths are not yet deployed.

GDELT requests share a per-process gate with one in-flight query, a 10-second gap, and a 10-minute success cache bounded to 32 query results. Throttling and transient failures return `retry_after_seconds` plus a `Retry-After` header rather than sleeping through a long cooldown or retrying immediately. Cooldowns start at 60 seconds and grow to 15 minutes; a longer provider `Retry-After` is respected. HTTP-200 plain-text throttle notices also enter cooldown. Cached results can remain available during another query's cooldown. State resets on process restart and is not shared across Cloud Run replicas.

GDELT queries override the endpoint client's timeout with 15-second connect / 20-second read budgets, following measured TLS handshakes of 8–11 seconds. With `retrieve_articles=true`, a successful title/phrase lookup without an alternate can additionally search Metro Manila place/flood terms within two days of the original publication, bounded to the last 90 days. Provider failures stop further index queries. If no approved index alternate exists, the backend independently probes at most five enabled, verified alternate publisher feeds for originals published within seven days; flood/place matches with publication times within two days become unverified leads. Alternate bodies remain capped at three. Feed leads expose their own `published_at`, with no fabricated index-seen time. No recovered body returns `alternate_article_unavailable`; successful retrieval still requires event review, and provider errors remain visible.

The existing `scripts.run_news_discovery --open-leads` mode runs the lookup without opening a database session. `--trace-network` reports TCP/TLS elapsed times, HTTP status, and public host without headers, credentials, or article bodies. With `--retrieve-articles`, an unavailable body returns exit code 1 even if index links exist. This diagnostic is separate from `--discover` and does not enable scheduled fallback.

`scripts.run_news_discovery --discover --dry-run --extract` exercises collection and the actual hybrid extractor in rules-only mode, without database sessions, external audits, or ingestion calls. It exposes claim actions/places/depth/time/provenance, per-article errors, and explicit no-candidate outcomes; non-dry-run extraction is rejected. The feed parser normalizes known HTML character names outside CDATA into numeric XML references while preserving XML escapes and rejecting DTD/custom entities. Received HTTP status is retained for XML parse failures; HTML/challenge responses are explicit failures. A healthy empty feed is not a network failure. This source change is not deployed.

Priority 2 adds `notices` (source ID, article URL, reason) to staff run responses and CLI discovery output. Five extra article probes per run can resolve location from body-only flood claims; known non-local city/province metadata and future timestamps are excluded. Local leads precede unknown-scope probes, ordered newest first within each feed. Notices are not a durable processing queue. Alternate `event_review.road_updates` records per-city/road previous and alternate observation times, depths, conditions, and a decision. Later observations can propose depth/status changes or clearance; older observations do not replace newer ones. Same-time disagreement, ambiguous states, different segments, and recurrence after clearance require review. Twelve-hour freshness applies to update proposals, and index/publication time is never substituted for observation time. Every proposal retains missing-original-body and unverified-segment/incident evidence. Copied bodies remain flagged, and original evidence/public zones stay untouched by the lookup. A stored body with a refresh error can use the protected fallback; an error-free full body still returns 409.

> **Stack:** Next.js 18 (App Router) | FastAPI | PostgreSQL + PostGIS | Valhalla / OpenRouteService
> This document maps every screen, component file, backend endpoint, and database table in the system.

---

## Table of Contents

1. [Global Layout & Navigation](#1-global-layout--navigation)
2. [Landing Page (/)](#2-landing-page-)
3. [Map Page (/map)](#3-map-page-map)
4. [Community Feed (/feed)](#4-community-feed-feed)
5. [Post Detail (/feed/id)](#5-post-detail-feedid)
6. [Profile Page (/profile)](#6-profile-page-profile)
7. [Auth Pages (/login, /register, /verify)](#7-auth-pages)
8. [About Page (/about)](#8-about-page-about)
9. [Analytics Page (/analytics)](#9-analytics-page-analytics)
10. [Admin Panel (/admin/*)](#10-admin-panel-admin)
11. [Backend API Reference](#11-backend-api-reference)
12. [Database Tables Reference](#12-database-tables-reference)
13. [Entity Relationship Summary](#13-entity-relationship-summary)
14. [Production Cloud Deployment Architecture](#14-production-cloud-deployment-architecture)

---


## 1. Global Layout & Navigation

These files are **always present** regardless of which page you are on.

### Always-Visible Files

| File | Location | What It Does |
|------|----------|--------------|
| `layout.tsx` | `src/app/layout.tsx` | Root HTML shell. Sets fonts (Open Sans, Roboto Mono), imports global CSS and MapLibre CSS, wraps every page in `QueryProvider`, `NavigationWrapper`, and `AppProviders`. |
| `globals.css` | `src/app/globals.css` | Global Tailwind base layer + custom MapLibre control overrides. |
| `NavigationWrapper.tsx` | `src/features/navigation/NavigationWrapper.tsx` | Route guard layer. Redirects unauthenticated users away from protected routes (`/profile`, `/report`, `/feed/create`). Redirects Super Admins to `/admin`. Shows a loading spinner overlay during redirects. |
| `FloatingNav.tsx` | `src/features/navigation/FloatingNav.tsx` | The pill-shaped floating top navigation bar (desktop only). Contains the LANES logo, links to Home / Feed / Map / Profile, an Admin shortcut (for non-Commuter staff), and a Log Out button. Always centered on the full viewport regardless of page. |
| `MobileNav.tsx` | `src/features/navigation/MobileNav.tsx` | Fixed bottom tab bar visible only on mobile. Same links as FloatingNav but icon-only with labels. |
| `OfflineBanner.tsx` | `src/features/offline/OfflineBanner.tsx` | A slim red banner that appears at the very top of the page when the browser loses internet connectivity. |
| `NotificationBell.tsx` | `src/features/notifications/NotificationBell.tsx` | A floating bell icon (bottom-right corner, desktop). Shows an unread count badge. Clicking opens a dropdown of recent notifications (likes, comments, system alerts, and administrative post removal/moderation warnings styled with amber `AlertTriangle` warning badges). Listens to a real-time SSE stream from the backend. |
| `GlobalMap.tsx` | `src/features/map/GlobalMap.tsx` | Mounts the map instance globally via `providers.tsx` so it persists across all page navigations. Manages which map panels are open (Route, Analytics, Save Place, Flood Report, Offline Manager). |
| `providers.tsx` | `src/app/providers.tsx` | Wraps children with `MapContextProvider` and mounts `GlobalMap`. This is why the map is always rendered even when visiting non-map pages. |

---

## 2. Landing Page (/)

**Route file:** `src/app/page.tsx` → renders `<LandingView />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `LandingHero.tsx` | `src/features/landing/LandingHero.tsx` — Full-screen responsive landing hero featuring animated headline typography, system value propositions, quick navigation action buttons to Live Map and Community Feed, and real-time community flood statistics. |
| `LandingView.tsx` | `src/features/landing/LandingView.tsx` — The entire landing page layout. Contains the hero section (headline, CTA buttons), stats row, features grid, how-it-works steps, and footer. Also tracks page visits by calling the `/public/visit` backend endpoint on mount. |
| `HomeStats.tsx` | `src/features/landing/HomeStats.tsx` — The three animated stat counters (Total Reports, Verified Zones, Total Visitors) displayed in the hero section. Fetches live counts from the backend `/public/stats` endpoint. |
| `WeatherWidget.tsx` | `src/features/landing/WeatherWidget.tsx` — A compact weather card showing current temperature, humidity, and a short description for Metro Manila. Fetches from the backend `/weather/current` endpoint. |
| `ForecastChart.tsx` | `src/features/landing/ForecastChart.tsx` — A 7-day rainfall/temperature forecast chart (Recharts line chart) displayed below the weather widget. |
| `FloodGauge.tsx` | `src/features/landing/FloodGauge.tsx` — Split-view interactive MMDA vehicle clearance rules and depth gauge container. Coordinates hover/tap state between the depth table and the SVG human silhouette, with responsive dual-screen layout and mobile auto-scroll. |
| `FloodGaugeTable.tsx` | `src/features/landing/FloodGaugeTable.tsx` — Interactive MMDA flood classification table with 8 canonical depth tiers (`gutter`..`neck`), severity indicators, dual-unit measurements (`inches` and `meters`), and animated expandable vehicle accessibility badges (`PATV`, `NPLV`, `NPATV`). |
| `FloodGaugeSilhouette.tsx` | `src/features/landing/FloodGaugeSilhouette.tsx` — Gender-neutral inline SVG human silhouette calibrated to 165 cm (5'5") reference height according to DOST-FNRI adult standards. Dynamically animates rising water levels via Framer Motion springs, vertical centimeter ruler ticks, water surface line, and depth measurement bubbles. |
| `FloodLegend.tsx` | `src/features/landing/FloodLegend.tsx` — A lightweight 4-card fallback legend card explaining flood severity colors (Low / Medium / High / Extreme) with MMDA vehicle clearance thresholds. |

### Hidden Until Interaction

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `WeatherInsightsModal.tsx` | `src/features/landing/WeatherInsightsModal.tsx` — Click the **"See Full Forecast"** button on the weather widget | Full-screen modal with detailed hourly and 7-day weather forecast, rain probability bar charts, wind speed data, and AI-generated commute recommendations powered by OpenRouter (`/weather/insights`). Calls backend directly via `NEXT_PUBLIC_API_URL`. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/public/visit` | Increments the visitor counter in the DB |
| `GET /api/v1/public/stats` | Returns total reports, verified zones, visitor count |
| `GET /api/v1/weather/current` | Current weather for Metro Manila |
| `GET /api/v1/weather/forecast` | 7-day weather forecast data |
| `GET /api/v1/weather/insights` | AI-generated commuter flood risk insights & weather advisory via OpenRouter |

---

## 3. Map Page (/map)

**Route file:** `src/app/map/page.tsx` → renders `<MapPage />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `MapCanvas.tsx` | `src/features/map/MapCanvas.tsx` — The full-screen MapLibre GL map canvas. Renders 3D terrain, Pasig city boundary, active flood avoidance zones (color-coded polygons), user location dot, alternative route polylines, saved places, and center-anchored pulsing red focus markers. Features resilient `map.getStyle()` layer mounting, `style.load` re-render listeners, auto camera `fitBounds` framing, container resize observer alignment for sidebar offsets, and parses `?lat=&lng=&zoom=` for smooth camera fly-to. |
| `useNoahHazardLayer.ts` | `src/features/map/hooks/useNoahHazardLayer.ts` — Displays one Metro Manila UP NOAH rainfall scenario as a transparent, terrain-draped map image beneath labels and operational zones. The source images are generated by `backend/scripts/export_noah_hazard_overlay.py` from the local 5-, 25-, and 100-year archives; they are display assets, not spatial analysis inputs. The layer reloads after map style changes, and failed image loads raise a toast. On `/map`, the selector appears above Saved Places on desktop or in a short drawer from the mobile `+` menu, only in 3D. No scenario is selected on entry to 3D; returning to 2D clears the display. The legend says the colors show modeled hazard, not live flooding. |
| `BaseMap.tsx` | `src/shared/ui/map/BaseMap.tsx` — Low-level MapLibre wrapper that owns one WebGL map instance, resize observation, and `onMapInit`/`onMapLoad` callbacks. It begins with MapTiler when configured, treats the first rendered frame after `style.load` as usable, and falls back to a LANES-identified OSM raster style only on a MapTiler resource error or exhausted 1.5-second budget. It retries MapTiler on reconnect/backoff. `style.load` preserves LANES-owned layers after each style replacement. A compact viewport-anchored status remains clear of the desktop floating navigation and wraps on smaller screens; document-level connection hints and production PWA caching accelerate MapTiler repeat visits. |
| `RoutePanel.tsx` | `src/features/routing/RoutePanel.tsx` — The left sidebar on desktop (collapsible on mobile). Contains the travel profile selector (including **Bike/Motorcycle**), start/destination inputs with focus guards and smart two-click "Choose on Map" advance, authenticated saved places chips with Start/End-preserving recalculation, and up to four navigable route cards categorized as Fastest, Safest, Balanced, and Alternative. Cards render route-specific flood exposure; a rejected fastest baseline is explanation-only, never selectable. |
| `FloodReportPanel.tsx` | `src/features/hazards/FloodReportPanel.tsx` — The responsive incident reporting panel (opens from FAB or top CTA). Step one accepts raw Start/End selections, then submits the verified road-only line or dual-carriageway coverage returned by the shared preview; it never persists a raw sidewalk-to-road connector. When **Share in Community Feed** is checked, the report is published to the feed immediately; only official map-zone visibility awaits administrator approval. The photo/video picker uses a direct native input and copies selected files before resetting it, so attachment chips remain visible on mobile and desktop; submission errors surface in the panel, and failed uploads prevent report creation. Account-private drafts restore only when an active report has a selected road endpoint plus severity, survey data, description, or media; queued reports remain recoverable. UI-only toggles, wizard state, survey visibility, and typed-but-unselected locations never restore a draft. Severity tiles are unselected by default and toggle off when reselected; opt-in two-way coverage is unchecked by default. The compact **Clear** dialog offers neutral **Clear all** (removes previews, queued drafts, media, and the persisted account draft) plus rightmost red **Clear this page** (preserves work on the other page). `useFloodMapPreview.ts` renders each validated carriageway in its own MapLibre source/layer so close parallel geometry remains visible through a style reload. |
| `OfflineManager.tsx` | `src/features/offline/OfflineManager.tsx` — The "Offline Routing — Ready for offline use" status indicator at the bottom of the RoutePanel. Shows whether the offline tile cache and Valhalla routing data are downloaded and ready. |
| `MapPickerMobileOverlay.tsx` | `src/features/map/MapPickerMobileOverlay.tsx` — A translucent overlay with a centered crosshair that appears on mobile when the user taps a location input, letting them drag the map to pin a point. |
| `useFloodMapPreview.ts` | `src/features/map/hooks/useFloodMapPreview.ts` — A shared custom hook for Start/End marker management and the bidirectional orange-dashed route preview. It renders only final snapped geometry returned by server verification, then positions the visible pins at that road geometry's endpoints. While verification is pending, the selected pins remain without a misleading straight connector. |
| `usePendingReportsLayer.ts` | `src/features/map/hooks/usePendingReportsLayer.ts` — Renders pending public reports as their existing transparent, severity-colored road aura at street-level zoom. Its endpoints and turns are intentionally rounded, matching Active Zone and public-preview road coverage. |
| `AdminFloodMapInteraction.tsx` | `src/features/admin/components/AdminFloodMapInteraction.tsx` — Admin `/admin/map` bridge between MapLibre and `MapContext`; owns Create Zone map clicks, crosshair cursor state, Start-to-End progression, and the shared preview lifecycle. |

### Hidden Until Interaction (Map Panels)

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `SavePlacePanel.tsx` | `src/features/places/SavePlacePanel.tsx` — Click the ❤️ (heart) icon in the right floating controls | A panel for saving a custom named location (Home, Work, School, etc.) with an icon picker and address field. Saves to the backend. |
| `AnalyticsPanel.tsx` | `src/features/analytics/AnalyticsPanel.tsx` — Click the 📊 (chart) icon in the right floating controls, or select **View Flood Analytics** on the landing page | A floating panel showing flood report analytics: active zone count, severity breakdown, and recent activity feed. The landing action opens `/map?panel=analytics`; `MapContext` consumes this signal and opens Flood Insights on arrival. |
| `LocationAutocomplete.tsx` | `src/shared/ui/LocationAutocomplete.tsx` — Typing in the Start or Destination input inside RoutePanel | A dropdown of geocoded place name suggestions powered by Nominatim via the backend. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/reports/zones` | Fetches all active flood avoidance zone polygons to render on the map |
| `POST /api/v1/reports/` | Submits a new flood report from the FloodReportPanel form |
| `POST /api/v1/reports/preview-bidirectional` | Builds an authoritative road preview from raw Start/End anchors. Valid routes retain only their Valhalla-snapped road vertices; the raw selections are input anchors and never become returned or saved connector geometry. Edge shape indexes split mixed road/topology runs before carriageway validation; a map-matched counterpart is trimmed to its longest genuinely parallel component. A short graph-mapped Y merge may be retained only when it connects the matching original-road endpoint, while cross-street or detached junction connectors cannot enter coverage. A verified opposite line therefore applies only to its matching run. Returns the original line, an optional graph-validated opposite carriageway, combined coverage geometry, road classification, validation status, and user-facing explanation. The `/routes/preview-bidirectional` controller remains the canonical implementation. |
| `POST /api/v1/reports/route` (also `/api/v1/routes` and `/api/v1/routes/route`) | Loads authoritative active PostGIS zones once, obtains both fastest and shortest Valhalla or ORS candidates with hard/cautious avoidance, evaluates each actual geometry under one server-side policy, removes ineligible paths, and returns up to four distinct categorized routes plus an optional non-selectable blocked-baseline explanation. Walking uses pedestrian graph access and has no vehicle heading constraint. The provider may return fewer than four distinct legal routes. |
| `GET /api/v1/geocode/autocomplete?q=...` | Returns place name suggestions for location inputs |
| `GET /api/v1/geocode/reverse?lat=&lon=` | Converts a map tap coordinate to a human-readable address |
| `POST /api/v1/users/me/saved-places` | Saves a bookmarked location |
| `GET /api/v1/users/me/saved-places` | Loads saved places to show as quick-access shortcuts in RoutePanel |

---

## 4. Community Feed (/feed)

**Route file:** `src/app/feed/page.tsx` → renders `<FeedPage />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `FeedPage.tsx` | `src/features/feed/FeedPage.tsx` — The main three-column feed layout. Center column shows the scrollable list of standalone `PostItem` cards separated by clean whitespace (`space-y-3 sm:space-y-4`) with responsive mobile edge margins (`px-3 sm:px-0 pt-3 sm:pt-4`), composer placeholder (`"What's happening?"` on mobile vs `"What's happening in your area?"` on desktop), and standalone loading/empty cards. Left and right sidebars are pinned on desktop. Fetches paginated posts on load. |
| `LeftSidebar.tsx` | `src/features/feed/LeftSidebar.tsx` — Left panel (desktop only). Shows the logged-in user's avatar, display name, trust score badge, quick stats, saved places pills (which open the Saved Places panel), and a "Create Post" shortcut button. Features hover-activated custom slim scrollbar. |
| `RightSidebar.tsx` | `src/features/feed/RightSidebar.tsx` — Right panel (desktop only). Shows community highlights: top contributors, recent active flood zones, and trending location tags. |
| `PostItem.tsx` | `src/features/feed/PostItem.tsx` | An independent, standalone card in the feed (`bg-white rounded-xl sm:rounded-2xl shadow-sm border border-gray-100`). Shows author avatar/name/role, post text, attached media carousel, responsive flood severity badge (compact on mobile, detailed on desktop), standalone `ArrowBigUp`/`ArrowBigDown` voting buttons with active fills, comment count, and responsive single-row action bar (compact map/share labels on iPhone SE/12). Provides a dropdown menu with soft-deletion support: author self-deletion prompts a standard confirmation dialog, while staff/admin removal triggers an **Administrative Post Removal** modal prompting for violation category and notes. Dispatches an in-app `SYSTEM` notification to the post author explaining the decision, logs an `ADMIN_DELETE_POST` audit record, and updates the feed via SSE. Its interactive location badge and flood-report **View on Map** action focus the road-length midpoint of the saved report geometry; paired carriageways focus their shared center. |
| `EmergencyHotlinesCard.tsx` | `src/features/feed/components/EmergencyHotlinesCard.tsx` — API-backed priority emergency contacts with expandable numbers, direct `tel:` links, loading/unavailable states, and a full-directory trigger. Rendered in the feed sidebar layout. |

### Hidden Until Interaction

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `CreatePostModal.tsx` | `src/features/feed/CreatePostModal.tsx` — Click **"Create Post"** or the **"+"** floating button | Full-screen modal with rich text area, drag-and-drop image & video upload (up to 100MB per file with explicit size validation toasts), address autocomplete or map crosshair location picking, coordinate persistence (`location_lat`, `location_lng`), and draft auto-saving that persists across auth redirects. Submits multipart payloads to `POST /api/v1/posts`. |
| `EmergencyDirectoryModal.tsx` | `src/features/feed/components/EmergencyDirectoryModal.tsx` — Click **"View All Hotlines"** | Lazily loaded national, Pasig city, and Pasig barangay hotline directory with tabbed sections, search, and phone links. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/feed/posts?page=&limit=` | Paginated list of community posts |
| `POST /api/v1/feed/posts` | Create a new community post |
| `DELETE /api/v1/posts/{id}` | Soft-deletes a post; supports optional `CommunityPostDeletePayload(reason, details)` when deleted by staff to deliver author notification and audit log |
| `POST /api/v1/feed/posts/{id}/interact` | Upvote or downvote a post |
| `PATCH /api/v1/posts/{id}` | Owner-only complete post update; writes an immutable before/after history version |
| `GET /api/v1/posts/{id}/history` | Public chronological edit-history entries for a post |
| `POST /api/v1/posts/{id}/reports` | Authenticated non-author submission of one private open moderation report |
| `GET /api/v1/hotlines/` | Loads cached national emergency hotlines for the sidebar card |
| `GET /api/v1/hotlines/full` | Lazily loads national, Pasig city, and Pasig barangay hotlines for the directory modal |

---

## 5. Post Detail (/feed/[id])

**Route file:** `src/app/feed/[id]/page.tsx` → renders `<PostDetailPage />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `PostDetailPage.tsx` | `src/features/feed/PostDetailPage.tsx` — Full expanded view of a single post. Shows all post content, attached media gallery, linked flood report details with severity badge (if any), and the full threaded comment section. Supports nested replies (up to 2 levels), inline upvote/downvote on each comment, comment pinning (for admins/moderators), and edit/delete for comment authors. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/feed/posts/{id}` | Full post data including flood report linkage |
| `GET /api/v1/comments/{post_id}` | All comments for the post (threaded) |
| `POST /api/v1/comments/{post_id}` | Submit a new top-level comment or reply |
| `PUT /api/v1/comments/{comment_id}` | Edit your own comment |
| `DELETE /api/v1/comments/{comment_id}` | Delete your own comment |
| `POST /api/v1/comments/{comment_id}/interact` | Upvote or downvote a comment |

---

## 6. Profile Page (/profile)

**Route file:** `src/app/profile/page.tsx` → renders `<ProfileView />`
**Requires authentication.** Redirects to `/login` if not logged in.

### Always Visible on Load

| File | What You See |
|------|-------------|
| `ProfileView.tsx` | `src/features/profile/ProfileView.tsx` — The full profile page split into tabs: **Personal Info** (name, contact, birthdate, address form), **Hazard Reports** (submitted user reports with severity and approval status), **Community Posts** (user's authored community feed posts rendered as standalone spaced cards with post count indicator badge and unboxed background styling), and **Settings** (instant optimistic privacy toggles for profile visibility, full name display, hide profile picture, secure password change with email OTP verification, and account Danger Zone for self-deletion with 30-day grace period). Includes an interactive avatar header with click-to-preview high-resolution modal, Cloudinary photo upload with loading spinner, and remove picture actions. |
| `PasswordOtpModal.tsx` | `src/features/profile/components/PasswordOtpModal.tsx` — Reusable security dialog with 6-box zero-click auto-submitting numeric OTP inputs, auto-focus, clipboard paste handling, resend countdown ticker, and inline verification errors for password update authorization. |
| `SavedRoutesList.tsx` | `src/features/profile/SavedRoutesList.tsx` — Sub-component inside ProfileView that lists the user's saved map places with their custom icons and addresses, and a delete button for each. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/users/me` | Load current user's full profile data |
| `PATCH /api/v1/users/me/profile` | Update profile fields and privacy toggles |
| `DELETE /api/v1/users/me` | Self-deactivate account with a 30-day recovery grace period |
| `POST /api/v1/users/me/avatar` | Upload and attach a profile picture to Cloudinary |
| `DELETE /api/v1/users/me/avatar` | Remove the custom profile picture and revert to initial avatar |
| `POST /api/v1/users/me/password/request-otp` | Validate current password and send 6-digit confirmation OTP to email |
| `PUT /api/v1/users/me/password` | Change password (requires current password and verified email OTP code) |
| `POST /api/v1/auth/request-otp` | Send OTP to email for re-verification |
| `POST /api/v1/auth/verify-otp` | Verify an OTP code |
| `GET /api/v1/users/me/places` | Load saved places list |
| `DELETE /api/v1/users/me/places/{id}` | Delete a saved place bookmark |


---

## 7. Auth Pages

### Login Page (/login)

| File | What You See |
|------|-------------|
| `LoginForm.tsx` | `src/features/auth/LoginForm.tsx` — Email + password fields, Google Sign-In button, "Forgot Password?" trigger, and a "Sign Up" redirect link. Displays a green success banner when redirected from registration with `?registered=true`. Prioritizes administrative roles (`Super Admin`, `DRRM Officer`, `Moderator`) to route directly to `/admin/dashboard` upon login while purging commuter session intents. For commuters, routes to `/map` or `/feed?openPostModal=true` if post intent is active. |

### Forgot Password Flow (/login?forgot=true or /forgot-password)

| File | What You See |
|------|-------------|
| `ForgotPasswordForm.tsx` | `src/features/auth/components/ForgotPasswordForm.tsx` — Pixel-consistent 3-step password recovery modal: Step 1 accepts user email and dispatches single-use OTP via Resend with progressive cooldown tiers (1m, 3m, 5m); Step 2 provides 6-box OTP entry with clipboard paste support and countdown timer; Step 3 provides new password entry with `<PasswordStrength>` meter, confirm password validation, and hold-to-view toggle. On submit, resets password and returns user to login. |

### Register Page (/register)

| File | What You See |
|------|-------------|
| `RegisterForm.tsx` | `src/features/auth/components/RegisterForm.tsx` — Multi-step registration wizard with identity-first email verification, OTP confirmation, password/profile entry, and PSGC address selection. Supports Google OAuth Sign-Up with automatic prefill of full name, email, and avatar, allowing citizens to complete only remaining required demographic fields before account activation. On final submit, calls `POST /api/v1/auth/register` (or `POST /api/v1/auth/google` with `mode: "register"`), clears registration drafts, and redirects to login. |

### Verify Page (/verify)

| File | What You See |
|------|-------------|
| OTP input page | Six-digit OTP code input. Calls `POST /api/v1/auth/verify-otp`. On success, the account becomes active and the user is redirected to `/map`. A "Resend Code" button calls `POST /api/v1/auth/request-otp`. |

### Backend Calls

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/auth/login` | Authenticates and returns a JWT access token |
| `POST /api/v1/auth/google` | Authenticates or registers users using verified Google OAuth ID tokens |
| `POST /api/v1/auth/register` | Creates a new user account and sends OTP via email |
| `POST /api/v1/auth/verify-otp` | Marks the account as active after OTP verification |
| `POST /api/v1/auth/request-otp` | Resend a new OTP to the email |
| `POST /api/v1/auth/forgot-password/request-otp` | Initiates self-service password recovery by sending a single-use OTP via Resend |
| `POST /api/v1/auth/forgot-password/verify-otp` | Verifies recovery OTP and returns a signed 15-minute `password_reset` JWT |
| `POST /api/v1/auth/forgot-password/reset` | Validates `password_reset` JWT and commits updated password hash |
| `POST /api/v1/auth/logout` | Invalidates the current JWT server-side |

---

## 8. About Page (/about)

**Route file:** `src/app/about/page.tsx`

Informational page describing the LANES project mission, authors, adviser, and system architecture. Features official communication channels and an interactive contact inquiry form.

### Always Visible on Load

| File | What You See |
|------|-------------|
| `ContactSection.tsx` | `src/features/about/ContactSection.tsx` — Direct contact card displaying official communication channels (`lanes@navlanes.live` with backup `navlanes.live@gmail.com`) with one-click copy support, and an interactive message inquiry form (Name, Email, Subject, Message) connected to Resend with client feedback states. |

### Backend Calls

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/public/contact` | Submits a contact inquiry with rate limiting (`5/min`) and dispatches transactional emails via Resend (`send_contact_email_async`) with direct reply-to headers |

---

## 9. Analytics Page (/analytics)

**Route file:** `src/app/analytics/page.tsx`

A public-facing data visualization dashboard. Shows flood report trends over time using Recharts charts. On this page, the map canvas switches to a read-only overview mode and the RoutePanel is hidden.

### Backend Calls

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/analytics/reports-over-time` | Time-series count of flood reports by day/week |
| `GET /api/v1/analytics/severity-distribution` | Count of reports grouped by severity level |
| `GET /api/v1/analytics/top-barangays` | The most frequently reported barangays |

---

## 10. Admin Panel (/admin/*)

**Requires authentication + a non-Commuter role.** All admin pages are wrapped in `AdminLayout.tsx` which renders the sidebar navigation and persistently mounts the Spatial Operations Live Map in the background to prevent map reloads during tab switches.

### Sub-pages

| Route | File | What It Does |
|-------|------|-------------|
| `/admin` | `AdminDashboard.tsx` | Entry landing — shows role-based nav links and a summary stats row (total users, reports, active zones). |
| `/admin/news` | `src/features/news/NewsIntelligencePage.tsx` | One server-filtered Flood Locations list with specific segment/intersection cards; Info has Flood Details / Source Article. Collection status opens a shared responsive drawer for failed/empty/questionable and all saved articles. More details retains immutable processing history. Newest recorded runs supply current cards; publication/save/flood clocks remain separate. Developer desktop/mobile acceptance pending; feed/source monitoring is later work. |
| `/admin/dashboard` | `DashboardPage.tsx` | Responsive overview cards for pending reports, active detours, today’s approvals, today’s Flood Report rejections, accounts, and privacy-preserving daily unique visitors. Features a unified 3-column bento layout organizing the 30-day visitor trend, reports over time, and severity breakdown in Row 1, with Top 5 Most Flooded Barangays, System Health Check, and Quick Administration Tasks aligned beside each other in Row 2. The rejection action opens the Flood Report Moderation workspace with rejected cases selected. |
| `/admin/map` | `LiveMapPage.tsx` | Full-screen admin map & spatial operations view (persistently mounted in `AdminLayout`). Pane 1 contains `PendingReportsPanel` and `ActiveZonesPanel`; Pane 2 shows one of Create Zone, Review Merge, or amber Edit Zone at a time. Pending Reports and Active Zones keep independent current selections. Returning to a tab flies to that tab's selected report or zone only; toggling the selected card or map feature off clears its selection and prevents a later tab switch from moving the map. Create and Edit are separate resumable sessions: the blue Create Zone bookmark retains its account-private draft, while the amber Edit Zone bookmark retains its selected zone and per-admin edit draft; neither replaces or discards the other. Create Zone is always the first desktop handle. Merge and Edit appear only after being opened and are arranged most-recent-first directly below it; switching keeps their component state and scroll position, while explicit Close removes the matching workspace rather than leaving a collapsed handle. The Edit close control is available on desktop and mobile and retains its discard confirmation. Review Merge remains independently resumable. On mobile, Active Zones exposes Create Zone and the shared drawer header can switch to the other available workspace. Normal report focus is neutral. **Review Merge Suggestions** starts a persistent merge session with explicit candidate checkboxes, in-card match evidence, a field comparison matrix, selected-only conflicts, reusable road/Terra Draw editing, confirmation, and primary/candidate/proposed map previews. `zoneDraftStorage.ts` restores Create Zone's active workspace and editable queued drafts. Edit Zone restores only a dirty per-admin draft after fetching the current zone; unchanged and legacy baseline copies are removed silently. It can replace a validated road centreline or reopen the final saved area polygon for Terra Draw vertex editing. A road update stores the new source line and regenerated 25-metre operational buffer; an area update stores the exact polygon and clears obsolete source geometry. It also includes `ReportDetailsModal`, the 400ms `FloodZonePopup` hover engine, and one shared `OfficialZoneDrawer` implementation with `GeometryModeSelector`, `RoadSegmentPicker`, `DraftZoneCart`, five aligned form sections, and Cloudinary media upload. |
| `/admin/users` | `UsersPage.tsx` | Searchable table of all registered users. Admin can filter by role, view trust scores, activate or deactivate accounts, and reassign roles. |
| `/admin/roles` | `RolesPage.tsx` | Role management. Create new roles with a granular permission matrix (view / manage / full per module). Edit or delete existing roles. |
| `/admin/data` | `DataManagementPage.tsx` | Data import/export tools. Upload flood report CSVs, export reports as JSON or CSV, and inspect raw PostGIS geometry for any record. |
| `/admin/audit` | `AuditTrailPage.tsx` | Chronological log of all admin actions — who did what, when, and on which record. Filterable by admin user, action type, and date range. |
| `/admin/moderation` | `ModerationCenterPage.tsx`, `components/FloodModerationQueue.tsx` | Staff-only tabbed Community Post and Flood Report tracking using the shared underline `Tabs` component. The Dashboard may deep-link to the Flood tab with rejected cases preselected. Flood cases show their outcome/context and filters, then provide a single **Review on Map** handoff; no spatial approval/rejection controls are duplicated here. The responsive action area remains clear of the mobile bottom navigation. |
| `/admin/flood-history` | `flood-history/page.tsx`, `features/flood-history/*` | Admin-only Flood History & Analytics has a server-calculated distinct-event planning dashboard plus a separate historical `BaseMap` source/layer set for Flood Event Records. Its responsive Recharts visuals include a verified-event/approved-report combination trend, severity doughnut, duration columns, recurrence rankings, and an accessible Philippine-time verification heatmap. The Overview clarifies distinct-event, ended-event, duration, recurrence, road, evidence, and timing definitions. Compact shared `Card`, `Button`, `Input`, `Select`, `DatePicker`, and `Tabs` components keep its filters, cards, controls, desktop/mobile map-list presentation, and blue-led non-severity graphs visually consistent with the Admin Dashboard. A protected record uses Overview, Official History, and Reports tabs: the first covers lifecycle, peak and affected places; the second covers official zones and timeline; and Reports is a responsive master-detail evidence review. On desktop, the report list remains visible while the existing shared report/evidence view slides into the right panel; on mobile, that shared view replaces the list with a Back to reports action. Event, zone, and source-report map actions focus a temporary overlay on the same read-only historical map; they never navigate to live Spatial Operations or affect routing. Protected filters drive recurrence, roads, peak severity, official duration, and time-series analytics; authorized users can download filtered planning records or aggregate analytics as CSV/JSON without reporter identity, raw evidence, report geometry, or media. |
| `/admin/settings` | `SystemSettingsPage.tsx` | Key-value configuration editor for runtime settings (e.g., flood zone expiry duration in hours, severity thresholds). |
| `/admin/archive` | `ArchivePage.tsx` | Centralized Archive Center with 30-day auto-purge retention lifecycle across three primary tabs: **Archived Users** (soft-deleted commuter accounts with 30-day countdown badge, restore action, and typed `"DELETE"` permanent purge), **Spatial Data** (dual sub-tabs for soft-deleted/rejected Flood Reports and deactivated/expired Avoidance Zones with detail inspection, Attached Media & Evidence photo/video gallery, reactivation, and typed `"DELETE"` permanent deletion), and **Archived Posts** (dual sub-tabs for Community Feed posts soft-deleted by authors/admins and posts hidden by moderators with full media/author inspection, feed restoration, and typed `"DELETE"` permanent deletion). Includes on-demand manual trigger to purge expired records. |
| `/admin/profile` | `AdminProfilePage.tsx` | Native Admin Profile hub matching public profile design. Super Admins, DRRM Officers, and Moderators can edit personal details, phone number, birthdate, and PSGC address, change account cover banner color, upload or remove avatar images, toggle privacy preferences ("Display Full Name", "Hide Profile Picture"), and securely change account passwords with live `<PasswordStrength>` validation and email OTP verification via `PasswordOtpModal`. Linked from the user profile card in the `AdminSidebar.tsx` footer. |

> **Flood Event lifecycle update (Phase 33):** `/admin/map` remains the only operational moderation workspace. `RejectFloodReportModal` requires a structured reason, keeps rejected evidence out of Archive Center, and notifies the submitting user through the existing bell without disclosing internal notes. Approving/merging a report or directly creating an official zone creates or links a verified Flood Event; server services calculate event metrics, record readable zone/severity timeline entries, and end the event when its final live zone ends. **Known Cloud SQL integrity issue ([BUG-055]):** active Events #6 and #8 currently retain timeline snapshots for missing reports/zones, so their historical detail correctly returns zero live links. Remediation is pending explicit schema/data approval; history remains read-only and does not reconstruct evidence in the UI.

### Backend Calls (Admin)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/admin/reports` | Paginated admin view of all reports with filters |
| `PUT /api/v1/admin/reports/{id}/approve` | Approve report, auto-generates flood avoidance zone polygon |
| `POST /api/v1/admin/reports/{id}/reject` | Reject report with a structured reason, moderation outcome, trust update, and reporter notification |
| `GET /api/v1/admin/flood-events` | Admin-only ordered list of verified Flood Events for the Flood History & Analytics entry surface |
| `GET /api/v1/admin/flood-events/history` | Admin-only filtered historical event records, including isolated historic zone geometry, locations, and server-calculated evidence metrics |
| `GET /api/v1/admin/flood-events/analytics` | Admin-only, filter-aware city-planning aggregation that counts distinct Flood Events once and returns recurrence, roads, peak severity, official-duration, time-series, and separate approved-report confidence metrics |
| `GET /api/v1/admin/flood-events/export` | Admin-only CSV/JSON export of filtered planning event records or aggregate analytics; default exports omit reporter identity, raw text, exact report geometry, and media |
| `GET /api/v1/admin/flood-events/{id}/history-detail` | Admin-only full historical Flood Event detail: event metrics, locations, event-owned zones, linked original reports, and readable incident timeline |
| `GET /api/v1/admin/flood-events/{id}/summary` | Admin-only server-calculated event duration, evidence, zone, location, peak, and status metrics |
| `GET /api/v1/admin/dashboard/visitors` | Admin-only 30-day first-party unique-visitor trend and current/lifetime aggregate totals; never returns visitor identifiers |
| `GET /api/v1/public/stats` | Public landing statistics, including the deduplicated first-party visitor total |
| `POST /api/v1/public/visits` | Records one visible browser’s daily visit from an opaque UUID after server-side HMAC hashing; known bots are rejected and no IP or fingerprint is stored |
| `POST /api/v1/admin/zones` | Create official flood avoidance zone (multipart `FormData` with JSON `body` and `media` files) |
| `GET /api/v1/admin/zones/{id}` | Retrieve the current shared zone before resuming an account-private Edit Zone draft |
| `PUT /api/v1/admin/zones/{id}` | Update existing avoidance zone metadata, depth, severity, passability, and notes |
| `POST /api/v1/admin/zones/{id}/media` | Append authenticated administrator evidence uploads to an existing zone |
| `GET /api/v1/admin/reports/merge-candidates` | Multi-factor spatial candidate scoring for report merging |
| `POST /api/v1/admin/reports/merge` | Multi-report merge into a new or existing avoidance zone |
| `GET /api/v1/admin/moderation/reports` | Staff-only list of open (or resolved) Community Post moderation cases, grouped by post |
| `POST /api/v1/admin/moderation/posts/{id}/resolve` | Atomically dismiss, warn, or soft-hide a Community Post and resolve all its open reports |
| `GET /api/v1/admin/moderation/flood-reports` | Admin-only Flood Report moderation cases with status, source, date, location, reporter, and rejection-reason filters; provides safe map-focus coordinates |
| `GET /api/v1/admin/reports/detail/{report_id}` | Admin-only full report read for a focused Spatial Operations review, including approved and rejected reports retained in moderation history |
| `GET /api/v1/admin/users` | All users with role and profile info |
| `PUT /api/v1/admin/users/{id}` | Update user role or active status |
| `POST /api/v1/admin/users/{id}/restore` | Restore a soft-deleted/archived user account and profile |
| `DELETE /api/v1/admin/users/{id}/permanent` | Permanently hard-delete a user account and profile |
| `POST /api/v1/admin/archive/purge-expired` | Manually execute 30-day auto-purge on expired archived users, posts, reports, and zones |
| `GET /api/v1/admin/roles` | All roles with their permission matrices |
| `POST /api/v1/admin/roles` | Create a new role |
| `PUT /api/v1/admin/roles/{id}` | Update role permissions |
| `DELETE /api/v1/admin/roles/{id}` | Delete a role |
| `GET /api/v1/admin/audit` | All audit log entries with filters |
| `GET /api/v1/admin/settings` | All system settings |
| `PUT /api/v1/admin/settings/{key}` | Update a specific system setting |
| `GET /api/v1/admin/zones` | All flood avoidance zones with PostGIS geometry |
| `POST /api/v1/admin/zones` | Manually create a new zone polygon |
| `PUT /api/v1/admin/zones/{id}` | Update zone geometry, status, or expiry |
| `DELETE /api/v1/admin/zones/{id}` | Permanently delete a zone |
| `POST /api/v1/admin/reports/{id}/restore` | Restore a genuinely soft-deleted flood report; rejected reports remain a durable moderation outcome |
| `POST /api/v1/users/me/password/request-otp` | Validate current password and dispatch 6-digit confirmation OTP to user email |
| `PUT /api/v1/users/me/password` | Verify current password and email OTP code, and update account password with password complexity validation |

**Base URL:** `http://localhost:8000/api/v1`
**Framework:** FastAPI (Python) with SQLAlchemy 2.x ORM
**Authentication:** JWT Bearer tokens — stored in `localStorage` on the frontend, sent as `Authorization: Bearer <token>` header

### Endpoint File Map

| File | URL Prefix | Who Can Access |
|------|------------|----------------|
| `auth.py` | `/auth` | Public |
| `public.py` | `/public` | Public |
| `weather.py` | `/weather` | Public |
| `users.py` | `/users` | Authenticated users |
| `reports.py` | `/reports` | Authenticated users |
| `feed.py` | `/feed` | Authenticated users |
| `posts.py` | `/posts` | Authenticated users |
| `comments.py` | `/comments` | Authenticated users |
| `notifications.py` | `/notifications` | Authenticated users |
| `analytics.py` | `/analytics` | Public |
| `sse.py` | `/sse` | Authenticated users (EventSource) |
| `sync.py` | `/sync` | Authenticated users (offline support) |
| `hotlines.py` | `/hotlines` | Public |
| `admin.py` | `/admin` | Staff roles only (non-Commuter) |
| `admin_news.py` | `/admin/news` | Staff-only source probes, feed health, pending candidates, collection, manual submission, and open leads. Saved extraction GET is read-only (3/minute). `GET /candidates/{article_id}/processing` lists the last 20 typed runs; POST enqueues/processes that candidate (3/minute), returns safe 409/503 failures and bounded outcomes. Lease tokens are never exposed. |
| `roles.py` | `/roles` | Staff roles only |
| `data.py` | `/data` | Staff roles only |
| `settings.py` | `/settings` | Staff roles only |

### Key Backend Services

| Service | What It Does |
|---------|-------------|
| **Taglish Flood Extraction and Geometry Prototypes** | `taglish_extraction_service.py` uses deterministic rules and the nationwide PSGC reference to extract source-linked places, canonical depth, flood condition, and event time. `nationwide_geometry_service.py` ranks locations and generates preview polygons with provenance; it does not verify the affected road segment or use LiPAD/UP NOAH hazard layers. `article_road_match_service.py` is a separate read-only local-PBF matcher for explicit spans and a splitter for OSM between-intersection road sections; `noah_road_prediction_service.py` ranks supplied sections from article context, place-matched DRRMO support, and modeled NOAH overlap. The C. Raymundo road-only audit remains ambiguous. These research services are not connected to article ingestion or zone creation. `hybrid_extraction_service.py` adds an optional OpenRouter Gemini auditor; an unavailable auditor leaves active claims in the exception path. `NewsAutoIngestionService` reevaluates all approval gates at the public-write boundary, but the present geometry provider cannot satisfy them. calamanCy and Cloud Natural Language are not integrated. The remaining GMA/Inquirer full-article replay is paused; the scheduled collector does not invoke the extraction prototype. |
| **RSS News Discovery** | `news_sources.py`, `news_feed_service.py`, and `news_discovery_service.py` read six verified runtime feeds and parse bounded RSS/Atom; the original 50-publisher research inventory stays in `docs/plans/rss-news-discovery-plan.md` and is not loaded by the collector. Current source prioritizes Metro Manila RSS clues, then permits five extra body-location probes per run for flood headlines with unknown scope. Accepted extra leads need an extracted local flood claim; unresolved/blocked/future/budget outcomes are exposed as run notices. Clearly non-local city/province metadata is skipped. `crud/news.py` saves conditional feed checkpoints/article evidence in the three deployed Cloud SQL tables. The new approved revision additionally enqueues immutable input versions and extraction runs atomically; migrate before running it. `news_processing_service.py` executes bounded rules-only extraction independently of feed responses. The optional `news_open_search_service.py` searches the public GDELT index by title, then an RSS phrase for an incomplete article when staff invoke its admin endpoint; returned links never populate `article_text`. Six feeds and a three-hour Cloud Run schedule were verified in the earlier rollout; the revised Metro Manila filter and pruned source configuration are not yet verified in the deployed Cloud Run job. No collector path currently creates a public zone or changes routing. |
| **Routing Engine Proxy** | Uses Valhalla (primary) or OpenRouteService (secondary) only to generate candidates. The shared FastAPI flood policy evaluates candidate geometry against active `flood_avoidance_zones`, blocks medium exposure for light/Bike-Motorcycle and Red/Extreme exposure for every public profile; Orange/High is a strongly cautioned 40% fallback only for Walking. It ranks up to four distinct legal routes and reports deterministic exposure details. |
| **Zone Deduplication** | When a new flood report is approved near an existing active zone (within a configurable buffer distance), it is linked to that zone instead of creating a new duplicate polygon |
| **Trust Score Engine** | Automatically recalculates a user's `trust_score`, `accuracy_rate`, and report counters in `profiles` whenever one of their reports is approved or rejected |
| **Weather Proxy** | Fetches data from the OpenWeatherMap API, transforms and caches the response, and serves it to the frontend |
| **SSE Broadcaster & LiveSync** | Pushes real-time notification events, active zone changes, and cache invalidations to connected clients via Server-Sent Events. Centralized in `sse.ts` to stream directly from FastAPI port 8000 in dev/LAN environments to bypass dev proxy response buffering, with unconditional unmount cleanup in `useLiveSync.ts` avoiding zombie reconnect loops. The backend `/sync/stream` polls using a short-lived worker-thread SQLAlchemy session per snapshot, so an open stream does not retain a database-pool connection. |
| **Data Retention & Auto-Purge Service (`retention_service.py`)** | Executes daily periodic background tasks and on-demand triggers to permanently purge soft-deleted users, posts, reports, and zones that exceed the 30-day retention window |
| **Hotline Aggregator** | Fetches and parses national and Pasig emergency contact pages, normalizes phone numbers for `tel:` links, and caches results for one hour |

---

## 12. Database Tables Reference

**Database:** PostgreSQL with PostGIS extension
**ORM:** SQLAlchemy 2.x + GeoAlchemy2 for spatial columns
**Migration tool:** Alembic

---

### News discovery evidence tables (migration `a83c1d4e7b92`)

These three tables were applied to development PostGIS and production Cloud SQL in the September 25 rollout. `news_feed_checkpoints` stores each feed URL, source ID, ETag, Last-Modified value, check/success times, and last error. `news_articles` keeps a unique canonical article URL, publisher source ID, title, excerpt, publication/fetch/seen times, optional public text or retrieval error, content fingerprint, and review state. `news_article_feed_entries` links each article to a source/feed URL/GUID with first/last seen times and optional JSONB metadata; the source, feed URL, and GUID combination is unique. The foreign key cascades only when a stored article is deleted. The current collector path does not create Flood Reports, Flood Events, or map zones.

---

### Durable extraction tables (migration `f29b6c8d104e`, not yet deployed)

`news_article_versions` stores immutable input snapshots keyed by article/hash, protected by an UPDATE-rejection trigger and RESTRICT foreign key. `news_extraction_runs` stores pipeline/mode-keyed typed artifacts, attempts, due times, token-owned leases, safe errors, and lifecycle timestamps. The [database contract](database-design-plan.md) records every field/constraint/index. Apply/rollback/apply and four database checks passed in disposable PostgreSQL/PostGIS. Collector processing is opt-in (`--discover --process`) or independent (`--process-saved`); both bound work at 200. No public report/event/zone writes or external audit calls occur.

### `roles`

Stores permission configurations for different staff types.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `name` | String(50), unique | Role label — e.g., "Commuter", "Moderator", "Super Admin" |
| `permissions` | JSON | Dictionary of module → permission level — e.g., `{"reports": "full", "zones": "view"}` |
| `is_template` | Boolean | Whether this is a built-in system template role |
| `created_at` | DateTime | Timestamp when the role was created |

---

### `users`

Core user accounts — one row per registered person.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `username` | String(50), unique | Public display handle |
| `email` | String(100), unique | Login email address |
| `hashed_password` | String(255) | Bcrypt-hashed password |
| `role_id` | FK → roles.id | The user's assigned role |
| `is_active` | Boolean | Whether the account is enabled (false = suspended or not yet verified) |
| `created_at` | DateTime | When the account was registered |
| `deleted_at` | DateTime, nullable | Soft-delete timestamp (null = account is live) |

---

### `profiles`

Extended personal details and community trust metrics. One-to-one with `users`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id, unique | The linked user account |
| `first_name` | String(100) | First name |
| `last_name` | String(100) | Last name |
| `middle_initial` | String(10), nullable | Middle initial |
| `suffix` | String(20), nullable | Name suffix — e.g., Jr., III |
| `contact_number` | String(20), nullable | Phone number |
| `birthdate` | Date, nullable | Date of birth |
| `avatar_url` | String(255), nullable | URL to the profile picture |
| `hide_profile_picture` | Boolean | Whether to hide avatar and display uppercase initial fallback (default: false) |
| `cover_color` | String(20) | Hex color for the profile page banner (default: `#3B82F6`) |
| `is_public` | Boolean | Whether the profile is visible to other users |
| `display_full_name` | Boolean | Whether to show full name or just username on posts |
| `trust_score` | Integer | Community trust score from 0–100 (default: 50) |
| `reports_submitted` | Integer | Total number of flood reports filed by this user |
| `reports_approved` | Integer | Number of their reports approved by admins |
| `reports_rejected` | Integer | Number of their reports rejected by admins |
| `accuracy_rate` | Float | Calculated as `(reports_approved / reports_submitted) × 100` |
| `updated_at` | DateTime | Last time the profile was updated |

---

### `addresses`

Residential address. One-to-one with `profiles`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `profile_id` | FK → profiles.id, unique | The linked profile |
| `house_number` | String(100), nullable | House or unit number |
| `street` | String(255), nullable | Street name |
| `barangay` | String(100) | Barangay name |
| `city_municipality` | String(100) | City or municipality |
| `province` | String(100) | Province |
| `postal_code` | String(20), nullable | Postal/ZIP code |
| `country` | String(100) | Country name (default: "Philippines") |

---

### `otp_verifications`

Temporary OTP codes for email verification. Records expire after 10 minutes.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `email` | String(100) | Email address the OTP was sent to |
| `otp_code` | String(255) | Bcrypt-hashed 6-digit code (never stored in plain text) |
| `expires_at` | DateTime | When the code expires (typically created_at + 10 minutes) |
| `attempts` | Integer | Number of wrong-guess attempts (lockout after 5) |
| `is_verified` | Boolean | Whether the code was successfully used |
| `created_at` | DateTime | When the OTP was generated |

---

### `flood_reports`

Incoming flood event reports from users or external scraped sources.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id, nullable | Reporter user (null if scraped from social media or seeded) |
| `raw_text` | String | Original report text, typically in Taglish |
| `source` | Enum | Origin: `twitter`, `facebook`, `direct_user`, or `manual_seeder` |
| `source_url` | String(500), nullable | Original URL if scraped from social media |
| `severity` | Enum | Flood level: `low`, `medium`, `high`, or `extreme` |
| `depth` | String(50), nullable | Estimated flood depth key (`gutter`, `knee`, etc.). Mapped dynamically to MMDA physical measurements (`depth_meters`, `depth_inches`, `depth_formatted`) in API responses without schema alterations |
| `status` | Enum | Moderation state: `pending`, `approved`, or `rejected` |
| `media_urls` | JSONB, nullable | Array of photo/video URLs attached to the report |
| `human_readable_location` | String(255), nullable | Geocoded address string for display purposes |
| `barangay` | String(100), nullable | Extracted barangay name (indexed for fast filtering) |
| `city` | String(100), nullable | Resolved city or municipality name (indexed for fast filtering) |
| `is_public` | Boolean | Whether this report appears in the community feed |
| `zone_id` | FK → flood_avoidance_zones.id, nullable | The avoidance zone this report was merged into (deduplication) |
| `geometry` | PostGIS GEOMETRY (SRID 4326), nullable | Point or LineString coordinates of the flood location |
| `created_at` | DateTime | When the report was submitted |
| `updated_at` | DateTime | Last modification time |
| `deleted_at` | DateTime, nullable | Soft-delete timestamp |
| `approved_at` | DateTime, nullable | Timestamp when an admin approved this report |

---

### `flood_report_locations`

Normalized location name tags extracted by NLP from flood report text. Many-to-one with `flood_reports` (3NF normalization).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `report_id` | FK → flood_reports.id | The parent flood report |
| `location_name` | String(100) | An extracted place name — e.g., "España Blvd", "Barangay 646" |

---

### `flood_report_surveys`

Survey answers submitted alongside a user-filed report. One-to-one with `flood_reports`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `report_id` | FK → flood_reports.id, unique | The parent flood report |
| `passable_vehicles` | String(500), nullable | Free-text answer — what vehicles can still pass? e.g., "motorcycles only" |
| `hidden_hazards` | Enum | Whether the reporter noticed hidden dangers: `yes`, `no`, or `unsure` |

---

### `flood_avoidance_zones`

Spatial polygon buffers generated around approved flood reports or curated directly by DRRMO administrators. Used by the routing engine to reroute traffic around flooded areas.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `name` | String(100), nullable | Descriptive operational name of the avoidance zone |
| `curated_by_admin_id` | FK → users.id, nullable | Admin who manually edited or created this zone (null if auto-generated) |
| `geometry` | PostGIS POLYGON (SRID 4326) | The actual closed polygon boundary of the avoidance area |
| `source_geometry` | PostGIS GEOMETRY, nullable | Original administrator-selected LineString or MultiLineString; used to render the active road core while `geometry` remains the routing buffer |
| `severity_override` | Enum, nullable | Overridden severity level (`low`, `medium`, `high`, `extreme`) |
| `depth_override` | String(50), nullable | Standard visual water depth gauge key (`gutter`, `knee`, etc.). Mapped dynamically to MMDA physical measurements (`depth_meters`, `depth_inches`, `depth_formatted`) in API responses without schema alterations |
| `passable_vehicles_override` | String(500), nullable | Comma-separated list of safe vehicle types |
| `hidden_hazards_override` | String(255), nullable | Presence of submerged dangers: `yes`, `no`, `unsure` |
| `admin_notes` | Text, nullable | Dispatch notes and operational instructions |
| `merge_rationale` | String(1000), nullable | Merge rationale summary |
| `media_urls` | JSONB, nullable | Photographic and video evidence URLs stored in Cloudinary |
| `is_active` | Boolean | Whether this zone is currently applied to route calculations |
| `created_at` | DateTime | When the zone was generated or created |
| `updated_at` | DateTime | Latest shared zone metadata update; used to protect Edit Zone drafts from overwriting a newer server version |
| `expires_at` | DateTime, nullable | Automatic expiry time (null = never expires automatically) |

---

### `saved_places`

Custom bookmarked map locations per user (Home, Work, School, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | The owner of this saved place |
| `name` | String(50) | Custom label — e.g., "Home", "Office", "School" |
| `icon` | String(50) | Icon identifier used for the map pin — e.g., "Home", "Briefcase", "Star" |
| `address` | String(255), nullable | Human-readable address string |
| `latitude` | Float | Latitude coordinate |
| `longitude` | Float | Longitude coordinate |
| `pin_order` | Integer, nullable | Custom order sequence for quick pills |
| `geometry` | PostGIS POINT (SRID 4326) | Spatial point for future proximity search queries |
| `created_at` | DateTime | When the place was bookmarked |

---

### `community_posts`

Posts in the community feed. Can be standalone or linked to a flood report.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | Post author |
| `flood_report_id` | FK → flood_reports.id, nullable | Linked flood report (if this post shares or discusses a report) |
| `content` | Text | Post body text |
| `media_urls` | JSONB, nullable | Array of attached image or video URLs |
| `location_tag` | String(255), nullable | Optional location label displayed on the post |
| `location_lat` | Float, nullable | Latitude coordinate for interactive map view / fly-to |
| `location_lng` | Float, nullable | Longitude coordinate for interactive map view / fly-to |
| `is_pinned` | Boolean | Pinned status flag |
| `pinned_at` | DateTime, nullable | Timestamp of pinning |
| `created_at` | DateTime | Post creation time |
| `updated_at` | DateTime | Last edit time |

### `community_post_edit_history`

Immutable before/after versions for Community Post edits. Each row belongs to one post and its author/editor, has a sequential per-post version number, and preserves content, media URLs, and location values as they existed before and after that edit.

---

### `comments`

Threaded comments on community feed posts.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | Comment author |
| `post_id` | FK → community_posts.id | The post this comment belongs to |
| `content` | String(250) | Comment text (max 250 characters) |
| `parent_id` | FK → comments.id, nullable | Parent comment ID for nested replies (null = top-level comment) |
| `upvotes` | Integer | Aggregated upvote count |
| `downvotes` | Integer | Aggregated downvote count |
| `created_at` | DateTime | When the comment was posted |
| `is_deleted` | Boolean | Whether the comment was soft-deleted (content replaced with "[deleted]") |
| `is_pinned` | Boolean | Whether an admin has pinned this comment to the top |
| `pinned_by` | String(150), nullable | Username of the admin who pinned it |
| `edited_at` | DateTime, nullable | Timestamp of the last edit |

---

### `post_interactions`

Upvote and downvote records for community posts. One record per user per post.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | User who interacted |
| `post_id` | FK → community_posts.id | The target post |
| `interaction_type` | Enum | `upvote` or `downvote` |
| `created_at` | DateTime | When the interaction was made |

---

### `comment_interactions`

Upvote and downvote records for comments. One record per user per comment.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | User who interacted |
| `comment_id` | FK → comments.id | The target comment |
| `interaction_type` | Enum | `upvote` or `downvote` |
| `created_at` | DateTime | When the interaction was made |

---

### `notifications`

In-app notification records pushed to users via SSE.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `user_id` | FK → users.id | The recipient of this notification |
| `type` | Enum | Notification category: `LIKE`, `COMMENT`, or `SYSTEM` |
| `message` | String(255) | Human-readable notification text shown in the dropdown |
| `payload` | JSONB | Extra data for deep-linking — e.g., `{"post_id": 42, "commenter": "juan"}` |
| `is_read` | Boolean | Whether the user has seen/dismissed this notification |
| `created_at` | DateTime | When the notification was created |

---

### `audit_logs`

Immutable trail of all admin actions for accountability and debugging.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `admin_id` | FK → users.id, nullable | Admin who performed the action (null if automated/system action) |
| `action_type` | String(50) | Category of action — e.g., `APPROVE_REPORT`, `UPDATE_ROLE`, `DELETE_USER` |
| `target_table` | String(50) | Which database table was affected — e.g., `flood_reports`, `users` |
| `target_id` | Integer, nullable | Primary key of the specific row that was affected |
| `metadata_json` | JSONB, nullable | Before/after snapshot or additional context data |
| `ip_address` | String(45), nullable | Admin's IP address at the time of action |
| `created_at` | DateTime | Exact timestamp of the action |

---

### `visitor_counts`

Legacy single-row landing counter retained only for historical database compatibility. The application no longer reads or updates it.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Always 1 (this table has exactly one row) |
| `total_visitors` | Integer | Cumulative count of landing page visits since deployment |

---

### `visitor_daily_visits`

First-party analytics rows used to calculate daily and lifetime unique visitors. A row is unique per UTC date and pseudonymous browser hash; it never stores raw browser IDs, IP addresses, fingerprints, or location.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Surrogate identifier |
| `visitor_hash` | String(64), indexed | HMAC-SHA256 of the browser-generated UUID; raw UUID is never persisted |
| `visit_date` | Date, indexed | UTC calendar day, unique with `visitor_hash` |
| `user_id` | FK → users.id, nullable | Optional signed-in account; aggregates collapse its browsers into one account visitor and becomes null if that user is deleted |
| `first_seen_at` / `last_seen_at` | DateTime | UTC activity timestamps for the day |

---

### `system_settings`

Key-value store for runtime-configurable system parameters editable by admins without code changes.

| Column | Type | Description |
|--------|------|-------------|
| `key` | String, PK | Setting identifier — e.g., `flood_zone_expiry_hours`, `min_report_trust_score` |
| `value` | JSONB | The setting value (any JSON type — number, string, array, object) |
| `last_updated_by` | FK → users.id, nullable | Admin who last changed this setting |
| `updated_at` | DateTime | Last update timestamp |

---

## 13. Entity Relationship Summary

```
roles ──< users ──< profiles ──< addresses
                │
                ├──< flood_reports ──< flood_report_locations
                │         │──< flood_report_surveys
                │         └──> flood_avoidance_zones (N reports → 1 zone)
                │
                ├──< community_posts ──< comments ──> (self-join: replies)
                │         │                └──< comment_interactions
                │         └──< post_interactions
                │
                ├──< saved_places
                ├──< notifications
                └──< audit_logs  (as admin actor)

otp_verifications  (standalone, keyed by email)
visitor_counts     (singleton table)
visitor_daily_visits ──> users (optional account attribution)
system_settings    (key-value store)
```

---

## 14. Production Cloud Deployment Architecture

The production environment operates across Google Cloud and Firebase within region `asia-east1` (Taiwan).

### Infrastructure Breakdown

| Component | Service | Configuration File | Role |
| :--- | :--- | :--- | :--- |
| **Frontend** | **Firebase App Hosting** | `frontend/apphosting.yaml`<br>`frontend/firebase.json` | Hosts Next.js SSR / App Router on Node.js 22 runtime. Builds via Google Cloud Build with injected build-time variables (`NEXT_PUBLIC_API_URL` pointing to Cloud Run backend). Production URL: `https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app`. |
| **Backend** | **Google Cloud Run** | `backend/Dockerfile` | Public FastAPI ASGI gateway. Binds to dynamic `$PORT` (8080), handles PostGIS and SSE, and calls private routing providers. Endpoint: `https://lanes-api-557679867071.asia-east1.run.app`. |
| **Online Router** | **Private Cloud Run Valhalla** | `infrastructure/valhalla/` | `lanes-valhalla` serves the Philippines graph with no public invoker. FastAPI supplies an ID token; Valhalla failures retry through ORS and the route response reports `engine_used` and `fallback_used`. |
| **CORS Policy** | **FastAPI CORSMiddleware** | `backend/app/main.py` | Dynamically authorizes local development (`localhost:3000`), production apex (`navlanes.live`), Vercel previews (`*.vercel.app`), and Firebase domains (`*.hosted.app`, `*.web.app`, `*.firebaseapp.com`). |
| **Secrets Mgmt** | **@dotenvx/dotenvx** | `backend/.env`<br>`backend/.env.keys` | Cross-platform AES-256 encrypted environment variables preventing credential leakage in git version control. |
| **CI/CD Pipeline** | **Google Cloud Build** | `cloudbuild.yaml` | Automates container image build (`gcr.io/$PROJECT_ID/github.com/pu-roi/lanes:$COMMIT_SHA`), executes database migrations via Cloud Run Job (`lanes-migration`), and deploys new revisions to `lanes-api` with `CLOUD_LOGGING_ONLY` audit logging. |
| **Database Migrations** | **Google Cloud Run Jobs** | `cloudbuild.yaml`<br>`backend/alembic/` | Serverless batch job (`lanes-migration`) executed synchronously (`--wait`) prior to web service rollout to apply Alembic migrations against production PostgreSQL. |

