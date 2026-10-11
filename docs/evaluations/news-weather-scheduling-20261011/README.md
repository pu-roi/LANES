# Automatic weather scheduling — local acceptance

> **Last Updated:** October 11, 2026, 11:03 PM
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Boundary:** Local implementation and read-only provider/cloud inspection. No deployment, IAM update, scheduled dispatch or shared-database mutation.

## Verified implementation

The [plan](../../plans/news-weather-scheduling.md) is implemented on `roi-branch`, preserving the existing uncommitted automation panel and pipeline progress changes. Adaptive policy selects 60/15/30 minutes; settings retain the collection switch and stored legacy interval but cannot change it. Machine-only POST and existing protected status GET have separate authentication. Worker and controller share due calculation; the independent expiry job remains intact.

Weather is scheduling context. Tests/probes below do not validate the 0.2 mm threshold as a flood predictor, street coverage, actual flood placement or monetary savings.

## Automated checks

| Check | Result |
|---|---|
| Weather/auth/dispatch/controller, operational settings, pipeline/status regressions | **146 passed**, three existing multipart/Pydantic warnings |
| Disposable PostgreSQL/PostGIS persistence and overlap checks | Included in the 146; fresh guarded database migrated to `d7e4b9a21c60` |
| News automation and System Settings Playwright | **28 passed**, desktop/mobile, one worker |
| Existing News Intelligence Playwright | **15 passed**, one intended desktop skip of mobile-only navigation |
| TypeScript `tsc --noEmit` | Passed |
| Scoped ESLint, changed admin/news source and three affected browser suites | Passed |

Policy fixtures cover threshold below/at/above 0.2 mm, negative/nonfinite/missing precipitation, upstream-only positives, missing coordinates/slots/units, provider disagreement, 30-minute freshness boundary, 60-minute cooldown boundary, active evidence priority, dated/undated no-advisory messages, unrelated locations, affected city names, invalid/future/stale advisories, rainfall/thunderstorm fallback ages, explicit validity and midnight updates.

Native tests cover committed reader snapshots/reservations before external starts, duplicate quarter-hour delivery, controller and worker locks, due/not-due collection, paused collection with pending processing, uncertainty followed by successful reconciliation, failed reconciliation retaining the token, proven absence retry, ignored legacy saves without spurious revisions, stale retained zones excluded from risk, empty completed extractions, overdue leases and due/future retry predicates. Existing operational settings tests preserve pipeline/publication/expiry switch behavior and failures.

Browser checks exercise desktop and mobile status, loading/read failure/retry, GET-only refresh, completed-cycle flood-card invalidation, source clocks/links, dispatch/parse failures, coverage disclosure and absent interval editing. Widths 320/390/1440/1920 have no horizontal overflow in adaptive status fixtures; screenshots were visually inspected. These are intercepted API fixtures, not cloud machine execution acceptance.

Reproduce backend acceptance with a **fresh empty** loopback database named `lanes_settings_test_*` and the guarded `LANES_SETTINGS_TEST_DATABASE_URL` fixture:

```powershell
cd backend
venv/Scripts/python.exe -m pytest tests/test_news_weather.py tests/test_news_weather_postgres.py tests/test_operational_settings_postgres.py tests/test_news_automation.py tests/test_operational_settings.py tests/test_news_pipeline.py -q
```

The run recorded here used `lanes_settings_test_weather_20261011f`; existing migrations were applied by the fixture, and head was independently read afterward. There are no new models, migrations or packages. Disposable databases are removed after acceptance; ordinary local/shared databases are excluded by the fixture guard.

```powershell
cd frontend
npx tsc --noEmit
npx eslint src/features/admin/SystemSettingsPage.tsx src/features/news/NewsAutomationPanel.tsx src/features/news/NewsIntelligencePage.tsx src/features/news/newsApi.ts tests/news-automation.spec.ts tests/system-settings.spec.ts tests/news-intelligence.spec.ts
npx playwright test tests/news-automation.spec.ts tests/system-settings.spec.ts --workers=1
npx playwright test tests/news-intelligence.spec.ts --workers=1
```

Initial fixture failures were corrected: browser navigation waited on unrelated map assets; alert selection conflicted with Next's route announcer; native cooldown setup omitted the last-positive timestamp; a mocked Google credential lacked its validity attribute after credential reuse was added. Final checks above passed. A dispatch reconciliation failure discovered during code review was fixed and given a native regression.

## Actual provider probe

[Saved read-only result](provider-probe.json), checked **October 11, 2026, 10:39:53 PM PHT**:

| Provider | Actual result |
|---|---|
| Open-Meteo batch | Risk; all 20 samples had precipitation meeting the engineering threshold; complete sampled slots, no coverage error |
| PAGASA official NCR page | Relevant Rainfall Advisory No. 6 for Metro Manila/Rizal; issued 8:00 PM PHT, next update/validity 11:00 PM PHT |
| PAGASA thunderstorm section | Undated no-advisory message; `advisory_timestamp_missing` |
| Combined decision | 15 minutes; positive rainfall signal takes precedence over incomplete thunderstorm freshness |

This probe fetched public weather only, without database writes, news collection or Cloud Run starts. It is a historical snapshot; do not present it as current weather. Run `python -m scripts.probe_news_weather --output PATH` from backend for a new read-only check.

[Monitoring catalog](monitoring-catalog.json) records the 17 NCR and three upstream engineering samples. The upstream locality relevance was checked against [official PAGASA basin geography](https://pubfiles.pagasa.dost.gov.ph/pagasaweb/files/hmd/riverbasin/ncrpasig-marikina-laguna-de-bay.pdf). That historical document supports basin/locality context only and is not ingested as a live scheduling advisory. [Open-Meteo documentation](https://open-meteo.com/en/docs) supports the batch hourly model-estimate request.

## Cloud inspection and remaining release acceptance

Read-only inspection confirmed the existing Scheduler is ENABLED at **`0 */3 * * *`**, PHT, POSTing directly to the news job with OAuth. API URL/runtime identity and Scheduler target/account/deadline were recorded in the [rollout guide](../../guides/news-weather-scheduling-rollout.md). No cloud setting was changed.

Release matching API, worker and frontend; provision scoped job dispatch/read permission to the API runtime identity; configure exact audience/account/job; then change Scheduler to a 15-minute OIDC controller POST. Verify actual machine requests, autonomous checks and executions with the browser closed. Capture provider issues, request durations and worker-start counter deltas under representative conditions before claiming savings. Preserve a coordinated previous-version and three-hour OAuth rollback.

## Documentation audit

The eight core records were inspected. Task plan/progress, stack, existing news feature description, Decision 25, screen/API documentation, JSON persistence note and bug log were updated within their existing scope. The functional-settings plan and release instructions now point to adaptive scheduling; the October 7 evaluation remains historical. The documentation index links the new plan, evaluation and rollout guide.

## Planner and publication audit

**October 11, 11:03 PM PHT — requested by the developer:** Audit all eight core records and retain their feature/decision scope. Expand existing Decision 25 rather than creating a duplicate flagship feature or unrelated architecture entry. Record why the lightweight controller owns wake-ups/due work, how weather is separated from publication evidence, exact OIDC identity, durable uncertain-dispatch handling, read-only observability, legacy interval preservation and coordinated release/rollback.

This continuation changes documentation only. The preceding completed acceptance remains **146 backend/native checks and 43 browser checks**, with one intended desktop skip, TypeScript/scoped lint and real read-only provider probes; these are not newly rerun or claimed as live cloud acceptance. No new imported library, requirement/package/lockfile, SQLAlchemy model or Alembic migration appears in the pending changes. Existing guarded native runs already applied the migration chain through `d7e4b9a21c60`. Source and controller additions reuse declared libraries; environment examples contain blank machine-configuration placeholders.

The publication checkpoint verifies changed Python syntax, added Markdown targets/decision anchor, catalog/probe JSON, staged whitespace and added-content secret patterns. Stage all existing code, status-panel, tests and documentation together under the repository's push protocol. Commit/push to `roi-branch` is authorized; cloud deployment/IAM/Scheduler mutation remains outside this request. Attribution: [@roicambe](https://github.com/roicambe) (Roi Cambe).
