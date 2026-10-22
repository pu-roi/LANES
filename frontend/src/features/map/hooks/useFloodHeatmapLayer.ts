import { useEffect, useRef } from "react";
import type { GeoJSONSource, HeatmapLayerSpecification, Map } from "maplibre-gl";

/** The established public Analytics heatmap, shared by all map surfaces. */
export const FLOOD_HEATMAP_PAINT: HeatmapLayerSpecification["paint"] = {
  "heatmap-weight": ["get", "weight"],
  "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 1, 15, 3],
  "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"],
    0, "rgba(0, 0, 255, 0)", 0.2, "royalblue", 0.4, "cyan", 0.6, "lime", 0.8, "yellow", 1, "red"],
  "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 2, 15, 20],
  "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 15, 0],
};

export function useFloodHeatmapLayer(map: Map | null, loaded: boolean,
  data: GeoJSON.FeatureCollection | undefined, enabled: boolean,
  options: { sourceId?: string; layerId?: string; beforeId?: string; onError: (message: string | null) => void }) {
  const { sourceId = "heatmap-source", layerId = "heatmap-layer", beforeId, onError } = options;
  const errorCallback = useRef(onError);
  useEffect(() => { errorCallback.current = onError; }, [onError]);
  useEffect(() => {
    if (!map || !loaded) return;
    const remove = () => {
      if (!map.getStyle()) return;
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };
    const draw = () => {
      if (!map.getStyle()) return;
      try {
        if (!enabled || !data?.features.length) { remove(); errorCallback.current(null); return; }
        const source = map.getSource(sourceId) as GeoJSONSource | undefined;
        if (source) source.setData(data); else map.addSource(sourceId, { type: "geojson", data });
        if (!map.getLayer(layerId)) map.addLayer({ id: layerId, type: "heatmap", source: sourceId,
          maxzoom: 15, paint: FLOOD_HEATMAP_PAINT }, beforeId && map.getLayer(beforeId) ? beforeId : undefined);
        errorCallback.current(null);
      } catch { errorCallback.current("The flood heatmap could not be drawn. Reload the map to retry."); }
    };
    draw();
    map.on("style.load", draw);
    return () => {
      map.off("style.load", draw);
      try { remove(); } catch { errorCallback.current("The flood heatmap could not be cleared. Reload the map to retry."); }
    };
  }, [map, loaded, data, enabled, sourceId, layerId, beforeId]);
}
