# News-zone release: exact operator steps

> **Last Updated:** October 07, 2026, 12:45 AM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Current state and responsibility

The developer has configured `lanes-api` and `lanes-news-discovery` in Google
Cloud with `LANES_NEWS_AUDITOR_PROVIDER=openrouter`,
`LANES_NEWS_AUDITOR_MODEL=openrouter/free`, and an OpenRouter key. These were
verified by read-only Cloud Run inspection. The deployed job still uses
`--process`; the new pipeline and map integration remain local/uncommitted.
The last cloud database check returned `c5a7e9d2104f`; the required existing
publication migration is `d7e4b9a21c60`.

Repository preparation is agent/developer work, not another key-copying task:
the Metro Manila NOAH bundle is now under `backend/runtime_data/noah-placement`,
with 897 original gzip tiles, preserved checksums and ODbL attribution. Docker
checks OSM, qualified barangay, NOAH and Pasig history assets during the build.
No new SQLAlchemy model, migration or dependency was introduced.

Do not interpret configuration, offline tests or synthetic probing as successful
current-article publication. Use the ordered steps below.

## 1. Check the free auditor locally before release

**Completed locally on October 7:** The agent's corrected synthetic probe passed
at both the normal 20-second worker deadline and a 60-second override. Exact
source quotes/offsets validated, and the January 2020 fixture remained historical
review. The Linux build/offline asset checks in step 2 also passed. You can
continue to the reviewed commit/push step; repeat these commands only if code or
configuration changes. [Current verification](../evaluations/phase-36-auditor-evidence-options-20261007.md).

In VS Code, open **Terminal → New Terminal**, then paste:

```powershell
Set-Location D:\Documents\Github\LANES\backend
dotenvx run -f .env -- .\venv\Scripts\python.exe -m scripts.check_news_auditor
```

Expected: `"status": "configuration_ok"`, provider `openrouter`, model
`openrouter/free`, and `"provider_request_made": false`. This checks the normal
cloud-backed local backend configuration without connecting to the database.
Do not print or share API keys.

To explicitly test one free AI response, run:

```powershell
dotenvx run -f .env -- .\venv\Scripts\python.exe -m scripts.check_news_auditor --probe
```

This makes **one request only** to the explicit free router, using an invented
historical article. It does not read/write a database, collect news or create
alerts/zones. It refuses other model selections, including `openrouter/auto:free`.
Expected: `"status": "valid_response"`. `"outcome": "review"` is expected for
historical synthetic evidence. `configuration_error`, `probe_failed` or nonzero
exit means stop and inspect the safe reason code; do not enable a paid fallback
or bypass confirmation. Rate limits and unavailable compatible models remain
possible. No live probe was run as part of the initial packaging work.

### Earlier timeout follow-up, subsequently repaired locally

The developer's first live probe returned `auditor_timeout` under the existing
20-second deadline. The command now supports a bounded per-probe override:

```powershell
dotenvx run -f .env -- .\venv\Scripts\python.exe -m scripts.check_news_auditor --probe --timeout-seconds 60
```

The agent's first such retry received a response, but strict
verification rejected it with `audit_evidence_offset_mismatch`: the returned
quote positions did not match the article text. The subsequent prompt v2 repair
supplies server-calculated source span options for the model to copy. Strict
source checks remain; probes now pass at both 20 and 60 seconds. Do not repeatedly
retry a new invalid audit hoping to bypass verification. OpenRouter documents
possible higher latency and changing
availability for its [free router](https://openrouter.ai/docs/guides/routing/routers/free-router);
this does not establish the cause of the original timeout.

The override permits 1-120 seconds, bounds both the HTTP exchange and complete
response, makes no extra retries and changes no persistent local/cloud setting.
Normal worker requests still default to 20 seconds; the successful default-limit
probe uses that same setting. No database access/public writes occurred. The
synthetic samples do not establish sustained free-provider availability or
successful current-article activation. New HTTP failures now include a safe
numeric `provider_http_status`; raw provider messages/keys remain excluded.

## 2. Verify the local release image and assets

Docker Desktop must be running. From a new terminal at the repository root:

```powershell
Set-Location D:\Documents\Github\LANES
docker build -t lanes-news-release-check:20261007 -f backend/Dockerfile backend
docker run --rm --network none lanes-news-release-check:20261007 python -m scripts.verify_news_runtime_assets
```

Expected: build succeeds; verification prints `"status": "assets_ok"`,
`"noah_tile_count": 897`, and `"qualified_barangay_count": 20`. This is accepted
partial community-boundary coverage, not a claim that all NCR barangays are
supported. The NOAH manifest identity is
`cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce`.
The check makes no provider requests or database writes.

The agent also verifies the existing migration in a newly created disposable
loopback PostGIS database, then removes that database. Do not manually run
`alembic upgrade head` against your cloud database just to inspect it.

## 3. Save the reviewed changes to roi-branch

After the image checks and provider probe pass, review the working changes and
commit/push to `roi-branch` using the repository's AGENTS.md push protocol.
If working with Codex, explicitly request **"update the documentation and push
to roi-branch"**; the agent handles branch/dependency/migration checks and Git.
This guide does not claim those actions have already happened.

## 4. Merge through GitHub and watch deployment

1. Open the LANES GitHub repository and select **Pull requests**.
2. Open the existing `roi-branch` → `main` PR, or click **New pull request**.
3. Set **base** to `main` and **compare** to `roi-branch`. Review the complete diff
   and checks; create the PR if needed, then merge through the approved workflow.
4. Open Google Cloud Console, select `lanes-project-508809`, search **Cloud Build**,
   and open **History**.
5. Open the build for that merge commit. Confirm it finishes successfully. The
   build updates and executes `lanes-migration` before deploying `lanes-api` and
   the `lanes-news-discovery` job. If any step fails, inspect its log and stop;
   do not manually skip the migration.
6. Open **Cloud Run → Jobs → lanes-migration → Executions**. Confirm the
   execution created by the build succeeded. The deployed schema must reach
   `d7e4b9a21c60`; read-only verification should confirm the revision.
7. Open **Cloud Run → Jobs → lanes-news-discovery → View and edit job
   configuration**. Verify command `python` and separate arguments
   `-m scripts.run_news_discovery --discover --pipeline --limit 50`. Check that
   the configured free auditor variables/key remain present.
8. Open **Cloud Run → Services → lanes-api → Revision History**. Confirm the
   new revision is ready and serves traffic, with the same reviewed image as
   the news job. Retain the existing database and routing configuration.

These are live release steps. They were not performed during local packaging.

## 5. Verify the frontend rollout separately

Open **Firebase Console → LANES project → App Hosting → lanes-frontend**.
Check the rollout for the same merged Git revision. If automatic rollout has not
occurred, inspect its rollout settings/live branch and create a rollout using the
supported Firebase workflow. Root `cloudbuild.yaml` deploys the backend, not the
frontend. Do not assume backend success means the frontend changed.

For local UI inspection, use VS Code **Terminal → Run Task → Start LANES Dev
Server**. Its existing tasks load `backend/.env` and `frontend/.env.local`; the
frontend currently uses `/api/v1` through the local backend, which uses your
configured cloud database. Restart the backend to load changed local settings.
The separate `start-local-news-test.ps1` launchers select the dedicated local
test database and are not required for your normal cloud-backed development.

## 6. Execute one controlled current-article check

Only after the schema/image/assets/provider checks pass, open **Cloud Run →
Jobs → lanes-news-discovery**, click **Execute**, and open the resulting execution
and its logs. This run fetches enabled feeds and can write real alerts/zones to
the cloud database. Avoid simultaneous manual local pipeline execution.

Inspect the JSON summary: `publication.published` alone is a source alert;
`footprints.estimated_activated` greater than zero establishes estimated-zone
activation. Inspect per-claim reason codes when no zone is created. A successful
run with no qualifying current reports is valid; do not fabricate an observation
time/depth or republish the September fixtures as current flooding.

Open `/admin/news`, `/admin/map`, and `/map` in the local or deployed frontend.
Use **Needs Review** for a selected transparent placement preview where valid
geometry exists; use **Active Zones** to inspect eligible core plus aura layers.
Zoom to street level, wait for the map refresh (approximately 15 seconds), and
inspect source, observation time, expiry and estimated-road labeling. Verify
desktop hover details and mobile tap details using the existing design.
Then check applicable vehicle routing and duplicate/refresh/clearance/expiry
behavior. Expiry is observation time plus two hours, not two hours after this run.

## 7. Review scheduling after the controlled run

The current scheduler is `lanes-news-discovery-every-3-hours` at `0 */3 * * *`
in `Asia/Manila`. That interval can miss evidence with a two-hour validity window.
Review a shorter collection/maintenance interval against measured execution
time, free-router quotas and cloud costs before changing the scheduler. Local
packaging did not change its frequency or establish physical PWA acceptance.

## Docker socket startup recovery performed October 7

Docker failed before engine startup while renaming `sailor-ingest.sock`. Its
Linux distro was stopped, and the two inspected runtime directories contained
only zero-byte endpoints. The normal CLI stop failed; recognized crashed Docker
processes were stopped. The directories were preserved as sibling backups:

- `%LOCALAPPDATA%\Docker\run.lanes-socket-backup-20261007-001138`
- `%LOCALAPPDATA%\docker-secrets-engine.lanes-socket-backup-20261007-001138`

Fresh runtime directories were created and Docker restarted successfully.
Engine `29.8.0`, the original `lanes_postgis_db`/`lanes_valhalla` containers and
`lanes_lanes_db_data` volume were observed afterward. No factory reset, WSL
unregister, persistent disk/volume removal or cloud database change occurred.
This workaround matches [reports in Docker's issue tracker](https://github.com/docker/desktop-feedback/issues/554);
recurrence after a later stop/start is possible and is not fixed by this LANES
packaging change.
