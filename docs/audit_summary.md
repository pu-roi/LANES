# LANES Codebase Audit Summary

*Date: 2026-07-30*
*Auditors: `api-agent`, `security-agent`, `ui-agent`*

This document serves as a permanent record of the comprehensive codebase audit conducted across the LANES repository.

## Phase 1: Backend Audit

### `backend/app/core/config.py`
- 🔴 **SECURITY VIOLATION**: `DATABASE_URL` is hardcoded with credentials (`postgresql+psycopg://postgres:postgres@localhost:5432/lanes`). It should use `os.getenv` or rely purely on `.env` parsing without a hardcoded default.
- 🔴 **SECURITY VIOLATION**: `SECRET_KEY` is hardcoded. If this is checked into version control, it is a critical vulnerability.
### `backend/app/api/v1/endpoints/reports.py`
- 🔴 **SWALLOWED ERRORS**: `read_reports` and `read_active_avoidance_zones` use `try/except` blocks that just `print` the error and return `[]`. This violates the rule to surface errors to the UI (should raise HTTPException 500/503).
- 🔴 **CRITICAL AUTHORIZATION / IDOR**: `create_avoidance_zone` does not require `Depends(get_current_user)` or any role checking. Any unauthenticated user could spam or create fake routing barriers.
### `backend/app/api/v1/endpoints/admin.py`
- 🟢 **SECURE**: All 14 endpoints strictly require `Depends(deps.get_current_active_admin)`. Audit logging is consistently implemented for mutation actions (approve, reject, deactivate, delete user). No IDOR vulnerabilities found.

### `backend/app/models/` & `backend/app/schemas/`
- 🟢 **ARCHITECTURE**: `report.py` correctly implements 3NF database normalization, splitting locations and surveys into their own tables. PostGIS geometry is correctly typed using SRID 4326.
- 🔴 **SWALLOWED ERRORS**: In `schemas/report.py`, the `@field_validator("geometry")` catches EWKB parsing exceptions and silently returns `None`. If the PostGIS data is corrupt, the frontend will just silently receive no map coordinates instead of a 500 error.

### `backend/app/services/routing.py`
- 🔴 **SWALLOWED ERRORS**: `calculate_flood_safe_route` catches DB errors on `get_active_flood_polygons`, prints a warning, and returns empty arrays. This silently bypasses flood avoidance logic. It could route a user into a flood if the database fails, rather than raising a 503 error to safely abort the route calculation.


## Phase 2: Frontend Audit

### `frontend/src/`

- 🔴 **SWALLOWED ERRORS (Frontend)**: Found 15 instances in `src/features/` where API errors are silently swallowed with `console.error(err)` instead of updating UI state or firing a toast notification (e.g., in `HomeStats.tsx`, `ForecastChart.tsx`, and `RegisterForm.tsx`). This violates the UI-Agent mandate.
- 🟢 **STYLING & ROUTING**: Confirmed Tailwind CSS is strictly used. App Router configuration is standard. No direct database queries found in the frontend bundle.
- 🟡 **PWA CONFIGURATION**: `next-pwa` is configured in `next.config.ts`, but a custom `sw.js` (service worker) is missing from the `public/` directory for full offline support, which aligns with the pending `TODO.md` task.
