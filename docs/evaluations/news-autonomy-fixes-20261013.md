# Automatic news cadence repair — October 13

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Main deployment, 285 Linux release checks, matching API/job/frontend rollout and natural post-release Scheduler collection verified.

## Completed deployment and automatic operation

[PR #136](https://github.com/pu-roi/LANES/pull/136) merged to main **5c6da286397399fa42c757df287074d121583bfc**. Existing Cloud Build **b24bfb9c-d8d8-4f5b-8bbc-5df73542f570** completed successfully at **11:29:17 PM PHT on October 13**: **285 Linux tests passed**, migrations and the existing release worker succeeded before traffic promotion. API revision `lanes-api-build-b24bfb9c-d8d8-4f5b-8bbc-5df73542f570` serves **100%**; API/news/expiry use the same main image, digest `sha256:5560640708bf996c5a4fc6cc7bc87769b281bb09d5b55efffbde2e0f73235f38`. Automatic frontend rollout `lanes-frontend-build-2026-10-13-004` also serves **100%**, using its existing backend URL. No redundant manual frontend build was started.

The **11:30 PM** natural Scheduler delivery returned HTTP 200 at **11:30:29 PM**. It dispatched execution **lanes-news-discovery-cvfjq**, which completed successfully at **11:31:10 PM** with zero inference requests and no pipeline errors. The persisted cycle read **120 feed entries** and no eligible new flood candidates; no fresh current-news activation is claimed. Latest collector start **11:30:40 PM** follows the prior **11:15:19 PM** collection: the next risk due slot is correctly **11:45 PM**, rather than an additional thirty-minute wait. This is observed automatic dispatch, distinct from Cloud Build's release-check execution.

Real local backend 8000, frontend 3000 and navlanes.live public/authenticated APIs all return the same active zone IDs **58–63**, source_rules mode, enabled collection/processing/publication, completed latest cycle, next due **11:45 PM**, and **automatic_expiry_enabled=false**. Current-policy queues have no pending/processing/retry/failed work. The original five historical news zones, source dates and existing citizen zone remain intact for video recording. Live map and source drawer load through the actual deployed APIs; source depth and September observation/publication dates remain visible.

Sanitized verification and real live-map screenshot are saved under ignored `data/news-autonomy-fixes-20261013/`: `pagasa.html`, `deployment-verification.json`, `api-verification.json`, `live-map-after-deployment.jpg`. The local backend was restarted on its existing 8000 port to load the same repair; a first bind attempt collided with the previous listener, then the original listener was stopped and the same port recovered. No second port/service remains.

The developer authorized applying the LLM-free readiness fixes and deployment. They explicitly instructed that automatic expiry remain disabled to preserve September zones for a video presentation. No setting, source date, incident record, credential, schema or dependency was changed.

## Changes and verification

- Added a shared quarter-hour collection cadence for the 15/30/60-minute policy. Controller, worker recheck, System Settings and News Intelligence now derive the same due slot from the original collection timestamp without rewriting it. A collection starting at 9:45:20 PM is eligible at 10:00 PM in risk mode, rather than missing that tick and waiting until 10:15 PM.
- Known Cloud Run operations are reconciled on the next tick even when reservation age is just under fifteen minutes. Unconfirmed starts keep the existing grace period, and running/unknown executions still prevent duplicate dispatch. Advisory locks and durable reservations are unchanged.
- PAGASA parsing now separates indented consecutive bulletins before resolving dates/locations. An archived stale sibling does not mark an otherwise current section unavailable; malformed or undated notices remain uncertain. Real captured official HTML confirms that the recurring missing-timestamp condition comes from the undated rainfall notice, not a network outage. That notice is deliberately not assigned a fabricated issue date.
- Added regressions for the exact recorded jitter and delayed collection start, all three intervals, repeats, future clocks, midnight, immediate reconciliation, unknown/running execution protection, multiple PAGASA dates and missing-date uncertainty. Updated the status due-time expectation to the actual scheduler slot.
- The deployed-image verification step now includes the new cadence regressions. The complete existing release test selection plus these checks passes **285 tests** in the existing installed Python environment. There are no new dependencies or migration files.

## Deployment scope

Release was prepared on `codex/news-autonomy-fixes` from main 5febb73 in a managed Git checkout. It reused the existing backend runtime for tests; primary development remains 3000/8000 connected to the same Cloud SQL database. Unrelated in-progress FeedPage edits and the local-only connected replay helper are excluded from the release code. The established main Cloud Build verified Linux tests, existing migrations and a real news worker before promoting API traffic; existing cloud services/jobs are reused.

## Preserved limits and operating choices

This release repairs cadence and advisory isolation; it does not claim every article/location becomes a polygon. Publisher challenges, undated advisories, missing qualified boundaries and ambiguous roads still require accessible evidence or staff exception review. Source_rules has no LLM inference requests and is not independent field verification. The five historical demo zones remain active while operator-disabled expiry is off; this is intentional for video recording. Credential replacement remains an operator task. [Measured pre-repair audit](news-autonomy-audit-20261013.md), [historical demonstration](news-connected-demo-20261013.md).


## roi-branch save verification — October 13, late evening

The requested branch save includes the already-deployed cadence source, final deployment receipts in docs, the approved connected reconstruction extension and existing FeedPage edits. All **292 backend tests pass** (the 285 release selection plus seven connected-reconstruction guards), using the existing encrypted-environment launcher and a non-connected test engine. TypeScript passes. Feed scoped lint has **three pre-existing state-in-effect errors and three warnings**; the baseline has the same three effect errors plus other errors removed by the working copy. Mobile load-more error feedback is logged as an open UI issue. Existing whitespace warnings remain in the preserved Feed edits. No dependency, model or migration file changed. This branch save does not establish deployment or complete responsive acceptance of the separate Feed changes. [@roicambe](https://github.com/roicambe) (Roi Cambe)
