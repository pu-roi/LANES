# Local News Intelligence replay

> **Last Updated:** October 03, 2026, 5:24 PM
> Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

The September 24 Daily Tribune report is saved in the separate Docker PostgreSQL/PostGIS database `lanes_news_test`. Version v6 produces five readable road sites; the two broad city summaries remain source context in processing history. This is a historical article demonstration, not current flooding or automatic map activation. Its publisher label includes **local historical test**, and its original event/publication dates are preserved.

## Start the private local servers

Docker Desktop must be running. The existing `lanes_postgis_db` container and volume supply PostgreSQL; the existing `lanes` database is preserved. The ignored `backend/.env.test.local` sets the dedicated local `DATABASE_URL`, development mode and a separate local JWT signing key. The encrypted shared `backend/.env` remains the cloud configuration. No credential values belong in this guide or in tracked source files.

From the repository root, run these in two PowerShell terminals:

```powershell
./backend/start-local-news-test.ps1
```

```powershell
./frontend/start-local-news-test.ps1
```

Both servers bind to `127.0.0.1` (backend 8000, frontend 3000). Stop a server using its existing terminal before starting a replacement. Open **http://127.0.0.1:3000/admin/news**. Sign in with the existing local bootstrap credentials **admin / admin**; these belong only to the separate local database. A cloud session does not authenticate against the separate local signing key. The agent verified the real login and main page, claim detail, captured source text and Collection status through the real API, without mocking requests.

The main list shows five street locations. Collection defaults to **Needs attention**, which correctly has zero items; choose **All saved articles** or **Locations available** to see the processed article and its five locations / zero mentions needing checks.

## Repeat the saved article test

Run from `backend`:

```powershell
dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.seed_local_news_replay
```

This fetches the publisher and uses the existing evidence policy, candidate saver, durable queue and API reader services. Only loopback PostgreSQL database `lanes_news_test` is accepted; cloud, the existing `lanes` database and connection-target query overrides are rejected before writes. Repeating identical input at the same pipeline revision creates no duplicate article, source version or extraction run. A revision change preserves the older run and creates a new one; the saved replay currently has one article and two runs (v5 and v6). It checks five readable road locations, absence of automatic approval and unchanged zone totals.

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
