# Automatic news cadence repair — October 13

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Implementation and 285 native release checks passed; cloud rollout pending.

The developer authorized applying the LLM-free readiness fixes and deployment. They explicitly instructed that automatic expiry remain disabled to preserve September zones for a video presentation. No setting, source date, incident record, credential, schema or dependency was changed.

## Changes and verification

- Added a shared quarter-hour collection cadence for the 15/30/60-minute policy. Controller, worker recheck, System Settings and News Intelligence now derive the same due slot from the original collection timestamp without rewriting it. A collection starting at 9:45:20 PM is eligible at 10:00 PM in risk mode, rather than missing that tick and waiting until 10:15 PM.
- Known Cloud Run operations are reconciled on the next tick even when reservation age is just under fifteen minutes. Unconfirmed starts keep the existing grace period, and running/unknown executions still prevent duplicate dispatch. Advisory locks and durable reservations are unchanged.
- PAGASA parsing now separates indented consecutive bulletins before resolving dates/locations. An archived stale sibling does not mark an otherwise current section unavailable; malformed or undated notices remain uncertain. Real captured official HTML confirms that the recurring missing-timestamp condition comes from the undated rainfall notice, not a network outage. That notice is deliberately not assigned a fabricated issue date.
- Added regressions for the exact recorded jitter and delayed collection start, all three intervals, repeats, future clocks, midnight, immediate reconciliation, unknown/running execution protection, multiple PAGASA dates and missing-date uncertainty. Updated the status due-time expectation to the actual scheduler slot.
- The deployed-image verification step now includes the new cadence regressions. The complete existing release test selection plus these checks passes **285 tests** in the existing installed Python environment. There are no new dependencies or migration files.

## Deployment scope

Release is prepared on `codex/news-autonomy-fixes` from main 5febb73 in a managed Git checkout. It uses the existing backend runtime for tests; no additional local server, port, database or container is started. Primary development remains 3000/8000 connected to the same Cloud SQL database. Unrelated in-progress FeedPage edits and the local-only connected replay helper are excluded from the release code. The established main Cloud Build will verify Linux tests, run existing migrations and the real news worker before promoting API traffic; existing cloud services/jobs are reused.

## Preserved limits and operating choices

This release repairs cadence and advisory isolation; it does not claim every article/location becomes a polygon. Publisher challenges, undated advisories, missing qualified boundaries and ambiguous roads still require accessible evidence or staff exception review. Source_rules has no LLM inference requests and is not independent field verification. The five historical demo zones remain active while operator-disabled expiry is off; this is intentional for video recording. Credential replacement remains an operator task. [Measured pre-repair audit](news-autonomy-audit-20261013.md), [historical demonstration](news-connected-demo-20261013.md).
