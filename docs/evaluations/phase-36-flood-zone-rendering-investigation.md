# Phase 36: Flood Zone rendering and placement integration investigation

> **Last Updated:** October 03, 2026, 11:16 PM
> **Author:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Scope:** Source-code investigation of the current checkout; implementation ordering recommendation. No browser, database, publisher retrieval, runtime test, application change or deployment performed.

## Shared rendering paths

| Surface | Current implementation | Display role |
| --- | --- | --- |
| Public Map | `MapCanvas.tsx` calls `useFloodZonesLayer` | Active zones from `/reports/active-zones`; polls every 15 seconds and has an offline-cache fallback. |
| Spatial Operations | `LiveMapPage.tsx` calls the same `useFloodZonesLayer` | Same active-zone endpoint and polling interval; adds selection, contributor inspection and tab visibility. |
| Flood Report Panel | Writes geometry-selection state to `MapContext`; `MapCanvas.tsx` calls `useFloodMapPreview` | Unsubmitted road preview: orange dashed line, optional start/end markers and opposite carriageway. |
| Admin Create/Edit Zone | `AdminFloodMapInteraction.tsx` calls `useFloodMapPreview` | Reuses the road preview; editing hides the original active-zone rendering for that zone. |
| Pending reports | `usePendingReportsLayer` | Shared severity tokens, translucent road/point auras and overview pins; distinct from active zones. |
| Merge workspace | `useMergePreviewLayer` | Distinct candidate colors and proposed-geometry preview. |
| NOAH display | `useNoahHazardLayer` | Georeferenced scenario PNG overlay on the public map when 3D hazard mode is available; separate from active-zone geometry. |

Sources are under `frontend/src/features/map/`, `frontend/src/features/admin/` and `frontend/src/features/hazards/`. Both active map surfaces reuse `mapStyles.ts` and `FloodZonePopup`; desktop uses hover popups and the active-zone hook uses a details modal for touch devices. This confirms source-level shared rendering, not visual acceptance on actual devices.

## The two active-zone layers

- Inner road core: linear `report_geometry`, displayed in the severity color at opacity 0.95, with round caps/joins and zoom-dependent pixel width.
- Outer area: the persisted zone `geometry`, displayed in the same severity color at opacity 0.25, increasing to 0.45 on selection.
- The actual paint expressions switch from overview pins to detailed geometry at zoom 14. Some source comments describe the boundary differently.
- Severity colors are low lime, medium yellow, high orange and extreme red.
- `FloodAvoidanceZone.report_geometry` prefers persisted `source_geometry`, then the primary report's geometry. Preserving the road centerline is therefore necessary to retain the inner road core.
- Polygon-only or point-origin zones do not automatically get a second solid inner polygon: the hook creates a solid core only for LineString/MultiLineString geometry. Contributor inspection also replaces the generic zone with that contributor's original geometry.

The outer polygon is operational geometry, not merely a screen glow. `flood_routing_policy.get_active_flood_zones` reads the same stored zone geometry and applies vehicle-specific policy. Its transparency does not mean it is excluded from routing.

## Backend polygon construction and compatibility checks

Current creation paths use different policies:

- Ordinary report approval in `backend/app/api/v1/endpoints/admin.py` defaults to a degree buffer of 0.00015 for a road line and 0.0005 for a point. Dual-line approval can use a convex hull around both buffered carriageways.
- Official line creation and editing use approximately 25 metres converted to degrees. Merge confirmation has its own default buffer handling.
- Hand-drawn polygons use the submitted footprint.

Consequently, `mapStyles.ts`'s comment calling the aura a 50 m PostGIS buffer does not describe all runtime creation paths. An automatic news corridor must specify its own supported bounds/units and preserve the centerline, rather than infer affected width from that comment. Screen line width also does not measure real flooded width.

Before publication integration, check geometry compatibility across the entire chain: create schemas accept Polygon/MultiPolygon, while the zone response declares Polygon and the routing reader currently skips non-Polygon geometry. This investigation did not reproduce or repair a MultiPolygon runtime failure.

## What is connected in article processing

`process_saved_news` calls captured extraction, which runs `HybridExtractionService` in `rules_only` mode and attaches `NewsRoadPlacementProvider.resolve` results. Saved claims retain source-identified OSM centerline candidates. This path does not call the independent auditor or publish public alerts/events/zones.

The OSM provider can match explicit spans and retain ambiguous road sections. It currently lacks authoritative barangay boundaries and returns `missing_valid_barangay_boundary` for claims needing them. NOAH ranking cannot silently bypass that place-check gap.

`rank_noah_road_sections` already compares exact vector overlaps in the 5-, 25- and 100-year NOAH scenarios and prioritizes article place specificity and matching DRRMO context. Current callers are audit scripts/tests, rather than the saved processing path. The actual overlap reader is also in an audit script.

`PasigHistoricalService` is available in existing location ranking, but its aggregated street/landmark bonus is not the complete section-specific historical evidence contract required for operational placement. The clean CSV is bundled for backend runtime; a production analytical NOAH source-vector provider still needs an explicit storage/index/access design. The frontend PNG overlay cannot substitute for exact analytical intersections.

`NewsAutoIngestionService` is a separate gated activation prototype. It is not invoked by the durable processor and does not establish acceptance of persistent alert identity, repeated activation, correction or expiry. Retain all existing evidence and independent-auditor gates when connecting it.

## Recommended first implementation slice

Start with backend placement evidence and a preview contract, then display that result in the existing Spatial Operations map. Reuse the active-zone two-layer styles when a zone is eligible; label placement candidates distinctly while they remain proposals.

1. Promote exact NOAH intersection support from audit code into a bounded server-owned provider, with source identity/checksums, scenario/class overlap and explicit unavailable-coverage results. Assess indexed vectors versus PostGIS before choosing storage; SQLAlchemy/Alembic changes require separate developer approval.
2. Attach NOAH context to OSM sections in shared saved/RSS processing. Resolve required city/barangay/landmark evidence; preserve alternatives, truncation and missing coverage rather than invent a segment.
3. For confirmed Pasig sections, attach only DRRMO rows matching that road and supported barangay/landmark. Outside Pasig, omit that dataset. Historical record counts are not proven event frequencies, and historical depths do not replace current article measurements.
4. Return a typed preview containing selected/reported/predicted placement, alternative centerlines, source provenance, article depth/time/status/passability and eligibility reasons. Keep the proposed operational polygon/buffer policy explicit and separate from modeled hazard footprint.
5. Verify one bounded non-Pasig article and one Pasig claim with matched historical context, plus ambiguous/missing-data cases, before adapting map presentation. Historical examples remain isolated previews and cannot establish live activation.
6. Connect durable automatic-alert/zone publication with independent audit, current-evidence checks, stable incident/claim identity, retry deduplication, correction/clearance and expiry. Assess existing storage before proposing exact schema changes.

UP NOAH modeled susceptibility helps locate plausible affected sections. The developer's five-year Pasig DRRMO history is a separate historical dataset from NOAH's 5-year return-period scenario. Neither supplies current flood confirmation, exact current depth or observed inundation width. Source-backed current article facts remain authoritative for those claim fields.

## Verification limits

Verified by reading callers, renderer paint, response/model geometry behavior, administrative buffer branches, saved extraction wiring, NOAH-ranking callers and routing consumption. No functional tests were run because this slice changes documentation only. Existing local extraction fixes remain untouched; no schema, dependency, live zone, push or release change.
