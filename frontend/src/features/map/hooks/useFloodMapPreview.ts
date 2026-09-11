import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import type { RouteGeometry } from "@/features/routing/routingApi";

export function useFloodMapPreview(
  mapInstance: maplibregl.Map | null,
  floodStart: { coords: [number, number]; label: string } | null,
  floodEnd: { coords: [number, number]; label: string } | null,
  floodPreviewGeometry: RouteGeometry | null,
  floodOppositeGeometry: RouteGeometry | null,
  floodIsBidirectional: boolean,
  isEnabled: boolean = true
) {
  // Sync flyTo animations
  useEffect(() => {
    if (!mapInstance || !floodStart || !isEnabled) return;
    mapInstance.flyTo({
      center: floodStart.coords,
      zoom: Math.max(mapInstance.getZoom(), 14),
      bearing: mapInstance.getBearing(),
      pitch: mapInstance.getPitch(),
      duration: 600,
    });
  }, [floodStart, mapInstance, isEnabled]);

  useEffect(() => {
    if (!mapInstance || !floodEnd || !isEnabled) return;
    mapInstance.flyTo({
      center: floodEnd.coords,
      zoom: Math.max(mapInstance.getZoom(), 14),
      bearing: mapInstance.getBearing(),
      pitch: mapInstance.getPitch(),
      duration: 600,
    });
  }, [floodEnd, mapInstance, isEnabled]);

  // Markers
  const startMarkerRef = useRef<maplibregl.Marker | null>(null);
  const endMarkerRef = useRef<maplibregl.Marker | null>(null);

  useEffect(() => {
    startMarkerRef.current?.remove();
    startMarkerRef.current = null;
    if (mapInstance && isEnabled && floodStart) {
      const snappedStart = floodPreviewGeometry?.coordinates[0] ?? floodStart.coords;
      startMarkerRef.current = new maplibregl.Marker({ color: "#f97316" })
        .setLngLat(snappedStart)
        .addTo(mapInstance);
    }

    return () => {
      startMarkerRef.current?.remove();
      startMarkerRef.current = null;
    };
  }, [mapInstance, floodStart, floodPreviewGeometry, isEnabled]);

  useEffect(() => {
    endMarkerRef.current?.remove();
    endMarkerRef.current = null;
    if (mapInstance && isEnabled && floodEnd) {
      const snappedEnd = floodPreviewGeometry?.coordinates.at(-1) ?? floodEnd.coords;
      endMarkerRef.current = new maplibregl.Marker({ color: "#991b1b" })
        .setLngLat(snappedEnd)
        .addTo(mapInstance);
    }

    return () => {
      endMarkerRef.current?.remove();
      endMarkerRef.current = null;
    };
  }, [mapInstance, floodEnd, floodPreviewGeometry, isEnabled]);

  // Preview layer
  useEffect(() => {
    const ORIGINAL_SOURCE = "shared-flood-preview-original-source";
    const ORIGINAL_LAYER = "shared-flood-preview-original-layer";
    const OPPOSITE_SOURCE = "shared-flood-preview-opposite-source";
    const OPPOSITE_LAYER = "shared-flood-preview-opposite-layer";
    if (!mapInstance) return;

    const removePreview = () => {
      try {
        if (!mapInstance || typeof mapInstance.getLayer !== "function") return;
        if (typeof mapInstance.getStyle === "function" && !mapInstance.getStyle()) return;
        for (const layerId of [ORIGINAL_LAYER, OPPOSITE_LAYER]) {
          if (mapInstance.getLayer(layerId)) mapInstance.removeLayer(layerId);
        }
        for (const sourceId of [ORIGINAL_SOURCE, OPPOSITE_SOURCE]) {
          if (mapInstance.getSource(sourceId)) mapInstance.removeSource(sourceId);
        }
      } catch {
        // Silently ignore teardown races
      }
    };

    const renderPreview = () => {
      removePreview();
      if (!isEnabled || !floodPreviewGeometry || !mapInstance.getStyle()) return;

      try {
        mapInstance.addSource(ORIGINAL_SOURCE, {
          type: "geojson",
          data: {
            type: "Feature",
            properties: {},
            geometry: floodPreviewGeometry,
          },
        });

        mapInstance.addLayer({
          id: ORIGINAL_LAYER,
          type: "line",
          source: ORIGINAL_SOURCE,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": "#f97316",
            "line-width": 6,
            "line-dasharray": [2, 2],
            "line-opacity": 0.9,
          },
        });

        // Keep the graph-validated counterpart in its own source/layer. This
        // prevents a very short, close carriageway from being collapsed by a
        // shared FeatureCollection update during React/MapLibre style reloads.
        if (floodIsBidirectional && floodOppositeGeometry) {
          mapInstance.addSource(OPPOSITE_SOURCE, {
            type: "geojson",
            data: {
              type: "Feature",
              properties: {},
              geometry: floodOppositeGeometry,
            },
          });
          mapInstance.addLayer({
            id: OPPOSITE_LAYER,
            type: "line",
            source: OPPOSITE_SOURCE,
            layout: { "line-join": "round", "line-cap": "round" },
            paint: {
              "line-color": "#f97316",
              "line-width": 6,
              "line-dasharray": [2, 2],
              "line-opacity": 0.9,
            },
          });
        }

      } catch (err) {
        console.warn("Failed to add shared preview layer", err);
      }
    };

    renderPreview();
    mapInstance.on("style.load", renderPreview);

    return () => {
      mapInstance.off("style.load", renderPreview);
      removePreview();
    };
  }, [mapInstance, floodPreviewGeometry, floodOppositeGeometry, floodIsBidirectional, isEnabled]);
}
