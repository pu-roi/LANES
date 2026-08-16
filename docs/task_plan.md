# LANES — Task Plan

> Tracking active sprints, backlog, and development priorities.

---

## Backlog

*(Currently empty — all immediate priorities are organized into phases below.)*

## Active Sprint (Next Feature)

### Phase 2: Spatial Moderation & Deduplication
> **Focus:** Handling duplicate/overlapping reports, Parent/Child zone relationships, trust score distribution, and unified Map+Feed moderation UI.

- [x] **1. Database Schema Updates (Backend)**:
  - **Modify `backend/app/models/report.py`**:
    - Remove the rigid 1:1 `report_id` constraint from the `FloodAvoidanceZone` model.
    - Add `zone_id` (ForeignKey) to `FloodReport` to establish a 1:N relationship (One Zone has Multiple Reports).
    - Add `curated_by_admin_id` to `FloodAvoidanceZone` to track if an admin modified the spatial boundary.
  - Generate and apply Alembic migration for these relational changes (`e89a3df04c63_phase2_spatial_dedup_1_to_n.py`).
- [x] **2. Trust Score & Zone Creation Logic (Backend)**:
  - **Modify `backend/app/crud/report.py` & `crud/zone.py`**:
    - Remove the logic that auto-generates a zone *before* admin intervention.
    - Implement a unified function for Trust Score credit: When a `FloodAvoidanceZone` is activated/approved, iterate through all its linked `FloodReport`s, mark them as `approved`, and increment `reports_verified` for each unique `user_id`.
    - Ensure reporters retain credit even if `curated_by_admin_id` is set.
- [x] **3. Moderation API Endpoints (Backend)**:
  - **Modify `backend/app/api/v1/endpoints/admin.py`**:
    - Update `POST /reports/{id}/approve` endpoint to accept an `ApproveReportRequest` payload (`action: "CREATE_NEW"` or `action: "MERGE"`, plus the custom geometry polygon/buffer data).
    - Implement PostGIS `ST_DWithin` spatial query to fetch "Nearby Active Zones" relative to a pending report's coordinates (`GET /api/v1/admin/zones/nearby`).
    - Implement `GET /api/v1/admin/reports/by-location` to group overlapping pending reports.
- [x] **4. Community Post Consolidation**:
  - Keep Community Posts separate: if 3 users report the same incident, they get merged into 1 Avoidance Zone while their 3 individual public posts remain independent in the feed.
- [x] **5. Spatial Moderation Dashboard & Fluid Layout (Frontend)**:
  - Refactor into a full-bleed edge-to-edge layout: Pending Reports & Active Zones sidebar (left) and interactive MapLibre GL map (right).
  - Mode Switcher using standardized `Tabs.tsx` (`variant="segmented"`).
  - Map Viewport Auto-fit to Pasig City (`[121.0515, 14.5338]` to `[121.1112, 14.6235]`) with `localStorage` position persistence.
  - Map Layers: Confirmed active zones render full polygons + glow lines; pending reports render transparent dashed buffer outlines on selection.
- [ ] **6. Interactive Dual-Layer Drawing & Geometry Editor (Sub-Phase 2.4)**:
  - Interactive polygon and line drawing tools (`@mapbox/mapbox-gl-draw` or custom handles) allowing admins to reshape or draw customized inundation detour zones.
  - Multi-merge UI modal to batch merge overlapping pending reports with one click.
- [x] **7. Testing & Verification**:
  - Created and passed `pytest backend/tests/test_spatial_merging.py` (100% passing) verifying 1:N schema linking and multi-user trust score crediting.

## Future Roadmap (Phases)

### Phase 3: External Integrations & IoT
> **Focus:** Connecting LANES to external data sources and physical hardware.
- **Open-Meteo GloFAS Integration**: Integrate `river_discharge` variables to predict river overflow and automatically mark nearby areas as high risk.
- **IoT Sensor Webhooks**: Create dedicated `/api/v1/reports` webhooks to ingest raw coordinate data from physical ultrasonic water-level sensors on bridges.

### Phase 4: Machine Learning (Long-Term)
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
