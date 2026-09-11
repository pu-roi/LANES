# LANES Bug Fix Log & Issue Tracker

> **Last Updated:** September 11, 2026, 2:58 PM

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
