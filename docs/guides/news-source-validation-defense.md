# NLP news processing and defense demonstration

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Checked:** October 13, 2026

## What to present

LANES automatically collects approved news, extracts flood facts through local Taglish NLP/rules, checks their consistency with the original source and plots sufficiently specific reports as estimated OSM/NOAH road zones. There are no LLM inference/quota requests in this mode. Uncertain reports remain source alerts or require review. Current wet extent and width are not measured by this process.

The adaptive controller checks every 15 minutes: relevant weather/current-flood/recent-risk evidence selects 15-minute collection, complete quiet weather selects 60 minutes, and uncertain coverage selects 30. These are free weather-data reads, separate from optional AI weather explanations.

## Running local session

The prepared frontend is at `http://127.0.0.1:3000/map`; backend is `http://127.0.0.1:8000`. They use the existing PostGIS/Valhalla containers. The private demonstration database is `lanes_nlp_demo_20261013_v3`, with its database-bound scenario file at `data/news-nlp-demo-20261013-v3/scenario.local.json`.

This session shows preserved **September 9, 2026** reporting at its historical observation clock. Explain that it is a historical replay, not current flooding. Normal production does not read the local scenario file. Preload the map before presenting; basemap tiles still need their normal network/cache availability.

1. Open the map and **News alerts**. Inspect the Santo Domingo NS Amoranto/Banawe report, then other mapped reports.
2. Show its original GMA source, reported time and depth, estimated-corridor explanation and evidence expiry. Use the normal source link to compare the report.
3. Show `data/news-nlp-demo-20261013-v3/result.json`: one article, 31 evaluations, 27 source alerts, seven zones, zero LLM requests and no new zones on repeat.
4. Explain why the other reports do not all become polygons: multiple possible road sections, missing bounds/depth, carriageway ambiguity or conflicting evidence. Explicit measurements take precedence over verbal labels: Santo Domingo now plots using its reported 19 inches. Other ambiguity and source/freshness gates remain.
5. Show the automated source-mode worker/configuration in production; keep the live and historical results separate.

The normal local administrative login is a development-only account in this private database. It is separate from production users. The backend generates a runtime key when no private development key is supplied, so restarting may require signing in again.

## Restart the replay backend

Stop only the existing port-8000 demonstration process before replacing it; never launch duplicate servers on other ports. From the repository root, call the launcher with the local database connection URL and the absolute scenario path:

```powershell
./backend/start-news-source-demo.ps1 -DatabaseUrl '<local PostgreSQL URL for lanes_nlp_demo_20261013_v3>' -ScenarioFile '<absolute repository path>/data/news-nlp-demo-20261013-v3/scenario.local.json'
```

The launcher enforces the development/private database guard, applies only existing migrations when the database is empty, runs the normal scheduled worker with captured publisher responses and historical clock and starts the API on 8000. Repeating against saved evidence is idempotent; it does not reset history or resurrect expired decisions.

Start the existing frontend with `BACKEND_URL` and `NEWS_SIMULATION_BACKEND_URL` pointing to that local backend, and `NEXT_PUBLIC_API_URL=/api/v1`. Preserve the normal encrypted frontend environment and existing simulation storage. The replay requires no publisher or model inference requests; only ordinary map/UI resources remain external.

## Normal source mode

The encrypted primary local configuration now selects:

```dotenv
LANES_NEWS_AUDITOR_PROVIDER=source_rules
LANES_NEWS_AUDITOR_MODEL=source-rules-v1
LANES_NEWS_AUDITOR_CONFIG_REVISION=source-rules-defense-20261013
```

Normal local development retains its pre-existing database binding; verify it before running a worker. The replay launcher explicitly selects local data. Existing provider keys are preserved but are not needed for news in source mode. Optional AI weather insights are a separate feature; do not treat this change as replacing every LLM use in LANES.

Production API/news/expiry use the same tested image and source mode. JWT signing is now bound to `lanes-jwt-signing-key` version 1 in Secret Manager; production users must sign in again. Do not copy credentials into the browser, docs or source. Existing production map code already supports these estimated zone responses; the new admin diagnostics wording is included in the accepted matching production frontend.

## Release safety and rollback

The focused image is based on main `cfd5aae`, without the unqualified MCP/framework upgrade. PR #134 integrates focused source/security changes into main 420b38f. The coordinated tested build and matching frontend rollout are verified. ROI retains the MCP experiment separately; its framework upgrades remain outside this release. [Release evidence](../evaluations/news-source-validation-20261013/README.md).

For a source-code rollback, pause only the news Scheduler and deploy a **new** revision using the prior baseline image while retaining the private `SECRET_KEY` binding. Do not restore traffic to old revisions with the public fallback key or recreate their retired public tags. Restore the previous explicit Gemini provider/model/revision only if deliberately returning to that limited/unqualified path; preserve its credential and quota history. Keep API/news/expiry images coordinated, then resume the captured adaptive Scheduler configuration. No database downgrade or deletion is needed.

## Full timeline acceptance

From backend, select a **fresh private loopback** PostgreSQL database named `lanes_nlp_acceptance_...` and source_rules/source-rules-v1, then run:

```powershell
python -m scripts.replay_news_source_timelines --scenario september24 --output '<private output directory>/september24.json'
python -m scripts.replay_news_source_timelines --scenario september9 --output '<private output directory>/september9.json'
```

Use a different fresh database for each command. Existing migrations are applied only when empty. The source HTML captures and early publisher-index text must be available in the preserved ignored `data/news-replay/september24-system` and `data/news-replay/september9` directories; captures are not downloaded or invented by the runner. Normal deployed code does not depend on these files. Receipts assert public HTTP 200, initial 19-inch and later 10-inch target publication, final expiry, no duplicate writes and zero inference. September 24 stale observations remain withheld.

The main-based source release includes Cloud Build regression checks, explicit source-mode configuration and a successful actual news-job execution before traffic promotion. Existing Scheduler and API machine identity remain configured separately. Keep the private signing-key Secret Manager binding. Frontend rollout must target the same accepted Git revision.
