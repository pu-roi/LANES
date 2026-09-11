# LANES Bug Fix Log & Issue Tracker

> **Last Updated:** September 11, 2026, 6:08 PM

This document records bugs, regressions, and unintended system behaviors that have been investigated, are pending resolution, or have been resolved in LANES. Each entry documents the bug context, root cause analysis, resolution strategy, and exact files modified to ensure a clear audit trail.

---

## 📋 Bug Resolution Format Standard

When adding entries to this log, use the following structure:

```markdown
### [BUG-XXX] Short Title of the Issue
- **Status**: [Resolved | In Progress | Investigating]
- **Severity**: [Critical | High | Medium | Low]
- **Date Reported / Resolved**: Month DD, YYYY
- **Affected Area**: [Frontend / Backend / Auth / Map / Database / Routing]
- **Author / Resolver**: [@username](https://github.com/username) (Full Name)

#### 1. Problem Description
Detailed description of the unexpected behavior, user steps to reproduce, and visual/operational symptoms.

#### 2. Root Cause Analysis (RCA)
Why the bug happened. Technical explanation of component state, lifecycle, race condition, or API mismatch.

#### 3. Solution & Architectural Strategy
How the issue was addressed, why this approach was selected, and how edge cases are safeguarded.

#### 4. Files Modified / What Changed
- `path/to/file1.ext`: Specific changes made.
- `path/to/file2.ext`: Specific changes made.
```

---

## 🗂️ Bug Log Entries

### [BUG-009] Admin Live Map Crashing on Login: Stale Edit Draft 404 & MapLibre getSource Timing
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Admin Live Map & Map Layer Hooks)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Upon logging into the administrator account and accessing `/admin/map` or `/admin/dashboard`, two distinct errors broke the map interface:
1. An error toast popped up saying *"Unable to resume your saved Edit Zone draft"*, with console output: `Failed to resume Edit Zone draft ApiError: Zone not found` triggered by `GET /api/v1/admin/zones/18 -> 404`.
2. A runtime exception was thrown: `Uncaught TypeError: Cannot read properties of undefined (reading 'getSource') at useMergePreviewLayer.useEffect (src/features/map/hooks/useMergePreviewLayer.ts:32:32)` during map initialization and MapTiler auto-recovery attempts.

#### 2. Root Cause Analysis (RCA)
1. **Stale Draft 404:** The admin client's IndexedDB draft storage retained an unfinished zone edit draft referencing zone ID `18`. Since Zone #18 had been deleted or reset in the database, the startup hook `findLatestZoneEditDraft` repeatedly attempted to fetch it and threw an unhandled 404 error toast on every single page load without ever discarding the invalid draft.
2. **MapLibre Style Readiness Timing:** During map startup or style recovery (e.g. MapTiler style timeout triggering `BaseMap` auto-recovery), MapLibre's internal `map.style` is temporarily `undefined`. `useMergePreviewLayer` executed `map.getSource(sourceId)` immediately at the top of its `useEffect` without verifying `map.getStyle()`, causing MapLibre's internal `this.style.getSource(id)` call to crash. In addition, the hook's unmount cleanup lacked defensive guards when tearing down layers on a destroyed map instance.

#### 3. Solution & Architectural Strategy
1. In `LiveMapPage.tsx`, updated the draft resuming effect to catch HTTP `404 Not Found` when requesting `getZone(draft.zoneId)`. On 404, it immediately calls `discardZoneEditDraft(createZoneDraftUserId, draft.zoneId)` to cleanly purge the obsolete draft from IndexedDB and silently ignores the missing zone without firing an alarmist toast.
2. In `useMergePreviewLayer.ts`, added `if (!map || !isLoaded || typeof map.getStyle !== "function" || !map.getStyle()) return;` before any MapLibre source or layer calls. Wrapped source retrieval and unmount cleanup in safe `try/catch` blocks.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Imported `discardZoneEditDraft` and purged stale drafts on 404 errors.
- `frontend/src/features/map/hooks/useMergePreviewLayer.ts`: Added `map.getStyle()` readiness guards and defensive cleanup handling.

---

### [BUG-008] User Reports Fetch 500 Error via Unexported get_flood_reports_by_user in CRUD Index
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Backend (Reports API & CRUD Module)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When a user (such as `roicambe`) submitted a flood report, the report was successfully inserted into PostgreSQL (`Report #1`). However, visiting the user's Profile or viewing submitted reports triggered an HTTP `500 Internal Server Error` on `GET /api/v1/reports/me`.

#### 2. Root Cause Analysis (RCA)
In `backend/app/api/v1/endpoints/reports.py`, the `read_my_reports` endpoint calls `crud.get_flood_reports_by_user(db=db, user_id=current_user.id)`. However, `backend/app/crud/__init__.py` did not import or expose `get_flood_reports_by_user` from `app.crud.report`. This resulted in an unhandled `AttributeError: module 'app.crud' has no attribute 'get_flood_reports_by_user'`, which the endpoint caught and converted into a `500 Internal Server Error: Database is offline`.

#### 3. Solution & Architectural Strategy
Updated `backend/app/crud/__init__.py` to import and expose `get_flood_reports_by_user`, along with other report and user management functions (`archive_flood_report`, `restore_flood_report`, `create_user_with_profile`, `update_user_role`), ensuring complete API module access.

#### 4. Files Modified / What Changed
- `backend/app/crud/__init__.py`: Added `get_flood_reports_by_user`, `archive_flood_report`, `restore_flood_report`, `create_user_with_profile`, and `update_user_role` to module exports.

---

### [BUG-007] Flood Preview Wait Has Weak Feedback and Report Controls Use Incorrect Defaults
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend / Map / Routing
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After the Decision #16 correctness repair, road verification could visibly pause while only a small loading text was shown. The Flood Report Start/End direction-swap button was absent, the first severity tile was selected automatically, and two-way coverage needed to be explicitly confirmed as opt-in.

#### 2. Root Cause Analysis (RCA)
The panel rendered `floodPreviewMessage` as ordinary status text for every preview state and did not use the existing shared loading overlay. `LocationInputGroup` retained swap support, but Flood Report no longer supplied its `canSwap` and `onSwap` properties. Local form initialization and reset paths hardcoded `visualOption` to `gutter`, with submission logic silently falling back to `low`. The backend also waited for its two independent directional route requests sequentially.

#### 3. Solution & Architectural Strategy
Flood Report now uses the shared accessible blocking overlay during verification on mobile and desktop, then shows the ordinary status explanation only after loading. The shared swap control exchanges coordinates and labels and triggers fresh validation. Bidirectional coverage remains false unless the user checks it. Severity begins empty, is required before advancing or saving, and has no implicit low-severity conversion. Directional route requests run concurrently while all validation rules remain unchanged.

#### 4. Files Modified / What Changed
- `frontend/src/shared/ui/feedback/LoadingOverlay.tsx`: Added reusable blocking behavior and accessible status semantics.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Integrated the loading screen, restored direction swapping, and enforced explicit two-way and severity choices.
- `backend/app/services/carriageway_service.py`: Executes independent forward/reverse Valhalla route checks concurrently.
- `backend/tests/test_carriageway_service.py`: Made directional-route regression mocking deterministic under concurrent execution.

---

### [BUG-006] Bidirectional Flood Preview Draws a Same-Side Parallel Line or Legal-Driving Loop
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend / Backend / Map / Routing
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
With “Affects both sides of the road (2-way)” enabled, narrow roads could display a second dashed orange line on the same side or a hooked loop through nearby streets instead of the real opposite carriageway. The Caruncho-area reproduction turned a short pair of anchors into an 834m legal-driving route.

A follow-up regression showed the corrected dashed route stopping visibly before its orange Start marker. The pin represented the raw selected anchor, while Valhalla returned a valid road snap several metres farther along the road.

After exact endpoint connectors were added, the apparent gap could still reappear only after loading completed even though the returned coordinate matched the marker.

#### 2. Root Cause Analysis (RCA)
`MapContext.tsx` first requested an ordinary traffic-law-aware route and passed that complete result into Decision #16. When anchor direction conflicted with mapped traffic flow, Valhalla legally detoured around neighboring roads. The carriageway service then used raw edge counts, searched only the left side, and accepted name similarity without proving distinct OSM way identity, lateral separation, overlap, or comparable length. A snap back onto the original road could therefore be labeled `DIVIDED_CARRIAGEWAY`.

The hardened service correctly limited endpoint snaps to 35 metres, but returned the snapped polyline unchanged. Because markers intentionally remained at the user’s raw anchors, accepted snap distance appeared as a gap between the marker and dashed coverage.

The remaining post-loading symptom was a MapLibre rendering artifact: changing from the temporary two-point line to the longer verified polyline recalculated `line-dasharray` phase. The endpoint could fall inside the pattern’s transparent interval, visually hiding the final portion despite correct geometry.

#### 3. Solution & Architectural Strategy
The backend now owns road-preview generation from raw anchors, evaluates both directions, rejects excessive detours, and uses length-weighted topology classification. Divided-road searches probe both sides and require road identity/class, distinct way IDs, opposing direction, parallelism, comparable length, longitudinal overlap, safe separation, and no loop. Narrow two-way roads intentionally render one mapped centerline. Ambiguous or unavailable graph data returns one conservative line with an explanation.

For a route that already passes endpoint-snap and loop validation, the backend now selects the candidate with the best combined endpoint fidelity and retains its snapped road vertices while adding short connectors to the exact Start and End anchors. Preview and persisted operational geometry therefore agree and visually meet both pins.

The shared preview hook additionally renders solid orange terminal caps for first/last segments no longer than 40 metres. These caps sit above the dashed layer and below the existing markers, while the road body remains dashed on both mobile and desktop maps.

#### 4. Files Modified / What Changed
- `backend/app/services/carriageway_service.py`: Added authoritative segment selection, conservative classification, two-sided probing, strict candidate validation, endpoint-fidelity ranking, and exact pin connectors.
- `backend/app/services/report_service.py`: Repeats raw-anchor validation before persistence so client geometry cannot create an unverified `MultiLineString`.
- `backend/app/api/v1/endpoints/routes.py`: Expanded the backward-compatible preview contract for raw anchors, coverage geometry, validation status, and explanation.
- `frontend/src/features/map/MapContext.tsx`: Removed the general-route preview chain and centralized shared preview status and geometry.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Added shared solid terminal-cap rendering and cleanup for public/admin preview maps.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Added responsive inline road-verification feedback.
- `frontend/src/features/admin/components/zones/`: Reused the same feedback and persisted validated dual-carriageway geometry for official zones.
- `backend/tests/test_carriageway_service.py`: Added focused regression coverage for narrow, divided, one-way, ambiguous, same-side, unrelated-road, loop, outage, concurrency, and exact pin endpoint cases.

---

### [BUG-005] Feed Post Creation 500 Error / Socket Hangup While Post Is Persisted in Database
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Backend (Feed API & Post Creation Serialization)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When submitting a community post containing media, video, and location, the UI reported an error (or socket hang up / 500 Internal Server Error). However, refreshing the feed revealed that the post was actually saved to the database and displayed properly.

#### 2. Root Cause Analysis (RCA)
- In `backend/app/api/v1/endpoints/posts.py`, the `create_post` endpoint committed the post and uploaded media to Cloudinary successfully.
- However, when returning the response, it manually spread `**post.__dict__` into a dictionary without the computed relational fields (`upvotes`, `downvotes`, `comment_count`, `report`, or clean Pydantic schema serialization). SQLAlchemy ORM internal state attributes (`_sa_instance_state`) inside `post.__dict__` interfered with FastAPI's `response_model=CommunityPostResponse` serialization, triggering a `ResponseValidationError` (HTTP 500) during output marshaling after the database transaction had already committed.

#### 3. Solution & Architectural Strategy
- Updated `create_post` in `backend/app/api/v1/endpoints/posts.py` to immediately retrieve the created post via `crud_feed.get_feed_post(db, post.id, user_id=current_user.id)` (or return an explicit, clean dictionary matching `CommunityPostResponse`), guaranteeing full consistency with the rest of the feed endpoints and avoiding raw ORM dict leaks.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/posts.py`: Used `crud_feed.get_feed_post` to format and return the newly created post with sanitized attributes.

---

### [BUG-004] Community Feed "View on Map" Pin Click Missing Coordinates Fly-To and Pulsing Ring
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Map & Feed Integration)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When viewing a post on `/feed` (or post detail or user profile) with an attached location, clicking the location button (`View on Map`) navigated to `/map`, but the map did not fly to the target coordinates or display the temporary red pulsing indicator ring.

#### 2. Root Cause Analysis (RCA)
- The click handlers originally invoked `router.push('/map?lat=${lat}&lng=${lng}&zoom=16')`.
- `MapCanvas` is a persistent root-level component across route changes. When transitioning from `/feed` to `/map`, Next.js App Router client transitions and `MapCanvas`'s `searchParams` hook did not reliably trigger the `useEffect([searchParams, isLoaded])` hook if the parameters were swallowed or unobserved during client route switching.
- However, `MapCanvas` already possessed a dedicated, robust `fly-to-location` window event listener (with built-in map camera animation and temporary animated pulsing DOM marker).

#### 3. Solution & Architectural Strategy
- Updated all "View on Map" click handlers to transition cleanly to `/map` and dispatch the `fly-to-location` custom event with coordinates and zoom level after a slight frame delay (150ms) to ensure layout readiness.
- Removed reliance on URL search parameters for ephemeral map focusing.

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/FeedPage.tsx`: Dispatches `fly-to-location` event with `{ latitude: lat, longitude: lng, zoom: 16 }` upon location badge click.
- `frontend/src/features/feed/PostDetailPage.tsx`: Updated `onViewMap` handler to dispatch `fly-to-location`.
- `frontend/src/features/profile/ProfileView.tsx`: Updated `handleViewMap` handler to dispatch `fly-to-location`.

---

### [BUG-003] Location Re-Selection in Create Post Modal Failing After Removal
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Create Post Modal / Map Picker)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In the `/feed` Create Post modal, attaching a location via "Choose on Map" worked on the first attempt. However, if the user removed the location and attempted to select a location a second, third, or fourth time, the location would no longer attach or populate until the entire modal was closed and reopened.

#### 2. Root Cause Analysis (RCA)
- State synchronization in the modal's location picker was retaining stale closure flags or unreset picking mode state when removing the active location tag.
- The map interaction listener was either still detached or held onto stale coordinates/unmounted event references without resetting picker readiness.

#### 3. Solution & Architectural Strategy
- Reset both coordinates state, location name state, and picker activation flags upon removing the location badge.
- Re-initialized the location selector hook lifecycle so subsequent "Choose on Map" triggers always mount fresh event listeners.

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/CreatePostModal.tsx`: Reset location picker state and re-armed map pick handlers upon location removal.

---

### [BUG-002] Logout UI Freezing / Requiring Manual Page Refresh
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend / Auth State
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When clicking "Log Out", the application UI appeared frozen or stuck on the current view. Only upon manually refreshing the browser did the session reflect that the user had indeed been logged out.

#### 2. Root Cause Analysis (RCA)
- The logout handler cleared tokens in `localStorage` but did not actively purge or reset React Query cache (`queryClient.clear()` / `queryClient.resetQueries()`) or notify dependent UI contexts.
- Components continued reading cached user data from memory, creating an apparent freeze until full browser reload reinitialized memory state.

#### 3. Solution & Architectural Strategy
- Updated authentication store / hook logout procedure to immediately invalidate and clear the QueryClient cache, reset user state to `null`, and trigger proper client routing back to `/login` or `/` without requiring manual page reloads.

#### 4. Files Modified / What Changed
- `frontend/src/features/auth/useAuth.ts`: Added reactive cache clearance and immediate navigation on logout.

---

### [BUG-001] Drafted Media Lost After Login Redirection in Create Post Modal
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Frontend (Feed / Create Post & Auth Recovery)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Unauthenticated users composing a post in `/feed` who attached images or videos and wrote text were prompted to log in. Upon authenticating and returning to `/feed`, only the text description was restored from draft; all uploaded images and video files were discarded.

#### 2. Root Cause Analysis (RCA)
- Drafts were stored in `localStorage`, which only supports serializable strings.
- Uploaded media objects were `File` or `Blob` instances which cannot be serialized cleanly into JSON strings; attempt to serialize them resulted in empty objects `{}` or dropped keys.

#### 3. Solution & Architectural Strategy
- Integrated browser-persistent storage (IndexedDB or cached base64/blob storage) for drafted post media files before auth redirect, restoring both description and files when the modal re-opens post-login.

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/CreatePostModal.tsx`: Implemented persistent draft recovery for media files.
