# LANES — Task Plan

> Tracking active sprints, backlog, and development priorities.
> **Last Updated:** September 10, 2026, 1:07 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

---

## Backlog

- [ ] (Empty for now)

## Active Sprint (Next Feature)

### Capstone Phase 18: Intelligent Flood-Report Merging & Spatial Operations Redesign (🟡 IN PROGRESS)
> **Focus:** Overhauling the flood-report merging logic, candidate identification, and Spatial Operations UI/UX to enable intelligent, multi-factor spatial matching, explainable recommendations, conflict resolution, and seamless final-zone editing while strictly preserving original crowdsourced reports and Community Feed posts.
> **Current Status (Sept 9, 2026):**
> - Backend candidate engine (`merge_service.py`), carriageway analysis (`carriageway_service.py`), and model overrides (`passable_vehicles_override`, `hidden_hazards_override`, `media_urls`) are implemented and migrated.
> - `CreateOfficialZonePanel` has been completely restructured into a modular Feature-Based architecture (`zones/`) with 5-section `FloodReportPanel` parity (Depth/Severity, Survey, Cloudinary media upload, Description) and buffer slider removal.
> - **IN PROGRESS / MANUAL VERIFICATION PENDING:** The Phase 5 merge interface has been implemented: report inspection is neutral; intelligent suggestions require an explicit action and selection; candidate evidence is grouped inside each report card; and the contextual secondary drawer preserves its merge session while collapsed. Create Zone now also resumes its in-memory draft after collapse, including form values, media, draft-cart entries, and map geometry; line picking uses the shared MapContext workflow and automatically advances Start to End. Desktop/mobile workflow verification remains with the developer before Phase 5 is marked complete.

---

#### 1. Current Implementation Analysis
- **Data Model**:
  - `FloodReport`: Stores incoming reports (commuters, social feeds, seeders). Holds `raw_text`, `severity`, `depth`, `human_readable_location`, `barangay`, `city`, `is_public`, `is_bidirectional`, `geometry` (Point, LineString, or MultiLineString for bidirectional), `user_id`, `media_urls`, `status` (`pending`, `approved`, `rejected`), `zone_id` (FK to `flood_avoidance_zones.id`), and `survey` (`passable_vehicles`, `hidden_hazards`).
  - `FloodAvoidanceZone`: Represents active routing barrier polygons utilized by Valhalla. Holds `curated_by_admin_id`, `geometry` (POLYGON), `is_active`, `expires_at`, `name`, `severity_override`, `depth_override`, `admin_notes`. Has a 1:N relationship with `FloodReport`.
  - `CommunityPost`: Created when `is_public=True`. Has `flood_report_id` (FK). Stores `content`, `media_urls`, `location_tag`, `location_lat`, `location_lng`.
- **Existing Merging & Proximity Logic**:
  - `POST /admin/reports/{report_id}/approve`: Accepts `action="MERGE"` with `target_zone_id`. Sets `report.zone_id = target_zone.id` and optionally applies `custom_geometry`, `severity`, `depth`, `admin_notes`.
  - `POST /admin/zones/{zone_id}/merge-pending`: Batch attaches a list of `report_ids` to an existing active zone. Does not recalculate or union geometries, and cannot create a *new* merged zone from multiple pending reports.
  - `GET /admin/zones/nearby`: Basic PostGIS `ST_DWithin` query checking euclidean distance ($d \le 400\text{m}$) from report geometry to active zones.
  - `PendingReportsPanel.tsx`: Naively identifies batch candidates if `r.barangay === selectedReport.barangay` or `JSON.stringify(r.geometry) === JSON.stringify(selectedReport.geometry)`.
  - `CreateOfficialZonePanel.tsx`: Movable floating panel (`<Panel>`) overlaying the map with Line mode (two-click Start/End pins) and TerraDraw modes (Polygon, Freehand, Rectangle, Circle).

#### 2. Problems Found in Existing Implementation
1. **Barangay-Wide Duplicate Trap**: Matching candidates purely by `r.barangay === selectedReport.barangay` treats reports on completely different streets kilometers apart as duplicates and hard-blocks normal approval.
2. **String-Exact Coordinate Equality**: Matching geometry by exact GeoJSON string equality fails on any GPS jitter, varying segment lengths, or differing vertex density along the same street.
3. **No Multi-Report to New Zone Merge**: Admins cannot select 3 pending reports and merge them into a *new* official avoidance zone; the backend only supports merging into pre-existing active zones.
4. **No Geometric Union or Spatial Synthesis**: Merging multiple reports does not combine their road lines or buffer them into a continuous hazard area; the existing avoidance zone polygon is left untouched.
5. **No Road Graph or Network Awareness**: The system lacks street name normalization, network distance calculation, direction/heading evaluation, and distinction between highways, service roads, and local alleys.
6. **Swallowed Conflicting Metadata**: Reports with conflicting severities (e.g. Low vs Extreme), water levels (Gutter vs Waist), or vehicle passabilities are merged without conflict warnings or explainability.
7. **Broken UI Interaction**: Clicking "Review & Merge All" in `PendingReportsPanel` opens a modal with `targetZoneId = null`, causing submission failure.
8. **Multi-Shape Bundling Flaw in Create Official Zone**: Previously allowed multiple unrelated polygons inside one single official zone. But each flood incident has its own unique severity, depth, vehicle passability, and description. 1 Zone must equal 1 Incident, supported by a clean Draft Cart ("Add Another Zone") for batching.

#### 3. Recommended Merge Logic (Decision #16 Powered with Graph Grouping)
- Merging is **system-suggested but human-confirmed** ("System Suggests $\rightarrow$ Admin Reviews & Selects $\rightarrow$ Admin Edits Final Data $\rightarrow$ Admin Confirms Merge").
- Uses **Decision #16 Valhalla Road Tracing (`trace_attributes`) & OSM Graph Grouping** as the foundational intelligence engine:
  - **OSM `way_id` Match**: Extracts the underlying OpenStreetMap `way_id` from Valhalla edge traces. Matching `way_id`s guarantee 100% road network identity match, bypassing naming anomalies.
  - **Condition 1 (Road Name & Class Firewall)**: OSM street name and highway classification must match. Prevents expressway lines from merging with parallel service roads or adjacent alleys.
  - **Condition 2 (Undivided Two-Way Road `NARROW_TWO_WAY`)**: If Valhalla reports `traversability: "both"`, reports along the same centerline represent both traffic directions on a single road. Merged into a unified bidirectional road hazard.
  - **Condition 3 (Divided Dual Carriageway `DIVIDED_CARRIAGEWAY`)**: If Valhalla reports `traversability: "forward"`, runs Decision #16's dynamic perpendicular offset probe (5m, 10m, 15m, 20m, 30m). If the second report matches the discovered opposite carriageway shape, the system confirms they are opposite carriageways of the same divided avenue (e.g. C-5 Northbound & Southbound). Merged as a dual-carriageway `MultiLineString` with `ST_ConvexHull(ST_Collect(...))` avoidance buffer.
  - **Condition 4 (Continuous Extension)**: If reports cover overlapping or adjacent segments of varying lengths on the same road, the system unites them from earliest start to furthest end along the road graph.

#### 4. Recommended Spatial Matching & Linear Referencing Approach
- **Corridor Generation**: Convert road LineStrings to a spatial corridor via PostGIS `ST_Buffer(geom, 0.00025)` ($\approx 25\text{m}$ buffer).
- **Corridor Intersection / Jaccard Metric**:
  $$\text{Overlap Ratio} = \frac{\text{ST\_Area}(\text{ST\_Intersection}(\text{corridor}_A, \text{corridor}_B))}{\text{Min}(\text{ST\_Area}(\text{corridor}_A), \text{ST\_Area}(\text{corridor}_B))}$$
- **Linear Path Alignment**: Calculate segment azimuths. Angles must align within $\pm 30^\circ$ (same direction) or $\pm 180^\circ \pm 30^\circ$ (opposite direction on two-way or dual carriageway).
- **Linear Referencing Geometry Synthesis**: Project candidate start/end coordinates onto the validated Valhalla road centerline via `ST_LineLocatePoint(centerline, pt)`. The merged road geometry is cleanly extracted using `ST_LineSubstring(centerline, min(t), max(t))`, completely eliminating multi-line gaps or vertex jitter artifacts.

#### 5. Candidate-Report Identification & Map Spotlight
- Endpoint `GET /api/v1/admin/reports/merge-candidates?report_id={id}`:
  1. Spatially index and query active zones and pending reports within a $500\text{m}$ bounding box.
  2. Runs Decision #16 Valhalla trace inspection on candidates.
  3. Detects explicit conflicts (severity, water level, vehicle passability, direction).
  4. Returns structured candidate payload with match score, human-readable explanations ("Same road: Ortigas Ave, 85% overlap, reported 18m apart"), and conflict flags.
- **Map Spotlight Behavior**:
  - Selecting a report highlights the target report in primary color and candidate reports in distinct merge colors.
  - **All other unrelated reports across the city are completely hidden (filtered out)** to eliminate background noise, matching existing `usePendingReportsLayer.ts` isolation behavior.

#### 6. Road, City, Barangay, and Geometry Matching
- **Road Name Normalization**: Strip administrative prefixes/suffixes ("Ave", "St", "Blvd", "Avenue", "Street", "Highway", "Road", "Dr", punctuation, whitespace, lowercase). Match against Valhalla edge names from map-matching traces.
- **City & Barangay**:
  - City mismatch blocks automatic suggestion.
  - Same barangay increases locality score; different barangays are permitted if the road crosses a boundary (e.g. Ortigas Ave passing through Ugong and Rosario).
  - Reports in the same barangay but on different road names are strictly classified as unrelated.

#### 7. Handling Different Start/End Coordinates and Report Lengths
- If User A reports a 100m segment and User B reports a 300m segment covering or extending beyond User A's segment on the same road:
  - The system computes the **linear referenced envelope** along the road line using $t_{\min} = \min(t_A, t_B)$ and $t_{\max} = \max(t_A, t_B)$ to cleanly extract the bounding road segment.
  - The final merged road segment extends from the earliest start point to the furthest end point along the street graph.
  - The UI displays both individual submissions as subtle colored traces and the synthesized road segment as the active proposal.

#### 8. Handling Same-Side, Opposite-Side, Divided Roads, and Highways
- **Same-Side**: Merged into a unified directional LineString corridor.
- **Opposite-Side (Two-Way Undivided / `NARROW_TWO_WAY`)**: Handled as a single centerline representing both flows with `is_bidirectional = True`.
- **Divided Carriageways / Expressways (`DIVIDED_CARRIAGEWAY`)**:
  - Evaluated via `find_opposite_carriageway()` (Decision #16).
  - If reports are on opposite carriageways of a divided avenue (e.g. C-5 Northbound vs Southbound), they are merged into a `MultiLineString` or `GeometryCollection` containing both roadways.
  - The resulting avoidance polygon uses `ST_ConvexHull(ST_Collect(ST_Buffer(line1, r), ST_Buffer(line2, r)))` ensuring both directions are avoided.
- **Service Roads & Parallel Alleys**:
  - Validated against OSM highway classification and name matching. An expressway (e.g. `trunk` / `primary`) will not merge with an adjacent service road (`service` / `residential`) even if within 15 meters.

#### 9. Handling Severity, Timestamps, Water Levels, Passability, and Conflicting Information
- **Safety-First Defaults with Full Admin Override**:
  - **Severity**: Default to the highest reported severity among the merged reports (e.g., Extreme > High > Medium > Low).
  - **Water Level**: Default to the highest MMDA level reported; if a newer report indicates receding water, flag a "Receding flood trend detected" notice.
  - **Vehicle Passability**: Default to the most restrictive passability profile (e.g., if one says Sedan passable and another says High Clearance only, default to High Clearance only).
  - **Timestamps**: All original timestamps preserved. The merged zone retains `created_at` (earliest report) and `updated_at` (merge time).
  - **Explanation of Conflicts**: Conflicts are rendered in a dedicated UI banner with clear visual indicators and one-click resolution choices.

#### 10. Recommended Merge Flood Reports UI/UX Workflow
A structured 4-stage workflow inside the **Dual-Pane Secondary Drawer**:
1. **Stage 1: Select Reports & View Recommendations**:
   - The admin views the selected report and AI/algorithm-suggested merge candidates sorted by confidence score.
   - The admin checks or unchecks reports to include in the merge.
2. **Stage 2: Review & Compare**:
   - Side-by-side comparison matrix showing Reporter, Role, Trust Score, Timestamp, Severity, Depth, Passability, Text, and Photo evidence.
   - Clear diff highlighting on conflicting fields.
3. **Stage 3: Edit Final Merged Flood Zone**:
   - Admin configures the operational zone data using the complete capabilities of `CreateOfficialZonePanel` (Line mode with Start/End pins and bidirectional toggle OR TerraDraw shape modes: Polygon, Freehand, Rectangle, Circle).
   - Admin reviews or edits Zone Name, Severity, Water Depth, Passable Vehicles, and Admin Notes.
4. **Stage 4: Confirm & Publish**:
   - Review summary of actions (e.g., "3 reports merged into Zone #12; 3 contributors credited +5 trust score; Community feed posts unchanged").
   - Confirm button dispatches atomic transaction.

#### 11. Admin Report Selection & Inspection
- Checkbox selection in the pending list and candidate drawer.
- Clicking any report highlights its specific geometry on the map in a unique color while hiding unrelated city floods.
- Admin can add or remove any candidate from the merge selection at will.

#### 12. Admin Editing of Final Merged Information
- Admin has final operational authority over:
  - Final Severity (Low, Medium, High, Extreme)
  - Final Water Level Depth (MMDA standard visual gauge)
  - Passable Vehicles (High-Clearance 4x4, Sedan, Motorcycle, Pedestrian)
  - Hidden Hazards presence (Yes, No, Unsure)
  - Administrative Notes / Location Description (Zones are described by real-world location & conditions; manual zone naming removed)
  - Spatial Boundaries (Road Line or Drawn Polygon)
  - Immediate Status: Created flood hazard detours are automatically active (`is_active: true`) without artificial scheduling.

#### 13. Spatial Editing Integration & 1 Zone = 1 Incident Standard
- **1 Zone = 1 Flood Incident**:
  - Replaces confusing multi-polygon bundling inside a single zone.
  - For each flood incident, the admin selects **either**:
    - **Line Mode**: Interactive two-click Start/End pin picking with Valhalla road snapping and bidirectional detection.
    - **Shape Mode**: Single custom boundary (Polygon, Freehand sketch, Rectangle, or Circle).
  - To declare multiple distinct flood zones across the city, the admin uses the **Draft Cart ("Add Another Zone")** to queue them independently and submit all in one click.

#### 14. Handling Decision #16 and Bidirectional Reports
- If any merged report has `is_bidirectional=True`, or if the admin enables bidirectional mode during final editing:
  - The system executes `find_opposite_carriageway()`.
  - For `DIVIDED_CARRIAGEWAY`, both road lines are preserved as a `MultiLineString` and buffered into a convex hull polygon.
  - For `NARROW_TWO_WAY`, a single centerline buffer is used with bidirectional metadata.

#### 15. Protecting Community Feed Posts & Immediate Feed Posting
- When a user submits a report and toggles **"Share to Community Feed"**:
  - It **posts immediately to the Community Feed (`/feed`)** so other commuters see it and can comment/upvote right away.
  - It **does NOT appear on `/map` as an avoidance barrier** until approved/merged by an admin.
- Merging reports MUST NOT alter, combine, or delete `community_posts` records!
- The author's original text, media attachments, location tag, upvotes, and comments remain exactly as submitted.
- The merge operation only updates operational routing data in `flood_avoidance_zones` and links `flood_reports.zone_id`.

#### 16. Preserving Original Reports and Audit History
- Original `FloodReport` records retain their raw user-submitted values (`raw_text`, `severity`, `depth`, `geometry`, `media_urls`, `user_id`, `survey`).
- `FloodReport.zone_id` links the report to the merged `FloodAvoidanceZone`.
- `FloodAvoidanceZone.contributors` serializes all linked reports for historical inspection in the Active Zones accordion.
- Audit log entry `MERGE_FLOOD_REPORTS` captures `admin_id`, `zone_id`, merged report IDs, original values, final values, and IP address.
- Merge transactions are fully atomic: failure during any step rolls back the entire transaction.

#### 17. Database & Model Changes
- In `models/report.py` (`FloodAvoidanceZone`):
  - Add `passable_vehicles_override: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)`
  - Add `hidden_hazards_override: Mapped[Optional[HazardPresence]] = mapped_column(Enum(HazardPresence, native_enum=False, length=50), nullable=True)`
  - Add `merge_rationale: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)` (storing composite score, candidate report IDs, and conflict resolution summary)
- Generate and run clean Alembic migration.

#### 18. Frontend Changes & Dual-Pane Architecture
- **Dual-Pane Sidebar / Secondary Flyout Drawer**:
  - Primary Sidebar (`PendingReportsPanel` / `ActiveZonesPanel`) remains docked on the left.
  - Secondary Slide-Out Drawer (`MergeWorkspacePanel` / `ZoneDataEditorForm`) docks alongside it when merging or creating official zones.
- Create `src/features/admin/components/merge/`:
  - `MergeWorkspacePanel.tsx`: The secondary drawer for reviewing, selecting, comparing, and finalizing merges.
  - `ReportComparisonCard.tsx`: Rich side-by-side comparison card displaying report differences and contributor metadata.
  - `MergeExplanationBanner.tsx`: Visual breakdown of why reports match (similarity score, road name, overlap distance).
  - `ConflictResolutionNotice.tsx`: Highlights conflicts (severity/water/passability) and allows one-click overrides.
- Refactor `CreateOfficialZonePanel.tsx`: Extract `ZoneDataEditorForm.tsx` enforcing 1 Zone = 1 Incident with Draft Cart batching.
- Create `src/features/map/hooks/useMergePreviewLayer.ts`: MapLibre hook rendering candidate report lines in distinct colors and showing a live preview of the proposed merged zone.

#### 19. Backend Changes
- Create `backend/app/services/merge_service.py`:
  - `calculate_spatial_similarity(geom_a, geom_b)`
  - `normalize_road_name(name)`
  - `find_merge_candidates(report_id, db)`: Uses Decision #16 Valhalla trace attributes.
  - `generate_merged_geometry(reports, is_bidirectional, db)`
- Add endpoints to `backend/app/api/v1/endpoints/admin.py`:
  - `GET /admin/reports/merge-candidates`: Returns scored candidate reports with conflict analysis.
  - `POST /admin/reports/merge`: Transactional multi-report merge into a new or existing avoidance zone.
- Update `backend/app/services/report_service.py` / `reports.py`:
  - Auto-create `CommunityPost` immediately upon report submission if `is_public=True`.

#### 20. Validation Rules
- At least two reports required for a merge (or 1 report + 1 existing zone).
- All reports must belong to the same city.
- Reports separated by $>500\text{m}$ without road continuity require explicit admin confirmation.
- The final merged geometry must be a valid, non-empty PostGIS geometry.
- Only authenticated admins/DRRMO personnel can execute merges.

#### 21. Edge Cases
- **Low GPS Accuracy**: Midpoint buffer snapping ensures drifting points snap to the nearest road segment.
- **Cross-Barangay Avenues**: Contiguous segments on roads crossing barangay borders are permitted if road name matches.
- **Divided Highways**: One report affecting both sides + one affecting single side are synthesized into a dual carriageway.
- **Conflicting Passability**: Safe fallback to most restrictive vehicle profile.
- **Stale / Delayed Reports**: Temporal score penalizes reports $>6$ hours old; warns admin of potential flood recession.
- **Archived/Rejected Reports**: Filtered out from merge candidates.

#### 22. Testing Strategy
- Automated Pytest suite (`backend/tests/test_flood_report_merging.py`):
  - Spatial corridor overlap and Decision #16 road trace matching.
  - Road name normalization and fuzzy trigram matching.
  - Candidate identification scoring and conflict detection.
  - Multi-report merge into a new `FloodAvoidanceZone`.
  - Multi-report merge into an existing `FloodAvoidanceZone`.
  - Immediate `community_posts` creation and post immutability on merge.
  - Awarding +5 trust score per unique contributor.
  - Rollback on invalid geometry.
- Frontend verification:
  - Dual-Pane Drawer interaction on desktop and mobile sheet.
  - Map preview layers and TerraDraw interaction during merge editing.
  - Verification of mobile layout responsiveness.

#### 23. Files and Components to Reuse, Extend, or Refactor
- **Reuse**:
  - `valhalla_service.py` (`find_opposite_carriageway`, `_shift_coords_perpendicular`, `decode_polyline6`)
  - `report_service.py` (`extract_representative_coordinates`)
  - `geocoding_service.py` (`reverse_geocode_structured`)
  - `useFloodMapPreview.ts` (MapLibre Start/End pin preview)
  - `ReportDetailsModal.tsx` (contributor and geometry formatters)
  - `ActiveZonesPanel.tsx` (multi-contributor accordion)
- **Refactor / Extend**:
  - `CreateOfficialZonePanel.tsx` $\rightarrow$ extract `ZoneDataEditorForm.tsx` (1 Zone = 1 Incident with Draft Cart).
  - `LiveMapPage.tsx` $\rightarrow$ integrate Dual-Pane secondary drawer alongside queue.
  - `PendingReportsPanel.tsx` $\rightarrow$ update batch candidate detection to call intelligent candidates API.
  - `admin.py` $\rightarrow$ add merge candidates and transactional merge endpoints.

#### 24. Recommended Layout: Dual-Pane Master-Detail Sidebar / Drawer
- **The Architecture**:
  - **Pane 1 (Primary Sidebar - 380px)**: Moderation Queue (`Pending Reports` & `Active Zones`).
  - **Pane 2 (Secondary Slide-Out Drawer - 420px)**: Docks seamlessly alongside Pane 1 when merging or declaring official zones. Slides out of view when dismissed.
  - **The Map**: Occupies remaining viewport with full-bleed canvas and instant resize.
  - **Zero Map Obstruction**: Operators can click pins, draw shapes, and inspect streets without dragging floating cards out of the way.

---

### Implementation Phases & Dependencies

#### Phase 1: Data Model, Database Migrations & Schemas
- **Objective**: Extend database models and Pydantic schemas to support vehicle passability overrides, hazard overrides, merge rationale, and transactional merge requests.
- **Affected Files**:
  - `backend/app/models/report.py`
  - `backend/app/schemas/report.py`
  - `backend/alembic/versions/*`
- **Dependencies**: None.
- **Expected Outcome**: `FloodAvoidanceZone` stores `passable_vehicles_override`, `hidden_hazards_override`, and `merge_rationale`. Migrations run cleanly via `alembic upgrade head`.
- **Validation**: Schema validation tests and clean alembic upgrade/downgrade.

#### Phase 2: Intelligent Spatial Matching & Merge Candidate Engine
- **Objective**: Build the backend multi-factor scoring service to identify merge candidates with spatial corridor overlap, normalized road matching, Decision #16 carriageway analysis, and conflict detection.
- **Affected Files**:
  - `backend/app/services/carriageway_service.py` [NEW] (Extracts Decision #16 logic from `valhalla_service.py`)
  - `backend/app/services/valhalla_service.py` (Re-exports for backwards compatibility)
  - `backend/app/services/merge_service.py` [NEW]
  - `backend/app/api/v1/endpoints/admin.py`
  - `backend/tests/test_merge_service.py` [NEW]
- **Dependencies**: Phase 1.
- **Expected Outcome**: Decision #16 isolated cleanly into `carriageway_service.py`; `GET /api/v1/admin/reports/merge-candidates` returns scored, explainable candidate reports with conflict flags.
- **Validation**: Pytest suite verifying corridor overlap, fuzzy road name matching, carriageway detection, and conflict detection.

#### Phase 3: Transactional Merge & Approval API
- **Objective**: Implement atomic merge execution supporting creation of new merged zones or merging into existing zones, crediting trust scores, preserving original reports, leaving Community Feed posts untouched, and recording audit logs.
- **Affected Files**:
  - `backend/app/api/v1/endpoints/admin.py`
  - `backend/app/crud/report.py`
  - `backend/tests/test_flood_report_merging.py` [NEW]
- **Dependencies**: Phase 1 & 2.
- **Expected Outcome**: `POST /api/v1/admin/reports/merge` executes atomic multi-report merge with SSE signaling.
- **Validation**: Pytest verifying transactional rollback, trust score increments, audit logs, and feed post immutability.

#### Phase 4: Reusable Spatial & Zone Data Editor Component
- **Objective**: Refactor `CreateOfficialZonePanel.tsx` to extract `ZoneDataEditorForm.tsx`, decoupling form controls, Line mode with Start/End pins, bidirectional detection, and TerraDraw shape tools for reuse in both zone creation and merge workflows.
- **Affected Files**:
  - `frontend/src/features/admin/components/ZoneDataEditorForm.tsx` [NEW]
  - `frontend/src/features/admin/components/CreateOfficialZonePanel.tsx`
- **Dependencies**: None (frontend).
- **Expected Outcome**: Clean, reusable component supporting both standalone zone creation and merge final editing.
- **Validation**: Component mounts and functions correctly in standalone official zone creation without regressions.

#### Phase 5: Redesigned Merge UI/UX Workspace & Live Map Integration
- **Objective**: Implement the docked `MergeWorkspacePanel.tsx`, `ReportComparisonCard.tsx`, and `ConflictResolutionNotice.tsx`, replace the broken merge modal in `PendingReportsPanel.tsx`, and add `useMergePreviewLayer.ts` for multi-report color coding and merged preview on MapLibre.
- **Confirmed Interaction Decision**: Normal report selection remains a neutral inspection action. Intelligent suggestions open only when the admin explicitly chooses **Review Merge Suggestions**. Suggestions are never called duplicates, never hard-block standalone approval, and are never automatically included without an admin selection.
- **Implementation Sequence**:
  1. [x] Remove legacy barangay/exact-GeoJSON candidate derivation, forced queue filtering, duplicate warnings, approval blocking, batch-selection remnants, and the obsolete merge modal. Keep the full pending queue visible during ordinary report inspection. (@roicambe)
  2. [x] Add a non-blocking **Review Merge Suggestions** action that opens the intelligent candidate workspace and activates map spotlight only for the duration of that workflow. Provide explicit loading, empty, error, retry, cancel, and defer states. (@roicambe)
  3. [x] Replace automatic score-based inclusion with explicit admin checkboxes. Retain confidence ranking and explanations as recommendations only, and recompute conflicts/preview from the reports actually selected. (@roicambe)
  4. [x] Replace stacked comparison cards with a responsive field comparison covering reporter identity/role/trust, timestamp, road/location, severity, depth, passability, hidden hazards, description, and media evidence. Visually identify differences without overwriting original values. (@roicambe)
  5. [x] Integrate reusable spatial controls from the official-zone workflow so the final merged zone supports routed Start/End editing, bidirectional detection, and Terra Draw Polygon/Freehand/Rectangle/Circle geometry. Avoid creating a second map-drawing implementation. (@roicambe)
  6. [x] Add a distinct confirmation step summarizing included/excluded reports, destination zone, final operational attributes, geometry, trust-score effects, and preservation of original reports and Community Feed posts. Enforce frontend validation before submission. (@roicambe)
  7. [x] Complete responsive behavior: docked master-detail panes on desktop and a full-width mobile workflow with an explicit map-view control, safe-area-aware actions, and no fixed-width overflow. (@roicambe)
  8. [ ] Complete developer-led desktop/mobile workflow verification for report focus changes, collapsed-drawer session persistence, candidate selection, spatial editing, Create Zone line/shape picking, and merge submission. TypeScript is currently clean; rerun the project lint/build once the existing local Next.js build lock is released. (@roicambe)
- **Affected Files**:
  - `frontend/src/features/admin/components/merge/MergeWorkspacePanel.tsx` [NEW]
  - `frontend/src/features/admin/components/merge/ReportComparisonCard.tsx` [NEW]
  - `frontend/src/features/admin/components/merge/ReportComparisonMatrix.tsx` [NEW]
  - `frontend/src/features/admin/components/merge/MergeExplanationBanner.tsx` [NEW]
  - `frontend/src/features/admin/components/merge/ConflictResolutionNotice.tsx` [NEW]
  - `frontend/src/features/admin/components/PendingReportsPanel.tsx`
  - `frontend/src/features/admin/LiveMapPage.tsx`
  - `frontend/src/features/admin/adminApi.ts`
  - `frontend/src/features/map/hooks/useMergePreviewLayer.ts` [NEW]
- **Dependencies**: Phases 2, 3, 4.
- **Expected Outcome**: Complete, understandable, map-centered merge review workspace in which the system recommends, the admin explicitly selects, original reports remain inspectable, final operational data and geometry are editable, and publication requires a deliberate confirmation.
- **Validation**: Focused ESLint and TypeScript validation; desktop and mobile checks for ordinary report inspection, candidate loading/error/empty states, candidate inclusion/exclusion, selected-only conflict resolution, line and shape editing, bidirectional preview, cancel/defer behavior, new-zone and existing-zone submission, and post-merge refresh.

#### Phase 6: Automated Testing & End-to-End Verification
- **Objective**: Execute end-to-end integration tests verifying database integrity, Community Feed post preservation, audit log completeness, and edge case handling.
- **Affected Files**:
  - `backend/tests/test_flood_report_merging.py`
  - Documentation updates in `docs/progress.md`

---

#### 25. Multi-Agent Execution Strategy (Option A)
To ensure rapid execution, clean boundaries, and zero git conflicts, execution across these phases will be orchestrated using domain-specific subagents matching `.agents/skills/`:
1. **`api-agent` (Phases 1, 2, 3)**:
   - Implements database models (`passable_vehicles_override`, `hidden_hazards_override`, `merge_rationale`), Alembic migrations, Pydantic schemas, `merge_service.py` (Decision #16 multi-factor road-matching logic), and FastAPI admin endpoints.
   - Ensures immediate creation of `community_posts` on public report submission while preserving complete post immutability on merge.
2. **`ui-agent` (Phases 4, 5)**:
   - Extracts reusable `ZoneDataEditorForm.tsx` (1 zone = 1 incident draft cart).
   - Builds the secondary slide-out drawer `MergeWorkspacePanel.tsx`, `ReportComparisonCard.tsx`, `ConflictResolutionNotice.tsx`, `useMergePreviewLayer.ts`, and Map Spotlight isolation.
3. **`test-agent` (Phase 6)**:
   - Authors and executes the comprehensive Pytest suite (`backend/tests/test_flood_report_merging.py`), verifying spatial corridor calculations, candidate scoring, trust score awarding (+5), and edge cases.
4. **Primary Orchestrator (Antigravity)**:
   - Supervises milestone handoffs, verifies dependencies (`requirements.txt`, `package.json`), checks branch protection (`roi-branch`), and conducts final E2E verification.
- **Dependencies**: Phases 1 through 5.
- **Expected Outcome**: All unit and integration tests pass (100%), documentation updated.
- **Validation**: `pytest backend/tests/test_flood_report_merging.py` exits 0.

---

## Delivered Phases

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
- [x] Standardize MapLibre drawing logic between FloodReportPanel and CreateOfficialZonePanel via shared `useFloodMapPreview` hook (@antigravity)
- [x] Force TerraDraw map interaction pass-through using native capture-phase canvas event listeners (@antigravity)
- [x] Integrate **Terra Draw** (`terra-draw`) for native Polygon, Freehand, Rectangle, and Circle drawing for Admin Official Zones
- [ ] Wire up real-time SSE broadcasts for zone updates

#### Phase 5: Spatial Operations — Live Map & Hover Interaction Engine
- [x] Fix layer geometry filters in `usePendingReportsLayer` & `useFloodZonesLayer` for `MultiLineString` & `Polygon` (@roicambe)
- [x] Implement non-resetting 400ms hover dwell timer to eliminate sweeping triggers (@roicambe)
- [x] Prevent ceiling clipping via dynamic 420px clearance anchor flipping & dynamic tip tinting (@roicambe)
- [x] Redesign `FloodZonePopup` with dedicated timestamp row and vehicle passability chips (@roicambe)
- [x] Resolve `ReportDetailsModal` coordinate parsing crash for non-Point geometries (@roicambe)
- [x] Scope Lenis smooth scrolling exclusively to Landing and About views (@roicambe)

### Phase 6: Community Feed Emergency Hotline Directory
- [x] Add cached national hotline scraping service and public `/api/v1/hotlines/` endpoints (@roicambe)
- [x] Add Pasig city and barangay hotline parsing through `/api/v1/hotlines/full` (@roicambe)
- [x] Replace static feed emergency contacts with responsive hotline cards and lazy directory modal (@roicambe)

### Phase 7: Saved Places Camera Synchronization & Navigation UX
- [x] Align saved place fly-to transitions with hazard zones (zoom 16, 1500ms duration, easing) (@roicambe)
- [x] Connect `fly-to-location` custom events to `MapCanvas.tsx` with 3s pulsing red ring indicator (@roicambe)
- [x] Route feed saved place pills to open the Saved Places panel directly instead of routing origin pins (@roicambe)
- [x] Eliminate browser text insertion carets on saved places with `select-none` and `caret-transparent` (@roicambe)
- [x] Fix `pin_order` overwrite bug during place updates in `backend/app/crud/saved_place.py` (@roicambe)
- [x] Add hover-triggered custom slim scrollbar styles to `LeftSidebar.tsx` (@roicambe)

### Phase 8: Community Post Geolocation & Seamless Map Fly-to View
- [x] Add `location_lat` and `location_lng` (Float) columns to `community_posts` with Alembic migration (@roicambe)
- [x] Update backend schemas, models, and CRUD layers to persist and serve coordinates (@roicambe)
- [x] Streamline `PostItem.tsx` header with clickable red pin location button flying to `/map` (@roicambe)
- [x] Eliminate redundant blue location tags and duplicate bottom "View on Map" buttons (@roicambe)
- [x] Implement container `ResizeObserver` in `BaseMap.tsx` to keep MapLibre dimensions synced (@roicambe)
- [x] Fix MapLibre desktop centering offset by coordinating layout reflow and resize against 340px sidebar (@roicambe)
- [x] Fix post draft auto-saving and coordinate preservation across login/signup redirects in `CreatePostModal.tsx` (@roicambe)

### Phase 9: Project Directory Cleanup & Shared Architecture Restructuring
- [x] Audit `frontend/` and `backend/` directories, clarifying `/map` vs `/admin/map` persistent routing (@roicambe)
- [x] Unify frontend API client by migrating `useHotlines.ts` to `@/lib/apiClient` and deleting `shared/api.ts` (@roicambe)
- [x] Delete unused `shared/types.ts` and empty `shared/components/` directory (@roicambe)
- [x] Eliminate 10 dead prototype files across `features/auth`, `features/hazards`, `features/profile`, and `features/admin` (@roicambe)
- [x] Relocate `src/components/Map/OfflineManager.tsx` to `features/offline/OfflineManager.tsx` and delete orphaned `src/components` (@roicambe)
- [x] Categorize 26 flat components in `src/shared/ui/` into domain subfolders (`forms/`, `feedback/`, `layout/`, `tables/`, `map/`), migrate all imports to clean barrel imports, and purge all 25 shims (@roicambe)
- [x] Backend root clutter cleanup: relocate maintenance scripts (`duplicate_reports.py`, `fix_locations.py`, `fix_locations_nominatim.py`) to `backend/scripts/`, move `zones.json` to `backend/tests/fixtures/`, and delete scratch files (@roicambe)
- [x] Domain & feature alignment: consolidate `savedPlacesApi.ts` into `features/places/` with backwards-compatible re-exports and local feature imports (@roicambe)
- [x] Service-Based Backend Routing Separation: establish dedicated `endpoints/routes.py` controller mounted at `/routes` with zero-regression delegation aliases in `endpoints/reports.py` (@roicambe)

### Phase 10: Route Planner Focus State, Saved Places & Route Rendering Fixes
- [x] Guard `setPointFromMap` with explicit `isPickingOnMap` and `activePoint` checks to prevent stray map clicks from overwriting focused input fields (@roicambe)
- [x] Streamline "Choose on Map" UX: automatically advance to `end` destination upon setting origin, allowing one-click destination selection on the map (@roicambe)
- [x] Fix Saved Places selection logic in `RoutePanel.tsx` to sequentialize origin and destination assignments and automatically trigger routing (@roicambe)
- [x] Fix "Choose on Map" event propagation in `RoutePanel.tsx` preventing portal click cancellation (@roicambe)
- [x] Fix MapLibre route polyline rendering in `MapCanvas.tsx`: replace fragile `isStyleLoaded()` guards with `map.getStyle()` and register `style.load` listeners to prevent dropouts on tile re-fetches (@roicambe)
- [x] Enhance active route paint reliability with standard `line-color` fallback and automatic camera `fitBounds` centering (@roicambe)

### Phase 11: Automated Street, Barangay & City Reverse-Geocoding for Flood Reports
- [x] Implement structured reverse geocoding with multi-provider fallback (Nominatim & Photon) in `geocoding_service.py` (@roicambe)
- [x] Add multi-geometry coordinate midpoint extraction (Point, LineString, MultiLineString) in `report_service.py` (@roicambe)
- [x] Add `city` column to `FloodReport` model and generate Alembic migration `a66a677fa71a_add_city_to_flood_reports.py` (@roicambe)
- [x] Update CRUD and schema layers to persist `barangay` and `city` on `POST /api/v1/reports` (@roicambe)
- [x] Execute historical backfill script updating all existing database reports with verified street, barangay, and city names (@roicambe)
- [x] Sync frontend `FloodReportPanel`, `ReportDetailsModal`, and `PendingReportsPanel` with dynamic city and road labels (@roicambe)
- [x] Add automated test suite in `backend/tests/test_report_geocoding.py` verifying coordinate extraction, reverse geocoding, and DB persistence (@roicambe)
- [x] Streamline Community Feed post cards: eliminate redundant blue location text beneath severity badge, unify post header location with red pin fallback to reverse-geocoded road or barangay, and preserve primary "View on Map" action button (@roicambe)

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
