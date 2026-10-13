# Autonomous news-to-map readiness — October 13 evening

> **Last Updated:** October 13, 2026, 10:25 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Assessment

The selected source_rules news workflow runs independently of ChatGPT, an agent, MCP or external LLM inference. The deployed scheduler, protected controller, existing worker, normal processing/publication/geometry services, shared database and frontend readers are connected. This audit does **not** certify the deployment as fully ready or every news location as automatically plottable. Remaining timing, provider, spatial-coverage and operational-setting issues are recorded below. No application code or operational settings were changed in this audit, and no worker was triggered manually.

## Direct observations

- Existing Cloud Scheduler news job is ENABLED, `*/15 * * * *`, Asia/Manila, targeting the OIDC-protected `/api/v1/internal/news-scheduler/tick`. Its historical name still contains `every-3-hours`; its actual schedule is fifteen minutes.
- During the audit, the **10:15 PM PHT** automatic delivery returned HTTP 200. Execution `lanes-news-discovery-nfdqp` started at **10:15:08 PM**, completed successfully at **10:15:46 PM**, and logged `outcome=completed`, enabled processing/publication, no pipeline error/retry and **zero LLM requests**. The persisted cycle reads 135 feed entries and no eligible flood candidates; it did not create a fresh current-news zone.
- Seven publishers and eleven feeds are enabled. At 10:18 PM the latest reader reports zero feed errors, one body error and one unresolved-scope count. These counts may concern the same lead; they do not prove two different failed articles. Derived automation state correctly says `partial` / `Latest collection needs attention`, although the worker itself completed.
- Active source_rules validation is configured with source-rules-v1 / source-rules-production-v2 and measurement-first source policy v2. Current-policy readers have no pending/processing/retry/failed claim work. Six retained non-completed evaluations use older policy fingerprints; they are not current source-mode queue failures and were not deleted/retried.
- The current deployed API/news/expiry image is main **5febb730cdec654a6f3429c7099d710e460dfc0f** (PR #135), with successful Cloud Build `c40824f4-8ae4-43cd-bfd5-0bf1e67701df`. API revision `lanes-api-build-c40824f4-8ae4-43cd-bfd5-0bf1e67701df` serves 100%; frontend rollout `build-2026-10-13-003` serves 100% and targets the existing Cloud Run API. The API and both jobs bind the same Cloud SQL `lanes-db` / `lanes` database. This supersedes the earlier 420b38f release snapshot. The newer main includes optional MCP/framework code, but the active news provider remains source_rules; news services are unchanged between the two main commits.
- Local 8000, frontend proxy 3000 and navlanes.live return HTTP 200 for public zones, public alerts, authenticated admin zones and authenticated news automation. All agree on active IDs **58–63**, the same source_rules mode, live controller heartbeat, partial collection state and completed last cycle.
- The minute expiry scheduler and its existing worker are enabled and executions succeed. The database's **automatic_expiry_enabled=false** setting intentionally prevents expiry during the presentation.
- Re-ran the existing weather, pipeline, pipeline CLI and source-validation suites in the installed backend environment: **99 passed**. No additional database, container or server was started.

## Connected code path

`Cloud Scheduler → news_scheduler.news_weather_tick → run_weather_tick → NewsJobGateway.start → scripts.run_news_discovery --discover --pipeline --scheduled --limit 50 → run_scheduled_news_tick → discover_news → run_news_pipeline`.

The normal pipeline commits extraction, seeds/evaluates source claims, processes publication and calls `process_news_footprints`. Eligible unique road candidates produce labeled estimated OSM/NOAH corridors; ambiguous/incomplete cases remain alerts or review cases. Database writes are read by public Active Zones and authenticated admin zone APIs. `MapCanvas` and `LiveMapPage` refresh active geometry every 60 seconds, with SSE invalidation where available; normal display does not require an agent to run a replay.

The credit-free source_rules branch checks source occurrences and consistency locally. It shares local extraction logic and is **not independent verification of news truth or field-measured flood boundaries**. `catalog_status=not_configured` refers to the optional incident-footprint catalog; the existing estimated-road path still operates.

## Remaining issues and required work

### 1. Risk cadence is not reliably fifteen minutes

Observed successful worker starts at 8:15, 8:45, 9:15, 9:45 and 10:15 PM PHT show approximately **30-minute spacing** while weather selects 15 minutes. This is not the old three-hour schedule.

The controller's pending-dispatch guard waits fifteen elapsed minutes before reconciliation, including already submitted operations. Due collection is also calculated from the later actual collector start. Small execution delays and Scheduler jitter can therefore skip the next quarter-hour check.

Exact recorded example: reservation `13:45:03.675142Z`, collector `13:45:20.492870Z`, next tick `14:00:03.094828Z`. At that tick the reservation is only **899.420 seconds** old, so the guard returns pending; collection is only **882.602 seconds** old, so its fifteen-minute due check is also false. The next chance is 10:15 PM. The same alignment issue affects targets of 30/60 minutes near tick boundaries. Current UI due times are targets, not a promise of collection at that minute.

Required code fix: align due scheduling with quarter-hour slots or intended dispatch timing, reconcile known completed operations promptly, and preserve overlap/idempotency guarantees. Add regression cases around jitter and the worker-start delay. **Not implemented in this audit; developer approval is required before new code changes.** Relevant code: `news_weather_controller_service.py` pending/due checks and `news_scheduler_service.py` worker due recheck.

### 2. Weather interpretation is degraded

Open-Meteo currently supplies risk. PAGASA reports `uncertain` / `advisory_timestamp_missing`; the cumulative provider failure counter is 38 across 37 controller checks. Risk from one provider still chooses fifteen minutes, so collection continues. With no positive risk, incomplete coverage selects thirty minutes; sixty-minute quiet mode requires both sources to support quiet conditions. Repair the PAGASA parser using captured actual advisory/no-advisory cases, without treating unparseable content as quiet.

### 3. Article retrieval and discovery are partial

One current body failure is visible. Older saved Inquirer failures include publisher challenges/HTTP 403; those older saved rows do **not** identify the latest failed article. The collector can skip inaccessible/unqualified leads and continue other feeds. Open-article lookup exists as a diagnostic CLI; no automatic open-search fallback call was found in the normal scheduled discovery path. Automatic collection covers approved accessible RSS membership, not all news on the internet. Improve accessible verified fallbacks and durable per-article failure diagnostics if broader coverage is required.

### 4. Spatial coverage and exception handling are incomplete

Diagnostics report **1,524 qualified barangay boundaries against 1,710 expected NCR PSGC identities: 186 missing**. Missing barangay coverage cannot silently use a broader city boundary when a claim specifies that barangay. Multiple equally supported sections, absent depth, unspecified roads and incomplete assets cannot produce a qualified polygon automatically. They need better source/asset evidence or staff exception review. The connected demonstration retained seven supported September 9 alerts without polygons; five had equally supported sections. The core routine path is automatic, but exception handling is intentionally not universally automatic.

### 5. Presentation settings are not unattended production settings

Historical zones 59–63 are active in the shared live database while expiry is off. Their original historical deadlines remain intact and their creation times are current October insertions; do not describe them as current October flooding. After presentation, restore automatic expiry through System Settings; the existing minute worker can then expire overdue zones through the normal lifecycle. This audit leaves that operator-controlled setting unchanged.

The connected historical command was manually initiated and has a development-only admission scope. It is not a production scheduling dependency. The Tribune September 24 event story was published September 25 at 4:41 AM: the ordinary freshness/observation checks do not activate those afternoon events at the next-morning arrival. Its presentation reconstruction cannot prove ordinary timely collection of that article. Earlier normal scheduled-worker historical acceptance does prove positive September 9 plotting with original source clocks; new eligible **live** reporting has not produced a positive zone during this audit.

### 6. Administrator credential needs replacement

The supplied easily guessed administrator sign-in is accepted by the shared live API, not only a disposable local account. The operator should replace it through the normal account flow before leaving the public system unattended. No credential is recorded here and no password/permission was changed.

## Evidence locations

Ignored sanitized artifacts are under `data/news-autonomy-audit-20261013/`: `runtime.json`, `remaining-errors.json`, `deployment.json`, `current-status.json`, `api-connections.json`. They contain no passwords, bearer tokens or database connection strings. Existing positive simulation details are in [connected demonstration](news-connected-demo-20261013.md) and [normal scheduled-worker timeline acceptance](news-source-validation-20261013/README.md#complete-historical-timeline-and-reproducible-release-acceptance). The next priority is the timing defect, followed by provider parsing/coverage and post-demo expiry restoration; optional MCP is not required for this workflow.
