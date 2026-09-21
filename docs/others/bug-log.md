# LANES Bug Fix Log & Issue Tracker

> **Last Updated:** September 22, 2026, 2:50 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)


This document records bugs, regressions, and unintended system behaviors that have been investigated, are pending resolution, or have been resolved in LANES. Each entry documents the bug context, root cause analysis, resolution strategy, and exact files modified to ensure a clear audit trail.

---

### [BUG-056] Mobile Map Panels Rendered Incorrectly from Feed Navigation and Allowed Re-Opening of Dismissed Report Panels
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 22, 2026
- **Affected Area**: Mobile Navigation / Global Map Panels / Saved Places / Flood Reporting
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

On mobile/small screens:
1. When navigating from the Community Feed drawer menu by tapping "Add a Place" (`/map?panel=saveplace&tab=add`), the Flood Report panel opened instead of (or rendered directly over) the Save Place panel.
2. After submitting a flood report or sliding down/dismissing the report panel on mobile and navigating to another view, returning to the map page caused the Flood Report panel to re-open automatically.

#### 2. Root Cause Analysis (RCA)

- **Panel Mutual Exclusivity**: `setIsSavePlacePanelOpen(true)` in `MapContext.tsx` closed Analytics, but failed to call `setIsReportPanelOpenState(false)` and did not set `activePanelState("save_place")`. Because `FloodReportPanel` was rendered after `SavePlacePanel` in `GlobalMap.tsx` with identical fixed positioning and `z-40`, the flood report panel completely occluded the save place panel.
- **Persistent URL Query Parameters**: Navigating with `?action=report` was never sanitized upon closing or successfully submitting a report. When returning to the map, `searchParams.get("action") === "report"` re-triggered the `useEffect` in `GlobalMap.tsx`, opening the report panel repeatedly.
- **Mobile Dismissal & Gesture Limitations**: In `Panel.tsx`, the header close button (`X`) was wrapped in `{!isMobile && ...}`, leaving mobile bottom-sheets with no dedicated close button. Additionally, `onDragEnd` required an excessive drag threshold (`offset.y > 60`) without velocity checking, causing quick swipe-down dismiss gestures to bounce back open instead of triggering `onClose()`.
- **Client Media Query Mount Lag**: `useMediaQuery` initialized its boolean match state to `false`, causing temporary flash-evaluations of mobile components as desktop layouts during initial client hydration.

#### 3. Solution & Architectural Strategy

- Enforced strict mutual exclusivity in `MapContext.tsx`: opening Save Place now explicitly closes Flood Report and Analytics while switching `activePanel` to `"save_place"`.
- Synchronized query parameter handling in `GlobalMap.tsx` and `SavePlacePanel.tsx` for `panel=saveplace`, and added URL query parameter cleanup via `router.replace('/map', { scroll: false })` whenever `action=report` or `panel=saveplace` panels are dismissed or submitted.
- Bound mobile `FloodReportPanel` rendering strictly to `isOpen={isMobile ? (isReportPanelOpen && activePanel === "flood") : true}`.
- Added a dedicated mobile header close button in `Panel.tsx` and enabled velocity-based drag dismissal (`offset.y > 60 || velocity.y > 250`).
- Updated `useMediaQuery` to initialize synchronously from `window.matchMedia(query).matches` on the client.

#### 4. Files Modified / What Changed

- `frontend/src/features/map/MapContext.tsx`: Updated `setIsSavePlacePanelOpen` and `setIsReportPanelOpen` to guarantee mutual exclusivity and `activePanel` state transitions.
- `frontend/src/features/map/GlobalMap.tsx`: Handled `panel=saveplace`, cleaned up `action=report` on close, and restricted mobile `FloodReportPanel` `isOpen` to `activePanel === "flood"`.
- `frontend/src/features/places/SavePlacePanel.tsx`: Connected `setActivePanel` state and cleaned `panel=saveplace` URL search param on panel close.
- `frontend/src/shared/ui/layout/Panel.tsx`: Added mobile close (`X`) button and velocity-aware swipe-down dismissal.
- `frontend/src/hooks/useMediaQuery.ts`: Synchronized initial match state on client and added standard media query change listeners.

---

### [BUG-055] Cloud SQL Flood Events Can Outlive Their Origin Evidence
- **Status**: Investigating
- **Severity**: High
- **Date Reported**: September 22, 2026
- **Affected Area**: Cloud SQL / Flood Event Lifecycle / Flood History & Analytics
- **Author / Investigator**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Flood History shows active Flood Events #6 and #8 with zero linked reports and zero official zones, despite timeline entries that reference reports/zones #30/#22 and #36/#25. The event detail is accurate about the current links, but it exposes records that no longer meet the product rule that every Flood Event retains an origin report and an active event retains an official zone.

#### 2. Root Cause Analysis (RCA)

Read-only Cloud SQL inspection confirmed that the referenced reports and zones no longer exist, while the events and their `flood_event_timeline_entries.snapshot_json` references remain. `snapshot_json` is a historical display snapshot rather than a foreign-key relationship. The deployed `flood_reports.event_id` and `flood_avoidance_zones.event_id` links are nullable, so they do not require an event to retain evidence or a zone. The direct official-zone path can also create an event with no administrator-origin report.

#### 3. Solution & Architectural Strategy

Before any schema change, classify the existing orphaned events with staff. A missing source record must be explicitly rebuilt as an administrator-origin report/zone or the event must be ended/marked invalid; no automated process may invent or silently relink evidence. Then introduce a normalized origin/supporting report relationship with one origin per event, restrict deletion of linked evidence, and enforce the active-event/active-zone invariant transactionally with deferred database validation where cross-row constraints are needed.

#### 4. Files Modified / What Changed

- `docs/others/database-design-plan.md`: Added the observed Cloud SQL state, the current nullable-link limitation, and the proposed migration-safe integrity design.
- `docs/task_plan.md`, `docs/progress.md`, `docs/others/system-documentation.md`: Marked Phase 33 integrity remediation as pending and documented the staff-facing limitation.

---

### [BUG-054] Site Visitor Counter Reported Page Loads Rather Than Reliable Visitors
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Landing Page / Admin Dashboard Analytics
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

The landing-page visitor number was a single mutable counter. It trusted a boolean browser flag, had no daily trend, could not deduplicate signed-in users across devices, and offered no distinction between a legitimate visible browser and a known automated client.

#### 2. Root Cause Analysis (RCA)

`visitor_counts` stored only an accumulated integer. The browser set its local “visited” flag before knowing whether the counter request succeeded, while the server had no pseudonymous identifier or time dimension with which to deduplicate activity.

#### 3. Solution & Architectural Strategy

Added first-party daily visitor measurement. The browser creates one UUID in local storage only after it becomes visible; FastAPI immediately HMAC-hashes it and stores only the hash, date, timestamps, and an optional account reference. Aggregate reads count an account once across browsers when known, otherwise a browser hash once. Known bot user agents are rejected and rate limiting protects the intake endpoint. No IP address, location, browser fingerprint, or raw UUID is persisted.

#### 4. Files Modified / What Changed

- `backend/app/models/audit.py`, `services/visitor_analytics_service.py`, and migration `c9f3e7a6b210`: introduced indexed, daily pseudonymous visitor records and aggregate queries.
- `backend/app/api/v1/endpoints/public.py`, `admin.py`, and typed visitor schemas: added public recording/read behavior and a protected visitor-trend endpoint.
- `frontend/src/features/landing/HomeStats.tsx`, `features/admin/DashboardPage.tsx`, and `features/admin/adminApi.ts`: use the new tracker and show a responsive 30-day administrator chart.
- `backend/tests/test_visitor_analytics.py`, `test_visitor_analytics_authorization.py`: cover identifier hashing, bot filtering, and route authorization.

---

### [BUG-053] Flood History Workspace Drifted from the Admin Visual System
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Admin Panel / Flood History & Analytics
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Flood History & Analytics used raw selects, inputs, native date fields, and an independently styled mobile switcher. Its cards and chart typography were noticeably larger than the Admin Dashboard, and non-severity charts introduced conflicting teal and indigo accents. The first shared-date-picker pass also placed visible labels above only the two date fields, causing those controls to drop below the rest of the desktop filter row.

#### 2. Root Cause Analysis (RCA)

The Phase 33 workspace was delivered incrementally around its protected data behavior without a final pass against the shared UI library and the Admin Dashboard graph treatment.

#### 3. Solution & Architectural Strategy

Replaced the filter and view controls with shared components, exposed an accessible label on the reusable shared `Select`, and made chart cards more compact. Non-severity charts now share the dashboard's primary blue, subtle dashed grids, and dark tooltips; severity colors remain semantic. The shared `DatePicker` now accepts an in-field empty display and accessible label, so the From/To controls are identifiable without increasing their grid-row height.

#### 4. Files Modified / What Changed

- `frontend/src/features/flood-history/FloodEventAnalytics.tsx`, `FloodEventRecords.tsx`, `FloodEventVisualizations.tsx`: standardized controls, compacted the dashboard, and aligned visual tokens.
- `frontend/src/shared/ui/forms/Select.tsx`, `DatePicker.tsx`: added optional accessible labels; DatePicker also supports compact in-field empty text for aligned date-range controls.
- `frontend/tests/flood-history.spec.ts`: updated the records-filter smoke test for the shared-select interaction.

---

### [BUG-052] Repeated Flood Moderation Map Review Did Not Re-focus the Report
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Moderation Center / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Reviewing a Flood Report could fail after returning from Spatial Operations, and approved/rejected moderation records were not available to the pending-only map query.

#### 2. Root Cause Analysis (RCA)

The map cached an identical focus URL and only searched its pending-report dataset.

#### 3. Solution & Architectural Strategy

Each handoff has a fresh review token. Spatial Operations retrieves the exact admin-authorized report, renders only that report, and clears active-zone data while focused.

#### 4. Files Modified / What Changed

- `backend/app/api/v1/endpoints/admin.py`, `frontend/src/features/admin/adminApi.ts`, `frontend/src/features/admin/LiveMapPage.tsx`, `frontend/src/features/admin/components/FloodModerationQueue.tsx`

---

### [BUG-051] Admin-Created Accounts Encounter 404 Not Found on Profile Edit & Missing Admin Profile Management
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Backend / User Profile / Admin Panel / Identity Lifecycle
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When an account was created via the Admin Panel's Account Registry modal (`POST /api/v1/admin/users`) (such as user `roicambe`), visiting their profile and attempting to update profile details failed with `404 Not Found` (`Profile not found`). Furthermore, Super Admins (restricted from public routes by `NavigationWrapper.tsx`) had no interface within the Admin Panel to edit their personal information, manage their avatar, or update their password.

#### 2. Root Cause Analysis (RCA)
1. **Uninstantiated Profile Model**: The admin user creation handler in `backend/app/api/v1/endpoints/admin.py` called `crud.create_user()`, which only inserted a row into the `users` table without initializing a row in the `profiles` table.
2. **Missing Self-Healing Fallback**: `PATCH /api/v1/users/me/profile` assumed `current_user.profile` always existed, raising `HTTPException(404, detail="Profile not found")`. Avatar upload and delete endpoints had the same limitation.
3. **Database Not-Null Constraints**: The PostgreSQL `profiles` table schema specifies `NOT NULL` for `first_name` and `last_name`. Any naive fallback creation without default string values caused a `psycopg.errors.NotNullViolation`.
4. **Admin Route Separation**: Because Super Admins are restricted from public routes like `/profile`, administrative staff needed an integrated profile management hub directly within the Admin Panel (`/admin/*`).

#### 3. Solution & Architectural Strategy
1. **Auto-Provisioning on Creation**: Updated `create_admin_user` in `admin.py` to automatically instantiate and commit `models.Profile(user_id=new_user.id, first_name=new_user.username, last_name="", display_full_name=True, is_public=True)`.
2. **Self-Healing Token & Profile Handlers**:
   - Updated `POST /api/v1/auth/test-token` to detect missing profiles and auto-provision them on session validation, instantaneously healing existing accounts like `roicambe`.
   - Added self-healing fallback to `PATCH /api/v1/users/me/profile`, `POST /api/v1/users/me/avatar`, and `DELETE /api/v1/users/me/avatar` with proper `first_name=current_user.username` defaults.
3. **Native Admin Profile Management**:
   - Created `AdminProfilePage.tsx` at `/admin/profile` mirroring the public profile design (custom cover color banner with color picker, avatar upload/view/remove, and personal/address info via `EditProfileForm`).
   - Added password change capability (`PUT /api/v1/users/me/password`) with current password verification and live `<PasswordStrength>` validation.
   - Updated `AdminSidebar.tsx` with a staff user profile link card in the footer showing avatar, name, and staff role.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Auto-provisioned `Profile` on admin user creation.
- `backend/app/api/v1/endpoints/auth.py`: Auto-heal missing profile in `test-token` endpoint.
- `backend/app/api/v1/endpoints/users.py`: Self-healing fallback in profile/avatar endpoints; added `PUT /api/v1/users/me/password`.
- `backend/app/schemas/user.py` & `backend/app/schemas/__init__.py`: Added `PasswordChangeRequest` schema.
- `backend/tests/test_admin_profile.py`: Pytest suite verifying self-healing and password change.
- `frontend/src/features/admin/AdminProfilePage.tsx`: Dedicated admin profile page component.
- `frontend/src/app/admin/profile/page.tsx`: Page route for `/admin/profile`.
- `frontend/src/features/navigation/AdminSidebar.tsx`: Profile link card in sidebar footer.
- `frontend/src/features/admin/AdminLayout.tsx`: Zero padding for `/admin/profile` layout.
- `frontend/src/hooks/useProfile.ts`: Added `changePassword` mutation.

---

### [BUG-050] Unique Constraint Collision When Re-creating Soft-Deleted User Accounts & Unhandled 500 Banner
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 21, 2026
- **Affected Area**: Backend / Admin / Database / User Lifecycle
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When an administrator attempted to create a new user account in the User Registry (`POST /api/v1/admin/users`) with an email or username that belonged to a previously soft-deleted/archived user, the backend crashed with an unhandled `500 Internal Server Error` (`psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "ix_users_email"`), and the frontend showed a red inline banner `"Operation Refused - Internal Server Error"`.

#### 2. Root Cause Analysis (RCA)
1. Soft-deletion in LANES sets `deleted_at = datetime.utcnow()` without physically deleting the user row in PostgreSQL to preserve activity history.
2. The `users` table has global `UNIQUE` indexes on `email` (`ix_users_email`) and `username` (`ix_users_username`).
3. The user creation handler checked `crud.get_user_by_email()`, which only queries active accounts (`deleted_at IS NULL`). When the new user record was inserted, PostgreSQL rejected the duplicate key.
4. The endpoint lacked an `IntegrityError` rollback handler, causing FastAPI to throw an unhandled 500 error.
5. In the frontend `UsersPage.tsx`, mutation failures triggered a raw inline error banner instead of utilizing the shared toast system (`useToast`).

#### 3. Solution & Architectural Strategy
1. **Archive Purge & Recreation**: Updated `create_admin_user` in `admin.py` to identify any soft-deleted records holding the clean email or username and purge them via `crud.hard_delete_user()` before inserting the new user.
2. **Safe Commit & Conflict Handling**: Wrapped database commits in a `try...except IntegrityError` block with `db.rollback()`, returning a structured `409 Conflict` if duplicate values occur.
3. **Shared Toast UI**: Removed the inline `Operation Refused` alert banner in `UsersPage.tsx` and connected all user mutation callbacks to `toast.success` and `toast.error`.
4. **Archive Management**: Added `restoreUser` (`POST /api/v1/admin/users/{user_id}/restore`) and `hardDeleteUser` (`DELETE /api/v1/admin/users/{user_id}/permanent`) endpoints.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Added stale archive purge, `IntegrityError` rollback, and user restore/permanent delete endpoints.
- `frontend/src/features/admin/adminApi.ts`: Added `restoreUser` and `hardDeleteUser` API callers.
- `frontend/src/features/admin/UsersPage.tsx`: Removed inline `Operation Refused` banner and wired mutations to `useToast`.

---

### [BUG-049] Rejected Flood Reports Did Not Notify Their Submitter
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 20, 2026
- **Affected Area**: Backend / Notifications / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description

Rejecting a Flood Report removed it from the live moderation queue but did not create an in-app notification, leaving the reporter without a decision in the existing notification bell.

#### 2. Root Cause Analysis (RCA)

The structured rejection service wrote the report state and staff moderation outcome only; unlike Community Post moderation, it did not add a `Notification` in the same transaction.

#### 3. Solution & Architectural Strategy

The rejection service now creates a `SYSTEM` notification atomically with the outcome and trust update. It includes the selected rejection reason but deliberately excludes the internal staff note from both the message and payload.

#### 4. Files Modified / What Changed

- `backend/app/services/flood_event_service.py`: Adds the reporter notification to the rejection transaction.
- `frontend/src/features/admin/components/RejectFloodReportModal.tsx`: Explains the user-notification and staff-note privacy behavior before confirmation.
- `backend/tests/test_spatial_archive.py`: Verifies the notification payload and privacy boundary.

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

### [BUG-048] ReferenceError `isTouchDevice is not defined` on Admin Map Zone & Pending Report Hover/Click
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 19, 2026
- **Affected Area**: Frontend / Map Engine / Admin Portal
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When navigating to `/admin/map` and hovering over or clicking a pending flood report or avoidance zone on the MapLibre canvas, the client application threw an uncaught runtime exception in the browser console:
```text
[browser] Uncaught ReferenceError: isTouchDevice is not defined
    at usePendingReportsLayer.useEffect.handlePopupOpen (src\features\map\hooks\usePendingReportsLayer.ts:309:78)
    at usePendingReportsLayer.useEffect.handleMouseEnterOrMove (src\features\map\hooks\usePendingReportsLayer.ts:347:9)
```
This crashed popup rendering for pending reports and prevented administrators from inspecting report details directly on the spatial map.

#### 2. Root Cause Analysis (RCA)
1. **Missing Parameter in Hook Signature**: In `usePendingReportsLayer.ts`, popup rendering logic was adapted from `useFloodZonesLayer.ts` to render `FloodZonePopup` and handle hover/click timers. However, `isTouchDevice` was referenced in the hook without being declared in the function arguments or initialized in scope.
2. **Missing Touch Propagation in Admin Map**: `LiveMapPage.tsx` was computing `isMobile` via `useMediaQuery("(max-width: 640px), (pointer: coarse)")`, but passed hardcoded `false` into `useFloodZonesLayer` and did not pass touch state to `usePendingReportsLayer`.

#### 3. Solution & Architectural Strategy
1. **Parametric Touch Support**: Added `isTouchDevice: boolean = false` to `usePendingReportsLayer` parameter list and its `useEffect` dependency array.
2. **Touch-Aware Hover & Click Protocol**: Updated `handleMouseEnterOrMove`, `handleMouseLeave`, and `handleLayerClick` inside `usePendingReportsLayer.ts` to disable hover dwell timers on touch devices while cleanly opening the popup on click/tap, mirroring `useFloodZonesLayer.ts`.
3. **Propagate Responsive State**: Passed `isMobile` from `useMediaQuery` into both `useFloodZonesLayer` and `usePendingReportsLayer` in `LiveMapPage.tsx`.

#### 4. Files Modified / What Changed
- `frontend/src/features/map/hooks/usePendingReportsLayer.ts`: Added `isTouchDevice` parameter, touch-aware event listeners, and robust popup cleanup.
- `frontend/src/features/admin/LiveMapPage.tsx`: Connected `isMobile` to `useFloodZonesLayer` and `usePendingReportsLayer`.

---

### [BUG-047] Community Feed Voting Desynchronization, Incomplete Flip Delta & Full Feed Re-fetch Lag
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 19, 2026
- **Affected Area**: Frontend / Backend / Community Feed / Interaction Engine
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When commuters upvoted or downvoted posts on the Community Feed, several issues occurred:
1. **Network Lag / Feed Jitter**: The voting action relied on query invalidation (`invalidateQueries(['feed'])`), triggering a heavy 50-post re-fetch over the network before the UI count updated.
2. **Count Desynchronization on Flipped Votes**: Clicking Downvote while previously Upvoted (or vice versa) produced incorrect visual delta counts because the client only decremented by 1 rather than applying a net flip delta ($\pm 2$).
3. **Missing Response Payload**: The `POST /feed/{post_id}/vote` endpoint only returned a generic status message rather than the new authoritative upvote/downvote/net_score state, preventing authoritative client cache synchronization.

#### 2. Root Cause Analysis (RCA)
1. **Lack of Optimistic Cache Mutators**: Vote mutations did not implement `onMutate` optimistic updates on TanStack Query caches, forcing the UI to wait for network roundtrips.
2. **Absence of Dedicated Vote Response Schema**: Backend only returned `{ "status": "success", "message": "Vote recorded" }`, leaving clients with no authoritative post vote counters unless a full re-fetch occurred.

#### 3. Solution & Architectural Strategy
1. **Optimistic Tri-State Vote Calculation**: Implemented `onMutate` hooks across `FeedPage.tsx`, `PostDetailPage.tsx`, and `ProfileView.tsx` that instantly calculate new scores in 0ms (fresh vote $\pm 1$, flip $\pm 2$, cancel vote) and rollback on error.
2. **Authoritative Vote Response**: Created `VoteResponse` Pydantic model and updated `crud/interaction.py` to return the new exact `upvotes`, `downvotes`, `net_score`, and `user_interaction` in `POST /feed/{post_id}/vote`.
3. **Reddit-Style Compact Pill**: Consolidated disjointed counters into a unified `▲ Net Score ▼` pill badge with active color coding and hover breakdown.

#### 4. Files Modified / What Changed
- `backend/app/schemas/feed.py`: Added `VoteResponse` schema.
- `backend/app/crud/interaction.py`: Added `get_post_vote_summary` function.
- `backend/app/api/v1/endpoints/feed.py`: Updated vote endpoint to return `VoteResponse`.
- `frontend/src/features/feed/feedApi.ts`: Updated `votePost` return type.
- `frontend/src/features/feed/PostItem.tsx`: Implemented unified `▲ Net Score ▼` pill badge.
- `frontend/src/features/feed/FeedPage.tsx`: Added optimistic vote mutations.
- `frontend/src/features/feed/PostDetailPage.tsx`: Added optimistic vote mutations for detail view.
- `frontend/src/features/profile/ProfileView.tsx`: Added optimistic vote mutations for profile feed tabs.
- `backend/tests/test_feed_voting.py`: Added automated schema and response tests.

### [BUG-046] Mixed Content Browser Blocking on HTTPS Due to Trailing Slash Redirection and Missing Proxy Headers
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 19, 2026
- **Affected Area**: Frontend / Backend / Networking & Deployment (Cloud Run)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On production (`https://navlanes.live`), navigating to `/admin/dashboard` or `/admin/map` triggered repeated console errors:
```
Mixed Content: The page at 'https://navlanes.live/admin/dashboard' was loaded over HTTPS, but requested an insecure resource 'http://lanes-api-557679867071.asia-east1.run.app/api/v1/notifications?skip=0&limit=20'. This request has been blocked; the content must be served over HTTPS.
```
This caused the notification bell component to fail fetching unread notifications and flooded the browser console.

#### 2. Root Cause Analysis (RCA)
1. **Frontend Trailing Slash Inconsistency**: The root `layout.tsx` mounts `NotificationBell`, which calls `getNotifications(0, 20)`. In `frontend/src/features/notifications/notificationsApi.ts`, the fetch URL was formulated with a trailing slash before query parameters (`/notifications/?skip=${skip}&limit=${limit}`).
2. **FastAPI Trailing Slash Normalization**: In `backend/app/api/v1/endpoints/notifications.py`, the route was registered as `@router.get("")`. When receiving a request with a trailing slash (`/notifications/?...`), Starlette issued an automatic `HTTP 307 Temporary Redirect` to canonicalize the route to `/notifications?...`.
3. **Missing Reverse Proxy Protocol Propagation**: Google Cloud Run terminates SSL/TLS at its edge load balancer and forwards plain HTTP internally to port 8080. Because Uvicorn was running without `--proxy-headers --forwarded-allow-ips "*"` and without `ProxyHeadersMiddleware`, FastAPI was unaware that the client connection originated over HTTPS. Consequently, FastAPI generated the redirect `Location` header using `http://` instead of `https://`.
4. **Mixed Active Content Blocking**: Browsers strictly disallow HTTPS pages from following or executing active fetch/XHR requests to insecure HTTP endpoints, causing the browser to block the notification request immediately.

#### 3. Solution & Architectural Strategy
1. **Eliminated Unnecessary Client-Side Redirect**: Updated `getNotifications` in `notificationsApi.ts` to call `/notifications?skip=${skip}&limit=${limit}` directly without the redundant trailing slash. This prevents the 307 roundtrip altogether, optimizing latency.
2. **Dual Route Registration for Resilience**: Added `@router.get("/", response_model=NotificationPaginatedResponse, include_in_schema=False)` to `backend/app/api/v1/endpoints/notifications.py` so that requests sent either with or without trailing slashes resolve directly with `200 OK` without triggering redirects.
3. **Proxy Header & Protocol Forwarding Enforcement**:
   - Updated `backend/Dockerfile` CMD to execute Uvicorn with `--proxy-headers --forwarded-allow-ips '*'`.
   - Injected `ProxyHeadersMiddleware` into the FastAPI application in `backend/app/main.py` so FastAPI recognizes `X-Forwarded-Proto: https` from reverse proxies (Google Cloud Run / Envoy) and ensures any system-generated redirect retains the HTTPS scheme.

#### 4. Files Modified / What Changed
- `frontend/src/features/notifications/notificationsApi.ts`: Removed the trailing slash before query parameters in `getNotifications`.
- `backend/app/api/v1/endpoints/notifications.py`: Added `@router.get("/")` alias route to avoid 307 trailing slash redirects.
- `backend/Dockerfile`: Added `--proxy-headers --forwarded-allow-ips '*'` to Uvicorn command.
- `backend/app/main.py`: Added `ProxyHeadersMiddleware` with trusted hosts wildcard.

### [BUG-045] Cloud Build Trigger Failure Under Custom Service Account Due to Missing Logging Configuration
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: CI/CD / Google Cloud Build / Infrastructure
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When executing automated Google Cloud Build workflows (`cloudbuild.yaml`) triggered on git commit pushes, builds utilizing a custom/user-managed Google Cloud service account failed immediately at initiation with the error:
`generic::invalid_argument: if 'serviceAccount' is specified, the build must specify a Cloud Storage bucket for logging or specify logging option CLOUD_LOGGING_ONLY`.

#### 2. Root Cause Analysis (RCA)
By default, Google Cloud Build attempts to stream logs to default Google-managed Cloud Storage buckets. When builds are configured with a custom service account for least-privilege security access rather than the default compute service account, Google Cloud requires an explicit build option designating whether build logs should stream to a dedicated storage bucket or directly to Google Cloud Logging.

#### 3. Solution & Architectural Strategy
Configured `options: logging: CLOUD_LOGGING_ONLY` in the root configuration block of `cloudbuild.yaml`. This routes all build logs directly into Google Cloud Logging without mandating external storage bucket provisioning while ensuring build invocations under custom service accounts succeed seamlessly.

#### 4. Files Modified / What Changed
- `cloudbuild.yaml`: Added `options: logging: CLOUD_LOGGING_ONLY`.

### [BUG-044] Archived Avoidance Zone Media (Photos & Videos) Missing in Archive Center Zone Details Modal
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Backend / Admin Archive Center / Zone Details
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When administrators inspected deactivated or expired flood avoidance zones in the Archive Center (`/admin/archive` -> **Spatial Data** -> **Archived Zones**) by clicking the view/details action icon, the `ZoneDetailsModal` displayed hazard attributes, coordinates, and metadata, but completely lacked any attached media (photos and videos), even when the avoidance zone was created with direct media uploads or originated from citizen flood reports with photographic evidence. In contrast, `ReportDetailsModal` in the adjacent Archived Reports tab rendered evidence thumbnails.

#### 2. Root Cause Analysis (RCA)
1. **Frontend Omission**: `ZoneDetailsModal.tsx` was built with attribute sections (Hazard & Severity, Timing & Lifecycle, Location & Coordinates, Operational Notes) but omitted a media gallery section and never parsed `media_urls` or `report_media_urls`.
2. **Backend Aggregation Limitation**: In `backend/app/api/v1/endpoints/admin.py`, the internal helper `_attach_report_media` only inspected `zone.primary_report.media_urls` rather than aggregating across all associated child reports in `zone.reports`.
3. **Lazy Loading Exclusion**: In `backend/app/crud/report.py`, `get_all_avoidance_zones_filtered` did not include eager loading (`selectinload(models.FloodAvoidanceZone.reports)`) or author profile loading for avoidance zones, risking detached instance queries or empty child collections when assembling media lists.

#### 3. Solution & Architectural Strategy
1. **Aggregated Media Serialization**: Updated `_attach_report_media` in `admin.py` to aggregate media URLs from all linked reports (`zone.reports`) alongside the zone's direct `media_urls`, preserving source attribution tags (`"Zone"` vs `"Report"`).
2. **Eager Loading in CRUD**: Enhanced `get_all_avoidance_zones_filtered` in `crud/report.py` to eagerly load `reports`, `user`, and `profile` via `selectinload`.
3. **Attached Media & Evidence Gallery**: Built an **Attached Media & Evidence** gallery in `ZoneDetailsModal.tsx` supporting:
   - Dynamic photo and video thumbnail previews with video indicator badges (`Video` Lucide badge).
   - Source provenance tags indicating whether media was directly attached to the official zone or contributed by an associated field report.
   - Click-to-preview functionality opening full-resolution media in a secure new browser tab.
   - Empty state fallback showing a camera icon with "No attached photos or video evidence for this zone."
4. **ArchivePage Media Prop Forwarding**: Passed `onOpenMedia={(url) => window.open(url, '_blank')}` to `ReportDetailsModal` in `ArchivePage.tsx` for cross-modal interaction parity.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Updated `_attach_report_media` to aggregate media from all linked reports and combine with zone media.
- `backend/app/crud/report.py`: Added `selectinload` for `reports`, `user`, and `profile` in `get_all_avoidance_zones_filtered`.
- `frontend/src/features/archive/components/ZoneDetailsModal.tsx`: Added Attached Media & Evidence gallery with photo/video preview, badges, and source tags.
- `frontend/src/features/archive/ArchivePage.tsx`: Connected `onOpenMedia` handler on `ReportDetailsModal`.

### [BUG-043] Archive Center Archived Posts 500 Error on 'Profile' Object Has No Attribute 'full_name'
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Backend / Admin Archive Center / Post Serialization
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When browsing `/admin/archive` and navigating to the "Archived Posts" tab (or toggling between "Deleted Posts" and "Hidden Posts"), the backend terminal reported repeated `500 Internal Server Error` exceptions with the message:
```text
AttributeError: 'Profile' object has no attribute 'full_name'
Unhandled Exception on GET /api/v1/admin/posts/archived: 'Profile' object has no attribute 'full_name'
```
This caused the archived posts table to fail to load records whenever any archived or hidden post had an author or remover with an existing user profile.

#### 2. Root Cause Analysis (RCA)
In `backend/app/api/v1/endpoints/admin.py`, the serialization block in `get_archived_community_posts` and `restore_archived_post` attempted to resolve author and moderator names using `post.user.profile.full_name`, `post.deleted_by.profile.full_name`, and `post.hidden_by.profile.full_name`.
However, the `Profile` SQLAlchemy model (`backend/app/models/profile.py`) stores names as separate `first_name` and `last_name` columns; it does not contain a `full_name` column or property. Accessing the non-existent attribute raised an unhandled `AttributeError`, aborting the request with HTTP 500.

#### 3. Solution & Architectural Strategy
Created a centralized helper function `_get_user_display_name(user: Optional[models.User], fallback: Optional[str] = "Unknown") -> Optional[str]` that safely inspects `user.profile` and constructs the full name via `f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip()`. If the profile or names are empty, it gracefully falls back to `user.username`, and ultimately to the supplied fallback string or `None`. Replaced all direct `.full_name` attribute accesses across the post archive endpoints.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Added `_get_user_display_name` helper and replaced all `profile.full_name` property accesses in `get_archived_community_posts` and `restore_archived_post`.

### [BUG-042] Profile Page Settings "Hide Profile Picture" Lag & Inoperative Camera Action Options
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Profile / Photo Management / React Query Cache
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On the `/profile` page:
1. Toggling "Hide Profile Picture" in the Settings tab exhibited UI lag or appeared unresponsive because the change was not updated optimistically in React Query state, resulting in switch bounce.
2. Clicking the camera icon on the user avatar opened a dropdown with three options ("View Profile Picture", "Change Profile Picture", "Hide Profile Picture"). All three options were non-functional dummy buttons that merely closed the dropdown menu without executing any action.
3. The "Hide Profile Picture" option was redundantly duplicated inside both the camera button dropdown and the Settings tab.

#### 2. Root Cause Analysis (RCA)
1. In `useProfile.ts`, `updateProfileMutation` only called `queryClient.invalidateQueries({ queryKey: ['auth-user'] })` in `onSuccess` without optimistic state updates (`onMutate`) or immediate `setQueryData` cache synchronization. As a result, the UI had to wait for an asynchronous background refetch over HTTP to re-render, creating visual delays and apparent switch failure.
2. In `ProfileView.tsx`, the camera dropdown items ("View Profile Picture" and "Change Profile Picture") were placeholder buttons executing only `setShowAvatarMenu(false)`. No image viewer modal or file upload pipeline existed.
3. "Hide Profile Picture" was unnecessarily placed in the camera button dropdown when the official switch is centralized under Profile Settings.

#### 3. Solution & Architectural Strategy
1. **Optimistic Updates & Immediate Cache Synchronization**: Enhanced `useProfile.ts` with `onMutate` to immediately write updated profile state into `['auth-user']` with automatic rollback on failure, and `onSuccess` to synchronize `['auth-user']`, `['my-posts']`, and `['posts']`.
2. **View Profile Picture Modal**: Built a dedicated preview modal in `ProfileView.tsx` showing the high-resolution avatar, username, handle, and a privacy status badge ("Hidden from public") when enabled, along with action shortcuts. Also made clicking the avatar in the header directly open this modal.
3. **Change Profile Picture Pipeline**: Implemented file input triggering with image format verification (JPEG, PNG, WebP) and a 10MB size guard, uploading directly to Cloudinary via backend endpoint `POST /api/v1/users/me/avatar`.
4. **Remove Picture Capability**: Added a "Remove Picture" action allowing users to revert to the default initials avatar via `DELETE /api/v1/users/me/avatar`.
5. **Redundant Option Excision**: Removed "Hide Profile Picture" from the camera dropdown per design requirements. Added outside-click dismissal to `showAvatarMenu`.

#### 4. Files Modified / What Changed
- `frontend/src/features/profile/ProfileView.tsx`: Implemented View Profile Picture Modal, file selection handler, avatar dropdown cleanup, and outside-click handler.
- `frontend/src/hooks/useProfile.ts`: Added optimistic updates, cache synchronization, and `uploadAvatar`/`removeAvatar` mutations.
- `backend/app/api/v1/endpoints/users.py`: Added `POST /me/avatar` and `DELETE /me/avatar` endpoints with MIME type validation.

### [BUG-041] Database Connection Pool Exhaustion (QueuePool limit 20 overflow 10 reached) Caused by Persistent Streaming SSE Endpoints
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Backend / Database Pooling / Server-Sent Events (SSE) / LiveSync
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On the production Cloud Run backend service (`lanes-api`), continuous client streaming calls to `/api/v1/sync` and `/api/v1/sse` resulted in severe database connection pool exhaustion errors:
`sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached, connection timed out, timeout 30.00`.
Subsequent API requests across the entire platform failed with HTTP 500 until the container restarted.

#### 2. Root Cause Analysis (RCA)
1. In FastAPI endpoints `sse.py` and `sync.py`, the database session dependency (`db: Session = Depends(get_db)`) was injected directly at the endpoint signature level.
2. In FastAPI generator-based streaming responses (`StreamingResponse`), dependency cleanup (`get_db()`'s `yield` context manager) does not close or return the database connection to the SQLAlchemy `QueuePool` until the generator is closed.
3. Because SSE connections are long-lived and persistent, each connected client held an exclusive PostgreSQL connection check-out indefinitely. Once more than 30 clients connected, the pool (size 20 + overflow 10) was completely starved, blocking all other endpoints.

#### 3. Solution & Architectural Strategy
1. **Removed Session Dependency from Streaming Signatures**: Removed `db: Session = Depends(get_db)` from the long-lived streaming endpoints in `sse.py` and `sync.py`.
2. **Ephemeral Sessions Per Event/Poll**: Refactored the internal event generator loops to instantiate short-lived worker sessions (`with SessionLocal() as session:`) strictly for the duration of the query snapshot, immediately closing and returning the connection to the pool between polling intervals.
3. **Database Pool Configuration Hardening**: Tuned `pool_size`, `max_overflow`, and `pool_pre_ping=True` in `database.py` to ensure resilient recycling under high concurrency.
4. **Client-Side Reconnect Resilience**: In `useLiveSync.ts` and `useSSE.ts`, added exponential backoff, visibility-based pause/resume, and proper unmount aborts to avoid reconnect storms.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/sync.py`: Refactored streaming generator to use ephemeral database sessions.
- `backend/app/api/v1/endpoints/sse.py`: Removed long-lived DB dependency injection from streaming generator.
- `backend/app/core/database.py`: Hardened pool size, overflow limits, and pre-ping connectivity tests.
- `frontend/src/hooks/useLiveSync.ts`: Added tab visibility awareness and resilient backoff.
- `frontend/src/hooks/useSSE.ts`: Added connection teardown cleanup.

### [BUG-040] AI Weather Insights Failed with 500 on Production Domain Due to Hardcoded Relative Fetch and Build-Time Rewrite Mismatch
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Production Cloud Infrastructure / Weather Insights
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On the production deployment (`https://navlanes.live`), opening the AI Weather Insights modal on the landing page failed with `500 Internal Server Error`, while the local dev environment and direct Cloud Run endpoint (`https://lanes-api-557679867071.asia-east1.run.app/api/v1/weather/insights`) responded with `200 OK`.

#### 2. Root Cause Analysis (RCA)
1. In `WeatherInsightsModal.tsx`, the API request hardcoded a relative URL path (`fetch('/api/v1/weather/insights')`) rather than using `process.env.NEXT_PUBLIC_API_URL`.
2. On Firebase App Hosting, the browser sent the request to the Next.js frontend container (`https://navlanes.live/api/v1/weather/insights`) instead of the Cloud Run API.
3. In `frontend/apphosting.yaml`, `BACKEND_URL` only had `RUNTIME` availability. During `next build`, Next.js rewrites in `next.config.ts` evaluated `process.env.BACKEND_URL` as undefined, falling back to `http://127.0.0.1:8000`. Because no backend runs inside the App Hosting container, Next.js server proxies failed and returned `500 Internal Server Error`.

#### 3. Solution & Architectural Strategy
1. Standardized `WeatherInsightsModal.tsx` to read `process.env.NEXT_PUBLIC_API_URL || '/api/v1'` matching `ForecastChart.tsx`, `apiClient.ts`, and auth components. The browser now calls the live Cloud Run backend gateway directly.
2. Added `BUILD` availability to `BACKEND_URL` in `apphosting.yaml` so any server-side Next.js rewrites correctly resolve `https://lanes-api-557679867071.asia-east1.run.app` at build time.

#### 4. Files Modified / What Changed
- `frontend/src/features/landing/WeatherInsightsModal.tsx`: Updated fetch call to use `NEXT_PUBLIC_API_URL`.
- `frontend/apphosting.yaml`: Added `BUILD` availability to `BACKEND_URL`.

### [BUG-039] TerraDraw Source Collision ("td-polygon already exists") and Perpetual Map Style Reload Loop in Edit Flood Zone
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 18, 2026
- **Affected Area**: Frontend / Map / Admin Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In `/admin/map`, when an administrator opened an existing road flood zone (e.g. Zone #1) and switched Spatial Geometry to Polygon mode, clicking on the map did not draw vertices and the instruction banner did not appear. The browser console reported `Failed to initialize TerraDraw: Error: Source "td-polygon" already exists`. Simultaneously, the map style entered an infinite background reload loop every 40–120 seconds due to MapTiler 403 Forbidden errors, wiping active layers and disrupting drawing interactions.

#### 2. Root Cause Analysis (RCA)
1. **Competing TerraDraw Instances**: Both CreateOfficialZonePanel (Pane 1) and EditOfficialZonePanel (Pane 2) were mounted simultaneously in `LiveMapPage.tsx`. In `OfficialZoneDrawer.tsx`, `useTerraDraw` was called with `isEnabled: true` hardcoded instead of `isEnabled: isOpen`. Pane 1 claimed `td-polygon` on `mapInstance`, so when Pane 2 mounted upon clicking "Edit", `draw.start()` threw `Source "td-polygon" already exists`, leaving `drawRef.current` null and the drawing tool uninitialized.
2. **Missing Mode Sync Dependency**: In `useTerraDraw.ts`, the mode sync effect did not depend on `drawInstance`. When TerraDraw finished asynchronous initialization after the component had already switched to `polygon`, the mode sync effect did not re-fire, leaving TerraDraw in `static` mode with `isDrawingMode` as false.
3. **Unbounded Retries on 403**: In `BaseMap.tsx`, `schedulePrimaryRetry` continually attempted to reapply the primary MapTiler style without checking whether the failure was a permanent authorization error (401/403).

#### 3. Solution & Architectural Strategy
1. **Instance Gating**: Gated `useTerraDraw` with `isEnabled: isOpen` so only the currently active, visible drawer connects TerraDraw to the map.
2. **Robust Cleanup**: Hardened `removeStaleTerraDrawArtifacts` to purge all `td-*` layers (outline, markers, fills) and sources (`td-polygon`, `td-linestring`, `td-point`) in proper detachment order before adapter creation and upon drawer unmount.
3. **Immediate Mode Activation**: Applied active mode immediately upon `draw.start()` and added `drawInstance` to mode sync dependencies so the crosshair cursor and instruction banner activate directly.
4. **Permanent Auth Throttling**: Added `isPermanentAuthError` detection in `BaseMap.tsx` to halt automated retries on 401/403 or invalid keys, preventing background style reload loops.
5. **Visual-Readiness Optimization**: Uses the first MapLibre render after `style.load` as the usability signal rather than waiting for all font glyph ranges. DNS/TLS preconnect and production PWA caching reduce cold connection work and accelerate later visits.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx`: Changed `isEnabled` to `isOpen` in `useTerraDraw` and added drawing restoration from `polygonSessionCacheRef` when `drawInstance` becomes ready.
- `frontend/src/features/admin/components/zones/hooks/useTerraDraw.ts`: Hardened layer/source cleanup in `removeStaleTerraDrawArtifacts`, set mode directly on start, and included `drawInstance` in mode sync dependencies.
- `frontend/src/shared/ui/map/BaseMap.tsx`: Throttled retries and halted automated style reload loop on permanent 401/403 errors.
- `frontend/src/app/layout.tsx`, `frontend/next.config.ts`: Added MapTiler connection hints and runtime caching for styles, glyphs, sprites, and tiles.
- `frontend/src/features/admin/LiveMapPage.tsx`: Isolated active zone layer so only the reference line represents the zone during editing.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Added `showMarkers` prop to hide pins in polygon mode while keeping the reference line.
- `frontend/src/features/map/MapContext.tsx`: Exposed `floodShowMarkers` state and setter.
- `frontend/src/features/admin/components/AdminFloodMapInteraction.tsx`: Forwarded `floodShowMarkers` to preview hook.
- `frontend/src/features/map/MapCanvas.tsx`: Forwarded `floodShowMarkers` to preview hook.

### [BUG-038] MapTiler Recovery and TerraDraw Could Retain Stale Map State
- **Status**: Resolved in code / manual verification pending
- **Severity**: High
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Map / Admin Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After an initial MapTiler-to-OSM fallback, successful MapTiler retries could continue to log `primary_retry_timeout`. Separately, reopening an Admin polygon workspace could fail with `Source "td-polygon" already exists`.

#### 2. Root Cause Analysis (RCA)
The fallback detector checked generic/nonexistent OSM identifiers, while MapTiler styles may also define a generic `osm` source. TerraDraw's deferred `style.load` initialization could run after React cleanup and leave its adapter layers/sources on the current MapLibre style.

#### 3. Solution & Architectural Strategy
The fallback style now uses LANES-specific source/layer identifiers and validates the actual active style before accepting a retry. TerraDraw cancels the deferred listener during cleanup and removes only its known stale adapter artifacts before creating its single replacement instance.

#### 4. Files Modified / What Changed
- `frontend/src/shared/ui/map/BaseMap.tsx`: Added LANES-specific OSM fallback identity and reliable active-style matching.
- `frontend/src/features/admin/components/zones/hooks/useTerraDraw.ts`: Added deferred-listener cleanup and safe stale TerraDraw artifact removal.

### [BUG-037] MapTiler Startup Timeout Recreated the Map and Prevented Automatic Detailed-Style Restoration
- **Status**: Resolved in code / manual verification pending
- **Severity**: Medium
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Map / PWA
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On `/map`, MapTiler could wait through a 2-second network preflight and an 8-second style watchdog before switching to OSM. Repeated retries destroyed and recreated the WebGL map, producing noisy browser logs and delaying access to a usable map. The fallback status could also overlap desktop map controls.

#### 2. Root Cause Analysis (RCA)
The map lifecycle treated MapTiler availability as a blocking preflight and recreated `MapLibre.Map` for each recovery attempt. After replacing the initial timed-out MapTiler style with OSM, the lifecycle did not mark that first successful fallback style as complete; later MapTiler `style.load` events were therefore ignored, even when the browser had successfully retrieved the style and tiles.

#### 3. Solution & Architectural Strategy
Removed the preflight and recreation loop. One MapLibre instance now starts with MapTiler and switches in place to OSM after 1.5 seconds or a confirmed MapTiler resource error. Attempt IDs, timer cleanup, and redacted structured diagnostics protect against stale callbacks. OSM is immediately usable; MapTiler retries on the `online` event and exponential backoff, with a six-second recovery window. Completing OSM marks the lifecycle ready for a later successful MapTiler `style.load`; existing feature hooks restore layers after each style replacement. The recovery notice is fixed to the viewport, constrained responsively, and placed below the desktop floating navigation.

#### 4. Files Modified / What Changed
- `frontend/src/shared/ui/map/BaseMap.tsx`: Implemented one-instance startup/fallback/retry lifecycle, diagnostics, lifecycle-completion guard, and responsive recovery notice.
- `frontend/src/features/map/MapCanvas.tsx`: Removed the unused duplicate hardcoded MapTiler style state.
- `frontend/apphosting.yaml`, `frontend/.env.local`: Centralized browser style configuration under `NEXT_PUBLIC_MAPTILER_KEY`; production configuration references the `maptiler-api-key` App Hosting secret.

---

### [BUG-036] Live Sync SSE Stream Exhausts SQLAlchemy Connection Pool Causing Cascading 500 & Apparent CORS Errors
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Database / SSE / Sync / CORS
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In production, all public API requests (`/api/v1/public/stats`, `/api/v1/feed`, `/api/v1/reports/active-zones`) began hanging for 30 seconds and failing with `HTTP 500 Internal Server Error: QueuePool limit of size 20 overflow 10 reached, connection timed out, timeout 30.00`. In web browsers, these failed requests appeared as `Access to fetch at ... has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource`.

#### 2. Root Cause Analysis (RCA)
1. **Connection Leak in SSE Streaming Endpoint**: The `/api/v1/sync/stream` endpoint had `db: Session = Depends(get_db)`. In FastAPI, dependencies provided via `Depends(get_db)` remain checked out for the entire lifetime of the HTTP connection. Because `EventSourceResponse` runs an infinite polling loop (`while True: await asyncio.sleep(10)`), each connected client held an active PostgreSQL database connection indefinitely. As soon as ~30 clients connected (or reconnects triggered), the entire connection pool was exhausted.
2. **Cascading Reconnect Storm**: When connections timed out, the SSE generator threw an unhandled exception, closing the stream. The frontend's `EventSource` automatically reconnected, requesting another connection and exacerbating the deadlock.
3. **CORS Masking of 500 Errors**: Starlette's raw `ServerErrorMiddleware` catches unhandled exceptions and outputs a plain `text/plain` 500 response without passing through `CORSMiddleware`. Browsers blocked reading the 500 error response due to missing `Access-Control-Allow-Origin` headers, making server database timeouts masquerade as CORS errors in developer tools.

#### 3. Solution & Architectural Strategy
1. **Short-Lived Sessions in Background Worker**: Removed `db: Session = Depends(get_db)` from `/api/v1/sync/stream`. Created `_get_active_floods_safe()` using `with SessionLocal() as db:` wrapped in `try/finally: db.close()`. Executed it using `await asyncio.to_thread(_get_active_floods_safe)` so that database checkouts only last milliseconds and 0 connections are held during the 10-second SSE idle sleep.
2. **Graceful Exception Fallback**: If a database blip occurs during live sync, `_get_active_floods_safe()` catches the exception and returns empty results rather than crashing the client's SSE connection and triggering reconnect storms.
3. **Calibrated Engine Pool**: Added `pool_timeout=10` to `create_engine` (reduced from 30s) and increased pool limits (`pool_size=25`, `max_overflow=20`) to prevent requests from hanging indefinitely during spikes.
4. **Global Exception Handler**: Added `@app.exception_handler(Exception)` in `backend/app/main.py` returning `JSONResponse(status_code=500)` so that uncaught server errors always pass through `CORSMiddleware` and supply proper CORS headers to the client.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/sync.py`: Removed `Depends(get_db)` from streaming route; decoupled queries into short-lived thread-pool sessions.
- `backend/app/core/database.py`: Added `pool_timeout=10` and tuned pool size to fail fast and accommodate burst traffic.
- `backend/app/main.py`: Added global `Exception` handler returning `JSONResponse` with CORS headers.

---

### [BUG-035] Flood-Routing Providers Return Inconsistent and Non-Route-Specific Safety Results
- **Status**: Resolved in code / Cloud verification pending
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Routing / Valhalla / OpenRouteService / Route Planner
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Valhalla and ORS do not currently apply the same flood passability rules or return trustworthy per-route flood metadata. A user can receive a blocked direct ORS route alongside safe routes, while the equivalent Valhalla path is suppressed. Cautious pedestrian and high-clearance routing is only partially represented by Valhalla and absent from ORS. The active route cards therefore cannot consistently explain vehicle safety, danger, or ranking.

#### 2. Root Cause Analysis (RCA)
1. Both provider services independently query and classify active flood polygons instead of consuming one policy result.
2. `valhalla_service.py` submits `avoid_polygons`, although the Valhalla route API documents `exclude_polygons`; its direct-route risk assessment assumes every active orange/yellow zone was intersected.
3. `ors_service.py` uses only binary `avoid_polygons`, inserts an always-blocked direct route, and labels all surviving routes 100% safe without measuring their intersections.
4. There is no centralized post-route PostGIS intersection evaluator, common exposure score, deterministic category ranker, or parity test suite. The current focused routing tests also contain stale `httpx.post` mocks (6 passed, 4 failed).

#### 3. Solution & Architectural Strategy
Implemented a typed FastAPI flood-routing policy and active-zone loader as the sole source of business decisions. Valhalla receives documented `exclude_polygons`; ORS receives GeoJSON `options.avoid_polygons`; both produce raw candidates only. The shared evaluator intersects each candidate geometry with authoritative active-zone geometry, attaches deterministic exposure/safety metadata, rejects impassable routes, deduplicates overlaps, and assigns up to four distinct Fastest/Safest/Balanced/Alternative cards. Walking through Orange is a strongly cautioned 40% fallback; vehicles remain blocked and Red remains blocked for every public profile. A blocked baseline is returned only as a non-selectable explanation when it was the fastest raw choice. Offline cached zones now carry server-authored per-profile restriction metadata and legacy metadata is treated conservatively.

#### 4. Files Modified / What Changed
- `backend/app/services/flood_routing_policy.py`, `routing_service.py`: Added shared policy, authoritative-zone evaluation, exposure scoring, deduplication, and deterministic ranking.
- `backend/app/services/valhalla_service.py`, `ors_service.py`, `report_service.py`: Converted current route flow to provider adapters, corrected polygon payloads, and synchronized offline restriction metadata.
- `backend/app/schemas/route.py`, `backend/tests/test_flood_routing_policy.py`, `backend/tests/test_routing_service.py`: Extended the contract and added/updated focused coverage (20 passing tests).
- `frontend/src/features/routing/routingApi.ts`, `RoutePanel.tsx`, `MapContext.tsx`, `workers/valhallaCore.ts`: Render route categories/exposure and a non-selectable blocked explanation on responsive layouts; keep offline routing fail-closed.
- `frontend/src/features/landing/FloodLegend.tsx`, `frontend/src/features/hazards/FloodReportPanel.tsx`: Corrected Medium-water passability wording.
- `docs/task_plan.md`, `docs/others/routing-logic.md`, `docs/others/vehicle-passability.md`, `docs/others/system-documentation.md`: Updated the policy and verification record.

### [BUG-034] Admin Login Redirection Routing to /feed Instead of /admin/dashboard
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Authentication / Client-Side Routing / Role-Based Access Control
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When logging in with an administrative account (e.g., `Super Admin`, `DRRM Officer`, `Moderator`), users were erroneously redirected to the `/feed` page (or `/feed?openPostModal=true`) instead of the admin dashboard (`/admin/dashboard`).

#### 2. Root Cause Analysis (RCA)
1. In `LoginForm.tsx`, `useGoogleAuth.ts`, and `login/page.tsx`, URL redirection (`redirectTo`) and guest post intent (`lanes_post_intent` stored in `sessionStorage` when unauthenticated users interacted with "Create Post" in the feed) were evaluated before checking user role (`isAdminRole`).
2. If `redirectTo` pointed to `/feed` or `/login?redirect=%2Ffeed`, or if `lanes_post_intent` was persisted in `sessionStorage`, the login process dispatched `router.push(redirectTo)` or `router.push('/feed?openPostModal=true')` immediately, bypassing the admin dashboard redirection logic entirely.
3. In `NavigationWrapper.tsx`, route guards only checked exact equality for `Super Admin` and lacked normalized coverage for other staff/admin roles, allowing admins to remain on or be directed to commuter pages.

#### 3. Solution & Architectural Strategy
1. **Admin-First Priority**: Inverted the navigation decision tree across `LoginForm.tsx`, `login/page.tsx`, and `useGoogleAuth.ts` so that `isAdminRole` is evaluated before any commuter post intent or public redirect targets.
2. **Post Intent Clearing**: When an admin account logs in, `sessionStorage.removeItem("lanes_post_intent")` is immediately invoked to purge any guest commuter draft intents.
3. **Target Routing**: If an admin account logs in with an explicit admin destination (`redirectTo.startsWith("/admin")`), they navigate directly to that sub-route; otherwise, they default to `/admin/dashboard`.
4. **Hardened Route Guards**: Updated `NavigationWrapper.tsx` to ensure any non-staff user attempting to access `/admin` is ejected to `/`, while `Super Admin` accounts visiting public routes are forwarded to `/admin/dashboard`.

#### 4. Files Modified / What Changed
- `frontend/src/features/auth/LoginForm.tsx`: Prioritized `isAdminRole` in post-login navigation, cleaned up session post intents, and routed non-admin deep-links appropriately.
- `frontend/src/app/(auth)/login/page.tsx`: Aligned the `useEffect` auth redirection logic so authenticated admin sessions navigate directly to `/admin/dashboard`.
- `frontend/src/features/auth/hooks/useGoogleAuth.ts`: Updated Google OAuth completion navigation to enforce the same admin-first routing priority.
- `frontend/src/features/navigation/NavigationWrapper.tsx`: Hardened role checks to recognize staff accounts and enforce route boundaries.

---

### [BUG-033] Forgot Password Link on Login Form Was an Inert Anchor Tag
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Backend / Authentication / Password Recovery
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The "Forgot password?" link on the login form was an inert `<a href="#">` element with no backend password recovery endpoints or verification workflow.

#### 2. Root Cause Analysis (RCA)
No password reset endpoints or client-side recovery views had been created. The platform required a secure, OTP-verified reset flow adhering to strict anti-enumeration and brute-force protection standards.

#### 3. Solution & Architectural Strategy
1. **Backend Endpoints & Cryptographic Security**:
   - `POST /api/v1/auth/forgot-password/request-otp`: Checks user status and resend cooldown eligibility; returns a generic success response to prevent email enumeration.
   - `POST /api/v1/auth/forgot-password/verify-otp`: Validates the 6-digit OTP against active codes and mints a signed 15-minute `reset_token` (JWT with `scope: "password_reset"`).
   - `POST /api/v1/auth/forgot-password/reset`: Validates the JWT signature and scope, enforces password complexity, updates `user.hashed_password`, purges OTP records, and logs `PASSWORD_RESET_SUCCESS`.
2. **Branded Email Notification**: Created `send_password_reset_email_async` delivering a clean, hosted-branding HTML email via Resend with single-use OTP code and expiry warnings.
3. **Consistent UI Experience**:
   - Created `ForgotPasswordForm` featuring a pixel-for-pixel consistent design with the registration flow: identical 6-box OTP inputs, auto-advance, clipboard paste support, progressive resend timer, `<PasswordStrength>` validation meter, and hold-to-view eye icons.
   - Integrated in-place transition into `LoginForm` preserving the split-screen Agnes background shell on desktop and mobile.
   - Added `/forgot-password` route redirection to `/login?forgot=true`.

#### 4. Files Modified / What Changed
- `backend/app/core/security.py`: Added `create_password_reset_token` and `verify_password_reset_token`.
- `backend/app/schemas/auth.py` & `backend/app/schemas/__init__.py`: Added password reset request/verify/confirm schemas.
- `backend/app/crud/user.py` & `backend/app/crud/__init__.py`: Added `update_user_password`.
- `backend/app/services/email_service.py`: Added `send_password_reset_email_async`.
- `backend/app/services/auth_service.py`: Added `generate_and_send_password_reset_otp`.
- `backend/app/api/v1/endpoints/auth.py`: Added `forgot-password/request-otp`, `verify-otp`, and `reset` endpoints with rate limiting.
- `backend/tests/test_forgot_password.py`: Unit test suite (7 tests) covering anti-enumeration, token forgery protection, and complexity rules.
- `frontend/src/features/auth/api/authClient.ts`: Added forgot password API calls.
- `frontend/src/features/auth/components/ForgotPasswordForm.tsx`: Created 4-phase animated recovery form.
- `frontend/src/features/auth/LoginForm.tsx`: Wired "Forgot password?" button to toggle recovery mode in-place.
- `frontend/src/app/(auth)/login/page.tsx`: Added dynamic header and view state binding.
- `frontend/src/app/(auth)/forgot-password/page.tsx`: Added fallback route redirecting to `/login?forgot=true`.

### [BUG-032] Google Sign-In and Registration Buttons Were Inert Placeholders
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Backend / Authentication / OAuth
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The "Sign in with Google" and "Sign up with Google" buttons on the Login and Registration forms were static UI placeholders that displayed an "Under Development" toast rather than executing an OAuth authentication flow.

#### 2. Root Cause Analysis (RCA)
Google OAuth 2.0 Web Client credentials had not yet been integrated into the system, and the backend lacked an endpoint to verify Google ID tokens / OAuth access tokens and authenticate or register users.

#### 3. Solution & Architectural Strategy
1. **Google Identity Services Integration**: Created `useGoogleAuth` hook using Google's modern GIS library (`accounts.google.com/gsi/client`) and `initTokenClient` for popup-blocker-free custom button authorization.
2. **Backend OAuth Gateway**: Added `POST /api/v1/auth/google` with rate limiting and audience verification (`GOOGLE_CLIENT_ID`) protecting against token substitution attacks.
3. **Intent-Specific Auth Flow (Strict Login vs Auto-Fill Signup)**:
   - **Login Mode**: When signing in from `/login`, unregistered Google accounts are rejected with HTTP 404 (`"No registered account found with this Google email. Please sign up first."`) displayed via a standard error toast.
   - **Register Mode**: Clicking "Sign up with Google" on `/register` fetches the user's verified Google profile and auto-populates their email, first name, last name, avatar, and suggested username, skipping redundant email OTP verification and password creation. The user completes their birthdate, contact number, and address before the account is provisioned.
4. **Environment Configuration**: Encrypted `GOOGLE_CLIENT_ID` in `backend/.env` and `NEXT_PUBLIC_GOOGLE_CLIENT_ID` in `frontend/.env.local` using `@dotenvx/dotenvx`, documented in `.env.example` and `apphosting.yaml`.

#### 4. Files Modified / What Changed
- `backend/app/core/config.py`: Added `GOOGLE_CLIENT_ID` to backend settings.
- `backend/app/schemas/auth.py` & `backend/app/schemas/__init__.py`: Added `GoogleAuthRequest` and `GoogleAuthResponse`.
- `backend/app/services/auth_service.py`: Added `verify_google_token` and `authenticate_or_register_google_user` supporting `login` and `register` modes with Profile and Address provisioning.
- `backend/app/api/v1/endpoints/auth.py`: Added `POST /auth/google` route.
- `backend/tests/test_google_auth.py`: Unit tests verifying audience checks, token verification, and unregistered user rejection.
- `frontend/src/features/auth/api/authClient.ts`: Added `loginWithGoogle` API method.
- `frontend/src/features/auth/hooks/useGoogleAuth.ts`: Created GIS OAuth hook with `signInWithGoogle` and `getGoogleUserProfile`.
- `frontend/src/features/auth/LoginForm.tsx`: Wired "Sign in with Google" button with error toast handling.
- `frontend/src/features/auth/components/RegisterForm.tsx`: Wired "Sign up with Google" auto-fill flow, step validation bypass, and connected Google account badge.
- `frontend/apphosting.yaml` & `backend/.env.example`: Documented Google Client ID.

### [BUG-031] Valhalla Production Route Requests Targeted an Absent Local Container
- **Status**: Resolved in code / Pending Cloud rollout
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Routing / Cloud Run
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The deployed `POST /api/v1/reports/route` request returned HTTP 503 when Valhalla was selected.

#### 2. Root Cause Analysis (RCA)
Cloud Run ran only FastAPI while `VALHALLA_URL` retained the local Docker address `http://localhost:8002`; no Valhalla process exists in that container.

#### 3. Solution & Architectural Strategy
Added a private Cloud Run Valhalla deployment flow backed by versioned Cloud Storage tiles, authenticated FastAPI-to-Valhalla calls, and automatic ORS fallback only for Valhalla availability failures.

#### 4. Files Modified / What Changed
- `infrastructure/valhalla/`: Reproducible artifact build and private-service deployment assets.
- `backend/app/services/routing_service.py`: Provider fallback and response metadata.
- `frontend/src/features/routing/RoutePanel.tsx`: Matching desktop/mobile fallback explanation.

### [BUG-030] Production Fallback Credentials Are Present in the Backend Code Path
- **Status**: Investigating
- **Severity**: Critical
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Backend / Authentication / Cloud Run Configuration
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The Cloud Run image deliberately excludes `backend/.env`, but the backend accepts a source-controlled fallback JWT signing secret when `SECRET_KEY` is missing. Its startup routine can also seed a predictable `admin/admin` account when the roles table is empty. This makes a missing or incorrectly injected Cloud Run secret a critical production security failure.

#### 2. Root Cause Analysis (RCA)
`backend/app/core/config.py` defines a concrete default `SECRET_KEY`, and `backend/app/main.py` creates the default administrator in the lifespan routine. Neither behavior is guarded by a production-environment check. The repository deployment files do not define the Cloud Run `SECRET_KEY` injection, so the codebase cannot verify that the secure runtime setting overrides the fallback.

#### 3. Solution & Architectural Strategy
Provision a unique `SECRET_KEY` as a Cloud Run secret and fail startup outside local development when it is absent. Remove production default-admin seeding; bootstrap an administrator with an explicit one-time deployment command or a securely supplied, rotated credential. Confirm the active Cloud Run revision has the secret before considering the deployment secure.

#### 4. Files Modified / What Changed
- `docs/others/bug-log.md`: Recorded the production credentials investigation and required remediation.
- `backend/app/core/config.py`: Requires environment-aware secret validation.
- `backend/app/main.py`: Requires production-safe administrator bootstrap behavior.

### [BUG-029] Weather Insights Uses a Build-Time Backend Rewrite Without a Build-Time Destination
- **Status**: Investigating
- **Severity**: High
- **Date Reported / Resolved**: September 17, 2026
- **Affected Area**: Frontend / Firebase App Hosting / Production API Routing
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
The weather-insights modal sends its request to the relative URL `/api/v1/weather/insights`, unlike the rest of the production client, which uses `NEXT_PUBLIC_API_URL` to call Cloud Run directly. In Firebase App Hosting, the relative request depends on the Next.js rewrite in `frontend/next.config.ts`. That rewrite can be compiled with its localhost fallback rather than the Cloud Run URL, causing only the **Generate AI Insights** action to fail in production while weather and other direct API calls continue to work.

#### 2. Root Cause Analysis (RCA)
`frontend/next.config.ts` constructs the rewrite destination from `process.env.BACKEND_URL`, with `http://127.0.0.1:8000` as its fallback. `frontend/apphosting.yaml` supplies `BACKEND_URL` only at `RUNTIME`; it does not make the value available during `BUILD`. Next.js resolves rewrite configuration while generating its build artifacts, so the deployment configuration does not guarantee that the production rewrite target is embedded in the build.

#### 3. Solution & Architectural Strategy
Use a single production API-resolution path. The preferred minimal fix is to update `WeatherInsightsModal.tsx` to use `NEXT_PUBLIC_API_URL` (with `/api/v1` as the local fallback), matching the other browser-side calls and avoiding a Next.js proxy hop. Alternatively, add `BUILD` availability to `BACKEND_URL` and retain the rewrite. After either change, run the production build and test the modal request against the deployed Cloud Run endpoint.

#### 4. Files Modified / What Changed
- `docs/others/bug-log.md`: Recorded the investigated production routing issue and remediation options.
- `frontend/src/features/landing/WeatherInsightsModal.tsx`: Requires the API URL resolution correction.
- `frontend/apphosting.yaml`: Requires `BACKEND_URL` build availability only if retaining the rewrite approach.

### [BUG-028] Cloud Run FastAPI Backend CORS Rejection on Firebase App Hosting Domains (*.hosted.app)
- **Status**: Resolved
- **Severity**: Critical
- **Date Reported / Resolved**: September 16, 2026
- **Affected Area**: Backend / Infrastructure / CORS / Firebase App Hosting
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Upon deploying the frontend Next.js application to Firebase App Hosting at `https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app`, opening the site in a browser triggered immediate cascading client-side network failures across all initial API fetches (`/weather/current`, `/weather/forecast`, `/reports/active-zones`, `/public/stats`) and streaming Server-Sent Events endpoints (`/sse/stream`, `/sync/stream`). The browser console logged:
`Access to fetch at 'https://lanes-api-557679867071.asia-east1.run.app/api/v1/...' from origin 'https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`

#### 2. Root Cause Analysis (RCA)
In `backend/app/main.py`, FastAPI's `CORSMiddleware` configured `allow_origin_regex` to match only:
`r"^(https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000|https://.*\.vercel\.app|https://.*\.navlanes\.live)$"`
Firebase App Hosting generates production and preview web domains ending with `.hosted.app`, `.web.app`, or `.firebaseapp.com`. Because none of these domains were included in either `origins` or `allow_origin_regex`, preflight `OPTIONS` and standard cross-origin `GET`/`POST` requests were rejected by Starlette's CORS filter without sending `Access-Control-Allow-Origin`.

#### 3. Solution & Architectural Strategy
Updated `allow_origin_regex` in `backend/app/main.py` to:
`r"^(https?://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):3000|https://.*\.vercel\.app|https://.*\.navlanes\.live|https://.*\.hosted\.app|https://.*\.web\.app|https://.*\.firebaseapp\.com)$"`
This securely permits all valid Firebase App Hosting rollouts and custom Firebase domains while maintaining strict origin sandboxing against arbitrary external domains.

#### 4. Files Modified / What Changed
- `backend/app/main.py`: Updated `allow_origin_regex` in `CORSMiddleware` to include `https://.*\.hosted\.app`, `https://.*\.web\.app`, and `https://.*\.firebaseapp\.com`.

### [BUG-027] Profile "Display Full Name" Setting Ignored in Community Feed and Comment Sections
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 14, 2026
- **Affected Area**: Backend / Frontend / Privacy & Community Feed / PostGIS SQL / REST API
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
In the Profile Settings tab, users can toggle the **"Display Full Name"** preference (`Profile.display_full_name`), which promises to show their real full name on posts and profile instead of their username handle. However, the Community Feed post cards, single-post detail pages, and comment sections continued to strictly display `User.username`. In addition, client-side author checks for post pinning and comment editing compared string values of `author_name === username`, which broke when full names were used.

#### 2. Root Cause Analysis (RCA)
1. In `backend/app/crud/feed.py`, the feed query expressions for `get_feed_posts` and `get_feed_post` hardcoded `func.coalesce(User.username, text("'Unknown'")).label("author_name")` without evaluating `Profile.display_full_name` or concatenating `Profile.first_name` and `Profile.last_name`.
2. In `backend/app/api/v1/endpoints/comments.py`, comment responses hardcoded `c.user.username` for `author_name` instead of inspecting the author's profile privacy preferences.
3. In `frontend/src/features/feed/PostDetailPage.tsx`, author ownership permissions (`isPostAuthor` and `isOwn`) checked `(post as any).author_name === user.username` instead of matching primary keys (`user.id === post.user_id` / `user.id === comment.user_id`).

#### 3. Solution & Architectural Strategy
1. **Server-Side Privacy Resolution (`api-agent` + `security-agent`)**: Added `get_user_display_name(user)` helper in `backend/app/crud/user.py`. In `feed.py`, constructed a SQL `case()` expression that dynamically concatenates `first_name` and `last_name` when `display_full_name` is true (or default) and falls back strictly to `User.username` without exposing personal names to unprivileged queries.
2. **Comment Profile Eager Loading**: Updated `get_comments` to eager-load `joinedload(Comment.user).joinedload(User.profile)` to avoid N+1 queries, returning resolved `author_name` and `author_avatar`.
3. **Primary Key Ownership Verification (`ui-agent`)**: Updated `PostDetailPage.tsx` and `feedApi.ts` to include `user_id` on comment responses and evaluate ownership via numeric user IDs. Added author avatar rendering support to comment cards.

#### 4. Files Modified / What Changed
- `backend/app/crud/user.py`: Added `get_user_display_name` helper function.
- `backend/app/crud/feed.py`: Applied SQL `author_name_expr` conditional expression in `get_feed_posts` and `get_feed_post`.
- `backend/app/api/v1/endpoints/comments.py`: Eager loaded profiles and resolved `author_name` / `author_avatar` in comment builders.
- `backend/app/api/v1/endpoints/posts.py`: Updated post author fallback to use `get_user_display_name`.
- `frontend/src/features/feed/feedApi.ts`: Added `user_id` and `author_avatar` to `CommentResponse`.
- `frontend/src/features/feed/PostDetailPage.tsx`: Fixed `isPostAuthor` and `isOwn` logic to compare user IDs; added comment avatar support.

### [BUG-026] Mobile Layout Inset and Horizontal Margin Overflow in Profile Subtabs
- **Status**: Resolved
- **Severity**: Low
- **Date Reported / Resolved**: September 14, 2026
- **Affected Area**: Frontend / UI / Mobile Responsiveness (PWA)
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On compact mobile screens (e.g., iPhone SE 375px, iPhone 12 390px), the Profile page's Posts and Reports tabs rendered with redundant nested horizontal padding (`px-4 sm:px-0`), creating visible left/right borders and shrinking usable card width.

#### 2. Root Cause Analysis (RCA)
Inner tab containers in `ProfileView.tsx` wrapped post and report item lists in an extra mobile padding block, causing double-margin inset on viewports under 640px.

#### 3. Solution & Architectural Strategy
Removed redundant mobile wrapper padding classes on the Posts and Reports subtab views in `ProfileView.tsx`, enabling seamless full-width card layout on mobile devices while preserving proper responsive gutters on desktop screens.

#### 4. Files Modified / What Changed
- `frontend/src/features/profile/ProfileView.tsx`: Flattened mobile margin hierarchy for profile subtabs.

### [BUG-025] Unauthenticated Navigation Tab Click Diverted to Profile Instead of Current View
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 14, 2026
- **Affected Area**: Frontend / Navigation / Authentication Flow
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When an unauthenticated commuter was exploring the Community Feed (`/feed`) or a specific post (`/feed/[id]`) and clicked the Profile navigation item to sign in, completing authentication always redirected them to `/profile` rather than returning them to the feed context they were browsing.

#### 2. Root Cause Analysis (RCA)
`FloatingNav.tsx` and `MobileNav.tsx` used hardcoded navigation handlers that routed unauthenticated users directly to `/login?redirect=/profile` regardless of their active page.

#### 3. Solution & Architectural Strategy
Updated navigation triggers to check the current `pathname` and preserve the active URL or return path in query parameters, allowing post-login redirection to gracefully return the user to their prior context.

#### 4. Files Modified / What Changed
- `frontend/src/features/navigation/FloatingNav.tsx`: Contextual auth redirect handling.
- `frontend/src/features/navigation/MobileNav.tsx`: Contextual auth redirect handling.

### [BUG-024] Community Sharing Helper Text Contradicted Actual Publication Timing
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Frontend / Backend / Flood Reports / Community Feed
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After a commuter selected **Share in Community Feed**, the submitted flood report appeared in the feed immediately, but the panel said that sharing would occur only after administrator approval. A second legacy publication branch also remained in the approval endpoint.

#### 2. Root Cause Analysis (RCA)
`process_new_report` had already made report submission the publication owner. `FloodReportPanel` retained pre-change wording, while `approve_report` retained an obsolete fallback that duplicated responsibility for the same lifecycle.

#### 3. Solution & Architectural Strategy
Community publication now has one owner: report submission. Map-zone approval remains exclusively responsible for official spatial activation. The helper text explicitly distinguishes immediate public sharing from later map approval.

#### 4. Files Modified / What Changed
- `backend/app/api/v1/endpoints/admin.py`: Removes the obsolete approval-time Community Post creation branch.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: States the immediate feed-publication and separate map-approval behavior.
- `docs/task_plan.md`, `docs/progress.md`, and `docs/others/system-documentation.md`: Synchronize the documented workflow.

### [BUG-023] Flood Polygon Fetch Failure During Route Calculation Due to Property Join
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Backend / Routing / Flood Avoidance / PostGIS / Valhalla / ORS
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
During route calculation (`POST /api/v1/reports/route` / `calculate_flood_safe_route`), the backend logged a database warning:
`Warning: Failed to fetch flood polygons ((psycopg.ProgrammingError) cannot adapt type 'property' using placeholder '%s' (format: AUTO) [SQL: SELECT ST_AsGeoJSON(flood_avoidance_zones.geometry) AS geojson, flood_reports.severity AS flood_reports_severity FROM flood_avoidance_zones JOIN flood_reports ON flood_reports.id = %(id_1)s::INTEGER ...]). Bypassing flood avoidance.`
As a result of this database error, active flood avoidance polygons failed to load, causing route calculations to bypass flood detour zones.

#### 2. Root Cause Analysis (RCA)
Following the 1:N spatial deduplication schema migration, `FloodAvoidanceZone` no longer has a physical `report_id` database column; instead, `report_id` was implemented as a Python `@property` dynamically resolving to the primary report's ID (`self.primary_report.id`), while the foreign key moved to `flood_reports.zone_id`.
In `backend/app/services/valhalla_service.py` and `backend/app/services/ors_service.py`, `get_active_flood_polygons` attempted an SQL join:
`models.FloodAvoidanceZone.report_id == models.FloodReport.id`.
SQLAlchemy evaluated `models.FloodAvoidanceZone.report_id` as the Python `property` descriptor object rather than an ORM Column / InstrumentedAttribute, passing `<property object>` as parameter `%(id_1)s` to psycopg and throwing a `psycopg.ProgrammingError`.
Furthermore, performing an inner join against `flood_reports` would drop admin-curated avoidance zones with no direct report and duplicate multi-report zones.

#### 3. Solution & Architectural Strategy
Refactored `get_active_flood_polygons` in both `valhalla_service.py` and `ors_service.py` to query `FloodAvoidanceZone` and its PostGIS GeoJSON geometry directly without an inner join.
Zone severities are evaluated using the model's authoritative `.severity` property, which correctly respects administrator severity overrides, prioritizes the highest severity across merged reports, and falls back to default values for standalone curated zones.

#### 4. Files Modified / What Changed
- `backend/app/services/valhalla_service.py`: Replaced the invalid SQL join with a direct `FloodAvoidanceZone` geometry query and `.severity` property classification.
- `backend/app/services/ors_service.py`: Synchronized `get_active_flood_polygons` to query `FloodAvoidanceZone` directly and use `.severity`.
- `docs/others/bug-log.md`: Documented root cause analysis and resolution for BUG-023.

---

### [BUG-022] Registration Success Was Shown Twice on Login
- **Status**: Resolved
- **Severity**: Low
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Frontend / Authentication
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After a successful registration, the Login page showed both the global **Account Created** toast and an identical green success banner above the credentials fields.

#### 2. Root Cause Analysis (RCA)
`RegisterForm` displays the toast before redirecting to `/login?registered=true`; `LoginForm` also rendered a static banner from the same query parameter.

#### 3. Solution & Architectural Strategy
The static Login banner was removed. The redirect keeps the `registered=true` compatibility parameter, while the single global toast remains the registration confirmation.

#### 4. Files Modified / What Changed
- `frontend/src/features/auth/LoginForm.tsx`: Removes only the duplicate post-registration banner.

### [BUG-021] Edit Zone Reopened Without an Actual Edit and Could Not Change Geometry
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 13, 2026
- **Affected Area**: Frontend / Backend / Admin Map / IndexedDB Drafts / PostGIS
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Opening an active zone wrote a local copy of its unchanged server values. On a later sign-in, that copy opened the amber Edit Zone workspace and displayed **Edit Restored** despite no work having been started. Edit Zone also exposed no Spatial Geometry section, preventing an administrator from correcting an active road centreline or saved area boundary.

#### 2. Root Cause Analysis (RCA)
The edit-draft lifecycle treated every saved IndexedDB record as meaningful and had no comparison to the fetched server version. The secured update request accepted only metadata overrides, even though Create Zone already supported routed lines and Terra Draw area geometry.

#### 3. Solution & Architectural Strategy
Edit drafts now use a versioned snapshot of the exact fetched baseline, then compare normalized editable values and selected media against that snapshot. This prevents the previous polygon-versus-source-line mismatch from classifying an untouched legacy record as an edit; incompatible v1 records are removed silently. An inactive Create Zone workspace is also barred from reading or saving shared MapContext anchors while Edit Zone is active, preventing it from creating a false Create draft. Only a genuine change resumes the edit workspace and produces the restore toast. Edit Zone now shares Create Zone's Line, Polygon, Freehand, Rectangle, and Circle controls. Road replacements preserve a source centreline and regenerate the existing 25-metre avoidance polygon; area replacements persist their exact edited polygon and remove obsolete road source geometry. Existing areas reopen as editable polygons because the database intentionally stores the final polygon, not a drawing-tool label.

**Follow-up data mapping repair:** Edit Zone now uses its effective zone response values—administrator override when present, otherwise the linked public report’s severity, depth, survey, and description. Original report media is returned separately as read-only evidence, so it remains preserved and cannot be confused with newly uploaded zone media.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/components/zones/zoneEditDraftStorage.ts`: Adds normalized edit-baseline comparison helpers.
- `frontend/src/features/admin/LiveMapPage.tsx`: Validates an edit draft against the freshly fetched zone before opening Pane 2.
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx` and `hooks/useTerraDraw.ts`: Adds editable geometry controls and Terra Draw vertex selection to Edit Zone.
- `frontend/src/features/admin/adminApi.ts`, `backend/app/schemas/report.py`, and `backend/app/api/v1/endpoints/admin.py`: Accept and securely persist supported edit geometry without a migration.
- `backend/tests/test_zone_edit_geometry_schema.py`: Covers line and polygon update payload validation.

### [BUG-020] Landing Flood Analytics Action Opened a Separate Page Instead of the Map Panel
- **Status**: Resolved
- **Severity**: Low
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Landing Page / Map Analytics
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Selecting **View Flood Analytics** from the landing page opened `/analytics` rather than the commuter map with Flood Insights visible.

#### 2. Root Cause Analysis (RCA)
The landing action used the standalone analytics route, while the map's URL-driven panel contract handled only the `saveplace` panel value.

#### 3. Solution & Architectural Strategy
The action now navigates to `/map?panel=analytics`. `MapContext` recognizes that panel value and opens the existing Flood Insights panel through its standard state setter, preserving map-panel layout, stacking, and responsive behavior.

#### 4. Files Modified / What Changed
- `frontend/src/features/landing/LandingView.tsx`: Routes the action to the map with the analytics panel signal.
- `frontend/src/features/map/MapContext.tsx`: Opens Flood Insights for `panel=analytics`.
- `docs/others/system-documentation.md`, `docs/task_plan.md`, `docs/progress.md`: Records the corrected landing-to-map flow.

---

### [BUG-019] Primary Map Tabs Must Fly Only to Currently Selected Items
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Admin Map / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After an administrator selected a Pending Report or Active Zone and then toggled its card or map feature off, the map still flew back to that item after returning to its primary tab.

#### 2. Root Cause Analysis (RCA)
The first repair added separate last-target IDs. That made deselected items continue to qualify for tab-switch navigation even though they were no longer selected.

#### 3. Solution & Architectural Strategy
Pending and Active selections remain independent, but tab-switch navigation now reads only `selectedReportId` or `selectedZoneId`. A selected item flies into view when its tab is reopened; toggling that same card or map feature off sets its selection to `null`, so the next tab switch leaves the map unchanged.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Restores a tab's currently selected item on return and prevents deselected items from triggering map movement.
- `docs/others/system-documentation.md`, `docs/task_plan.md`, `docs/progress.md`: Records the independent per-tab fly-to memory.

---

### [BUG-018] Secondary Workspace Tabs Used a Fixed Order and Did Not Close
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Admin Map / Spatial Operations
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On `/admin/map`, the secondary drawer handles always followed a hard-coded Create → Edit → Merge sequence. A Merge or Edit workspace could remain as a collapsed handle after its Close action, so the visible stack did not reflect opened workspaces or the most recently opened one.

#### 2. Root Cause Analysis (RCA)
Each drawer render path positioned its handles with fixed offsets. Close handlers only hid a drawer in some paths, retaining the Merge report or Edit zone session that caused a stale placeholder to remain. Inactive workspace components were also unmounted, losing in-progress view state when switching tabs.

#### 3. Solution & Architectural Strategy
`LiveMapPage` now maintains a shared most-recent-first Merge/Edit workspace order. Create Zone stays permanently first; only sessions the administrator opened are rendered, and reopening Merge or Edit moves it directly below Create Zone. Switching keeps the workspace component mounted so its in-progress state and scroll position remain available. Explicit Close clears the matching session and its ordering entry. The Edit drawer has the same visible Close control on desktop and mobile; its existing discard confirmation continues to protect unsaved edits.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Adds recency-based workspace ordering, preserves inactive workspace mounts, and clears Merge/Edit sessions on close.
- `frontend/src/features/admin/components/merge/MergeWorkspacePanel.tsx`: Keeps an inactive opened Merge workspace mounted until it is explicitly closed.
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx`: Keeps inactive zone workspaces mounted and exposes the Edit Close control at every viewport size.
- `docs/others/system-documentation.md`, `docs/task_plan.md`, `docs/progress.md`: Records the corrected workspace-tab behavior.

---

### [BUG-017] Flood Report Saved Accidental UI-Only Drafts
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Flood Report Panel / IndexedDB Drafts
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
An accidental severity selection could be saved and restored as a Flood Report draft. The panel’s `Clear locations` action also left survey answers, media, sharing state, preview geometry, queued reports, and other report values behind.

#### 2. Root Cause Analysis (RCA)
Draft eligibility accepted any populated field, while the clear control only reset location inputs. UI-only values and incomplete interactions therefore looked like recoverable report work.

#### 3. Solution & Architectural Strategy
Draft eligibility now requires at least one selected road endpoint plus substantive report content (severity, survey answer, description, or media); queued reports remain recoverable. Two-way coverage, sharing, wizard state, survey visibility, and unselected location text cannot create a draft. Severity tiles now toggle off. **Clear** presents a compact, no-wrap choice row: neutral **Clear all** followed by the rightmost red **Clear this page**, which preserves work on the other report page.

#### 4. Files Modified / What Changed
- `frontend/src/features/hazards/floodReportDraftStorage.ts`: Separates meaningful draft eligibility from any local panel state.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Adds toggleable severity and scoped/full Clear handlers.
- `frontend/src/shared/ui/feedback/ConfirmDialog.tsx`: Supports the compact optional third action used by the Flood Report Clear dialog.
- `docs/others/bug-log.md`, `docs/task_plan.md`, `docs/progress.md`, `docs/others/system-documentation.md`: Records the corrected Flood Report draft contract.

---

### [BUG-016] Empty Flood Report Draft Triggered a False Restore Message
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Flood Report Panel / IndexedDB Drafts
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
After sign-in, Flood Report could display “Draft Restored” even though the report panel contained no locations, severity, text, media, or queued report.

#### 2. Root Cause Analysis (RCA)
Flood Report persisted every hydrated form state, including an entirely empty active form. On startup it treated the presence of any account-private IndexedDB record as a successful draft restore and showed the toast without checking whether it contained report work.

#### 3. Solution & Architectural Strategy
A shared meaningful-draft check now gates both persistence and restoration. Empty records are deleted silently, never produce a restore message, and are not re-saved. The follow-up eligibility refinement in BUG-017 requires a selected road endpoint plus substantive report content for an active form, while queued reports remain recoverable.

#### 4. Files Modified / What Changed
- `frontend/src/features/hazards/floodReportDraftStorage.ts`: Adds the shared meaningful Flood Report draft classifier.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Removes empty persisted records before restore and deletes rather than saves an empty active form.

---

### [BUG-015] Feed Create Post Draft Lost Media Attachments and Location on Refresh
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Frontend / Community Feed / Post Composer
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
When composing a community post in `CreatePostModal` on `/feed`, attaching media (images or videos) and selecting a location tag/coordinates were held purely in volatile React state. Refreshing or reloading the page discarded the attached files and selected location. Furthermore, previously restored files were prematurely cleared from IndexedDB upon initial restore.

#### 2. Root Cause Analysis (RCA)
1. Media files in `selectedFiles` and location coordinates were only saved to storage on explicit button navigation actions ("Choose on Map" or clicking 'X' and choosing "Save Draft"), rather than continuously synchronizing state changes.
2. `CreatePostModal` called `del('lanes_draft_files')` immediately when loading files into React state on mount, erasing the persistent IndexedDB record. Subsequent browser refreshes therefore found no stored files.
3. `FeedPage` initialized `isCreateModalOpen` to `false` without checking whether a draft session was active before the page reload.

#### 3. Solution & Architectural Strategy
1. **Continuous Draft Synchronization**: Added reactive synchronization effects that automatically persist text content, location tags, and coordinates to `localStorage` (with `sessionStorage` fallback) and attached `File[]` objects to IndexedDB via `idb-keyval`.
2. **Preserve Draft Until Terminal Action**: Removed premature deletion on mount. Draft storage is now only cleared when the user successfully publishes a post (`createMutation.onSuccess`) or explicitly clicks **"Discard Post"**.
3. **Session Restoration on Refresh**: `FeedPage` checks for an active composing session on mount and restores the open modal state alongside the draft content, location tag/coordinates, and all attached media files (re-generating object preview URLs).

#### 4. Files Modified / What Changed
- `frontend/src/features/feed/CreatePostModal.tsx`: Implements continuous auto-save for content, location, and IndexedDB media files, eliminates premature IndexedDB deletion, merges `initialFiles` on mount, and ensures clean draft disposal on post or discard.
- `frontend/src/features/feed/FeedPage.tsx`: Restores composer modal state if user reloads while composing, and syncs modal closure to draft storage.
- `docs/others/bug-log.md`: Documents BUG-015 root causes and resolution.

---

### [BUG-014] Edit Zone Replaced the Create Zone Workspace Bookmark
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Admin Map / Spatial Operations Workspace
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
On `/admin/map`, selecting **Edit** from Active Zones passed the selected zone into the same secondary drawer state used by Create Zone. The lone blue Create Zone bookmark therefore changed into an amber Edit Zone bookmark, leaving the unfinished Create workspace inaccessible and making the control appear permanently renamed.

#### 2. Root Cause Analysis (RCA)
`LiveMapPage.tsx` represented both actions with `isCreateZoneDrawerOpen` and a mutable `editingZone`. The drawer title, color, form mode, and bookmark were all derived from that one state pair. This conflated two independent admin sessions even though `OfficialZoneDrawer` already supports separate create and per-zone edit draft persistence.

#### 3. Solution & Architectural Strategy
Create and Edit now have independent visibility sessions. Create keeps its blue bookmark and account-private draft; Edit keeps its selected zone and amber bookmark. Only one Pane 2 drawer is visible at once, while switching preserves the other workspace through the existing IndexedDB draft mechanism. Merge Review remains an independent third session. Desktop bookmarks now use non-overlapping stacked offsets: Create, Edit, then Merge. Mobile exposes Create from Active Zones and provides a workspace switch action in the shared drawer header.

#### 4. Files Modified / What Changed
- `frontend/src/features/admin/LiveMapPage.tsx`: Separates Create/Edit drawer state, preserves sessions while switching, and renders distinct blue, amber, and merge bookmarks.
- `frontend/src/features/admin/components/CreateOfficialZonePanel.tsx`: Forwards optional mobile workspace-switch controls to the shared drawer.
- `frontend/src/features/admin/components/zones/OfficialZoneDrawer.tsx`: Adds the mobile-only workspace switch action without duplicating the form or changing APIs.
- `frontend/src/features/admin/components/ActiveZonesPanel.tsx`: Exposes a mobile Create Zone entry point.

---

### [BUG-013] Mixed Road Topology Was Classified as One Whole Route
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Flood Report / Decision #16 Carriageway Detection
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
A report spanning Caruncho Avenue and Urbano Velasco Avenue showed only one orange line, or previously could produce a misleading counterpart, because its Start/End range crossed one-way and two-way map sections. The valid opposite carriageway exists only for the appropriate Urbano Velasco run.

#### 2. Root Cause Analysis (RCA)
The service evaluated the entire Valhalla route as one unit and chose its dominant traversability. For the reproduced coordinates, Valhalla edges identify Caruncho as one-way, Urbano Velasco as one-way, then Urbano Velasco as two-way. One whole-route counterpart search cannot represent that topology safely.

#### 3. Solution & Architectural Strategy
The trace request now includes Valhalla edge `begin_shape_index` and `end_shape_index`. The service splits the snapped route whenever road identity or traversability changes, classifies each run independently, and searches for an opposite carriageway only for eligible runs. Before validation, a map-matched candidate is reduced to its longest contiguous component that is actually parallel and laterally separated from the selected run. A short terminal transition is restored only when the graph-mapped geometry reaches the matching endpoint of that original road run, which represents a genuine Y merge; unrelated cross-street or detached connectors remain removed. For split routes only, the valid component can cover 50%+ of the run with a 3.5m lateral tolerance for six-decimal polyline rounding. The final preview keeps the original full line and adds only the verified counterpart section.

#### 4. Files Modified / What Changed
- `backend/app/services/carriageway_service.py`: Requests edge shape indexes, applies per-run carriageway classification, and retains only endpoint-attached graph-mapped Y transitions from otherwise trimmed counterparts.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Renders the original and verified counterpart through independent MapLibre sources/layers so a short nearby line cannot be lost when the map style reloads.
- `backend/tests/test_carriageway_service.py`: Covers road-identity/traversability splits, connector removal, and the mixed-run partial-counterpart threshold.
- `docs/decisions.md`: Updates Decision #16 to prohibit dominant whole-route topology classification and scopes the partial-run tolerance.

---

### [BUG-012] Feed View-on-Map Pulse Was Offset from Road Coverage
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 12, 2026
- **Affected Area**: Community Feed / Map Focus Indicator
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
Clicking a Flood Report location or **View on Map** in the Community Feed opened `/map`, but the temporary red pulsing circle could sit above or beside the reported road. Curved segments and two-carriageway reports made the misalignment especially visible.

#### 2. Root Cause Analysis (RCA)
`PostItem.tsx` reduced every road geometry to the midpoint of its bounding box. That mathematical point is often off a curved line and does not correctly represent paired carriageways. The `fly-to-location` MapLibre marker also used the default bottom anchor, which placed the visual pulse above its supplied geographic coordinate.

#### 3. Solution & Architectural Strategy
The shared map geometry utility now finds a LineString's midpoint by travelled road distance. For a `MultiLineString`, it calculates each carriageway's travelled-distance midpoint and uses their length-weighted average, producing the expected center between paired directions. The Feed shares that utility for both map entry points, and the pulse marker uses a center anchor so the animation's visual center exactly matches the fly-to coordinate.

#### 4. Files Modified / What Changed
- `frontend/src/features/map/mapGeoUtils.ts`: Added road-length and dual-carriageway coverage midpoint calculation.
- `frontend/src/features/feed/PostItem.tsx`: Replaced its duplicate bounding-box midpoint logic with the shared utility.
- `frontend/src/features/feed/feedApi.ts`: Recognizes `MultiLineString` report geometry from the API.
- `frontend/src/features/map/MapCanvas.tsx`: Center-anchors `fly-to-location` pulse markers.

---

### [BUG-011] Public Road Preview Saved Raw Sidewalk Connectors
- **Status**: Resolved
- **Severity**: High
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Public Flood Report / Routing / Pending Reports
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
An orange public road preview could look acceptable beneath its Start/End pins, but the same pending report later appeared to extend toward a sidewalk or nearby building in the admin map. The severity aura exposed geometry that was not actually on the road.

#### 2. Root Cause Analysis (RCA)
The authoritative route service first found a valid Valhalla-snapped road line, then prepended and appended the user's raw clicked coordinates to make the dashed preview visibly meet the pins. For ordinary reports, that combined line was stored directly. For bidirectional reports, the frontend submitted only the original line and persistence independently rebuilt coverage, allowing the public preview and stored geometry to drift.

#### 3. Solution & Architectural Strategy
Raw clicks are now input anchors only. The preview service returns only the snapped road line, and public markers move to its endpoints after verification. Flood Report submits the full validated dual coverage when available; the backend still rebuilds every submitted road segment before storage, using the first validated road line for authoritative classification. Pending Reports continues to render stored geometry directly, which is now road-only for newly created reports.

#### 4. Files Modified / What Changed
- `backend/app/services/carriageway_service.py`: Removed raw-anchor connector vertices from authoritative preview output.
- `backend/app/services/report_service.py`: Rebuilds both single and bidirectional submitted road geometry before persistence.
- `frontend/src/features/hazards/FloodReportPanel.tsx`: Submits validated `MultiLineString` coverage when an opposite carriageway was confirmed.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Places visible public Start/End markers on the validated road endpoints.
- `backend/tests/test_carriageway_service.py`: Replaced connector expectations with road-only preview and persistence regression coverage.

---

### [BUG-010] Pending Report Aura Extends Beyond Validated Road Endpoints
- **Status**: Resolved
- **Severity**: Medium
- **Date Reported / Resolved**: September 11, 2026
- **Affected Area**: Admin Map / Pending Reports
- **Author / Resolver**: [@roicambe](https://github.com/roicambe) (Roi Cambe)

#### 1. Problem Description
At street level, pending public flood reports could appear to spill from the correctly aligned road into adjacent buildings or lots. The problem was most visible at either end of a report segment as a large transparent severity-colored bulb, giving the impression that the report geometry was not aligned with the map.

#### 2. Root Cause Analysis (RCA)
The pending layer correctly rendered the persisted validated report geometry without recalculating a route. However, its 24px aura (32px when selected) used MapLibre's `round` line cap. A round cap extends past each geometry endpoint by half the line width, so the visual aura exceeded the saved road segment even though its coordinates were correct.

The initial layout correction applied only when the custom MapLibre layer was first created. Because the global map instance survives panel navigation and development Fast Refresh, an already-created layer could retain its old `round` cap while its GeoJSON source refreshed normally. This made the fixed code appear ineffective for current reports.

#### 3. Solution & Architectural Strategy
The geometry-source repair in BUG-011 removes the actual off-road connector cause. Pending Reports intentionally use MapLibre `round` caps and rounded joins again, matching the rounded endpoint treatment of Active Zones and the public orange preview. The hook reapplies this layout to existing live layers after navigation or Fast Refresh. Approved-zone rendering remains unchanged, using its server-created transparent buffer with a dark road core.

#### 4. Files Modified / What Changed
- `frontend/src/features/map/hooks/usePendingReportsLayer.ts`: Restored intentional rounded endpoint caps and rounded joins for the pending road aura, and synchronizes that layout on existing live layers.

---

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

A further UX regression briefly drew a raw straight orange connector between the selected pins during verification, then replaced it with the mapped road shape. This made the preview look broken before the final result was ready.

#### 2. Root Cause Analysis (RCA)
`MapContext.tsx` first requested an ordinary traffic-law-aware route and passed that complete result into Decision #16. When anchor direction conflicted with mapped traffic flow, Valhalla legally detoured around neighboring roads. The carriageway service then used raw edge counts, searched only the left side, and accepted name similarity without proving distinct OSM way identity, lateral separation, overlap, or comparable length. A snap back onto the original road could therefore be labeled `DIVIDED_CARRIAGEWAY`.

The hardened service correctly limited endpoint snaps to 35 metres, but returned the snapped polyline unchanged. Because markers intentionally remained at the user’s raw anchors, accepted snap distance appeared as a gap between the marker and dashed coverage.

The remaining post-loading symptom was a MapLibre rendering artifact: changing from the temporary two-point line to the longer verified polyline recalculated `line-dasharray` phase. The endpoint could fall inside the pattern’s transparent interval, visually hiding the final portion despite correct geometry.

`MapContext.tsx` explicitly placed that temporary two-point geometry in shared preview state as soon as both anchors existed. The loading overlay covered the panel but not the map, so users could see an unverified straight route before Valhalla completed.

#### 3. Solution & Architectural Strategy
The backend now owns road-preview generation from raw anchors, evaluates both directions, rejects excessive detours, and uses length-weighted topology classification. Divided-road searches probe both sides and require road identity/class, distinct way IDs, opposing direction, parallelism, comparable length, longitudinal overlap, safe separation, and no loop. Narrow two-way roads intentionally render one mapped centerline. Ambiguous or unavailable graph data returns one conservative line with an explanation.

For a route that already passes endpoint-snap and loop validation, the backend now selects the candidate with the best combined endpoint fidelity and retains its snapped road vertices while adding short connectors to the exact Start and End anchors. Preview and persisted operational geometry therefore agree and visually meet both pins.

The shared preview hook additionally renders solid orange terminal caps for first/last segments no longer than 40 metres. These caps sit above the dashed layer and below the existing markers, while the road body remains dashed on both mobile and desktop maps.

Shared preview state is now cleared while an authoritative request is in flight. The Start and End pins remain visible with the loading overlay, and the orange route is rendered only after the service returns its final validated or conservative fallback geometry. API failures leave the map clear and keep the existing panel error feedback.

The earlier raw-anchor connector and solid terminal-cap workaround is superseded by BUG-011: raw clicks are no longer geometry vertices, and pins move to the verified road endpoints instead.

#### 4. Files Modified / What Changed
- `backend/app/services/carriageway_service.py`: Added authoritative segment selection, conservative classification, two-sided probing, strict candidate validation, endpoint-fidelity ranking, and exact pin connectors.
- `backend/app/services/report_service.py`: Repeats raw-anchor validation before persistence so client geometry cannot create an unverified `MultiLineString`.
- `backend/app/api/v1/endpoints/routes.py`: Expanded the backward-compatible preview contract for raw anchors, coverage geometry, validation status, and explanation.
- `frontend/src/features/map/MapContext.tsx`: Removed the general-route preview chain and centralized shared preview status and geometry.
- `frontend/src/features/map/MapContext.tsx`: Removed the temporary raw straight-line fallback during loading so shared public/admin maps never animate from an unverified connector to the final road shape.
- `frontend/src/features/map/hooks/useFloodMapPreview.ts`: Initially added terminal-cap rendering; BUG-011 removed that workaround in favor of a single road-only dashed geometry and snapped visible pins.
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
