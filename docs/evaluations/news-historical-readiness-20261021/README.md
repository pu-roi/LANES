# Historical news demonstration — readiness review

> **Last Updated:** October 21, 2026, 11:21 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Status: investigation and component verification complete; detailed implementation plan next.** Presentation target is Sunday, October 25, 2026. This report preserves the completed review in the current conversation; it is not a new end-to-end acceptance, production release or cloud-reset record. [Task handoff](../../task_plan.md#october-25-presentation--review-complete-detailed-implementation-plan-next) · [Progress](../../progress.md#historical-news-demonstration--readiness-review-complete).

## 1. Completed review and predecessor evidence

Read the referenced chats **Plan flood NER integration** (`01a15440-9910-78f2-bb7a-1dd833b1c4b1`) and **Review completed phases and frontend** (`01a15a5d-7d71-7e00-9d3d-db94fe677193`) through `read_thread`, then checked the current task plan, source code and saved reports. Chat outcomes are historical context; source/evaluation scope controls completion claims.

| Checkpoint | Recorded delivered scope | Remaining distinction |
|---|---|---|
| [V46](../flood-ner-backend-location-v46-20261020/README.md) | Backend preview; 1,281 recorded tests and one real-worker API comparison | Preview default remains disabled; not cloud production activation |
| [Phase A](../../plans/rss-ner-integration-contract.md) | Integration specification | Specification alone is not implementation |
| [Phase B, 3 GiB](../rss-ner-runtime-phase-b-3g-20261020/README.md) | Local one-CPU / 3-GiB qualification | Earlier 1-/2-GiB failures and actual cloud verification remain distinct |
| [Mode schema](../rss-ner-mode-schema-20261020/README.md) | Approved focused change and 66-check disposable-local verification | Shared/cloud migration was not applied by this review |
| [C1](../rss-ner-method-boundary-20261020/README.md), [C2](../rss-ner-native-projection-20261020/README.md), [C3a](../rss-ner-native-worker-20261020/README.md) | Method/history, projection/source checking, runtime/queue isolation | Local controlled boundaries remain explicit |
| [C3b](../rss-ner-rss-integration-20261021/README.md) | 754 recorded distinct tests; ten retained inputs; exact 4,483-span parity; four native cards | Mocked RSS; retained publication paused; zero public alerts/zones from that real-model run |
| [Phase D](../rss-ner-monitoring-20261021/README.md) | 608 recorded distinct checks; saved monitoring/error/retry contracts | Later auditor-configuration/maintenance regression remains open; visible corrections remain Phase E |
| [Chris integration](../chris-integration-20261021/README.md) | Verified frontend merge; 41 browser passes, three intentional desktop skips | Does not implement News Intelligence Phase E |
| [Spatial/history delivery](../spatial-history-scale-20261021/README.md) | Complete historical browsing and bounded/grouped spatial reads | Dense scale/mobile, cold/concurrent and visual acceptance remain qualified |

These predecessor suites were read, not rerun or added together as a new test total. No training, new dataset collection or validation/holdout use occurred. Eleven unresolved reviewed-article rows and the documented reference/type/language limits remain.

## 2. Existing geometry and lifecycle path

The retained v19 neural model recognizes location labels; v40/v44 repairs and v42 rules associate depth, time, flood condition and access. `news_ner_durable.enrichment` calls the existing road-placement and placement-preview providers. The local native pipeline calls existing publication and footprint workers; it does not implement a second geometry engine.

`NewsRoadPlacementProvider` resolves city/road/junction/locality evidence against the checked OSM catalog. Its bundled source is the September 27, 2026 OSM extract; it is not a live geocoder or a full-road flood boundary. `NewsPlacementPreviewService` measures exact road-line intersections with NOAH 5-/25-/100-year source vectors, preserves gaps and checks locality evidence. Pasig historical rows apply to matching Pasig evidence only. A unique susceptibility-ranked section is still an estimated location, not an observed wet perimeter.

`build_estimated_road_zone` requires a unique article-grounded bounded section, modeled fragments, checked assets/locality/elevation and complete evidence. It generates validated polygon components with corresponding centerlines and the existing 25-metre policy margin. `activate_estimated_road` rechecks source/evaluation evidence and uses the common atomic activation writer. That writer persists active zones, event locations and append-only source/decision/zone links. The existing history reader and `HistoricalEventsMap` can display saved event-linked inactive geometry.

NOAH susceptibility does not establish event occurrence, source observation time, measured depth or floodwater width. An ambiguous road, unsupported time, native-only collective group or unavailable geometry may remain inspectable without a generated zone. Prior September connected demonstrations used the older rules pipeline and therefore are not evidence that deployed neural processing generated their polygons.

## 3. Fresh component verification

The current conversation ran the existing `test_news_estimated_road.py` and `test_news_road_placement.py` suites under the project virtual environment with `--confcutdir=tests -q -p no:cacheprovider`. A process-only replacement for `sqlalchemy.engine.Engine.connect` raised on every attempted database connection. **54 checks passed, with three existing library warnings**. Tests exercise source-bounded placement, alias/junction ambiguity, automatic corridor generation, retained centerlines/gaps and unsafe/incomplete estimate rejection using constructed fixtures. No database connection was needed; this was not real-article inference or end-to-end historical persistence.

The read-only `scripts.verify_news_runtime_assets.verify_assets` function checked bundled OSM, barangay and NOAH catalogs and the Pasig history source. It returned **assets_ok**, with **1,524 qualified barangays** and **897 checked NOAH tiles** (299 per scenario). Identities returned:

| Asset | SHA-256 |
|---|---|
| OSM compressed road catalog | `b43240e75fb0eeeeb3e9a9d15724c162f24197c4bc0a05e834ae11776062b801` |
| Qualified barangay catalog | `f67812d70dd0816ce3f231315398f8650095543a6dc131ee459d65bdb073463f` |
| NOAH catalog manifest | `cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce` |
| Matching Pasig history CSV | `e3fd9c5a1fc966ea017de89f061eb8e80a199a026c93f58fcab5d96379623e13` |

This verifies current local bundled assets. It does not independently inspect files inside the serving cloud container. Output was observed in this conversation; no additional frozen private receipt package was produced or claimed. No new neural request, database migration/write or cloud job launch occurred.

## 4. Dated read-only cloud and data findings

Google Cloud CLI inspection confirmed project `lanes-project-508809`, region `asia-east1`, services `lanes-api`, `lanes-frontend`, `lanes-valhalla`, the `lanes-db` PostgreSQL 15 instance and existing migration/news/expiry jobs. The inspected API and discovery job use image tag `2ad49665b84ca97880781837d234d896c542848f`. API traffic is on revision `lanes-api-build-ef4389a5-500c-405a-a594-012b9cee59d2`; the frontend latest-ready revision is `lanes-frontend-build-2026-10-13-006` (latest-ready alone does not prove traffic selection). The worker uses one CPU / 1 GiB, a 600-second timeout and the legacy `scripts.run_news_discovery --discover --pipeline --scheduled --limit 50` entrypoint.

Database inspection used explicit `SET TRANSACTION READ ONLY`, a bounded statement timeout and rollback. It read the remote database `lanes`; that temporary transaction restriction did not alter normal application CRUD permissions. It found:

- Alembic head `d7e4b9a21c60`, preceding the locally approved native-mode change.
- 120 completed extraction runs, all `rules_only`; no stored `ner_rules_v1` run in the inspected aggregate.
- 74 articles, with publication/fetch activity through October 21. Recent rows are weather/commuter updates, not evidence of newly observed road flooding. Some event records have October report/verification dates; importing or creating a record in October does not establish an October news event.
- In a later read-only inspection, saved automatic expiry was **false**; all **56** zone rows were inactive. Zones **59–60** retain valid geometry and September 24 4:34 PM observations; **61–63** retain valid geometry and September 9 8:55 AM observations. All five have ended event records; lifecycle end timestamps do not establish observed physical clearance.
- Both `https://lanes-api-tymrlmxbkq-de.a.run.app/api/v1/reports/active-zones` and `https://navlanes.live/api/v1/reports/active-zones` returned HTTP 200 and `[]`. The endpoint results corroborate the current inactive database state, not a full browser acceptance of map rendering.

Source inspection confirms active reads require `is_active`; with automatic expiry off, the common deadline predicate no longer hides otherwise active rows. Manual deactivation/qualified clearance still apply. The public map requests the active-zone endpoint; history uses separate event/zone readers. Disabling expiry neither deletes history nor restores inactive rows. These observations are dated to this conversation on October 21 and may change under ordinary activity.

The requested internet search did not establish a confirmed October 1–21 Metro Manila rain-flood event from the retrieved reporting. Results included weather forecasts, flood-control projects, older-event accounts and a reported Antipolo pipe-break incident outside NCR. This limited search is not proof that no October flood occurred, that September 24 is the latest real event, or that collection is exhaustive. No new article was admitted or processed from the search.

## 5. Findings and requirements for the next planning step

The user selected the existing hosted system and already captured real inputs. Start the presentation batch at extraction, reuse existing geometry services, retain complete normal event/zone/evidence relationships, and persist historical results without current active-map/alert/routing effects or system-clock changes. During the original September event window, eligible records would have followed the ordinary active lifecycle; deactivated/expired results remain in the same stored event/zone structures for history.

The reviewed activation writer opens active events/zones and rechecks live freshness. A direct historical persistence path is not yet implemented. Native processing presently requires the disposable-test configuration/database identity, and the native-reader dependency defaults to legacy. Those guards are not a cloud deployment switch. Exact cloud asset/runtime/context delivery and the already approved migration's shared application need a separate concrete implementation/release step.

History date filters and daily metrics currently use `verified_at`; verification and creation use wall time. Duration metrics use verification-to-end intervals. The next design must avoid reporting an October import as a September occurrence or a simulated closure as observed flood duration. User permits an assumed closure where the source omits an end time, but no exact duration was selected. Label/source-bind that assumption separately, preserve unknown observations, and define honest chart/export behavior. This review does not approve silently rewriting source timestamps.

The user identifies current cloud data as testing data and explicitly does not require a backup before cleanup. Reset scope, dependency ordering, preservation of needed input captures and treatment of accounts/settings/unrelated records remain undecided. Existing uniqueness and append-only protections must be accounted for; deleting everything is neither performed nor the definition of data integrity. Historical reprocessing must also be repeat-safe.

The separately reviewed Phase D maintenance regression remains open: auditor construction/configuration failure occurs before independent publication/expiry maintenance. No new reproduction or repair was performed here. Phase E interface acceptance, Phase F 403 disposition, existing spatial-scale qualifications and actual cloud end-to-end/release evidence remain open.

## 6. Documentation-only handoff

Recorded completed review work at the top of task plan/progress, indexed this evaluation and added the historical-import/date finding to the issue log. Existing completed milestones and their historical acceptance/failure evidence are preserved. No new feature, dependency, schema or architectural replacement was delivered, so feature reference, tech stack, database design, system behavior documentation and architectural decisions are not rewritten to describe unimplemented functionality.

No application files, credentials, data records, expiry settings, system clock or cloud resources changed. No cleanup, seed, migration, deployment, commit or push is included. The next requested task is the detailed delivery plan.

## 7. September record reuse and redundancy recheck

After the detailed plan was documented, the user asked whether E0 would redundantly recreate existing historical records. Additional October 21 read-only SQL transactions (bounded statement timeout and rollback) confirmed:

| Existing input | Saved versions and processing | Principal saved history |
|---|---|---|
| Article 25, Daily Tribune, Minor flooding hits some metro areas | Versions 61/66; eight completed `rules_only` runs including principal zone-producing run 134 | Zones/events 59 and 60: valid geometry, inactive zones, ended events, September 24 4:34 PM observations |
| Article 47, GMA, FLOOD ALERT: Flooded roads in Metro Manila on Wednesday, September 9, 2026 | Version 137; two completed `rules_only` runs, 137/139; principal zone-producing run 137 | Zones/events 61, 62 and 63: valid geometry, inactive zones, ended events, September 9 8:55 AM observations |

Tribune also retains older Boni zone/event 23 linked to run 66. Its old publication decision is no longer the case's current decision; this is retained history, not proof of a duplicate identical road occurrence. The five principal geometry-linked decisions still have their original `active_zone` publication state, while their actual zone flags are false and event statuses are ended. Historical publication-state snapshots must not be mistaken for currently active geometry. All 120 inspected extraction runs remain completed `rules_only`; there is no stored cloud native run in that aggregate.

Exact input comparisons:

- Tribune saved body: 1,136 characters, SHA-256 `dc4773d602277a22fb0660705e21eb45f64125f4bd8167cd55ad21ec3350bc0f`, exactly matching the local saved text capture.
- GMA saved body: 1,970 characters, SHA-256 `a7b92b1ec22db882779dcc2d3f0d3dc153d834f325a00432a551d04357b57708`. Local indexed capture: 1,990 characters, SHA-256 `fed669c9d499a4afee792b380a062807c4a3c78aab01f5392e39761fcab7504d`. Splitting both on whitespace yields exactly equal word sequences, but bytes/offsets are not interchangeable.
- Existing input fingerprints: Tribune version 66 `0e1e1ba1f6b90200ac6188e544d62ec0f4c65a56024bee68676f9972cebec940`; GMA version 137 `b7dc414b045b1f203a385867169a74b8af5d18553f86a07b51d1a2921055c131`. E0 must bind its selected representation exactly and retain original provenance; this recheck does not itself freeze a native input manifest.

**Disposition:** E0 is verification/reuse, not fresh article gathering or reseeding existing history. A future `ner_rules_v1` run can legitimately add a new processing-method record against the existing captured source, but output persistence must first match existing incidents and avoid duplicate event/zone insertion. Confirmed matching history is reused with new lineage; evidence/geometry disagreement remains review-only; only a genuinely missing supported observation can create a new historical event. Dataset membership alone is not deduplication against legacy history. The task checklist and blueprint now state these requirements explicitly.

No article, event, zone, source timestamp or database permission was changed. No neural extraction ran. The current inactive/ended record inspection supports their availability to historical readers; it is not a new browser acceptance of every history screen.
