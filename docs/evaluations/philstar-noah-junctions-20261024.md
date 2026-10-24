# Philstar UP NOAH junction follow-up

> **Last Updated:** October 24, 2026, 09:20 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Superseded placement interpretation

The [reviewed street correction](philstar-street-correction-20261024.md) supersedes these circular Amoranto-centered shapes. The developer identified the street-role defect in screenshots; earlier persistence/color acceptance did not establish affected-street correctness. IDs 88/89 survive with corrected Palali/Tabayoc geometry and append-only before/after evidence. Keep the original execution checkpoint below as history, not the current geometry contract.

## Source and result

The developer authorized continuing the matched intersections with UP NOAH hazard data. Reused saved Philstar article **274/source 573**, accepted result **401** and its unchanged full-body hash. No RSS, NER, Gemini generation or new article/extraction record was needed. Cloud preview matched the restored rehearsal checksum `f0fc2a0c41fe43296b04d72d2da7ef8184abefe2ddb7159c0b4a6c9f6162b102` before the atomic apply.

| Intersection, Sienna, Quezon City | Disposition | Reported depth/access |
|---|---|---|
| NS Amoranto / Palali | New event/zone **88** | Waist deep, 37 inches; no vehicles |
| NS Amoranto / Tabayoc | New event/zone **89** | Tire deep, 26 inches; no vehicles |
| NS Amoranto / Ubay | No duplicate; estimate overlaps existing zone **83** | Existing overlapping observation retained |
| NS Amoranto / Don Jose | Held: overlaps zone **84** with differing reported depth/access | No silent overwrite or unsupported conflict resolution |

Both new observations retain **September 9, 2026, 4:30 PM Philippine time** and the same source evidence in News Intelligence. The historical presentation lifecycle remains unchanged: polygons are active for inspection; after the final polygon is manually deactivated, the same event enters unified Flood History. Historical presentation outputs remain excluded from ordinary routing and real-event statistics. No live polygon was deactivated.

## OSM identity and NOAH comparison

Each of the four previously tied matches has two adjoining mapped sections meeting at the same OSM node/endpoint, primary road and article-named crossing. City and barangay were checked; these are not two different cities or barangays. Both candidate sections at every checked junction have **100% class-3 line coverage** in the **5-, 25- and 100-year scenarios**. There is no unique more susceptible side. NOAH models susceptibility, not measured flood depth, current flooding or a measured inundation boundary. Palali's higher reported water level comes from the article; both newly plotted zones retain the existing high/orange severity palette because their source reports prohibit all vehicles.

`source-junction-noah-v1` is an explicit, source-bound estimate policy. Its **25 m radius** is an application review/display window adapting the existing 25 m margin; the article does not report that radius. Geometry intersects the window with checked NOAH vectors, retaining holes/dry gaps and only components with source-aligned road cores. Barangay identifies the source junction without cropping boundary roads; the full window must remain inside the checked city. Missing assets/scenarios, extra candidates, disconnected roads, ambiguous grade or mismatched source identities fail qualification. New cut vertices may move only within the existing ten-micrometre source precision to satisfy exact containment; original OSM vertices stay unchanged.

The authority permits only the two Palali/Tabayoc groups and output processing, binding source/result, complete preview, application/release and OSM/NOAH evidence. Existing overlap checks and source preservation guards remain active. Saved-output reuse distinguishes this placement policy from the original policy without changing old receipts or reactivating deactivated polygons.

## Execution and checks

- Fresh full backup: **1,051,127 bytes**, SHA-256 `dfc1353df4fe9cf348af3cf6cebb93ef183344d1f5ee37c3e8898ed8d6fb5bee`; restored into an isolated disposable PostGIS database before shared writes.
- Scoped regressions: **126 passed, 1 skipped, 2 deselected**. The database-dependent behavior excluded from that host invocation was exercised against the actual restored source/database in the pinned worker.
- Final restored rehearsal passed actual-source qualification, stale-preview rejection, rollback, concurrent apply/reuse, original-policy reuse, no reactivation and final-deactivation-to-history. All **11** original active zones stayed active there.
- Cloud preview **`lanes-news-verified-js7fq`** matched the rehearsal; apply **`lanes-news-verified-tl44m`** saved 88/89. Repeat **`lanes-news-verified-kjzbj`** returned `reused`, events 88/89, **zero writes**. Each stage reports **zero provider requests**.
- Pinned worker image digest: `sha256:4b1197750b79fbc883b3cbfb4a17e2b41179dc8da71695fe3302648e97f779c8`; release SHA-256 `aec0ef9f514ad6ad4343ecd2d41402629268e0b165d6e56f2d2f7d383bbbf0c9`. Worker retry/resource limits remain unchanged. Existing conditional private-receipt grants were extended only to the new receipt prefix; unrelated IAM bindings were verified unchanged.

Shared preservation passed: every original row across **41 tables** remains byte-fingerprint identical. Only **2 zones, 2 events, 6 locations, 4 timeline entries and 2 policy evaluations** were appended. All **11** prior active zones remain active; the API returns **13** active zones. No source/article/run/user/settings record was changed. The stopped **62-attempt ledger and its generation are identical**, with the conservative cumulative estimate still **US$1.0215894**. Automation remains paused and both expiry flags remain disabled. The serving API specification and traffic are unchanged.

Protected checks passed for News Intelligence (**16** total / **10** Philstar observations), the active queue and all 13 group-member endpoints, both zone details, and both accepted source-group details. Existing history inspections **76, 86 and 87** return 200; new active presentation events **88/89** remain outside history and their history inspection returns 404. Existing routing-eligible zones **86/87** remain eligible; new 88/89 stay excluded. Staff/public geometry equals the approved preview, source depth/access is intact, and `affects_routing` remains false.

Hosted **desktop 1440×1000** and **mobile 390×844** acceptance passed: all ten Philstar details retain 4:30 PM and source text; existing history remains accessible; all 13 active groups load; new zone details retain “No vehicles”; selected admin polygons and public polygons render with **`#f97316`** retained through real MapLibre features. DOM/map-layer snapshots are retained privately. The browser checks used the existing lightweight test basemap with the real hosted API, so they do not certify external basemap availability or pixel appearance against every production style. The known blocked-service-worker Workbox harness error was recorded separately; no other page error was accepted.

Source changes remain **uncommitted on `roi-branch`**; this follow-up does not merge main or deploy the separate refresh-label change. The pinned manual worker is published and its cloud apply is complete; no API deployment was needed.

## Documentation and security audit

The manual authority is limited to output processing for the exact Palali/Tabayoc group IDs and trusted source/result/application/asset identities. Wrong operation, placement policy or selected group is rejected. Existing authenticated readers and role dependencies are unchanged; no public write endpoint or schema is introduced. Private credentials, grants, receipts and backups stay outside tracked source. The existing application identity and preview checks cover the complete output before its atomic write; restored rollback and concurrent reuse checks passed.

| Core record | Audit/action |
|---|---|
| Task plan / progress | Completed gates, actual new IDs, open overlaps and local publication recorded |
| Feature reference | Existing news checkpoint updated; no new flagship feature section |
| System documentation | Existing worker/readers/lifecycle and source-bound estimate explained |
| Bug log | Adjoining-section limitation resolved for two groups; overlap/conflict limits retained |
| Tech stack | Audited: existing libraries and hazard data reused; no dependency/version change |
| Decisions | Audited: scoped extension of existing placement policy; no fundamental architecture pivot |
| Database design plan | Audited: existing models/metadata only; no schema or migration changes |

## Remaining limitations

Ubay overlap is not proof that the entire new review circle is already covered. Don Jose needs an explicit source/geometry conflict decision before changing zone 84. Damayan, Del Monte and Talipapa Alley still lack accepted canonical-road placement; nineteen verification targets remain unresolved. Source-card excerpts can still begin with article headers/social-link boilerplate, tracked separately. No additional Gemini budget was consumed and no new dependency, schema or public API is introduced.

Private receipts and provider/database captures remain under ignored `data/philstar-junction-20261024/`; they are not published in source control. [Plan](../plans/philstar-noah-junctions-20261024.md) · [Original pilot](philstar-saved-article-20261024.md).
