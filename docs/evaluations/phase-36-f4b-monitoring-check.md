# Phase 36 — F4b monitoring verification

> **Last Updated:** October 03, 2026, 11:23 AM
> Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer approved four additive telemetry tables on October 3. Implementation and rollout are documented in the [monitoring plan](../plans/news-monitoring-telemetry-plan.md).

| Check | Result |
| --- | --- |
| News discovery, open-search, browsing, results, saved extraction, processing, telemetry, ingestion and placement regressions | 214 passed; one existing `python_multipart` deprecation warning. |
| Disposable PostgreSQL extraction queue at new head | 4 passed. Updated test cleanup explicitly includes telemetry children/parents; only dedicated test databases are accepted. |
| Fresh full PostgreSQL migration chain and telemetry round-trip | 1 passed. Upgrade/head → downgrade `f29b6c8d104e` → upgrade/head → repeated upgrade. Prior article body preserved; new model/migration columns, nullability, checks and indexes agree. |
| Local migration | `alembic upgrade head` succeeded; current revision `c5a7e9d2104f`. |
| Local history service reads | Both paginated services read successfully with zero recorded attempts and zero new attempt rows. |
| Frontend full TypeScript and scoped ESLint | Passed, including `NewsTelemetryHistory`, drawer/API and news-intelligence fixtures. |
| Whitespace check | `git diff --check` passed. |

New backend cases verify staff/commuter/anonymous guards, stable pagination, sanitized 503, partial feed failure, duplicate candidate counting, preserved earlier feed commits, zero-hit versus throttle outcomes, idempotent finalization, atomic failure rollback, worker interruption and fallback input capture across revisions. Stored telemetry has no article body or raw provider exception.

The first broad run passed 211 cases and found one old collector fixture missing new tables. Updating its isolated schema resolved that failure; the final complete run passed all 214. Earlier sandbox temporary-folder failures were avoided using normal temporary-folder access. Both disposable PostgreSQL databases were removed after verification.

Browser tests and development servers were not started. Prepared fixture cases cover lazy history loading, GET-only pagination, unsafe alternate URLs, error/retry, 1440px desktop, 390px mobile, 320px narrow and landscape with Escape/focus restoration. These are not recorded as executed visual acceptance.

**Production follow-up:** approved migration `c5a7e9d2104f`, API/collector and Firebase releases succeeded. Normal collector execution records current attempts. Thirteen deployed desktop/mobile asset checks pass with mocked API/session responses; TypeScript passes. See [release evidence](phase-36-news-content-quality-investigation.md#completed-production-release). Remaining: developer desktop/mobile acceptance and publication timestamps/lifecycle contract for delay measurement. Older monitoring runs are not synthesized; history GET never starts collection, lookup or recovery.
