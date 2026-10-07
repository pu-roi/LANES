# Structured Pasig flood follow-ups — local implementation

> **Last Updated:** October 07, 2026, 8:35 PM (Asia/Manila)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Code implemented locally and source-reviewed; database/API/browser acceptance and deployment pending.

## Delivered

Owners can record a still-flooded/subsided follow-up under their report in Profile → My Hazard Reports. Staff see a separate follow-up queue in Flood Report moderation, can review evidence and location, and export the current page as JSON. Narrow/wide layouts share the same components. The profile bottom padding now respects the bottom-navigation variable and safe area.

The workflow reuses existing audit JSON storage and the existing event timeline. No SQLAlchemy model, Alembic definition or dependency was added. It collects immutable source claims, not automatic clearance decisions or automatically admitted model examples. It has not been deployed.

| Layer | Files |
| --- | --- |
| Contracts | `backend/app/schemas/flood_followup.py` |
| Bounded queries and persistence | `backend/app/crud/flood_followup.py` |
| Owner/review/export rules | `backend/app/services/flood_followup_service.py` |
| Endpoints/router | `backend/app/api/v1/endpoints/flood_followup.py`, `backend/app/api/v1/api.py` |
| Generic audit privacy exclusion | `backend/app/crud/audit.py` |
| Frontend feature | `frontend/src/features/flood-followups/followupApi.ts`, `FollowupSubmission.tsx`, `FollowupReviewQueue.tsx` |
| Integration | `frontend/src/features/profile/ProfileView.tsx`, `frontend/src/features/admin/components/FloodModerationQueue.tsx` |

## API and evidence contract

All routes are under `/api/v1`:

| Route | Access and result |
| --- | --- |
| `GET /reports/{report_id}/follow-ups` | Authenticated owner; bounded history and server-owned submission eligibility/reason. |
| `POST /reports/{report_id}/follow-ups` | Authenticated owner; explicit observation, supporting text, same-location attestation, optional measured centimeters/HTTPS link and idempotency UUID. |
| `GET /admin/flood-follow-ups` | Non-Commuter staff with Reports `view/full`; review-state filter, up to 100 entries and older-ID pagination. |
| `POST /admin/flood-follow-ups/{followup_id}/review` | Reports `full`; independent accept/reject with supporting review text and same-location verification for acceptance. |
| `GET /admin/flood-follow-ups/export` | Same read capability; paged JSON with schema/target version, generation clock, original provenance, observations/reviews and `training_admitted=false`. |

Data preserves four different clocks: observed condition; evidence submission/availability; original citizen-observation availability when supported; staff review. The original source audit ID and original observed time stay separate and null when unavailable. Original geometry and reporter must match before that earlier provenance is used. Operational expiry, approval and event end do not supply any of these observation clocks.

Submissions freeze report, event/zone IDs, locality/place and geometry fingerprint. Pasig scope checks stored city aliases and nonempty valid SRID 4326 geometry; this is **not** certified polygon containment or affected-road validation. Owner and reviewer attestations remain human source evidence. No depth threshold or borrowed neighboring claim establishes subsidence.

The reporter chooses the observation time explicitly; the form never defaults it to now. A timezone is required, future observations are rejected, and a supported original wet clock bounds the follow-up chronology. Positive depth conflicts with subsided; zero conflicts with still flooded. Text is required and optional source URLs must be HTTPS without credentials; they are never fetched by the server. Media upload is not implemented in this first slice.

Report locks serialize UUID checks and the 100-follow-up bound. Same normalized payload/request ID returns the same record; changed reuse conflicts. Follow-up locks serialize the single append-only review. Self-review is forbidden. Acceptance requires unchanged original locality/geometry/event/zone snapshot and a qualifying current report; changed correspondence returns a visible conflict rather than silently rebinding old evidence. A pending report later linked to a new event can therefore require another current-snapshot submission/review; old claims remain preserved.

Accepted reviews can append a sanitized readable entry to an already matching event timeline. Original text/source URL and staff evidence remain in the private evidence records. The generic audit feed excludes both private action types before filters, count and pagination (BUG-118). Dedicated reads enforce owner/staff access and use `Cache-Control: no-store`. Submission/review/storage errors remain visible; database exceptions do not print private SQL parameters.

## Verification actually performed

- A separate source reviewer completed the [five-source data audit](pasig-clearance-followup-20261007/independent_review.json): all ten captures, all 33 rows, time bounds and unchanged ancestor/model hashes. Reviewed outputs were rebuilt with independent-review flags true. No new subsidence-duration pair was found.
- An independent code reviewer inspected ownership, report capabilities, immutable observations/reviews, locks/idempotency, original provenance, no operational writes, response admission flags, retry handling, visible errors and narrow/wide layout classes. The generic audit leak and mobile safe-area findings were fixed and re-read; no unresolved source-review blocker remained.
- Full frontend `tsc --noEmit --incremental false` completed successfully after final integration changes. Seven changed Python files parsed successfully with `ast.parse`. Dataset input/output hashes matched and `git diff --check` passed.

**Not performed:** automated tests, actual authenticated HTTP calls, database writes/concurrency checks, browser screenshots/viewport interaction, physical PWA acceptance, deployment, commit or push. Source review and compilation do not establish those runtime outcomes. No migration was introduced or run for this slice.

## Remaining work

1. Exercise actual owner/staff API behavior, durable transaction/lock/idempotency paths, privacy exclusions, JSON pagination/export, and desktop/mobile/PWA interaction in an authorized disposable environment before release.
2. Collect real follow-ups after deployment, preserving missing outcomes and biased/late reports. Review actual Pasig DRRMO incident-monitoring exports when supplied; the current annual CSV lacks incident clearance clocks.
3. Prepare a separate qualified duration export with outcome-independent reference selection, predictor availability, defensible scope/continuity and independent-event evaluation. A staff-accepted claim is not automatically sufficient for training. The fitted conditional AFT model remains unchanged and production-ineligible.

Full [implementation plan](../plans/flood-followup-evidence-plan.md). No current map/routing/zone expiry/reputation or public status changes are introduced by these follow-up records.
