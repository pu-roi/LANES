# Adaptive news scheduler release — October 13, 2026

> **Checked:** October 13, 2026, 1:30 PM PHT
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer requested correcting production scheduling to the implemented 60/15/30-minute policy. Before this release, the enabled Scheduler called the Cloud Run news job directly on `0 */3 * * *`; the adaptive controller existed in the deployed image but lacked machine configuration and dispatch permissions. A three-hour wake-up could not deliver 15-minute risk collection.

## Changes

- Reused Scheduler `lanes-news-discovery-every-3-hours`; changed its schedule to `*/15 * * * *`, Asia/Manila, and target to `https://lanes-api-tymrlmxbkq-de.a.run.app/api/v1/internal/news-scheduler/tick`.
- Replaced Google API OAuth target authentication with OIDC using `lanes-news-scheduler@lanes-project-508809.iam.gserviceaccount.com` and exact audience `https://lanes-api-tymrlmxbkq-de.a.run.app`.
- Set the existing API's `NEWS_SCHEDULER_AUDIENCE`, `NEWS_SCHEDULER_SERVICE_ACCOUNT`, and `NEWS_CLOUD_RUN_JOB` to that origin, identity and existing `lanes-news-discovery` resource.
- Bound custom role `lanesNewsDispatcher` to the existing news job for the API runtime identity. It contains only `run.jobs.run`, `run.jobs.runWithOverrides`, `run.executions.get`, and `run.executions.list`.
- Bound custom role `lanesNewsOperationReader` to the project for that identity, containing only `run.operations.get` for regional operation reconciliation.
- Promoted configuration revision `lanes-api-00081-n4x` to 100% normal traffic. Image digest remains `sha256:8f0cd8dc47f9277561b7002d3bacd97f86d03234b29577ee445609d9a35322d7`, the existing main release `cfd5aae`. No MCP/ChatGPT candidate code was deployed.

No application code, dependency, database schema, frontend, provider selection, extra container, or independent minute expiry schedule changed. Controller heartbeat/reservation writes and the dispatched worker use their normal backend paths.

## Verification

- `test_news_weather.py`: **61 passed**, including policy, authentication and dispatch behavior; no new provider inference probe.
- Scheduler metadata shows the quarter-hour schedule, controller target, expected OIDC identity/audience and no OAuth target token.
- API health returned HTTP 200; an anonymous POST to the controller returned HTTP 401.
- A user-requested verification delivery at **1:24:36 PM PHT** returned **HTTP 200**, approximately 18 seconds, on the promoted revision. Scheduler delivery logs confirm HTTP 200.
- Persisted controller state: checks=1, interval=15, reason=Relevant weather risk, worker_starts=1, dispatch_state=submitted, dispatch_error=null.
- Open-Meteo reported risk; PAGASA also reported risk with a partial `advisory_timestamp_missing` issue. Positive supported risk takes precedence over incomplete coverage. The partial provider issue remains visible; it is not fixed by the scheduling change.
- Execution `lanes-news-discovery-hjtpk` was created by this delivery and completed successfully at **1:25:45 PM PHT**. Successful execution does not establish a verified flood audit or zone activation.
- The next **automatic** Scheduler delivery at **1:30:03 PM PHT** returned HTTP 200 in approximately 4.9 seconds. Persisted checks increased to 2; risk interval remained 15, dispatch_error stayed null and worker_starts remained 1. The initial reservation is still within the controller's 15-minute pending guard, so this tick did not duplicate the worker. Later operation reconciliation remains to be observed.

The current observed interval is 15 minutes. Quiet 60-minute and uncertain 30-minute policy behavior pass deterministic tests; representative live periods and cost savings are not yet established. One verification delivery and one autonomous quarter-hour delivery are confirmed; a longer delivery history and later reconciliation remain unverified. ChatGPT automatic auditing remains unqualified.

## Rollback and retained evidence

Ignored local snapshots are in `data/news-scheduler-rollout-20261013/`: before-scheduler.json, before-job-iam.json and before-api.json. Previous normal traffic revision was `lanes-api-build-654a1d9f-0a0d-4938-8a7c-cc29244ea84b`; it uses the same image without the controller environment values.

If rollback is required, pause this Scheduler, restore its captured three-hour direct-job OAuth target using the [runbook](../guides/news-weather-scheduling-rollout.md#rollback), and restore previous API traffic before resuming. Restore the API template's previously absent three machine variables as well so later builds do not inherit a partly rolled-back controller configuration. Remove only the two newly added API runtime role bindings; do not remove pre-existing Scheduler permissions. Preserve controller and flood evidence records. No database downgrade or container cleanup is required.
