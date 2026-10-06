# Phase 36: Automatic approved-footprint worker integration

> **Last Updated:** October 05, 2026, 11:28 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Automatic worker connection verified locally; real current footprint source, map controls and release acceptance pending.

The automatic pipeline now invokes approved operational footprint activation after saved extraction, independent evaluation and source-alert publication/refresh/clearance/expiry. This implements the next slice after [BUG-107–BUG-110 repairs](phase-36-trusted-footprint-contract.md). No real current perimeter is provisioned; unsupported geometry stays a text-only source alert.

## Implementation

- `news_footprint_worker_service.py` shortlists latest unexpired automatic evaluated alerts matching the current policy and exact catalog article/input/claim/incident/observation identity. It resolves one record and calls existing atomic activation with expected revision, SRID, record ID and source/checksum. Activation rechecks catalog approval/current policy/qualified evidence/locality/component/revision gates. Staff correct/defer/reject decisions are excluded.
- The catalog remains operator-owned through `LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR`. Missing configuration returns `catalog_status=not_configured` without failing the normal alert fallback; invalid configured assets return a safe failure. Ambiguous records cannot be chosen by rank. No geometry is downloaded, inferred or repaired by the worker.
- A sweep scans at most 500 catalog-matching current decisions; the supplied 1–200 limit caps successful activations. Missing records do not consume the sweep. Failed early records cannot block later candidates inside that bound. Each transaction rolls back independently; summaries expose safe reason codes, and database details stay private. Cursors wrap to admit older alerts after new proof is provisioned.
- Restart seeding skips already handed-off current-policy runs, empty claims, old publication/pipeline shortlists. Immutable evidence and approved source/freshness checks still run before binding. Explicit `--after-run-id` remains available to move past rejected seeds; repeated malformed/unapproved batches require operator attention rather than being silently discarded.
- `scripts.run_news_discovery --discover --pipeline --limit 50` performs discovery then the full pipeline even after HTTP 304/no candidates or feed error responses. `--process-saved --pipeline` uses saved work without HTTP discovery. The old `--process` remains extraction-only. Invalid argument combinations stop before DB/network work. Pipeline failures, including seed and configured catalog errors, produce nonzero exit status.
- `scripts.run_news_pipeline` carries seed and footprint cursors in interval mode. Publication/expiry now report safe per-transaction storage errors and continue other cases; counters increment only after commit. Extraction storage loss still aborts rather than reporting durable success.
- Local `cloudbuild.yaml` selects full-pipeline discovery for a future release. No Cloud Run/Scheduler setting, provider configuration, production data or deployment was changed.

## Verification

| Final fresh verification | Passed |
|---|---:|
| Twelve targeted geometry/evidence/processing/pipeline/CLI/publication/read/routing suites | 258 |
| Eight related auditor/evaluation/zone/presentation/road/barangay suites | 194 |
| Existing event regression suite | 4 |
| Distinct total across 21 suites | **456** |

Native PostGIS checks cover exact activation/idempotency, absent/invalid/missing/ambiguous catalog fallback, protected staff choices, candidate batching, rollback/continued processing after approval or storage failure, parallel workers, restart seeding and saved pipeline handoffs through expiry. The saved-pipeline check uses real immutable queue/lease/binding/evaluation/decision/event/zone/link transactions, **mocked extraction and independent auditor responses**, a synthetic approved footprint and synthetic locality. It does not verify real NLP/provider accuracy or a live affected perimeter. Existing policy/routing tests verify geometry inclusion/vehicle policy; no live Valhalla detour or browser map acceptance was executed.

Both final commands created fresh loopback-only disposable databases, applied existing head `d7e4b9a21c60` and removed all four allocated databases. Historical diagnostic probes again pass depth/severity, retention, full-containment rejection and linked expiry/clearance. Python syntax, declared runtime imports, changed documentation relative links, candidate secret scan and diff checks pass. Existing deprecation warnings remain. No SQLAlchemy model/Alembic/package change occurred. All eight authoritative records were audited; Storage and architectural decisions are unchanged; database-design runtime status is synchronized. Current task/progress/feature/system/stack/bug records and operator/parent plans are synchronized.

```powershell
backend/venv/Scripts/python.exe docs/evaluations/phase-36-integration-audit-20261005/verify.py
backend/venv/Scripts/python.exe docs/evaluations/phase-36-integration-audit-20261005/verify.py --additional-regressions --zone-metadata-regressions
```

## Remaining delivery

1. Extend backend safe zone provenance and desktop/mobile existing map layers/details/exception controls. Verify API and both screen sizes with fixtures; preserve unavailable/error/offline status.
2. Provision an actual approved current incident footprint source and qualified boundaries in matching API/job runtimes, and verify evaluator model/policy/configuration. OSM, NOAH, DRRMO history and source text alone do not establish affected width or perimeter.
3. Complete real article → polygon → public map → vehicle routing → qualified refresh/clearance/expiry acceptance, followed by controlled staging and physical PWA verification. Prepared cloud job args are not a deployment result.

Gate 3 is complete locally. Overall automatic news-derived map plotting remains pending. No live provider call, normal/cloud DB write, push or deployment is part of this slice.
