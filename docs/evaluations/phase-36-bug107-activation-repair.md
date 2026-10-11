# Phase 36: BUG-107 activation and refresh repair

> **Last Updated:** October 05, 2026, 10:59 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Repaired and verified locally on `roi-branch`; operational integration remains open.

BUG-107's two original native failures now pass. The repair also fixes the previously masked decision-operation constraint and refresh-link ordering failures. **240 distinct checks passed across twelve suites**. BUG-108 zone metadata, BUG-109 retained support and BUG-110 trusted current footprint acceptance remain open; this checkpoint does not complete automatic article-to-zone routing.


## Latest trusted-footprint follow-up

BUG-107/108/109/110 are now repaired locally with **398 distinct passing checks**. Exact current incident/staff approval, explicit SRID, full locality/component containment and safe unsupported-renewal fallback pass. Actual current footprint provisioning, automatic worker/map integration and staging/PWA acceptance remain open. The findings and test counts below preserve earlier checkpoints. [Latest verification](phase-36-trusted-footprint-contract.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


## Later metadata/support repair

This report preserves the earlier BUG-107 checkpoint. BUG-108/109 have since been repaired locally; **289 distinct checks pass** in the newer verification. BUG-110 and actual worker/map/staging/PWA integration remain open. [Current verification](phase-36-zone-metadata-support-repair.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Root causes and research

The activation helper applied strict Python-object validation to stored JSON and swallowed the resulting error, leaving `_public` without an audit. JSON arrays and date strings need the strict JSON validation path already used by `_load`. This behavior is documented in [Pydantic 2.7 JSON parsing](https://docs.pydantic.dev/2.7/concepts/json/); the installed and declared version is 2.7.4. Strict validation remains enabled.

Once decoding was repaired, native PostGIS tests exposed two additional blockers. The helper wrote `activate_zone`, which the approved decision-operation constraint does not allow. Qualified zone refresh inserted supported links before writing their active decision, violating the existing link trigger. The repair uses existing evaluate/correct operations and writes the refresh decision before its support links. No database constraint was changed.

## Resulting service contract

- `activate_operational_footprint` requires `expected_revision` and reuses `_load` to validate immutable evaluation, source, policy, pipeline/auditor, input, claim and current observation evidence. Malformed or missing audits return safe rejection reasons. Snapshot and public identities are checked against the current case and decision.
- Current active/rising evidence, independently confirmed canonical depth and vehicle passability are rechecked. Expired observations, newer matched wet observations and historical clearance reject operational writes.
- The request digest includes case/revision, actor, geometry hash, caller source/checksum, optional parent hash and policy/pipeline/auditor identity. An exact retry returns its original decision even after the observation expires, creates no additional rows and does not extend expiry. Reusing its UUID with a changed accepted payload returns an identity conflict.
- Request locking precedes immutable evidence reads; incident locking precedes the case lock/revision recheck, matching existing publication/staff ordering. Event, zone, decision and link writes share the caller's transaction; a rollback removes all partial writes.
- Optional typed `operational_provenance` is private metadata in the existing decision JSONB snapshot. Qualified zone refresh, clearance and expiry retain it. It is absent from the public projection. Old v1 snapshots remain readable. Attribution hashes are not a source-trust verdict and do not complete BUG-110.

Changed application files are [publication service](../../backend/app/services/news_publication_service.py), [publication snapshot schema](../../backend/app/schemas/news_publication.py), and [native lifecycle tests](../../backend/tests/test_news_publication_lifecycle_postgres.py). SQLAlchemy models, Alembic definitions, requirements and frontend code were not modified.

## Verification

| Scope | Distinct successful checks | Result |
|---|---:|---|
| Eight operational/pipeline/publication/routing suites, including native lifecycle and authenticated read/API suites | 103 | Passed; includes both original failures and 23 new checks |
| Independent claim auditor, evaluation and native evaluation suites | 133 | Passed |
| Existing flood-event service suite | 4 | Passed with the required isolated fixture admin |
| Total | **240** | Passed |

Added native checks cover expired evidence, changed policy, unapproved sources, stale revisions, unknown depth, passable-to-all claims, seven changed retry payloads, stable generated request IDs, private provenance, concurrent same-request activation, full rollback, malformed/missing/mismatched saved evidence, historical newer-wet/clearance barriers, and provenance through linked expiry/clearance. The existing refresh test also checks preserved provenance and supported link creation.

The first additional regression run lacked the admin assumed by two existing event tests: 135 checks passed and two fixture-dependent event checks failed. The runner now explicitly seeds the required admin only in its fresh evaluation test database; the four event tests then passed. The other 133 passing checks were not repeated or double-counted. No product behavior was changed to accommodate this fixture setup. Existing multipart and `datetime.utcnow` deprecation warnings remain.

Disposable Docker PostGIS databases completed the existing migration chain to **`d7e4b9a21c60`**. Each run removes only its uniquely named allocated databases in `finally`; final cleanup succeeded. Normal local application and cloud databases were untouched. Providers use saved/synthetic test evidence, with no live or paid requests. Diagnostic probes still reproduce BUG-108/109/110; they are findings, not acceptance passes for those defects.

From the repository root, use the [preserved runner](phase-36-integration-audit-20261005/verify.py):

```powershell
# Eight targeted suites plus remaining-defect probes
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py

# Auditor/evaluation suites, then isolated fixture seeding and event suite
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py --additional-regressions

# Event suite alone with isolated fixture seeding
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py --event-regressions-only
```

The final targeted and event-only runs succeeded. The full additional mode's auditor/evaluation and event stages were verified in separate runs as described above. Connection settings are read internally from the local container and never printed.

Final Python AST parsing and `git diff --check` passed. A scan of 579 local documentation targets confirms that every added target resolves; nine stale `file://` references in the existing feature reference were already present at HEAD and are outside this repair. Tech-stack and architectural-decision records were audited and need no change because the repair uses existing dependencies and accepted architecture.

## Remaining work

1. Repair BUG-108 and BUG-109: persist accepted zone depth/severity/access on every component and preserve a case's newly retained support; verify readers, lifecycle and vehicle policy.
2. Complete BUG-110's trusted current incident evidence, CRS, locality and component contract. Shape validity, caller labels and modeled/administrative polygons are insufficient.
3. Connect accepted geometry to the actual worker and public/staff desktop/mobile contracts; the configured discovery job currently stops at extraction and the explicit pipeline has no automatic footprint activation caller.
4. Complete supported-footprint staging replay, real routing acceptance and physical PWA permissions/cache/offline verification. San Miguel boundary research remains a separate coverage task.

No deployment, push, new dependency, SQLAlchemy schema change or physical/browser rerun occurred. The [original integration audit](phase-36-integration-audit-20261005/README.md) preserves its historical 78 passing/two failing baseline; this repair supersedes BUG-107's failure state without closing the other operational gates.
