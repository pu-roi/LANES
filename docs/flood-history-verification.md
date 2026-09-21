# Flood History & Analytics Verification Guide

> **Last Updated:** September 21, 2026, 3:20 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This guide is the Phase 33.7 release script for the protected Flood History & Analytics workspace. Run it with a staff account and a disposable, non-production verification dataset.

## Automated checks

- Backend lifecycle, aggregation, rejection-reason, privacy-safe export, and authorization checks are in `backend/tests/test_flood_event_service.py`, `backend/tests/test_spatial_archive.py`, and `backend/tests/test_flood_history_authorization.py`.
- Frontend smoke coverage is in `frontend/tests/flood-history.spec.ts`. It covers the analytics view, protected records filters, and the mobile list/map switcher without committing staff credentials.

To run the frontend tests, start the frontend and API with a staff test account, install Chromium once with `npm exec playwright install chromium`, save an authenticated browser state outside version control, then set `PLAYWRIGHT_STORAGE_STATE` to that file and run `npm run test:e2e` from `frontend`. `PLAYWRIGHT_BASE_URL` defaults to `http://127.0.0.1:3000` and may target an approved staging environment instead.

## Manual release script

1. Sign in as a Commuter and request `/admin/flood-history`, `/api/v1/admin/flood-events/history`, `/analytics`, `/export`, and a guessed `/history-detail` ID. Each request must be denied; no event, report, or export data may render.
2. As staff, open Moderation Center, select a pending flood report, and use the rejection modal. Check that each structured reason is selectable, that **Other** requires an internal note, and that the rejected report stays in staff moderation history rather than Archive Center or the public map.
3. Approve one pending report as a new zone, then inspect Spatial Operations. Confirm the wording identifies a new verified Flood Event and the new live routing zone. Approve a corroborating pending report by linking/merging it to that active event-enabled zone; it must become supporting evidence without creating a second Flood Event.
4. From Flood History & Analytics, open **Flood Event Records**. Verify status, severity, date, barangay, road, place, and multiple-location filters refresh both the list and historical map together. Select a list row, then a map footprint, and verify the same event is highlighted and focused.
5. Open **View event** for a record. Confirm the modal shows the readable event timeline and its linked reports. The report **View** action must open the authorized evidence detail, not expose it in the aggregate dashboard or exports.
6. Deactivate an event's final active zone. Confirm the event is ended, remains in Flood History & Analytics, and does not appear as an ordinary Archive Center record. Create a genuinely new verified zone afterwards and confirm it starts a distinct event.
7. In Overview & Analytics, compare each chart/filter result with the record list. Event totals, recurrence, severity, durations, and timing must count Flood Events once; approved report volume must remain a labelled, separate confidence signal. Download all four CSV/JSON export options and confirm they omit reporter identity, raw report text, exact report geometry, and media URLs.
8. Review desktop at 1440px and mobile at 390px. On mobile, switch explicitly between **List** and **Map**, ensure controls remain usable without horizontal clipping, and confirm bottom controls clear the PWA safe area.

## Security and privacy review record

The Phase 33 routes were reviewed statically on September 21, 2026:

- History, analytics, export, and evidence-detail routes each require `get_current_active_admin`; the authorization test also verifies a guessed event ID is denied before record lookup.
- Aggregation and export operate from Flood Events. `serialize_flood_event_planning_records` produces only safe event-level planning fields, while approved report counts remain an explicitly separate measure.
- Detailed reports are intentionally available only from the protected event-detail route. They are not returned by analytics, records exports, or the public map.
- CSV export prefixes spreadsheet-formula characters, and the client presents error states/toasts for failed analytics and exports.
- No Phase 33.7 schema change was made. The migration baseline is validated through the deployment migration workflow; future schema changes must again run `alembic upgrade head` against PostgreSQL/PostGIS before rollout.
