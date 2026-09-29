# Phase 36: Santo Domingo Article-to-Road-Span Audit

> **Checked:** September 29, 2026, 4:38 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This is a read-only candidate-placement check for the [August 29 GMA flood report](https://www.gmanetwork.com/news/topstories/metro/1000340/heavy-rains-from-habagat-cause-floods-in-metro-manila/story/). The article explicitly describes Sto. Domingo Avenue **between Atok and Calamba Streets** in Quezon City. The source reports waist-deep floodwater as of 1:12 p.m. The check uses the local Metro Manila OSM PBF and the original Metro Manila NOAH flood polygon ZIPs. It does not create a map alert, avoidance zone, or database row.

The reusable `backend/scripts/audit_article_road_span.py` accepts the article road and bounded span, a manually selected audit bounding box, and the local source files. It normalizes `Sto.` to `Santo`, accepts only a supported between-two-cross-streets phrase, requires exactly one shared OSM node for each crossing, and follows connected ways with the main road's name. Missing or multiple junctions and disconnected roads fail rather than falling back to a whole-road geometry. It also retrieves the specifically identified OSM administrative relation for the reported city, checks that its boundary members form a complete polygon, and requires that polygon to contain the selected path. NOAH intersection uses source polygons, not a visual tile or point-sampling grid.

| Evidence | Read-only result |
| --- | --- |
| OSM road name | `Santo Domingo Avenue` (article: `Sto. Domingo Avenue`) |
| Atok Street junction | OSM node `60449727` |
| Calamba Street junction | OSM node `43082816` |
| Bounded centerline path | Nodes `60449727 → 12382081588 → 43082816`, OSM way `9793981`, approximately **86.2 m** |
| Reported-city boundary | OSM Quezon City administrative relation `106569` assembled from 140 outer ways; it contains the entire candidate path |
| OSM grade tags on selected way | No bridge, tunnel, or layer flag mapped |
| NOAH 5-, 25-, and 100-year source vectors | Each overlaps the entire candidate centerline at `Var=3` in this local calculation; `Var=1` and `Var=2` overlap 0 m |
| Pasig DRRMO history | Not applicable: the report concerns Quezon City, while the historical CSV covers Pasig |

The OSM nodes, city relation, and NOAH classes narrow a candidate location. They do **not** prove that water covered this path on August 29, establish the road's elevation, verify its carriageway or routing direction, or make the OSM boundary an official city survey. The manually selected search box remains an audit input, although the path itself was checked against OSM's Quezon City polygon. `Var=3` is modeled susceptibility that combines depth and velocity; it is not the article's measured depth. The source article is historical as of this check. No current routing decision is justified. Other article span phrasings, cross-street aliases, barangay boundaries, and multiple carriageway paths still need evaluation before this becomes an automatic geometry provider.

From `backend/`, reproduce the local check with the ignored files documented in the [spatial plan](../plans/lipad-noah-flood-placement.md):

```powershell
venv\Scripts\python.exe scripts/audit_article_road_span.py ..\data\metro_manila_road_audit.osm.pbf ..\data\noah_metro_5yr_inspect.zip ..\data\noah_metro_25yr_inspect.zip ..\data\noah_metro_100yr_inspect.zip --source-url https://www.gmanetwork.com/news/topstories/metro/1000340/heavy-rains-from-habagat-cause-floods-in-metro-manila/story/ --city-name "Quezon City" --city-relation-id 106569 --road "Sto. Domingo Avenue" --span "between Atok and Calamba Streets" --bbox 120.98 14.61 121.04 14.67
```

Six offline tests check the bounded phrase, road alias, junction ambiguity, disconnected-road failure, equal-length carriageway ambiguity, and complete city-relation containment. The local road and hazard source files are ignored and are not bundled into the runtime container; the city relation is requested only by this read-only audit command.
