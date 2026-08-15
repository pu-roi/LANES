# LANES — Task Plan

> Tracking active sprints, backlog, and development priorities.

---

## Backlog

*(Currently empty — all immediate priorities are organized into phases below.)*

## Active Sprint (Next Feature)

### Phase 1: Audit Trail Synchronization & Full Coverage
> **Focus:** Ensure all state-altering administrative, security, and data operations across backend and frontend are comprehensively logged and observable in the admin UI.
- [ ] **Backend — Role Management Auditing ([roles.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/roles.py))**:
  - Add `create_audit_log` call to `POST /api/v1/roles` (`CREATE_ROLE`) logging `role_name` and initial `permissions`.
  - Add `create_audit_log` call to `PUT /api/v1/roles/{role_id}` (`UPDATE_ROLE`) logging previous vs. new permissions and name.
  - Add `create_audit_log` call to `DELETE /api/v1/roles/{role_id}` (`DELETE_ROLE`) capturing target role ID and name.
  - Add `create_audit_log` call to `POST /api/v1/roles/{role_id}/clone` (`CLONE_ROLE`) capturing source role ID and cloned role name.
  - Pass `Request` object into each endpoint function to extract `client_ip` via `request.client.host`.
- [ ] **Backend — Archive & Soft-Delete Auditing**:
  - Dispatch explicit audit events (`ARCHIVE_REPORT`, `RESTORE_REPORT`, `ARCHIVE_ZONE`, `RESTORE_ZONE`) when flood reports or zones are archived/soft-deleted or restored.
- [ ] **Frontend — Badge & Filter Synchronization ([AuditTrailPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/AuditTrailPage.tsx))**:
  - Update `ACTION_BADGES` mapping with styling and human-readable labels for:
    - `UPDATE_ZONE` ("Active Zones Map")
    - `CREATE_USER` ("Users Management")
    - `UPDATE_USER_ROLE` ("Users Management")
    - `CREATE_ROLE`, `UPDATE_ROLE`, `DELETE_ROLE`, `CLONE_ROLE` ("Roles & Permissions")
    - `EXPORT_DATA` ("Data Management")
    - `UPDATE_SETTINGS` ("System Settings")
    - `ARCHIVE_REPORT`, `RESTORE_REPORT`, `ARCHIVE_ZONE`, `RESTORE_ZONE` ("Archive")
  - Update the `Filter Activity` `<Select />` options list to include these actions so admins can easily filter the log table.

## Future Roadmap (Phases)

### Phase 2: Community Moderation & System Rules
> **Focus:** Establishing user trust, automated rules, and managing active flood data without ML.
- [ ] **Rule-Based Flood Expiration**: 
  - *Implementation:* Backend sets `expires_at` in `FloodAvoidanceZone` based on severity when an admin approves a report.
  - *Crowd-Sourced Extension:* Add "Flood Subsiding" / "Still Flooded" buttons on the map for users to reduce or extend expiration time.
- [ ] **Trust-Based Auto-Approval Engine**: 
  - Allow high-trust users (>90 score) to bypass the admin moderation queue.
  - *Crowd Consensus:* Auto-approve a flood if 3 independent users report it in the same radius within a short timeframe.
- [ ] **Duplicate Resolution (Admin Panel)**: 
  - Add admin tools to merge overlapping flood polygons using PostGIS `ST_Intersects` and `ST_Union`.

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
