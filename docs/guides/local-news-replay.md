# Local News Intelligence replay

> **Last Updated:** October 03, 2026, 8:09 PM
> Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

The September 24 Daily Tribune report is saved in the separate Docker PostgreSQL/PostGIS database `lanes_news_test`. Version v6 produces five readable road sites; the two broad city summaries remain source context in processing history. This is a historical article demonstration, not current flooding or automatic map activation. Its publisher label includes **local historical test**, and its original event/publication dates are preserved.

The September 9 replay now adds three actual reports with **33 readable location records** (27 Philstar, 3 GMA alert, 3 GMA evening). They share one historical day and retain original dates. The September 24 article remains with five roads. Current local processing is v8/v1.6; older saved runs remain available. Twenty records preserve explicit cautious passability, shown in Flood Details. See [day replay evidence](../evaluations/phase-36-september9-production-day-replay.md) and [workflow follow-up](../evaluations/phase-36-news-workflow-follow-up.md).

## Start the private local servers

The latest four-article re-audit is local **v9/v1.7**, with 38 locations/four articles/five input versions/fourteen runs. Source depth wording is shown without invented precision; two Tribune corridors retain generic passability and the cleared roads retain **by** timestamps. Four wrong province labels are corrected. Earlier version/count statements below record replay history. [Current audit](../evaluations/phase-36-four-article-source-audit.md). Refresh the page after the backend restart to load current labels; browser visual acceptance remains incomplete.

Docker Desktop must be running. The existing `lanes_postgis_db` container and volume supply PostgreSQL; the existing `lanes` database is preserved. The ignored `backend/.env.test.local` sets the dedicated local `DATABASE_URL`, development mode and a separate local JWT signing key. The encrypted shared `backend/.env` remains the cloud configuration. No credential values belong in this guide or in tracked source files.

From the repository root, run these in two PowerShell terminals:

```powershell
./backend/start-local-news-test.ps1
```

```powershell
./frontend/start-local-news-test.ps1
```

Both servers bind to `127.0.0.1` (backend 8000, frontend 3000). Stop a server using its existing terminal before starting a replacement. The private backend runs without auto-reload because Windows reload workers lost their inherited socket; restart explicitly after backend edits. Open **http://127.0.0.1:3000/admin/news**. Sign in with the existing local bootstrap credentials **admin / admin**; these belong only to the separate local database. A cloud session does not authenticate against the separate local signing key. September 24 browser verification was completed earlier. September 9 authenticated API and frontend proxy list/detail checks pass; its final visual check remains blocked by the browser tool's saved permission setting.

With no search or publisher filters, the main list contains 38 records across both replay dates. The September 9 evening title does not contain the date, so searching only “September 9” omits its three locations. Use the article titles or their local historical test publisher labels to distinguish them. Collection defaults to **Needs attention**: the September 9 articles retain questionable/context mentions and can appear there. Choose **All saved articles** or **Locations available** to inspect all four articles; September 24 alone remains ready with zero questionable mentions.

## Repeat the September 9 day test

Run from `backend`:

```powershell
dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.replay_september9_news --persist --output ../data/news-replay/september9/persisted-result.json
```

This uses ignored captured publisher HTML under `data/news-replay/september9/`, reconstructed RSS and a fixed September 9 11:00 PM Philippine clock. It is not an authentic archived-feed test. Missing captures can be fetched with `--capture` before replay; run `--help` for capture/preview options. Only the dedicated loopback PostgreSQL test target is accepted before writes, checking both configuration and the bound engine. No live feed registration, age-policy override outside this one-shot process, production write or historical zone activation occurs. Repeating identical input/version leaves counts unchanged and preserves older runs.

The 27 Philstar rows share 4:30 PM; the three GMA alert rows have 2:47 PM supported by the explicit 3:09 PM publisher update while preserving 9:19 AM publication. Evening report times/depths/passability remain unknown where unstated. Caution wording and its distinct `passable_with_caution` status are preserved; it cannot authorize automatic closure or unrestricted vehicle applicability.

## Repeat the saved article test

Run from `backend`:

```powershell
dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.seed_local_news_replay
```

This fetches the publisher and uses the existing evidence policy, candidate saver, durable queue and API reader services. Only loopback PostgreSQL database `lanes_news_test` is accepted; cloud, the existing `lanes` database and connection-target query overrides are rejected before writes. Repeating identical input at the same pipeline revision creates no duplicate article, source version or extraction run. A revision change preserves the older run and creates a new one; the September 24 subset currently has one article and two runs (v5 and v6). Running it under current v8 creates a further immutable run. It checks five readable road locations, absence of automatic approval and unchanged zone totals.

For the locally captured source body, use the optional offline form:

```powershell
dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.seed_local_news_replay --body-file ../data/news-replay/september24-body.txt
```

The captured body is private, Git-ignored test data. The replay preserves September 24 observation times and September 25 publication. It deliberately does not alter live source registration, the seven-day discovery age policy, production data or map/routing eligibility.

## Existing migrations and return to cloud-backed development

The complete existing migration chain was applied successfully to the new database, ending at `c5a7e9d2104f`. No SQLAlchemy model or migration was changed for this setup. To check or upgrade that local database, use the same explicit test environment:

```powershell
dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m alembic current
dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m alembic upgrade head
```

To return to the previous cloud-backed local backend, stop the test backend and launch the normal backend using only `dotenvx run -f .env`, omitting `.env.test.local`. Restart/sign in again as needed. The private test file and database can remain for later testing. A Git push is unnecessary for this switch; the dedicated launchers choose the configuration for that process only.

## Docker startup recovery performed on October 3

Docker Desktop 4.91.0 failed to rename its Ingest and Secrets Engine sockets with Windows error 1920. After verified Desktop/backend shutdown, the socket directories were renamed as recoverable backups. Both had to be isolated in the same stopped state because a failed start left fresh unusable sockets. Docker then started and both original containers resumed.

Preserved runtime backups are under the existing user-local Docker directories: `Docker/run.backup-20261003-1320`, `Docker/run.backup-20261003-1315`, and `docker-secrets-engine.backup-20261003-1320`. No factory reset, volume deletion, WSL unregister or disk-image modification was performed. This records the recovery observed on this computer, not a universal or maintainer-approved repair. Similar failures are reported in [Docker's issue tracker](https://github.com/docker/desktop-feedback/issues/675); [Docker troubleshooting documentation](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/) describes restart/reset alternatives.
