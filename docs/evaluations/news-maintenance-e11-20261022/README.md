# E1.1 — auditor-independent expiry maintenance

> **Last Updated:** October 22, 2026, 12:24 AM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). **Implemented and verified locally; not deployed.** [Task plan](../../task_plan.md#e1--connect-controlled-historical-processing) · [Aggregate verification](summary.json).

## Problem and correction

`run_news_pipeline` constructed and validated the auditor before reaching publication's expiry loop. An invalid constructor setting or unsupported auditor configuration therefore blocked due-case maintenance even though expiry does not require an auditor. The scheduler correctly reported a configuration error but could not retain a maintenance result that never ran.

`news_publication_service.process_news_expiry` now owns the shared due-case loop without constructing an auditor or accepting new source evidence. Normal publication calls the same helper and merges its expiry count and bounded skips. Existing case/configuration locks, due dates, effective operational deadlines, transaction boundaries, idempotent decisions, batch limits and scoped clocks remain in use. The helper checks the automatic-expiry setting before selecting cases and again before each case; `expire_case` retains its authoritative setting check under the existing configuration lock.

If auditor construction or semantic validation fails, the pipeline runs only this helper, attaches its `PublicationSummary` to the same bounded `AuditorConfigurationError` and rethrows that original error. No article claim, extraction, evaluation, provider request, clearance processing, new publication or footprint generation is admitted through this failure path. SQL and unexpected maintenance failures become separate bounded skip codes; exception messages, credentials and invalid setting values are not copied into output.

The scheduler records maintenance counts, errors and stage health separately from the pipeline configuration error. A successful maintenance stage cannot advance the overall last-successful timestamp or turn the cycle into success. A failed maintenance stage retains its previous successful timestamp, while the original auditor error remains the cycle's primary error. Existing runtime JSON/stage contracts accommodate this; no public endpoint, database schema or frontend type was added.

## Verification

**82 checks passed; zero failures or skips**, with three existing multipart/Pydantic warnings. The final run includes:

- Constructor parsing failure, unsupported provider and invalid revision: independent maintenance runs once; dependent stages, policy construction and provider requests are forbidden; original error codes remain unchanged.
- Initial selection failure, per-case storage/revision failures and unexpected helper failure: bounded maintenance diagnostics remain separate from the auditor error; successfully committed cases remain counted.
- Automatic expiry off and operator pause after selection: no expiry lifecycle action occurs.
- Real disposable PostGIS zone with expiry off: case revisions, decisions, zone activity/deadline/geometry, event status and source version/run counts stay identical across two failed-config executions.
- Real disposable PostGIS zone with expiry on: one expiry decision deactivates the zone and ends its event without changing geometry; repeating adds no decision, source version or extraction run.
- Not-yet-due and repeated case maintenance: original deadlines and idempotency are preserved.
- Portable and real PostGIS scheduler paths: original configuration error, maintenance counts and failure health survive finalization; overall last-successful time does not advance and private setting values are absent.
- Existing valid-configuration pipeline switches/progress/CLI checks, Phase D monitoring and protected read-only health checks, expiry projections, automatic publication, qualified clearance with publication paused, source pause/resume and operational deadline refresh remain passing.

Suites: `test_news_pipeline.py`, `test_news_pipeline_cli.py`, `test_news_expiry_maintenance.py`, `test_news_maintenance_postgres.py`, `test_news_monitoring_phase_d.py`, `test_news_publication_lifecycle.py`, plus six selected lifecycle checks from `test_news_publication_lifecycle_postgres.py` (including both clearance-toggle parameter cases).

The private runner uses only the local PostGIS container and explicit disposable database names, replacing inherited database configuration before application imports. Existing approved migrations reached `e8a6f1c2d903` on fresh test storage; no migration file was changed. Case databases are cloned from the owned empty template and removed by their fixtures. The owned template and lifecycle database were removed after the run; no case databases remain. Docker Desktop required a restart before these checks; no cloud database or model inference was used.

Private XML, runner, exit and cleanup receipts remain under ignored `data/news-maintenance-e11-20261022/`. All five frozen E0 package files retain their exact prior file hashes. Frozen article/model/neural/rule artifacts were not edited. Application-code hashes covered by future execution manifests may change because the publication service changed; the E0 package remains a historical preparation record and must not be rewritten to disguise that change.

## Delivery boundary

This fixes only E1.1. The historical manifest-bound command, controlled target policy, date normalization, NER/geometry qualification, active demo/history persistence, interface work and cloud release remain pending. There are **no new map zones or frontend controls to test manually from E1.1**. The configured cloud automatic-expiry setting was neither read nor changed during this task. Dependency manifests, models and migration files are unchanged; no cloud write, deployment, commit or push occurred.
