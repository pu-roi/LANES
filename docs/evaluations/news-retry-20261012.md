# Historical news replay retry — October 12

> **Last Updated:** October 12, 2026, 9:09 PM PHT
> **Developer:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Outcome:** Both scheduled replays completed. Real batching and four independent verifications were observed; positive zone/history/depth-update acceptance remains unverified.

## Execution and isolation

The developer requested September 24–25 first, followed by September 9. Both use the current `roi-branch` application, original captured sources and `run_scheduled_news_tick`. No application source, provider/model, schema, migration definition, dependency, observation, depth or product label changed. There was no push or cloud deployment.

Docker Desktop initially failed on its stale Ingest socket. After stopping its processes, the runtime socket directories were moved to recoverable `run.retry-backup-20261012-202347` and `docker-secrets-engine.retry-backup-20261012-202347` backups under LocalAppData. The original PostGIS container/volume was reused; no reset or deletion occurred. Existing migrations reached `d7e4b9a21c60` in each new database.

Ignored helpers now accept bounded retry database names and JSON output basenames. They reject remote targets, connection query overrides, an existing database, output path traversal and existing result files. Six refusal checks passed. Worker/preview targets are isolated; the preview's private Docker-network TCP forward keeps its application database connection on loopback. Provider timing uses actual UTC; replay processing uses original historical clocks.

## Observed results

| Scenario | Dedicated database | Scheduled checkpoints | Articles / versions / runs | Final locations | Zones / events / history locations |
|---|---|---:|---|---:|---|
| September 24–25 | `lanes_workflow_retry_20261012_2026_sep24` | 5 | 3 / 1 / 1 | 5 | 0 / 0 / 0 |
| September 9, including indexed early body and article edit | `lanes_workflow_retry_20261012_2026_sep9` | 26, every 30 minutes from 09:56 to 22:26 | 3 / 4 / 4 | 33 | 0 / 0 / 0 |

September 24 produced eleven local evaluation decisions: five `observation_outside_admission_window` and six `unsupported_claim_context`. The five Tribune locations remain saved. Their original September 24 observations were already more than twelve hours old when the September 25 article became available. No provider audits were needed; zero zones is an admission outcome, not another quota failure.

Both provider preflight checks returned HTTP 200 with **0 used / 50 limit / 50 remaining**. September 9 made **20 actual audit requests**, dispatching **131 claim attempts including retries**. The first early-body group dispatched 27 eligible claims in four requests; the separate synthetic 26-claim acceptance from the previous implementation remains a distinct regression check. A final independent quota GET returned HTTP 200 with **20 used / 50 limit / 30 remaining**. No daily-quota exhaustion or HTTP 429 occurred in this retry.

September 9 finished with seventy completed evaluations and seven failed evaluations. Completed does not mean approved: forty-six completed with `observation_evidence_expired`, eight with `not_observed_flood_evidence`, eight with `unsupported_claim_context`, three with `missing_supported_observation_time`, one with `unsupported_locality`, and four with `claim_evidence_verified`. Terminal failures were three `audit_parent_locality_evidence_missing`, two `audit_claim_identity_mismatch` and two `audit_depth_qualifier_unsupported`. Tick snapshots additionally preserve transient `auditor_timeout` and `audit_batch_result_missing` failures before retries or expiry.

## Real verifications and placement

| Verified source claim | Original observation | Footprint outcome |
|---|---|---|
| Rizal Avenue Extension, San Agustin, Malabon — gutter deep | 14:47 | `missing_valid_barangay_boundary` |
| F. Sevilla Boulevard, Tañong, Malabon — gutter deep | 14:47 | `missing_valid_barangay_boundary` |
| Marcos Highway Underloop, Marikina — gutter deep | 14:47 | `local_place_not_grounded` |
| G. Araneta corner Kitanlad, Tatalon, Quezon City — 8 inches | 16:30 | `missing_valid_barangay_boundary` |

All four real verified claims reached the normal text-alert workflow. The existing footprint worker kept them in review and created no operational zones. Their later expiry is preserved in append-only decisions. No geometry or boundary was supplied manually to manufacture a successful result.

The matched comparison is **N.S. Amoranto corner Banawe, Santo Domingo, Quezon City**, distinct from other intersections or the same street in Sienna:

| Source observation | Evaluation | Actual audit attempts | Final result |
|---|---:|---:|---|
| Early GMA indexed body: 19 inches at 08:55 | 13 | 2 | Timeout retries, then evidence expired |
| Later Philstar body: 10 inches at 16:30 | 50 | 3 | Timeout/missing-result retries, then evidence expired |

The first eligible zone never existed. Consequently, updating an existing zone versus creating another remains unverified. Zero history events cannot establish a history-writing defect. The paired facts, barangay, intersection, original measurements and source text remain intact.

## Repeatability, preview and limitations

Each scenario repeated its final checkpoint once. Article/version/run/zone/event/history counts remained unchanged and completed evaluation attempt counts did not increase. Original publisher HTML hashes match the previous batch replay; the early indexed body is unchanged. A read-only check confirms the preserved `lanes_plotting_20261011` snapshot still has Zones/Events 58, 59 and 60 active.

The separate frontend on **3004** and backend on **8004** displayed September 24 first. The final [News Intelligence preview](http://127.0.0.1:3004/admin/news) uses the September 9 database at the final 22:26 checkpoint. Its original application bootstrap provides `admin` / `admin` only in these isolated databases. A database-bound private scenario supplies the read clock for this preview's own claim/zone IDs; independent retention is paused in the preview process. HTTP status reads do not dispatch provider requests. The existing port-3000 configuration and shared/cloud data were untouched. SSE endpoints and preview-origin CORS returned HTTP 200; unauthenticated automation status returned 401.

Browser verification finished with limitations. September 24 attempts preserved desktop news/map/history success, mobile news/history success and repeated cold/navigation failures, including blank mobile map loads. The final September 9 bounded inspection reports the following; failed attempts and screenshots are retained, not counted as passing:

| Page | Desktop 1440×1000 | Mobile 390×844 |
|---|---|---|
| News Intelligence, 33 locations | Passed, no horizontal overflow | Blank page; tab never appeared within timeout |
| Flood History | Blank page; records tab never appeared within timeout | Blank page; `Invalid or unexpected token` browser error |
| Public map | Canvas rendered, no horizontal overflow | Canvas absent; `Invalid or unexpected token` browser error |

The four inspection APIs (locations, automation, public zones and history) all returned HTTP 200 and the expected 33/0/0 records. The same application had successful earlier responsive inspections; this run does not establish a clean final mobile or History rendering pass. The failing JavaScript asset/root cause has not been identified. The map provider also returned HTTP 403 and the existing basic-map fallback appeared. No UI repair is included in this task. Earlier preview-login HTTP 500 checks occurred before the fresh backend completed startup; after readiness, authenticated login/API checks passed.

Private replay JSON, runtime logs, safe provider readout, guard results and browser screenshots are under ignored `data/news-replay/`, with the `retry-20261012-2026-` prefix. Credentials and unrestricted provider responses are not part of the published record.

Historical fidelity remains limited by reconstructed RSS membership, the current approved source registry, the recovered early GMA indexed text with reconstructed markup, and spatial assets newer than the replay dates. Weather-controller/cloud dispatch was not exercised; the ordinary unavailable-weather 30-minute worker policy is unchanged. These are local historical simulations, not current public flood reports.

**Remaining acceptance:** reliable real verification for the depth pair and an eligible source-grounded footprint before testing zone update/history behavior. Any auditor-contract, source-locality or placement repair requires a separate scope. [Previous batch verification](news-batch-audit-20261012/README.md) and [historical source qualifications](news-scheduled-historical-workflow-20261012.md) remain preserved.
