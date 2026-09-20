# Flood Event History — Lifecycle and Migration Design

> **Status:** Proposed for developer approval — September 20, 2026
> **Scope:** Capstone Phase 33.1. This is a design and lifecycle-audit artifact only; it does not authorize or include model, migration, endpoint, or UI changes.

---

## 1. Purpose

LANES must retain verified flooding as durable city-planning history without letting historical data affect active routing. The proposed **Flood Event** is therefore the permanent verified incident record. `FloodAvoidanceZone` remains a temporary, editable operational routing barrier, while original `FloodReport` records remain their own evidence.

This design preserves the Phase 33 decisions in `docs/task_plan.md`: one event may have many zones, reports, roads, and barangays; related reports are corroborating evidence rather than duplicate events; and rejected reports are staff moderation records, not archive records or historical events.

## 2. Current-State Lifecycle Audit

| Current path | Existing behavior | Phase 33 gap |
|---|---|---|
| Reject report | `update_flood_report_status(..., "rejected")` sets both `status = rejected` and `deleted_at`, then applies the reporter trust penalty. | Rejection is incorrectly conflated with soft deletion and Archive Center recovery. |
| Restore rejected report | Restoring clears `deleted_at`, changes the report back to `pending`, and reverses the penalty. | It erases the moderation outcome instead of retaining a structured decision history. |
| Report archive | `archive_flood_report` independently sets `deleted_at`. | Genuine deletion/recovery must remain distinct from moderation rejection. |
| Approve/create zone | Creating a zone marks its source report approved and attaches it through `FloodReport.zone_id`. | No permanent incident is created. |
| Merge into zone | Pending reports are approved and attached to an existing zone through `zone_id`. | Corroborating reports have no common historical-event identity. |
| Direct official zone | An administrator can create a zone without a report. | A trusted official operational decision currently leaves no durable event record. |
| Deactivate zone | Deactivation only sets `is_active = false`; Archive Center treats inactive/expired zones as archived. | No verified event end, duration, or preserved historical record exists. |
| Expire zone | Active routing queries omit zones once `expires_at <= now`; no lifecycle write occurs. | An event could disappear operationally without a recorded end timestamp. |
| Restore/hard-delete zone | Restore reactivates the zone; hard delete detaches linked reports. | Linked historical evidence could be broken or silently reinterpreted. |

The affected implementation areas are `backend/app/models/report.py`, `backend/app/crud/report.py`, `backend/app/api/v1/endpoints/admin.py`, and the Admin Archive Center. All current admin write endpoints already use the active-admin dependency; Phase 33 must preserve that protection for every historical read, export, and transition.

## 3. Target Lifecycle Contract

```text
Pending Flood Report
  ├─ Reject with structured reason ──> Internal moderation history only
  └─ Approve / link as evidence ────> Verified Flood Event ──> one or more live zones

Direct official admin zone ─────────> Verified Flood Event ──> live zone

Final live zone ends (manual or expiry service)
  └─> Flood Event becomes ended and remains in admin history/analytics
```

### Invariants

- An event is created in the same transaction as its first official zone, whether the source is a report or a direct DRRMO action.
- A supporting report belongs to at most one Flood Event. It may remain associated with the event even if its current operational zone changes.
- A zone belongs to exactly one Flood Event for its lifetime. A later recurrence creates a new event and new zone; closed events are never reopened.
- Ending one zone ends its event only when that event has no other active, unexpired zones.
- Expiry must run through the same server-side end service as manual deactivation. A GET/read query must never quietly mutate lifecycle state.
- Rejected reports do not receive an event link, do not appear in event analytics, and retain their moderation outcome for authorized staff.
- A linked event prevents hard deletion of its source evidence/zone unless a future, explicitly governed retention workflow is approved.

## 4. Proposed 3NF Data Design

### `flood_events`

One row per verified incident.

| Field | Notes |
|---|---|
| `id` | Integer primary key, consistent with the existing schema. |
| `status` | `active` or `ended`; indexed. |
| `first_reported_at` | Earliest linked report time; nullable for a direct official zone with no reports. |
| `verified_at` | Time the first official zone was created; required. |
| `ended_at` | Set only when the final zone ends. |
| `peak_severity`, `peak_depth` | Highest verified state reached, preserved even after conditions recede. |
| `created_at`, `updated_at` | Audit-friendly record timestamps. |

`official_duration` is calculated from `verified_at` to `ended_at`; it is not stored as a separately mutable value.

### Event ownership on existing evidence

- Add nullable, indexed `event_id` to `flood_avoidance_zones`. A zone has one historical event owner and an event has many zones.
- Add nullable, indexed `event_id` to `flood_reports`. A verified supporting report has one event; a pending or rejected report has none.
- Existing `FloodReport.zone_id` remains the operational contributor link. It must not be repurposed as historical identity.

### `flood_event_locations`

Normalized affected-place rows: `id`, `event_id`, `location_type` (`road`, `barangay`, or `city`), `display_name`, `normalized_name`, optional SRID-4326 geometry, and timestamps. A unique constraint on `(event_id, location_type, normalized_name)` prevents one event from counting the same named place twice. This supports multi-road and cross-barangay events without forcing a single location string.

### `flood_report_moderation_outcomes`

An append-only staff decision history: `id`, `report_id`, `outcome` (`approved`, `linked`, `rejected`), nullable `rejection_reason`, nullable `internal_note`, `event_id`, `zone_id`, `acted_by_user_id`, and `acted_at`.

For a rejection, `rejection_reason` is one of `insufficient_evidence`, `incorrect_location_or_details`, `false_spam_or_malicious`, `outside_coverage_area`, `withdrawn`, or `other`; `other` requires `internal_note`. The current `FloodReport.status` remains a fast current-state field, while this table preserves the decision history.

### `flood_event_timeline_entries`

A readable incident history, separate from Audit Trail: `id`, `event_id`, `entry_type`, `occurred_at`, `summary`, and `snapshot_json`. Entry types include `event_verified`, `report_linked`, `zone_created`, `zone_updated`, `severity_peak_changed`, and `event_ended`.

`snapshot_json` stores the event-relevant state at that moment (for example, the zone GeoJSON and official overrides). This preserves what staff verified even when the operational zone is later edited. Technical actor/IP/request details continue to belong in the existing `AuditLog`.

## 5. Indexes and Integrity Rules

- B-tree indexes: `flood_events(status, verified_at)`, `flood_events(ended_at)`, `flood_reports(event_id)`, `flood_avoidance_zones(event_id, is_active)`, `flood_report_moderation_outcomes(report_id, acted_at)`, and `flood_event_timeline_entries(event_id, occurred_at)`.
- Location index: `(event_id, location_type, normalized_name)` unique, plus `(location_type, normalized_name)` for recurring-place analytics.
- Spatial index: a GIST index on any `flood_event_locations.geometry`, using SRID 4326. Existing zone/report spatial indexes remain unchanged.
- Database checks: an `ended` event requires `ended_at`; an `active` event must not have `ended_at`; the rejection reason/note rules are validated in both Pydantic and the database constraint where practical.
- The event service owns all multi-table transitions. Routes remain thin; they must not calculate duration, peak severity, or active-zone completion in the frontend.

## 6. Required Service Transactions

1. **Create official zone:** create `FloodEvent`, create zone with `event_id`, create `event_verified` and `zone_created` timeline records, and audit the action in one transaction.
2. **Approve a report into a new zone:** create one event and zone, approve/link the report, update event timestamps/peak, write moderation outcome and timeline entries, then apply reporter credit once.
3. **Link supporting report:** lock the report/event as needed, approve/link the report to the existing event/zone, refresh first-report and peak values when applicable, write outcome/timeline, and apply credit once.
4. **Reject report:** validate a structured reason, write rejection outcome, set current report status to rejected without setting `deleted_at`, apply the existing penalty exactly once, and write Audit Trail.
5. **End zone:** mark the requested zone inactive. If it is the final active/unexpired zone for the event, set `ended_at` and `status = ended`, then append `event_ended`. Manual and expiry-driven endings call this same transaction.

Each transition needs idempotency safeguards: a retry must not create a second event, duplicate timeline entry, or credit/penalize a reporter twice.

## 7. Legacy-Data Policy

No existing rejected report, archived report, inactive zone, or expired zone will be silently converted into verified historical data. The migration will introduce empty/new structures and preserve legacy records exactly as they are.

After release, authorized staff may use a deliberately designed classification/backfill workflow for legacy data. That workflow must require a human decision and leave an audit record; it is not part of the initial migration.

## 8. Expiry Recommendation Requiring Confirmation

Use a reliable scheduled server-side job (recommended: authenticated Cloud Scheduler/Cloud Run execution) to find due zones and call the shared end service. This is more reliable than a FastAPI in-process background task, which can be interrupted by Cloud Run instance shutdown. Until the scheduled job exists, staff can explicitly end zones through Spatial Operations; a normal list/map request must not perform the write implicitly.

## 9. Migration Sequence After Approval

1. Create the four new tables and the two nullable event foreign keys with indexes/checks; do not backfill historical incidents.
2. Register models and typed schemas, then implement and test the event service transactions.
3. Redirect rejection away from `deleted_at`/Archive Center while retaining true archive behavior for intentional deletion.
4. Update active-zone deactivation and expiry handling to end events only after the final active zone.
5. Build the moderation, records, and analytics surfaces only after the lifecycle contract passes tests.

## 10. Approval Gate

Before any SQLAlchemy model or Alembic migration is created, the developer must approve:

- the ownership model (`event_id` on reports and zones),
- the four new tables and retention policy,
- the no-automatic-backfill rule, and
- the scheduled expiry strategy.

