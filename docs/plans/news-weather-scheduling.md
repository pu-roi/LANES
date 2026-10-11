# Automatic weather-based news scheduling

> **Last Updated:** October 11, 2026, 10:52 PM
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Implemented and verified locally on `roi-branch`; coordinated cloud activation remains a separate release.

## Policy

| Signals | Collection interval |
|---|---:|
| Both fresh providers support quiet conditions, no eligible active flood | 60 minutes |
| Any relevant positive weather signal or eligible current active flood | 15 minutes |
| Incomplete, stale or unavailable weather without positive evidence | 30 minutes |

Risk wins over uncertainty. A positive check keeps the 15-minute interval for 60 minutes after its persisted timestamp. Snapshot freshness expires at 30 minutes; GET reads evaluate expiry without saving anything. Weather changes collection frequency only. Existing source, extraction, independent audit, publication, observed-time and spatial gates still decide flood alerts and polygons.

Open-Meteo is requested in one batch for the current UTC hourly slot and next two slots. Any sampled precipitation of at least **0.2 mm** activates risk. This is an initial engineering trigger, not a calibrated flood probability. Incomplete slots cannot establish quiet conditions; a valid upstream-only positive still activates risk. These are model estimates, not rain gauges. See [Open-Meteo documentation](https://open-meteo.com/en/docs).

The official [PAGASA NCR page](https://www.pagasa.dost.gov.ph/regional-forecast/ncrprsd) reader uses only the rainfall and thunderstorm sections. It records advisory identity, dated issue clock, affected locations and explicit validity/next update. Without explicit validity, rainfall expires after three hours and thunderstorm after two. Invalid, missing, future or overdue clocks and undated no-advisory text produce uncertainty. A valid relevant advisory still wins when another section is uncertain. Dated unrelated advisories can support quiet sampled coverage; no new advisories are inferred from generic forecasts or navigation text.

## Versioned sampled coverage

`news_weather_service.POINTS` and [catalog snapshot](../evaluations/news-weather-scheduling-20261011/monitoring-catalog.json) record all 17 NCR local governments plus three upstream samples, with coordinates, locality, role and relevance. This is one representative point per locality, not complete city, catchment or street coverage. The Open-Meteo grid location may differ slightly from the requested coordinate.

| Upstream sample | Latitude, longitude | Engineering relevance |
|---|---|---|
| Rodriguez | 14.7320, 121.1450 | Upper Marikina corridor |
| San Mateo | 14.6965, 121.1218 | Marikina corridor upstream of NCR |
| Antipolo | 14.6600, 121.2300 | Upper Marikina tributary rain context |

The upstream locality selection was reviewed against [PAGASA basin geography, bulletin page 1](https://pubfiles.pagasa.dost.gov.ph/pagasaweb/files/hmd/riverbasin/ncrpasig-marikina-laguna-de-bay.pdf), which names these localities in Upper Marikina and its tributaries. Coordinates are engineering samples, not PAGASA station coordinates or certified watershed boundaries. Province-wide Rizal advisories are conservatively relevant to upstream monitoring. Future coordinate/coverage revisions require a new catalog version and review.

## Controller, persistence and worker

Cloud Scheduler will POST every 15 minutes to `/api/v1/internal/news-scheduler/tick` after release. Google-signed OIDC verification requires the configured audience, Google issuer, verified email and exact Scheduler service account. Application user JWTs cannot invoke it. Provider requests use bounded timeouts, fixed public URLs, no redirects and capped response bodies, independently of the landing weather widget cache.

The controller takes a PostgreSQL session advisory lock, saves its own `SystemSetting` JSON record `news_weather_controller_v1`, and prevents repeated quarter-hour checks. It computes collection due time using the latest recorded collection and the shared adaptive decision. Bounded database predicates also find actionable capture/extraction retries, claim binding/evaluation, publication maintenance, expiry and interrupted placement handoffs. Empty completed extractions and future retries do not keep launching jobs. Collection OFF still permits eligible pending processing and maintenance, subject to their own settings.

Before an external start, the controller commits a unique reservation token. Cloud Run gets the token as an execution environment override. Accepted operations are reconciled through operation/execution reads; uncertain starts search token-bearing execution pages, including soft-deleted executions. Running, unresolved or failed reconciliation retains the reservation and blocks an unproven resend. Proven absence permits a new attempt; incomplete listings do not establish absence. The existing worker advisory lock independently prevents overlapping pipeline work.

The worker rechecks the same adaptive interval, due time and enabled publisher settings immediately before collection. Current active evidence uses recent supported observation clocks (two-hour maximum) and original future deadlines. Historical alerts/zones retained only by disabling expiry do not activate weather risk. The independent minute zone-expiry job remains separate.

No SQLAlchemy model, Alembic migration or package was added. Controller snapshots and cumulative counters use the existing JSON setting table. Legacy `news_collection_interval_minutes` stays in DTOs/storage for compatibility; saves preserve its existing value and ignore submitted changes. It no longer controls due time.

## Admin status and acceptance

The staff-protected automation GET remains read-only and reports effective interval/reason, due time, sampled points, provider health and issue/validity times, controller heartbeat, dispatch errors, last request duration and cumulative check/provider-issue/accepted-worker-start counters. Desktop/mobile News Intelligence shows these with source links and explicit stale/failure states. System Settings retains collection and other pipeline switches while removing interval editing. A completed worker cycle refreshes displayed flood results.

[Local verification](../evaluations/news-weather-scheduling-20261011/README.md) separates disposable-database tests, responsive fixtures and actual read-only provider probes from cloud acceptance. [Rollout and rollback](../guides/news-weather-scheduling-rollout.md) require matching API, worker and frontend releases before changing the existing three-hour trigger. After activation, verify autonomous checks and executions with the browser closed; measure starts and provider failures over representative quiet/rain periods before claiming cost savings.
