# Proposal: durable NER-backed news processing mode

> **Last Updated:** October 20, 2026, 7:56 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: explicitly approved, implemented and verified in disposable local PostGIS.** The user authorized the focused model/migration implementation and local verification on October 20. This is the database portion of the [Phase A integration contract](rss-ner-integration-contract.md); shared/cloud DDL and deployment remain outside that authorization. [66-check verification report](../evaluations/rss-ner-mode-schema-20261020/README.md). Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Exact requested change

Before this approved migration, `backend/app/models/news.py` constrained `news_extraction_runs.mode` to `rules_only`, using the named `rules_only_mode` CheckConstraint and the existing `(article_version_id, pipeline_version, mode)` uniqueness rule.

The approved implementation replaces only that allowed-mode check with:

```sql
CHECK (mode IN ('rules_only', 'ner_rules_v1'))
```

Keep the existing constraint name to minimize unrelated DDL and keep mode length 30, all existing columns/defaults/nullability, result JSONB, unique constraints, indexes, foreign keys, lease/status/attempt constraints and historical rows unchanged. The inspected finalized database name is `ck_news_extraction_runs_rules_only_mode`; revision `e8a6f1c2d903` preserves it with `op.f`, without double-prefixing.

No new table, mode column, reference-data seed, geometry change, full-text duplication or data backfill is requested. The versioned native graph and derived compatibility projection live together in the existing immutable result JSONB as specified by the contract. They are one run artifact, not a second authoritative relational fact store. Nothing is relabeled from legacy to neural. The existing default remains `rules_only`; selection of the new method is explicit application configuration in a later implementation.

## Application compatibility accompanying the migration

The DDL alone is insufficient. Later implementation must:

- Extend backend/frontend method literals and typed saved-result unions for `ner_rules_v1` / `lanes-news-ner-result-v1`; preserve the complete envelope rather than silently discarding unknown fields.
- Parameterize enqueue, current pipeline identity, capture/lease claims, latest-method readers, evaluation seeding and correction reconciliation. Bind model/tokenizer/rules/runtime/projection/geography identities into the new pipeline fingerprint.
- Keep legacy mode/result semantics unchanged. Old and new runs for the same input can coexist under different method/pipeline identity; duplicate new-mode enqueue returns the same run.
- Dispatch versioned source checking by persisted run mode. Existing `rules_only` source/fact equality is not a hidden neural eligibility requirement.
- Carry stable graph-to-claim bindings through immutable claim hashes, publication source rows and reader detail routes. No historical evaluation/decision is rewritten.

Do not add a general unknown-mode fallback. Unknown strings, native discriminator/mode mismatch and mode spoofing are rejected. No production method switch occurs as part of a schema migration.

## Approved upgrade sequence and later release ordering

1. Identify the current Alembic head and actual constraint name on a dedicated disposable local PostgreSQL/PostGIS database; do not generate unrelated autogenerate changes from the dirty working tree. Author one focused migration plus the corresponding model-check change.
2. Acquire `ACCESS EXCLUSIVE` within the migration transaction before validating the exact named check and legacy-only rows, then replace the check atomically. SQL guards fail on missing/drifted definitions or unexpected nonlegacy rows; the same protections exist in generated SQL. Do not rewrite rows or indexes.
3. Test `alembic upgrade head` from an empty disposable database and from its predecessor migration with representative legacy extraction/history/source rows. Confirm one clean head and dependency availability. No shared/cloud migration is authorized by Phase A.
4. Release method-aware API readers, normal/scheduled/manual processing entry points, source validators, maintenance tools and matching frontend while new-mode writes are disabled. Drain old in-flight workers; do not trust their lack of a mode filter or ability to parse unknown result fields.
5. Only after Phase B runtime parity, Phase C acceptance and the separate release decision, enable the new method for newly captured eligible work. Do not silently reprocess the historical backlog or reset prior attempts/decisions. Any retained pending legacy queue needs an explicit drain plan before the switch; old completion must not displace the selected current method.

Mixed versions may serve only while **all writers remain rules-only** and older consumers cannot see unhandled native results. Once new-mode writes begin, every reader/worker that can encounter them must understand the discriminator and method. A schema that accepts both modes does not make an old API/worker safe.

## Downgrade and rollback restrictions

Application rollback normally means disable/drain new processing and keep method-aware readers plus the additive database check. Preserve native artifacts and their source/evaluation/decision links; never delete or convert them to rules-only to make rollback pass. Do not start an older incompatible worker against a database containing native runs.

A downgrade restoring `CHECK (mode = 'rules_only')` must first count rows with any other mode and refuse with an explicit diagnostic if any exist, including pending/failed/native-only rows. If zero exist, restore the old check atomically. The downgrade does not purge artifacts, relabel methods, drop links or hide data. Roll-forward is required after native rows exist unless a separately approved preservation/recovery plan makes a full rollback safe.

## Verification coverage and remaining consumer gates

| Check | Required outcome |
|---|---|
| Fresh upgrade / predecessor upgrade | `alembic upgrade head` succeeds in disposable PostGIS; historical row bytes and links unchanged; one clean head |
| Allowed modes | Legacy and `ner_rules_v1` accepted; unsupported, blank and null modes rejected under existing nullability/checks |
| Run identity | Duplicate input/pipeline/mode remains one row; legitimate legacy and native runs coexist |
| Existing constraints | Invalid lease/status/attempt/completed-result cases still fail; indexes/foreign keys/defaults unchanged |
| Typed round trip | Both methods survive API/Pydantic/JSON/frontend reading with complete native graph and clear method identity |
| Worker isolation | Legacy worker cannot claim native jobs; native worker cannot relabel or consume legacy jobs accidentally |
| Staged release | New writes remain off until every consuming process is compatible and runtime/acceptance gates pass |
| Downgrade without native rows | Restores predecessor check without changing rows |
| Downgrade with native rows | Refuses before destructive DDL; every native artifact and source/decision remains intact |

**Historical Phase A verification performed:** inspected the current model, CRUD mode literals, typed result/readers and downstream consumers; prepared this proposal and linked it to the integration contract. **No migration/model change, Alembic execution, database check, inference or runtime acceptance test was performed.** That was the Phase A state; the later explicit schema approval and local verification below supersede its approval gate.

## Approved schema delivery — October 20, 2026

Revision `e8a6f1c2d903` follows `d7e4b9a21c60`; one 45-revision chain remains. Fresh/repeated upgrade and legacy downgrade/re-upgrade pass. Fictional complete legacy rows, publication/source/evaluation/decision links and unaffected schema objects remain identical. Unsupported/blank/null modes, duplicate identities and existing invalid lease/status/attempt/result states are rejected. Pending, failed and completed native rows refuse downgrade atomically; missing/drifted constraints refuse migration. A concurrent insert demonstrates exclusive-lock ordering, and generated SQL executes with the same guards. **66 checks pass:** 23 focused schema, 37 existing publication-storage, four existing queue and two harness-cleanup checks. [Measurements, preservation and reproduction](../evaluations/rss-ner-mode-schema-20261020/README.md).

The DDL rows in the table above are locally verified; **typed API/frontend round trip, worker isolation and staged activation remain Phase C/release gates**. JSONB storage acceptance is not API compatibility. Application writers still use `rules_only`. The owned loopback container is stopped; no shared/cloud migration, native processing switch, new dependency or neural inference occurred. Historical runtime artifacts remain unchanged, with the approved current SQLAlchemy mode-check delta recorded separately.

## Later consumer checkpoint — C1

[93 checks](../evaluations/rss-ner-method-boundary-20261020/README.md) verify queue method isolation and backend native-history serialization. This closes that foundation, not full API/frontend native-group compatibility, source/projection qualification or activation. Normal writers remain `rules_only`; schema/rollback behavior above is unchanged.
