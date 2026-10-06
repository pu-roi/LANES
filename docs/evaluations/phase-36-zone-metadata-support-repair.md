# Phase 36: News zone metadata and retained-support repair

> **Last Updated:** October 05, 2026, 10:59 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** BUG-108/109 resolved locally on `roi-branch`; trusted footprints and automatic worker/map integration remain pending.

News-created zones now persist the verified depth/severity and audited access metadata on every disconnected polygon component. A case can retain its existing zone without immediately deactivating it. Native public-zone responses and vehicle policy consume these persisted values correctly. **289 distinct checks passed across fourteen suites**; this is a backend repair, not completed automatic news-to-map plotting.


## Latest trusted-footprint follow-up

BUG-107/108/109/110 are now repaired locally with **398 distinct passing checks**. Exact current incident/staff approval, explicit SRID, full locality/component containment and safe unsupported-renewal fallback pass. Actual current footprint provisioning, automatic worker/map integration and staging/PWA acceptance remain open. The findings and test counts below preserve earlier checkpoints. [Latest verification](phase-36-trusted-footprint-contract.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


## Changes and evidence

BUG-108 set the FloodEvent peak but omitted zone metadata. Zone readers consequently fell back to medium severity/no depth. The shared news service now derives existing `severity_override`, `depth_override` and `passable_vehicles_override` attributes from independently validated claim evidence and supplies them to both staff and automatic creation paths. The first component uses the existing event helper's `zone_attributes`; later components receive the same metadata within the caller's transaction. No SQLAlchemy model or Alembic definition changed.

Unknown depth cannot authorize a zone; it remains eligible for a source alert under existing alert rules. Known access classifications require independent confirmation. Explicit passable-to-all claims reject activation in both paths. Unknown vehicle access stays unset. "Light vehicles prohibited" and "No vehicles" tighten the existing routing policy without implying permitted vehicle classes or pedestrian closure. Caution/unspecified access labels preserve source meaning and never relax the depth-based policy.

Native public API checks exposed a second BUG-108 blocker: `ZoneContributorResponse` accepts polygons but its EWKB decoder omitted polygon conversion. The existing polygon parser now decodes news contributor geometry, allowing real `/api/v1/reports/active-zones` responses to serialize successfully.

BUG-109's withdrawal query excluded every decision from the previous case, including its newly current supported revision. It now excludes only the prior decision ID while still requiring current case revision, active-zone state, unexpired evidence and a link to that exact zone. Retention preserves the original zone expiry; exact retries do not extend it. Older active history cannot retain withdrawn support. Rejection, deferral, text-only correction, clearance and expiry end solely news-supported coverage; reopening a withdrawn case cannot resurrect it. Active cases continue to reject reopening. Replacing a footprint ends removed coverage while preserving the new zone. Existing independent-news/citizen support checks continue to pass, and the existing manual-owner exemption remains unchanged.

The staff existing-zone path additionally rejects an expired zone even if maintenance has not cleared its active flag. Authentication/capability dependencies and public API routes remain unchanged. No new request-level metadata override fields were exposed.

Application files:

- [News publication service](../../backend/app/services/news_publication_service.py)
- [Vehicle routing policy](../../backend/app/services/flood_routing_policy.py)
- [Zone/contributor response schema](../../backend/app/schemas/report.py)
- [Native publication/lifecycle regressions](../../backend/tests/test_news_publication_lifecycle_postgres.py)

## Verification

| Scope | Distinct passing checks |
|---|---:|
| Eight targeted operational/pipeline/publication/read/routing suites | 140 |
| Auditor, evaluation, native evaluation, zone-edit schema and reported-depth presentation suites | 145 |
| Existing flood-event service suite | 4 |
| Total | **289** |

The targeted run includes 37 new checks: sixteen staff/automatic MultiPolygon metadata cases, five native public-zone API/routing-reader matrices, three staff measurement/access rejections, two unconfirmed automatic-access rejections, six retained-support lifecycle cases, replacement, concurrent retention, two rollback cases and expired-zone retention rejection. Existing BUG-107 activation/retry/evidence checks remain intact and pass.

Test fixtures now quote their actual canonical depth and access condition instead of reporting knee depth for every gauge. Reader tests use the fixture clock in actual SQL expiry predicates and an isolated dependency override for HTTP requests. They query persisted polygons and metadata, including derived physical measurements and publisher contributors; they do not stub zones. They verify walk/motorcycle/light/heavy policy and disappearance from public/routing readers after expiry. No live Valhalla detour, real article-to-operational-polygon placement, browser run or physical PWA acceptance is claimed.

Final service probes read waist zones as high/waist, retain the same zone active with unchanged expiry, and end solely linked coverage/event on clearance or expiry. The BUG-110 probe still accepts an arbitrary source label and partial parent overlap; that remaining defect is explicitly open.

From the repository root:

```powershell
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py --additional-regressions --zone-metadata-regressions
```

Both final commands succeeded and removed their two allocated disposable databases. Existing migrations upgraded to `d7e4b9a21c60`. The related run seeds only the admin required by existing event fixtures in its isolated test database. Normal local/cloud databases, dependencies and frontend code were untouched. Existing multipart/`datetime.utcnow` warnings remain. No deployment or Git push occurred.

Final Python AST parsing and `git diff --check` passed. All added documentation targets resolve in a scan of 597 local links; nine stale feature-reference `file://` targets were already present at HEAD. The eight authoritative records were audited; tech-stack and decision records need no change because this repair uses existing dependencies, storage and architecture.

## Next delivery steps

Complete BUG-110's current incident/geometry trust, CRS, full locality containment and component contract. Then connect accepted geometry to the real automatic worker and public/staff desktop/mobile map contracts. Finish actual article-to-zone, vehicle routing and evidence lifecycle acceptance before release. These are the remaining steps of the [automatic news-zone map delivery](../task_plan.md), not a substitute feature.

The [original audit](phase-36-integration-audit-20261005/README.md) and [BUG-107 repair](phase-36-bug107-activation-repair.md) preserve earlier checkpoints; this report supersedes their open BUG-108/109 status.
