# LANES — Task Plan

> Tracking active sprints, backlog, and development priorities.
> **Last Updated:** September 4, 2026, 12:22 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

---

## Backlog

- [ ] (Empty for now)

## Active Sprint (Next Feature)

### Official Flood Zones (DRRMO) Moderation
> **Focus:** Separating user-submitted flood reports from official DRRMO map data to ensure data integrity and streamline moderation via the Spatial Operations page.

#### Phase 1: Backend Data Integrity & API Layer
- [x] Modify `FloodAvoidanceZone` model (add `severity_override`, `depth_override`, `admin_notes`)
- [x] Create Pydantic schemas for Zone Overrides
- [x] Update `admin.py` endpoints (`approve_report`, `PUT /zones/{id}`, `POST /zones`)
- [x] Run Alembic migrations

#### Phase 2: Frontend Architecture Cleanup
- [x] Delete `frontend/src/app/admin/reports` completely
- [x] Remove Reports link from sidebar layout
- [x] Consolidate historical reports viewing into the Archive Center

#### Phase 3: Spatial Operations — Moderation Sidebar
- [x] Add explicit Checkboxes to `PendingReportsPanel.tsx` for batch merging
- [x] Implement strict Duplicate Hard Blocker (warning modal) for approvals
- [x] Add Troll Filtration (sort by Trust Score, filter by Severity) to sidebar
- [x] Port the `ReportDetailsModal` into the Map view to prevent redirects

#### Phase 4: Spatial Operations — DRRMO Zone Overrides (Map)
- [x] Add `createOfficialZone` to `adminApi.ts`
- [x] Adapt `FloodReportPanel.tsx` with `isAdminMode` & `onAdminSubmit` props
- [x] Integrate adapted `FloodReportPanel` into `LiveMapPage.tsx`
- [x] Refine "Create Official Zone" map interaction in `LiveMapPage.tsx`
- [x] Fix "Create Official Zone" Panel logic (identical to public Line flow with Start/End pin markers & road segment preview line)
- [x] Integrate **Terra Draw** (`terra-draw`) for native Polygon, Freehand, Rectangle, and Circle drawing for Admin Official Zones
- [ ] Wire up real-time SSE broadcasts for zone updates

## Future Roadmap (Phases)

### Phase 4: External Integrations & IoT
> **Focus:** Connecting LANES to external data sources and physical hardware.
- [ ] **Open-Meteo GloFAS Integration**: Integrate `river_discharge` variables to predict river overflow and automatically mark nearby areas as high risk.
- [ ] **IoT Sensor Webhooks**: Create dedicated `/api/v1/reports` webhooks to ingest raw coordinate data from physical ultrasonic water-level sensors on bridges.

## Future Roadmap (Phases)

### Phase 5: Machine Learning (Long-Term)
> **Focus:** Moving from rule-based to predictive AI architectures.
- **Historical Weather Correlation**: Use Open-Meteo historical APIs to correlate past typhoons with flood occurrences to build a training dataset.
- **Predictive Expiration Models**: Transition from Rule-Based Expiration to an ML model (Python/scikit-learn) trained on historical DRMMO data to predict exact expiration times based on rainfall and terrain.

## Defense Talking Points

### 1. Future ML Architecture
- **Supervised Learning**: If DRMMO provides historical flood data (rainfall + expiration times), we can immediately train an ML model (using Python/scikit-learn) to predict future expirations.
- **Online Learning ("Self-Learning")**: Without initial DRMMO data, the system relies on Rule-Based Expiration for immediate accuracy. However, the architecture is designed to continuously collect live data. Once enough floods are naturally recorded over time, the system can seamlessly transition to Online Machine Learning to predict expiration times automatically.

### 2. Defining "Real-Time" without Hardware Sensors
- **SSE-Driven Real-Time Broadcast**: The platform implements **instantaneous communication latency**. Within milliseconds of an admin approving a report (or a user submitting a post), Server-Sent Event (SSE) connections broadcast the updated routing barriers and active zones to all connected commuter clients globally. The *propagation of routing data* is true real-time.
- **Plug-and-Play IoT Sensor Hooks (MQTT/REST Webhooks)**: The database layer utilizes standard PostGIS geometry points and polygons. The architecture is explicitly designed to ingest coordinates. In the future, telemetry devices (e.g., ultrasonic water-level sensors installed on bridges or lamp posts) can write data directly to the `/api/v1/reports` endpoint via secure webhook keys, bypassing human input entirely.

### 3. Future Architecture: Duplicate Resolution & Auto-Approval
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
