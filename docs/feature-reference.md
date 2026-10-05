# LANES Feature Reference Document

> **Last Updated:** October 05, 2026, 7:02 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 5 publication/lifecycle follow-up:** Automatic source-labeled **text-only news alerts**, atomic append-only decisions, supported observation refresh, matched clearance and two-hour evidence expiry are implemented locally. Read-time expiry becomes **Unconfirmed** even before maintenance; the default current feed retains it for 24 hours after expiry (configurable 1–72 hours), while safe historical detail remains available. Staff correction/defer/reject/reopen/clearance controls and desktop/mobile public-map News alerts are connected. Operational flood-zone activation/routing remains blocked by missing verified current affected polygons; OSM/NOAH/community boundaries remain placement evidence. No live deployment, paid provider request, new schema/dependency or normal/cloud database migration occurred. [Verification](evaluations/phase-36-news-publication-lifecycle.md), [operator guide](guides/news-publication-lifecycle.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


**Earlier October 5 independent evaluation and spatial coverage:** provider-separated independent auditing and immutable claim binding/leased evaluation are implemented locally using the approved tables. Explicit seed/evaluate commands preserve completed extraction and write no publication decisions, reports or zones. The same September 27 OSM snapshot now includes explicit C5 route relations, resolving 45 Pasig member ways into 14 ambiguous sections; this is road coverage, not verified flood extent. The bundled twenty-barangay OSM community catalog now supports Pasig locality previews including Ugong; full administrative coverage, operational footprints and automatic publication/expiry remain pending. [Current verification](evaluations/phase-36-independent-evaluation-and-spatial-coverage.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier local v11 placement follow-up:** locality aliases now validate barangay level and exact parent city; reviewed boundary catalogs clip supported road candidates; exact NOAH intersections preserve disconnected fragments with scenario/source identity. Spatial Operations uses the existing transparent review aura, with reported-depth severity and gray for unknown depth. No solid news core or public/routing write is introduced. Real reviewed barangay polygon provisioning and C5/Pasig catalog coverage remain pending. The constructed C. Raymundo probe yields 25 candidates/141 modeled fragments, with disconnected display geometry on 13 candidates; it does not confirm current flooding. [Disconnected placement verification](evaluations/phase-36-disconnected-news-placement.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Phase 36 current delivery:** independent evaluation, F5 previews, F6 staff exception controls and F7 source-alert visibility are implemented locally. The approved five-table storage supports atomic public alert/refresh/clearance/expiry decisions. Current operational flood footprints, linked-zone activation, broader asset coverage, duration prediction and deployment remain pending. [Lifecycle verification](evaluations/phase-36-news-publication-lifecycle.md).

**Local reviewed flood growth:** Spatial Operations suggests related evidence across barangays and nearby ongoing event zones. Admins explicitly choose extension, evidence-only linking or a separate event section; server-owned preview/publication preserves supported existing coverage and original evidence. Existing event locations and per-section zones handle multi-road/multi-barangay floods and differing conditions without a migration. News decisions/automatic publication remain pending. [Implementation and validation](evaluations/phase-36-needs-review-inspection.md#october-4-cross-boundary-growth-implementation).

**Latest local v9/v1.7:** complete four-article source/database re-audit preserves 38 sites and fixes source-depth precision, unspecified vehicle passability, road-homonym provinces and clearance labels. All 595 backend tests and 38 real API/proxy detail comparisons pass. Four new immutable runs preserve history; no schema/dependency or production change. Actual visual acceptance remains blocked. [Audit](evaluations/phase-36-four-article-source-audit.md). Earlier checkpoint statements below record verification history.

**Earlier local v8 checkpoint:** v8/v1.6 retains the September 24 results and adds the September 9 three-article replay with 33 readable sites, including 20 explicit caution records. Independent road facts, publisher corrections and visible retrieval failures are repaired; Flood Details renders server-owned passability. The pre-push regression run passes 555 tests spanning news, routing, depth, authorization and geometry, plus frontend TypeScript and scoped lint. Earlier local v5/v6 descriptions below are verification history. Production remains v4; final visual acceptance, freshness policy and automatic publication remain pending. [Workflow evidence](evaluations/phase-36-news-workflow-follow-up.md).

**Private local news testing delivered:** the September 24 historical replay is persisted in separate Docker database `lanes_news_test` and visible through the real authenticated News Intelligence page, detail/source and Collection. Loopback launchers load ignored database/JWT overrides while preserving cloud configuration. Local v6/v1.4 keeps city summaries as context where credible specific sites exist in the same city: five street cards, one article, two preserved versioned runs and no zones. City-only reports and distinct explicit observation times remain independent. All 224 related backend tests pass; no schema, dependency or API/UI contract change. Production v4 remains deployed. [Runbook](guides/local-news-replay.md).

This document serves as the central technical reference for all currently implemented and future planned functionality of the **LANES (Localised Alternative Navigation for Environs under Submersion)** platform. It maps high-level feature behaviors directly to the underlying frontend components, backend routers, databases, and algorithms.

**Local historical replay follow-up:** the real September 24 report exposed and corrected streamed article retrieval, road/city/PSGC attribution, hyphenated depths, cleared conditions, original clocks and qualifier/attention duplication. Five road sites pass the replay; 373 backend tests, 19 PostgreSQL policy and 11 real-claim parity checks pass (one migration skip). v5/v1.3 remain local and undeployed; affected extents and the original automatic placement/publication integration remain pending. [Evidence](evaluations/phase-36-september24-historical-replay.md).

**Phase 36 strict collection follow-up released:** actual-flood admission requires readable, affirmative Metro Manila body evidence. New unreadable leads remain diagnostics; legacy unsupported articles remain in an explicit excluded-history filter outside default attention. Forecasts, simulations, drills, habitual descriptions and caption-only artifacts cannot qualify. Matching v4 API/collector/Firebase releases pass 341 backend tests, 15 PostgreSQL checks and 15 deployed desktop/mobile cases (API/session mocked). Ten new runs preserve all 30 prior runs; all 24 legacy articles are excluded. [Evidence](evaluations/phase-36-news-content-quality-investigation.md#v4-backend-release-verification).

**Phase 36 monitoring/content release:** Sources & feeds Pipeline supplies saved body totals, newest extraction statuses, ten retrieval issues and paginated discovery/fallback histories through protected GET APIs. Approved revision `c5a7e9d2104f` is tested/applied locally and in production. Matching API/collector/Firebase releases and 13 deployed desktop/mobile asset checks pass (API/session mocked). Shared evidence/Metro Manila screening excludes the nine known false cards; ten corrected runs preserve all source/history. Refresh performs no collection or lookup. Publication-delay telemetry awaits the lifecycle contract; developer visual acceptance remains open. See [release evidence](evaluations/phase-36-news-content-quality-investigation.md#completed-production-release).

---

## 🛠️ Feature Reference (Current and Planned)

### 1. Bilingual Taglish NLP Ingestion, Multi-Tier Hybrid Ensemble & Smart Auto-Activation
*   **Local v10 placement evidence:** shared captured extraction adds exact NOAH vector overlaps and section-matched Pasig DRRMO rows with source identity, alternatives and explicit unavailable evidence. A protected no-write GET supplies the locally implemented F5 map inspection. Immutable analytical assets are separate from the raster overlay. All 550 distinct checks pass (one skip); existing JSONB is reused. Public alerts/zones, independent-auditor integration and production release remain pending. Section 7 describes the subsequently implemented staff inspection UI. [Verification](evaluations/phase-36-backend-placement-preview.md).
*   **Runtime OSM dependency:** Catalog placement uses pure graph/geometry routines without loading `osmium`; the native import/handler is confined to `load_bounded_osm_roads` for raw-PBF tools. 140 focused checks pass after this isolation. Raw-PBF parsing remains subject to the local Windows signing-policy restriction; no dependency, schema or automatic-publication behavior changed. See [verification](evaluations/phase-36-automatic-plan-alignment-audit.md#verification-recovery-runtime-dependency-isolation).
*   **Priority 5 F1/F2 verification history:** Earlier saved-article browsing passed isolated tests and live local desktop/mobile checks after Docker recovery and the approved existing extraction migration. The article-first presentation is superseded by the unified design below. Original evidence remains in [F2 verification](evaluations/phase-36-f2-article-browsing-check.md). No production rollout or public-state activation is claimed.
*   **Current Priority 5 reading UI — manual acceptance pending:** `/admin/news` has one Flood Locations list. Specific reported intersections/segments lead cards; Info contains Flood Details and Source Article. Flood observation, publication and original LANES-save clocks remain distinct. Collection status preserves failed, empty and questionable articles. Source Article retains captured versions and processing history; collection inspection keeps history under More details. Backend SQL selects each article's newest recorded run and screens sentence-like names, unsupported place-only mentions, forecast/negated/historical statements and incomplete results. This reading gate does not verify map placement or alter lifecycle decisions. Forty-nine backend checks, TypeScript/lint, PostgreSQL summary agreement and seven PostgreSQL predicate cases pass with zero stored writes. No browser or development server was started; developer desktop/mobile acceptance remains pending. F4a publisher/feed configuration and saved checkpoints are now accessible through Sources & feeds. F4b durable discovery/fallback history is implemented; publication-delay telemetry and durable news decisions remain open; combined Spatial Operations inspection is locally implemented. See [verification](evaluations/phase-36-f3-result-browsing-check.md).
*   **Deployed Priority 4 placement:** Saved/discovered extraction attaches typed `road_placement` evidence from a server-owned, checksum-identified NCR OSM catalog. Explicit spans can yield a unique bounded centerline; road-name-only, incomplete-way, missing-barangay, and competing-path cases retain uncertainty. Catalog refresh creates new versioned results. Production verified ten enriched backlog artifacts without duplicates/public writes and the actual historical GMA 86.2 m span; no geometry is promoted to verified live flood extent or routing closure. See [release evaluation](evaluations/phase-36-reusable-road-match-check.md#production-release-verification). Publication/review/correction/expiry is next; fresh current incident acceptance remains open.
*   **Latest Info layout:** Flood Details shows flood facts and evidence. Source Article alone displays processing history: desktop has independently scrolling article/timeline panes in a wide shared dialog, while mobile switches between Article and Processing history within Source Article. The article uses compact publication/save metadata, larger headline typography and full text open by default. The secondary history pane contains only status, date, attempt/mention counts and a View details action. Detailed saved records open full-width with Mentions / Article / Technical tabs and Back; article/history state stays mounted for return. Shared RecordTimeline also renders Flood History's incident timeline. This frontend-only refinement passes TypeScript/lint; developer visual acceptance remains pending. Collection article history stays under More details. F4a adds the Sources & feeds drawer using existing source configuration and saved checkpoint reads; durable discovery/fallback history is now available, while publication delay remains unavailable. The developer accepted the revised F3 design; full manual checks remain pending.
*   **Current sequencing:** Priority 3 durable rules extraction is deployed and verified on ten saved RSS-linked bodies; repeated processing creates no duplicates. Priority 2 fresh live positive matching, verified geometry, incident grouping, and public-zone integration remain open. Production migration `f29b6c8d104e`, runtime reference checksums, and API health checks pass. The collector runs `--discover --process --limit 50`. The local-status descriptions below are pre-release history; see the [production release](evaluations/phase-36-open-article-fallback-check.md#production-extraction-release--october-2).
*   **Purpose:** Automatically discover and structure flood evidence across the Philippines, starting with current Metro Manila source/analytical coverage. Local OSM/NOAH/Pasig DRRMO previews assist placement; eligible automatic alerts/zones are the intended publication path. F5 inspection, independent audit, durable source-alert publication/correction/expiry and F6/F7 source-alert interfaces are implemented locally; verified operational geometry, routing-zone activation and deployment remain unfinished. Staff handles exceptions; routine eligible news claims bypass approval.
*   **Policy-text evidence guard (local Priority 2 repair):** Flood-control program/project phrases alone no longer create flood observations. Shared extraction preserves genuine measured flooding in mixed-topic articles, excludes administrative clauses and project dimensions, and retains source text/offsets. Thirteen focused cases and 207 combined regressions pass. One real manually selected Philstar administrative article yielded no qualifying flood observation. Live automatically discovered positive matching and rollout remain open.
*   **Earlier discovery implementation baseline:** News discovery is scheduled and stores pending article evidence. Current source prioritizes Metro Manila RSS place clues and probes up to five additional flood articles per run for body-grounded local claims. Run notices expose unresolved scope and limits; the revised filter is not deployed. The runtime feed registry is narrowed to six verified feeds (GMA News, Inquirer, Rappler, Philstar, BusinessWorld, Interaksyon), while candidate inventories remain in research documentation (`docs/plans/rss-news-discovery-plan.md`). Full-article fetching enforces a 100,000-character bound without silent truncation, isolates publisher story containers, excludes related-story widgets, rejects detected same-article continuations, and flags contradictory same-road clearing updates. A sampled [publisher audit](evaluations/phase-36-publisher-body-and-pagination-audit.md) found a Rappler rolling article that still links onward after page 32 and Inquirer article-page Cloudflare challenges; both remain incomplete leads. A 51-site expected-facts fixture previously matched 27/27 Philstar, 16/16 PNA August 17, and 8/8 PNA August 8 sites in [source evaluations](evaluations/phase-36-three-article-check.md); the current Philstar replay still matches, while both current PNA requests return HTTP 500 and those historical results cannot yet be refreshed. Explicit `as of` observation clocks can now resolve to Asia/Manila within a bounded publication-time window. One [read-only road-span audit](evaluations/phase-36-sto-domingo-road-span-audit.md) found a bounded OSM candidate for a historical GMA report and intersected it with NOAH polygons; this does not verify geometry for automatic placement. Nationwide deterministic extraction code, geometry ranking, optional LLM auditing, and zone creation exist as separate source-code prototypes. The collector does not invoke `NewsAutoIngestionService`; staff review and broader real-article validation are incomplete.
    1. **Tier 1 (Lead Extractor):** Local deterministic Taglish rules and 43,778 official PSA PSGC records (`philippine_location_service.py`) dynamically resolve places, depth gauges (`gutter`..`neck`), and active conditions in sub-millisecond execution with zero hardcoded place lists.
    2. **Planned tiers:** `calamanCy` Tagalog NER and Google Cloud Natural Language API were evaluated in the plan but are not integrated in the runtime pipeline.
    3. **Supporting auditor prototype:** `hybrid_extraction_service.py` can call an OpenRouter Gemini model for candidate checks. Missing credentials or a failed request uses unconfirmed deterministic classification and sends active claims to staff review.
    4. **Zone creation prototype:** `NewsAutoIngestionService` contains dormant report/event/zone creation code and independently reevaluates a claim's auditor, observation time, status, and geometry before a public write. Automatic creation is allowed when every gate passes; the current geometry provider never yields a verified affected segment, so no news zone is generated yet. The former post-decision 98% score was removed; place-ranking scores are not calibrated approval probabilities. See [activation safety contract](plans/news-activation-safety-gates.md).
    5. **Suppression prototype:** Rule and auditor classifications can suppress detected subsided, forecast, and negated claims in focused tests; broader real-article evaluation is pending.
*   **Metro Manila rollout:** Nationwide PSGC extraction and place-hierarchy code remains in the repository as completed historical work, but the active RSS discovery, article evaluation, UP NOAH hazard integration, spatial prediction, and news-derived map-zone rollout strictly target Metro Manila (including Pasig City). `NationwideGeometryService` can generate suggested road or point buffers. The 726-row Pasig history is a ranking prior with no coordinates; LiPAD/UP NOAH hazard layers are not yet integrated. The [spatial data plan](plans/lipad-noah-flood-placement.md) uses the [NOAH data lead](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps) found through DavFlood. Current geometry is not production-validated.
*   **Blocked article fallback:** Protected staff lookups use the free GDELT index, optionally search by Metro Manila place and publication-date window, and can fetch up to three approved alternate publisher bodies for same-event review. If the index supplies no approved alternate, recent originals can use independent approved-publisher feeds with flood/place and publication-date filters. Alternate event-review notes compare specific places, city-qualified roads, publication/observation dates, depth/status differences, and duplicate body fingerprints. Overlap remains unverified and copied bodies cannot establish independence. Index metadata, feed publication timestamps, and alternate bodies stay separate from the stored original; this does not activate flood zones. GDELT has dedicated 15-second connect / 20-second read budgets, per-process pacing, bounded caching, and provider cooldowns. Live automatic recovery, shared coordination across replicas, and automatic matching remain open; see the [fallback evaluation](evaluations/phase-36-open-article-fallback-check.md). The implementation stays in the existing FastAPI backend (`news_open_search_service.py`), with no new deployed service, schema, or dependency.
*   **Access & Roles:** Staff have protected source and pending-candidate endpoints. A dedicated AI claim review and correction interface is still planned.
*   **Saved extraction (deployed Priority 3):** Read-only previews remain available. Approved immutable `news_article_versions` and version-keyed `news_extraction_runs` preserve exact evidence/results and enforce idempotency. The worker uses short PostgreSQL SKIP LOCKED claims, five-minute token-owned leases, bounded five-attempt retries, and safe failure states. RSS/manual persistence enqueues valid pending inputs; staff GET/POST processing APIs and `--process-saved` / `--discover --process` handle work independently of restart/304. No external auditor, public ingestion, or moderation change is performed. Production migration and reference-file checks pass; ten stored artifacts contain 50 source-linked candidate claims. Repeated processing creates no duplicates or public writes. The release rerun passes 28 focused tests; fresh discovery acceptance remains open.
*   **Observation updates (local Priority 2 follow-up):** Alternate review compares city-qualified road observation time/depth/status/clearance. Older evidence cannot supersede newer observations; simultaneous disagreements, segment ambiguity, incomplete evidence, and recurrence remain unresolved. Same-URL publication revisions refresh bodies, preserving successful body/date on failure and preventing activation of retained errored text. Comparisons remain unverified proposals. Live matching and rollout remain open; grouping and existing-zone updates are later integration work. Priority 3 extraction persistence is now approved and implemented locally.
*   **Related Components:**
    *   **Frontend:** [FloodReportPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx) (for manual text submission and incident reporting).
    *   **Backend:** [reports.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/reports.py) handles manual reports; `admin_news.py` and `news_discovery_service.py` handle RSS evidence. Core NLP and geometry services: [`hybrid_extraction_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/hybrid_extraction_service.py), [`nationwide_geometry_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/nationwide_geometry_service.py), [`news_auto_ingestion_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/news_auto_ingestion_service.py), [`philippine_location_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/philippine_location_service.py), and [`taglish_extraction_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/taglish_extraction_service.py). Detailed plan: [`docs/plans/smart-auto-activation-and-hybrid-nlp-plan.md`](file:///d:/Documents/Github/LANES/docs/plans/smart-auto-activation-and-hybrid-nlp-plan.md).

---

### 2. Structured Flood Incident Survey & Automated Reverse-Geocoding (3NF Normalized)
*   **Purpose:** Collects precise, structured data about flood scenarios directly from ground users while automatically resolving spatial street, barangay, and city attributes without requiring manual text input.
*   **What it does:** Allows users to fill out categorical passability surveys (e.g., Hidden hazards, Passable vehicles) and mark road segments on the map. The backend automatically extracts topological midpoints and performs structured reverse geocoding to persist verified street, barangay, and city records.
*   **How it works:** 
    1. Replaces standard text fields with responsive UI chips and toggle groups within `FloodReportPanel.tsx`.
    2. When road segments (`LineString`/`MultiLineString`) or points are submitted, the backend (`report_service.py`) calculates the representative midpoint coordinate and queries a multi-provider reverse geocoding engine (Nominatim with Photon fallback in `geocoding_service.py`).
    3. Address components are cleaned and parsed into normalized attributes: `human_readable_location` (street/road), `barangay`, and `city` (persisted to `flood_reports` with dedicated PostGIS indices).
    4. Survey responses map directly to a dedicated `flood_report_surveys` table holding a strict foreign key to the root report, ensuring full Third Normal Form (3NF) relational integrity.
*   **Access & Roles:** Public users can submit surveys; DRRM officers review them.
*   **Related Components:**
    *   **Frontend:** [FloodReportPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx), [ReportDetailsModal.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/ReportDetailsModal.tsx), [PendingReportsPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/PendingReportsPanel.tsx).
    *   **Backend:** [report.py](file:///d:/Documents/Github/LANES/backend/app/models/report.py), [report_service.py](file:///d:/Documents/Github/LANES/backend/app/services/report_service.py), [geocoding_service.py](file:///d:/Documents/Github/LANES/backend/app/services/geocoding_service.py), `POST /api/v1/reports` endpoint.

---

### 3. Identity-First Citizen Onboarding & Zero-Click OTP Verification
*   **Purpose:** Provides a seamless, identity-first registration wizard with secure email validation, spam resistance, network-latency resilience, and instant verification.
*   **What it does:** Breaks registration into an Identity-First sequence (`Email -> OTP -> Account Credentials -> Personal Profile -> Demographic Address`). Delivers zero-click automatic verification as soon as 6 digits are entered, while managing progressive resend cooldowns and sliding grace windows.
*   **How it works:**
    1. **Identity-First Stage:** User submits their email address first. The backend verifies uniqueness and dispatches a 6-digit OTP via the Resend REST API (from `Lanes <noreply@navlanes.live>`) using a crisp, zero-attachment CDN brand seal.
    2. **Progressive Rate Limiting & Cooldowns:** Enforces progressive resend cooldown tiers (**1 minute** -> **3 minutes** -> **5 minutes**) to prevent gateway spamming while providing ample time to check inbox/spam folders.
    3. **Sliding Grace Window for Network Latency:** Retains up to **3 unexpired active codes** (5-minute lifetime) per session. If a delayed email arrives after a resend, entering the older code still succeeds. All codes are purged immediately upon verification.
    4. **Zero-Click Verification & Attempt Throttling:** 6 distinct pin boxes auto-advance, handle paste events, and automatically fire verification when the 6th digit is entered. Wrong attempts auto-clear and refocus with remaining attempt warnings; exceeding 5 failed attempts locks verification for 5 minutes.
    5. **Demographic & Address Profile:** Upon verification, the user sets their username/password, completes their profile, and selects Province -> City -> Barangay using live PSGC API data.
    6. **Explicit Login Redirection:** Successfully creating the account clears pending registration drafts and redirects to the login page (`/login?registered=true`), displaying a green notification banner informing the citizen of account creation and prompting explicit credential authentication.
*   **Access & Roles:** Public users.
*   **Related Components:**
    *   **Frontend:** [RegisterForm.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/auth/components/RegisterForm.tsx), [DatePicker.tsx](file:///d:/Documents/Github/LANES/frontend/src/shared/ui/DatePicker.tsx), [LocationPickerModal.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/auth/components/LocationPickerModal.tsx).
    *   **Backend:** [auth.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/auth.py), [auth_service.py](file:///d:/Documents/Github/LANES/backend/app/services/auth_service.py), [crud/otp.py](file:///d:/Documents/Github/LANES/backend/app/crud/otp.py), [email_service.py](file:///d:/Documents/Github/LANES/backend/app/services/email_service.py).

---

### 4. Flood-Adaptive Route Calculation & Rerouting
*   **Purpose:** Ensures commuter safety by dynamically routing vehicles around active flood hazards.
*   **What it does:** Calculates optimal navigation paths between origin and destination coordinates, ensuring that any road segments intersecting active flood zones are bypassed, and visualizes alternative detours and turn-by-turn maneuvers directly on the map.
*   **How it works:**
    1. When a user requests a route, the backend fetches all active avoidance polygons (Red, Orange, Yellow) from the PostGIS database.
    2. The routing service queries the private **Valhalla** Cloud Run engine using an authenticated, dynamically built HTTP request; availability failures transparently retry through OpenRouteService and identify the backup result to the user.
    3. The avoidance polygons are passed natively into Valhalla's `avoid_polygons` parameter.
    4. The routing algorithm mathematically treats the polygons as impassable barriers, generating a safe alternative detour route. If trapped, it falls back to allowing Yellow zones, then Orange zones.
    5. The commuter can toggle "Ignore Floods" to compare the safe path against the default flooded route.
    6. **Resilient Map Hydration & Style Persistence:** In `MapCanvas.tsx`, route polylines are added checking `map.getStyle()` with persistent `map.on("style.load")` listeners, ensuring routes never drop out during background tile fetches or 3D terrain toggles. When crossing floods, dynamic `"line-gradient"` interpolation indicates hazard approach; clear routes use reliable native `"line-color": "#2563eb"`.
    7. **Auto-Framing Camera (`fitBounds`):** Automatically zooms and frames the full route geometry and terminal markers with responsive padding (offsetting desktop left panels and mobile bottom sheets).
    8. **Sequential Saved Places Recalculation:** Authenticated commuters can tap saved place quick chips to sequentially assign Start and Destination, automatically firing routing without manual field clearing.
*   **Access & Roles:** Open to all public commuters.
*   **Related Components:**
    *   **Frontend:** [RoutePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/routing/RoutePanel.tsx) (input panels, turn-by-turn lists, flood toggle, saved places chips), [MapCanvas.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapCanvas.tsx) (route line rendering, camera fitBounds), [GlobalMap.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/GlobalMap.tsx).
    *   **Backend:** [reports.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/reports.py) and [routes.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/routes.py) router (`POST /api/v1/reports/route`), [routing.py](file:///d:/Documents/Github/LANES/backend/app/services/routing.py) service (`calculate_flood_safe_route`).

---

### 5. Dynamic AI Weather Insights
*   **Purpose:** Helps everyday users understand raw meteorological data (PoP%, mm/h) by converting it into simple, educational interpretations.
*   **What it does:** Provides a completely automated, on-demand AI explanation of the next 4 hours of weather data via a dedicated modal on the homepage.
*   **How it works:**
    1. The frontend parses the 12-hour forecast array from Open-Meteo.
    2. The user clicks "Generate AI Insights" in the Weather Modal.
    3. The backend compiles the first 4 hours of data into a highly constrained system prompt, commanding the AI to act as a "teacher."
    4. The server securely calls the **OpenRouter API** (`openrouter/free` model routing) to avoid costs while maintaining dynamic NLP generation.
    5. The AI returns a strict JSON object containing short interpretations of both Storm Risk and Environmental Conditions, which is rendered dynamically in the UI.
*   **Access & Roles:** Public users.
*   **Related Components:**
    *   **Frontend:** [WeatherInsightsModal.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/landing/WeatherInsightsModal.tsx).
    *   **Backend:** [weather.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/weather.py) (`POST /api/v1/weather/insights`).

---

### 6. Height-Aware Rerouting (Dynamic Vehicle Profiles)
*   **Purpose:** Customizes detour calculations based on vehicle clearance constraints (e.g., Pedestrian, Motorcycle, Sedan, SUV).
*   **What it does:** Allows commuters to select their vehicle profile and intelligently decides which flood polygons to avoid. High-clearance vehicles (SUVs) can safely cross knee-deep water (Yellow/Orange) but incur a 35% safety penalty to account for hidden hazards, while low-clearance vehicles (Sedans) are completely blocked.
*   **How it works:**
    1. Commuters select their vehicle profile in the route panel.
    2. The backend dynamically builds avoidance polygons by analyzing the `blocked` vs `penalized` zones based on the specific vehicle type.
    3. The 8 MMDA visual severity options (Gutter, Half-Knee, Tire, etc.) are mapped to exact routing logic penalties.
*   **Access & Roles:** Open to all public commuters.
*   **Related Components:**
    *   **Frontend:** [RoutePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/routing/RoutePanel.tsx), [routingOptions.ts](file:///d:/Documents/Github/LANES/frontend/src/features/routing/routingOptions.ts).
    *   **Backend:** [reports.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/reports.py) router, [routing.py](file:///d:/Documents/Github/LANES/backend/app/services/routing.py) service (`calculate_flood_safe_route`).

---

### 7. Spatial Operations & Queue-Based Admin Moderation Workflow

*   **Primary Panel refinement (local):** Search and city/barangay/severity filters are server-owned and run before card pagination, retaining full related groups. Cards summarize actual roads/areas and mixed conditions; reports, active zones and contributors reuse the flat `FloodRecordSummary` presentation with compact desktop/touch-aware actions. Source styling, own-record moderation and reviewed merge semantics remain. [Verification](evaluations/phase-36-needs-review-inspection.md#october-4-primary-panel-search-and-detail-consistency).
*   **Purpose:** Implements a "human-in-the-loop" validation workflow to prevent automated NLP ingestion errors or mapping hallucinations from misdirecting drivers.
*   **What it does:** Needs Review combines pending user reports and current news exceptions in Spatial Operations, with All/User Reports/News Claims filters. User reports retain staff moderation; news evidence and dashed placement suggestions are currently inspection-only. Fully eligible news claims retain the intended automatic publication path once its backend lifecycle is connected.
*   **Queue presentation:** Light blue user cards group pairwise related reports within two hours: up to 500 m on the same road/city, or 50 m across roads/cities; barangay boundaries alone do not exclude review; opening a card shows the related list inside report details, retaining each report's evidence, severity, depth and actions without a queue dropdown. Light violet news cards retain individual claim identity. Grouping is server-owned display organization, with member pagination and separate report/card counts; actual merging still requires the existing explicit review workflow.
*   **How it works:**
    1. Newly parsed reports are inserted with a status of `pending`.
    2. DRRM operators inspect source-specific evidence within the map workspace. User-report actions remain available; news exceptions show missing/conflicting evidence and bounded OSM/NOAH/Pasig history suggestions without approval/publication controls in this delivery. Selecting a report or candidate is neutral; it never forces a merge or activates a zone.
    3. When an operator explicitly selects **Review Merge Suggestions**, the system opens the four-stage merge workspace. Candidates remain unselected until the operator checks them, and each card keeps its score and supporting evidence with that report.
    4. In the merge workspace, operators choose extension, evidence-only linking, or a separate section of the same event. The secured coverage preview buffers reviewed road lines in projected metres (25 m default; validated 1–100 m), accepts valid drawn polygons, and retains existing coverage/core during extension. Evidence-only linking preserves boundary/conditions; separate sections keep their own conditions. Points or disconnected combined coverage cannot be published through this reviewed merge path.
    5. This buffer is saved to the `flood_avoidance_zones` table as an active polygon, which immediately updates Valhalla route requests.
    6. Discarded reports are marked as `rejected`.
*   **Access & Roles:** Restricted to `admin` / `drrm` roles.
*   **Related Components:**
    *   **Frontend:** [LiveMapPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/LiveMapPage.tsx) (Spatial Operations map), [PendingReportsPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/PendingReportsPanel.tsx), [ActiveZonesPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/ActiveZonesPanel.tsx).
    *   **Backend:** [admin.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py) endpoints (`/reports/pending`, `/reports/{report_id}/approve`, `/reports/{report_id}/reject`).

---

### 8. Interactive Spatial Map Visualization (WebGL Tiles & Autocomplete)
*   **Purpose:** Renders real-time hazard layers, detour vectors, and geocoding on a performant mobile canvas.
*   **What it does:** Displays an interactive street map overlaying color-coded pins (White, Yellow, Orange, Red) for flood heights, outlines avoidance zone shapes, and handles address geocoding search.
*   **How it works:**
    1. Utilizes **MapLibre GL JS v5** to render vector maps on the client side using WebGL, fully supporting 3D Terrain (`setTerrain`) via AWS Terrarium DEM tiles and a custom `atmosphere` sky layer.
    2. Feeds MapTiler and OpenStreetMap tiles for dynamic base imagery, controllable via a floating `MapStylePickerControl` with 5 selectable modes (Streets, Dark, Roads, Satellite, OpenStreetMap) and a `Toggle3DControl` to disable building extrusions in 2D mode.
    3. Integrates the **Komoot Photon API** (`photon.komoot.io`) for geocoding search, localized and scored specifically for Pasig City bounds to provide relevant location autocomplete results.
    4. Renders geo-coordinates as visual icons and polygon vectors in real time, employing zoom-based shader opacity step expressions (rather than layer culling) to guarantee seamless visibility during extreme 3D pitch angles.
*   **Access & Roles:** Public commuters and system administrators.
*   **Related Components:**
    *   **Frontend:** [MapCanvas.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapCanvas.tsx), [MapContext.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapContext.tsx), [geocodingApi.ts](file:///d:/Documents/Github/LANES/frontend/src/features/geocoding/geocodingApi.ts).

---

### 9. Real-Time Event Signaling (Server-Sent Events)
*   **Purpose:** Ensures instant, reactive visual updates across commuter and admin maps without forcing manual browser refreshes.
*   **What it does:** Signals active database events (approvals, deactivations, database cleans) from the backend directly to active frontend sessions.
*   **How it works:**
    1. The React app connects to a native `EventSource` on the FastAPI server at `/api/v1/sse/stream`.
    2. The backend maintains an active connection manager mapping open client streams.
    3. When an admin approves a report or deactivates a zone, the server broadcasts an event (e.g. `report_approved`).
    4. The frontend intercepts the payload and automatically invalidates the React Query cache, triggering a silent background refetch of map layers.
*   **Access & Roles:** Public clients and administrative dashboards.
*   **Related Components:**
    *   **Frontend:** [useSSE.ts](file:///d:/Documents/Github/LANES/frontend/src/hooks/useSSE.ts), `providers.tsx`.
    *   **Backend:** [sse.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/sse.py), `app.core.sse`.

---

### 10. Role-Based Access Control (RBAC) & JWT Security
*   **Purpose:** Secures sensitive admin interfaces, settings, and database endpoints from public modifications.
*   **What it does:** Separates authorization levels between `commuters` and `admin` / `drrm` profiles, enforcing login parameters and auditing.
*   **How it works:**
    1. Hashes passwords using **bcrypt** with adaptive salt rounds before database storage.
    2. Issues signed **JSON Web Tokens (JWT)** via `python-jose` containing the user ID and role during login.
    3. FastAPI route handlers intercept calls using dependency injection (`get_current_active_admin`) to validate JWT signatures and enforce permissions.
*   **Access & Roles:** Registration is open to all; admin pages require role-checks.
*   **Related Components:**
    *   **Frontend:** [LoginForm.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/auth/LoginForm.tsx), [SignupForm.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/auth/SignupForm.tsx).
    *   **Backend:** [auth.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/auth.py), [users.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/users.py), [deps.py](file:///d:/Documents/Github/LANES/backend/app/api/deps.py).

---

### 11. Offline Resiliency & True Offline Routing (PWA)
  *   **Purpose:** Ensures mobility tool usability and intelligent flood detouring when mobile networks fail during severe typhoons.
  *   **What it does:** Runs a full routing engine client-side, caching map graphs, assets, and active flood polygons locally.
  *   **How it works:**
      1. Operates as a Progressive Web App using `@ducanh2912/next-pwa` service workers.
      2. Caches Valhalla `.tar` routing graphs and offline vector tiles into IndexedDB and the Origin Private File System (OPFS).
      3. Uses a background Web Worker (`valhallaCore.ts`) to execute the Valhalla WebAssembly binary off the main thread, dynamically mounting the Emscripten filesystem to the `.tar` tile data.
      4. Listens to Server-Sent Events (SSE) while online to instantly cache active `FloodAvoidanceZone` geometries to IndexedDB.
      5. Automatically falls back to offline routing when `navigator.onLine` toggles off, computing detours using the locally cached polygons.
*   **Access & Roles:** Public commuters.
*   **Related Components:**
    *   **Frontend:** [OfflineBanner.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/offline/OfflineBanner.tsx), `frontend/package.json`.

---

### 12. System Audit Logging & Trail
*   **Purpose:** Maintains organizational transparency and logs all administrative updates to prevent accidental or malicious map changes.
*   **What it does:** Logs admin actions (report approval, rejection, user deletion, backups, data clears, configurations) to a central ledger.
*   **How it works:**
    1. Every admin-restricted route wraps its database transaction with an `audit_log` write operation.
    2. Saves details including `admin_id`, `action_type`, `target_table`, `metadata_json` (containing changes details), `ip_address`, and a UTC timestamp.
*   **Access & Roles:** Admins can view this ledger.
*   **Related Components:**
    *   **Frontend:** [AuditTrailPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/AuditTrailPage.tsx).
    *   **Backend:** [admin.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py) (`/audit-logs`), [audit.py](file:///d:/Documents/Github/LANES/backend/app/models/audit.py) schema & models.

---

### 13. Database Backup, Exports & Cleanup Management
*   **Purpose:** Protects database integrity, enables archival, and exports research data.
*   **What it does:** Creates and restores SQL dumps of the PostgreSQL/PostGIS database, exports reports/avoidance zones as CSV or JSON, and implements records cleaning.
*   **How it works:**
    1. Exports query database tables using standard Python `csv` and `json` libraries.
    2. Backup calls trigger shell processes (`docker exec` executing `pg_dump` and `pg_restore`) to compress or import dump files.
    3. Cleanup sweeps database tables, purging old flood incident logs and zones older than user-specified date ranges.
*   **Access & Roles:** Limited to admins.
*   **Related Components:**
    *   **Frontend:** [DataManagementPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/DataManagementPage.tsx).
    *   **Backend:** [data.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/data.py), [data_service.py](file:///d:/Documents/Github/LANES/backend/app/services/data_service.py).

---

### 14. Cloudinary Photo Evidence Upload & Edge Compression
*   **Purpose:** Allows commuters to submit visual proof of flood hazards and community posts, while minimizing server memory overhead and saving mobile bandwidth.
*   **What it does:** Uploads user-provided media alongside the text report, securely hosts it, and displays it in the feed. Large files are aggressively optimized.
*   **How it works:**
    1. The frontend uses `browser-image-compression` to resize images (max 1200px) and converts them to `WebP` before network transmission, vastly reducing mobile data costs.
    2. A strict 20MB payload limit is enforced on the frontend UI and the FastAPI backend (via `Content-Length` interception) to prevent malicious massive uploads.
    3. The FastAPI backend streams the file to **Cloudinary** via their Python SDK.
    4. Cloudinary automatically transcodes the delivery format (`f_auto`) and quality (`q_auto`), serving optimal formats like AV1 or WebP based on the viewer's browser.
    5. The resulting CDN URL is saved as `image_url` or `media_urls` in the PostgreSQL database.
*   **Access & Roles:** Public users can upload; administrators and peers can view.
*   **Related Components:**
    *   **Frontend:** [FloodReportPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx), [CreatePostModal.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/feed/CreatePostModal.tsx).
    *   **Backend:** [cloudinary_service.py](file:///d:/Documents/Github/LANES/backend/app/services/cloudinary_service.py), [reports.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/reports.py), [posts.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/posts.py).

---

### 15. Archive Center (Soft Deletes)
*   **Purpose:** Centralizes the management of suspended user accounts, rejected flood reports, and deactivated zones without destroying relational data integrity.
*   **What it does:** Uses `deleted_at` timestamps to hide records from active queries while retaining them for historical analytics and administrative audit trails.
*   **How it works:**
    1. Instead of a SQL `DELETE`, a record is updated with `deleted_at = NOW()`.
    2. Active database queries filter with `WHERE deleted_at IS NULL`.
    3. The Archive Center provides a dual-pane or vertical sidebar interface to browse these hidden records.
*   **Access & Roles:** Restricted to `admin` / `drrm` roles.
*   **Related Components:**
    *   **Frontend:** `src/features/archive/` (Components), `src/app/(admin)/archive/page.tsx`.

---

### 16. Community Feed & Social Validation
*   **Purpose:** Provides commuters with localized, real-time crowdsourced updates, general disaster discussion, and enables peer validation of flood reports.
*   **What it does:** Displays a 3-column feed containing shared `FloodReport`s and general `CommunityPost`s. Enables highly interactive community discussions via a rich, threaded comments section supporting quote replies, user mentions, upvote/downvote sorting, auto-collapsing low-score replies, and admin pinning.
*   **How it works:**
    1. Fetches feed items using PostGIS `<->` operators for distance-based sorting or chronological ordering.
    2. Users interact via upvote/downvote and comments, which updates the `post_interactions` and `comments` tables.
    3. The Comment Engine structures threads recursively in the backend, supporting infinite nesting via adjacency lists (`parent_comment_id`).
    4. The frontend utilizes React `useRef` based focus-within compound input forms to safely manage complex multi-input layouts without triggering React re-renders or cursor jumping.
    5. Interaction events (Likes, Mentions, Replies) trigger real-time `Notification` rows stored in the database for the post author, accessible via the global Bell icon.
    6. **Post Geolocation & Map Fly-to:** Community posts support tagged coordinates (`location_lat`, `location_lng`). When published, the header displays a clickable red pin badge that navigates directly to `/map`, uses container `ResizeObserver` alignment to center coordinates within the desktop visible area (compensating for the 340px routing panel), and focuses the camera with a 3-second pulsing red indicator.
    7. **Persistent Post Drafting (IndexedDB):** Prevents accidental data loss when users navigate away from the post creation modal or lose connection. Text content is persisted in `sessionStorage`, while heavy media binary blobs (images/videos) are serialized into the browser's native **IndexedDB** via `idb-keyval`, reconstructing them safely back into JavaScript `File` objects and object URLs on remount.
    8. **100MB Multi-format Media Uploads & Video Streaming:** Supports photo and video attachments up to 100MB per file with Next.js proxy client size configuration (`experimental.proxyClientMaxBodySize: '100mb'`), FastAPI multipart handling, dynamic Cloudinary resource classification (`resource_type="video"`), and detailed user error toasts specifying exact file size versus system limits on rejection.
*   **Access & Roles:** Public users can post and reply. Admins and Authors can Pin comments.
*   **Related Components:**
    *   **Frontend:** `src/features/feed/` ([PostItem.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/feed/PostItem.tsx), [CreatePostModal.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/feed/CreatePostModal.tsx)), [MapCanvas.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapCanvas.tsx), [BaseMap.tsx](file:///d:/Documents/Github/LANES/frontend/src/shared/ui/BaseMap.tsx), `src/features/notifications/` (NotificationDropdown).
    *   **Backend:** [posts.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/posts.py), [post.py](file:///d:/Documents/Github/LANES/backend/app/crud/post.py), [models/post.py](file:///d:/Documents/Github/LANES/backend/app/models/post.py).

---

### 17. Intelligent Bidirectional Flood Reporting (Hybrid Carriageway Detection Strategy)
*   **Purpose:** Accurately models road-segment submersion along divided boulevards, dual carriageways (e.g., C-5, Ortigas Ave, Shaw Blvd), and narrow two-way streets without erroneously blocking oncoming lanes or under-reporting flooded dual lanes.
*   **What it does:** Dynamically inspects the OpenStreetMap/Valhalla road network graph at report creation. When a user reports a bidirectional flood on a divided carriageway, it identifies both opposing highway lines, validates street naming consistency to prevent false positives across unrelated alleys, and generates a unified multi-geometry avoidance zone.
*   **How it works:**
    1. **Authoritative Pre-Submission Preview:** `POST /api/v1/reports/preview-bidirectional` receives raw Start/End anchors, evaluates both route directions, rejects legal-driving loops, and returns road-only snapped original/optional counterpart coverage. Raw clicks never become geometry vertices; preview pins move to the returned road endpoints and the same coverage is rebuilt before persistence.
    2. **Road-Run Classification Engine:** Uses Valhalla edge shape indexes to split a mixed route wherever its road identity or traversability changes, then classifies every run independently:
       - `NARROW_TWO_WAY`: Single physical pavement with two-way traffic flow; standard directional buffering applies.
       - `DIVIDED_CARRIAGEWAY`: Physically separated dual carriageways requiring paired opposite-lane discovery.
       - `TRUE_ONE_WAY`: Confirmed single-direction street with no counterpart.
       - `AMBIGUOUS`: Mixed road topology or an excessive route detour; conservative single-line coverage applies.
       - `UNMAPPED`: Segment outside graph coverage.
    3. **Two-Sided Dynamic Perpendicular Probe:** For one-way candidates, searches left and right at 5m, 10m, 15m, 20m, and 30m so anchor direction cannot force the search onto the wrong side.
    4. **Counterpart Validation Firewall:** Requires matching normalized road identity and class, distinct OSM way IDs, opposing direction, comparable length, parallel alignment, sufficient longitudinal overlap, and 4–35m lateral separation before accepting a second carriageway. For a mixed route only, the service may retain a 50%+ verified parallel subsection using a 3.5m quantization tolerance. It removes unrelated junction connectors but retains a ≤50m graph-mapped Y merge only when it reaches the corresponding original-road endpoint within 12m; normal single-road checks remain 70% overlap/length and 4m separation.
    5. **PostGIS Dual-Buffering:** In `report_service.py` and `admin.py`, creates buffered line geometries for both carriageways and merges them into a single avoidance polygon boundary (`ST_Multi` / `ST_Buffer`), guaranteeing Valhalla detour calculations route around both carriageways simultaneously.
*   **Access & Roles:** Public users can report bidirectional hazards; DRRM officers inspect and confirm carriageway pairs during spatial moderation.
*   **Related Components:**
    *   **Frontend:** [FloodReportPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx), [CreateOfficialZonePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/CreateOfficialZonePanel.tsx), [LiveMapPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/LiveMapPage.tsx).
    *   **Backend:** [carriageway_service.py](file:///d:/Documents/Github/LANES/backend/app/services/carriageway_service.py), [report_service.py](file:///d:/Documents/Github/LANES/backend/app/services/report_service.py), [routes.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/routes.py) (`/preview-bidirectional`), [admin.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py).

---

### 18. Spatial Analytics & Flood Risk Heatmap Engine
*   **Purpose:** Aggregates historical and active flood reports into spatial density visualizations and risk rankings to guide municipal DRRM resource allocation and citizen route planning.
*   **What it does:** Delivers commuter and administrative analytics dashboards visualizing flood incident concentration, recurrent submersion hotspots, top barangay hazard statistics, and temporal trend analyses across Pasig City.
*   **How it works:**
    1. **MapLibre WebGL Heatmap Shader:** Computes continuous Kernel Density Estimation (KDE) on client-side WebGL GPU shaders (`type: "heatmap"`), interpolating `heatmap-weight` from report severity and dynamically scaling `heatmap-radius` and `heatmap-color` across zoom levels (0 to 15).
    2. **PostGIS Spatial Aggregations:** Backend runs optimized PostGIS spatial queries (`ST_Within`, `ST_Intersects`) aggregating historical incident reports grouped by Pasig barangay boundary polygons.
    3. **Comparative Metric Cards:** Computes average severity indices, verification rates, and hourly incident frequency for DRRMO operational debriefs.
    4. **Commuter & Admin Perspectives:** Commuters access localized hazard summaries on the map, while administrators access comprehensive spatial heatmaps and drill-down metrics in the dedicated Analytics portal.
    5. **Verified-event counting contract:** Flood History & Analytics uses distinct verified Flood Events for incident totals; supporting reports remain a separate evidence/confidence metric and cannot inflate recurrence rankings. Its planning dashboard shows recurrence, roads, peak verified severity, official duration, and verification time-series data from admin-only server aggregations.
    6. **Protected history and planning boundary:** The dedicated `/admin/flood-history` workspace keeps historical MapLibre event footprints separate from live routing zones. Filtered CSV/JSON planning exports contain event-level data only; raw report text, reporter identity, exact report geometry, and media remain in the authorized event-detail view.
*   **Access & Roles:** Commuters (public summary); Administrators & DRRM officers (full spatial analytics dashboard).
*   **Related Components:**
    *   **Frontend:** [AnalyticsDashboard.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/AnalyticsDashboard.tsx), [AnalyticsPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/analytics/AnalyticsPanel.tsx), [MapCanvas.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapCanvas.tsx), [LiveMapPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/LiveMapPage.tsx), [FloodEventAnalytics.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/flood-history/FloodEventAnalytics.tsx), [FloodEventVisualizations.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/flood-history/FloodEventVisualizations.tsx), and [FloodEventRecords.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/flood-history/FloodEventRecords.tsx) with its isolated `HistoricalEventsMap` layer.
    *   **Backend:** [analytics.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/analytics.py), [reports.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/reports.py), [admin.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py), [flood_event_service.py](file:///d:/Documents/Github/LANES/backend/app/services/flood_event_service.py), [crud/report.py](file:///d:/Documents/Github/LANES/backend/app/crud/report.py).

---

### 19. Official DRRMO Zone Creation & Interactive Terra Draw Vector Engine
*   **Purpose:** Empowers disaster management officials to declare official flood avoidance zones, custom detour boundaries, or road closures directly onto the interactive map.
*   **What it does:** Provides an administrative creation panel featuring 5 vector geometry modes: **Line** (road-snapping timeline segment), **Polygon**, **Freehand** (smooth sketch tool), **Rectangle**, and **Circle**. Captures geometries and submits them directly into the PostGIS routing avoidance layer.
*   **How it works:**
    1. Integrates **Terra Draw** (`terra-draw` & `terra-draw-maplibre-gl-adapter`) directly onto the MapLibre GL JS WebGL canvas.
    2. Uses React `useRef` lifecycle guards to maintain instance persistence and prevent ghost collision errors during fast unmounts.
    3. For Line mode: leverages `MapContext` shared coordinates to provide click-to-pick with Orange (`#f97316`) Start and Dark Red (`#991b1b`) End pins, rendering a real-time dashed road segment preview layer.
    4. For Shape modes: renders a responsive bottom-centered instruction pill directly over the map canvas and snapshots GeoJSON geometries on `change` events.
    5. Dispatches payload via `POST /api/v1/zones` (or `POST /api/v1/reports` in admin mode) to immediately persist avoidance zones into PostgreSQL/PostGIS.
*   **Access & Roles:** Restricted to `admin` / `drrm` roles.
*   **Related Components:**
    *   **Frontend:** [CreateOfficialZonePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/CreateOfficialZonePanel.tsx), [LiveMapPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/LiveMapPage.tsx).
    *   **Backend:** [admin.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py), [reports.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/reports.py).

---

### 20. Saved Places (Personalized Location Bookmarks)
*   **Purpose:** Allows authenticated commuters to bookmark up to 10 frequently visited locations on the map for quick re-use as route origins or destinations.
*   **What it does:** Provides a full CRUD management interface for personalized saved places, each with a custom emoji icon, label, and geographic coordinates. Displays all saved places as icon markers directly on the map.
*   **How it works:**
    1. The user opens the **Save Place Panel** from the map interface and switches between two tabs: **Add Place** and **My Places (X/10)**.
    2. To pick a location, the user taps "Choose on Map", which activates a crosshair pin-drop mode on the `MapCanvas`. The chosen coordinates are reflected back to the panel.
    3. The backend enforces a hard limit of **10 saved places** per user. Attempting to create an 11th place returns an `HTTP 400` error with a human-readable message.
    4. Saved places are fetched and displayed in a list under the **My Places** tab, showing the icon, name, and address. Each entry has a **Delete** button to free a quota slot.
    5. All saved places are rendered on the `MapCanvas` as plain emoji icon markers centered directly over their stored coordinates. Hovering reveals the place name label.
    6. **Camera Synchronization & Indicator:** Selecting a saved place smoothly centers the camera using standardized hazard zone transitions (zoom 16, 1500ms duration) with a 3-second pulsing red highlight ring. Saved place quick pills in the feed sidebar open the Saved Places panel directly without setting origin pins.
*   **Access & Roles:** Authenticated users only.
*   **Related Components:**
    *   **Frontend:** [SavePlacePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/places/SavePlacePanel.tsx), [MapCanvas.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapCanvas.tsx), [MapContext.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapContext.tsx), [LeftSidebar.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/feed/LeftSidebar.tsx).
    *   **Backend:** [saved_places.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/saved_places.py) (`GET/POST/DELETE /api/v1/saved-places`), [crud/saved_place.py](file:///d:/Documents/Github/LANES/backend/app/crud/saved_place.py) (`MAX_SAVED_PLACES = 10`).

---

### 21. Emergency Hotline Directory
*   **Purpose:** Gives commuters direct access to current national, Pasig city, and Pasig barangay emergency contact numbers from the community feed.
*   **What it does:** Replaces static sidebar contacts with API-backed priority hotlines, expandable number lists, direct `tel:` links, and a full searchable directory modal.
*   **How it works:**
    1. The backend fetches and parses national contacts from `ehotlines.e.gov.ph` and Pasig contacts from the city government page.
    2. National and Pasig results are cached server-side for one hour to reduce upstream requests while preserving a public API surface.
    3. The feed renders priority contacts immediately through `GET /api/v1/hotlines/`; the full directory is fetched lazily from `GET /api/v1/hotlines/full` when opened.
    4. The directory separates national, Pasig city, and barangay contacts and exposes phone numbers as mobile-friendly `tel:` links.
*   **Access & Roles:** Public read-only access.
*   **Related Components:**
    *   **Frontend:** [EmergencyHotlinesCard.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/feed/components/EmergencyHotlinesCard.tsx), [EmergencyDirectoryModal.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/feed/components/EmergencyDirectoryModal.tsx), [useHotlines.ts](file:///d:/Documents/Github/LANES/frontend/src/features/feed/useHotlines.ts).
    *   **Backend:** [hotlines.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/hotlines.py), [hotline_service.py](file:///d:/Documents/Github/LANES/backend/app/services/hotline_service.py).

---

## 🔮 Future Features

### 1. User-Submitted Image Depth Classifier (Computer Vision AI)
*   **Purpose:** Automates flood severity validation via crowdsourced visual proof.
*   **Why it is needed:** Text descriptions are often subjective or exaggerated. While we currently accept photo evidence (via Cloudinary), human admins must still verify them. An AI classifier will automate the objective verification of street conditions.
*   **Expected functionality:**
    *   Commuters upload a photo of the road flood (already implemented).
    *   A deep learning model (e.g., CNN or YOLO) analyzes the uploaded image URL from Cloudinary.
    *   It detects key anchor references (submerged wheels, fire hydrants, doors) to classify water height.
    *   Populates the moderation queue with the visual estimation of severity.
*   **How it will integrate:**
    *   Establish a secondary Python ML worker (or use FastAPI background tasks) running a PyTorch pipeline to process image URLs.
*   **Dependencies:** Host machine GPU acceleration, a trained reference dataset of street-level urban flooding photos.

---

### 2. Automated Social Media Scraper Service (X/Twitter and Facebook APIs)
*   **Purpose:** Dramatically speeds up data ingestion by eliminating reliance on manual reports.
*   **Why it is needed:** During typhoons, emergency data updates are shared at high velocity across social media platforms like X (Twitter) and Facebook. An automated crawler will capture these inputs in real time.
*   **Expected functionality:**
    *   A celery-based background worker continuously queries X and Facebook search endpoints for keyword patterns (e.g., "baha Pasig", "Caruncho Ave baha").
    *   Parsed matches are run through the spaCy NER pipeline and loaded directly into the admin moderation queue.
*   **How it will integrate:**
    *   Add a new scraper microservice to the project stack.
    *   Pipes scraped JSON outputs into the backend `/api/v1/reports` API.
*   **Dependencies:** Developer API keys from Twitter/X and Meta Platforms.

---

### 3. Bilingual Speech-to-Text Voice Reporting
*   **Purpose:** Enables motorists in transit to report active hazards hands-free.
*   **Why it is needed:** Typist reporting is dangerous for active drivers. Letting users dictate short reports keeps eyes on the road during severe storms.
*   **Expected functionality:**
    *   Commuters tap a microphone button, record a Taglish description (e.g., *"Baha rito sa San Joaquin, lagpas bewang na"*), and submit.
    *   The system transcribes the speech and pipes the raw text into spaCy.
*   **How it will integrate:**
    *   Integrate browser MediaRecorder APIs in [FloodReportPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx).
    *   Create a backend utility using a bilingual transcription framework (e.g., OpenAI Whisper).
*   **Dependencies:** Speech-to-Text model pipeline, micro-permissions access in browser clients.

---

### 4. Turn-by-Turn Voice Navigation (Text-to-Speech)
*   **Purpose:** Prevents driver distractions by dictating detour directions audibly.
*   **Why it is needed:** Drivers cannot safely read map paths or turn-by-turn lists while navigating heavy rain and storm conditions.
*   **Expected functionality:**
    *   The PWA speaks directions aloud (e.g., *"In 200 meters, turn left to bypass the flooded street ahead"*).
*   **How it will integrate:**
    *   Hook into the HTML5 **Web Speech API (`SpeechSynthesis`)** inside [RoutePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/routing/RoutePanel.tsx).
    *   Trigger directions audio prompts based on geolocation tracking updates relative to the Valhalla path coordinate array.
*   **Dependencies:** Secure HTTPS deployment (for geolocation sensor permissions).

---

### 5. IoT Telemetric Sensor Nodes Integration
*   **Purpose:** Automatically registers baseline hazard metrics at high-risk municipal points.
*   **Why it is needed:** Certain low-lying streets (e.g., Pasig Mega Market perimeter) flood during every minor rainfall event. Real-time telemetry ensures instant database updates.
*   **Expected functionality:**
    *   Ultrasonic water-level sensors measure current road water levels.
    *   The sensor microcontrollers transmit depth values directly to the spatial database.
    *   Avoidance zones are automatically updated without manual administrator intervention.
*   **How it will integrate:**
    *   Build a dedicated backend route handler `POST /api/v1/telemetry/report` restricted to authenticated IoT gateway tokens.
    *   Pipes telemetric depth metrics directly into the PostGIS database.
*   **Dependencies:** Physical ESP32 microcontrollers, ultrasonic sensors, and cellular/LoRa transmitters.
