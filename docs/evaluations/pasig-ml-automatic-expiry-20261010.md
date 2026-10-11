# Pasig ML automatic expiry: implementation and local/cloud acceptance

> **Last Updated:** October 10, 2026, 9:22 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Documentation and pre-push audit

**Pasig coverage and abstention:** Eligible Pasig polygons can use the shared Pasig model even when their barangay has no local historical outcomes. This is not guaranteed inference for every record. Unverified location, missing observation time without an accepted registration/submission proxy, incompatible depth snapshots, changed/review-pending evidence or unavailable model assets can still produce an explicit unavailable/fixed-fallback state. A saved operational forecast remains visible after expiry even when the current research preview is inactive or stale. Expiry means Unconfirmed, not observed flood clearance; p90 is an experimental policy estimate, not calibrated certainty.

At the developer's explicit senior-planner/push request, audit and synchronize all eight core documents and the catalog, amend Decision 27's eligibility contract and clarify Decision 26's historical research boundary. Preserve older runtime snapshots as historical; no universal availability or accuracy claim is adopted. Author: [@roicambe](https://github.com/roicambe) (Roi Cambe).

Pre-push: branch `roi-branch` was synchronized with origin; all current changed/new files are included under the repository's stage-all protocol, including earlier news/map work. A fresh native repeat passes **63 tests**, exercising existing `alembic upgrade head` through the guarded disposable PostGIS fixture and removing its test database. This is a repeat of existing acceptance, not 63 additional distinct tests. No staged SQL model/migration, dependency manifest or lockfile change exists. Changed Python source parses; external runtime imports remain registered. Staged credential/key/JWT/database-password patterns and local environment/runtime-artifact checks find no matches. Changed document catalog entries and relative links resolve; whitespace checks pass. The prior 43 source tests, 10 responsive fixtures, four actual Info workflows, TypeScript/scoped lint and deployed API/job verification remain the recorded acceptance. Full project-wide tests are not claimed rerun; the separate reviewed-merge duplicate-location failure remains tracked in the task plan.

This publication request commits repository work; it does not itself confirm a subsequent cloud frontend rollout or new live flood observations. Temporary deployment bundles, credentials and test data remain ignored. No force-push is requested.

## Legacy recovery and saved UI acceptance — October 10, 9:15 PM

**Delivered locally and to the shared cloud API/workers.** This supersedes the 8:48 PM investigation and original v1 activation snapshots below. No new historical evidence, source timestamps, flood onset, training outcome, model artifact, SQL schema or dependency was created.

The internal resolver adds an operational recovery mode. Current source identity, geometry, versions, approval, edits, follow-ups and review state still qualify at the real clock. Only forecast age is evaluated at immutable original issuance; public research previews retain their current-clock staleness. The policy version is `pasig-experimental-ml-expiry-v2`, invalidating the old cached null fallback. A late first run can recover an overdue original p90 without moving it to now. Existing manual fixed deadlines, disabled ML, global pause, model fallback and no-resurrection contracts remain.

The existing policy audit JSON now stores all three quantiles, prediction issuance and model checksum. The authenticated no-store expiry DTO supplies these to `ZoneExpiryPolicy.tsx`, which displays **Saved ML subsidence estimate**, its interval/anchor/proxy and the operational deadline. `ActiveZonesPanel.tsx` retains Info for inactive history; inactive details do not offer Deactivate. The current research preview may correctly say inactive while the saved historical forecast remains visible.

| Zone | Live state | Method | Saved automatic expiry (PHT) |
|---|---|---|---|
| 17 | Inactive; event ended Unconfirmed | Pooled Pasig, registration proxy | October 9, 2026, 7:25:02 AM |
| 18 | Inactive; event ended Unconfirmed | Pooled Pasig, approved submission proxy | October 10, 2026, 5:04:13 AM |
| 19 | Active | Pooled Pasig | October 11, 2026, 11:27:52 AM |
| 20 | Active | Pooled Pasig | October 11, 2026, 9:23:33 PM |
| 21 | Active | Depth/cross-location | October 12, 2026, 3:46:36 AM |

#17's saved median is October 8, 5:13:48 PM; #18's is October 9, 2:52:59 PM (PHT). Automatic expiry uses the upper p90, not the median. Actual observed flood onset remains unknown. Both events' `evidence_expired` timelines explicitly contain `condition=Unconfirmed` and their event status is ended. Due lifecycle deactivation changes the zone edit clock in its normal way; policy calculation itself preserves source clocks.

Verification: **43 source/submission tests + 63 native PostGIS prediction/settings/expiry tests = 106 backend checks**, including unchanged rejection gates, old v1 null fallback recovery, late approved-submission recovery, edits/public updates, idempotence, immutable timestamps and private inactive DTO. Disposable native databases apply existing migrations and are removed afterward. **10 desktop/mobile Playwright checks** cover saved history Info, inactive labeling, forecast display, fixed/pooled/cross methods and visible failures. TypeScript and scoped ESLint pass. Transaction-only preview recovered #17/#18 and kept #19–#21's exact previous deadlines, then rolled back. Finally **four actual authenticated desktop/mobile workflows** open #17/#18 through All History → Info against real endpoints, show saved forecasts and confirm no horizontal overflow. Screenshots were visually inspected. Short-lived verification credentials stayed in process memory; no synthetic flood records or direct source edits were needed.

Cloud Build `33be2a0c-31ed-414d-8c66-8cf06da5e8ea` succeeded with runtime asset verification. Image `gcr.io/lanes-project-508809/github.com/pu-roi/lanes:pasig-ml-expiry-recovery-20261010-2105`, digest `sha256:bdddcaceef2b5f8cb0fb2283725144c79de763d70635981a7bc2619736889382`. Staged and production authenticated GETs reproduce all five saved methods/deadlines/quantiles/issuance values. API `lanes-api-00069-fey` serves 100% traffic. Both cloud jobs use the same image. The old local worker was stopped; minute Scheduler was briefly paused during image handover, then resumed **ENABLED** at its unchanged cadence. The new local worker expired two overdue zones; cloud execution `lanes-zone-expiry-m4qpq` subsequently succeeded with `expired=0`, proving idempotent maintenance. Scheduler-created `lanes-zone-expiry-2wk4p` also completed successfully. Matching news execution `lanes-news-discovery-zxzsg` completed successfully at 9:14:56 PM PHT. Repeated local minute runs report `expired=0`; production health confirms database connectivity and anonymous private status access returns 401. Existing migration head is `d7e4b9a21c60`; configuration flags remain enabled without a settings save.

Local API/worker and frontend 3000 run the repair. Refresh `/admin/map`, open Active Zones → All History → Info for #17/#18. Cloud frontend was not released in the authorized local-app/shared-worker scope. No Git commit/push occurred. Scientific accuracy and independent prospective outcomes remain open; operational integration is verified, not a guarantee of physical subsidence.

## Follow-up investigation: legacy zones 17 and 18 — October 10, 8:48 PM

**Historical 8:48 PM status: confirmed integration gap; superseded by the recovery acceptance above.** The developer questioned why zones 17/18 receive no expiry despite the previously delivered pooled/cross-location adapters. Read all four referenced chats: Review ML progress and task plan (`01a1192b-4fb3-7802-8e32-1c507c6cdafd`), Review ML progress and next steps (`01a11698-3bef-7ca3-9d0b-b839813e8454`), Plan flood zone expiry (`01a1072a-88d1-7541-ba75-da9e96795b59`) and Review flood plotting conversation (`01a105dd-b43a-70b2-aa2b-4fa054aa144b`). Earlier acceptance explicitly demonstrated registration simulation for #17 and approved submission simulation for #18. These were read-only previews before the expiry bridge was deployed.

Live read-only inspection confirms both zones remain active with null `expires_at`, enabled expiry flags, valid Pasig geometry and available fitted models. This investigation makes no source/status/deadline/configuration changes and does not deploy or push code.

| Zone | Existing source | Current blocker | Original model p90 reconstructed read-only (PHT) |
|---|---|---|---|
| 17 | Ugong; unchanged official registration audit #140, October 7 at 11:35:53 PM | Registration is about 69 hours old, exceeding the preview's 2,000-minute wall-clock age gate | October 9, 2026, 7:25:02 AM |
| 18 | San Nicolas/Santo Tomas; report #16, submission audit #164 October 8 at 9:15:04 PM and approval audit #166 at 9:15:49 PM | Submission is about 47.5 hours old, exceeding the same wall-clock gate | October 10, 2026, 5:04:13 AM |

Both immutable source adapters otherwise pass their current checks: no qualifying edits/review signals, matching source/zone/event/geometry and approved submission lineage. Actual observation time remains unknown. The quoted generic no-observation reason is therefore incomplete: supported recording-time proxies exist but are omitted once their age exceeds 2,000 minutes (33 hours 20 minutes).

`zone_prediction_service.resolve_zone_prediction` compares the worker's current clock with the registration/submission clock before producing a proxy. `pasig_ml_expiry_service.apply_zone_policy` reuses that resolver, then saves fixed fallback with the original deadline, which is null for these legacy records. Its cache also retains that unchanged null fallback. These records predate the new operational bridge, so no valid deadline was initially saved while the preview clock was eligible. Recent zones 19/20/21 do qualify and keep their saved model deadlines.

To verify the distinction without changing records, run the real resolver/model at each recorded issuance clock, call the cross-location comparator, then call the pure deadline chooser. Both return `ml_pooled`, `pooled_geographic_transfer=true`, recording-proxy provenance, deadlines within the 48-hour issuance bound and `already_overdue=true`. This is a reconstruction of the original model output, not a newly saved deadline, observed flood onset or evidence of physical subsidence. The research artifact remains unchanged.

The depth/location candidate has separate input gates: #17's old registration audit has no frozen numeric depth snapshot; #18 spans two barangays, so the single-locality depth candidate abstains. Neither prevents the already implemented shared Pasig baseline from transferring to those locations. Training from other locations is functioning; late operational initialization is the missing path.

**Required repair:** qualify current evidence/versions/review state at the real clock, calculate eligible original recording-proxy forecasts at their immutable issuance clocks, and permit recovery of an overdue saved-policy deadline without moving it to now. Preserve research preview staleness, actual unknown observation times, current evidence rejection, manual deadlines, pause/disable behavior and source facts. Bump the operational policy version so cached null fallback audits are reconsidered. Verify first worker execution after the age limit, repeat idempotence, new/reviewed/edited evidence rejection, unchanged zones 19/20/21 and event ending as Unconfirmed; deploy matching local/cloud API and workers before acceptance. A repaired worker would end these already-overdue records as Unconfirmed, never observed cleared.

Earlier bridge test counts and successful cloud executions remain valid, but did not cover this first-run-after-age-limit case. The earlier generic description of #17/18 as simply lacking timing evidence is superseded by this RCA. At that investigation checkpoint runtime correction remained open; it is now delivered as recorded above.

## Delivered behavior

The developer explicitly requested operational ML expiry after discovering that the earlier prediction work was research-only. A separate policy now connects those fitted estimates to saved zone deadlines. It does not relabel the artifacts as validated production models or change training admission.

- `automatic_expiry_enabled` pauses all scheduled expiry and deadline-based map/routing hiding.
- `pasig_ml_expiry_enabled` enables experimental ML expiry for eligible Pasig polygons, defaulting to true in the updated runtime. Disabling restores an applied zone's original fixed deadline on synchronization.
- Prefer the frozen-depth cross-location candidate when its source, clock, depth and geometry gates pass. Otherwise use an eligible pooled Pasig estimate. Outside Pasig, unsupported evidence, model errors and explicit staff deadlines retain fixed policy.
- Select p90 at the recorded issuance clock. Reject a deadline outside a 48-hour issuance bound. This bound is an operational limit, not a scientific maximum flood duration or calibrated confidence guarantee.
- Recording-time proxies remain labelled; actual observation times are not invented. No physical clearance or passability labels are inferred.
- Save the deadline in existing `flood_avoidance_zones.expires_at`; record source signature, original deadline, method, model hash, proxy basis, quantile, policy version and reason through `APPLY_ZONE_EXPIRY_POLICY` in existing audit storage.
- Source/model fingerprints prevent refreshes from extending unchanged deadlines. Policy writes preserve the source edit clock and have their own audit timestamp.
- Manual deactivation and reviewed clearance remain available. No inactive zone is resurrected. Due expiry ends the zone/event as **Unconfirmed**, not observed cleared.
- Linked current news uses the operational zone deadline for projection and maintenance. Immutable news decision/source deadlines and snapshots remain unchanged.

## Runtime connections

`pasig_ml_expiry_service` uses the internal evidence resolver. Protected HTTP prediction wrappers retain both Reports and Zones capability checks. New private read-only endpoint: `GET /api/v1/admin/zones/{zone_id}/expiry-policy`, typed and no-store. Database failures remain visible; qualified model/source failures produce an explicit fallback.

Official creation and staff/citizen approval apply policy after source audits exist. Reviewed follow-ups trigger reconsideration. The existing scheduled expiry path synchronizes active zones before due checks. Standalone local maintenance avoids news collection and paid AI providers:

```powershell
# From backend using existing dotenvx configuration:
node ../frontend/node_modules/@dotenvx/dotenvx/src/cli/dotenvx.js run -f .env -- venv/Scripts/python.exe -m scripts.run_zone_expiry --interval 60
```

VS Code normal Dev/Production start groups include **LANES: Zone Expiry Worker**. System Settings exposes **Use ML expiry for Pasig**. Spatial Operations zone details show the applied method, saved deadline, experimental status and recording proxy basis, with loading/error/retry states on desktop and mobile.

## Verification

**386 distinct backend/database checks passed:** 165 kernel/model/API/policy checks (163 combined plus two strict ML flag cases); 59 native Pasig prediction/settings/expiry cases; 162 native news lifecycle regression cases. The older news suite explicitly runs the ML-off fixed-timer contract. Separate native ML-on cases prove fitted deadlines, refresh idempotence, fixed restoration, pause/resume, proxy preservation, staff deadlines, permissions, map/routing eligibility, event ending and linked news coordination. No failing tests were removed. A standalone import cycle was fixed through lazy audit delegation in configuration writes; native checks passed again.

**10 distinct desktop/mobile scenarios passed:** cross-location, pooled/proxy and fixed fallback states, visible storage errors and independent ML setting persistence. Two repeated scenarios verify scrolled policy screenshots, without double-counting. TypeScript and scoped ESLint passed. Screenshots under ignored `frontend/test-results/ml-expiry-verified` and `ml-expiry-visual` use mocked API/session fixtures; they are not field accuracy evidence.

Disposable local PostGIS fixtures upgraded the existing Alembic head successfully and were removed. No SQLAlchemy definitions, migrations, requirements or package dependencies changed. Original fitted model/evaluation artifacts remain unchanged.

Native reproduction requires an empty disposable local database via `LANES_SETTINGS_TEST_DATABASE_URL`, named with prefix `lanes_settings_test_`:

```powershell
venv/Scripts/python.exe -m pytest tests/test_pasig_ml_expiry.py tests/test_zone_prediction.py tests/test_operational_settings_postgres.py -q
```

The news suite separately requires `LANES_NEWS_PUBLICATION_LIFECYCLE_TEST_DATABASE_URL`, an empty local database prefixed `lanes_publication_lifecycle_test_`:

```powershell
venv/Scripts/python.exe -m pytest tests/test_news_publication_lifecycle_postgres.py -q
```

Frontend:

```powershell
npx playwright test tests/system-settings.spec.ts tests/flood-review-suggestions.spec.ts --grep 'Pasig ML expiry|automatic expiry policy|automatic expiry storage' --workers=2
npx tsc --noEmit
```

## Actual local activation

The normal API on port 8000 was restarted. OpenAPI confirms the expiry endpoint and ML setting are loaded. A hidden local expiry worker runs every 60 seconds; first synchronization recorded zero due deactivations and applied model deadlines to existing zones:

| Zone | Applied method | Saved deadline (Asia/Manila) |
|---|---|---|
| 19 | Pooled Pasig ML | October 11, 11:27:52 AM |
| 20 | Pooled Pasig ML | October 11, 9:23:33 PM |
| 21 | Depth/cross-location ML | October 12, 3:46:36 AM |

Zones 17 and 18 did not qualify; existing null deadlines remain null with visible fallback reasons. A missing fixed deadline is not presented as a running timer. Zone 23 remains inactive. The local worker wrote operational policy/deadline audits to the normal configured database; **the shared settings record was not changed**. Deadlines were read back independently after commit. No new flood zones or training labels were created.

## Limits and remaining rollout

This is functioning experimental operational expiry. The baseline's 37 projections share only three subsidence summaries; the depth candidate has 36 qualified rows and incomplete holdouts. Neither model establishes field accuracy, calibrated p90 coverage or confirmed dry/passable roads. Artifact shadow/deployment flags and zero production training admission remain unchanged. Independent outcomes and prospective validation remain open.

## Actual shared cloud release — October 10, 8:36 PM

The developer answered **Local app and shared cloud worker**, explicitly authorizing the matching API/worker rollout. The release uses a checked backend working-tree snapshot, not a Git commit/push. A bounded source bundle contains application/scripts/runtime assets and existing dependency/migration definitions; local environments, secrets, test databases and replay data are excluded.

| Component | Verified release |
|---|---|
| Cloud Build | `8e8cf8cf-4693-41a5-a829-53b5da08a89a`, SUCCESS; Docker runtime-asset verification passed |
| Image | `gcr.io/lanes-project-508809/github.com/pu-roi/lanes:pasig-ml-expiry-20261010-1928` |
| Immutable digest | `sha256:4c48fb60f211e35753953e0577c8cc821b86621496d69b140c0041fdb4579fee` |
| API | `lanes-api-00067-zox`, healthy, 100% traffic; new expiry endpoint and ML schema loaded; anonymous private access returns 401 |
| Independent expiry job | `lanes-zone-expiry`, same image; `python -m scripts.run_zone_expiry`; existing runtime account/database binding, production environment, 1 GiB, 300-second timeout |
| Scheduler | `lanes-zone-expiry-every-minute`, ENABLED, every minute, Asia/Manila; existing scheduler account has job-scoped Run invoker permission |
| Matching news job | `lanes-news-discovery`, same image and existing scheduled arguments; existing three-hour collection Scheduler remains unchanged |
| Schema | Cloud read-only query confirms `d7e4b9a21c60`; no cloud migration was necessary or executed |

First expiry execution `lanes-zone-expiry-7vd5p` completed successfully (`expired=0`). Separate read-only cloud execution `lanes-zone-expiry-ll8hr` recomputed the fitted forecasts for zones 19/20/21: all three methods, model hashes and deadlines match the existing saved values exactly. Both automatic-expiry and Pasig ML flags read true without changing the settings record. First Scheduler-created expiry execution `lanes-zone-expiry-ncp2z` also completed successfully; Scheduler logs show HTTP 200 delivery at 8:35 and 8:36 PM. This establishes cloud maintenance without an open local app.

The old news worker had failed at 6 PM with `worker_failed`; the prior logs expose no deeper cause. Matching release execution `lanes-news-discovery-cx8f8` now completes with outcome `completed`, zero new source publications and zero estimated-zone activations. This is worker acceptance, not a claim of new live article plotting or field accuracy. Independent expiry no longer depends on RSS/provider success.

Normal local API/worker continue running. The local UI is tested on mobile/desktop and exposes policy controls. **The cloud frontend was not released in this requested local-app/shared-worker scope**; use the local updated UI for the new control. Root `cloudbuild.yaml` now updates the independent expiry job on future normal backend releases. No Git commit/push was requested or performed for this operational implementation/release. See [rollout and rollback](../guides/system-settings-rollout.md#october-10-pasig-ml-cloud-expiry-release).

Related: [Decision 27](../decisions.md#27-experimental-pasig-ml-deadlines-as-an-operational-expiry-policy), [cross-location plan](../plans/cross-location-flood-prediction.md), [earlier fixed-timer investigation](automatic-expiry-toggle-20261010.md).
