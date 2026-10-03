import { useEffect, useRef } from "react";
import { LngLatBounds, type Map, type MapLayerMouseEvent } from "maplibre-gl";
import type { FeatureCollection, LineString, MultiLineString } from "geojson";
import type { PlacementEnvelope } from "./reviewApi";

const SOURCE = "news-placement-suggestions";
const LAYER = "news-placement-centerlines";

export function useNewsPlacementLayer(map: Map | null, loaded: boolean, data: PlacementEnvelope | null,
  selectedId: string | null, enabled: boolean, visible: boolean,
  onSelect: (id: string | null) => void, onError: (message: string | null) => void) {
  const focused = useRef<string | null>(null);
  useEffect(() => {
    if (!map || !loaded || !enabled || !data) return;
    const geometry: FeatureCollection<LineString | MultiLineString> = {
      type: "FeatureCollection", features: data.preview.candidates.map((candidate) => ({
        type: "Feature", geometry: candidate.centerline_geojson,
        properties: { candidate_id: candidate.candidate_id },
      })),
    };
    const draw = () => {
      if (!map.isStyleLoaded()) return;
      try {
        if (!map.getSource(SOURCE)) map.addSource(SOURCE, { type: "geojson", data: geometry });
        if (!map.getLayer(LAYER)) map.addLayer({ id: LAYER, type: "line", source: SOURCE,
          layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": ["case", ["==", ["get", "candidate_id"], selectedId ?? ""], "#1d4ed8", "#60a5fa"],
            "line-width": ["case", ["==", ["get", "candidate_id"], selectedId ?? ""], 7, 4],
            "line-dasharray": [2, 1.5], "line-opacity": 0.9 } });
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
    const token = `${data.run_id}:${data.claim_index}:${selectedId ?? "all"}`;
    if (focused.current === token) return;
    const sections = selectedId ? data.preview.candidates.filter((candidate) => candidate.candidate_id === selectedId) : data.preview.candidates;
    const bounds = new LngLatBounds();
    for (const candidate of sections) {
      const lines = candidate.centerline_geojson.type === "LineString" ? [candidate.centerline_geojson.coordinates] : candidate.centerline_geojson.coordinates;
      for (const line of lines) for (const position of line) bounds.extend([position[0], position[1]]);
    }
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 48, maxZoom: 17, duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 650 });
      focused.current = token;
    }
  }, [map, loaded, enabled, visible, data, selectedId]);
}
