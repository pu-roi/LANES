# Phase 36: LiPAD / UP NOAH Flood Placement Integration

> **Last Updated:** October 02, 2026, 2:33 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Gates 1–3 evidence checks passed. Priority 4 now connects checksum-identified NCR OSM placement to shared article processing; explicit spans and uncertainty are persisted without public/routing effects. The operational NOAH/DRRMO corroboration path, public alerts and verified affected geometry remain open. The commuter NOAH display overlay is separate modeled presentation, not runtime analytical flood proof. The source-map vintage is not published in the checked NOAH metadata; coverage/source limits remain documented. Priority 5 is [lifecycle/frontend planning only](news-publication-review-frontend-plan.md).

**Historical research context:** The local-PBF/caller-boundary descriptions below record September investigations. The separate bundled `NewsRoadPlacementProvider` now supplies checked city relations and source catalog to production extraction; this does not promote a centerline to verified flood extent. See [release verification](../evaluations/phase-36-reusable-road-match-check.md#production-release-verification).

The read-only [reusable road-match check](../evaluations/phase-36-reusable-road-match-check.md) now accepts explicit `between` and `from ... to` claim spans and returns a bounded OSM centerline candidate or an unresolved reason. It reproduces the GMA Santo Domingo path but cannot yet resolve the PNA Araneta/Maria Clara/Florentino phrase from the local OSM junctions. It requires caller-supplied checked administrative boundaries and a local PBF, so it is not an operational ingestion geometry provider.

The read-only [NOAH ranking check](../evaluations/phase-36-noah-road-ranking-check.md) now orders supplied OSM sections using exact vector overlap plus article-place and DRRMO-context signals. It predicts the explicit Santo Domingo location, while the Bernal/Mercedes 100 m audit windows remain unselected despite different modeled overlap.
The local C. Raymundo network split now supplies 25 between-cross-street sections, excluding arbitrary OSM way ends and same-street dual junctions. One retains alternative carriageway uncertainty. Many sections tie even after comparing total NOAH overlap and `Var` class; a road-name-only report still cannot select one location. Article barangay/landmark context and place-matched DRRMO rows are needed to narrow this set before any automatic zone rule.

The September 30 [Metro Manila coverage audit](../evaluations/phase-36-metro-spatial-coverage-audit.md) assembled all 17 OSM city relations, measured named-way coverage, and sampled all three NOAH archives across every city. It found a 2026-09-27 OSM snapshot, no automatic LANES refresh, and a NOAH archive with no published model-vintage date. The 5-year sample had no Pasay hit, while 25- and 100-year samples hit at least one polygon in all 17 cities. These are documented coverage limits, not evidence that uncovered locations are safe.

## Purpose

Get current, credible news flood claims onto the map quickly and automatically. Use the Pasig DRRMO history and permitted LiPAD / UP NOAH spatial layers to improve the *location* of a claim. A modeled hazard layer is context for where flooding is plausible; the recent article or field report is evidence that flooding is happening now.

## What exists today

- `data/flooded_areas_pasig_clean.csv` has 726 historical rows with year, barangay, street, landmark, and estimated depth range. The original workbook and raw CSV have annual headings, row numbers, and `Water Level (Estimated)`; they do **not** supply event dates, observation/onset/clearance times, coordinates, or distinct event IDs. A row count is not a confirmed flood-event frequency, and the year cannot set an active zone's lifetime.
- `PasigHistoricalService` currently calls its row count `recurrence_count` and adds a place-ranking bonus; this name does not establish independent recurrent events. `NationwideGeometryService` still constructs preview polygons from fixed offline coordinates or caller coordinates. It does not intersect LiPAD / UP NOAH layers.
- The RSS collector saves articles, but it does not yet process them into map alerts or flood zones. No public news alert or automatic zone should be claimed as delivered.

## Source lead from DavFlood and Verified UP NOAH Data Source

[DavFlood](https://github.com/kaizenics/davflood) is a Davao hazard-map implementation using 5-, 25-, and 100-year UP NOAH polygons. Its README confirms it sources data from the [BetterGov.PH Project NOAH dataset](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps), where per-province ESRI shapefiles are already in WGS84 (`EPSG:4326`) with a single `Var` attribute (1 = Low 0–0.5m, 2 = Medium >0.5–1.5m, 3 = High >1.5m, accounting for both depth and water velocity).

Inspection of the BetterGovPH repository files API confirms the availability of all three return-period archives for Metro Manila:
- **5-year flood scenario:** `Flood/5yr/MetroManila.zip` (33.38 MB)
- **25-year flood scenario:** `Flood/25yr/MetroManila.zip` (36.25 MB)
- **100-year flood scenario:** `Flood/100yr/Metro Manila.zip` (24.86 MB — *note space in filename*)
- **PMTiles alternative:** Prebuilt single-file vector tiles under `PMTiles/layers/` (`flood_5yr.pmtiles` 486 MB, `flood_25yr.pmtiles` 563 MB, `flood_100yr.pmtiles` 969 MB).
- **Metadata & Methodology (`metadata_flood.txt`):** FLO-2D FEMA-approved flood routing simulation by PAGASA and UP NIGS. Major river basins (including Marikina/Pasig River Basin) are modeled using 1-meter resolution LiDAR topography and synoptic rainfall interpolation.
- **License:** The original [Project NOAH Open Data License PDF](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps/resolve/main/NOAH_License.pdf) confirms Open Data Commons Open Database License (ODC-ODbL 1.0). Redistribution and adaptation require attribution to Project NOAH and its contributors; redistributed derived data must use the same license.

### File-level verification (September 28, 2026)

Downloaded only the three Metro Manila ZIPs into ignored local `data/noah_metro_*_inspect.zip` files. The repeatable read-only inspection script is `backend/scripts/inspect_noah_metro_archive.py`. All archives passed ZIP CRC checks and contain `.shp`, `.shx`, `.dbf`, and `.prj`. Each shapefile is polygon shape type 5 in WGS 84 and contains exactly three `Var` records (1, 2, 3). The whole-layer bounding boxes span approximately longitude 120.907–121.135 and latitude 14.352–14.785. These bounds alone cannot establish city coverage.

Using the repository's `frontend/public/pasig-boundary.geojson`, 624 regular sample points lay within Pasig. Actual polygon point-in-ring checks found the following numbers of those points within each hazard class:

| Scenario | `Var=1` | `Var=2` | `Var=3` |
| --- | ---: | ---: | ---: |
| 5-year | 124 | 144 | 49 |
| 25-year | 108 | 203 | 80 |
| 100-year | 75 | 211 | 171 |

This proves that each scenario has actual Pasig polygon coverage at sampled locations. Counts are **not** area percentages, road-overlap measures, or present-day flood frequencies. The archives are about 33.38 MB, 36.25 MB, and 24.86 MB; their SHA-256 hashes are `99BB769DB123C574D8190B4316150F72C818A6BB3DACDB1D0B609F28E960E7F9`, `B5354166CCE55F21EBAEAAD72CE8D86F6D3F7092FB0072D17A434096A7435264`, and `7F92B0E079FF611907ADC4B102B5EBDA45331A819109F9CBB97F56F42889B3E2` respectively. ZIP/DBF modification dates range from 2021 to 2022 but do not establish when the underlying maps were modeled or last field-validated. The original NOAH license PDF was read and confirms the dataset card's ODbL terms.

For a bounded road source, [openstreetmap.fr lists a Metro Manila `.osm.pbf` extract of about 58 MB](https://download.openstreetmap.fr/extracts/asia/philippines/). Its contents and road-name coverage still need inspection. The current `NationwideGeometryService.geocode_osm_feature` returns an offline anchor for C. Raymundo Avenue before querying OSM, so that path cannot verify its road geometry. Public Nominatim is unsuitable for systematic road extraction under its [usage policy](https://operations.osmfoundation.org/policies/nominatim/); use a regional extract or the existing Valhalla graph as the road source.

A single, read-only [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) query for roads named Raymundo in a Pasig-area bounding box returned 31 OSM ways: 26 named **C. Raymundo Avenue**, three Michael Raymundo Street, one G. Raymundo Street, and one N. Raymundo Street. Its response is retained in ignored `data/osm_raymundo_probe.json` for the local audit. Using 314 roughly 15-meter-spaced sample points on C. Raymundo ways inside the Pasig boundary, the inspection script found markedly different modeled hazard along the road. For example, OSM way `90642172` had no sampled overlap in the 5- and 25-year layers and 17 of 19 samples outside the 100-year layer, while way `18754956` had medium-class overlap at 26 of 27 samples in the 5-year layer, all 27 in the 25-year layer, and high-class overlap at all 27 in the 100-year layer. This was preliminary point sampling, not a prediction of a current flood.

### Bounded junction probe (September 28, 2026)

Downloaded the [Metro Manila OSM PBF extract](https://download.openstreetmap.fr/extracts/asia/philippines/) (60,552,006 bytes; SHA-256 `0FA54508AD7FE5E9DEBD6F46B6CD5CA01EEB57B26E2BA5D5B751A5539B6B2B1D`) into ignored `data/metro_manila_road_audit.osm.pbf`. The reproducible read-only `backend/scripts/audit_noah_road_intersections.py` uses Pyosmium and Shapely to find **26** named C. Raymundo ways and shared junction nodes, then intersects the original NOAH polygon rings with short C. Raymundo centerline windows. Invalid source rings are repaired for this local calculation, and ring holes are retained. Its 100 m radius around each junction is an **arbitrary inspection window**, not the extent of any reported flood. Lengths use a local meter approximation; geometric intersections use the source vectors, not 15 m point samples or display tiles.

| C. Raymundo junction window | Mapped junctions | Road line checked | 5-year NOAH overlap | 25-year NOAH overlap | 100-year NOAH overlap |
| --- | ---: | ---: | --- | --- | --- |
| Bernal Street | 1 shared node | 199.8 m | 199.8 m `Var=2` | 199.8 m `Var=2` | 199.8 m `Var=3` |
| Mercedes Avenue | 2 shared nodes/carriageway connections | 208.1 m | 121.9 m `Var=1` | 106.5 m `Var=1`; 97.5 m `Var=2` | 208.1 m `Var=2` |

The DRRMO CSV has three Bernal/C. Raymundo corner rows labeled Rosario (2024–2025) and four Mercedes/C. Raymundo place rows labeled San Miguel or Caniogan (2023–2024, including the misspelling `Mercedez`). These are historical records with year and place, not four or three proven independent flood events. The separate junctions and different modeled overlap demonstrate how article cross streets could narrow a road-wide claim. The calculation does **not** prove either corner is flooded now, identify the precise flooded length, settle the correct barangay on both sides of Mercedes, validate OSM bridge/elevation against field conditions, or justify a routing closure. OSM road-name completeness, full Metro Manila NOAH coverage, source-map vintage, and general article-to-segment matching are still unverified.

### GMA bounded article span (September 28, 2026)

The [read-only Santo Domingo audit](../evaluations/phase-36-sto-domingo-road-span-audit.md) takes the August GMA article's explicit `Sto. Domingo Avenue between Atok and Calamba Streets` evidence through the local OSM extract and exact NOAH source-vector intersection. OSM maps the road as `Santo Domingo Avenue` and has one shared node at each named crossing. The connected candidate path is OSM way `9793981`, approximately 86.2 m, with no mapped bridge/tunnel/layer tag. The complete OSM Quezon City administrative relation `106569` contains the path. Each of the three NOAH scenarios overlaps this candidate line at `Var=3`. This is one historical article and a manually bounded search area, not a production article-to-segment resolver, verified flood extent, or live routing zone. Pasig DRRMO records do not apply to this Quezon City report.

## Source and access check

1. **Metro Manila Only:** Do NOT download or import the full 34.1 GB national dataset. Do NOT bundle hazard shapefiles into the Cloud Run container. Only process the Metro Manila archives (`MetroManila.zip` / `Metro Manila.zip`).
2. **Schema & Storage Boundaries:** Do NOT alter SQLAlchemy models or Alembic migrations without prior developer approval (`AGENTS.md`). Before proposing a spatial table for NOAH polygons, evaluate PostGIS spatial indexing (`ST_Intersects`) against a pre-clipped vector spatial index. PMTiles are useful for display but should not be presumed exact enough for road-overlap decisions.
3. **Hazard Polygons are Modeled Susceptibility:** Return periods (5yr, 25yr, 100yr) indicate long-term susceptibility under extreme rain scenarios; they are NOT real-time flood observations and do not validate active inundation. They must never overwrite reported news depths or MMDA measurements.
4. **Pasig DRRMO Context:** Use Pasig DRRMO records as an additional spatial heuristic (road + barangay + landmark), not an independent event frequency or duration source. DRRMO lacks timestamps and distinct event IDs.

## Prediction from a named location

For a current article saying only **C. Raymundo Avenue**, first ground the road in Pasig and split its routable centerline at intersections and barangay boundaries. A news cross street or named landmark is strong segment evidence. Match historical DRRMO rows to the same road **and** their barangay/landmark; do not transfer a Rosario/Bernal row to a Caniogan/Mercedes section or confuse C. Raymundo Avenue with G. Raymundo Street. DRRMO rows with no landmark remain weaker road/barangay evidence.

Intersect each candidate section with verified 5-/25-/100-year NOAH flood polygons. Record overlap length, scenario and `Var` class as **modeled susceptibility**, not a present-day flood observation or measured depth. The archive's `Var` class includes velocity as well as depth, so it must not overwrite a news depth or the MMDA depth field. Check OSM bridge/tunnel/layer tags and the routable carriageway before interpreting a map-plane overlap; a road above a floodplain is not necessarily flooded. One continuous plausible section may produce a bounded *predicted* location; several separated overlaps remain several candidates. Ranking can use exact article span > article barangay/landmark > consistent DRRMO place rows > NOAH overlap, with contradiction and stale-report checks. These are explainable signals, not a fabricated 95% probability. Do not claim that the highest-scoring section is the exact reported coordinate.

For a fresh credible flood claim, publish a source-labeled map alert automatically at the best defensible precision. A uniquely bounded predicted section may become a clearly labeled, expiring zone and affect routing **only after** the evidence and geometry rules below are met; neither NOAH nor an old DRRMO record alone can activate a zone. If several separated sections remain plausible, show a road-level alert and candidate areas without closing the full road. Staff handles disputes and corrections rather than every routine alert. If a publisher reports recession, update or expire the active state; historical DRRMO years cannot supply that time.

## Server-side placement sequence

1. Normalize licensed hazard vectors to PostGIS SRID 4326 while preserving source CRS, return period, publication date, and hazard class. Validate geometry and coverage. A new table/migration needs developer approval under `AGENTS.md`; design the exact schema before requesting it.
2. Resolve each article's city, barangay, road, cross streets, landmarks, and explicit flooded span against a routable road network. Use Pasig DRRMO matches to disambiguate and rank repeatedly recorded corridors, without treating each row as a separate event. Use hazard intersection as an additional signal, never as sole proof of an active flood or an exact flooded segment.
3. Publish a recent, source-labeled **news flood alert** automatically when flooding is credible but the affected segment is unresolved. Show its observed/reported time and location precision. An approximate alert must not create a Valhalla avoidance zone.
4. Define a route-affecting tier that accepts an explicit article span or a uniquely bounded *predicted* road section backed by current flood evidence, consistent place/depth/status extraction, independently matched road geometry, and corroborating local spatial evidence. Record whether placement is reported or predicted. A source-labeled alert can appear sooner when that tier is not met. Recheck all evidence at the persistence boundary, deduplicate retries, and expire or update stale claims. Staff handles contradictions, ambiguous spans, and corrections; routine claims do not wait for staff. Set the actual thresholds after measuring false closures in a controlled development replay; do not label a heuristic score as probability.

## Acceptance evidence before release

- A source-metadata audit for map vintage and representative exact NOAH-to-road segment intersections. The checked source metadata does not publish a modeling/validation date; ODbL terms, Metro Manila sample coverage, and local exact intersections are recorded. Production geometry remains a later integration task.
- A trace from source sentence to named road, cross streets or landmark, bounded road segment, DRRMO match if any, hazard intersection if available, and output geometry. The real GMA Pasig trace and non-Pasig Santo Domingo span audit are linked in the [coverage evaluation](../evaluations/phase-36-metro-spatial-coverage-audit.md).
- A C. Raymundo example showing separate Rosario/Bernal and Caniogan/Mercedes candidates, how article context disambiguates them, and how multiple plausible sections remain unresolved. Junction nodes and related DRRMO rows are grounded for the two research windows; general article-to-segment selection remains open.
- Separate checks for alert latency, segment accuracy, false routing closures, stale/receded updates, duplicate articles, and missing spatial layers. Do not treat a numerical place-ranking score as a calibrated probability.
- Development map and routing verification before production connection. Keep the user-requested article simulations paused for now; ordinary automated checks remain part of implementing code changes.
