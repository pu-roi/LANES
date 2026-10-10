# Local News Intelligence replay

> **Last Updated:** October 10, 2026, 6:36 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current connected availability:** #23 was deactivated at October 10, 6:00:29 PM by a shared scheduled worker with the real clock. The earlier connected reconstruction described below succeeded, but #23 is now inactive; its original data remains stored. A local frozen clock never overrides deactivation. System Settings → Evidence expiry now has an automatic-expiry toggle; matching shared API/worker rollout is required before changing cloud policy. It preserves active records only and does not restore #23. [Details](../evaluations/automatic-expiry-toggle-20261010.md).

## Connected source-faithful reconstruction on port 3000

The developer explicitly authorized testing the original historical article alongside their connected cloud records. This local development mode now shows actual automatic **Zone #23** plus Active Zones **17–21** through normal backend **8000** on frontend **3000**. Incorrect official #22 is deactivated and retained in history. Original private #56 remains intact. The actual system's new zone has the original Daily Tribune excerpt/title/link and unchanged September 24 **4:34 PM observation / 6:34 PM expiry**; no TEST labels, source rewriting or new current observation.

Run ordinary **Start LANES Dev Server** tasks and reload the public/Admin tabs. If the separate private frontend mode was enabled, **LANES: Use Current Data** selects normal backend 8000; it does not clear this backend scenario. View [Boni](http://localhost:3000/map?lat=14.58323758&lng=121.02823311&zoom=17) or [Admin Active Zones](http://localhost:3000/admin/map?tab=zones). Use **Zone #23 → Deactivate** when finished; actual lifecycle tests confirm the frozen clock cannot override deactivation. Preserve original information and interactions.

**LANES: Reconstruct Connected Boni** reruns collector, rules extraction, the configured real auditor, publication and footprint services. It is idempotent for the saved result, not a staff-zone copy, and does not reactivate a deactivated zone. It requires `--authorize-connected-reconstruction` and development environment. Original captured HTML drives the collector; historical RSS metadata is reconstructed because an authentic historical feed capture was unavailable. The operator command separately admits later-published evidence at September 25 **4:42 AM** while reconstructing September 24 **4:39 PM**, without changing article timestamps. It returns failure if no linked zone results.

Ignored `data/news-replay/connected-scenario.local.json` binds the selected case/zone clock to the database identity. Public/Admin zone lists, news projection/feed, routing and expiry maintenance apply September 24 4:39 PM only to those IDs. Other records use current time. Production ignores the file and ordinary HTTP publication does not obtain historical admission. Removing this exact local configuration restores real-time eligibility, so the historical zone disappears naturally. No SQLAlchemy model or migration changed.

**Verification:** Both readers return `[17,18,19,20,21,23]`; 18 other stored zone-response hashes match the baseline. Original geometry and excerpt match private #56. Desktop/mobile original source link, observed date, layers, common hover/fly/tap, Admin card/sign-in and deactivation confirmation pass. Developer visual acceptance remains pending; unrelated clearance auditor exceptions remain separate. [Evidence](../evaluations/news-boni-corridor-reconstruction-20261010.md#connected-source-fidelity-correction).

## Superseded official cloud display test

The #22 staff-copy approach was rejected because it omitted news decision/source linkage, inserted TEST notes and changed displayed dates. It was deactivated after the actual source-linked replacement was verified. Do not use or repeat that helper to prove automatic news behavior.

## Current persisted Boni reconstruction

The original system replay creates **Zone #56**. In VS Code run **Tasks: Run Task → Start LANES Reconstruction**, then open [public Boni map](http://localhost:3000/map?lat=14.58323758&lng=121.02823311&zoom=17) and [Admin Active Zones](http://localhost:3000/admin/map?tab=zones). The frontend launcher reuses this checkout's running **port 3000**, or starts it explicitly there; it never falls back to 3001. Reload existing tabs after enabling reconstruction. Private Admin login is `admin` / `admin` (verified locally). Public map checks use a signed-out reconstruction session; use a separate private window if an Admin session redirects you to the dashboard.

The visible **Historical flood reconstruction** label identifies the local session. All zone/Admin/auth/action/SSE calls target the guarded private backend on 8001; normal backend 8000 and its database are preserved. Reconstruction JWTs and dynamic flood IndexedDB use distinct storage keys, so local login/logout/offline fallback do not overwrite the normal session. Static routing tiles can be shared. These viewers use September 24, **4:39 PM** and do not process articles on startup.

To restore your normal data on the **same port 3000**, run **LANES: Use Current Data**, then reload every open LANES tab. Starting ordinary Dev/Production tasks does not reset an explicitly enabled reconstruction file; use the Current Data task to disable it. Production and non-loopback browsers ignore local reconstruction configuration. The earlier port-3001 instructions below are historical checkpoints, superseded by this section.

The source observation remains **4:34 PM**, expiry **6:34 PM** and later publication admission September 25 **4:42 AM**. To repeat the actual guarded collector/extractor/auditor/publisher/worker, run from `backend/`:

```powershell
node ../frontend/node_modules/@dotenvx/dotenvx/src/cli/dotenvx.js run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.replay_september24_pipeline --reconstruct --at 2026-09-24T16:39:00+08:00 --output ../data/news-replay/september24-reconstruction-repeat.json
```

The final repeat created no duplicate zone. Docker must be healthy and the configured/bound database must remain loopback `lanes_news_test`. The existing `.env.test.local` and dotenvx key must be available locally; never commit them. [Root causes, actual API/browser checks and remaining scope](../evaluations/news-boni-corridor-reconstruction-20261010.md). Earlier sessions below retain their historical outcomes.

## October 10 requested historical reconstruction

The developer selected reconstruction using the report's September 24 **4:34 PM** observation and later original article evidence. Run the existing system from `backend/` with the private dotenvx launcher:

```powershell
node ../frontend/node_modules/@dotenvx/dotenvx/src/cli/dotenvx.js run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.replay_september24_pipeline --reconstruct --at 2026-09-24T16:34:00+08:00 --output ../data/news-replay/september24-reconstructed-system-20261010.json
```

The real provider may time out. Advance the simulated present to the returned scheduled retry time (`16:35` in the recorded run) and rerun the same command with a different output filename. Do not substitute an auditor answer. Publication admission remains September 25 at 4:42 AM; original publication and observation dates are preserved. The policy and its stored JSON distinguish this from live collection. All writes require the dedicated loopback database.

For private browser inspection, set these variables in the backend-launcher terminal before starting `backend/start-persisted-news-simulation.ps1`; start the existing frontend launcher separately:

```powershell
$env:LANES_NEWS_SIMULATION_AT = '2026-09-24T16:35:00+08:00'
$env:LANES_NEWS_RECONSTRUCTION_PUBLICATION_AT = '2026-09-25T04:42:00+08:00'
```

Open `http://127.0.0.1:3001/map` and `/admin/map`. The original Boni now appears in News alerts as a verified text observation and remains available for placement review; neither map has a Boni Active polygon because its four road alternatives have arbitrary bounds. Public/Admin only draw persisted zones. [Actual system replay and regression evidence](../evaluations/news-reconstruction-activation-fixes-20261010.md). Earlier clocks and approval conclusions below are historical.

**Latest October 10 persisted session (supersedes preview-as-activation expectations):** Start `backend/start-persisted-news-simulation.ps1` and `frontend/start-persisted-news-simulation.ps1` from the repository root in separate terminals. Open `http://127.0.0.1:3001/map` and `/admin/map`; sign into the existing private account. All API/auth/SSE reads and actions use guarded loopback `lanes_news_test` on 8001, with the September 25 4:42 AM read clock. Public/Admin render only persisted active zones; no preview overlay. Original Boni currently creates zero zones; five locations remain in News Intelligence. Normal port 3000 retains its connected API and records. The frontend uses a separate build directory and restores the previous ignored mode file on exit. Backend startup performs no collection/publication and omits wall-time retention. Existing socket errors recovered after two stopped-state runtime-folder backups; database volumes were preserved. [Evidence and policy distinctions](../evaluations/news-persisted-simulation-session-20261010.md).

> **Last Updated:** October 10, 2026, 4:13 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> Author: [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Latest October 10 overlap correction:** Public replay draws the two-layer display only when placement resolves to one eligible section. Original Boni is ambiguous, so its `display_zone` is null and it is excluded from public painting and camera bounds. Inspect its four preserved alternatives one at a time through News Intelligence → Inspect placement on map → Admin Needs Review. Restart only the guarded snapshot launcher and reload after this change; normal API/auth and active zones 17/18 remain on their normal connection. [Evidence](../evaluations/news-placement-alternatives-20261010.md). This supersedes the earlier all-carriageway public appearance described below.

## Current port-3000 simulation session

**October 10 inner/outer appearance:** Public automatic plotting now renders a solid road core plus one dissolved decorative polygon halo with canonical Active paint. Restart the guarded snapshot launcher after pulling this change and reload the map: the response must include `placement.preview.display_zone` with both geometries. Backend uses the staff default 25-m margin for decoration only. Original source status remains Needs Review; this appearance does not publish a zone or change routing. Admin Needs Review keeps its original aura-only style. The preceding single-layer public behavior is superseded. [Evidence](../evaluations/news-shared-map-renderer-20261009.md#october-10-requested-solid-inner-line-and-transparent-outer-area).

**Latest shared-renderer correction:** Reload the map after frontend changes. The guarded 8001 snapshot server now supplies three drawable sections from four original Boni candidates, using the same backend display service as admin placement. News is a data adapter into the existing zone hook; detail is shown at zoom 14+, overview pins below 14. Desktop click only flies to zoom 16, hover shows details; mobile tap shows the common modal and explicit close permits reopening. Original Boni remains Needs Review and has no active solid core/polygon or staff Active Zones entry. The older overview-visible/independent-controller behavior described below is superseded. [Verification and limits](../evaluations/news-shared-map-renderer-20261009.md).

Use **http://localhost:3000/map** and **http://localhost:3000/admin/news**, with a full reload to load the changed frontend. API, login/profile, zone operations and live SSE now use the **normal connected database**, preserving existing zones 17/18. Use the normal account; if the earlier private test login is still stored, sign back into the normal account. The developer clarified that no existing work should be removed and September 24 must be additive.

Expected: the original interface without the added simulation status box, **five** extracted locations from connected-database article 25/run 61 and **four** backend-generated Boni road candidates added alongside existing zones. The box is removed from map, News Intelligence and both news-alert layouts following explicit developer correction. Camera bounds include both current zone geometries and replay candidates; transparent review lines remain visible at overview zooms. The normal extractor processes the original captured body; no polygon is manually inserted. Source approval, chronology/section uncertainty and current Pasig model scope still prevent active-zone/subsidence completion. The simulated present is September 25, 4:42 AM, immediately after the selected story's first publication.

The explicit requested addition used `dotenvx run -f .env -- ./venv/Scripts/python.exe -m scripts.add_september24_news --expected-database lanes --write --output ../data/news-replay/september24-cloud-addition.json`. This exact-article operator capture uses `save_candidate`, `process_saved_news`, scoped `seed_claim_evaluations` and the actual estimated-road builder. Original body hash, dates and measurements remain unchanged; idempotent repeats retain the existing article/run. This is not proof of authentic historical RSS collection. Evaluation stops with `unapproved_article_source`; automatic publication is not executed.

Start frontend normally with `npm run dev`. The ignored local JSON mode file now selects **only** the additional `/news/simulation` snapshot, not global API/auth/database routing. The guarded snapshot server remains on 8001 and reads the service-produced connected-database capture artifact, including real run 61 identity; fallback private replay remains isolated. Restart it using `dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.serve_local_news_replay`. Its configured and bound engines must remain loopback `lanes_news_test`. This launcher never performs cloud writes.

Verification compares full public zone snapshots before/after: existing zones 17/18 are identical. Eleven backend addition/guard/clock checks, TypeScript/scoped lint and browser-free additive camera/API/SSE contracts pass. No browser or physical device rendering is claimed. Prior port-3001, global private routing and invented-article instructions are superseded.

## September 24 as the simulated present: zone-only scope

The developer requests the collector → extraction → OSM/NOAH → active flood zone → subsidence path, without flood report panel work. Run existing captures from `backend` with `dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.replay_september24_pipeline --timeline --output ../data/news-replay/september24-system/timeline-with-subsidence.json`. Alternatively use `--at 2026-09-24T16:59:00+08:00` for one checkpoint. This clock acts as the simulated present; it does not rewrite source dates. Future publisher snapshots are unavailable. Both configured and bound URLs must be the dedicated loopback database.

The actual zone reader now accepts a backend-only `now` argument for isolated simulations, preserving PostgreSQL time for normal requests. Pipeline and reader use the same simulation clock. The three checked times return zero candidates/zones, so the zone-dependent prediction stage is explicitly `not_reached_no_new_zone`; this is not a successful full-chain demonstration. The model itself loads, and separate read-only checks on existing cloud zones exercise registration/submission proxy estimates. The current zone prediction adapter excludes estimated news corridors and current model scope is Pasig; neither boundary is overridden. [Evidence and test counts](../evaluations/september24-plotting-simulation-20261009.md#september-24-as-the-simulated-present-zone-and-subsidence-checks).

## October 9: Corrected scope — actual published reports through backend services

The developer rejects the fabricated article/stubbed audit demonstration and requires the system's collector/pipeline on actual September 24 coverage. `scripts/replay_september24_pipeline.py` captures three original publisher HTML/body snapshots through the bounded fetcher: two September 24 GMA weather advisories and Tribune's event story, published September 25 at 4:41 AM. A process-local clock is September 25 at 4:42 AM, the article's first availability. Original text, dates, approvals and geometry assets remain unchanged. Authentic historical RSS is unavailable: only known titles/URLs/publication metadata are reconstructed, without assumed descriptions. This is partial known-article coverage, not complete historical feed acceptance.

Normal `discover_news` parses two approved GMA entries and admits **zero** flood candidates. Tribune is absent from the approved publisher registry. Normal `run_news_pipeline` admits no evaluations/publications and skips saved run 57 with `unapproved_article_source`; **zero new zones** result. The configured real `NewsClaimAuditor` receives **zero calls** because no claim reaches it. Read-only original-body diagnostics retain five Tribune roads and four Boni modeled previews: Boni is already 12 hours 8 minutes old/passable-all with ambiguous sections; Quirino/Gov. Pascual lack observation time and grounded placement; East/Aurora are cleared. No gate or source registration is overridden to produce a polygon.

Run from `backend`: `dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.replay_september24_pipeline --capture --output ../data/news-replay/september24-system/result.json`. Omit `--capture` to reuse HTML. Both configured and bound database URLs must pass the private-target guard. The earlier fabricated **zone 55 is archived** through the normal private admin API; local public Active Zones returns zero. Shared zones 17/18 remain unchanged. Earlier demonstration links below are superseded.

The shared public-map coordinate handoff also removed URL parameters before its delayed camera action. Next history synchronization could rerun cleanup and cancel that timer. Move removal after camera movement; a Node harness reproduces the original cancellation and verifies corrected ordering at 390/1365 fixture widths without a browser. TypeScript and 53 backend replay/pipeline/guard checks pass. Actual mobile/desktop rendering remains pending. The authentic September 24 run **has not demonstrated successful polygon activation**.

## October 9: Superseded fabricated active plotting demonstration

The developer subsequently requests an active simulation. `backend/scripts/seed_local_news_simulation.py` discovers a separately labeled fabricated RSS article, using the normal extractor, bundled checked OSM/UP NOAH, audit evidence validator, publication services and PostGIS. Publisher/feed HTTP and the paid auditor answer are MockTransport fixtures; no external provider charges or browser calls. Both configured and bound URLs must pass the loopback `lanes_news_test` guard before writes. The fixture source is injected only into this local run, never the production registry.

Fresh observation/publication time, **Quirino Avenue from Asuncion Street to Camia Street in Manila**, hypothetical **knee depth** and unknown vehicle access are explicitly synthetic inputs. The original September 24 article/run 57 remains intact. Article **6**, run **60**, case **5** automatically create zone **55**, with Polygon aura and LineString core. Source/name explicitly say **SIMULATION**. It expires **October 9, 4:28 AM Manila**. Display naming is added after creation; no polygon is manually inserted and activation gates remain enabled.

- Public map: **http://127.0.0.1:3001/map?lat=14.5673884&lng=120.989284&zoom=17**.
- Staff Active Zones: **http://127.0.0.1:3001/admin/map?tab=zones&lat=14.5673884&lng=120.989284&zoom=17**. Local login **admin / admin**; reopen the link after signing in.
- The existing design shows markers at zoom 14 and below. Zoom 17 exposes the solid road core and transparent outer layer.

Public and authenticated staff APIs return zone 55; the public page returns HTTP 200. Seventeen focused checks pass, including normal audit offset rejection and shared/overridden database refusal. No browser rendering is claimed. The original 3000/8000 processes had stopped; only frontend 3000 was restarted for the 3001 proxy's page upstream. Private backend 8001 remains the API target; shared data are unchanged. Use **3001** for this simulation.

Repeat from `backend`: `dotenvx run -f .env.test.local -f .env -- ./venv/Scripts/python.exe -m scripts.seed_local_news_simulation --output ../data/news-replay/september24-active-simulation.json`. Each invocation creates new synthetic evidence with normal finite expiry. Private output records assumptions and stage counters.

The first fixture's `between Asuncion Street and Camia Street` wording became three extracted roads rather than a bounded primary claim, so Quirino remained Needs Review (`candidate_set_truncated`). The successful fixture uses the supported `from ... to ...` form. This wording limitation remains open; the successful run does not establish arbitrary article accuracy or actual independent LLM verification.

## October 9: September 24 manual map inspection

The developer chose historical review replay rather than a synthetic active-zone demo. Offline captured-body processing creates immutable run **57**, with five readable road records and unchanged zone totals in guarded loopback database `lanes_news_test`. Existing migration `d7e4b9a21c60` was applied after the older `c5a7e9d2104f` setup caused a missing `news_claim_sources` table and HTTP 503 in the review reader. No model or migration definition was changed.

The original frontend/backend continue on ports **3000/8000**. A separate private backend runs on **8001** with `.env.test.local` taking precedence. A lightweight loopback-only preview proxy on **3001** forwards frontend pages/assets to 3000 and `/api/v1` requests to 8001. This avoids a second full frontend build and leaves the current frontend's API configuration unchanged. A copied frontend under ignored `data/news-replay/september24-frontend-20261009/` was prepared but its duplicate development server was stopped because the cold build was slow; it is not the running preview.

1. Open **http://127.0.0.1:3001/admin/news** yourself; use the local-only **admin / admin** account if prompted.
2. Search **Minor flooding**, open Boni Avenue's **Info**, then choose **Inspect placement on map**. The shared button is available on both desktop and mobile layouts.
3. Alternatively, after signing in, open **http://127.0.0.1:3001/admin/map?review_news=57:1** directly.
4. Inspect the four modeled placement suggestions using the existing transparent review aura. The panel should explain that this preserved item no longer belongs to the current review queue. Old evidence is intentionally absent from that current queue; no observation/publication date or freshness gate was changed.

HTTP checks pass for authentication, five saved results, archived review detail, placement and the map page. The archived detail reports `is_current_review=false` and `news_actions_available=false`; all four Boni candidates have modeled preview linework but ambiguous selection. Port 3001 has **zero active zones**, while the original port 3000 still returns existing zones **17/18**. Private result metadata is under `data/news-replay/september24-frontend-ready-20261009.json`. TypeScript and scoped dialog lint pass. No browser was opened, so rendering, map tiles and physical desktop/mobile inspection remain user acceptance steps.

The current running preview uses ignored helper `data/news-replay/september24_review_proxy.py` with the existing backend interpreter. Restart its backend using the established private environment and `uvicorn app.main:app --host 127.0.0.1 --port 8001`, then run the proxy script. It binds only to loopback and uses fixed loopback upstreams. It is a temporary HTTP/SSE inspection proxy; it does not proxy Next's development HMR WebSocket, so reload the page after future frontend edits. Stop only these preview processes when finished; preserve the original servers and database.

Earlier version/count/port checkpoints below describe their dated setup. The new map handoff selects existing read-only inspection; it does not activate historical flooding or publish a live alert.

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
