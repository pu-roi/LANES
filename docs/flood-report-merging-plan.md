# Intelligent Flood-Report Merging & Spatial Operations Redesign

> **Authoritative Implementation Plan**
> **Last Updated:** September 10, 2026, 11:58 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Reference:** Capstone Phase 18 (`docs/task_plan.md` and `docs/progress.md`)

Overhaul the flood-report merging logic, candidate identification, and Spatial Operations UI/UX to enable intelligent, multi-factor spatial matching, explainable recommendations, conflict resolution, and seamless final-zone editing while strictly preserving original crowdsourced reports and Community Feed posts.

---

## Current Phase 5 Implementation Status

The Phase 5 interface is implemented and awaits developer-led end-to-end verification. The delivered behavior supersedes the former audit findings:

1. Ordinary report selection is neutral: it focuses the report without deriving legacy candidates, filtering the queue, labeling reports as duplicates, or blocking standalone approval.
2. **Review Merge Suggestions** explicitly starts a merge session and fetches scored candidates. Loading, empty, error, retry, cancel, and defer states are visible.
3. Candidates begin unselected. Selection uses a prominent checkbox, and recommendations, conflicts, map previews, and proposed geometry reflect only the reports included by the admin.
4. Each candidate is a single readable report card. Its match score, consensus badge, and supporting evidence are grouped inside that card under its own explanation rather than floating between reports.
5. The workspace now has four stages: Candidates, Compare, Edit Zone, and Confirm. It reuses the official-zone road controls and Terra Draw geometry tools.
6. Create Zone and Review Merge use separate contextual edge-tab handles. Review Merge appears only after a merge session starts; collapsing it preserves the selected report, current step, choices, and edits until the admin changes the focused report or completes the merge.
7. The desktop workspace is docked; mobile uses a full-width workflow with an explicit map return control. Scrollbars are visually quiet until the relevant pane is hovered, focused, or actively scrolled.

Focused TypeScript, targeted ESLint, and production build checks pass. Manual desktop/mobile workflow and final submission verification remain open.

### Approved Phase 5 Execution Plan

1. **Neutral Report Inspection**: Remove legacy candidate derivation, forced spotlighting, duplicate terminology, and approval blocking from normal report clicks.
2. **Explicit Intelligent Review Entry**: Add a non-blocking **Review Merge Suggestions** action. Fetch `GET /admin/reports/merge-candidates` only inside the merge workflow and surface loading, empty, error, retry, cancel, and defer states.
3. **Admin-Owned Selection**: Rank candidates by confidence but start them unselected. Update map spotlight, proposed geometry, and conflict display from the explicit selection.
4. **Responsive Field Comparison**: Compare original report values in aligned rows/columns on desktop and a readable field-by-field stack on mobile, with differences and evidence clearly identified.
5. **Reusable Final-Zone Spatial Editing**: Reuse the official-zone road and Terra Draw controllers for Start/End, bidirectional, Polygon, Freehand, Rectangle, and Circle editing. Do not duplicate drawing logic.
6. **Deliberate Confirmation**: Add a fourth step summarizing included/excluded reports, destination, final values, final geometry, contributor credit, and data-preservation guarantees before calling `POST /admin/reports/merge`.
7. **Responsive and Accessibility Verification**: Preserve the docked desktop map workspace; use a full-width, safe-area-aware mobile workflow with an explicit way to inspect the map. Ensure keyboard labels, focus states, and non-color conflict indicators.
8. **Quality Gate and Documentation Sync**: Run focused lint/type checks and manual desktop/mobile verification. Update progress and system documentation only after the flow is functioning.

**Implementation status (Sept 10, 2026):** Steps 1–7 are implemented. TypeScript, focused ESLint (zero errors; one image-optimization warning), and the optimized Next.js production build pass. Step 8 remains open for developer-led desktop/mobile workflow and final-submission verification; the progress tracker and system documentation now record only the delivered, verified behavior.

---

## User Review Required

> [!IMPORTANT]
> **Layout & Interaction Architecture (Option Selection)**:
> We evaluated the three layout options (Option A: Improve Movable Panels, Option B: Map-Centered Merge Workspace, Option C: Multi-Stage Merge Workflow).
> We strongly recommend a **Docked Map-First Workspace (Hybrid of B & C)**:
> - The map canvas stays permanently mounted and 100% visible on the right with full-bleed real estate (preserving Decision #7).
> - Draggable floating `<Panel>` windows are replaced during merge operations with a clean, docked, collapsible workspace (~480px width on desktop; full-width bottom sheet on mobile).
> - Selected reports' geometries are rendered on the map with color-coded pins/lines, and the workspace guides the DRRMO admin through a structured 4-step workflow: **1. Select Reports $\rightarrow$ 2. Review & Compare Conflicts $\rightarrow$ 3. Edit Final Zone Data $\rightarrow$ 4. Confirm Merge**.

> [!IMPORTANT]
> **Database Schema Additions**:
> To support vehicle passability and hazard overrides directly on the merged official zone (consistent with `CreateOfficialZonePanel` and `FloodReportPanel`), we propose adding:
> - `passable_vehicles_override`: `VARCHAR(500)` nullable
> - `hidden_hazards_override`: Enum `HazardPresence` nullable
> - `merge_rationale`: `VARCHAR(1000)` nullable (stores the merge rationale summary)
> to `flood_avoidance_zones`. A clean Alembic migration will be created and run (`alembic upgrade head`).

> [!WARNING]
> **Community Feed Post & Crowdsourced Report Immutability**:
> Crowdsourced `FloodReport` records and `CommunityPost` records will **NEVER be overwritten or combined**.
> - Each user's post in the Community Feed remains 100% untouched (original text, photos, location tag, and author).
> - The merge operation strictly updates operational routing barriers (`flood_avoidance_zones`) and links each report's `zone_id` for 1:N deduplication and communal trust score awards (+5).

---

## Proposed Architecture & Logic Breakdown

### 1. Multi-Factor Intelligent Merge Engine (`merge_service.py`)
Rather than relying on naive barangay string matching or exact coordinate equality, the system computes an explainable **Merge Confidence Score (0–100%)**:
1. **Spatial & Topological Alignment (40 pts)**:
   - Buffer road lines into spatial corridors via PostGIS `ST_Buffer(geom, 0.00025)` ($\approx 25\text{m}$).
   - Computes corridor intersection ratio:
     $$\text{Overlap Ratio} = \frac{\text{ST\_Area}(\text{ST\_Intersection}(\text{corridor}_A, \text{corridor}_B))}{\text{Min}(\text{ST\_Area}(\text{corridor}_A), \text{ST\_Area}(\text{corridor}_B))}$$
   - Evaluates vector azimuth alignment: angles within $\pm 30^\circ$ (same direction) or $\pm 180^\circ \pm 30^\circ$ (opposite direction).
2. **Road / Street Identity (30 pts)**:
   - Normalized text matching stripping prefixes/suffixes ("Ave", "St", "Blvd", "Avenue", "Street", "Highway", "Road", "Dr", punctuation, lowercase).
   - Token-based Levenshtein / Trigram similarity $\ge 0.75$ and Valhalla edge name cross-referencing.
3. **Boundary & Locality Context (15 pts)**:
   - City match (mandatory).
   - Same barangay increases confidence score; adjacent barangays are allowed if the road crosses a boundary (e.g. Ortigas Ave).
   - Same barangay with different street names is strictly disqualified from merging.
4. **Temporal Proximity (15 pts)**:
   - Exponential decay based on report time difference (reports within 1 hour score max; $>12$ hours penalized).

### 2. Carriageway & Decision #16 Integration
- **Same Carriageway**: Union of road segments along the same travel line.
- **Opposite-Side of Undivided Road (`NARROW_TWO_WAY`)**: Handled as a single centerline representing both flows with `is_bidirectional = True`.
- **Divided Dual Carriageway (`DIVIDED_CARRIAGEWAY`)**:
  - Reuses `find_opposite_carriageway()` from Decision #16.
  - Automatically identifies opposing carriageway pairs (e.g. C-5 Northbound and Southbound) and merges them into a `MultiLineString` / `GeometryCollection`.
  - Avoidance buffer uses `ST_ConvexHull(ST_Collect(ST_Buffer(line1, r), ST_Buffer(line2, r)))`.
- **Service / Frontage Roads vs Expressways**:
  - Validates against OSM highway classification. Main expressway lanes will not merge with parallel service roads.

### 3. Conflict Resolution Engine
- **Severity**: Default to the highest reported severity among merged reports (safety-first in DRRM).
- **Water Depth**: Default to highest MMDA gauge; warn if a newer report indicates receding water.
- **Passable Vehicles**: Default to most restrictive vehicle clearance profile.
- **Admin Control**: All values are explicitly editable before confirming the merge.

---

## Proposed Changes

### Backend Components

#### [MODIFY] [backend/app/models/report.py](file:///d:/Documents/Github/LANES/backend/app/models/report.py)
- Add `passable_vehicles_override`, `hidden_hazards_override`, and `merge_rationale` columns to `FloodAvoidanceZone`.

#### [MODIFY] [backend/app/schemas/report.py](file:///d:/Documents/Github/LANES/backend/app/schemas/report.py)
- Add schemas for `MergeCandidateResponse`, `MergeCandidatesListResponse`, `MergeReportsRequest`, `MergeConflict`, and `MergedZoneFinalData`.

#### [NEW] [backend/alembic/versions/add_merge_overrides_to_avoidance_zones.py](file:///d:/Documents/Github/LANES/backend/alembic/versions/)
- Alembic migration script adding the new columns to `flood_avoidance_zones`.

#### [NEW] [backend/app/services/merge_service.py](file:///d:/Documents/Github/LANES/backend/app/services/merge_service.py)
- Implements:
  - `calculate_spatial_similarity(geom_a, geom_b, db)`
  - `normalize_road_name(name)`
  - `find_merge_candidates(report_id, db)`
  - `detect_conflicts(reports)`
  - `synthesize_merged_geometry(reports, is_bidirectional, db)`

#### [MODIFY] [backend/app/api/v1/endpoints/admin.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/admin.py)
- Add `GET /admin/reports/merge-candidates`: Returns scored candidate reports, match explanations, and detected conflicts.
- Add `POST /admin/reports/merge`: Transactional endpoint supporting multi-report merge into a new or existing avoidance zone with trust score crediting (+5 per unique reporter), SSE signaling, and audit logging.

#### [NEW] [backend/tests/test_flood_report_merging.py](file:///d:/Documents/Github/LANES/backend/tests/test_flood_report_merging.py)
- Automated Pytest suite covering spatial corridor overlap, candidate scoring, conflict detection, new zone creation, existing zone merge, trust score crediting, and feed post immutability.

---

### Frontend Components

#### [NEW] [frontend/src/features/admin/components/ZoneDataEditorForm.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/ZoneDataEditorForm.tsx)
- Reusable form and drawing controller extracted from `CreateOfficialZonePanel.tsx`.
- Supports Line mode (two-click Start/End pins with road snap and bidirectional preview) and TerraDraw shape modes (Polygon, Freehand, Rectangle, Circle).
- Controls for Zone Name, Severity pills, MMDA Visual Depth options, Vehicle Passability chips, Hidden Hazards, and Admin Notes.

#### [MODIFY] [frontend/src/features/admin/components/CreateOfficialZonePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/CreateOfficialZonePanel.tsx)
- Refactored to consume `ZoneDataEditorForm.tsx`, eliminating duplicate code.

#### [NEW] [frontend/src/features/admin/components/merge/MergeWorkspacePanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/merge/MergeWorkspacePanel.tsx)
- Docked, collapsible merge workspace integrating the 4-stage workflow:
  1. Candidate Selection
  2. Side-by-side Report Comparison & Conflict Resolution
  3. Final Zone Editing (reusing `ZoneDataEditorForm`)
  4. Confirmation & Submission

#### [NEW] [frontend/src/features/admin/components/merge/ReportComparisonCard.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/merge/ReportComparisonCard.tsx)
- Side-by-side comparison card displaying reporter details, trust score, timestamp, severity badge, water level, vehicle passability, description, and photo thumbnails.

#### [NEW] [frontend/src/features/admin/components/merge/MergeExplanationBanner.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/merge/MergeExplanationBanner.tsx)
- Human-readable explanation pill (e.g. "94% Match • Same Road (Ortigas Ave) • 160m overlap • Reported 20 mins apart").

#### [NEW] [frontend/src/features/admin/components/merge/ConflictResolutionNotice.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/merge/ConflictResolutionNotice.tsx)
- Visual warning banner highlighting attribute mismatches with quick-resolve recommendations.

#### [NEW] [frontend/src/features/map/hooks/useMergePreviewLayer.ts](file:///d:/Documents/Github/LANES/frontend/src/features/map/hooks/useMergePreviewLayer.ts)
- MapLibre custom hook rendering distinct colors for each selected candidate report and a pulsing live preview for the proposed merged zone.

#### [MODIFY] [frontend/src/features/admin/components/PendingReportsPanel.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/components/PendingReportsPanel.tsx)
- Remove naive barangay-wide blocking and broken modal.
- Connect "Review & Merge" button to open the `MergeWorkspacePanel`.

#### [MODIFY] [frontend/src/features/admin/LiveMapPage.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/admin/LiveMapPage.tsx)
- Integrate `MergeWorkspacePanel` and `useMergePreviewLayer` into the map workspace.

#### [MODIFY] [frontend/src/features/admin/adminApi.ts](file:///d:/Documents/Github/LANES/frontend/src/features/admin/adminApi.ts)
- Add TypeScript interfaces and API methods: `getMergeCandidates(reportId)` and `mergeReports(payload)`.

---

## Verification Plan

### Automated Tests
- Execute backend tests:
  ```powershell
  cd backend
  pytest tests/test_flood_report_merging.py -v
  ```
- Verify existing geocoding and spatial tests still pass:
  ```powershell
  pytest tests/test_report_geocoding.py -v
  pytest tests/test_spatial_merging.py -v
  ```

### Manual Verification
1. **Candidate Identification**:
   - Open `/admin/map`, select a pending report on a known street.
   - Verify that candidates are ranked by score with clear explanations.
   - Verify that reports on different streets in the same barangay are NOT falsely grouped.
2. **Conflict Resolution & Comparison**:
   - Verify side-by-side comparison displays differences in severity, water levels, and vehicle passability.
   - Test one-click conflict resolution chips.
3. **Spatial Editing**:
   - In Step 3, test both Line mode (moving Start/End pins) and TerraDraw Polygon mode.
   - Test "Affects both sides" toggle and verify opposite carriageway detection.
4. **Transaction & Data Integrity**:
   - Confirm merge.
   - Verify that the active avoidance zone is created/updated with the final attributes.
   - Verify that each reporter received +5 trust score.
   - Navigate to `/feed` and verify that the original Community Feed posts remain unchanged.
5. **Mobile Responsiveness**:
   - Verify layout adapts to mobile screen sizes with a clean slide-up bottom sheet.
