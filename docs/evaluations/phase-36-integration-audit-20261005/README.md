# Phase 36: Integration and completion audit

> **Last Updated:** October 05, 2026, 10:59 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Checkpoint:** `67cdffa`, `roi-branch`; application source unchanged by this audit.
> **Status:** Source-alert checks pass; operational-zone completion claim reopened.


## Latest trusted-footprint follow-up

BUG-107/108/109/110 are now repaired locally with **398 distinct passing checks**. Exact current incident/staff approval, explicit SRID, full locality/component containment and safe unsupported-renewal fallback pass. Actual current footprint provisioning, automatic worker/map integration and staging/PWA acceptance remain open. The findings and test counts below preserve earlier checkpoints. [Latest verification](../phase-36-trusted-footprint-contract.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


## Earlier metadata/support follow-up

BUG-108/109 are now repaired locally with **289 distinct passing checks**. Final probes show high/waist zone metadata and active same-case retention; final clearance/expiry still ends solely supported zones/events. BUG-110 and real worker/map/staging/PWA acceptance remain open. Original audit outcomes below are historical. [Verification](../phase-36-zone-metadata-support-repair.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Earlier BUG-107 repair follow-up

This document preserves the original findings at `67cdffa`. BUG-107 has since been repaired locally with **240 distinct passing checks**, including both original failing tests. The preserved runner now verifies repaired source and offers additional regression modes. BUG-108/109/110 and automatic worker/frontend/staging/PWA integration remain open. [Repair verification](../phase-36-bug107-activation-repair.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Original audit result

The implementation contains reusable zone/event/link helpers, but it does not complete automatic operational plotting. The configured discovery job stops after extraction. The explicit pipeline connects saved extraction, independent evaluation, publication and expiry, but first publication creates a text-only alert. `activate_operational_footprint` has no application caller outside its definition; its only calls are in native tests, and both activation tests fail on a freshly migrated database.

This audit supersedes the earlier claim that all five operational-zone gates and native activation tests passed. Earlier checkpoints remain historical records. Research and boundary coverage do not resolve these code failures.

## Current phase assessment

| Part | Evidence and current status |
|---|---|
| Extraction and placement previews | Implemented; versioned OSM/NOAH/community assets and separate predicted fragments remain preview evidence. No new spatial replay was performed here. |
| Independent evaluation | Existing leased evaluation and policy/evidence checks feed the explicit worker. A live provider request was not run. |
| Source alerts and lifecycle | Targeted source-alert/publication/API/pipeline checks pass, including immediate Unconfirmed projection, qualified observation refresh, matched clearance, immutable history and permissions. |
| Gate 1: operational footprint | Polygon/MultiPolygon shape, topology, area, coordinate bounds and decomposition exist. Parent checks are optional and use intersection; a nonempty arbitrary source label satisfies provenance. This does not establish verified current incident geometry or enforce a Shapely SRID. |
| Gate 2: transaction helpers | Non-committing event/zone helpers exist. Source-alert rollback tests pass; the failed activation transactions leave no committed zones. This is not a completed operational acceptance gate. |
| Gate 3: activation and links | Staff correction can create/link zones through the API. The separate activation helper crashes. Initial automatic publication remains `active_alert`; existing active-zone refresh can extend links. Same-case relinking can deactivate the very zone retained by the new decision. |
| Gate 4: provenance and metadata | News source/contributor properties exist. Operational zone severity/depth are not populated from the accepted claim, so readers/routing can use the wrong severity. |
| Gate 5: integrated acceptance | Reopened: two native activation failures, metadata/lifecycle defects and absent automatic runtime caller. Existing mocked browser checkpoints are not real article-to-operational-zone acceptance. |
| Production and PWA | Matching worker/job release, real supported-footprint replay, desktop/mobile integrated walkthrough and physical permission/cache/offline acceptance remain open. No cloud state was inspected. |

## Call-chain evidence

- [Cloud Build](../../../cloudbuild.yaml) configures `lanes-news-discovery` with `scripts.run_news_discovery --discover --process --limit 50`.
- [Discovery command](../../../backend/scripts/run_news_discovery.py) calls `process_saved_news` when processing is requested; it does not call the evaluator or publication orchestration.
- [Explicit pipeline](../../../backend/app/services/news_pipeline_service.py) calls `process_saved_news`, `seed_claim_evaluations`, `evaluate_news_claims`, then `process_news_publications`. [CLI](../../../backend/scripts/run_news_pipeline.py) provides bounded/repeated execution. This source configuration does not prove the command is deployed or scheduled.
- [Publication](../../../backend/app/services/news_publication_service.py) creates first eligible claims as `active_alert`; refresh can retain an already active zone. The operational activation helper has no runtime caller.
- [Staff API](../../../backend/app/api/v1/endpoints/admin_news_publication.py) authenticates sessions/capabilities and delegates footprint/zone requests to `apply_staff_decision`.
- Frontend [public alert types](../../../frontend/src/features/news/publicNewsApi.ts) still restrict geometry to `text_only`, `display_geojson` to null and routing to false. [Staff request types](../../../frontend/src/features/admin/review/reviewApi.ts) omit `operational_footprint`/`operational_zone_id`; shared decision controls supply no operational geometry input. Existing zone layers may display saved zones, but these contracts do not demonstrate a completed operational news workflow.

## Fresh verification

Command from the repository root:

```powershell
& .\backend\venv\Scripts\python.exe .\docs\evaluations\phase-36-integration-audit-20261005\verify.py
```

The preserved runner obtains local Docker connection settings without printing secrets, creates uniquely named empty test databases, sets only subprocess test configuration, runs existing suites and diagnostic probes, and drops only those exact databases in `finally`. It never runs the live news worker or calls an AI provider. The original nonzero exit reflected the failures recorded below; the repaired source now passes the default tests; `LANES_PHASE36_PROBE_ONLY=1` runs only the diagnostic path on a freshly migrated test database.

Eight suites were run: `test_operational_footprint`, `test_news_pipeline`, `test_news_publication_lifecycle`, `test_news_publication_api`, `test_routing_service`, `test_flood_routing_policy`, `test_news_publication_lifecycle_postgres`, and `test_news_publication_reads_postgres`.

**78 passed, 2 failed**, with one existing multipart deprecation warning. Both failures are:

- `test_activate_operational_footprint_splits_multipolygon_and_creates_zones`
- `test_observation_refresh_extends_active_zone_expiry`

The helper applies strict `IndependentAuditResult.model_validate` to a JSON-backed dictionary. Serialized list/tuple and timestamp values need the strict JSON decoding path used by `_load`. A broad exception handler replaces the failed audit with None, and `_public` raises `AttributeError` when reading `audit.evidence`. Failure occurs after transient zone/event creation, within the caller's rolled-back transaction. The fresh run does not support the prior native success claim.

Four disposable databases were created and removed across the test run and follow-up diagnostics. Three full existing migration upgrades completed to **`d7e4b9a21c60`**; the second diagnostics-only evaluation database was allocated but unused. Normal local application and cloud databases were untouched. No model, dependency, migration definition, provider request, deployment, browser rerun or physical-device test occurred.

## Diagnostic findings

These probes call actual services against the disposable database; they are observations of current behavior, not passing acceptance tests for the intended behavior.

| Probe | Observed result | Implication |
|---|---|---|
| Partly outside parent boundary, arbitrary provenance label | `is_eligible=True`, `reason=verified_operational_footprint`, `parent.covers(footprint)=False` | Valid polygon shape and overlap cannot certify current flood extent, source trust or full locality fit. |
| Audited waist-depth claim activated through staff correction | Event peak `high`/`waist`; persisted zone `medium`/null | Zone helpers omit severity/depth overrides. Existing readers and vehicle policy use zone metadata, not event peak. |
| Staff correction after observation expiry | Rejected with `observation_evidence_expired` | Staff path retains freshness gates. |
| Staff correction under changed policy | Rejected with `publication_policy_changed` | Staff path retains policy identity gates. |
| Correct active zone to support the same existing zone | New decision `active_zone`; linked zone inactive, expiry truncated to now | `_withdraw_support` ignores new support from the previous case itself. |
| Expire a solely news-supported staff-created zone | Zone inactive; event ended | Basic linked expiry works through staff-created fixtures. |
| Matched clearance for a solely news-supported staff-created zone | Zone inactive; event ended | Basic linked clearance works through staff-created fixtures. |

Source inspection adds unresolved activation-helper risks masked by its current parsing crash: it does not call `_load` to revalidate the current evaluation/policy/freshness; its request digest omits footprint/checksum/actor/policy; provenance is not persisted as a complete immutable geometry evidence record. These are code findings, not successful runtime bypass demonstrations.

Existing native shared-support checks pass for the prepared independent news/citizen fixtures. This does not validate every support transition or justify clearing expiry for unsupported geometry. Contributor properties also suppress lookup exceptions and select the first historical link; complete multi-source/current attribution requires separate acceptance.

## Ordered next work

1. Repair strict audit decoding and fail closed; recheck current policy, source/claim identity, observation freshness, revision/clearance barriers and complete request identity before operational writes. Reproduce the two existing failing tests, then add meaningful regressions for the uncovered requirements.
2. Preserve supported claim depth/severity/access on every polygon component, and preserve same-case retained support when withdrawing the previous decision. Verify actual zone readers and vehicle-specific routing, not just a preconstructed `ActiveFloodZone` stub.
3. Define the trusted current-footprint input and bind its source/checksum, observation and incident identity. Enforce the established locality/CRS/component contract. Do not promote NOAH intersections, centerlines, administrative polygons or arbitrary buffers to operational evidence.
4. Connect the accepted footprint input to the real orchestration and update public/staff frontend contracts on desktop/mobile. Verify worker scheduling and maintenance in staging before claiming continuous operation.
5. Verify San Miguel relation 18323640 and its PSGC/parent/topology mapping, then provision a new immutable catalog version. Current receipt remains 20 accepted Pasig barangays; coverage improvement alone does not establish current flooding.
6. Complete controlled article-to-alert/zone/routing/refresh/expiry/clearance staging acceptance, followed by the real admin/public-map walkthrough and physical PWA checks. Duration ML remains a separate optional research gate.

## Documentation reconciliation

Task/progress completion states and current publication/system/feature/storage notes now distinguish reusable implementation from failed or unconnected acceptance. BUG-107 through BUG-110 record the discovered defects. The dependency stack and accepted architecture decisions did not change. Historical checkpoints and their test counts remain historical, not cumulative current totals.

[Task plan](../../task_plan.md), [progress](../../progress.md), [bug log](../../others/bug-log.md), [earlier lifecycle verification](../phase-36-news-publication-lifecycle.md).
