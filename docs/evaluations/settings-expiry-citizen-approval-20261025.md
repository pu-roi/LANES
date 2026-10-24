# Fixed evidence expiry and citizen automatic approval investigation

> **Date:** October 25, 2026, Asia/Manila
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Local implementation; no production settings, records or deployment changed.

## Evidence expiry

With automatic expiry enabled and Pasig ML disabled, policy v3 selected the saved fixed deadline even when it was null. It only generated activation retention in that branch if a previous ML fallback had already recorded that basis. Official zones and staff-approved reports could therefore remain active indefinitely with no timer.

Policy v4 generates configured per-depth retention for both fixed and fixed-fallback decisions without a saved deadline. Unknown depth uses its configured duration. The anchor is original zone activation, never worker execution or page refresh. Existing saved fixed timers and explicit staff deadlines remain intact. A timer already overdue ends through the existing Unconfirmed zone/event lifecycle on the worker run. Global pause still stops synchronization and expiry, and inactive records remain inactive.

The cache records the configured retention durations, so generated deadlines respond to changed settings without moving their activation anchor. Old active policy caches synchronize to v4; inactive v1–v3 forecasts remain readable. Both zone details `expires_at` and the private expiry-policy `deadline` expose the same saved timestamp. The settings explanation describes the fixed fallback; the existing shared details component already renders its deadline and retention basis at both viewport sizes.

## Citizen approval

The toggle is persisted correctly and is read by `approve_citizen_report`. Approval runs on new submissions; saving the toggle does not scan or retroactively approve existing pending reports. The public `FloodReportPanel` omits `observed_at`, including legacy draft timestamps. This was intentional in the October 8 Report Flood observation-time removal (BUG-122). The backend still requires an explicit timezone-aware observation within 30 minutes; report creation/submission time is not that observation.

An authenticated reporter satisfying trust and documented human-review history still receives `status=pending` and `automatic_review_reason=explicit_observation_time_required` when submitting the current form. Other admission requirements include validated continuous road geometry, known matching depth/access/hazards and either compatible existing zone support or two qualifying independent reporters. Default thresholds are trust 75, reviewed accuracy 90%, and five human reviews. Automatic approvals do not increase reputation.

System Settings now explains that current Report Flood submissions stay in staff review even with this toggle enabled. No observation control was reintroduced and no admission requirement was relaxed. Supporting current-form automatic approval requires a separate product decision on collecting explicit observation evidence; inferring it from submission would bypass the existing evidence rule.

## Verification

- 73 backend checks pass across `test_pasig_ml_expiry.py`, `test_operational_settings.py` and `test_operational_settings_postgres.py` using a fresh disposable local PostgreSQL/PostGIS database. Existing Alembic migrations apply through the test fixture.
- New regressions cover null fixed deadlines with/without legacy caches, known/unknown depth durations, stable refresh, details API agreement, lifecycle expiry, duration changes, and the actual authenticated multipart report submission without observation time.
- Targeted ESLint and TypeScript checks pass. Six desktop/mobile browser scenarios pass: fixed expiry details, citizen toggle persistence/limitation, and global expiry toggle persistence. The fixed expiry test verifies both the Expires field and automatic deadline; screenshots are inspected at both sizes.
- Initial harness setup was corrected: a template0 database was needed because the PostGIS image prepopulates its default database; explicit nonsecret auditor configuration overrides encrypted dotenv fields. Browser tests use a synthetic API base so intercepted fixtures match.
- No dependency, SQLAlchemy model or Alembic migration change; no production data write, push or release.

## Changed application files

- `backend/app/services/pasig_ml_expiry_service.py`: fixed fallback and policy cache/version handling.
- `frontend/src/features/admin/SystemSettingsPage.tsx`: existing settings explanations only; layout and controls preserved.
- Backend and Playwright regression suites listed above and in `system-settings.spec.ts` / `flood-review-suggestions.spec.ts`.
