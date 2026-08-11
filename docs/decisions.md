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
