# Philstar reviewed street correction and full rounded buffers

> **Last Updated:** October 24, 2026, 09:20 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Defects and reviewed interpretation

The previous extraction kept Amoranto as the primary road in five corner reports, and the junction estimate followed those Amoranto centerlines. Earlier checks established persistence and rendered color, not correctness of the affected-street interpretation. The developer explicitly reviewed the five entries as **Don Jose, Palali, Banawe, Tabayoc and Ubay**, with Amoranto as their junction reference. This interpretation is recorded for this article only; there is no universal rule that the street after “corner” must be flooded.

The old buffer construction also changed the visible shape: original zone 83 omitted approximately 3,329 m² of its uncut rounded buffer; 84 omitted approximately 980 m². Zones 88/89 used 25 m-radius discs rather than road-shaped buffers. This was stored geometry behavior, not merely a screenshot/rendering defect.

## Corrected construction and retained evidence

Opt-in **`philstar-reviewed-street-corner-v1`** binds accepted Philstar **274/source 573/result 401**, exact seven groups, reviewed street roles, old-zone fingerprints, configured margin, current application/assets and the complete preview. It follows up to **25 m per connected arm**, stopping at the next mapped junction/end. OSM names/aliases, locality, exact junction, connected road and ground-level grade are checked. UP NOAH's **5-, 25- and 100-year** class intersections retain supported cores and gaps; classes never replace the source's depth/access/time.

The outer aura uses the same **EPSG:32651 `ST_Buffer`**, configured staff-road margin, rounded joins/caps and eight quadrant segments as staff-created road polygons. It is never cropped to barangays, NOAH edges or the former circle. The outer aura is an application estimate, not measured inundation. Disconnected cores remain disconnected even where display margins overlap. Intersecting source cores or unrelated-zone conflicts fail qualification; halos around separate source junctions do not silently merge their facts.

Generated outer-buffer coordinates serialize at **12 decimal degrees**. A first strict cloud comparison correctly stopped before writes because three coordinates differed from local PostGIS at roughly 10⁻¹⁵ degrees. The conservative serialization makes generated display shapes deterministic at a scale far below the existing source precision, without modifying OSM/NOAH inputs. Final application still requires an exact complete-preview hash match.

Existing **83/84/85/88/89** retain IDs, event links, active states, depth/access, source and immutable old receipts. Only geometry, source core, placement name, target-line admin notes and modification time may change. New source-bound historical metadata and before/after correction receipts append to existing JSONB timeline storage. Original input, NER, Gemini and extraction rows stay immutable. Don Jose/Scout Alcaraz and G. Araneta/Kitanlad retain their original primary-road interpretations.

Saved readers project the reviewed street and source-specific excerpt without altering result 401. The existing placement endpoint returns the saved corrected core/aura for News Intelligence map handoffs. History uses the latest metadata per source/group, retaining distinct source evidence and avoiding duplicate counts. Correction evaluations have their own internal schema rather than pretending to implement the legacy historical-output presentation contract. No public route/response model or database schema was added.

## Checks before shared application

- Fresh **1,056,438-byte** full backup, SHA-256 `995e7215b22bc1fc335e7211bb583ab7970235f6bb5921b7cc602b7c254f745a`; restored disposable PostGIS rehearsals retain all private artifacts.
- **480 runtime tests and 94 mandatory PostGIS checks pass**, including short blocks, wrong streets/crossings/localities, grade ambiguity, absent scenarios, source dry gaps, full rounded halos and saved map handoffs. An initial host run loaded local provider configuration and produced two unrelated fixture failures; the clean CI-equivalent working environment passes the full suite.
- Final restored rehearsal qualifies all seven junctions; stale-preview rejection, rollback, concurrent apply/reuse, corrected source labels, single source count, final-deactivation-to-history and no reactivation all pass. Shared records were untouched by rehearsals.
- Zero-provider pinned worker and API **`lanes-api-philstar-streets-20261024-v3`** are published. Protected candidate checks and all original 41-table row fingerprints pass before shared application. Retention eligibility is **zero** for users, posts, reports and zones before deployment.

## Shared apply and preservation — complete

Final cloud preview **`lanes-news-verified-52cfm`** matched restored checksum **`0e15459de511cf757f023825e5e3c8f2db5703500553a8b5059c2632a17e3d2c`** exactly. Apply **`lanes-news-verified-hx666`** saved the full correction atomically. Repeat **`lanes-news-verified-xtp2j`** reused all seven events with **zero writes**. Every stage reports **zero provider requests**. Worker release SHA-256: `2ff967c1268d173ab26a680f74e0cf0375043fd49160882de4e1f4386be5c786`.

| Event/zone | Reviewed placement | Source depth/access |
|---|---|---|
| **90**, new | Don Jose at NS Amoranto | 37 inches / waist; no vehicles |
| **88**, retained | Palali at NS Amoranto | 37 inches / waist; no vehicles |
| **83**, retained | Banawe at NS Amoranto | 26 inches / tires; no vehicles |
| **89**, retained | Tabayoc at NS Amoranto | 26 inches / tires; no vehicles |
| **91**, new | Ubay at NS Amoranto | 26 inches / tires; no vehicles |
| **84**, retained | Don Jose at Scout Alcaraz | 19 inches / knee; light vehicles prohibited |
| **85**, retained | G. Araneta at Kitanlad | 8 inches; passable with caution |

Original-row fingerprints across **41 tables** show only the five allowlisted zone rows changed. Full-field comparison limits changes to geometry, source geometry, name, admin notes and modification time. Every unrelated row, original article/version/extraction/provider record and original timeline row remains unchanged. Appended: **2 zones, 2 events, 6 locations, 14 timeline entries and 7 policy evaluations**. No record was deleted. All **13** prior active zones remain active; total is **15**.

The stopped **62-attempt ledger and object generation are identical**, with conservative cumulative estimate **US$1.0215894**. Automation remains paused and both expiry flags stay disabled. Existing routing-eligible 86/87 and history 76/86/87 remain intact; the seven historical presentation events remain excluded from ordinary routing/statistics and wait outside history until final manual deactivation. Lifecycle changes were rehearsed only on disposable databases.

Protected news collection (16 total, ten Philstar), all group/member endpoints, all seven zone/source details, public geometry, existing history and saved Palali/Don Jose map handoffs pass. Staff/public geometry equals the approved preview and source access restrictions are unchanged.

## Production-basemap desktop/mobile acceptance — complete

Hosted **1440×1000 desktop** and **390×844 mobile** checks pass for all ten Philstar details/source timestamps, existing history, fifteen active groups, and every reviewed zone's restrictions and selected/public severity colors. Real MapTiler/OSM requests were used **without tile interception**: all 278 desktop / 166 mobile recorded basemap responses returned 200. Desktop briefly displayed the application's real OSM fallback/reconnection notice; mobile/public MapTiler vector labels also rendered. This does not certify every external-provider availability scenario.

Inspected actual screenshots for desktop Palali/Don Jose and mobile/public Palali. The core follows labeled Palali Street toward the reported corner, not Amoranto, and visible auras have full rounded ends. Private `ui-production/` retains PNG/DOM/MapLibre snapshots. The known service-worker-blocked Workbox harness exception was recorded separately; no other page error was accepted. This supplies the labeled-street visual evidence missing from the earlier lightweight-basemap/color-only checks.

Source remains **uncommitted on `roi-branch`**. API/worker publication and shared correction are complete; no Git push/main merge or unrelated frontend deployment was performed. Three accepted observations still lack canonical-road placement and nineteen verification targets remain unresolved. Existing refresh-label and concurrent News Automation edits remain separate.

## Documentation and security audit

Task/progress, existing feature checkpoint, system documentation and bug log are synchronized; plans/evaluations are indexed. Existing dependencies, models/migrations and fundamental architecture are unchanged. Admin authentication remains on the placement reader, with explicit 409/503 failures. Manual writes bind exact source/result/groups, reviewed roles, old-zone fingerprints, configured margin, application/assets and full preview; stale/concurrent changes fail closed. Credentials, backups and private grants remain outside tracked source.

Private backup, authorities, source/provider data and receipts remain under ignored `data/philstar-street-correction-20261024/`. [Plan](../plans/philstar-street-correction-20261024.md).
