# LANES: Architecture & Design Decisions

> **Last Updated:** September 26, 2026, 3:30 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This document tracks major technical decisions, architecture shifts, and the reasoning behind them to ensure future maintainability and a clear record of "why" certain technologies were chosen.

---

## 1. Routing Engine Architecture: Valhalla (Online HTTP) + OpenRouteService (Cloud) + Valhalla WASM (Offline)
**Date:** August 2026
**Decision:** Settle on a triple-path routing architecture — Valhalla HTTP for online routing, OpenRouteService as a cloud fallback, and Valhalla WebAssembly for offline resilience. GraphHopper was evaluated and dropped.

**Context:**
LANES requires real-time flood detouring and multiple route recommendations for commuters. The routing engine has gone through several iterations:
- **Phase 1:** Valhalla (self-hosted Docker) — worked but had challenges generating diverse alternatives around flood polygons.
- **Phase 2:** GraphHopper (self-hosted JAR) — integrated for its `custom_models` API allowing polygon injection. Later removed due to self-hosting complexity and the requirement for Java on the deployment machine.
- **Phase 3 (Current):** Return to Valhalla for online routing via its HTTP API, with **OpenRouteService** (ORS) as a cloud-hosted secondary engine, and Valhalla **WebAssembly** for fully offline client-side routing.

**Final Routing Decision:**

| Engine | Mode | Use Case |
|---|---|---|
| Valhalla HTTP | Online (primary) | Flood-aware multi-route routing via self-hosted Docker container |
| OpenRouteService | Online (secondary) | Cloud backup; user can switch in UI; used when Valhalla returns poor routes |
| Valhalla WASM | Offline | Runs entirely in the browser; activated automatically when `navigator.onLine === false` |

**Reasoning:**
1. **Valhalla (Online):** Natively supports `exclude_polygons` for flood avoidance, multiple alternatives (`alternates=2`), and vehicle profiles (`auto`, `motorcycle`, `pedestrian`). The Docker container (`ghcr.io/gis-ops/docker-valhalla`) can be run locally or on a server.
2. **OpenRouteService (Cloud):** Free tier supports Philippines data. Uses `/directions/{profile}/geojson` endpoint with Accept `application/geo+json`. ORS gives users an independent routing opinion, useful when Valhalla produces questionable detours.
3. **Valhalla WASM (Offline):** Map tiles (`.tar`) are highly compressed and mountable via Emscripten's virtual filesystem (OPFS/IndexedDB). By injecting a custom `valhallaCore.ts` engine, we bypass the restrictive official JS wrapper and feed custom `exclude_polygons` from IndexedDB-cached flood zones.
4. **GraphHopper Removal:** GraphHopper required a self-hosted Java JAR and had no practical advantage over Valhalla+ORS. Removed to simplify the deployment stack.

**UI Implementation:**
- The route planner sidebar has an engine toggle: **Valhalla | OpenRouteService**
- When offline, the app silently falls back to WASM regardless of the toggle selection
- An `OfflineManager` in the sidebar footer shows download status and triggers tile caching

**Production deployment update (September 17, 2026):** Valhalla is deployed as a separate, private Cloud Run service rather than assumed to exist on the FastAPI container's localhost. FastAPI authenticates with its runtime identity and automatically retries via ORS only for Valhalla availability failures. The versioned Philippines tile archive lives in private Cloud Storage and is baked into each immutable Valhalla image, avoiding startup downloads.

---

## 2. Real-time Signaling: WebSockets vs. Server-Sent Events (SSE)
**Date:** August 2026
**Decision:** Migrate from WebSockets to Server-Sent Events (SSE).

**Context:**
The LANES platform needs to broadcast real-time updates when a flood report is approved, a detour zone is created, or a user interacts with a community post. Initially, WebSockets were considered because they provide two-way real-time communication.

**Reasoning for the Switch:**
1. **Unidirectional Flow:** The real-time requirement for LANES is strictly "Server-to-Client" (broadcasting map updates or notifications). Clients do not need a persistent pipe to send data back; they use standard secure HTTP POST requests for actions (like posting a report or comment).
2. **Built-in Reconnection:** SSE operates over standard HTTP and natively handles automatic browser reconnections if a user's mobile connection drops. WebSockets require complex manual heartbeat and reconnection logic.
3. **Mobile & APK Compatibility:** Because the Next.js frontend will eventually be wrapped into an Android `.apk` (via Capacitor or Trusted Web Activity), SSE is significantly more battery-efficient and less prone to dropping on mobile networks.
4. **Simplicity:** SSE allows us to use `EventSource` on the frontend and a simple async queue on the FastAPI backend without dealing with bidirectional socket states.

---

## 3. Authentication: JWT Tokens in LocalStorage vs. HttpOnly Cookies
**Date:** August 2026
**Decision:** Retain standard JWT Bearer Tokens (stored in `localStorage`) instead of migrating to `HttpOnly` secure cookies.

**Context:**
For web applications, `HttpOnly` cookies are considered the gold standard for preventing Cross-Site Scripting (XSS) attacks. We initially planned to migrate to `HttpOnly` cookies for maximum security.

**Reasoning for the Switch:**
1. **The Native APK Goal:** The ultimate goal for LANES is to be downloadable from the Google Play Store as an Android `.apk`.
2. **WebView Limitations:** When a PWA is wrapped into a native app, it runs inside a mobile WebView. WebViews and native iOS/Android environments have extremely strict, sometimes unpredictable rules regarding cross-origin cookies to prevent user tracking. Relying on `HttpOnly` cookies often causes broken authentication flows on mobile devices.
3. **Mobile Security Context:** Native mobile apps are fundamentally less vulnerable to XSS than standard web browsers because they don't execute arbitrary third-party scripts.
4. **Future-Proofing:** By using standard JWT tokens, the backend API remains completely decoupled. When we compile the APK, we simply swap `localStorage.setItem('token')` to a native secure storage plugin (e.g., Capacitor Secure Storage or iOS Keychain), and the backend won't need a single line of code changed.

---

## 4. Local Network Configuration (CORS & Proxying)
**Date:** August 2026
**Decision:** Restrict backend CORS to specific Local Area Network (LAN) IP ranges and utilize Next.js rewrites for proxying.

**Context:**
To test the app across multiple smartphones on the same WiFi network, hardcoding `localhost` causes connection failures on mobile devices (since `localhost` on a phone points to the phone itself, not the dev laptop).

**Reasoning:**
1. **Dynamic Backend URL:** The Next.js frontend `next.config.ts` was updated to read `process.env.BACKEND_URL`, defaulting to `127.0.0.1`. By setting `NEXT_PUBLIC_API_URL` to the host computer's IPv4 address, mobile devices can reach the backend.
2. **CORS Hardening:** The previous wildcard (`*`) CORS setting was highly insecure. It was replaced with a regex `^https?://(192\\.168\\.\\d+\\.\\d+|10\\.\\d+\\.\\d+\\.\\d+):3000$` that strictly allows local WiFi connections (e.g., `192.168.x.x`), preventing unauthorized external domains from accessing the API while still allowing local mobile testing.

---

## 5. Modular Map Architecture: Imperative Hook Pattern & BaseMap
**Date:** August 2026
**Decision:** Decouple MapLibre initialization from feature layers using a pure `<BaseMap>` component and modular React hooks (`useCityBoundaries`, `useFloodZonesLayer`).

**Context:**
Originally, MapLibre instances were independently constructed in `MapCanvas.tsx` (commuter map) and `LiveMapPage.tsx` (admin live map). This led to duplicated map control styling, boundary fetching logic, and inconsistent layer behaviors between commuter and admin views. Furthermore, road-based flood reports had their geometric polygons hidden (`is_road_based == false`), showing only street line glows, which prevented admins and commuters from seeing exact flood boundaries.

**Reasoning for the Switch:**
1. **Imperative Hook Pattern (Standard React MapLibre Architecture):** Raw MapLibre GL JS operates imperatively on a canvas. Creating a bare `<BaseMap>` that handles canvas mounting, tile style fallbacks (MapTiler → OpenStreetMap), `TopViewControlV3`, and native navigation controls allows any page to instantiate a styled map effortlessly.
2. **Pluggable Layer Hooks:** By extracting spatial datasets into custom hooks (e.g., `useCityBoundaries(map, isLoaded)` and `useFloodZonesLayer(map, isLoaded, activeZones)`), any future page can compose any combination of map layers in a single line of code without duplicating initialization logic.
3. **Unified Flood Polygons & Severity Color Scale:** Removed the restriction hiding road-based flood polygons so both admins and commuters see exact spatial flood hazard boundaries. Standardized the 4-tier color scale (`low`: Lime `#84cc16`, `medium`: Amber `#eab308`, `high`: Orange `#f97316`, `extreme`: Red `#ef4444`).

---

## 6. 1:N Spatial Relational Deduplication & Trust Score Pooling
**Date:** August 2026
**Decision:** Transition from 1:1 `report_id` on `FloodAvoidanceZone` to 1:N `zone_id` foreign key on `FloodReport` with communal trust score crediting.

**Context:**
During monsoon events, multiple commuters frequently submit independent reports for the same flooded street. Originally, each avoidance zone strictly required a unique `report_id`, creating duplicate conflicting avoidance barriers for the Valhalla routing engine and blocking administrators from merging identical submissions.

**Reasoning & Architecture:**
1. **Relational Inversion (1:N Migration):** Moved the foreign key to `FloodReport.zone_id` referencing `FloodAvoidanceZone.id` (`ondelete="SET NULL"`). This allows a single physical avoidance barrier to encapsulate $N$ crowdsourced reports.
2. **Fair Trust Score Pooling:** Merging or approving a zone iterates across all linked reports to award verified trust points (`+5`) and increment `reports_verified` for every unique contributor, ensuring crowdsourced contributions are recognized without polluting the map.
3. **Proximity Search via PostGIS:** Utilizes `ST_DWithin` on the backend (`/api/v1/admin/zones/nearby`) to automatically detect existing active zones within 200–500m of incoming reports.

---

## 7. Shared Fluid UI Design System & Anti Box-in-a-Box Standard
**Date:** August 2026
**Decision:** Standardize multi-variant animated Tabs (`shared/ui/Tabs.tsx`) and full-bleed edge-to-edge spatial dashboards.

**Context:**
Different admin and profile pages used isolated tab implementations, leading to visual inconsistencies, frame nesting ("container inside container" syndrome), and horizontal scrollbar flicker during framer-motion transitions.

**Reasoning & Architecture:**
1. **Consolidated Tab Component (`Tabs.tsx`):** Implemented a shared component supporting `segmented`, `underline`, and `pills` variants with direction-aware sliding indicators and hidden overflow wrappers (`[scrollbar-width:none]`).
2. **Full-Bleed Spatial Workspaces:** Refactored `AdminLayout` to conditionally strip outer padding (`p-0` on `/admin/map`) while preserving padding on data tables, maximizing screen real estate for map operations.
3. **Viewport Auto-Fit & Persistence:** Integrated automatic Pasig City bounding box fitting (`[121.0515, 14.5338]` to `[121.1112, 14.6235]`) on first load, coupled with `localStorage` camera state tracking to persist user zoom/pan coordinates across navigation.

---

## 8. Unified Map Layer Zoom Hierarchy & Multi-Reporter Spatial Inspection
**Date:** August 2026
**Decision:** Standardize zoom thresholds ($Z \le 14$ vs. $Z > 14$) with shared tokens in `mapStyles.ts` and implement inline contributor inspection without blocking modals.

**Context:**
City overview views and street-level views previously had conflicting layer styles, duplicate road glows, and harsh outline borders on avoidance buffers. Additionally, merged avoidance zones obscured individual contributor reports.

**Reasoning & Architecture:**
1. **Strict Zoom Separation ($Z=14$ Cutoff)**:
   - **City Overview ($Z \le 14$)**: Uses solid filled circle pins with darker contrast borders matching the severity level for optimal visibility against white basemap tiles.
   - **Street Level ($Z > 14$)**: Eliminates all outline borders. Avoidance zones render as pure transparent $50\text{m}$ buffer auras with bold solid road centerlines.
2. **Inline Contributor Accordion vs. Modal**: Instead of interrupting the admin with screen-blocking dialogs, merged zones feature an inline animated drawer showing each contributor's avatar, timestamp, trust score, and quote.
3. **Dynamic Single-Report Map Focus**: Clicking an individual contributor temporarily isolates their exact original report geometry on the map while hiding the merged avoidance zone, allowing fine-grained spatial verification.

---

## 9. Admin Navigation Refactoring
**Date:** August 2026
**Decision:** Decompose `AdminNav.tsx` into modular configuration and layout components.

**Context:**
The admin interface originally contained a large, monolithic `AdminNav.tsx` file combining routing, UI layouts, styling, icons, and badge calculation logic in a single 150-line component. This proved brittle and difficult to maintain.

**Reasoning:**
1. **Separation of Concerns:** Routing arrays were split out into `routes.ts`, and helper badge hooks (like `usePendingBadge`) were isolated. `AdminLayout.tsx` handles pure wrapping structure.
2. **Readability:** Extracting the configuration dramatically reduces the lines of code in the actual layout wrapper. Adding a new route is now a simple data entry task in `routes.ts` rather than a JSX structure modification.

---

## 10. MapLibre Dynamic Layer Updating: Avoid `isStyleLoaded()` Strict Checks
**Date:** August 2026
**Decision:** Remove strict `map.isStyleLoaded()` checks when dynamically updating vector layers (GeoJSON) and utilize `setData()` rather than tearing down and rebuilding layers.

**Context:**
When active flood zones were added to the map using `useFloodZonesLayer.ts`, the zones often completely failed to render on initial page load, failing silently without errors.

**Reasoning:**
1. **The "Silent Deadlock":** MapLibre's `isStyleLoaded()` method is extremely strict. While intuitively it seems to mean "is the base map ready", it actually means "is the map 100% idle with no pending vector tile downloads". If a React hook checks `isStyleLoaded()` during tile fetching, it returns `false` and aborts silently.
2. **The Failsafe `getStyle()`:** MapLibre is perfectly capable of parsing and queuing custom sources/layers even while background tiles download. Removing `isStyleLoaded()` and simply verifying `map.getStyle()` exists prevents the deadlock.
3. **`setData()` Optimization:** Repeatedly calling `removeLayer` and `removeSource` on every React re-render can cause visual flickering and MapLibre race conditions. Using `.setData()` on the existing GeoJSON source is the native, performant way to push data updates into MapLibre.

---

## 11. Route Panel UI: Fixed Sidebar, Scrollable, Turn-by-Turn
**Date:** August 2026
**Decision:** Convert the floating/draggable route planner panel into a permanent fixed left sidebar with inline loading, scrollable results, and a Turn-by-Turn step list with map segment highlighting.

**Context:**
The original floating route panel was movable and closable, causing UX confusion. Users couldn't see step-by-step directions, and the full-screen loading overlay blocked the map during route calculation.

**Reasoning:**
1. **Fixed Sidebar:** The route panel is now a permanent `fixed top-0 left-0 bottom-0` sidebar (`340px` wide) — always visible, never closable, similar to Google Maps / OSM web. The map canvas starts at `340px` from the left.
2. **Inline Loading:** Replaced the full-screen frosted-glass overlay with a compact `LoadingOverlay variant="inline"` inside the panel so the map remains visible while calculating.
3. **Scrollable Results:** The header (inputs, engine toggle, vehicle profiles) and footer (Offline Manager) are fixed. The results section (`flex-1 overflow-y-auto`) scrolls independently.
4. **Compact Route Cards:** Route alternatives are rendered as slim horizontal strips (label + flood icon + ETA + km) rather than large bordered cards — reducing vertical space by ~50% per route option.
5. **Turn-by-Turn with Hover Highlight:** Each `instruction` from the route response is listed below the route cards. Hovering a step fires a `route-step-hover` DOM event; `MapCanvas` draws a `step-highlight-layer` (cyan glow + line) on the corresponding coordinate slice. Clicking a step also flies the map to that segment's midpoint.
6. **Segment Coordinate Extraction:** ORS steps use `way_points: [startIdx, endIdx]`; Valhalla uses `begin_shape_index`/`end_shape_index`. Both formats are handled to slice `geometry.coordinates` for the highlight.

---

## 12. 3D Map Terrain & Perspective Zoom Visibility (MapLibre GL JS v5)
**Date:** August 2026
**Decision:** Remove layer-level `minzoom`/`maxzoom` filters on active zone vector layers and replace them with Zoom-based opacity step expressions (`["step", ["zoom"]]`). Add 3D Terrain via AWS Terrarium DEM tiles.

**Context:**
When tilting the map to a 45-80° pitch, the effective zoom level becomes distorted by perspective (objects near the camera fall into a higher zoom bracket than objects near the horizon). Strict `minzoom` cutoffs caused geometries at the top/bottom of the screen to prematurely disappear, leading to flickering and broken UX during pitch interactions.

**Reasoning:**
1. **Shader-Level Control:** By removing `minzoom` and `maxzoom` from the `useFloodZonesLayer` logic, geometries are always sent to the WebGL rendering pipeline regardless of pitch angle frustum clipping.
2. **Opacity Steps:** We control the visibility natively using step expressions for opacity in `mapStyles.ts`. The `["zoom"]` expression evaluates against the global camera state rather than the distorted tile depth, guaranteeing a seamless transition between City View (Pins) and Street View (Polygons).
3. **Terrain Integration:** 3D terrain elevation is supplied via `terrarium-dem` AWS S3 tiles, providing a realistic 3D mesh draped with raster/vector basemaps (e.g. OpenStreetMap).
4. **Style Swapping:** A unified `MapStylePickerControl` was introduced to let users swap between 5 styles (Streets, Dark, Roads, Satellite, OSM). The `setTerrain()` method wipes layers in MapLibre v5, so custom layers are guarded via `if (!m.getLayer(...))` inside `style.load` event listeners to ensure they persist across style and 3D/2D swaps.

---

## 14. Persistent Admin Map Layout & Centralized Camera Transition Engine
**Date:** August 2026
**Decision:** Mount `<LiveMapPage />` persistently in `AdminLayout.tsx` and centralize camera transition helpers (`flyToFeature`, `flyToCoordinates`) in `mapGeoUtils.ts`.

**Context:**
1. In the admin interface, navigating between `/admin/reports` and `/admin/map` was unmounting the MapLibre canvas on every route change, causing tile re-downloads, loading spinners, and resetting the administrator's camera view.
2. Clicking "View on Map" from the Reports page or selecting items in the Live Map sidebar had inconsistent zoom levels, differing pitch perspectives, and lacked unified coordinate extraction for complex geometries.

**Reasoning:**
1. **Zero-Latency Admin Navigation:** By mounting `<LiveMapPage />` directly inside `AdminLayout.tsx` (using CSS visibility toggling) and returning `null` from `admin/map/page.tsx`, the map instance is preserved in memory across all admin route changes. Returning to `/admin/map` is instantaneous (0ms load time) with no tile fetching or terrain reloads.
2. **Centralized Camera Physics:** `flyToFeature()` in `mapGeoUtils.ts` automatically extracts midpoints and centroids across Points, LineStrings, and Polygon avoidance zones, standardizing on a uniform 45-degree angle, zoom level 16, and 1400ms duration for all flood inspection workflows.
3. **Selection State Guards:** Camera movements are strictly guarded to only execute when selecting an item, preventing unwanted camera jarring when deselecting.

---

## 3. Moderation UI & Spatial Operations Consolidation
**Date:** August 2026
**Decision:** Drop standalone tabular 'Reports' pages in favor of integrating moderation directly into the Spatial Operations Map via overlay panels.

**Context:**
Initially, flood reports were moderated via a traditional data-table view in the admin panel. However, flood reports are inherently spatial—approving or rejecting a report requires visualizing its location relative to existing floods and active detours.

**Reasoning:**
1. **Context Switching:** Forcing admins to jump between a tabular list and a map to verify coordinates was inefficient.
2. **Duplicate Prevention:** By moderating on the map (via `PendingReportsPanel`), admins can visually identify clusters of duplicate reports and use batch operations to merge them instantly.
3. **Unified UI:** The `FloodReportPanel` originally built for public users was seamlessly adapted for Admins to create 'Official DRRMO Zones' directly on the map, removing the need for a separate admin-only creation form.

**Implementation:**
The entire moderation workflow now lives inside `LiveMapPage.tsx`, acting as the 'Smart Controller' that passes data down to specific sidebar panels (Active Zones, Pending Reports) and overlays (FloodReportPanel for creation, ReportDetailsModal for moderation).

---

## 15. Geospatial Drawing Engine: `mapbox-gl-draw` vs. `terra-draw`
**Date:** August 2026
**Decision:** Completely remove `mapbox-gl-draw` (and unmaintained circle/rectangle plugins) and migrate to **Terra Draw** (`terra-draw` + `terra-draw-maplibre-gl-adapter`) for interactive map boundary drawing in the Admin Panel.

**Context:**
The DRRMO Admin panel requires interactive map tools to define custom detour geometries (Polygons, Freehand sketches, Rectangles, and Circles) when creating official zones:
- Initially, `mapbox-gl-draw` along with community extensions (`mapbox-gl-draw-circle`, `mapbox-gl-draw-rectangle-mode`) was integrated.
- However, `mapbox-gl-draw` relied on legacy Node.js build dependencies (such as `jsonlint-lines` requiring `fs`, `os`, `path`), which caused constant build/bundler failures in Next.js Turbopack and required fragile webpack mock fallbacks.
- Furthermore, rapid mounting and unmounting during React 18 development (Strict Mode) triggered fatal crashes (`Uncaught Error: Source "mapbox-gl-draw-cold" already exists`) because `mapbox-gl-draw` failed to cleanly synchronously detach WebGL layers/sources from the MapLibre canvas.

**Reasoning for the Migration to Terra Draw:**
1. **Modern Bundler & Framework Compatibility:** Terra Draw is modern, lightweight, fully TypeScript-typed, and framework-agnostic. It carries zero legacy Node.js dependencies (`fs`), eliminating all Webpack and `package.json` mock hacks in Next.js.
2. **Native Multi-Shape Capabilities:** Terra Draw provides first-party modes for `Polygon`, `Freehand`, `Rectangle`, and `Circle` out of the box, removing the need for fragile third-party wrapper plugins.
3. **Official MapLibre GL JS Adapter:** Uses `terra-draw-maplibre-gl-adapter` to attach directly to MapLibre instances cleanly, avoiding DOM control collision and unmount leaks in React 18.
4. **Interactive Freehand Support:** Natively supports smooth freehand drawing (`TerraDrawFreehandMode`), allowing operators to sketch organic flood extents directly on the map.

---

## 16. Bidirectional Flood Report: Hybrid Carriageway Detection Strategy
**Date:** September 2, 2026
**Decision:** Replace the naive CSS `line-offset` visual hack for "Affects both sides of the road" with an intelligent **Hybrid Carriageway Detection Strategy** combining authoritative Valhalla routing/map matching, perpendicular geometric hinting, and PostGIS `MultiLineString` storage.

**Context:**
When a user submits a flood report and checks "Affects both sides of the road (2-way)", the system needs to show and buffer both carriageways of the affected road. The challenge is that roads in the Philippines vary significantly:
- **Narrow two-way roads**: Both directions share the same centerline in OSM.
- **Wide undivided roads**: Two-way, one centerline, wide lanes.
- **Divided dual carriageways** (e.g., C-5, NLEX, EDSA): Mapped in OSM as **two completely separate one-way roads** with a physical median between them.

The original approach was a CSS `line-offset: -8px` visual trick — drawing the same MapLibre line shifted slightly left. This failed fundamentally:
1. It is purely cosmetic — the flood zone buffer in PostGIS still only covered one road.
2. On wide divided roads, the offset line landed in the median or on the wrong road entirely.
3. Mathematical parallel offsets do not account for variable road widths or OSM's dual-way modeling.

**Rejected Approaches:**
- **Standard reverse routing (`/route` A→B reversed to B→A):** The Valhalla routing engine is traffic-law-aware. If the road is one-way, it will hunt for U-turns or legal crossing points, producing massive detours instead of a parallel line. ❌
- **Fixed geometric offset only:** A fixed 15m offset works on some roads but fails on roads narrower than 5m (lands in buildings) or wider than 40m (lands in the median). ❌

**The Traversability-Aware Hybrid Strategy (Selected):**
The final decision combines Valhalla's Traversability metrics with a dynamic geometric search loop:

| Step | Technique | Purpose |
|---|---|---|
| 1 | **Authoritative Segment Selection** | Evaluates Start→End and End→Start from the raw user anchors, normalizes the shorter valid result to Start→End order, and rejects excessive legal-driving loops before topology detection. |
| 2 | **Edge-Indexed Road-Run Inspection** (`/trace_attributes`) | Requests Valhalla `begin_shape_index`/`end_shape_index` attributes and splits a report where normalized road identity or traversability changes. Each run is then classified independently as one-way, divided, or narrow two-way; no dominant whole-route label is used for a mixed route. |
| 3 | **Two-Sided Dynamic Offset Search** | For one-way roads or divided highways, probes both perpendicular sides at **5m, 10m, 15m, 20m, 30m**. Geometry is a search hint only. |
| 4 | **Coordinate Reversal & Map Matching** | Reverses each shifted probe and map-matches it so the candidate follows the expected opposing flow without constructing a legal U-turn route. |
| 5 | **Strict Counterpart Validation** | Accepts `DIVIDED_CARRIAGEWAY` only when normalized name/reference and road class match, OSM way IDs are distinct, direction is opposite, length is 70–130%, longitudinal overlap is at least 70%, lateral separation is 4–35m, and the candidate is not a loop. For a route split into multiple topology runs, a counterpart may cover 50–130% with at least 50% overlap and 3.5–35m separation. Non-parallel geometry is removed except for a short graph-mapped Y transition that joins the matching endpoint of the proven parallel road section; a cross-street or detached connector remains rejected. |

**Why Map Matching avoids U-turns:**
The standard `/route` API is path-finding (must obey traffic laws between two points). The `/trace_attributes` Map Matching API is shape-fitting (finds the road beneath a shape, regardless of legal drivability). Feeding it a reversed shape causes it to snap directly to the opposite-flowing lane without needing any legal U-turn maneuver.

**PostGIS Storage:**
When an opposite carriageway is successfully found, the backend stores **both** LineStrings as a single `MultiLineString` in the `flood_reports.geometry` column. During admin approval, the buffer query is updated:
- **Single road (LineString):** `ST_Buffer(geometry, 0.00015)` — standard single-line buffer.
- **Dual carriageway (MultiLineString):** `ST_ConvexHull(ST_Collect(ST_Buffer(line1), ST_Buffer(line2)))` — wraps both buffered lines into one convex hull polygon that accurately covers both carriageways.

**Shared Preview and Persistence Contract:**
`POST /api/v1/reports/preview-bidirectional` accepts raw Start/End anchors and returns `original`, `opposite`, `coverage_geometry`, `road_type`, `is_divided`, `validation_status`, and a user-facing `message`. The returned lines contain only Valhalla-snapped road geometry; raw clicks are inputs, never connector vertices. `MapContext` uses the result for the orange preview and moves its visible pins to the snapped endpoints. Public submission carries the verified single or dual coverage, and server persistence independently rebuilds every road line before saving so Pending Reports render the same road-only contract.

**Fallback Behavior:**
- If no opposite carriageway is proven (true one-way, ambiguous, unmapped, or routing unavailable), the system conservatively keeps only the original LineString and shows a non-blocking explanation. It never persists a guessed mathematical parallel.

**Files Modified:**
- [`backend/app/services/carriageway_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/carriageway_service.py) — authoritative segment routing, classification, opposite search, and validation
- [`backend/app/services/report_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/report_service.py) — server-authoritative revalidation and validated `MultiLineString` construction
- [`backend/app/api/v1/endpoints/routes.py`](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/routes.py) — canonical `POST /preview-bidirectional` implementation and response contract
- [`backend/app/api/v1/endpoints/reports.py`](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/reports.py) — backwards-compatible `POST /reports/preview-bidirectional` alias
- [`backend/app/api/v1/endpoints/admin.py`](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py) — `ST_ConvexHull(ST_Collect(...))` dual-buffer approval logic
- [`frontend/src/features/map/MapContext.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapContext.tsx) — centralized validated geometry, road type, status, and explanation
- [`frontend/src/features/map/MapCanvas.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapCanvas.tsx) — Dual-source real line rendering replacing CSS offset hack

---

## 17. Multi-Report "Draft Cart" Architecture vs. Backend Bulk Endpoint
**Date:** September 3, 2026
**Decision:** Implement a client-side "Draft Cart" array holding `DraftReport` objects in `MapContext.tsx`, combined with an iterative `Promise.all` sequence on submit, instead of rewriting the backend REST API to support bulk JSON arrays.

**Context:**
Users frequently encounter multiple flooded streets connected to one another (e.g., crossing a neighborhood block). The previous workflow forced the user to complete the report form, submit it, close the panel, and restart the entire reporting flow for the next street.
We needed a way to submit multiple disconnected or connected reports in one go, including the ability to draft mixed geometries (routed lines and drawn TerraDraw polygons).

**Reasoning:**
1. **Preserving the Endpoint Structure:** The FastAPI backend endpoints (`/reports` for public users via `FormData` and `/admin/zones` for admins via JSON) were highly optimized for single-entity submission, validation, and notification broadcasts. Rewriting them to accept heterogeneous arrays (mixed `FormData` for files and JSON for geometry) would cause significant regression risks and drastically increase endpoint complexity.
2. **Client-Side Drafting:** By lifting a `draftReports` array state up to `MapContext.tsx`, the MapCanvas can reactively render pending drafts as dashed purple lines (`#8b5cf6`), allowing users to visualize what they are about to submit.
3. **Promise.all Iteration:** The `handleSubmit` logic in both `FloodReportPanel.tsx` and `CreateOfficialZonePanel.tsx` loops over `draftReports` (plus the currently filled form, if any) and dispatches individual, concurrent API requests. This achieves the user's goal of "batch reporting" without requiring any backend schema changes.
4. **Community Feed Separation:** By sending them as individual reports, the system automatically generates separate posts in the Community Feed. This was explicitly chosen because a single massive "combo post" containing 5 random disconnected streets would be unreadable on the feed map.

**Files Modified:**
- [`frontend/src/features/map/MapContext.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapContext.tsx) — Added `DraftReport` type and `draftReports` state.
- [`frontend/src/features/map/MapCanvas.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/map/MapCanvas.tsx) — Added `draft-reports-source` and `draft-reports-layer` rendering logic.
- [`frontend/src/features/hazards/FloodReportPanel.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/hazards/FloodReportPanel.tsx) — Refactored to include "Add Another Road" button, Draft Cart list view, and looping submit loop.
- [`frontend/src/features/admin/components/CreateOfficialZonePanel.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/CreateOfficialZonePanel.tsx) — Cloned the Draft Cart logic, extending it to support TerraDraw drawn features alongside routed lines.

---

## 18. Official Avoidance Zone Moderation Architecture & Media Ingestion Pipeline
**Date:** September 9, 2026
**Decision:** Deconstruct the monolithic `CreateOfficialZonePanel.tsx` into a Feature-Based subcomponent hierarchy (`frontend/src/features/admin/components/zones/`), standardize form schema and UI sections directly with `FloodReportPanel.tsx`, introduce multipart `FormData` uploads to Cloudinary for avoidance zone evidence, and establish a decoupled boundary for the ongoing Flood-Report Merge Workspace (`MergeWorkspacePanel.tsx`).

**Context:**
1. Over iterative development, `CreateOfficialZonePanel.tsx` grew into a 1,000+ line monolithic component containing geometry mode switching, two-click road snapping, TerraDraw integration, draft queue state, and custom form controls.
2. The form fields within the zone creation drawer drifted away from the public commuter reporting patterns in `FloodReportPanel.tsx`:
   - It relied on manual severity pills (Low/Medium/High/Extreme) instead of auto-deriving severity from real-world water depth.
   - Vehicle passability was rendered with generic pills missing critical local transport categories (e.g., Bicycles/E-Bikes).
   - Hidden hazards lacked standard Yes/No/Unsure options.
   - Admins had no way to attach photographic or video evidence directly to official DRRMO zones, unlike commuter reports.
   - Non-standard UI controls like "Avoidance Polygon Buffer Width" sliders introduced visual clutter and confusion.
3. Simultaneously, Capstone Phase 18 introduced backend models and endpoints for multi-report candidate merging (`merge_service.py`), but the frontend merge workspace (`MergeWorkspacePanel.tsx`) and live multi-report map resolution interface remain incomplete and in active development.

**Architectural Shifts & Technical Strategy:**
1. **Feature-Based Subcomponent Extraction (`src/features/admin/components/zones/`):**
   - Refactored `CreateOfficialZonePanel.tsx` into a lightweight wrapper exporting `OfficialZoneDrawer.tsx`.
   - Extracted dedicated, single-responsibility subcomponents:
     - `GeometryModeSelector.tsx`: Line vs. TerraDraw shape controls.
     - `RoadSegmentPicker.tsx`: Two-click start/end pin coordination and bidirectional road detection.
     - `DraftZoneCart.tsx`: Draft list management for 1 Zone = 1 Incident batching.
2. **Unified 5-Tier Form Architecture:**
   Standardized the drawer sections to strictly mirror `FloodReportPanel.tsx`:
   - **1. Spatial Geometry**: Road snapping (Line) or Terra Draw shapes (Polygon, Freehand, Rectangle, Circle).
   - **2. Hazard Attributes**: 8-tile visual depth gauge (Gutter, Half-Knee, Half-Tire, Knee, Tires, Waist, Chest, Neck) with auto-derived severity (`low`, `medium`, `high`, `extreme`), plus directional carriageway toggling. The arbitrary buffer width slider was completely excised.
   - **3. Survey (\*)**: Mandatory checkboxes for passable vehicles (including Bicycles/E-Bikes, Pedestrians, Sedans, etc.) and hidden hazard presence (Yes/No/Unsure).
   - **4. Photos & Videos (Optional)**: Drag-and-drop media upload supporting JPEG, PNG, and MP4 files up to 10MB with interactive preview tags.
   - **5. Description (\*)**: Mandatory operational notes and dispatch context.
3. **Decoupled Form State (`ZoneDataEditorForm.tsx`):**
   - Added granular section toggles (`hideSurvey`, `hideDescription`, `hideBidirectional`) to allow `ZoneDataEditorForm` to be reused cleanly between standalone zone creation/editing and future merge operations without code duplication.
4. **Multipart FormData & Cloudinary Media Upload (`POST /admin/zones`):**
   - Updated `POST /api/v1/admin/zones` to accept multipart `FormData` consisting of `body` (JSON string) and `media: List[UploadFile]`.
   - Uploaded files are streamed synchronously to Cloudinary via `cloudinary_service.upload_image()`, returning secure URLs persisted into the new `media_urls` JSONB column on `flood_avoidance_zones`.
   - Database schema migrated via Alembic migration `33ec62de236d_add_media_urls_to_avoidance_zones.py`.
5. **Separation from Merge Workspace:**
   - Explicitly decoupled the official zone creation/editing flow from the merge flow. The merge workspace interface (`MergeWorkspacePanel.tsx`) is an ongoing development initiative that will consume `ZoneDataEditorForm` as a child step once candidate recommendation and side-by-side conflict resolution UI are fully constructed.

**Files Modified:**
- [`backend/app/models/report.py`](file:///d:/Documents/Github/LANES/backend/app/models/report.py) — Added `media_urls` JSONB column to `FloodAvoidanceZone`.
- [`backend/app/schemas/report.py`](file:///d:/Documents/Github/LANES/backend/app/schemas/report.py) — Added `media_urls` to `FloodAvoidanceZoneResponse`.
- [`backend/app/api/v1/endpoints/admin.py`](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py) — Converted `create_official_zone` to multipart `FormData` with Cloudinary upload.
- [`backend/alembic/versions/33ec62de236d_add_media_urls_to_avoidance_zones.py`](file:///d:/Documents/Github/LANES/backend/alembic/versions/33ec62de236d_add_media_urls_to_avoidance_zones.py) — Database migration for `media_urls`.
- [`frontend/src/features/admin/adminApi.ts`](file:///d:/Documents/Github/LANES/frontend/src/features/admin/adminApi.ts) — Updated `createOfficialZone` to dispatch `FormData`.
- [`frontend/src/features/admin/components/ZoneDataEditorForm.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/ZoneDataEditorForm.tsx) — Rewritten with visual depth picker, survey isolation props, and buffer slider removal.
- [`frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx) — Main modularized drawer supporting create & edit modes, media upload, and standalone Survey & Description sections.
- [`frontend/src/features/admin/components/zones/subcomponents/`](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/zones/subcomponents/) — Extracted `GeometryModeSelector.tsx`, `RoadSegmentPicker.tsx`, and `DraftZoneCart.tsx`.

---

## 19. Verified Flood Event History as the Permanent Incident Unit
**Date:** September 2026
**Decision:** Keep temporary routing zones and individual reports operationally distinct from a durable, admin-only Flood Event record. A verified report or official zone opens one event; corroborating reports link to that event; the final live zone ending closes it without moving the event into Archive Center.

**Context:**
The previous lifecycle could treat rejected reports and ended zones as recycle-bin records, while multiple reports about one incident had no durable common identity. That made event duration, recurrence, evidence confidence, and city-planning analytics unreliable.

**Architectural Shifts & Technical Strategy:**
1. Added normalized `flood_events`, `flood_event_locations`, `flood_report_moderation_outcomes`, and `flood_event_timeline_entries` tables with indexed event ownership and PostGIS-compatible location design.
2. Centralized multi-table transitions in `flood_event_service.py`, including event creation, supporting-report linkage, structured rejection, final-zone ending, server-calculated metrics, timeline snapshots, and idempotent retries.
3. Kept all historical reads admin-protected. The Moderation Center tracks outcomes and hands spatial decisions back to Spatial Operations; it does not duplicate map actions.
4. Reused the shared underline `Tabs` component for the Moderation Center’s Community and Flood Report queues so staff navigation follows the established admin UI system.

**Files Modified:**
- [`backend/app/services/flood_event_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/flood_event_service.py) — Transactional event lifecycle and metrics.
- [`backend/app/api/v1/endpoints/admin.py`](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py) — Protected moderation/event summary endpoints and lifecycle handoffs.
- [`frontend/src/features/admin/ModerationCenterPage.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/admin/ModerationCenterPage.tsx) — Shared tabbed moderation navigation.
- [`frontend/src/features/admin/components/FloodModerationQueue.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/FloodModerationQueue.tsx) — Filtered staff tracking surface.

---

## 20. Flood Event as the Sole Historical Analytics Unit and Export Boundary
**Date:** September 2026
**Decision:** Use one distinct verified Flood Event as the unit for historical planning analytics, recurrence, severity, duration, and event-time trends. Treat approved reports only as a separately labelled corroboration signal; expose original evidence solely through the authorized event-detail route, never in planning aggregates or default exports.

**Context:**
One flooding incident can generate several public reports and one or more temporary routing zones. Counting those operational and evidence records directly would multiply one real-world incident in city-planning charts. Conversely, an export containing raw reports, reporter identity, media, or precise report geometry would turn a staff planning tool into an unnecessary privacy exposure.

**Reasoning:**
1. **Analytical integrity:** Event ownership provides one stable historical identity regardless of how many reports support it or how many live-zone adjustments occur. Rejected and deleted reports are excluded, and normalized locations are counted once per event.
2. **Operational separation:** Live avoidance zones remain the routing source of truth. Historical map layers are isolated from active routing layers, so selecting or filtering history cannot alter navigation behavior.
3. **Privacy by default:** Analytics and CSV/JSON planning exports provide event-level dates, status, peak severity, duration, normalized places, and aggregate supporting-report counts only. Full source evidence remains available to authorized staff in context.
4. **Comprehensible visual semantics:** The dashboard labels the combination chart's event and report series separately, uses a peak-severity doughnut, official-duration distribution, ranked recurrence views, and an accessible timing heatmap. These views answer distinct planning questions without treating color or evidence volume as incident frequency.

**Consequences:**
- `/admin/flood-history` is an admin-only planning and records workspace, not a public incident feed or an Archive Center substitute.
- `build_flood_event_history_query` is shared by history, analytics, and export paths so filters resolve the same authorized event set.
- New historical metrics must preserve the one-event-one-count contract and document any non-event confidence measure explicitly.

**Files Modified:**
- [`backend/app/services/flood_event_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/flood_event_service.py) — Shared event query, distinct-event planning aggregation, and privacy-safe event record serialization.
- [`backend/app/api/v1/endpoints/admin.py`](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py) — Admin-protected analytics and CSV/JSON export endpoints.
- [`frontend/src/features/flood-history/FloodEventAnalytics.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/flood-history/FloodEventAnalytics.tsx) and [`FloodEventVisualizations.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/flood-history/FloodEventVisualizations.tsx) — Responsive analytics, filter, export, and error-state presentation.
- [`frontend/src/features/flood-history/HistoricalEventsMap.tsx`](file:///d:/Documents/Github/LANES/frontend/src/features/flood-history/HistoricalEventsMap.tsx) — Historical-only event footprint layers and accessible severity/selection legend.

---

## 21. Smart Auto-Activation and Supporting LLM Auditor Architecture for Trusted News
**Date:** September 2026  
**Decision:** Adopt Option 2 (Smart Auto-Activation) where complete flood reports from verified Philippine news sources are automatically approved directly into live Valhalla routing avoidance zones and official PostGIS flood events without admin bottleneck. Gemini 1.5 Flash is strictly confined to a Supporting Auditor / Double-Check role to verify claims rather than hallucinating from scratch; receded waters ("humupa na") and forecasts ("posibleng bahain") are strictly suppressed with zero created avoidance zones.

**Context:**
The previous workflow required administrators to manually inspect and approve every single ingested flood candidate before any avoidance zone or event could be created. Because news reports from accredited publishers (GMA News, Inquirer, Rappler, SunStar, etc.) are already vetted public intelligence, this manual queue created unnecessary delays during live flash-flood emergencies. Simultaneously, relying on an LLM to parse entire articles from scratch created hallucination risks and latency.

**Architectural Shifts & Technical Strategy:**
1. **Explicit Division of Labor:** Deterministic Taglish rules and the 43,778 official PSA PSGC reference dataset (`philippine_location_service.py`) act as the lead extractor for place and canonical depth (`gutter`..`neck`). Gemini 1.5 Flash acts strictly as a double-check auditor, answering targeted verification queries on the candidate claim and evidence sentence.
2. **Smart Auto-Activation Engine:** [`news_auto_ingestion_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/news_auto_ingestion_service.py) automatically provisions the approved `FloodReport`, official `FloodEvent`, and operational `FloodAvoidanceZone` atomically when confidence reaches $\ge 95\%$ and depth, road, and active status are confirmed.
3. **Safety Suppression Gates:** News reports indicating that floodwaters have already subsided or receded (*"humupa na"*) or statements that are merely future weather predictions (*"posibleng bahain"*) are strictly suppressed, creating zero avoidance zones and keeping passable roads open.
4. **Nationwide Geometry Service:** [`nationwide_geometry_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/nationwide_geometry_service.py) constructs authoritative 50m road corridor polygons and circular buffer polygons (GeoJSON SRID 4326) across Luzon, Visayas, and Mindanao without hardcoded place lists in Python source code.

**Consequences:**
- Complete active flood reports update the live map and Valhalla routing avoidance instantly without waiting for an administrator.
- Zero risk of closing dry roads due to old receded flood reports or weather forecasts.
- Ambiguous or city-level only reports remain enqueued in the staff review queue with pre-computed candidate geometry for 1-click verification.
- Completely adheres to existing 3NF database schemas with zero schema migrations required.

**Files Created / Modified:**
- [`backend/app/services/hybrid_extraction_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/hybrid_extraction_service.py) — 4-tier hybrid ensemble with Gemini 1.5 Flash supporting auditor.
- [`backend/app/services/nationwide_geometry_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/nationwide_geometry_service.py) — Nationwide hierarchy resolution, 50m corridor polygon generation, and city safety guards.
- [`backend/app/services/news_auto_ingestion_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/news_auto_ingestion_service.py) — Smart Auto-Activation transaction engine.
- [`backend/app/services/philippine_location_service.py`](file:///d:/Documents/Github/LANES/backend/app/services/philippine_location_service.py) — Official PSA PSGC dataset index (43,778 records).
- [`docs/plans/smart-auto-activation-and-hybrid-nlp-plan.md`](file:///d:/Documents/Github/LANES/docs/plans/smart-auto-activation-and-hybrid-nlp-plan.md) — Authoritative plan and architecture documentation.
- Test suites: [`test_hybrid_extraction_service.py`](file:///d:/Documents/Github/LANES/backend/tests/test_hybrid_extraction_service.py), [`test_nationwide_geometry.py`](file:///d:/Documents/Github/LANES/backend/tests/test_nationwide_geometry.py), [`test_news_auto_ingestion.py`](file:///d:/Documents/Github/LANES/backend/tests/test_news_auto_ingestion.py) — 45/45 passing tests.
