# Functional System Settings verification

> **Date:** October 7, 2026, Asia/Manila
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Boundary:** Local code and controlled verification; production rollout/live plotting remain open.

## Delivered behavior

The page now governs staff road defaults, per-depth evidence expiry, conservative citizen automatic approval and three independent news stages. Typed policy is shared by API handlers and workers. Settings/revision/audit are atomic; stale edits conflict and missing permissions fail authorization. Legacy values remain readable for history and legacy writes return 410.

Explicit citizen observation times persist in existing audit storage and local drafts. Eligibility uses documented human decisions, not the profile accuracy cache. Two distinct qualifying reporters create only their continuous common road section. Existing support requires matching live coverage and conditions. Automatic approvals do not raise trust/accuracy. Fresh full-section support can refresh an automatic zone; partial support preserves only its own contribution. Explicit staff deadlines remain authoritative. Staff can inspect automatic labels and correct/deactivate existing zones.

The scheduled worker locks overlapping executions, checks due collection from the database, respects publisher selection and saves stage health. Paused processing preserves saved evidence; already qualified clearance and expiry continue. Publication rechecks its switch immediately before the decision write. Expired evidence is Unconfirmed and stops affecting routing even before maintenance. Policy edits cannot retrospectively extend saved deadlines.

No SQLAlchemy model or migration is changed. Settings work introduces no dependency. The unused-settings/audit repair is tracked as BUG-119. Separate duration research/model and structured follow-up/profile changes in the shared workspace are preserved and are not adopted by this feature.

## Acceptance evidence

- **PostGIS acceptance: 174 checks pass** (24 settings/citizen/scheduler, 135 news lifecycle and 15 staff growth). Generated loopback databases apply existing migrations to `d7e4b9a21c60`, exercise settings/citizen/scheduler, existing news lifecycle and staff growth regressions, and are removed afterward. Coverage includes audit rollback, HTTP validation/permissions/legacy behavior, concurrent administrators, independent corroboration, stale/future/missing time, unvalidated roads, trust/human accuracy, duplicate evidence, continuous intersections, staff deadlines, cadence, publisher selection, overlap, paused stages, mid-run publication pause and delayed expiry.
- **Focused regressions:** 121 checks pass across policy validation, pipeline, extraction, evaluation, publication projections/API, media failure and spatial review/grouping. Together with native acceptance, this is **295 distinct backend checks**.
- **Browser acceptance:** 16 distinct controlled Chromium cases pass across desktop and iPhone-sized viewports: settings Save/Revert/health, view-only mode, save failure, conflicts, missing permissions, unsaved navigation, citizen draft observation preservation and automatic/manual feedback. API/authentication are fixtures; these are not real automatic approvals.
- **Frontend:** production build succeeds for all 26 routes; TypeScript succeeds. Scoped lint for the new settings page and new browser tests succeeds. Broader touched-file lint still reports pre-existing `any`/effect issues in existing modules; it is not claimed globally clean.
- **Migration/schema:** existing head is verified through fresh upgrades in the disposable acceptance databases. No application/cloud database migration is required or performed for this feature.

Earlier test runs exposed and repaired fixture setup errors, obsolete mock signatures, an optional-form default in direct handler tests, delayed permission errors, test locator/panel-state assumptions and paused-publisher queue handling. A mixed legacy suite also exposed existing module-level authentication overrides/local database assumptions; final unit and native groups use isolated, explicit targets. No failed check is counted as passing.

## Docker recovery during verification

Docker Desktop 4.91.0 failed on `sailor-ingest.sock`; after that socket directory was replaced, startup exposed a second stale `docker-secrets-engine/engine.sock`. Recognized crashed Docker processes were stopped; verified zero-byte socket directories were moved to backups and recreated. Docker then started successfully, with `lanes_postgis_db` and `lanes_valhalla` running. Databases, volumes and application files were preserved. The sequence matches the [reported Docker Desktop defect/workaround](https://github.com/docker/desktop-feedback/issues/554).

Recoverable backups:

```text
C:\Users\roicambe\AppData\Local\Docker\run.lanes-socket-backup-20261007-201848
C:\Users\roicambe\AppData\Local\Docker\run.lanes-socket-backup-20261007-201959
C:\Users\roicambe\AppData\Local\docker-secrets-engine.lanes-socket-backup-20261007-201959
```

This recovery is a workaround; repeated unclean shutdowns may leave stale sockets again. No factory reset was used.

## Release and live results

Production API/worker/frontend and Scheduler were not changed by this implementation. The accepted default is 30-minute collection behind a fixed 15-minute tick; the previously recorded production interval remains three hours until the [matching rollout](../guides/system-settings-rollout.md). Citizen approval defaults to staged disabled until release acceptance; agreed thresholds are already configured in code.

The existing live audit recorded six successful scheduled collections and a latest 94-entry collection with zero eligible flood reports. That establishes collection operation, not current-article independent evaluation or real plotting. No fixture result in this document closes live plotting or physical-device/PWA acceptance. See the [live audit](news-live-operational-audit-20261007.md).
