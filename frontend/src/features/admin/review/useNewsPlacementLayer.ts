import { useCallback, useEffect, useMemo, useRef } from "react";
import { LngLatBounds, type Map } from "maplibre-gl";
import type { PlacementEnvelope } from "./reviewApi";
import { useFloodZonesLayer } from "@/features/map/hooks/useFloodZonesLayer";
import { flyToFeature } from "@/features/map/mapGeoUtils";

/** News-specific data adapter only. Painting/popups/map clicks use the zone hook. */
export function useNewsPlacementLayer(map: Map | null, loaded: boolean, data: PlacementEnvelope | null,
  selectedId: string | null, enabled: boolean, visible: boolean,
  onSelect: (id: string | null) => void, onError: (message: string | null) => void,
  contextCoordinates?: number[][], isTouchDevice = false, activeAppearance = false) {
  const focused = useRef<string | null>(null);
  const revision = data ? `${data.run_id}:${data.claim_index}:${data.placement_revision}` : null;
  const inspectedId = activeAppearance ? null : selectedId;
  const records = useMemo(() => {
    if (!enabled || !visible || !data) return [];
    const claim = data.claim;
    const displayZone = data.preview.display_zone;
    // An older server may still combine all alternatives. Never present that
    // response as a resolved zone. Review draws only the explicitly inspected
    // candidate, whose geometry is already normalized by the backend.
    const resolvedDisplay = data.preview.status === "predicted_candidate"
      && displayZone?.candidate_ids.length === 1
      && displayZone.candidate_ids[0] === data.preview.selected_candidate_id;
    const sections = activeAppearance ? (resolvedDisplay && displayZone ? [{ display_id: "claim-display",
      candidate_ids: displayZone.candidate_ids, geometry: displayZone.core_geometry }] : [])
      : data.preview.candidates.flatMap(candidate =>
      candidate.candidate_id === inspectedId && candidate.preview_geometry ? [{ display_id: candidate.candidate_id,
        candidate_ids: [candidate.candidate_id], geometry: candidate.preview_geometry }] : []);
    return sections.map((section, index) => {
      const members = data.preview.candidates.filter(candidate => section.candidate_ids.includes(candidate.candidate_id));
      return { id: index + 1, candidate_ids: section.candidate_ids,
        geometry: activeAppearance ? displayZone?.aura_geometry ?? null : null, report_geometry: section.geometry,
        is_pending: true,
        severity: data.preview.reported_severity || "unknown", depth_formatted: claim.depth_formatted || claim.depth_raw,
        created_at: claim.event_time_resolved, report_text: claim.evidence_sentence,
        reporter_name: data.source?.publisher || "News report", reporter_role: "News report",
        placement_details: {
          location: [claim.canonical_road || claim.raw_place_name, claim.canonical_barangay, claim.canonical_city].filter(Boolean).join(", "),
          section: members.map(candidate => candidate.cross_streets.map(names => names.join(" / ")).join(" — ")).filter(Boolean).join("; "),
          depth: claim.depth_formatted || claim.depth_raw,
          passability: claim.road_passability?.replaceAll("_", " ") || "Not specified",
          observedAt: claim.event_time_resolved, sourceTitle: data.source?.title, sourceUrl: data.source?.canonical_url,
          publisher: data.source?.publisher, publishedAt: data.source?.published_at,
          ambiguousCarriageway: members.some(candidate => candidate.ambiguous_carriageway),
        },
      };
    });
  }, [data, enabled, visible, activeAppearance, inspectedId]);
  const displayError = enabled && visible && data && activeAppearance
    && data.preview.status === "predicted_candidate" && data.preview.display_zone
    && (data.preview.display_zone.candidate_ids.length !== 1
      || data.preview.display_zone.candidate_ids[0] !== data.preview.selected_candidate_id)
    ? "The automatic plot contains unresolved alternatives. Update the backend and reload the map." : null;
  const reportLayerError = useCallback((message: string | null) => onError(message || displayError), [onError, displayError]);
  const selectedRecord = records.find(record => selectedId && record.candidate_ids.includes(selectedId));
  const selectFromMap = useCallback((id: number | null) => {
    const record = records.find(item => item.id === id);
    const candidateId = record ? (selectedId && record.candidate_ids.includes(selectedId) ? selectedId : record.candidate_ids[0]) : null;
    // The shared map click already performs fly-to. Only panel selection below
    // needs an additional camera action.
    focused.current = candidateId ? `${revision}:${candidateId}` : `${revision}:all:${contextCoordinates?.length ?? 0}`;
    onSelect(candidateId);
  }, [records, selectedId, revision, onSelect, contextCoordinates]);
  const options = useMemo(() => ({ namespace: "news-placement", mode: activeAppearance ? "active" as const : "review" as const,
    onError: reportLayerError }), [reportLayerError, activeAppearance]);
  // Panel inspection chooses what is drawn; it is not a map-click selection.
  // Keeping these distinct permits mobile tap to open the shared details.
  useFloodZonesLayer(map, loaded, records, isTouchDevice, "zones", activeAppearance ? selectedRecord?.id : undefined,
    selectFromMap, undefined, undefined, undefined, options);

  useEffect(() => {
    if (!enabled || !data) { focused.current = null; return; }
    if (!map || !loaded || !visible) return;
    const token = selectedId ? `${revision}:${selectedId}` : `${revision}:all:${contextCoordinates?.length ?? 0}`;
    if (focused.current === token) return;
    if (selectedId) {
      const candidate = data.preview.candidates.find(item => item.candidate_id === selectedId);
      if (candidate?.preview_geometry) {
        flyToFeature(map, candidate.preview_geometry, null,
          { duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 1500 });
        focused.current = token;
      }
      return;
    }
    const bounds = new LngLatBounds();
    for (const position of contextCoordinates ?? []) bounds.extend([position[0], position[1]]);
    const geometries = activeAppearance ? records.map(record => record.report_geometry)
      : data.preview.candidates.flatMap(candidate => candidate.preview_geometry ? [candidate.preview_geometry] : []);
    for (const geometry of geometries) {
      const lines = geometry.type === "LineString" ? [geometry.coordinates] : geometry.coordinates;
      for (const line of lines) for (const position of line) bounds.extend([position[0], position[1]]);
    }
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 48, maxZoom: 17,
        duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 650 });
      focused.current = token;
    }
  }, [map, loaded, enabled, visible, data, revision, selectedId, contextCoordinates, activeAppearance, records]);
}
