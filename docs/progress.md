# LANES — Progress Tracker

> Tracking completed milestones, delivered features, and past sprints.

---

## Completed Milestones (31+ Commits Integrated)

| # | Milestone | Status | Key Features Delivered |
|---|-----------|--------|------------------------|
| 1 | Architecture & Core Services | Completed | FastAPI setup, PostGIS routing, PWA support, Modular frontend, Domain-based backend structure |
| 2 | Advanced 3D Map Engine | Completed | 3D MapTiler integration, Pasig boundary overlay, Persistent Global Map, Location Autocomplete |
| 3 | Spatial Flooding & Routing | Completed | Road-based flood highlights, Dynamic route gradients, LineString avoidance logic, Ignore-floods toggle |
| 4 | Immersive UI & Navigation | Completed | Floating animated navigation (Framer Motion), FAB menu, Route picker panel, Split-screen Auth layout |
| 5 | Authentication & Identity | Completed | OTP Registration (Brevo integration), User Profiles, Profile Picture Uploads, Secure Sessions |
| 6 | RBAC & Admin Dashboard | Completed | 3NF DB Normalization, Roles CRUD, User Management, Audit Trails, Data Mgmt & System Settings |
| 7 | Real-Time Operations | Completed | Server-Sent Events (SSE) broadcasting, Live active zones, Real-time admin dashboard invalidations |
| 8 | Community Feed & Moderation | Completed | Feed layout, Upvotes/Downvotes, Post archiving, Soft deletes, Map coordinate rendering |
| 9 | Spatial Analytics & Heatmap | Completed | Global Heatmap, Top Barangays stats, Dedicated Analytics Pages for Commuters and Admins |

## Capstone Roadmap - Delivered Phases

### Phase 1: Audit Trail Synchronization & Full Coverage (🟢 COMPLETED)
- [x] **Backend — Role Management Auditing**:
  - Add `create_audit_log` call to `POST /api/v1/roles` (`CREATE_ROLE`) logging `role_name` and initial `permissions`.
  - Add `create_audit_log` call to `PUT /api/v1/roles/{role_id}` (`UPDATE_ROLE`) logging previous vs. new permissions and name.
  - Add `create_audit_log` call to `DELETE /api/v1/roles/{role_id}` (`DELETE_ROLE`) capturing target role ID and name.
  - Add `create_audit_log` call to `POST /api/v1/roles/{role_id}/clone` (`CLONE_ROLE`) capturing source role ID and cloned role name.
  - Pass `Request` object into each endpoint function to extract `client_ip` via `request.client.host`.
- [x] **Backend — Archive & Soft-Delete Auditing**:
  - Dispatch explicit audit events (`ARCHIVE_REPORT`, `RESTORE_REPORT`, `ARCHIVE_ZONE`, `RESTORE_ZONE`) when flood reports or zones are archived/soft-deleted or restored.
- [x] **Frontend — Badge & Filter Synchronization**:
  - Update `ACTION_BADGES` mapping with styling and human-readable labels for:
    - `UPDATE_ZONE`, `CREATE_USER`, `UPDATE_USER_ROLE`, `CREATE_ROLE`, `UPDATE_ROLE`, `DELETE_ROLE`, `CLONE_ROLE`, `EXPORT_DATA`, `UPDATE_SETTINGS`, `ARCHIVE_REPORT`, `RESTORE_REPORT`, `ARCHIVE_ZONE`, `RESTORE_ZONE`
  - Update the `Filter Activity` `<Select />` options list to include these actions so admins can easily filter the log table.

### Capstone Phase 1: Home Page & Onboarding (🟢 COMPLETED)
- [x] **Dynamic Weather Widget**: Integrate Open-Meteo API with Meteocons (reads from user profile location, defaults to Pasig).
- [x] **Daily Stats**: Show the number of *verified* flood reports for the current day.
- [x] **Site Visitors**: Display a metric for total active/historical site visitors.
- [x] **Flood Status Legend**: Add a clear breakdown of White, Yellow, Orange, and Red on the home page.

### Capstone Phase 2: Map & Routing Engine (🟢 COMPLETED)
- [x] **Vehicle Profiles**: Implement clearance-based routing labels:
  - *4-Wheel High Clearance* (SUVs, Pickups)
  - *4-Wheel Low Clearance* (Sedans, Hatchbacks)
  - *2-Wheels* (Motorcycles, Bicycles)
  - *Pedestrian* (Walking)
- [x] **Route Metrics**: Display "Safety %" and "Flood Risk" directly on alternative route banners.
- [x] **Flood Timelines**: Show when a flood was reported and approved directly on the map popup.
- [x] **Weather & Chart Legend**: Add a sleek UI guide/legend near the forecast chart to explain what the weather icons, rain percentages, and volume numbers mean to everyday users.
- [x] **AI Weather Insights**: Integrate OpenRouter API (`openrouter/free`) into the backend to dynamically generate educational, conversational interpretations of raw weather forecast data.

### Capstone Phase 3: Community Feed & Notifications (🟢 COMPLETED)
- [x] **Report Hazard Button**: Jump straight to the Flood Report Panel.
- [x] **Create Post Button**: Allows users to post text/photos to the community feed with an optional location tag.
- [x] **In-App Notification Center**: Global Bell Icon for comments, likes, and critical system alerts pinned to the top.

### Capstone Phase 4: Admin Panel & Report Moderation (🟢 COMPLETED)
- [x] **Active Zones Full View**: Show timeline, reporter details, and actions (View, Edit, Deactivate, Archive).
- [x] **Admin Dashboard Charts**: 
  - Pie Chart: Flood Severity Distribution.
  - Line Chart: Reports over time (Dynamic: Last 7 Days, Month, Year).
  - Bar Graph: Top 5 Most Flooded Barangays.

### Phase 2: Spatial Moderation, 1:N Deduplication & Fluid Spatial Hub (🟢 SUB-PHASES 2.1–2.3 DELIVERED)
- [x] **Backend — 1:N Relational Schema Migration**:
  - Inverted the foreign key constraint by moving `zone_id` onto `FloodReport` (`ondelete="SET NULL"`) and adding `curated_by_admin_id` to `FloodAvoidanceZone`.
  - Executed Alembic migration `e89a3df04c63_phase2_spatial_dedup_1_to_n.py`.
- [x] **Backend — Spatial Moderation & Proximity Lookup**:
  - Implemented `POST /api/v1/admin/reports/{id}/approve` supporting both `"CREATE_NEW"` and `"MERGE"` zone actions with automatic PostGIS buffer geometry calculation.
  - Implemented `GET /api/v1/admin/zones/nearby` with PostGIS `ST_DWithin` and `ST_Distance` returning nearby active zones within 500m.
  - Implemented `GET /api/v1/admin/reports/by-location` to group overlapping pending reports by street.
- [x] **Backend — Communal Trust Score Crediting**:
  - Updated approval & merge logic to iterate through all linked reports to award verified trust scores (`+5`) and increment `reports_verified` for every unique contributor.
  - Passed automated test suite `backend/tests/test_spatial_merging.py` (100% passing).
- [x] **Frontend — Shared Fluid UI Design System**:
  - Created standardized animated `Tabs.tsx` with `segmented`, `underline`, and `pills` variants and hidden overflow wrappers to eliminate horizontal scrollbar flicker.
  - Standardized tab design across Profile, Live Map, Reports, User Registry, and Archive pages.
- [x] **Frontend — Edge-to-Edge Spatial Workspace & Viewport Persistence**:
  - Refactored `AdminLayout.tsx` and `LiveMapPage.tsx` to remove outer margins/padding (`p-0` on `/admin/map`) for a full-bleed interactive map canvas adhering to Anti Box-in-a-Box rules.
  - Implemented whole-Pasig-City bounding box auto-fitting (`[121.0515, 14.5338]` to `[121.1112, 14.6235]`) on first visit.
  - Implemented persistent camera viewport tracking via `localStorage` restoring exact pan/zoom coordinates across admin page navigation.
  - Guarded MapLibre layer hooks against async style switching and OSM fallback loading.

## Recently Completed
- [x] **Saved Places Feature**: Integrated "Saved Places" with map picking, saved places feed integration, mobile drawer support, custom emoji saving, and database persistence.
- [x] **Progressive Web App (PWA) & UI Fixes** (Installability banner, offline fallback, comment UI overhaul, safe area paddings)
- [x] **Documentation Update**: AGENTS.md and DESIGN.md updated with latest architecture.
- [x] Implement Comments Section for community feed (Threaded quote replies, mention parsing, pin/edit, dynamic focus-within input forms)
- [x] Implement Photon API Reverse Geocoding on backend to extract and save 'barangay' for approved reports
- [x] Create /api/v1/analytics/heatmap and /api/v1/analytics/stats endpoints
- [x] Build /analytics (public) and /admin/analytics pages with MapLibre Heatmap layer and data tables
- [x] Design Decision: Reverse geocoding via Photon is used to resolve barangays dynamically without storing heavy shapefiles
- [x] **Security & Local Networks**: Refactored real-time updates from WebSockets to SSE, applied `slowapi` rate limiting, restricted CORS, and implemented frontend route guards for future APK compatibility.
- [x] **UI/UX Refinements**: 
  - Extracted Login to a standalone page to prepare for future profile customization UI.
  - Fixed map white screen issue occurring after user logout.
  - Removed hover effects from Admin Dashboard severity charts for cleaner UX.
- [x] **Data Integrity**: Ensured specific flood depth strings (e.g., "Half-Knee") are successfully passed from the frontend and explicitly saved into the PostgreSQL `FloodReport` and `FloodAvoidanceZone` records.
- [x] **User Metrics & Profile Page**: 
  - Track metrics and build the frontend Profile UI for users.
  - *Backend Implementation:* Added `reports_submitted`, `reports_approved`, `reports_rejected`, `accuracy_rate`, `trust_score` columns to `profile.py`. Added endpoints `/api/v1/reports/me` and `/api/v1/posts/me` for user activity history. Added address schemas support for profile updating.

  - *Logic:* Trust score starts at 50. +5 for every approved report (cap 100), -10 for rejected (min 0). Accuracy = Approved / (Approved + Rejected).
  - *Frontend Implementation:* Built `ProfileView.tsx` with metrics cards, user details, tabs for "My Reports" and "My Posts", and a robust PSGC-integrated `EditProfileForm` component.
- [x] **Rich Community Posts on Profile Page**:
  - Reused `PostItem` from the feed to bring media galleries, upvotes, comments, and map linking to the user's Profile View.
  - Implemented dynamic scroll-to-stick sidebar logic for the profile metrics pane.
  - Redesigned profile tab navigation to a sleek hypertext style with a bottom-border active indicator.
- [x] **Auth Flow & Security Upgrade (Identity-First)**:
  - Completely restructured the registration flow to be "Identity-First" (Email -> OTP -> Username/Password -> Profile -> Address).
  - Decoupled OTP validation from account creation using new `/api/v1/auth/request-signup-otp` and `/verify-signup-otp` backend endpoints.
  - Seamless automatic login upon successful registration; removed the standalone `/verify` page completely.
  - Added modern "Sign in with Google" UI buttons to the Login and Registration forms.
- [x] **Profile & Feed UI/UX Polish**:
  - Implemented seamless 3-column "Feed Morph" mode for viewing posts inside the Profile page without route switching.
  - Added sticky frosted-glass "Back to Feed" / "Close" buttons for deep comment scrolling.
  - Dynamically hide the mobile notification bell when reading full posts.
  - Fixed full-width cover photo container layout on Profile page.
  - Updated design guidelines to formally ban "Box-in-a-Box Syndrome" for flatter, breathable UI.
- [x] **Dynamic Panel Stacking & Smooth Animations**:
  - Implemented dynamic global Z-indexing engine in `MapContext` allowing windows to pop to the front on-click or on-open (similar to OS windows/browser tabs).
  - Perfected panel dodging choreography: Swapped bouncy spring physics for predictable ease-in-out tween animations. Panels now smoothly collapse (250ms), slide (300ms), and enter with synchronized delays to prevent overlapping or jittering.
  - Fixed Save Place icon selector layout using smart CSS Grid to ensure perfectly distributed rows without trailing white space.
- [x] **Modular Map Architecture & Admin Live Map Overhaul**:
  - Created standalone, unopinionated `<BaseMap>` component (`src/shared/ui/BaseMap.tsx`) for clean map canvas instantiation.
  - Built pluggable layer hooks: `useCityBoundaries` (Pasig/Philippines borders & dark mask) and `useFloodZonesLayer` (active flood polygons, road glows, popups).
  - Merged Admin Live Map & Zones into a split-screen interface powered by `<BaseMap>`.
  - Fixed flood polygon rendering bug: Removed restrictive road-based polygon filter so exact flood polygons are rendered for all active hazard reports.
  - Standardized 4-tier severity color scale: `low` (Lime `#84cc16`), `medium` (Amber `#eab308`), `high` (Orange `#f97316`), `extreme` (Red `#ef4444`).
- [x] **Flood Zone Popup Redesign & Metadata Integration**:
  - Overhauled `FloodZonePopup.tsx` with dynamic severity-matched header background, vehicle passability survey results, reporter identity with role badges (e.g. DRRMO Officer, Admin, Moderator, Commuter), and reported flood depth indicators (e.g. Gutter, Half Knee, Tire).
  - Switched map hover/click interactions dynamically: hover trigger on desktop vs. tap trigger on touch/mobile devices.
  - Added full reporter metadata (`reporter_name`, `reporter_role`, `report_text`, `vehicles_passable`, `hazards_hidden`, `depth_estimate`) to backend `FloodAvoidanceZone` models and schemas.
- [x] **Database Sanitization Script**:
  - Created `backend/scripts/clear_db.py` to truncate all flood reports, avoidance zones, community posts, comments, notifications, and user profiles while safely preserving system roles and the default admin account.
- [x] **Admin Analytics & Live Map Integration**:
  - Merged the standalone Analytics dashboard into the Admin Live Map & Zones page. Removed the `/admin/analytics` route and sidebar entry.
  - Added an Analytics MapLibre control button to the bottom-right of the map to toggle the floating insights panel and activate the heatmap layer.
  - Added a dedicated "Export to CSV" button in the top-right corner of the map canvas for exporting barangay and street flood statistics.
  - Stacked bottom-right map controls in exact order: Analytics (top), Navigation/Zoom (middle), Top View (bottom).
  - Refactored AdminSidebar to expand as an overlay drawer so map canvases and floating panels remain completely stationary during navigation.

- [x] **OTP Verification Lifecycle, Progressive Cooldown & Zero-Click UX**:
  - Implemented progressive cooldown tiers for OTP requests (1 min -> 3 mins -> 5 mins) to prevent gateway abuse while allowing enough time to check spam folders.
  - Implemented sliding grace window retaining up to 3 unexpired active codes for delayed network/mobile deliveries.
  - Added attempt throttling (up to 5 incorrect guesses) with a 5-minute brute-force lockout.
  - Upgraded frontend to zero-click automatic verification upon entering/pasting the 6th digit, with automatic input clearing on error.
  - Redesigned OTP view with 6 interactive pin boxes, inline verification indicator, and clean bottom navigation actions (Change Email & Resend Code).
  - Integrated official LANES CDN brand header into Brevo transactional email templates without downloadable attachments.
  - Created automated Pytest suite in `backend/tests/test_otp_lifecycle.py` verifying cooldowns, grace periods, and lockout rules.

## Backlog / Upcoming

