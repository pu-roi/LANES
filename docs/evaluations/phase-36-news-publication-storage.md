# Phase 36: Approved news publication storage

> **Last Updated:** October 05, 2026, 3:17 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Scope:** Five approved additive models, migration and isolated local PostGIS verification. No automatic publication, frontend edits, cloud migration, push or deployment.

## Authorization and implementation

The developer explicitly approved the exact five-table proposal and disposable local PostGIS migration verification in the continuation chat. This supersedes the earlier pending-schema approval for this proposal; it does not enable production publication or approve an affected-geometry policy.

New model module: `backend/app/models/news_publication.py`, exported through `app.models`. New migration: `d7e4b9a21c60`, following `c5a7e9d2104f`. Existing table columns, source enums, extraction results, report/event/zone geometry and API routes are unchanged. No new dependency is imported beyond the already declared backend stack.

| Table | Implemented storage safeguards |
| --- | --- |
| `news_claim_cases` | Stable integer identity, nonnegative revision with default zero, timezone-aware creation clock; no duplicated public state. |
| `news_claim_sources` | RESTRICT links to case and immutable extraction run; unique run/ordinal; nonnegative ordinal; lowercase SHA-256; immutable binding. Services must still verify ordinal/hash against completed schema-valid extraction. |
| `news_claim_evaluations` | Unique source/policy hash, `attempt_count` bounded 0–5, leased processing state, completed result/time, failed error/time, retry due/error, named safe error codes; completed and failed rows are immutable. |
| `news_claim_decisions` | Unique case/revision and globally unique UUID request; actor identity checks; state/operation enums; finite active observation/expiry ordering; object snapshot bounded to 65,536 UTF-8 bytes; safe reason code. Automatic evaluate inserts require a completed evaluation. |
| `news_claim_zone_links` | Unique decision/zone; partial unique creation owner per zone; multiple historical support links; links require an active-zone decision. Existing operational geometry remains authoritative. |

All new foreign keys use `ON DELETE RESTRICT`. Source bindings, decisions and links reject UPDATE/DELETE; terminal evaluations reject UPDATE/DELETE. Their four history tables also reject TRUNCATE, including CASCADE, so row-trigger protections cannot be bypassed by ordinary truncation. Explicit migration downgrade drops only the new tables and their three functions; it is destructive to new publication history and is not a recommended production rollback.

Relationships expose source→extraction, decision→evaluation/actor, case→sources/decisions and link→zone without altering existing model fields. No automatic actor is fabricated. Evaluation references may support a clearance decision for a different target case; the future service must establish actual continuity rather than enforcing an incorrect same-case requirement.

This delivery does not implement snapshot Pydantic validation, supported claim binding, auditor transport, lease claiming, locked decision/revision writes, publication gates, current support reads, refresh/clearance matching, Unconfirmed/Cleared public projection, expiry maintenance, endpoints or the frontend. Database constraints are storage safeguards, not permission to activate a flood zone.

## Verification

**60 distinct focused tests passed:**

- 37 in `tests/test_news_publication_storage.py`.
- 18 existing extraction unit checks in `tests/test_news_processing.py`.
- Four native PostgreSQL extraction checks in `tests/test_news_processing_postgres.py`.
- One full telemetry migration round-trip in `tests/test_news_telemetry_migration.py`.

The publication fixture refuses non-loopback connections, non-test database names and databases already containing application tables. It performs the full historical migration chain to the preceding head, inserts synthetic article/version/completed-extraction and operational-zone evidence, then applies `alembic upgrade head` twice. It verifies only five added tables with no seeded public decisions/zones, downgrade/re-upgrade and unchanged original row JSON, including geometry and expiry. Reflected columns, types, nullability, CHECK names, indexes and RESTRICT foreign keys match the new ORM definitions.

Database checks cover malformed hashes/ordinals, duplicate binding, lease/result/retry/error states, successful finalization, immutable completed/failed evaluations, actor rules, missing/reversed expiry, inactive clear/reject/expire operations, bounded snapshots, duplicate request/revision, automatic audit prerequisites, independent zone support/unique creation ownership, alert isolation, protected parent deletion and rejected history truncation. Existing native queue tests also verify concurrent enqueue, skip-locked claiming and lost-lease ownership at the new head.

The first run had one assertion-format failure: SQLAlchemy's default reflected TIMESTAMP string omitted its timezone qualifier. Compile both types with the PostgreSQL dialect to compare them correctly; no timestamp schema repair was needed. Corrected final publication/extraction run: **55 passed**. Native extraction/telemetry run: **5 passed**. The existing `python_multipart` pending-deprecation warning remains.

The extraction PostgreSQL fixture now checks the current Alembic head and deletes only dedicated extraction-test rows in dependency order. Parent TRUNCATE is incompatible with the new RESTRICT publication foreign keys even when child tables are empty; it neither truncates nor deletes publication history.

To reproduce, provision fresh disposable local databases, apply the current head to the extraction-test database, and set the existing opt-in variables without committing connection strings:

```powershell
# TEST_NEWS_PUBLICATION_DATABASE_URL: lanes_publication_test_*, fresh and loopback
python -m pytest tests/test_news_publication_storage.py tests/test_news_processing.py -q
# LANES_NEWS_TEST_DATABASE_URL: lanes_p3_verify_*, migrated to head
# TEST_NEWS_TELEMETRY_DATABASE_URL: lanes_telemetry_test_*, fresh
python -m pytest tests/test_news_processing_postgres.py tests/test_news_telemetry_migration.py -q
```

Only newly created disposable databases were used; all four created test databases were removed after verification, including the first assertion-failure run. The normal `lanes` application database, existing replay databases, cloud database and configuration were not migrated by this task. Commit/push/release remain separate.

## October 5 pre-push checkpoint

The requested `roi-branch` checkpoint repeated migration/storage/queue verification against the final pending code: **59 checks passed** across `test_news_publication_storage.py` (37), `test_news_processing.py` (18) and `test_news_processing_postgres.py` (four). The queue database completed the full `alembic upgrade head` chain to `d7e4b9a21c60`; the publication fixture additionally repeated upgrade and downgrade/re-upgrade while preserving synthetic prior evidence. Both newly created uniquely named local disposable databases were removed in final cleanup. Normal application/replay/cloud databases remain untouched.

No dependencies changed. This is a separate rerun, not 59 additional distinct tests to add to the earlier 60 storage checks or 226 placement checks; the 18 extraction unit checks overlap placement verification. Earlier TypeScript/scoped lint and 14 browser cases/two project-inapplicable skips remain the UI evidence for unchanged code. Senior planner synchronization does not establish live publication, model training or deployment. Git commit/push completion is reported separately after the command result. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

## Local Docker startup recovery

Docker Desktop 4.91.0 initially failed to rename `sailor-ingest.sock`, then `docker-secrets-engine/engine.sock`. After a verified Docker process stop, preserved both runtime directories under new `.stale-20261005-*` names and recreated them together before a single launch. `docker ps` then showed the existing PostGIS and Valhalla containers, and native migration tests succeeded. No factory reset, uninstall, WSL distro deletion, Docker volume removal or secret-content inspection occurred.

The filesystem/socket failure and directory-preservation workaround resemble the first-hand [Docker issue 554](https://github.com/docker/desktop-feedback/issues/554); this is a local recovery, not proof of an upstream fix or guaranteed recurrence prevention. [BUG-100](../others/bug-log.md#bug-100-local-docker-startup-fails-on-stale-windows-unix-sockets) records exact runtime paths and limitations.

## Next slice

Repair and test auditor transport/context and structured place/status/time/depth evidence, then implement immutable claim binding and leased evaluations. Follow the [backend readiness contract](../plans/news-publication-readiness-plan.md) for atomic decisions, safe public alerts, the accepted two-hour fallback and matched-clearance handling. Supported affected geometry and remaining retention/routing choices still govern zone activation. The subsequent [v11 preview/aura implementation](phase-36-disconnected-news-placement.md) resumes that explicitly authorized frontend slice; F6/F7 decision/publication integration still requires its backend contracts.
