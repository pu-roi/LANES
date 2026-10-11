# Phase 36: Metro Manila OSM and NOAH Coverage Audit

> **Checked:** September 30, 2026 by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This is a read-only local-data audit. It checks all Metro Manila city boundaries in the downloaded OSM extract, summarizes road-name coverage, and samples the three Metro Manila UP NOAH hazard archives. Reproduce it from `backend/` with:

```powershell
venv/Scripts/python.exe scripts/audit_phase36_metro_spatial_coverage.py `
  ../data/metro_manila_road_audit.osm.pbf `
  ../data/noah_metro_5yr_inspect.zip `
  ../data/noah_metro_25yr_inspect.zip `
  ../data/noah_metro_100yr_inspect.zip
```

## Verified source limits

- The OSM PBF replication header is dated `2026-09-27T00:56:56Z` and points to the Metro Manila minute-replication source. The local file is a snapshot; LANES does not refresh it automatically.
- All 17 expected NCR city/municipality level-6 administrative relations assembled from their member ways. Missing relation ways or invalid boundaries stop the audit.
- The extract has 166,396 highway ways; 66,144 (39.8%) have a `name`, `name:en`, or `alt_name`. Major-road coverage is stronger—motorway 696/702, trunk 991/991, primary 3,898/3,943, secondary 5,393/5,407, tertiary 6,350/6,544, and unclassified 2,573/3,184—but this is not a complete named-road inventory. An absent or unnamed road must stay unresolved rather than be guessed.
- The BetterGovPH [Project NOAH hazard dataset card](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps) describes nationwide coverage and 5-, 25-, and 100-year scenario layers. Its [flood metadata](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps/blob/main/Flood/metadata_flood.txt) defines `Var=1/2/3` as low/medium/high hazard classes that account for modeled depth and velocity. These are susceptibility classes, not a dated observation, current water depth, or calibrated probability.
- The checked archive metadata does not state the source maps' modeling or field-validation date, nor an update schedule. ZIP/DBF member timestamps (2021–2022) do not prove map vintage. Keep this unknown visible in provenance; do not label the maps “newer” based on file timestamps.

## Metro Manila coverage sample

The audit generated 267 deterministic interior points across the 17 assembled city polygons (the number per city varies with polygon shape). A point counted as a hit when it fell inside a source hazard polygon of any `Var` class.

| NOAH scenario | Cities with at least one sampled hit | Important limit |
|---|---:|---|
| 5-year | 16/17 | No sampled point in Pasay hit a polygon. This small sample does not prove the source has no Pasay coverage. |
| 25-year | 17/17 | Samples establish presence at those points only. |
| 100-year | 17/17 | Samples establish presence at those points only. |

These are point-coverage checks, not city-wide polygon completeness, area percentages, road coverage, flood frequencies, or proof that an uncovered road is safe. The map display may show the layer, while placement uses exact source-vector intersections when present. Missing hazard overlap cannot veto a credible current article claim.

## Article-to-location trace

The read-only [Pasig article prediction audit](../../backend/scripts/audit_phase36_pasig_article_prediction.py) fetched the full accessible [GMA July 9, 2025 report](https://www.gmanetwork.com/news/topstories/nation/951995/floods-reported-in-luzon-mindanao-amid-heavy-rains/story/) and ran the registered-source fetcher and rules-only extraction. It extracted Maysilo Circle as a Mandaluyong landmark with Barangay Plainview, and Caruncho Avenue as a separate Pasig claim. The Caruncho claim was compared with six bounded OSM sections inside the checked Pasig polygon. Because the article gives only the road name for Caruncho, all six remain candidates. Six place-matched DRRMO rows support those sections and 22 related rows remain unmatched/visible. All three NOAH scenarios were intersected with each candidate; their overlap fractions range from zero to full overlap. The ranker has a unique top candidate, but its reason is `unique_ranked_prediction_not_verified_flood_extent`; a score is a ranking signal, not proof of today's flood footprint.

The article was published 448 days before this audit, has no resolved observation time, and is outside the existing 12-hour activation window. It is therefore not eligible for an automatic current alert or routing zone. The audit wrote no Flood Report, alert, Flood Zone, or route change.

For a non-Pasig example, the existing [Santo Domingo span audit](phase-36-sto-domingo-road-span-audit.md) grounds a historical GMA report's explicit Atok-to-Calamba span to one approximately 86.2 m Quezon City OSM path and checks all three NOAH scenarios. Pasig DRRMO records do not apply outside Pasig. This remains an offline prediction check, not a production geometry provider.

## Decision limits

- Use Pasig DRRMO place history only within Pasig, as supporting location context. Its annual labels and row counts are not event timestamps, independently verified events, current conditions, or clearance times.
- Use NOAH 5/25/100 layers as spatial context across Metro Manila. Preserve the three scenarios and hazard classes; do not collapse them into a “newest” layer or claim their rank is a probability.
- Preserve the article's reported city, barangay, road, cross street, landmark, direction, depth, and observation time separately. A generic named landmark can now be extracted with its local city/barangay scope, but a landmark without a verified mapped geometry remains a candidate, not a routing segment.
- A road-name-only claim can yield a set of bounded candidates. Keep multiple candidates visible; never close the entire road from that ranking. A missing NOAH hit or incomplete OSM name match remains uncertainty.

The helper tests cover inner city-boundary holes, missing relation ways, interior-only sample points, and polygon point-in-ring checks. The real-data audit and the Phase 36 article/spatial acceptance suite passed; see the [task plan](../task_plan.md) and [progress tracker](../progress.md). No runtime or database integration was made.
