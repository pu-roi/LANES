# LANES Bug Fix Log & Issue Tracker

> **Last Updated:** September 16, 2026, 10:15 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)


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
