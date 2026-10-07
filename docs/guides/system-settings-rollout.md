# System Settings rollout and rollback

> **Date:** October 7, 2026, Asia/Manila
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Prepared release steps; no production setting/schedule change was performed by this task.

## Before release

Review the [implementation contract](../plans/functional-system-settings.md) and [verification evidence](../evaluations/functional-system-settings-20261007.md). This task adds no model, migration or dependency. Preserve/review the separate duration research changes independently when choosing the release source; do not silently include unrelated working-tree changes.

Run from `backend` using the project Python environment:

```powershell
venv\Scripts\python.exe -X utf8 scripts/verify_settings_postgis.py
```

This command creates fresh loopback databases from the existing development PostGIS container, applies existing migrations to head, runs settings/publication/staff-growth acceptance and removes only its generated databases. It never targets the application database. New clones also need the existing Python/Node dependency installation; use the repository's normal encrypted-environment loading workflow for the application.

From `frontend`, run type checks, the production build and controlled desktop/mobile tests:

```powershell
npx tsc --noEmit
npm run build
npx playwright test tests/system-settings.spec.ts tests/citizen-observation.spec.ts
```

Installed Chrome may be selected with `PLAYWRIGHT_CHROME_PATH` on machines without bundled Playwright browsers. Browser tests use synthetic authentication and intercepted API responses; they cannot establish live backend publication.

## Release sequence

1. Release the reviewed API and matching discovery image through the existing [news release checklist](news-zone-release-checklist.md). Verify existing migration head `d7e4b9a21c60`; there is no new settings migration. The worker must use:

   ```text
   python -m scripts.run_news_discovery --discover --pipeline --scheduled --limit 50
   ```

2. Release the matching frontend through the configured Firebase workflow. Root Cloud Build deploys the API/job, not the frontend. Verify the four groups, recorded health, view-only permissions and atomic saves against the actual versioned API. Keep citizen automatic approval disabled during mixed-version deployment.
3. Confirm one controlled job execution runs the scheduled path, persists stage health and leaves paused stages untouched. Verify job service-account/HTTP targeting against its existing configuration. Do not provision cloud-management permissions to the web application.
4. **Only after those checks**, change the existing Scheduler job `lanes-news-discovery-every-3-hours`, in project `lanes-project-508809`, region `asia-east1`, to the fixed 15-minute tick:

   ```powershell
   gcloud scheduler jobs update http lanes-news-discovery-every-3-hours --project=lanes-project-508809 --location=asia-east1 --schedule="*/15 * * * *" --time-zone=Asia/Manila
   ```

   Preserve the existing target/authentication and all other fields. Its historical name need not change. The database default is **30-minute collection**, so alternate ticks normally perform lifecycle maintenance without RSS collection. Administrators can subsequently select 15/30/60 minutes without editing Google Cloud.
5. In System Settings, verify trust 75, reviewed accuracy 90 and five human reviews, then enable citizen automatic approval after release acceptance. Incomplete/older-client reports remain pending. Inspect staff moderation labels and existing zone correction/deactivation controls.
6. Record actual scheduled attempts, feed counts, errors and due/not-due behavior. Separately record a genuine current article's independent evaluation, publication, plotted road coverage and routing effect. Zero eligible articles cannot satisfy that final live plotting check.

The previous automatic three-hour cadence was recorded during the September 25 rollout and confirmed in the [October 7 live audit](../evaluations/news-live-operational-audit-20261007.md). It operates without an open browser.

## Rollback

Pause collection/processing/publication independently before reverting the application release. Keep expiry and qualified clearance maintenance running. Disable citizen approval if its acceptance fails. Save the current revision and configuration first; use the versioned endpoint to restore reviewed policy values, never direct legacy writes. Saved policy snapshots and old deadlines remain immutable and must not be extended or resurrected by rollback.

If reverting to the previous worker, restore the previously verified three-hour Scheduler cadence and command before enabling collection; the old worker does not use database due checks. Retain evidence/audit rows and existing database volumes. Review API/worker/frontend versions together.
