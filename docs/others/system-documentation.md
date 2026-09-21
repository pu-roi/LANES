# LANES - Full System Documentation

> **Last Updated:** September 21, 2026, 2:39 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

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
| `FloodLegend.tsx` | `src/features/landing/FloodLegend.tsx` — A small color-coded legend card explaining what each flood severity color (Low / Medium / High / Extreme) means. Static, no API calls. |

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
| `BaseMap.tsx` | `src/shared/ui/map/BaseMap.tsx` — Low-level MapLibre wrapper that owns one WebGL map instance, resize observation, and `onMapInit`/`onMapLoad` callbacks. It begins with MapTiler when configured, treats the first rendered frame after `style.load` as usable, and falls back to a LANES-identified OSM raster style only on a MapTiler resource error or exhausted 1.5-second budget. It retries MapTiler on reconnect/backoff. `style.load` preserves LANES-owned layers after each style replacement. A compact viewport-anchored status remains clear of the desktop floating navigation and wraps on smaller screens; document-level connection hints and production PWA caching accelerate MapTiler repeat visits. |
| `RoutePanel.tsx` | `src/features/routing/RoutePanel.tsx` — The left sidebar on desktop (collapsible on mobile). Contains the travel profile selector (including **Bike/Motorcycle**), start/destination inputs with focus guards and smart two-click "Choose on Map" advance, authenticated saved places chips with Start/End-preserving recalculation, and up to four navigable route cards categorized as Fastest, Safest, Balanced, and Alternative. Cards render route-specific flood exposure; a rejected fastest baseline is explanation-only, never selectable. |
| `FloodReportPanel.tsx` | `src/features/hazards/FloodReportPanel.tsx` — The responsive incident reporting panel (opens from FAB or top CTA). Step one accepts raw Start/End selections, then submits the verified road-only line or dual-carriageway coverage returned by the shared preview; it never persists a raw sidewalk-to-road connector. When **Share in Community Feed** is checked, the report is published to the feed immediately; only official map-zone visibility awaits administrator approval. Account-private drafts restore only when an active report has a selected road endpoint plus severity, survey data, description, or media; queued reports remain recoverable. UI-only toggles, wizard state, survey visibility, and typed-but-unselected locations never restore a draft. Severity tiles are unselected by default and toggle off when reselected; opt-in two-way coverage is unchecked by default. The compact **Clear** dialog offers neutral **Clear all** (removes previews, queued drafts, media, and the persisted account draft) plus rightmost red **Clear this page** (preserves work on the other page). `useFloodMapPreview.ts` renders each validated carriageway in its own MapLibre source/layer so close parallel geometry remains visible through a style reload. |
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
| `POST /api/v1/routing/calculate` | Loads authoritative active PostGIS zones once, obtains Valhalla or ORS candidates with hard/cautious avoidance, evaluates each actual geometry under one server-side policy, removes ineligible paths, and returns at most four distinct categorized routes plus an optional non-selectable blocked-baseline explanation. |
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
| `/admin/dashboard` | `DashboardPage.tsx` | Overview cards: total users, reports filed today, currently active flood zones. Recent activity feed and quick action shortcuts. |
| `/admin/map` | `LiveMapPage.tsx` | Full-screen admin map & spatial operations view (persistently mounted in `AdminLayout`). Pane 1 contains `PendingReportsPanel` and `ActiveZonesPanel`; Pane 2 shows one of Create Zone, Review Merge, or amber Edit Zone at a time. Pending Reports and Active Zones keep independent current selections. Returning to a tab flies to that tab's selected report or zone only; toggling the selected card or map feature off clears its selection and prevents a later tab switch from moving the map. Create and Edit are separate resumable sessions: the blue Create Zone bookmark retains its account-private draft, while the amber Edit Zone bookmark retains its selected zone and per-admin edit draft; neither replaces or discards the other. Create Zone is always the first desktop handle. Merge and Edit appear only after being opened and are arranged most-recent-first directly below it; switching keeps their component state and scroll position, while explicit Close removes the matching workspace rather than leaving a collapsed handle. The Edit close control is available on desktop and mobile and retains its discard confirmation. Review Merge remains independently resumable. On mobile, Active Zones exposes Create Zone and the shared drawer header can switch to the other available workspace. Normal report focus is neutral. **Review Merge Suggestions** starts a persistent merge session with explicit candidate checkboxes, in-card match evidence, a field comparison matrix, selected-only conflicts, reusable road/Terra Draw editing, confirmation, and primary/candidate/proposed map previews. `zoneDraftStorage.ts` restores Create Zone's active workspace and editable queued drafts. Edit Zone restores only a dirty per-admin draft after fetching the current zone; unchanged and legacy baseline copies are removed silently. It can replace a validated road centreline or reopen the final saved area polygon for Terra Draw vertex editing. A road update stores the new source line and regenerated 25-metre operational buffer; an area update stores the exact polygon and clears obsolete source geometry. It also includes `ReportDetailsModal`, the 400ms `FloodZonePopup` hover engine, and one shared `OfficialZoneDrawer` implementation with `GeometryModeSelector`, `RoadSegmentPicker`, `DraftZoneCart`, five aligned form sections, and Cloudinary media upload. |
| `/admin/users` | `UsersPage.tsx` | Searchable table of all registered users. Admin can filter by role, view trust scores, activate or deactivate accounts, and reassign roles. |
| `/admin/roles` | `RolesPage.tsx` | Role management. Create new roles with a granular permission matrix (view / manage / full per module). Edit or delete existing roles. |
| `/admin/data` | `DataManagementPage.tsx` | Data import/export tools. Upload flood report CSVs, export reports as JSON or CSV, and inspect raw PostGIS geometry for any record. |
| `/admin/audit` | `AuditTrailPage.tsx` | Chronological log of all admin actions — who did what, when, and on which record. Filterable by admin user, action type, and date range. |
| `/admin/moderation` | `ModerationCenterPage.tsx`, `components/FloodModerationQueue.tsx` | Staff-only tabbed Community Post and Flood Report tracking using the shared underline `Tabs` component. Flood cases show their outcome/context and filters, then provide a single **Review on Map** handoff; no spatial approval/rejection controls are duplicated here. The responsive action area remains clear of the mobile bottom navigation. |
| `/admin/flood-history` | `flood-history/page.tsx`, `features/flood-history/*` | Admin-only Flood History & Analytics has a server-calculated distinct-event planning dashboard plus a separate historical `BaseMap` source/layer set for Flood Event Records. Its responsive Recharts visuals include a verified-event/approved-report combination trend, severity doughnut, duration columns, recurrence rankings, and a UTC verification-pattern heatmap with per-cell text labels. Protected filters drive recurrence, roads, peak severity, official duration, and time-series analytics; authorized users can download filtered planning records or aggregate analytics as CSV/JSON without reporter identity, raw evidence, report geometry, or media. The records tab retains synchronized desktop map/list and a mobile-safe map/list switcher, with full original evidence available only in protected event detail. |
| `/admin/settings` | `SystemSettingsPage.tsx` | Key-value configuration editor for runtime settings (e.g., flood zone expiry duration in hours, severity thresholds). |
| `/admin/archive` | `ArchivePage.tsx` | Centralized Archive Center with 30-day auto-purge retention lifecycle across three primary tabs: **Archived Users** (soft-deleted commuter accounts with 30-day countdown badge, restore action, and typed `"DELETE"` permanent purge), **Spatial Data** (dual sub-tabs for soft-deleted/rejected Flood Reports and deactivated/expired Avoidance Zones with detail inspection, Attached Media & Evidence photo/video gallery, reactivation, and typed `"DELETE"` permanent deletion), and **Archived Posts** (dual sub-tabs for Community Feed posts soft-deleted by authors/admins and posts hidden by moderators with full media/author inspection, feed restoration, and typed `"DELETE"` permanent deletion). Includes on-demand manual trigger to purge expired records. |
| `/admin/profile` | `AdminProfilePage.tsx` | Native Admin Profile hub matching public profile design. Super Admins, DRRM Officers, and Moderators can edit personal details, phone number, birthdate, and PSGC address, change account cover banner color, upload or remove avatar images, toggle privacy preferences ("Display Full Name", "Hide Profile Picture"), and securely change account passwords with live `<PasswordStrength>` validation and email OTP verification via `PasswordOtpModal`. Linked from the user profile card in the `AdminSidebar.tsx` footer. |

> **Flood Event lifecycle update (Phase 33):** `/admin/map` remains the only operational moderation workspace. `RejectFloodReportModal` requires a structured reason, keeps rejected evidence out of Archive Center, and notifies the submitting user through the existing bell without disclosing internal notes. Approving/merging a report or directly creating an official zone creates or links a verified Flood Event; server services calculate event metrics, record readable zone/severity timeline entries, and end the event when its final live zone ends.

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
| `roles.py` | `/roles` | Staff roles only |
| `data.py` | `/data` | Staff roles only |
| `settings.py` | `/settings` | Staff roles only |

### Key Backend Services

| Service | What It Does |
|---------|-------------|
| **NLP Location Extractor** | Uses spaCy to parse Taglish flood report text and extract barangay/street location names, storing them in `flood_report_locations` |
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
| `depth` | String(50), nullable | Estimated flood depth description — e.g., "knee-deep", "waist-high" |
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
| `depth_override` | String(50), nullable | Standard visual water depth gauge (e.g. `knee`, `waist`, `chest`) |
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

Single-row running total counter for landing page visit tracking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Always 1 (this table has exactly one row) |
| `total_visitors` | Integer | Cumulative count of landing page visits since deployment |

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

