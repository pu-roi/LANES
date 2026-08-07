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

### Phase 1: Home Page & Onboarding (🟢 COMPLETED)
- [x] **Dynamic Weather Widget**: Integrate Open-Meteo API with Meteocons (reads from user profile location, defaults to Pasig).
- [x] **Daily Stats**: Show the number of *verified* flood reports for the current day.
- [x] **Site Visitors**: Display a metric for total active/historical site visitors.
- [x] **Flood Status Legend**: Add a clear breakdown of White, Yellow, Orange, and Red on the home page.

### Phase 2: Map & Routing Engine (🟢 COMPLETED)
- [x] **Vehicle Profiles**: Implement clearance-based routing labels:
  - *4-Wheel High Clearance* (SUVs, Pickups)
  - *4-Wheel Low Clearance* (Sedans, Hatchbacks)
  - *2-Wheels* (Motorcycles, Bicycles)
  - *Pedestrian* (Walking)
- [x] **Route Metrics**: Display "Safety %" and "Flood Risk" directly on alternative route banners.
- [x] **Flood Timelines**: Show when a flood was reported and approved directly on the map popup.
- [x] **Weather & Chart Legend**: Add a sleek UI guide/legend near the forecast chart to explain what the weather icons, rain percentages, and volume numbers mean to everyday users.
- [x] **AI Weather Insights**: Integrate OpenRouter API (`openrouter/free`) into the backend to dynamically generate educational, conversational interpretations of raw weather forecast data.

### Phase 3: Community Feed & Notifications (🟢 COMPLETED)
- [x] **Report Hazard Button**: Jump straight to the Flood Report Panel.
- [x] **Create Post Button**: Allows users to post text/photos to the community feed with an optional location tag.
- [x] **In-App Notification Center**: Global Bell Icon for comments, likes, and critical system alerts pinned to the top.

### Phase 4: Admin Panel & Report Moderation (🟢 COMPLETED)
- [x] **Active Zones Full View**: Show timeline, reporter details, and actions (View, Edit, Deactivate, Archive).
- [x] **Admin Dashboard Charts**: 
  - Pie Chart: Flood Severity Distribution.
  - Line Chart: Reports over time (Dynamic: Last 7 Days, Month, Year).
  - Bar Graph: Top 5 Most Flooded Barangays.

## Recently Completed
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
