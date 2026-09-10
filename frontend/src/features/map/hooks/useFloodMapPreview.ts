import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

export function useFloodMapPreview(
  mapInstance: maplibregl.Map | null,
  floodStart: { coords: [number, number]; label: string } | null,
  floodEnd: { coords: [number, number]; label: string } | null,
  floodPreviewGeometry: any,
  floodOppositeGeometry: any,
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
  }, [floodStart?.coords[0], floodStart?.coords[1], mapInstance, isEnabled]);

  useEffect(() => {
    if (!mapInstance || !floodEnd || !isEnabled) return;
    mapInstance.flyTo({
      center: floodEnd.coords,
      zoom: Math.max(mapInstance.getZoom(), 14),
      bearing: mapInstance.getBearing(),
      pitch: mapInstance.getPitch(),
      duration: 600,
    });
  }, [floodEnd?.coords[0], floodEnd?.coords[1], mapInstance, isEnabled]);

  // Markers
  const startMarkerRef = useRef<maplibregl.Marker | null>(null);
  const endMarkerRef = useRef<maplibregl.Marker | null>(null);

  useEffect(() => {
    if (!mapInstance || !isEnabled) return;
    startMarkerRef.current?.remove();
    startMarkerRef.current = null;
    if (floodStart) {
      startMarkerRef.current = new maplibregl.Marker({ color: "#f97316" })
        .setLngLat(floodStart.coords)
        .addTo(mapInstance);
    }
  }, [mapInstance, floodStart, isEnabled]);

  useEffect(() => {
    if (!mapInstance || !isEnabled) return;
    endMarkerRef.current?.remove();
    endMarkerRef.current = null;
    if (floodEnd) {
      endMarkerRef.current = new maplibregl.Marker({ color: "#991b1b" })
        .setLngLat(floodEnd.coords)
        .addTo(mapInstance);
    }
  }, [mapInstance, floodEnd, isEnabled]);

  // Preview layer
  useEffect(() => {
    if (!mapInstance || !isEnabled) return;

    const PREVIEW_SOURCE = "shared-flood-preview-source";
    const PREVIEW_LAYER = "shared-flood-preview-layer";

    try {
      if (mapInstance.getLayer(PREVIEW_LAYER)) mapInstance.removeLayer(PREVIEW_LAYER);
      if (mapInstance.getSource(PREVIEW_SOURCE)) mapInstance.removeSource(PREVIEW_SOURCE);
    } catch {}

    if (!floodPreviewGeometry) return;

    const features: any[] = [
      {
        type: "Feature",
        properties: { is_opposite: false },
        geometry: floodPreviewGeometry,
      },
    ];

    if (floodIsBidirectional && floodOppositeGeometry) {
      features.push({
        type: "Feature",
        properties: { is_opposite: true },
        geometry: floodOppositeGeometry,
      });
    }

    try {
      mapInstance.addSource(PREVIEW_SOURCE, {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features,
        },
      });

      mapInstance.addLayer({
        id: PREVIEW_LAYER,
        type: "line",
        source: PREVIEW_SOURCE,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": [
            "case",
            ["==", ["get", "is_opposite"], true],
            "#fb923c",
            "#f97316",
          ],
          "line-width": 6,
          "line-dasharray": [2, 2],
          "line-opacity": 0.85,
        },
      });
    } catch (err) {
      console.warn("Failed to add shared preview layer", err);
    }

    return () => {
      try {
        if (mapInstance.getLayer(PREVIEW_LAYER)) mapInstance.removeLayer(PREVIEW_LAYER);
        if (mapInstance.getSource(PREVIEW_SOURCE)) mapInstance.removeSource(PREVIEW_SOURCE);
      } catch {}
    };
  }, [mapInstance, floodPreviewGeometry, floodOppositeGeometry, floodIsBidirectional, isEnabled]);
}
