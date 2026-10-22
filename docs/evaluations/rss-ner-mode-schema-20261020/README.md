# Durable NER mode schema — local verification

> **Last Updated:** October 20, 2026, 3:44 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Result: approved schema step implemented and verified locally; 66 checks pass.** Revision `e8a6f1c2d903` follows `d7e4b9a21c60` in one 45-revision chain. The SQLAlchemy model and migration now allow `rules_only` and `ner_rules_v1`. Application writers still use `rules_only`. Automatic NER processing, native API readers, UI integration and shared/cloud migration are pending. [Aggregate verification](summary.json) · [Approved proposal](../../plans/rss-ner-processing-mode-schema-proposal.md) · [Current roadmap](../../task_plan.md#phase-c--connect-automatic-article-processing).

## Exact change and transactional protection

Only the allowed-mode check changes to `CHECK (mode IN ('rules_only', 'ner_rules_v1'))`. Its database name remains `ck_news_extraction_runs_rules_only_mode`, finalized with Alembic `op.f` to avoid naming-convention duplication. Columns, application defaults, server defaults, nullability, indexes, foreign keys, other constraints, triggers, immutable versions, historical values/links and `(article_version_id, pipeline_version, mode)` uniqueness remain unchanged. No table, backfill or conversion is added.

Both directions acquire `ACCESS EXCLUSIVE` before inspecting rows or replacing the check, within PostgreSQL's migration transaction. SQL blocks validate the exact named, local, validated mode-only check and its inspected PostgreSQL 15 canonical expression. Missing, unvalidated or drifted definitions fail explicitly. Each direction refuses any row whose mode is distinct from `rules_only`; upgrade therefore refuses unexpected preexisting native rows, and downgrade refuses pending, failed and completed native rows. Refusals retain rows, links, the current check and Alembic revision. No rows are deleted or relabeled. Generated offline SQL contains the same guards and was executed against the disposable server.

After native rows exist, application rollback must preserve the wider check and method-aware consumers. Do not downgrade or run incompatible workers by deleting evidence or pretending neural output is legacy output. Shared/cloud migration and activation require their later release decision.

## Verification evidence

| Group | Passed checks | Evidence covered |
|---|---:|---|
| Focused PostgreSQL schema suite | 23 | Fresh/repeated upgrade, reflected model compatibility, complete fictional legacy row/link preservation, both modes/default, uniqueness, invalid values and unchanged lease/status/attempt/result rules, immutable snapshots, legacy rollback/re-upgrade, native-row and drift refusal, offline SQL, concurrent writer protection |
| Existing publication-storage suite | 37 | Historical publication/evaluation/decision/link behavior; single-head assertion now accepts descendants while retaining historical ancestry |
| Existing extraction-queue PostgreSQL suite | 4 | Existing leases, attempts, immutable capture, queue ownership/history behavior |
| Qualification-harness software checks | 2 | Both success and setup failure stop only the owned disposable container |
| **Total unique checks** | **66** | Independent receipt/source/container verification adds no inference |

The 64 PostgreSQL/regression cases passed in 117.63 seconds. Each group used guarded, separately created disposable databases; focused fixtures additionally created fresh databases per scenario. The runner set the disposable URL before application imports, sanitized its environment and avoided the configured development/shared database. All article/history/native fixtures were fictional. The two harness tests were also retained as JUnit evidence; repeated execution does not increase the unique count.

PostgreSQL 15 / PostGIS 3.4 used the inspected local image ID `sha256:3f4a5d48e0be9580ed70ed618cd039ce57bbb2dd113053d3836e28513f1f87cd`. Its dedicated labeled container used generated private credentials, a temporary filesystem and an ephemeral loopback-only port. Independent inspection confirms it is stopped with no live server process. Raw logs, connection state, credentials and receipts remain ignored/private.

| Small-fixture measurement | Seconds |
|---|---:|
| Empty database → head | 2.391 |
| Predecessor → expanded mode check | 0.203 |
| Legacy-only downgrade | 0.218 |
| Legacy-only re-upgrade | 0.234 |
| Contended downgrade, including guard refusal | 0.313 |

These include local harness/Alembic overhead and are not production estimates. The contention test observed the migration waiting for `ACCESS EXCLUSIVE` behind an uncommitted native insert. After the writer committed, downgrade refused and preserved the inserted row/head. The last duration is total operation time, not an isolated lock-wait measurement. Production table size, lock contention and release scheduling need their own review.

## Frozen runtime preservation

Both failed one-/two-GiB runtime attempts and the passing three-GiB artifacts, snapshots, manifests and receipts remain unchanged. There were **zero inference runs** in this schema task. Relative to the three-GiB frozen 1,040 source/asset bindings, the only authorized current-source difference is the exact allowed-mode line in `backend/app/models/news.py`; the other **1,039** bindings still match. The historical frozen model copy is not changed, and its old hash is not rewritten to claim current-file equality. This schema verification records that explicit exception separately. No model/rule/tokenizer, runtime, dependency, normal build or cloud resource change occurred.

## Reproduction and remaining gates

Use `backend/.venv/Scripts/python.exe -B backend/scripts/verify_news_ner_mode_schema.py` with `prepare`, then `test`, each followed by `--output` and the same **new absent directory under ignored** `backend/training/flood_ner/artifacts/`, with a `news-ner-mode-schema-` name prefix. Run from the repository root with the inspected image available locally. The database-test command records 64 cases and stops the owned container even if setup fails. Separately run the two software-only cases in `backend/tests/test_news_ner_mode_schema_runner.py` with `--noconftest -p no:cacheprovider` and `--junitxml=<output>/runner-tests.xml`; retain its exit code as `runner-test-exit.json` containing `{"returncode": 0}` only after it succeeds. Capture its stdout/stderr privately too. Then run the script's `verify --output <output>` command to audit all 66 receipts, stopped container and source preservation without database access or inference. The verifier writes new files exclusively; do not repeat it into a finalized package.

Do not point the opt-in PostgreSQL test variable at development/shared storage. The completed package is evidence to preserve, not an invitation to overwrite it or rerun neural qualification.

Phase C still needs method-aware readers and worker isolation, RSS/body admission, native-result serialization, runtime/queue budget integration, extraction wiring, source checking and publication compatibility. The contract's 23 full integration scenarios remain pending; the 23 focused schema cases are a different suite. No API/type change, collection-policy change, shared/cloud DDL, deployment or automatic NER activation is delivered here.
