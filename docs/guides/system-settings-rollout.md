# System Settings rollout and rollback

> **Last Updated:** October 11, 2026, 12:23 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 11 commuter-news release (current)

API revision **`lanes-api-build-86a78939-ca6d-4bce-9d18-db533a8e1c23`** serves 100% traffic. API and both news/expiry jobs use commit `429dd19495d75c71859796cb75ccf0d7bed427b0`, digest `sha256:2614ca4bbf446cbb242e4c49edb1eb4af172ca15a8de416f28f643d6501445bd`. Cloud Build `86a78939-ca6d-4bce-9d18-db533a8e1c23` succeeds, including existing migration execution `lanes-migration-nkhtg` and exact API promotion after both workers. Initial commuter frontend App Hosting rollout `build-2026-10-11-002` succeeds from the same commit. Current frontend rollout `build-2026-10-11-003` serves 100% traffic from UI commit `b93dc0b7b4735025ba83ebf2720d731806d43044`; build `ca3f2568-9ec5-4e4a-bac6-a3a1527c15ae` succeeds. Actual live acceptance at six widths verifies the 344-pixel desktop sidebar, hidden-until-hover/focus scrollbar, contained keyboard/wheel scrolling and expandable news/refresh on smaller screens. Backend/worker images are unchanged by this UI-only release. Actual public endpoint and desktop/mobile show five real commuter articles with publisher/date/source links. Health is connected; public alerts return 200, unauthenticated staff collection 401. Normal approved-source collection saved ten articles without new flood extraction (84 before/after). No new schema/dependency, policy or schedule change.

Rollback must keep API and workers coordinated. Previous API `lanes-api-build-2a8073e9-bb04-4731-9db3-7f3f9b9bb7e4` uses commit `549a31b1d50c38e0dcc6430e591c83df478b7887`, digest `sha256:d6eef5e1403e577967fe3a0bc2d4b4807a65eb51362676119605835181333134`; that earlier flood-only reader does not show commuter stories. Initial repair revision `lanes-api-00064-kjc` and recovery tag `ml-expiry` remain historical fallback choices. Image rollback does not undo saved captures or resurrect expired zones. [Acceptance](../evaluations/community-local-updates-20261011.md#commuter-news-live-release--october-11-1210-pm-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 11 Local Updates traffic correction (historical)

API revision **`lanes-api-00064-kjc`** served 100% traffic at this checkpoint. Its image is commit `9ab8979118871c4a466bd78aeba5af4ff646c2f4`, digest `sha256:b077c3301e43b1ff810d262acbd61bbbc62f1781f779ec7d80ce3c9976d4e549`; both existing news/expiry jobs already use that commit image. Successful builds had preserved traffic pinned to the October 10 recovery revision, causing the new Local Updates endpoint to return 404. Preview and actual public desktop/mobile reads now pass. The previous `lanes-api-00069-fey` remains available with its `ml-expiry` tag for rollback; if reverting runtime images, keep API/workers coordinated. No setting, scheduler, source data or schema was modified. Root Cloud Build now names the prepared API revision `lanes-api-build-$BUILD_ID`, leaves traffic unchanged until both workers deploy, and explicitly promotes that exact revision. At this checkpoint the build change was statically checked; the commuter-news release above later exercises it successfully. [Acceptance](../evaluations/community-local-updates-20261011.md#live-loading-failure-and-traffic-repair--october-11-1130-am-pht). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 10 legacy recovery release (historical)

Current API revision **`lanes-api-00069-fey`**, 100% traffic; both jobs use `pasig-ml-expiry-recovery-20261010-2105`, digest `sha256:bdddcaceef2b5f8cb0fb2283725144c79de763d70635981a7bc2619736889382`. Policy v2 recovers valid original issuance forecasts after a late first run while preserving current evidence/review checks. #17/#18 have expired as Unconfirmed; no inactive zone is revived. #19–#21 retain their saved dates. Minute Scheduler is ENABLED, existing three-hour news cadence/configuration is preserved, local API/worker run the matching code. Existing migration head remains `d7e4b9a21c60`; no schema/dependency/settings change.

Local UI: refresh `/admin/map` → Active Zones → All History → Info to review inactive saved forecasts. Cloud frontend remains a separate release. Recovery uses existing audit JSON for quantiles, original issuance and model checksum. [Acceptance](../evaluations/pasig-ml-automatic-expiry-20261010.md#legacy-recovery-and-saved-ui-acceptance--october-10-915-pm). [@roicambe](https://github.com/roicambe) (Roi Cambe)

For rollback of this recovery release, coordinate API and both jobs back to revision `lanes-api-00067-zox` / image `pasig-ml-expiry-20261010-1928`; pause minute scheduling while versions differ. That historical v1 lacks late recovery and saved quantile display. Rolling back an image does not undo deactivation or resurrect #17/#18. Keep audit/source rows. The older pre-bridge rollback instructions below refer to a different release boundary.

## October 10 Pasig ML cloud expiry release

The developer authorized **Local app and shared cloud worker**. Matching API revision `lanes-api-00067-zox` now serves 100% of traffic. Both `lanes-news-discovery` and independent `lanes-zone-expiry` use image `pasig-ml-expiry-20261010-1928` with digest `sha256:4c48fb60f211e35753953e0577c8cc821b86621496d69b140c0041fdb4579fee`, in project `lanes-project-508809`, region `asia-east1`. Existing runtime account, database connectivity and other environment bindings are preserved. No schema/dependency changes, cloud migration, settings save, Git push or cloud frontend release occurred. [Cloud execution evidence](../evaluations/pasig-ml-automatic-expiry-20261010.md#actual-shared-cloud-release--october-10-836-pm).

`lanes-zone-expiry-every-minute` invokes the new job every minute through the existing OAuth scheduler account, with job-scoped `roles/run.invoker`. The job runs `python -m scripts.run_zone_expiry` once at 1 GiB, with a 300-second timeout. It synchronizes saved model deadlines before deactivation and does not collect news or call external AI providers. Scheduler HTTP 200 delivery and a completed scheduled execution were verified. The existing news Scheduler keeps its three-hour cadence; news/provider failures cannot stop this independent expiry path. Root `cloudbuild.yaml` updates both jobs to the matching API image on future backend releases.

The local updated UI on port 3000 exposes **Use ML expiry for Pasig** and **Enable automatic expiry**. Both flags currently read true in the cloud runtime; the shared settings record was not changed. Global pause takes precedence. Ineligible/outside-Pasig zones keep fixed fallback; existing null deadlines remain visibly unscheduled. Due expiry means Unconfirmed, never observed dry/passable. Source timestamps, immutable news decisions and model qualification flags remain unchanged. The cloud frontend remains on its previous release, so use the updated local UI for these new controls.

For an immediate maintenance check:

```powershell
gcloud run jobs execute lanes-zone-expiry --region=asia-east1 --project=lanes-project-508809 --wait
```

Inspect the execution and logs for successful completion; repeated maintenance must preserve unchanged model deadlines. Read-only cloud inference already reproduced zone 19/20/21 deadlines exactly. This verifies operational integration, not predictive accuracy.

For policy rollback, disable **Use ML expiry for Pasig** through the updated versioned settings UI and run maintenance so original fixed deadlines are restored. Review overdue restored deadlines: normal expiry can then end those records as Unconfirmed. No inactive zones are revived. For a runtime rollback, first complete that policy restoration, pause only `lanes-zone-expiry-every-minute`, restore API traffic to the recorded previous revision `lanes-api-00058-hx4`, and restore the news job's previous image `gcr.io/lanes-project-508809/github.com/pu-roi/lanes:2260c7e07358e4c3c12c06738b87dc11ac4b7bda`. Retain all evidence/audit rows; an old image does not contain the new expiry command. Keep API/worker versions together. The older release instructions below are historical and should not be repeated as new migration/schedule work.

## Automatic expiry control — October 10 local addition

System Settings → Evidence expiry → **Enable automatic expiry** controls both scheduled expiry and deadline-based public/Admin/news/routing visibility. Default ON preserves current behavior. OFF keeps existing active records available past saved deadlines; it does not revive inactive records, bypass new evidence admission, alter source timestamps or stop manual deactivation/qualified clearance. ON resumes saved deadlines immediately, with overdue records ended on the next worker run. The separate experimental Pasig operational policy now applies fitted deadlines under Decision 27; research prediction GETs remain read-only.

Use the matching updated settings client **before saving the shared policy**. The flags are persisted in the existing atomic configuration envelope outside legacy nested settings; old strict-schema workers can continue reading known fields, but do not honor the pause. An old settings writer can drop the new envelope flags. The cloud API/workers now match; the local updated settings UI remains on frontend 3000/backend 8000. The earlier toggle-only test did not deploy or save cloud policy; the cloud release above supersedes its deployment state. [Earlier verification and files](../evaluations/automatic-expiry-toggle-20261010.md).

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

Pause collection/processing/publication independently before reverting the application release. Leave automatic expiry enabled unless a deliberate expiry pause is required; qualified clearance maintenance continues independently. Disable citizen approval if its acceptance fails. Save the current revision and configuration first; use the versioned endpoint to restore reviewed policy values, never direct legacy writes. Saved policy snapshots and old deadlines remain immutable and must not be extended or resurrected by rollback.

If reverting to the previous worker, restore the previously verified three-hour Scheduler cadence and command before enabling collection; the old worker does not use database due checks. Retain evidence/audit rows and existing database volumes. Review API/worker/frontend versions together.
