import { useEffect, useRef } from "react";
import { LngLatBounds, type GeoJSONSource, type Map, type MapLayerMouseEvent } from "maplibre-gl";
import type { FeatureCollection, LineString, MultiLineString } from "geojson";
import type { PlacementEnvelope } from "./reviewApi";
import { PENDING_REPORT_ROAD_AURA_PAINT, SEVERITY_COLORS } from "@/features/map/mapStyles";

const SOURCE = "news-placement-suggestions";
const LAYER = "news-placement-centerlines";

export function useNewsPlacementLayer(map: Map | null, loaded: boolean, data: PlacementEnvelope | null,
  selectedId: string | null, enabled: boolean, visible: boolean,
  onSelect: (id: string | null) => void, onError: (message: string | null) => void) {
  const focused = useRef<string | null>(null);
  useEffect(() => {
    if (!map || !loaded || !enabled || !data) return;
    const geometry: FeatureCollection<LineString | MultiLineString> = {
      type: "FeatureCollection", features: data.preview.candidates.flatMap((candidate) => candidate.preview_geometry ? [{
        type: "Feature" as const, geometry: candidate.preview_geometry,
        properties: { candidate_id: candidate.candidate_id, is_selected: candidate.candidate_id === selectedId,
          color: data.preview.reported_severity ? SEVERITY_COLORS[data.preview.reported_severity] : "#94a3b8" },
      }] : []),
    };
    const draw = () => {
      if (!map.isStyleLoaded()) return;
      try {
        if (!map.getSource(SOURCE)) map.addSource(SOURCE, { type: "geojson", data: geometry });
        else (map.getSource(SOURCE) as GeoJSONSource).setData(geometry);
        if (!map.getLayer(LAYER)) map.addLayer({ id: LAYER, type: "line", source: SOURCE,
          layout: { "line-cap": "round", "line-join": "round" },
          paint: PENDING_REPORT_ROAD_AURA_PAINT });
        onError(null);
      } catch (error) {
        onError(`Placement suggestions could not be drawn. ${error instanceof Error ? error.message : "Reload the map to retry."}`);
      }
    };
    const select = (event: MapLayerMouseEvent) => {
      const id = event.features?.[0]?.properties?.candidate_id;
      if (typeof id === "string") onSelect(id);
    };
    const enter = () => { map.getCanvas().style.cursor = "pointer"; };
    const leave = () => { map.getCanvas().style.cursor = ""; };
    draw();
    map.on("style.load", draw);
    map.on("idle", draw);
    map.on("click", LAYER, select);
    map.on("mouseenter", LAYER, enter);
    map.on("mouseleave", LAYER, leave);
    return () => {
      map.off("style.load", draw); map.off("click", LAYER, select);
      map.off("idle", draw);
      map.off("mouseenter", LAYER, enter); map.off("mouseleave", LAYER, leave);
      if (map.getStyle()) {
        if (map.getLayer(LAYER)) map.removeLayer(LAYER);
        if (map.getSource(SOURCE)) map.removeSource(SOURCE);
        map.getCanvas().style.cursor = "";
      }
    };
  }, [map, loaded, enabled, data, selectedId, onSelect, onError]);

  useEffect(() => {
    if (!enabled || !data) { focused.current = null; return; }
    if (!map || !loaded || !visible) return;
    const token = `${data.run_id}:${data.claim_index}:${data.placement_revision}:${selectedId ?? "all"}`;
    if (focused.current === token) return;
    const sections = selectedId ? data.preview.candidates.filter((candidate) => candidate.candidate_id === selectedId) : data.preview.candidates;
    const bounds = new LngLatBounds();
    for (const candidate of sections) {
      if (!candidate.preview_geometry) continue;
      const lines = candidate.preview_geometry.type === "LineString" ? [candidate.preview_geometry.coordinates] : candidate.preview_geometry.coordinates;
      for (const line of lines) for (const position of line) bounds.extend([position[0], position[1]]);
    }
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 48, maxZoom: 17, duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 650 });
      focused.current = token;
    }
  }, [map, loaded, enabled, visible, data, selectedId]);
}
