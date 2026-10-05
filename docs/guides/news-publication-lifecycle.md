# News source-alert publication and lifecycle operator guide

> **Last Updated:** October 05, 2026, 10:45 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

Automatic source alerts are implemented locally after independent evidence evaluation. They publish text-only reported conditions; operational flood-zone creation/routing remains disabled until current affected geometry is verified. No live pipeline execution or deployment is part of this checkpoint.

## Explicit pipeline

From `backend`, the operator command is:

```powershell
venv/Scripts/python.exe -m scripts.run_news_pipeline --limit 50 --after-run-id 0
```

This writes to the configured database and may incur fees from the explicitly configured independent AI provider. Verify the intended environment and credentials before operational use; this task ran only disposable fixtures and `--help`. No secret belongs in a command argument, source file or log.

Each bounded stage processes saved article evidence → seeds completed claims → independently audits leased work → publishes/clears/expires eligible source alerts. The JSON summary includes stage outcomes and `next_seed_cursor`; use that cursor on the next batch. `--interval 30` repeats bounded batches (accepted interval 30–3600 seconds). Discovery/collection remains an independent existing process. Standalone `scripts.evaluate_news_claims --seed`/`--evaluate` remains available and creates no publication decisions; see [independent evaluator guide](news-claim-evaluation.md).

Missing/invalid provider/model configuration, unsupported or stale evidence and audit disagreement cannot produce Active. Provider/model/config revision is part of policy identity. Fix configuration and deliberately change its nonsecret revision for new policy evaluation rather than mutating terminal history. Use matching processing/spatial assets in every participating runtime.

## Status and retention

Active expiry is supported observation plus two hours; publication, collection or processing time cannot reset it. Read-time expiry immediately yields Unconfirmed. `LANES_NEWS_UNCONFIRMED_RETENTION_HOURS` defaults to 24 and accepts 1–72, bounding default-feed retention after evidence expiry or supported clearance; it is a display setting, not predicted flood duration. Detail/history preserves safe last-known information. Cleared requires newer independently audited matched evidence; expiry alone does not prove dry roads or vehicle passability.

Exact same-article qualified sections may refresh a stable case from a genuinely newer observed update within twelve-hour continuity. Ambiguous sections/different source articles require stronger matching. Retries never extend evidence lifetime. Historical clearance prevents older wet evidence reactivation even after staff reopening/defer/rejection.

## Reads and staff decisions

Public `GET /api/v1/news/alerts` uses page/page_size and safe latest-decision projections; `/alerts/{case_id}` provides safe detail. Staff `/api/v1/admin/news/claims/{case_id}`, `/history`, `/decision-preview` and `/decisions` use active-session reports capabilities. Internal reasons stay private; only explicit public correction text is public. Preview is read-only and save repeats all gates under locks.

Use the same request UUID for uncertain retries. An altered request identity or stale expected revision returns 409; reload current evidence and prepare a new decision after resolving the conflict. Published decisions and audit history remain append-only. A failure rolls back the decision transaction. The shared staff interface retains drafts and consults durable history when a save response is uncertain.

## Operational activation boundary after the integration audit

`scripts.run_news_pipeline` connects saved extraction/evaluation to source alerts and maintenance; the configured discovery job still invokes only extraction. The separate activation helper has no automatic worker caller. BUG-107/108/109/110 pass locally; actual current footprint provisioning and worker/map integration remain open. [Current verification](../evaluations/phase-36-trusted-footprint-contract.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Automatic activation requires `expected_revision`, `geometry_srid=4326` and `evidence_record_id` for an exact current operator-approved catalog record. Configure its operator-owned directory through the process environment variable `LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR`; it contains checksummed `manifest.json` and `footprints.json`. The verification report documents fields, limits and approval/archive responsibilities. No real catalog was provisioned. Missing/invalid records, source/incident/input/claim/time/geometry mismatches or missing qualified locality boundaries cannot create routing geometry. Labels, OSM/NOAH/admin polygons and historical data cannot establish a current affected extent.

Authenticated staff preview/submit require `operational_footprint_srid=4326` with geometry and bind review to the stored active/capable actor and request UUID. Both repeat current independent evidence, metadata, full containment and component gates. Existing-zone relinking additionally verifies article/incident/component ownership and unchanged routing metadata. Shared frontend request types/geometry controls remain pending. Exact retries and retention do not extend expiry.

Newer observations renew old coverage only with one exact current approved extent and matching persisted components/depth/access. Missing or changed approval becomes a text-only alert with a private failure reason, and unsupported old links are withdrawn while independent coverage stays protected. Changed extent or depth needs new activation. Legacy attribution remains readable without approving relinks. Do not enable the dormant ingestion prototype or manufacture affected width/perimeters from modeled placement. [Earlier metadata/support checkpoint](../evaluations/phase-36-zone-metadata-support-repair.md).

## Release boundary

API-process SSE is emitted only after commit. Separate command/job processes do not share that in-memory manager; current reads plus public 30-second polling/focus/reconnect provide recovery. Offline/error snapshots are labeled last downloaded with current status unavailable. Deployment must separately verify matching workers/assets, migration head, provider/model availability and physical PWA behavior. No production publication or operational routing acceptance is implied by local fixture checks.

[Verification](../evaluations/phase-36-news-publication-lifecycle.md), [backend readiness contract](../plans/news-publication-readiness-plan.md).
