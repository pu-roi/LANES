# Philstar developer-reviewed Riverside pins

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). October 25, 2026, Asia/Manila. **Status: applied live; preservation, reuse and hosted desktop/mobile acceptance pass.**

## Authorized interpretation and source preservation

The developer explicitly requested plotting the two supplied coordinates after the investigation-only checkpoint. `philstar-reviewed-pins-v1` binds Philstar article **274**, source **573**, immutable result **401**, groups **resolved-n22** and **resolved-n31**, reviewed coordinates and OSM ways. Talipapa Alley remains skipped. The cancelled whole-street expansion remains cancelled.

| Source observation | Developer latitude, longitude | Checked mapped road / way | Retained source depth/access |
|---|---|---|---|
| West Riverside Interior, Damayan | 14.643080, 121.011474 | West Riverside Drive / 11435673 | 19 inches, knee; light vehicles prohibited |
| W Riverside / Atty Pat Senador, Del Monte | 14.645922, 121.013534 | Attorney Pat Senador Sr. Avenue / 11436044 | 8 inches, gutter; passable with caution |

Both retain **September 9, 4:30 PM Philippine time**. The checked community polygons place the pins in Del Monte and San Antonio respectively. These differences are explicitly stored as mapped versus reported locality; original source names and facts are not overwritten. The second pin is approximately 134 metres from the mapped Riverside junction, so `source_junction_confirmed=False` remains explicit. Neither supplied coordinate is represented as publisher evidence or independent field confirmation.

## Geometry and transaction

Checked catalog/name/city/ground-level ways ground the pins within 15 metres of their road; no nearest-road search is allowed to substitute an unrelated name. The containing OSM block is bounded at another named-road intersection/end. At most 25 metres each direction are retained, followed by exact NOAH scenario intersection and the existing full rounded staff-road `ST_Buffer` in EPSG:32651. The outer aura is not clipped to locality or model boundaries. This is estimated display extent, not measured flooded length/width.

The first supported core is approximately **29.51 m**, ending sooner at a mapped junction; the second is approximately **49.99 m**. All supported lengths fall in **class 3** in all **5-, 25- and 100-year** scenarios. Modeled susceptibility does not replace the article's 19/8-inch depths or access restrictions. Source hashes, road IDs, pin/road distance, original/mapped barangays, scenario/class overlap and gaps remain in append-only receipts.

The new output path appends two events/zones and linked historical metadata/receipts/evaluations atomically. Existing rows are never updated/deleted. Exact source/result, current application/assets, pins, buffer, baseline checksum and complete preview are checked before writes; an advisory lock and zone/event table locks serialize apply. Repetition returns saved identities without writing or reactivating a manual deactivation. Existing presentation exclusions from ordinary routing and real-event statistics, and final-deactivation-to-unified-history behavior, are retained.

The saved reader projects the reviewed road and exact source passage without changing extraction evidence. Its existing map handoff returns the saved new core/aura. The API overlay also contains the already locally tested field-verification metadata required by that reader; frontend badges remain a separate unpushed frontend change.

## Backup, checks and stopped attempts

- Fresh full backup **1,076,398 bytes**, SHA-256 **6de4a2fabef8635888227347a03649e2c00c956f4477e354fd1fb40d8ece2fc7**, restored to a disposable PostGIS database. An earlier 1,076,383-byte backup is also retained privately.
- **504 runtime and 105 mandatory PostGIS checks pass**, no failures/skips in the final required runs. All 62 normalizer-bound files remain unchanged; there is no NER rerun, Gemini request or extraction identity migration.
- Actual restored-data rehearsal passes both qualifications, stale-preview rejection, rollback, concurrent apply/reuse, source projection, saved map handoffs, source evidence/history after manual deactivation and no reactivation. All fifteen existing active zones remain intact. Local preview hash **4d8df5a6b58c43133869c26e619c160f6230d61f8b75883ce9bb4b9387776ca6** is unchanged across rehearsals.
- Initial construction tried to inspect the lazy OSM catalog before loading it; the service now explicitly authenticates its revision before reading ways. An exact timestamp comparison was corrected to compare the supported observation in UTC. Both stopped before writes and final tests/rehearsals pass.
- A first rehearsal assertion compared tuples to JSON lists; geometry equality now checks geometry rather than container types. This was confined to the private rehearsal harness.
- Initial strict baseline checks stopped on a live `visitor_daily_visits` update. That ordinary website counter is the only excluded baseline table; all flood/source/user/configuration records remain bound. A later **LOGIN_SUCCESS** audit entry was append-only, so a fresh backup/baseline was taken rather than weakening audit/source protection. Preservation verification covers all forty non-visit tables and separately reports expected visit telemetry.
- A cloud preview stopped before source processing because the complete row-hash baseline made its private authority exceed the existing 262,144-byte storage-reader limit. The authority now binds a checksum instead; the compact final authority is approximately 10 KB. No ledger reader limit was increased, no IAM grant was broadened and no provider operation was attempted.
- No retention-eligible users/posts/reports/zones exist at the release gate. Worker retries/resources/provider budget remain unchanged; automation is paused and expiry disabled. Final release SHA-256 **31e0e39d9e98c551a5006fab01d8a53011fcf84e0df0cc943e614fcdd1737986**.

## Shared and hosted acceptance

Checked API **`lanes-api-philstar-pins-20261025-v2`** passed protected news/group/placement/history reads and baseline preservation before promotion. Cloud preview **`lanes-news-verified-6rjng`** matched the restored preview hash exactly. Atomic apply **`lanes-news-verified-c8ltw`** created **zone/event 92 (West Riverside Interior)** and **93 (W Riverside/Attorney Pat Senador)**. Repetition **`lanes-news-verified-5nr9p`** reused those identities with **zero writes** and no reactivation. Each stage reports **zero provider requests**; the stopped budget ledger and generation are unchanged.

All original rows across **forty non-visit tables** are preserved, including users, source/version/extraction/provider records and existing flood/event/timeline rows. The original fifteen active zones remain active. Appended: **2 zones, 2 events, 6 locations, 4 timeline entries and 2 evaluations**. Ordinary website-visit telemetry is explicitly excluded from the strict baseline, rather than falsely claiming visitors never updated it. No record was deleted. Automation is paused and expiry disabled. Existing history remains 76/86/87 and routing remains limited to 86/87; the two new historical presentation events follow the rehearsed final-deactivation lifecycle.

Protected reads confirm **16 total News Intelligence observations, ten Philstar observations**, **17 active zones**, both new source/group and placement handoffs, unchanged source barangays/depth/access/time, exact public geometry and saved estimate status. Philstar now has **nine of ten accepted observations plotted**; Talipapa remains skipped/unplotted. The seventeen source-list entries absent from accepted results are not processed by this task, leaving eighteen of the full twenty-seven list entries without their own polygon.

Hosted **1440×1000 desktop** and **390×844 mobile** checks pass for all ten Philstar observation details and representative original-source panes, existing history, the 17-zone overview, and selected/public colors for **92/93**. Actual selected-zone screenshots were inspected against labeled production streets: West Riverside Drive and Attorney Pat Senador Sr. Avenue align with the reviewed pins, preserve yellow/green source-severity colors on selection, and show full rounded buffers. Public-map rendered features also retain the expected IDs/colors. All **75 recorded basemap responses per viewport** returned HTTP 200, with no tile interception. Public screenshots capture the flood overlay before every basemap tile has painted; labeled street inspection is supplied by the fully rendered admin captures, not inferred from a blank public background. This is not a general provider-availability certification.

An initial screenshot-preparation wait stalled on fonts after the desktop source checks; that run was stopped and retained. The successful run uses direct browser screenshots for the map, without image manipulation. The already known service-worker-blocked Workbox `reading 'waiting'` harness error is recorded once per viewport; all other page errors fail acceptance. Private `ui-checked/` holds the successful PNG/HTML/MapLibre snapshots, progress and summary. No application changes were needed for either browser-harness condition.

No schema, dependency or API-route change. Admin auth and existing protected placement GETs remain intact; no unauthenticated write route is introduced. Original/third-party local changes are preserved. Source is uncommitted on `roi-branch`; Git push/main merge and frontend deployment are not included. [Plan](../plans/philstar-reviewed-pins-20261025.md). Private evidence remains under ignored `data/philstar-reviewed-pins-20261025/`.
