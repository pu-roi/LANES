# Adaptive news scheduling rollout and rollback

> **Last Updated:** October 11, 2026, 10:52 PM
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Prepared only. No deployment, IAM change or Scheduler mutation performed in this implementation.

## Recorded existing configuration

Read-only cloud inspection on October 11 confirmed:

| Resource | Recorded value |
|---|---|
| Project / region | `lanes-project-508809` / `asia-east1` |
| API service URL | `https://lanes-api-tymrlmxbkq-de.a.run.app` |
| API/job runtime identity | `lanes-api-runtime@lanes-project-508809.iam.gserviceaccount.com` |
| News job | `lanes-news-discovery` |
| Scheduler | `lanes-news-discovery-every-3-hours` (ENABLED) |
| Current schedule | `0 */3 * * *`, `Asia/Manila` |
| Current target | `https://run.googleapis.com/v2/projects/lanes-project-508809/locations/asia-east1/jobs/lanes-news-discovery:run` |
| Current authentication | OAuth, `lanes-news-scheduler@lanes-project-508809.iam.gserviceaccount.com`, cloud-platform scope |
| Attempt deadline | 180 seconds |

Refresh this read-only record immediately before release; retain API revision/image, both job images/commands, frontend rollout, configuration revision and Scheduler fields in the release evidence. Existing reconstruction/historical replay data must not be mistaken for a fresh rain observation. Cloud metadata contains no credentials.

## Coordinated release gate

1. Finish local acceptance in the [evaluation](../evaluations/news-weather-scheduling-20261011/README.md). Publish matching API, news worker and frontend using the existing coordinated Cloud Build/Firebase workflows. Keep the expiry job's matching image and independent minute schedule. The news command remains `python -m scripts.run_news_discovery --discover --pipeline --scheduled --limit 50`.
2. Configure these API environment values as part of the matching release, preserving existing variables/secrets:
   - `NEWS_SCHEDULER_AUDIENCE=https://lanes-api-tymrlmxbkq-de.a.run.app`
   - `NEWS_SCHEDULER_SERVICE_ACCOUNT=lanes-news-scheduler@lanes-project-508809.iam.gserviceaccount.com`
   - `NEWS_CLOUD_RUN_JOB=projects/lanes-project-508809/locations/asia-east1/jobs/lanes-news-discovery`
3. Grant the **API runtime identity**, scoped to the existing news job where supported, permission to run with overrides and read execution state: `run.jobs.run`, `run.jobs.runWithOverrides`, `run.executions.get/list`, plus regional `run.operations.get`. [Google's role reference](https://docs.cloud.google.com/run/docs/reference/iam/roles) lists Jobs Executor With Overrides and Viewer; use the narrow required binding/custom role and verify operation-read scope. Ordinary web users receive none of these permissions. Keep the Scheduler service agent's existing token-generation permission; the exact configured account must be allowed to invoke the API if Cloud Run platform authentication is enabled. Do not enable public machine access as a workaround.
4. Verify anonymous/browser JWT POSTs are rejected, staff status GET is read-only, provider probes respond, saved stage switches are respected, and the actual frontend displays source clocks, uncertainty, due time and failures at desktop/mobile widths. Missing controller environment fails closed. Existing public API access need not change.
5. Only after matching versions and machine identity are accepted, replace the existing Scheduler target/authentication and cadence. The historical job name can stay:

```powershell
$apiServiceUrl = 'https://lanes-api-tymrlmxbkq-de.a.run.app'
$schedulerEmail = 'lanes-news-scheduler@lanes-project-508809.iam.gserviceaccount.com'
gcloud scheduler jobs update http lanes-news-discovery-every-3-hours --project=lanes-project-508809 --location=asia-east1 --schedule="*/15 * * * *" --time-zone=Asia/Manila --uri="$apiServiceUrl/api/v1/internal/news-scheduler/tick" --http-method=POST --oidc-service-account-email="$schedulerEmail" --oidc-token-audience="$apiServiceUrl" --attempt-deadline=180s --clear-message-body
```

The OIDC option replaces the previous OAuth target authentication. Re-describe the job and confirm it contains the expected OIDC email/audience and no OAuth token configuration. Review existing headers/retries while preserving other fields. The configured audience must be exact; do not use a browser JWT or a signed token in documentation. See [Scheduler HTTP authentication](https://docs.cloud.google.com/scheduler/docs/http-target-auth) and [update command](https://docs.cloud.google.com/sdk/gcloud/reference/scheduler/jobs/update/http).

## Operational acceptance and savings

Close the browser and observe actual Scheduler deliveries, API heartbeat and Cloud Run executions over several checks. Capture timestamps, API request duration, provider status/error codes, interval/reason, collection due/not-due outcome, execution IDs/results and counter deltas. Verify a quiet tick starts no full worker when no pipeline work is due, a risk or uncertain tick uses the appropriate due calculation, and pending retry/maintenance can run while collection is paused. Do not require quiet weather for activation acceptance when actual sources currently signal risk; use local fixtures for policy coverage and record actual live conditions honestly.

A complete no-token execution listing can establish absence; permission failures, paging exhaustion or uncertain operation responses cannot. If reconciliation stays unresolved, retain the reservation and investigate the matching execution/operation before any manual retry. Persisted `dispatch_error` and stale heartbeat are visible in News Intelligence. A failed worker execution is separate from provider uncertainty.

Record a baseline and representative quiet/rain periods before claiming monetary savings. Useful diagnostics are cumulative `checks`, `provider_failures` (including parse/partial-coverage issues), `worker_starts` and `last_tick_duration_ms`, with Cloud Run request/execution logs for history. A weather-triggered collection does not itself prove a published or correctly plotted flood.

## Rollback

Pause the Scheduler during a coordinated rollback. Restore the recorded API revision/image, worker image/command and frontend rollout together; preserve evidence, controller/settings JSON and original expiry deadlines. Restore the captured OAuth identity, target and three-hour schedule before resuming the older release:

```powershell
gcloud scheduler jobs update http lanes-news-discovery-every-3-hours --project=lanes-project-508809 --location=asia-east1 --schedule="0 */3 * * *" --time-zone=Asia/Manila --uri="https://run.googleapis.com/v2/projects/lanes-project-508809/locations/asia-east1/jobs/lanes-news-discovery:run" --http-method=POST --oauth-service-account-email="lanes-news-scheduler@lanes-project-508809.iam.gserviceaccount.com" --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" --attempt-deadline=180s --clear-message-body
```

Restore any other changed Scheduler fields from the release snapshot. Leave the independent zone-expiry schedule intact. Legacy interval values are preserved by the adaptive release, so coordinated old-version rollback can read them again. No database downgrade or new migration is required.
