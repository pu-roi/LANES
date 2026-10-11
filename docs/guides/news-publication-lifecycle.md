# News source-alert publication and lifecycle operator guide

> **Last Updated:** October 07, 2026, 12:45 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

Automatic source alerts, exact approved footprints and server-derived estimated road corridors are implemented locally after independent evidence evaluation. A uniquely article-grounded, qualified-locality-contained OSM/NOAH estimate may activate automatically using the existing 25 m road-zone margin and stored centerline. It is labeled estimated; NOAH supplies modeled susceptibility rather than measured current flood extent. Unsupported estimates remain Needs Review/source alerts. No real-event accuracy, matching release or live pipeline execution is established by local fixtures. [Current integration evidence](../evaluations/phase-36-estimated-road-zone-integration-20261006.md).

The worker prioritizes exact approved incident records, then checks eligible automatic source alerts for estimates. Unresolved attempts record the checked placement revision in existing decision JSONB; unchanged attempts are excluded from later sweeps to admit later claims. Replaced catalogs require a worker/API restart because placement providers are process-cached. Carry both returned seed and case cursors in interval mode. Storage/invalid-catalog errors remain explicit failure outcomes.

Estimated operation requires matching checked OSM/NOAH and qualified locality/history assets plus the existing independently configured evaluator. `LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR` is optional for that path; it configures the separate authoritative current-extent catalog. An invalid configured incident catalog fails the footprint stage and must be corrected. Existing two-hour observation expiry, metadata/access, current source/audit, identity/revision and staff-choice protections apply to both paths. Unchanged estimated extents/core/metadata can refresh after recomputation; changed extent falls back to an alert and withdraws unsupported old coverage.

Accepted zones are available to public/routing API reads at commit. Map clients use existing SSE/polling/cache invalidation, with roughly 15-second database polling; no sub-second delivery claim is made. Public/staff details reuse existing layouts and show article/source, observation, status, expiry and geometry basis.

## Release preparation

Exact-source auditor options under prompt v2 pass strict evidence checks with live synthetic free responses at both 20 and 60 seconds. Existing response schema and lifecycle gates remain. [Latest verification](../evaluations/phase-36-auditor-evidence-options-20261007.md).

The analytical bundle is now prepared and checked in the local Linux image. Follow the [exact release checklist](news-zone-release-checklist.md) for the free-only provider probe, existing migration, matching API/job/frontend deployment and controlled current-article checks. Local fixtures and packaging do not establish live operation. [Verification](../evaluations/phase-36-news-runtime-packaging-20261007.md).

## Explicit pipeline

From `backend`, the operator command is:

```powershell
venv/Scripts/python.exe -m scripts.run_news_pipeline --limit 50 --after-run-id 0 --after-case-id 0
```

This writes to the configured database and may incur fees from the explicitly configured independent AI provider. Verify the intended environment and credentials before operational use; this task ran only disposable fixtures and `--help`. No secret belongs in a command argument, source file or log.

Each bounded stage processes saved article evidence → seeds completed claims → independently audits leased work → publishes/refreshes/clears/expires source decisions → activates exact approved current footprints. The JSON summary includes `next_seed_cursor` and `next_footprint_cursor`; pass them as `--after-run-id` and `--after-case-id` on the next batch. `--interval 30` repeats batches and carries both cursors (accepted interval 30–3600 seconds). Restart seeding skips existing current-policy handoffs and empty/old candidates; partial sweeps wrap so newly approved older evidence can be reconsidered. If rejected seeds repeatedly fill a batch, inspect their safe reason codes and use the explicit run cursor to process later work. Standalone `scripts.evaluate_news_claims --seed`/`--evaluate` remains available and creates no publication decisions; see [independent evaluator guide](news-claim-evaluation.md).

Discovery can opt into the full pipeline:

```powershell
venv/Scripts/python.exe -m scripts.run_news_discovery --discover --pipeline --limit 50
venv/Scripts/python.exe -m scripts.run_news_discovery --process-saved --pipeline --limit 50
```

The saved-only command performs no feed/article HTTP discovery. Discovery runs maintenance even after unchanged feeds or feed errors; failure exit status remains nonzero. `--discover --process` remains extraction-only. `--pipeline` cannot be combined with dry-run or `--process`. The local Cloud Build job command is prepared for full-pipeline discovery, but no deployed job was changed.

Missing/invalid provider/model configuration, unsupported or stale evidence and audit disagreement cannot produce Active. Provider/model/config revision is part of policy identity. Fix configuration and deliberately change its nonsecret revision for new policy evaluation rather than mutating terminal history. Use matching processing/spatial assets in every participating runtime.

## Status and retention

Active expiry is supported observation plus two hours; publication, collection or processing time cannot reset it. Read-time expiry immediately yields Unconfirmed. `LANES_NEWS_UNCONFIRMED_RETENTION_HOURS` defaults to 24 and accepts 1–72, bounding default-feed retention after evidence expiry or supported clearance; it is a display setting, not predicted flood duration. Detail/history preserves safe last-known information. Cleared requires newer independently audited matched evidence; expiry alone does not prove dry roads or vehicle passability.

Exact same-article qualified sections may refresh a stable case from a genuinely newer observed update within twelve-hour continuity. Ambiguous sections/different source articles require stronger matching. Retries never extend evidence lifetime. Historical clearance prevents older wet evidence reactivation even after staff reopening/defer/rejection.

## Reads and staff decisions

Public `GET /api/v1/news/alerts` uses page/page_size and safe latest-decision projections; `/alerts/{case_id}` provides safe detail. Staff `/api/v1/admin/news/claims/{case_id}`, `/history`, `/decision-preview` and `/decisions` use active-session reports capabilities. Internal reasons stay private; only explicit public correction text is public. Preview is read-only and save repeats all gates under locks.

Use the same request UUID for uncertain retries. An altered request identity or stale expected revision returns 409; reload current evidence and prepare a new decision after resolving the conflict. Published decisions and audit history remain append-only. A failure rolls back the decision transaction. The shared staff interface retains drafts and consults durable history when a save response is uncertain.

## Operational activation boundary after the integration audit

`scripts.run_news_pipeline` and opt-in discovery `--pipeline` now invoke automatic approved-footprint activation after source publication/maintenance. The worker filters exact current catalog identities before activation and rechecks all service gates atomically. Each sweep considers at most 500 catalog-matching current decisions; `--limit` caps successful footprint activations. Rejected records do not block later candidates within that bound. Per-claim failures roll back independently and expose safe summary codes; seed/auditor/publication/footprint failures produce a nonzero one-shot exit. Missing catalog is normal text-only fallback; invalid configured catalog is an error. **456 distinct checks pass locally**. Actual current footprint provisioning, desktop/mobile map integration and matching deployed runtime acceptance remain open. [Current verification](../evaluations/phase-36-automatic-footprint-worker.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

Automatic activation requires `expected_revision`, `geometry_srid=4326` and `evidence_record_id` for an exact current operator-approved catalog record. Configure its operator-owned directory through the process environment variable `LANES_NEWS_OPERATIONAL_FOOTPRINT_DIR`; it contains checksummed `manifest.json` and `footprints.json`. The verification report documents fields, limits and approval/archive responsibilities. No real catalog was provisioned. Missing/invalid records, source/incident/input/claim/time/geometry mismatches or missing qualified locality boundaries cannot create routing geometry. Labels, OSM/NOAH/admin polygons and historical data cannot establish a current affected extent.

Authenticated staff preview/submit require `operational_footprint_srid=4326` with geometry and bind review to the stored active/capable actor and request UUID. Both repeat current independent evidence, metadata, full containment and component gates. Existing-zone relinking additionally verifies article/incident/component ownership and unchanged routing metadata. Shared frontend request types/geometry controls remain pending. Exact retries and retention do not extend expiry.

Newer observations renew old coverage only with one exact current approved extent and matching persisted components/depth/access. Missing or changed approval becomes a text-only alert with a private failure reason, and unsupported old links are withdrawn while independent coverage stays protected. Changed extent or depth needs new activation. Legacy attribution remains readable without approving relinks. Do not enable the dormant ingestion prototype or manufacture affected width/perimeters from modeled placement. [Earlier metadata/support checkpoint](../evaluations/phase-36-zone-metadata-support-repair.md).

## Release boundary

API-process SSE is emitted only after commit. Separate command/job processes do not share that in-memory manager; current reads plus public 30-second polling/focus/reconnect provide recovery. Offline/error snapshots are labeled last downloaded with current status unavailable. Deployment must separately verify matching workers/assets, migration head, provider/model availability and physical PWA behavior. No production publication or operational routing acceptance is implied by local fixture checks.

[Verification](../evaluations/phase-36-news-publication-lifecycle.md), [backend readiness contract](../plans/news-publication-readiness-plan.md).
