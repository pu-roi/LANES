# Automatic news flood plotting: developer-intent alignment audit

> **Last Updated:** October 06, 2026, 12:30 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Historical source audit and ten focused checks. Its local implementation gaps are addressed by [subsequent integration](phase-36-estimated-road-zone-integration-20261006.md); release/real-data acceptance remains open.

## Developer clarification

The October 6 request specifies article road + city/barangay/nearby clues → narrowed OSM road sections → NOAH-supported location estimation → estimated flood-zone geometry. Claims needing review show the existing transparent outer layer. Sufficiently supported claims automatically become Active Zones, show both existing layers and appear on the public map without routine staff approval. All presentation must reuse the existing system design, components and shared UI.

This review changes no application source. Prior uncommitted worker code is retained. The earlier statement that the remaining task was solely a UI phase was too broad: the implemented automatic worker accepts separately approved current footprint records and does not activate the article/OSM/NOAH predicted sections described here.

## Code comparison

| Requested behavior | Current implementation | Verdict |
|---|---|---|
| Extract more than C5 alone | `taglish_extraction_service.py` captures city, exact-parent barangay, local-area/landmark, crossing/span, observation/status/depth/access and uncertainty context. Nearby-clue coverage is rule/asset dependent. | Implemented with coverage limits |
| Narrow C5 to supported locality | `news_road_placement_service.py` uses city assets, C5 route-reference aliases, explicit crossings or junction sections and barangay clipping. Missing named barangay does not fall back to a whole-city guess. | Implemented with coverage limits |
| Combine OSM and NOAH | `news_discovery_service.py` attaches placement and preview to captured extraction. `news_placement_preview_service.py` intersects OSM lines with exact NOAH scenario vectors, preserves gaps and ranks using article specificity, matching Pasig context and susceptibility. | Implemented locally |
| Select likely reported section | `noah_road_prediction_service.py` can return one uniquely ranked bounded section; ties, arbitrary bounds, truncated sets and unsupported clues remain unresolved. The result explicitly remains a prediction. | Implemented as a candidate |
| Draw Needs Review using transparent layer | `useNewsPlacementLayer.ts` imports `PENDING_REPORT_ROAD_AURA_PAINT` from existing shared map styles and renders backend modeled fragments with reported severity. `LiveMapPage.tsx` mounts it for the selected news review, including mobile map/evidence switching. | Implemented for selected previews |
| Turn sufficient estimated placement into Active Zone automatically | `news_footprint_worker_service.py` calls activation only for exact separately approved catalog records. It does not consume `selected_candidate_id` or `preview_geometry` as activation evidence. `approve_news_footprint` accepts current incident records or authenticated staff review. | Missing for the clarified estimated-road workflow |
| Persist/expire active zones | Existing publication/event/zone/link transactions supply current audit/policy/revision gates, retries, accepted depth/severity/access, refresh/clearance/expiry and retained support. Catalog-backed worker connection passed the earlier local checkpoint. | Implemented for accepted footprints |
| Active news road zone uses both existing layers | `useFloodZonesLayer.ts` draws the solid core only from LineString/MultiLineString `report_geometry`; the aura uses the zone polygon. News activation saves polygon geometry without `source_geometry` or a primary road report. `report_geometry` therefore lacks the line required for the solid core. | Partially implemented; road handoff missing |
| Show active zone publicly without staff action | Public `MapCanvas.tsx` and staff map already read `/reports/active-zones` and share `useFloodZonesLayer`. Public polling is 15 seconds. Activation can create records available to this reader, but the clarified estimated path is absent and literal immediate refresh is unverified. | Partially implemented |
| News source/article/time/status in existing details | Backend has safe publication projections, `report_source=news` and a basic publisher contributor fallback. Main zone reporter can still display System. Frontend `publicNewsApi.ts` fixes geometry to text_only/null and affects_routing=false; staff requests/effects omit footprint controls and hardcode unchanged routing. | Partially implemented |

The actual bundled C5/Ugong test verifies centerline containment, source relation identity and 20 accepted Pasig community barangays. Ten Pasig barangays remain unsupported; this is not universal barangay/landmark coverage. Existing review previews show the selected claim's candidates, not every unreviewed claim simultaneously.

## Existing design to reuse

- `frontend/src/features/map/mapStyles.ts`: severity colors, transparent pending road aura, active polygon aura, solid active road core and existing zoom/pin behavior.
- `frontend/src/features/admin/review/useNewsPlacementLayer.ts`: current news preview rendering.
- `frontend/src/features/map/hooks/useFloodZonesLayer.ts`: shared public/staff active rendering.
- `frontend/src/features/map/components/FloodZonePopup.tsx`, `frontend/src/features/admin/components/FloodRecordSummary.tsx`, `ActiveZonesPanel.tsx`, `ZoneContributors.tsx`, `NewsReviewEvidence.tsx`: existing evidence/details/source presentation.
- `frontend/src/shared/ui/`: established forms/buttons, record detail panels/dialogs, timeline, metrics and layout primitives.

The solid road core is a road line, while the outer layer is the zone/avoidance area or the pending preview aura. The integration must supply their correct geometries; adding another polygon to the current news activation does not automatically produce both layers. Preserve disconnected parts and existing colors, panels, selection and mobile interactions.

## Placement and activation distinction

NOAH's official [Studio](https://noah.up.edu.ph/noah-studio) exposes 5-, 25- and 100-year hazard scenarios. LANES treats their intersections as modeled susceptibility, not measured counts of recent flooding or the current incident perimeter. Article evidence supplies the reported current condition; OSM supplies road geometry. A useful estimated-location path must retain that distinction.

The current approval contract is stricter than the clarified estimated-road target. Implement an explicit server-owned estimated corridor acceptance contract: sufficient current/audited place/time/depth/access, supported bounded road section, authoritative/qualified parent containment, ambiguity/bridge/carriageway checks, selection of relevant disconnected fragments, and extent/width semantics using the existing road-zone machinery where justified. Preserve inferred versus observed provenance; never relabel NOAH modeling as a field-verified current perimeter. Define this path before replacing any existing fail-closed gate. Reuse existing storage where possible; this audit authorizes no SQLAlchemy model or migration change.

## Next tasks

1. Define the estimated road-zone acceptance/extent contract and bind it to current article plus OSM/NOAH identity; the catalog-backed contract remains a separate existing path.
2. Connect qualifying estimated sections to atomic activation and persist the corresponding bounded source centerline plus operational area, preserving gaps, retry identity, metadata, support and observation-based lifecycle.
3. Complete safe source/article/observation/status readers and consume them in existing public/staff details and controls. Use the existing shared styles and components only.
4. Verify automatic Needs Review → Active behavior, both visual layers, public refresh delay, expiry/clearance and routing on desktop/mobile; surface request/offline errors through existing mechanisms. Matching runtime assets/deployment and broader coverage remain open.

## Verification and limits

**10 focused existing tests pass** across C5 city-versus-barangay extraction, C5 OSM aliases, actual bundled Ugong containment/provenance, disconnected NOAH fragments, reported-span facts/provenance and incomplete/missing-boundary rejection. No browser session, live article fetch, auditor call, shared/cloud DB write, migration, deployment or push was run. Only deterministic tests/temp fixtures and existing assets were used. Existing multipart deprecation warning remains.

The earlier [456-check worker verification](phase-36-automatic-footprint-worker.md) is historical evidence for the catalog-backed connection; it does not certify the estimated activation path requested here. Do not add these overlapping tests to that historical total.
