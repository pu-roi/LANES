# News collection, automatic plotting and lifecycle audit

> **Last Updated:** October 07, 2026, 6:31 PM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Result

News collection is operating in production. Automatic estimated-road activation,
map presentation and lifecycle pass controlled verification, but no qualifying
current news report has exercised production publication. An empty public map
does not by itself demonstrate either a failure or successful live plotting.

The scope is the current news-to-map delivery in `task_plan.md`, including its
auditor, OSM/NOAH placement, source alerts, staff exceptions, routing, refresh,
clearance and expiry. This is not acceptance of every historical milestone or
backlog feature.

## Read-only production evidence

- API `lanes-api-00057-cuf` receives 100% of traffic. Its health endpoint returned
  HTTP 200 with the database connected. Public news alerts returned total 0;
  active zones returned an empty array. Unauthenticated staff monitoring returned
  HTTP 401.
- Scheduler `lanes-news-discovery-every-3-hours` is enabled in Asia/Manila. The
  deployed job uses the matching `perf2-c361b61-20261007` image, 1 GiB and
  `--discover --pipeline --limit 50`.
- All six inspected executions succeeded: October 7 at 3, 6, 9 AM and noon,
  3 and 6 PM Philippine time. Latest execution `lanes-news-discovery-r68rq`
  completed at 6:00:41 PM. No ERROR-level job log was returned for this interval.
  This verifies successful scheduled operation after the memory change, not peak
  memory usage or sustained flood-event load.
- Persisted discovery run 52 completed. All six feeds parsed successfully:
  GMA 15 entries, INQUIRER 20, Rappler 10, Philstar 10, BusinessWorld 29 and
  Interaksyon 10: **94 entries**, zero saved candidates, zero feed/body errors.
  Logged notices include non-Metro Manila geography and an El Niño explainer
  without body-grounded Metro Manila flood evidence. Many non-flood headlines
  are skipped before article capture; these notices are not a 94-article body audit.
- Cloud database reads used `SET TRANSACTION READ ONLY`. There are 24 saved
  articles, all excluded by current collection policy, zero displayed claims,
  zero attention articles, 10 completed current-pipeline runs and 50 completed
  extraction runs across preserved history. There are zero claim cases,
  evaluations, decisions and zone links. Latest saved article sighting is
  September 30; current successful feed polling is independently recorded.
- Existing migration head is `d7e4b9a21c60`. No production database write,
  collector execution, publication, deployment or schedule change was triggered.
- Job auditor provider/model are `openrouter` / `openrouter/free`. Local encrypted
  configuration passes the free-only configuration check with the 20-second
  worker deadline. Configuration does not establish provider reliability.

`footprints.catalog_status = not_configured` refers to the optional approved
current-incident perimeter catalog. The separate estimated OSM/NOAH path remains
connected; its latest considered/activated counts are zero because no published
claim exists. Do not interpret this field alone as a missing estimated-road worker.

## Verification

| Check | Result and scope |
|---|---|
| Focused backend suites | **273 passed** across pipeline/CLI, extraction admission, independent audit, geometry/estimates, activation safety, temporal/passability rules, lifecycle, sync, weather concurrency and vehicle routing. |
| Native PostGIS lifecycle suite | **131 passed**, including full existing Alembic upgrade, automatic estimated and approved-footprint activation, actual public-zone API reads, routing, rollback/concurrency/idempotency, supported refresh, clearance and expiry. Extraction/auditor/incident evidence uses controlled fixtures. |
| Deployed frontend with intercepted fixtures | **10 public desktop/mobile checks passed**: visible solid road core and transparent polygon, source/basis details, pagination, SSE updates, offline/failure feedback and bounded polling. |
| Staff decisions with intercepted API/session | Four distinct desktop/mobile cases pass across runs, including preserved drafts, stable retry identity and lost-response history recovery. One desktop save-feedback check failed during concurrent verification, then passed alone in 14.3 seconds. No real staff decision was submitted. |
| Runtime bundle | `assets_ok`: 897 NOAH tiles, 20 qualified barangays, matching OSM/barangay/history identities; NOAH manifest `cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce`. This is partial placement coverage, not live flood proof. |
| Test lint | Scoped ESLint passed for the two modified browser fixtures. |
| Live free synthetic auditor probe | **Failed: `auditor_timeout`** at the normal 20-second deadline, outcome `unavailable`, no HTTP status received. One request only; historical fixture, no database access/public writes. Earlier successful probes do not guarantee current availability. |

The 71-check early backend run overlaps the 273-check run and is not additive.
The final distinct backend total is **404**. Existing multipart deprecation
warnings remain; no dependency/model/migration definitions changed.

Initial public browser checks failed during Docker recovery. The public alert
fixture used an uncontrolled browser clock, and failed output showed refreshing
cached status instead of current Active. Pin the browser clock to each fixture's
server time in `news-zone-map.spec.ts` and `public-news-alerts.spec.ts`; retain the
polling test's timer advance. Both desktop/mobile suites passed serially afterward.
No application freshness or expiry gate was relaxed. The first polygon timeout
does not establish a calendar-expiry renderer defect.

The separate failed staff trace showed its mocked save response taking 7.18 seconds
and history response 7.43 seconds, beyond the five-second UI assertion. Mobile
passed and the isolated desktop rerun passed. Keep the resource/timing limitation
visible; a permanent staff implementation defect was not demonstrated.

The first native attempt was refused by the fixture's empty-database guard:
the PostGIS image initialized extension tables in its default database. Create
a separate empty database from `template0` inside the disposable test container;
the unchanged guard and all 131 tests then pass. This was runner setup, not a
schema failure. Only the audit container/databases/anonymous volume are disposable;
the original local/cloud databases are preserved. After verification the exact
audit container and its sole anonymous volume were removed.

## Docker interruption and recovery

The user reported `sailor-ingest.sock` rename/file-access failure after the audit
started Docker. Stop the identified failed Desktop/backend processes, verify
their exit, and inspect exact ordinary runtime directory/parent paths. Both
directories contained only zero-byte runtime socket objects. Preserve them as:

- `C:/Users/roicambe/AppData/Local/Docker/run.lanes-audit-backup-20261007-182011`
- `C:/Users/roicambe/AppData/Local/docker-secrets-engine.lanes-audit-backup-20261007-182011`

Recreate both runtime directories and launch once. Engine **29.8.0** responds;
original `lanes_postgis_db` and `lanes_valhalla` containers are running. No factory
reset, WSL unregister, volume reset or secret-content inspection was used.
This recurring environment failure matches [Docker's issue tracker](https://github.com/docker/desktop-feedback/issues/554);
permanent recurrence prevention remains unverified.

## Remaining acceptance and limitations

1. **Real current article:** Production has never created a news claim case or
   zone in the inspected database. Verify an actual supported current source
   through the independent audit, public map, vehicle routing and lifecycle.
   Historical replays must retain original dates and cannot substitute for this.
2. **Collection cadence:** Three-hour polling is longer than the two-hour
   observation-evidence lifetime. A current report may expire before the next
   run; finite RSS windows can also omit intervening headlines. Assess latency,
   feed coverage and cost before deciding on a shorter schedule. Do not weaken
   observation-time requirements or expiry to compensate.
3. **Coverage:** Qualified barangay placement remains 20/30 in the accepted
   catalog; San Miguel topology/identity acceptance is open. Unresolved geometry
   must stay reviewable rather than creating unsupported routing closures.
4. **Staff geometry exceptions:** Optional staff-supplied footprint/existing-zone
   geometry-editor handoff remains open in the current task plan. Passing text
   decision controls does not complete it.
5. **Physical PWA and study:** Browser viewports do not verify physical Android
   permissions/cache/offline behavior. Pasig duration training/model selection
   and broader real-article accuracy acceptance remain separate unfinished work.
6. **Live auditor availability:** The final free historical synthetic request
   timed out at 20 seconds. No production current-article audit was exercised;
   provider/server/network cause is not established by a client timeout. Current
   claims require independent confirmation and can enter Needs Review when the
   auditor fails. Preserve this gate; measure availability with representative
   evidence before claiming reliable unattended news activation. No paid fallback,
   persistent timeout change or repeated synthetic retries were used.

No source-code behavior, dependency or schema change was required for this audit.
Only fixture determinism and documentation were changed; no commit/push requested.
