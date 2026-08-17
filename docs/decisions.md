# LANES: Architecture & Design Decisions

This document tracks major technical decisions, architecture shifts, and the reasoning behind them to ensure future maintainability and a clear record of "why" certain technologies were chosen.

## 1. Real-time Signaling: WebSockets vs. Server-Sent Events (SSE)
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

## 2. Authentication: JWT Tokens in LocalStorage vs. HttpOnly Cookies
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

## 3. Local Network Configuration (CORS & Proxying)
**Date:** August 2026
**Decision:** Restrict backend CORS to specific Local Area Network (LAN) IP ranges and utilize Next.js rewrites for proxying.

**Context:**
To test the app across multiple smartphones on the same WiFi network, hardcoding `localhost` causes connection failures on mobile devices (since `localhost` on a phone points to the phone itself, not the dev laptop).

**Reasoning:**
1. **Dynamic Backend URL:** The Next.js frontend `next.config.ts` was updated to read `process.env.BACKEND_URL`, defaulting to `127.0.0.1`. By setting `NEXT_PUBLIC_API_URL` to the host computer's IPv4 address, mobile devices can reach the backend.
2. **CORS Hardening:** The previous wildcard (`*`) CORS setting was highly insecure. It was replaced with a regex `^https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000$` that strictly allows local WiFi connections (e.g., `192.168.x.x`), preventing unauthorized external domains from accessing the API while still allowing local mobile testing.

---

## 4. Modular Map Architecture: Imperative Hook Pattern & BaseMap
**Date:** August 2026
**Decision:** Decouple MapLibre initialization from feature layers using a pure `<BaseMap>` component and modular React hooks (`useCityBoundaries`, `useFloodZonesLayer`).

**Context:**
Originally, MapLibre instances were independently constructed in `MapCanvas.tsx` (commuter map) and `LiveMapPage.tsx` (admin live map). This led to duplicated map control styling, boundary fetching logic, and inconsistent layer behaviors between commuter and admin views. Furthermore, road-based flood reports had their geometric polygons hidden (`is_road_based == false`), showing only street line glows, which prevented admins and commuters from seeing exact flood boundaries.

**Reasoning for the Switch:**
1. **Imperative Hook Pattern (Standard React MapLibre Architecture):** Raw MapLibre GL JS operates imperatively on a canvas. Creating a bare `<BaseMap>` that handles canvas mounting, tile style fallbacks (MapTiler -> OpenStreetMap), `TopViewControlV3`, and native navigation controls allows any page to instantiate a styled map effortlessly.
2. **Pluggable Layer Hooks:** By extracting spatial datasets into custom hooks (e.g., `useCityBoundaries(map, isLoaded)` and `useFloodZonesLayer(map, isLoaded, activeZones)`), any future page can compose any combination of map layers (e.g., map with floods but no borders, or map with borders but no floods) in a single line of code without duplicating initialization logic.
3. **Unified Flood Polygons & Severity Color Scale:** Removed the restriction hiding road-based flood polygons so both admins and commuters see exact spatial flood hazard boundaries. Standardized the 4-tier color scale (`low`: Lime `#84cc16`, `medium`: Amber `#eab308`, `high`: Orange `#f97316`, `extreme`: Red `#ef4444`).

---

## 5. 1:N Spatial Relational Deduplication & Trust Score Pooling
**Date:** August 2026
**Decision:** Transition from 1:1 `report_id` on `FloodAvoidanceZone` to 1:N `zone_id` foreign key on `FloodReport` with communal trust score crediting.

**Context:**
During monsoon events, multiple commuters frequently submit independent reports for the same flooded street. Originally, each avoidance zone strictly required a unique `report_id`, creating duplicate conflicting avoidance barriers for the Valhalla routing engine and blocking administrators from merging identical submissions.

**Reasoning & Architecture:**
1. **Relational Inversion (1:N Migration):** Moved the foreign key to `FloodReport.zone_id` referencing `FloodAvoidanceZone.id` (`ondelete="SET NULL"`). This allows a single physical avoidance barrier to encapsulate $N$ crowdsourced reports.
2. **Fair Trust Score Pooling:** Merging or approving a zone iterates across all linked reports to award verified trust points (`+5`) and increment `reports_verified` for every unique contributor, ensuring crowdsourced contributions are recognized without polluting the map.
3. **Proximity Search via PostGIS:** Utilizes `ST_DWithin` on the backend (`/api/v1/admin/zones/nearby`) to automatically detect existing active zones within 200–500m of incoming reports.

---

## 6. Shared Fluid UI Design System & Anti Box-in-a-Box Standard
**Date:** August 2026
**Decision:** Standardize multi-variant animated Tabs (`shared/ui/Tabs.tsx`) and full-bleed edge-to-edge spatial dashboards.

**Context:**
Different admin and profile pages used isolated tab implementations, leading to visual inconsistencies, frame nesting ("container inside container" syndrome), and horizontal scrollbar flicker during framer-motion transitions.

**Reasoning & Architecture:**
1. **Consolidated Tab Component (`Tabs.tsx`):** Implemented a shared component supporting `segmented`, `underline`, and `pills` variants with direction-aware sliding indicators and hidden overflow wrappers (`[scrollbar-width:none]`).
2. **Full-Bleed Spatial Workspaces:** Refactored `AdminLayout` to conditionally strip outer padding (`p-0` on `/admin/map`) while preserving padding on data tables, maximizing screen real estate for map operations.
3. **Viewport Auto-Fit & Persistence:** Integrated automatic Pasig City bounding box fitting (`[121.0515, 14.5338]` to `[121.1112, 14.6235]`) on first load, coupled with `localStorage` camera state tracking to persist user zoom/pan coordinates across navigation.

---

## 7. Unified Map Layer Zoom Hierarchy & Multi-Reporter Spatial Inspection
**Date:** August 2026
**Decision:** Standardize zoom thresholds ($Z \le 14$ vs. $Z > 14$) with shared tokens in `mapStyles.ts` and implement inline contributor inspection without blocking modals.

**Context:**
# LANES: Architecture & Design Decisions

This document tracks major technical decisions, architecture shifts, and the reasoning behind them to ensure future maintainability and a clear record of "why" certain technologies were chosen.

## 1. Real-time Signaling: WebSockets vs. Server-Sent Events (SSE)
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

## 2. Authentication: JWT Tokens in LocalStorage vs. HttpOnly Cookies
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

## 3. Local Network Configuration (CORS & Proxying)
**Date:** August 2026
**Decision:** Restrict backend CORS to specific Local Area Network (LAN) IP ranges and utilize Next.js rewrites for proxying.

**Context:**
To test the app across multiple smartphones on the same WiFi network, hardcoding `localhost` causes connection failures on mobile devices (since `localhost` on a phone points to the phone itself, not the dev laptop).

**Reasoning:**
1. **Dynamic Backend URL:** The Next.js frontend `next.config.ts` was updated to read `process.env.BACKEND_URL`, defaulting to `127.0.0.1`. By setting `NEXT_PUBLIC_API_URL` to the host computer's IPv4 address, mobile devices can reach the backend.
2. **CORS Hardening:** The previous wildcard (`*`) CORS setting was highly insecure. It was replaced with a regex `^https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000$` that strictly allows local WiFi connections (e.g., `192.168.x.x`), preventing unauthorized external domains from accessing the API while still allowing local mobile testing.

---

## 4. Modular Map Architecture: Imperative Hook Pattern & BaseMap
**Date:** August 2026
**Decision:** Decouple MapLibre initialization from feature layers using a pure `<BaseMap>` component and modular React hooks (`useCityBoundaries`, `useFloodZonesLayer`).

**Context:**
Originally, MapLibre instances were independently constructed in `MapCanvas.tsx` (commuter map) and `LiveMapPage.tsx` (admin live map). This led to duplicated map control styling, boundary fetching logic, and inconsistent layer behaviors between commuter and admin views. Furthermore, road-based flood reports had their geometric polygons hidden (`is_road_based == false`), showing only street line glows, which prevented admins and commuters from seeing exact flood boundaries.

**Reasoning for the Switch:**
1. **Imperative Hook Pattern (Standard React MapLibre Architecture):** Raw MapLibre GL JS operates imperatively on a canvas. Creating a bare `<BaseMap>` that handles canvas mounting, tile style fallbacks (MapTiler -> OpenStreetMap), `TopViewControlV3`, and native navigation controls allows any page to instantiate a styled map effortlessly.
2. **Pluggable Layer Hooks:** By extracting spatial datasets into custom hooks (e.g., `useCityBoundaries(map, isLoaded)` and `useFloodZonesLayer(map, isLoaded, activeZones)`), any future page can compose any combination of map layers (e.g., map with floods but no borders, or map with borders but no floods) in a single line of code without duplicating initialization logic.
3. **Unified Flood Polygons & Severity Color Scale:** Removed the restriction hiding road-based flood polygons so both admins and commuters see exact spatial flood hazard boundaries. Standardized the 4-tier color scale (`low`: Lime `#84cc16`, `medium`: Amber `#eab308`, `high`: Orange `#f97316`, `extreme`: Red `#ef4444`).

---

## 5. 1:N Spatial Relational Deduplication & Trust Score Pooling
**Date:** August 2026
**Decision:** Transition from 1:1 `report_id` on `FloodAvoidanceZone` to 1:N `zone_id` foreign key on `FloodReport` with communal trust score crediting.

**Context:**
During monsoon events, multiple commuters frequently submit independent reports for the same flooded street. Originally, each avoidance zone strictly required a unique `report_id`, creating duplicate conflicting avoidance barriers for the Valhalla routing engine and blocking administrators from merging identical submissions.

**Reasoning & Architecture:**
1. **Relational Inversion (1:N Migration):** Moved the foreign key to `FloodReport.zone_id` referencing `FloodAvoidanceZone.id` (`ondelete="SET NULL"`). This allows a single physical avoidance barrier to encapsulate $N$ crowdsourced reports.
2. **Fair Trust Score Pooling:** Merging or approving a zone iterates across all linked reports to award verified trust points (`+5`) and increment `reports_verified` for every unique contributor, ensuring crowdsourced contributions are recognized without polluting the map.
3. **Proximity Search via PostGIS:** Utilizes `ST_DWithin` on the backend (`/api/v1/admin/zones/nearby`) to automatically detect existing active zones within 200–500m of incoming reports.

---

## 6. Shared Fluid UI Design System & Anti Box-in-a-Box Standard
**Date:** August 2026
**Decision:** Standardize multi-variant animated Tabs (`shared/ui/Tabs.tsx`) and full-bleed edge-to-edge spatial dashboards.

**Context:**
Different admin and profile pages used isolated tab implementations, leading to visual inconsistencies, frame nesting ("container inside container" syndrome), and horizontal scrollbar flicker during framer-motion transitions.

**Reasoning & Architecture:**
1. **Consolidated Tab Component (`Tabs.tsx`):** Implemented a shared component supporting `segmented`, `underline`, and `pills` variants with direction-aware sliding indicators and hidden overflow wrappers (`[scrollbar-width:none]`).
2. **Full-Bleed Spatial Workspaces:** Refactored `AdminLayout` to conditionally strip outer padding (`p-0` on `/admin/map`) while preserving padding on data tables, maximizing screen real estate for map operations.
3. **Viewport Auto-Fit & Persistence:** Integrated automatic Pasig City bounding box fitting (`[121.0515, 14.5338]` to `[121.1112, 14.6235]`) on first load, coupled with `localStorage` camera state tracking to persist user zoom/pan coordinates across navigation.

---

## 7. Unified Map Layer Zoom Hierarchy & Multi-Reporter Spatial Inspection
**Date:** August 2026
**Decision:** Standardize zoom thresholds ($Z \le 14$ vs. $Z > 14$) with shared tokens in `mapStyles.ts` and implement inline contributor inspection without blocking modals.

**Context:**
City overview views and street-level views previously had conflicting layer styles, duplicate road glows, and harsh outline borders on avoidance buffers. Additionally, merged avoidance zones obscured individual contributor reports.

**Reasoning & Architecture:**
1. **Strict Zoom Separation ($Z=14$ Cutoff)**:
   - **City Overview ($Z \le 14$)**: Uses solid filled circle pins with darker contrast borders matching the severity level (Olive for Lime, Dark Amber for Yellow, Rust for Orange, Maroon for Red) for optimal visibility against white basemap tiles.
   - **Street Level ($Z > 14$)**: Completely eliminates all outline borders. Avoidance zones render as pure transparent $50\text{m}$ buffer auras with bold solid road centerlines. Pending reports render as pure transparent glowing auras.
2. **Inline Contributor Accordion vs. Modal**:
   - Instead of interrupting the admin with screen-blocking dialogs, merged zones feature an inline animated drawer (`ActiveZonesPanel.tsx`) showing each contributor's avatar, timestamp, trust score, and quote.
3. **Dynamic Single-Report Map Focus**:
   - Clicking an individual contributor temporarily isolates their exact original report geometry on the map while hiding the merged avoidance zone, allowing fine-grained spatial verification.

---

## 8. Admin Navigation Refactoring
**Date:** August 2026
**Decision:** Decompose `AdminNav.tsx` into modular configuration and layout components.

**Context:**
The admin interface originally contained a large, monolithic `AdminNav.tsx` file combining routing, UI layouts, styling, icons, and badge calculation logic in a single 150-line component. This proved brittle and difficult to maintain.

**Reasoning:**
1. **Separation of Concerns:** Routing arrays were split out into `routes.ts`, and helper badge hooks (like `usePendingBadge`) were isolated. `AdminLayout.tsx` handles pure wrapping structure.
2. **Readability:** Extracting the configuration dramatically reduces the lines of code in the actual layout wrapper. Adding a new route is now a simple data entry task in `routes.ts` rather than a JSX structure modification.

---

## 9. MapLibre Dynamic Layer Updating: Avoid `isStyleLoaded()` Strict Checks
**Date:** August 2026
**Decision:** Remove strict `map.isStyleLoaded()` checks when dynamically updating vector layers (GeoJSON) and utilize `setData()` rather than tearing down and rebuilding layers.

**Context:**
When active flood zones were added to the map using `useFloodZonesLayer.ts`, the zones often completely failed to render on initial page load, failing silently without errors.

**Reasoning:**
1. **The "Silent Deadlock":** MapLibre's `isStyleLoaded()` method is extremely strict. While intuitively it seems to mean "is the base map ready", it actually means "is the map 100% idle with no pending vector tile downloads". When the map loads, it immediately begins fetching background street tiles. If a React hook checks `isStyleLoaded()` during this time, it returns `false`, causing the hook to abort silently. Waiting for a `styledata` event is ineffective because `styledata` only fires when the JSON style itself changes, not when tiles finish downloading.
2. **The Failsafe `getStyle()`:** MapLibre is perfectly capable of parsing and queuing custom sources/layers even while background tiles download. Removing `isStyleLoaded()` and simply verifying `map.getStyle()` exists prevents the deadlock.
3. **`setData()` Optimization:** Repeatedly calling `removeLayer` and `removeSource` on every React re-render can cause visual flickering and MapLibre race conditions. Using `.setData()` on the existing GeoJSON source is the native, performant way to push data updates into MapLibre.
