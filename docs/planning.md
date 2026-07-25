# LANES — Planning

> Tracking milestones, features, and development priorities.

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
| 7 | Real-Time Operations | Completed | WebSocket broadcasting, Live active zones, Real-time admin dashboard invalidations |
| 8 | Community Feed & Moderation | Completed | Feed layout, Upvotes/Downvotes, Post archiving, Soft deletes, Map coordinate rendering |
| 9 | Spatial Analytics & Heatmap | Completed | Global Heatmap, Top Barangays stats, Dedicated Analytics Pages for Commuters and Admins |

## Active Sprint (Next Feature)

**Goal:** Comments Section for community feed

- [ ] Implement Comments Section for community feed

## Recently Completed

- [x] Implement Photon API Reverse Geocoding on backend to extract and save 'barangay' for approved reports
- [x] Create `/api/v1/analytics/heatmap` and `/api/v1/analytics/stats` endpoints
- [x] Build `/analytics` (public) and `/admin/analytics` pages with MapLibre Heatmap layer and data tables
- [x] Design Decision: Reverse geocoding via Photon is used to resolve barangays dynamically without storing heavy shapefiles


## Backlog

- Add authenticated routing for local networks
- **User Registry & System Rules**
  - **User Metrics**: Track "Reports Submitted", "Accuracy Rate", and "Trust Score".
  - **Rule-Based Expiration**: Admin configurable manual presets for flood expiration (e.g. 4 hours, 12 hours).
- **Open-Meteo Integrations (Future Work)**
  - **Global Flood API (GloFAS)**: Integrate `river_discharge` variables to predict river overflow and automatically mark nearby areas as high risk.
  - **Historical Weather API**: Correlate past typhoons and known flood occurrences to train an ML model for predictive flood mapping.

## Capstone Roadmap (1-2 Month Execution Plan)

> **Implementation Strategy:** We will execute this roadmap in 5 distinct phases, starting with high-visibility features (Home Page) and ending with complex logic (Admin Charts & Trust Scores).

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
- [ ] **Weather & Chart Legend**: Add a sleek UI guide/legend near the forecast chart to explain what the weather icons, rain percentages, and volume numbers mean to everyday users.

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

### 5. Defense Talking Points (Future ML Architecture)
- **Supervised Learning**: If DRMMO provides historical flood data (rainfall + expiration times), we can immediately train an ML model (using Python/scikit-learn) to predict future expirations.
- **Online Learning ("Self-Learning")**: Without initial DRMMO data, the system relies on Rule-Based Expiration for immediate accuracy. However, the architecture is designed to continuously collect live data. Once enough floods are naturally recorded over time, the system can seamlessly transition to Online Machine Learning to predict expiration times automatically.

### 6. Defense Talking Points: Defining "Real-Time" without Hardware Sensors
- **WebSocket-Driven Real-Time Broadcast**: The platform implements **instantaneous communication latency**. Within milliseconds of an admin approving a report (or a user submitting a post), WebSocket connections broadcast the updated routing barriers and active zones to all connected commuter clients globally. The *propagation of routing data* is true real-time.
- **Plug-and-Play IoT Sensor Hooks (MQTT/REST Webhooks)**: The database layer utilizes standard PostGIS geometry points and polygons. The architecture is explicitly designed to ingest coordinates. In the future, telemetry devices (e.g., ultrasonic water-level sensors installed on bridges or lamp posts) can write data directly to the `/api/v1/reports` endpoint via secure webhook keys, bypassing human input entirely.

### 7. Future Architecture: Duplicate Resolution & Auto-Approval
- **Spatial Deduplication & Bounding Polygon Merging (Admin Panel)**:
  - If multiple users report the same street with overlapping boundaries or conflicting depths, the admin panel will flag them as **"Potential Overlaps"** (using PostGIS `ST_Intersects` or `ST_DWithin` queries).
  - Admins can select duplicate reports and click **"Merge & Resolve"** to compute a unified boundary (`ST_Union`) or upgrade the severity scale based on the most recent/authoritative user input.
- **Trust-Based Auto-Approval Engine**:
  - To eliminate the admin bottleneck, reports from users with a **high Trust Score** (e.g., verified local authorities or commuters with >95% historical accuracy) can bypass the moderation queue and auto-approve instantly.
  - **Crowd Consensus Rule**: If `N` (e.g. 3) independent users report a flood within the same barangay and spatial radius within `T` minutes, the system automatically marks it as approved and updates the Valhalla routing network.

## Known Issues

- Share and Clipboard API are disabled by browsers on non-HTTPS local IPs (except localhost).

---

## Routing — Known Constraints & Design Decisions

> **Reference this section when debugging multi-route alternative issues.**

### One-Way Road Limitations (Philippines Urban Grid)

Philippine cities — particularly Pasig, Mandaluyong, Marikina, and the Ortigas CBD — have a **dense network of one-way streets**. Valhalla strictly enforces one-way restrictions as encoded in OpenStreetMap data. This creates a known class of routing behaviour to be aware of:

#### What Happens

When Valhalla is asked for alternative routes (`alternates=2`), it may return **fewer than 3 routes**. Because Valhalla actively snuffs out routes that intersect avoided polygons, it might determine there are only 1 or 2 possible paths that don't violate one-way streets while avoiding the flood.

This is **not a bug** — it is Valhalla correctly refusing to suggest an illegal route.

#### Future Debugging Checklist

If alternative routes look wrong or are missing:
- [ ] Check the Valhalla response directly from the Python backend logs
- [ ] Confirm the OSM data has the correct one-way tags for that street segment (check `openstreetmap.org`)
- [ ] Verify the `philippines-latest.osm.pbf` data is not too old (current snapshot is from Geofabrik; re-run `setup_valhalla.ps1` to refresh)

#### OSM Data Currency

The routing graph is built from `philippines-latest.osm.pbf` downloaded from Geofabrik. One-way restrictions in the OSM data may lag behind real-world road changes. If a known road change is not reflected in routes, re-run the Valhalla build script:

```powershell
# From the repo root
.\setup_valhalla.ps1
```

Then restart the Valhalla Docker container:

```powershell
docker-compose restart valhalla
```
