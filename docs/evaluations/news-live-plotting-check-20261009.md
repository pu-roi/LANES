# News-to-map runtime check

> **Last Updated:** October 09, 2026, 3:18 AM, Asia/Manila
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

Automatic discovery, extraction, independent evaluation, publication and estimated-road activation are connected and enabled. A real news flood has not exercised the deployed publication/plotting path: the cloud database contains zero claim cases, evaluations, decisions and news-zone links. Public news alerts are empty. The two public active zones are official/manual Zone #17 and citizen-report Zone #18, with empty news contributors.

## Read-only runtime evidence

### October 9, 3:18 AM: screenshot and connected-database reconciliation

The developer's screenshots use `localhost:3000`, whose relative API requests rewrite to the normal backend on port 8000. Public HTTP reads from both ports return zero news alerts and active zone IDs 17/18. The configured normal database host matches the primary address returned by `gcloud sql instances list` for `lanes-project-508809:asia-east1:lanes-db`, a RUNNABLE PostgreSQL 15 instance. Its database is `lanes`; the replay database is the separate loopback `lanes_news_test`, reached through ports 3001/8001. No replay record was saved to the cloud database, so the normal interface cannot display it. This is a test-environment mismatch, not evidence that refreshing the frontend would expose the replay.

Both inspections explicitly used read-only transactions and rollback. Cloud counts: 24 articles, 10 captured versions, 60 completed extraction runs, and zero claim cases/evaluations/decisions/zone links. The normal result reader returns zero locations; Collection status retains all 24 articles as excluded. Latest saved runs contain 41 raw mentions: 38 unknown, two historical subsided, and one forecast marked active. Their reader eligibility is zero; raw mention counts do not establish reported flood locations. Several articles have missing/blocked bodies; others concern flood-control projects, politics or flooding outside Metro Manila. None is the selected September 24 Tribune story.

Latest cloud collection #63 ran October 9 at 3:00 AM and records `feed_partial_failure`; Rappler retains its feed-size/XML-declaration error, while the other five checkpoints succeeded. This inspection did not repeat live feed fetching or change the scheduler, cloud settings, schemas, data or running frontend/backend processes.

The private database has six articles and 42 readable location rows, including earlier September 9 and superseded synthetic fixtures. Its original Tribune article/run 57 remains available for archived staff inspection, but its public Active Zones response is empty after archiving fixture zone 55. The corrected September 24 collector/pipeline replay produced zero new zones. **The requested successful actual-news-to-map demonstration remains incomplete**, including on the private interface. Private audit outputs are `data/news-replay/connected-cloud-database-check.json` and `connected-local-database-check.json`; these are ignored operational artifacts, not credentials or committed data.

### Earlier midnight checkpoint

- Cloud Run job `lanes-news-discovery-z2bc9` completed successfully October 9 at 12:01 AM. Its command includes `--discover --pipeline --scheduled --limit 50`, with 1 GiB memory.
- Cloud Scheduler remains enabled at `0 */3 * * *`, Asia/Manila, despite database collection settings of 30 minutes and a runtime tick expectation of 15 minutes. The latest trigger was midnight. A database interval cannot cause an external scheduler to invoke the worker more often. Three-hour invocation also exceeds the two-hour observation-evidence lifetime.
- Collector run #62 at midnight and #61 at October 8, 9 PM have `feed_partial_failure`. Run #60 at 6 PM completed. Latest collection parsed 84 entries from five publishers, saved zero eligible candidates and recorded zero body errors. Rappler (`feedspot-03`) failed with stored message: `Feed exceeds size limit or contains an XML declaration not allowed here`. The message does not distinguish which condition occurred; no feed-validation bypass or fresh network reproduction was attempted.
- The execution log records an initial `exit(1)` at 12:00:38 AM followed by `exit(0)` at 12:01:03 AM. The latest persisted runtime marks collection `not_due`, but its retained collection stage correctly records the earlier failure. These logs and runtime state are consistent with the retry skipping collection under the cadence gate; overall job success is insufficient evidence of healthy collection. Extraction, evaluation, publication and estimated activation counts are all zero.
- All three news switches are enabled with six selected verified sources. Existing database migration head is `d7e4b9a21c60`. Cloud database queries used `SET TRANSACTION READ ONLY` and rolled back.
- Deployed API revision `lanes-api-00058-hx4` receives 100% traffic; public health reports database connected. Both local and deployed public endpoints return zero alerts and two non-news zones.

## Verification and frontend connection

The focused discovery, processing, pipeline, estimated-road and publication-lifecycle suites pass **106 tests**. Local spatial bundle verification reports `assets_ok`, 897 NOAH tiles and 20 qualified placement barangays. Auditor configuration is valid for `openrouter/free`; no provider request was made, so current provider availability is unverified.

Source inspection confirms the public map consumes `/reports/active-zones`, preserves news source details in its shared layer/popup, and exposes News alerts. Staff `LiveMapPage` uses the same endpoint; `ActiveZonesPanel` renders linked article, observation and placement details. Initial local browser inspection reached the News alerts panel; browser work stopped when the user requested it. No browser tests or further browser interaction were performed afterward. This check does not establish new desktop/mobile visual acceptance.

Remaining acceptance: align the external scheduler with the intended collection interval, diagnose Rappler safely, then follow a genuine supported current article through independent evaluation and public/staff zone reads. Historical or synthetic reports must not be published as current floods to populate the map. No application code, cloud settings, database contents, dependencies or schema were changed.
