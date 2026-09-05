# LANES - Full System Documentation

> **Last Updated:** September 6, 2026, 2:32 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
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
| `NotificationBell.tsx` | `src/features/notifications/NotificationBell.tsx` | A floating bell icon (bottom-right corner, desktop). Shows an unread count badge. Clicking opens a dropdown of recent notifications (likes, comments, system alerts). Listens to a real-time SSE stream from the backend. |
| `GlobalMap.tsx` | `src/features/map/GlobalMap.tsx` | Mounts the map instance globally via `providers.tsx` so it persists across all page navigations. Manages which map panels are open (Route, Analytics, Save Place, Flood Report, Offline Manager). |
| `providers.tsx` | `src/app/providers.tsx` | Wraps children with `MapContextProvider` and mounts `GlobalMap`. This is why the map is always rendered even when visiting non-map pages. |

---

## 2. Landing Page (/)

**Route file:** `src/app/page.tsx` → renders `<LandingView />`

### Always Visible on Load

| File | What You See |
|------|-------------|
| `LandingView.tsx` | `src/features/landing/LandingView.tsx` — The entire landing page layout. Contains the hero section (headline, CTA buttons), stats row, features grid, how-it-works steps, and footer. Also tracks page visits by calling the `/public/visit` backend endpoint on mount. |
| `HomeStats.tsx` | `src/features/landing/HomeStats.tsx` — The three animated stat counters (Total Reports, Verified Zones, Total Visitors) displayed in the hero section. Fetches live counts from the backend `/public/stats` endpoint. |
| `WeatherWidget.tsx` | `src/features/landing/WeatherWidget.tsx` — A compact weather card showing current temperature, humidity, and a short description for Metro Manila. Fetches from the backend `/weather/current` endpoint. |
| `ForecastChart.tsx` | `src/features/landing/ForecastChart.tsx` — A 7-day rainfall/temperature forecast chart (Recharts line chart) displayed below the weather widget. |
| `FloodLegend.tsx` | `src/features/landing/FloodLegend.tsx` — A small color-coded legend card explaining what each flood severity color (Low / Medium / High / Extreme) means. Static, no API calls. |

### Hidden Until Interaction

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `WeatherInsightsModal.tsx` | `src/features/landing/WeatherInsightsModal.tsx` — Click the **"See Full Forecast"** button on the weather widget | Full-screen modal with detailed hourly and 7-day weather forecast, rain probability bar charts, and wind speed data. All data from the backend `/weather/forecast` endpoint. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/public/visit` | Increments the visitor counter in the DB |
| `GET /api/v1/public/stats` | Returns total reports, verified zones, visitor count |
| `GET /api/v1/weather/current` | Current weather for Metro Manila |
| `GET /api/v1/weather/forecast` | 7-day weather forecast data |

---

## 3. Map Page (/map)

**Route file:** `src/app/map/page.tsx` — This page renders an empty `<main>` tag. The actual map is mounted by `GlobalMap` in `providers.tsx` and is always present on screen.

### Always Visible on the Map

| File | What You See |
|------|-------------|
| `MapCanvas.tsx` | `src/features/map/MapCanvas.tsx` — The core MapLibre GL v5 map canvas. Renders 3D Terrain via AWS Terrarium DEM tiles, dynamic vector basemap styles via `MapStylePickerControl` (5 styles), flood avoidance zone polygons (controlled seamlessly via zoom-based opacity steps), user location marker, route polylines, and all map controls (ZoomLevelControl with Pitch telemetry, Toggle3DControl, compass, scale bar). On desktop, offset to the right of the 340px RoutePanel. |
| `BaseMap.tsx` | `src/shared/ui/BaseMap.tsx` — Low-level wrapper around MapLibre GL JS. Manages the map instance lifecycle and exposes an `onMapLoad` callback. |
| `RoutePanel.tsx` | `src/features/routing/RoutePanel.tsx` — The 340px-wide fixed sidebar on the left (desktop). Contains the engine switcher (Valhalla / OpenRouteService), vehicle profile selector (Car / Bike / Walk), start and destination location inputs with autocomplete, a swap/reverse button between the two inputs, and the calculated route results (distance, time, turn-by-turn steps). On mobile this becomes a bottom drawer. Always mounted on non-admin pages. |
| `FloodReportPanel.tsx` | `src/features/hazards/FloodReportPanel.tsx` — The collapsible "Report Flood" panel. On desktop, always shown collapsed with a header. Expanding it reveals a form with severity selector, flood depth input, location picker, photo upload, and survey questions. On mobile, shown only when the user taps the Report Flood button. |
| `OfflineManager.tsx` | `src/components/Map/OfflineManager.tsx` — The "Offline Routing — Ready for offline use" status indicator at the bottom of the RoutePanel. Shows whether the offline tile cache and Valhalla routing data are downloaded and ready. |
| `MapPickerMobileOverlay.tsx` | `src/features/map/MapPickerMobileOverlay.tsx` — A translucent overlay with a centered crosshair that appears on mobile when the user taps a location input, letting them drag the map to pin a point. |

### Hidden Until Interaction (Map Panels)

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `SavePlacePanel.tsx` | `src/features/places/SavePlacePanel.tsx` — Click the ❤️ (heart) icon in the right floating controls | A panel for saving a custom named location (Home, Work, School, etc.) with an icon picker and address field. Saves to the backend. |
| `AnalyticsPanel.tsx` | `src/features/analytics/AnalyticsPanel.tsx` — Click the 📊 (chart) icon in the right floating controls | A floating panel showing flood report analytics: active zone count, severity breakdown, and recent activity feed. |
| `LocationAutocomplete.tsx` | `src/shared/ui/LocationAutocomplete.tsx` — Typing in the Start or Destination input inside RoutePanel | A dropdown of geocoded place name suggestions powered by Nominatim via the backend. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/reports/zones` | Fetches all active flood avoidance zone polygons to render on the map |
| `POST /api/v1/reports/` | Submits a new flood report from the FloodReportPanel form |
| `POST /api/v1/routing/calculate` | Calculates a route via Valhalla or ORS, injecting avoidance zones as exclusion polygons |
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
| `FeedPage.tsx` | `src/features/feed/FeedPage.tsx` — The main three-column feed layout. Center column shows the scrollable list of `PostItem` cards. Left and right sidebars are pinned on desktop. Fetches paginated posts on load. |
| `LeftSidebar.tsx` | `src/features/feed/LeftSidebar.tsx` — Left panel (desktop only). Shows the logged-in user's avatar, display name, trust score badge, and quick stats (reports submitted, accuracy rate). Also has a "Create Post" shortcut button. |
| `RightSidebar.tsx` | `src/features/feed/RightSidebar.tsx` — Right panel (desktop only). Shows community highlights: top contributors, recent active flood zones, and trending location tags. |
| `PostItem.tsx` | `src/features/feed/PostItem.tsx` — A single post card in the feed. Shows author avatar/name/role, post text, attached images, flood severity badge (if linked to a report), upvote/downvote buttons with counts, and comment count. Clicking the post body navigates to the full post detail page. |
| `EmergencyHotlinesCard.tsx` | `src/features/feed/components/EmergencyHotlinesCard.tsx` — API-backed priority emergency contacts with expandable numbers, direct `tel:` links, loading/unavailable states, and a full-directory trigger. Rendered in the feed sidebar layout. |

### Hidden Until Interaction

| File | How to Trigger It | What It Shows |
|------|-------------------|--------------|
| `CreatePostModal.tsx` | `src/features/feed/CreatePostModal.tsx` — Click **"Create Post"** or the **"+"** floating button | Full-screen modal with a rich text area, drag-and-drop image upload, optional location tag, and a flood report linking selector. Submits to `POST /api/v1/feed/posts`. |
| `EmergencyDirectoryModal.tsx` | `src/features/feed/components/EmergencyDirectoryModal.tsx` — Click **"View All Hotlines"** | Lazily loaded national, Pasig city, and Pasig barangay hotline directory with tabbed sections, search, and phone links. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/feed/posts?page=&limit=` | Paginated list of community posts |
| `POST /api/v1/feed/posts` | Create a new community post |
| `POST /api/v1/feed/posts/{id}/interact` | Upvote or downvote a post |
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
| `ProfileView.tsx` | `src/features/profile/ProfileView.tsx` — The full profile page split into tabs: **Personal Info** (name, contact, birthdate, address form), **Security** (change password + OTP verification), **Saved Places** (list of bookmarked map locations), **Privacy** (toggle profile visibility and full name display), and **Trust Score** (gamified accuracy stats showing a score bar, reports submitted, approved, rejected, accuracy rate). |
| `SavedRoutesList.tsx` | `src/features/profile/SavedRoutesList.tsx` — Sub-component inside ProfileView that lists the user's saved map places with their custom icons and addresses, and a delete button for each. |

### Backend Calls from This Page

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/users/me` | Load current user's full profile data |
| `PUT /api/v1/users/me` | Update profile fields |
| `PUT /api/v1/users/me/password` | Change password (requires current password) |
| `POST /api/v1/auth/request-otp` | Send OTP to email for re-verification |
| `POST /api/v1/auth/verify-otp` | Verify an OTP code |
| `GET /api/v1/users/me/saved-places` | Load saved places list |
| `DELETE /api/v1/users/me/saved-places/{id}` | Delete a saved place bookmark |

---

## 7. Auth Pages

### Login Page (/login)

| File | What You See |
|------|-------------|
| `LoginForm.tsx` | `src/features/auth/LoginForm.tsx` — Email + password fields, a "Forgot Password?" link, and a "Sign Up" redirect link. On submit, calls `POST /api/v1/auth/login`. The returned JWT is stored in `localStorage`. |

### Register Page (/register)

| File | What You See |
|------|-------------|
| `SignupForm.tsx` | `src/features/auth/SignupForm.tsx` — Registration form with username, email, password, and confirm password fields. On submit calls `POST /api/v1/auth/register`, which triggers an OTP email via Brevo SMTP and then redirects to `/verify`. |

### Verify Page (/verify)

| File | What You See |
|------|-------------|
| OTP input page | Six-digit OTP code input. Calls `POST /api/v1/auth/verify-otp`. On success, the account becomes active and the user is redirected to `/map`. A "Resend Code" button calls `POST /api/v1/auth/request-otp`. |

### Backend Calls

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/auth/login` | Authenticates and returns a JWT access token |
| `POST /api/v1/auth/register` | Creates a new user account and sends OTP via email |
| `POST /api/v1/auth/verify-otp` | Marks the account as active after OTP verification |
| `POST /api/v1/auth/request-otp` | Resend a new OTP to the email |
| `POST /api/v1/auth/logout` | Invalidates the current JWT server-side |

---

## 8. About Page (/about)

**Route file:** `src/app/about/page.tsx`

A static informational page with no backend API calls. Describes the LANES project mission, team, and the technology stack used (Next.js, FastAPI, PostGIS, Valhalla).

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
| `/admin/map` | `LiveMapPage.tsx` | Full-screen admin map & spatial operations view (persistently mounted in `AdminLayout`). Moderation happens entirely here: features `PendingReportsPanel` for approving/rejecting user reports, `ActiveZonesPanel` for monitoring ongoing floods, `ReportDetailsModal` for deep inspection of MultiLineString and Polygon geometries, `FloodZonePopup` hover badge engine with a 400ms non-resetting dwell timer and ceiling-collision prevention, and `CreateOfficialZonePanel` with **Terra Draw** (Polygon, Freehand, Rectangle, Circle, and Line modes) for manual DRRMO override polygon map picking. |
| `/admin/users` | `UsersPage.tsx` | Searchable table of all registered users. Admin can filter by role, view trust scores, activate or deactivate accounts, and reassign roles. |
| `/admin/roles` | `RolesPage.tsx` | Role management. Create new roles with a granular permission matrix (view / manage / full per module). Edit or delete existing roles. |
| `/admin/data` | `DataManagementPage.tsx` | Data import/export tools. Upload flood report CSVs, export reports as JSON or CSV, and inspect raw PostGIS geometry for any record. |
| `/admin/audit` | `AuditTrailPage.tsx` | Chronological log of all admin actions — who did what, when, and on which record. Filterable by admin user, action type, and date range. |
| `/admin/settings` | `SystemSettingsPage.tsx` | Key-value configuration editor for runtime settings (e.g., flood zone expiry duration in hours, severity thresholds). |

### Backend Calls (Admin)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/admin/reports` | Paginated admin view of all reports with filters |
| `PUT /api/v1/admin/reports/{id}/approve` | Approve report, auto-generates flood avoidance zone polygon |
| `PUT /api/v1/admin/reports/{id}/reject` | Reject report with a reason (updates trust score) |
| `PUT /api/v1/admin/reports/merge` | Merge multiple reports into one shared avoidance zone |
| `GET /api/v1/admin/users` | All users with role and profile info |
| `PUT /api/v1/admin/users/{id}` | Update user role or active status |
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

---

## 11. Backend API Reference

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
| **Routing Engine Proxy** | Forwards route calculation requests to Valhalla (primary) or OpenRouteService (secondary), injecting active `flood_avoidance_zones` polygons as exclusion areas so routes avoid flooded roads |
| **Zone Deduplication** | When a new flood report is approved near an existing active zone (within a configurable buffer distance), it is linked to that zone instead of creating a new duplicate polygon |
| **Trust Score Engine** | Automatically recalculates a user's `trust_score`, `accuracy_rate`, and report counters in `profiles` whenever one of their reports is approved or rejected |
| **Weather Proxy** | Fetches data from the OpenWeatherMap API, transforms and caches the response, and serves it to the frontend |
| **SSE Broadcaster** | Pushes real-time notification events to connected authenticated clients via Server-Sent Events, avoiding battery-draining WebSocket connections |
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

Spatial polygon buffers generated around approved flood reports. Used by the routing engine to reroute traffic around flooded areas.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer, PK | Auto-increment ID |
| `curated_by_admin_id` | FK → users.id, nullable | Admin who manually edited this zone's geometry (null if auto-generated) |
| `geometry` | PostGIS POLYGON (SRID 4326) | The actual closed polygon boundary of the avoidance area |
| `is_active` | Boolean | Whether this zone is currently applied to route calculations |
| `created_at` | DateTime | When the zone was generated or created |
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
| `created_at` | DateTime | Post creation time |
| `updated_at` | DateTime | Last edit time |

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
