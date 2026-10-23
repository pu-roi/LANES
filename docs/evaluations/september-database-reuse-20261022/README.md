# September 9 and 24 — database reuse versus deletion

Checked October 22, 2026, 3:14 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe). [Structured evidence](summary.json).

**Recommendation:** retain the existing News Intelligence inputs and Flood History records for the selected active-zone workflow. Reusing an article for a new processing method and a separate selected active instance does not require deleting the article or its prior history. This is an inspection/recommendation, not a user-approved reset decision.

**Later approved correction:** article 47 now has publisher version/run 140. This report retains its original pre-correction read-only counts; see the [applied source correction and retention verification](../news-publisher-body-capture-20261022/README.md). No old record was deleted or reactivated.

## Target and read-only verification

Google Cloud reports `lanes-db` in project `lanes-project-508809` as RUNNABLE, PostgreSQL 15. The configured remote database `lanes` exactly matches E0's frozen database identity. Connection startup enforces `default_transaction_read_only=on`; inspection uses explicit `SET TRANSACTION READ ONLY`, repeatable read, bounded statement/lock timeouts, verifies read-only state and rolls back. No application server, worker, inference, collection, migration, UPDATE, DELETE, TRUNCATE or trigger change ran. Connection credentials and raw SQL receipts stay in ignored private storage.

Cloud Alembic revision remains `d7e4b9a21c60`; the native-mode and narrow archive-endpoint migrations are not applied there. All 120 saved extraction runs are completed `rules_only`; neither selected article has a native NER run. There are no `historical_import` timeline entries. Cloud release/processing/output qualification remains necessary before Part 2A/2B execution. These findings do not alter that release scope.

## Selected articles and history

| Source | Article | Immutable versions | Completed legacy runs | Linked historical event/zone IDs |
|---|---:|---|---:|---|
| September 9 GMA flood alert | 47 | 137 | 2 | 61, 62, 63 |
| September 24 Daily Tribune, Minor flooding hits some metro areas | 25 | 61, 66 | 8 | 23, 59, 60 |

Every linked zone is inactive and every linked event is ended. All six geometries are valid, SRID 4326. Version 66/137 fingerprints and complete saved snapshots match the frozen E0 captures unchanged.

| Event/zone | Retained source location | Source observation (PHT) |
|---:|---|---|
| 23 | Boni Avenue, Mandaluyong (older Tribune-linked history) | September 24, 2026, 4:34 PM |
| 59 | Quirino Avenue near Guazon Street, Manila | September 24, 2026, 4:34 PM |
| 60 | Gov. Pascual Avenue, Malabon | September 24, 2026, 4:34 PM |
| 61 | NS Amoranto / Banawe, Sienna, Quezon City | September 9, 2026, 8:55 AM |
| 62 | Don Jose / Sct Alcaraz, Sienna, Quezon City | September 9, 2026, 8:55 AM |
| 63 | NS Amoranto / Banawe, Santo Domingo, Quezon City | September 9, 2026, 8:55 AM |

Locations/dates above summarize saved legacy evidence; valid geometry is not new native/source/geometry acceptance. This review does not establish that similarly named locations are duplicate incidents. The selected active candidates still require actual qualified extraction and geometry checks. Stored verification/creation timestamps are in October for these records; the September observations cannot be safely selected for cleanup using row creation dates. End timestamps describe saved lifecycle actions, not independently observed physical flood clearance.

## Table and dependency scope

| Table | Selected linked rows | Purpose |
|---|---:|---|
| `news_articles` | 2 | Original article identities and captured source bodies |
| `news_article_versions` | 3 | Immutable exact extraction input snapshots |
| `news_extraction_runs` | 10 | Completed legacy processing records |
| `news_article_feed_entries` | 4 | Source/discovery links referencing the articles |
| `news_claim_cases` | 53 | Claim identities |
| `news_claim_sources` | 53 | Run/claim evidence bindings |
| `news_claim_evaluations` | 75 | Historical processing/evaluation evidence |
| `news_claim_decisions` | 87 | Append-only publication decisions |
| `news_claim_zone_links` | 6 | Decision-to-zone references |
| `flood_events` | 6 | Ended incidents/lifecycle |
| `flood_avoidance_zones` | 6 | Inactive retained geometry |
| `flood_event_locations` | 13 | Event locations |
| `flood_event_timeline_entries` | 25 | Lifecycle evidence |
| `flood_reports` linked to these events/zones | 0 | No directly linked citizen-report rows found |

The database contains 74 articles, 56 events/zones and 43 reports overall. The selected graph currently includes all stored news claim cases/sources/evaluations/decisions/zone links; a broad publication-table reset would therefore affect the whole stored publication graph, not just five principal polygons. Foreign keys were inspected across 19 related tables. References from versions/runs/sources/evaluations/decisions/zone links use deletion restrictions. Event locations/timeline and article feed entries have cascading dependencies. No outside-article support source was found in these selected cases.

Actual enabled database triggers reject changes/deletes to claim sources, decisions and zone links, reject changes/deletes to finalized evaluations, and reject truncation of the publication history tables. Article version update protection is also enabled. No protected DML was attempted to test this; trigger definitions and foreign-key catalogs were read. Cleanup would be an intentional evidence-reset operation requiring its own exact scope, dependency treatment and replacement input/match-map preparation. It is not an ordinary history-row deletion or a prerequisite for reusing the articles.

## Recommended execution

1. Retain article/version IDs and the six historical records as the baseline. Preserve the sealed E0 manifest and its reference hashes.
2. Complete Part 2A qualification/seeding for supported existing/training-article history, matching existing incidents rather than reseeding them.
3. In Part 2B, add the authenticated native NER processing evidence for the selected September articles, generate geometry using the existing source/OSM/NOAH checks, and save the separately identified active instance for a qualified selected candidate.
4. Verify both active maps, normal authenticated deactivation and retained history. Internal instance lineage and count/routing policy distinguish the active presentation lifecycle from an additional real flood occurrence; existing UI design and user-removed labels/dropdown stay unchanged.

Deleting the existing IDs would invalidate the current frozen original-history match map and force new preparation before execution. Keeping them does not block the new native processing identity. **Nothing was deleted, cleared, reactivated or otherwise changed in Cloud SQL.**
