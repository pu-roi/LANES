# Connected September news demonstration — October 13

> **Last Updated:** October 13, 2026, 9:50 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer explicitly approved extending the existing connected reconstruction command for both captured scenarios and writing their results into the shared Cloud SQL database. They disabled automatic expiry through System Settings. This is a historical presentation simulation, visible to live users through the shared database, not a report of current October flooding.

## Runtime and results

The existing frontend on 3000 and backend on 8000 use the same `lanes` Cloud SQL database as the deployed API and navlanes.live. No service, port, container or database instance was added. Schemas, dependencies, ordinary runtime publication rules and source facts are unchanged. Only the existing operator reconstruction command and its guard/input-retention tests were extended. The development-only connected admission scope resets when the command exits.

| Captured scenario | Article / extraction run | Completed evaluations | New estimated zones |
| --- | --- | --- | --- |
| September 24 Tribune event | 25 / 134 | 11 | 59 Quirino Avenue; 60 Gov. Pascual Avenue |
| September 9 morning GMA report | 47 / 137 | 31 | 61 NS Amoranto–Banawe, Sienna, 26 inches; 62 Don Jose–Scout Alcaraz, 19 inches; 63 NS Amoranto–Banawe, Santo Domingo, 19 inches |

Both evaluation stages record **zero LLM requests**, no failed/retry/lease-lost extraction or evaluation, and no publication exceptions. September 24 reuses an already captured cloud article; discovery checks its reconstructed feed and yields no new candidate, then the normal queue processes its current extraction. September 9 discovery retrieves the preserved body through the ordinary article fetcher and stores one new candidate. This run is two preserved reports, not exhaustive coverage of every September 9 update or historical feed.

Each run calls `discover_news`, `enqueue_article`, `process_saved_news`, `seed_claim_evaluations`, `evaluate_news_claims`, `publish_completed_evaluation`, and `process_news_footprints`. The command supplies only historical publisher HTTP inputs and clocks; it does not supply extraction outputs, audit decisions, coordinates or manually drawn zones. Normal source_rules and OSM/NOAH placement services decide the results.

## Verification

- Port 8000, port 3000 proxy, deployed API and navlanes.live public Active Zones all return HTTP 200 with IDs **58–63**. Existing citizen zone 58 remains active.
- Authenticated backend and frontend `/api/v1/admin/zones/all?active_only=true&limit=100` both return total **6** and the same IDs.
- Read-only Cloud SQL checks confirm all five new geometries valid, SRID 4326, and active. Stored historical expiry deadlines are intact; global automatic expiry is off.
- Article 25 retains original publication **September 25, 4:41 AM PHT**, despite the event being September 24. Article 47 retains **September 9, 9:19:06 AM PHT**. The article's supported September 9 observation remains **8:55 AM**; Tribune observations remain **September 24, 4:34 PM**. New zone creation timestamps correctly reflect the actual October 13 insertion time.
- Actual sign-in and Spatial Operations → Active Zones show six cards, original source links/times, 19-inch target measurement and estimated-corridor labels. Selecting zone 63 and opening the real map displays its generated corridor at NS Amoranto/Banawe.
- Seven focused tests pass: wrong-database rejection before sessions, production-environment refusal, LLM-provider refusal, enabled-expiry refusal, preservation of both scenario sets without repeat duplicates, another-database scenario refusal, and preserved original numeric/source input with uncaptured requests rejected. `git diff --check` passes.

Raw receipts, database/API verification and actual UI screenshots remain ignored under `data/news-connected-demo-20261013/`: `before.json`, `september24.json`, `september9.json`, `verification.json`, `alerts-api.json`, `scenario.local.json`, `active-zones.jpg`, `flood-zone-map.jpg`. No credentials or connection strings are written there.

## Input provenance and remaining limits

Archived RSS snapshots are unavailable. Feed entries are reconstructed from original titles, URLs and publication times, with separate feed-checkpoint query URLs to avoid changing ordinary live collector checkpoints. September 24 uses original captured HTML (SHA-256 `a8f2948343b438218236d1ae06245c9d7cb3d291c2b42bbe211496bca0b9fadb`). September 9 uses preserved publisher-index text for the 9:55 AM snapshot (SHA-256 `fed669c9d499a4afee792b380a062807c4a3c78aab01f5392e39761fcab7504d`) inside the same escaped HTML wrapper used by the existing timeline replay. Both capture hashes remain unchanged after processing.

The September 24 article was published the next morning. Its afternoon reconstruction explicitly admits that later-published evidence without rewriting dates. It cannot establish that the collector could have gathered this article during the preceding afternoon.

Seven September 9 supported alerts do not qualify for polygons: five have multiple equally supported road sections, one lacks verified operational depth, and one has no reported road. Remaining claims stay unpublished according to their evidence/context gates. September 24 retains source-observation supersession and context/clearance restrictions; only two eligible cases produce zones. These outcomes are retained, not overridden to match earlier fresh-database replay counts. These five polygons are estimates supported by article locations and modeled susceptibility, not measured water boundaries.

## Operator command

`python -m scripts.reconstruct_connected_news` is the existing backend-only operator command, extended with required `--scenario september24|september9`, required `--confirm-database`, and explicit `--authorize-connected-reconstruction`. Its preflight requires development mode, matching configured/bound database, configured source_rules, all three news stages enabled, the captured publisher enabled, expiry disabled by the operator, and a scenario file belonging to this same database. It merges both sets of result IDs into the existing backend-bound scenario file atomically. Never paste a database password into command arguments. This command was run with the same cloud settings as the existing 8000 backend; ordinary HTTP requests cannot enable its reconstruction scope.
