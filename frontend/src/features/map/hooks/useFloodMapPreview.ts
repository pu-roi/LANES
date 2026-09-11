import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import type { RouteGeometry } from "@/features/routing/routingApi";

const MAX_ENDPOINT_CONNECTOR_METERS = 40;

function distanceMeters(first: [number, number], second: [number, number]) {
  const meanLatitude = ((first[1] + second[1]) / 2) * (Math.PI / 180);
  const dx = (second[0] - first[0]) * 111_000 * Math.cos(meanLatitude);
  const dy = (second[1] - first[1]) * 111_000;
  return Math.hypot(dx, dy);
}

function endpointConnectorFeatures(geometry: RouteGeometry): GeoJSON.Feature<GeoJSON.LineString>[] {
  const coordinates = geometry.coordinates;
  if (coordinates.length < 3) return [];

  const segments = [
    [coordinates[0], coordinates[1]],
    [coordinates[coordinates.length - 2], coordinates[coordinates.length - 1]],
  ] as [number, number][][];

  return segments
    .filter(([start, end]) => distanceMeters(start, end) <= MAX_ENDPOINT_CONNECTOR_METERS)
    .map((segment) => ({
      type: "Feature",
      properties: {},
      geometry: { type: "LineString", coordinates: segment },
    }));
}

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
      startMarkerRef.current = new maplibregl.Marker({ color: "#f97316" })
        .setLngLat(floodStart.coords)
        .addTo(mapInstance);
    }

    return () => {
      startMarkerRef.current?.remove();
      startMarkerRef.current = null;
    };
  }, [mapInstance, floodStart, isEnabled]);

  useEffect(() => {
    endMarkerRef.current?.remove();
    endMarkerRef.current = null;
    if (mapInstance && isEnabled && floodEnd) {
      endMarkerRef.current = new maplibregl.Marker({ color: "#991b1b" })
        .setLngLat(floodEnd.coords)
        .addTo(mapInstance);
    }

    return () => {
      endMarkerRef.current?.remove();
      endMarkerRef.current = null;
    };
  }, [mapInstance, floodEnd, isEnabled]);

  // Preview layer
  useEffect(() => {
    const PREVIEW_SOURCE = "shared-flood-preview-source";
    const PREVIEW_LAYER = "shared-flood-preview-layer";
    const ENDPOINT_SOURCE = "shared-flood-preview-endpoint-source";
    const ENDPOINT_LAYER = "shared-flood-preview-endpoint-layer";

    if (!mapInstance) return;

    const removePreview = () => {
      try {
        if (!mapInstance || typeof mapInstance.getLayer !== "function") return;
        if (typeof mapInstance.getStyle === "function" && !mapInstance.getStyle()) return;
        if (mapInstance.getLayer(ENDPOINT_LAYER)) mapInstance.removeLayer(ENDPOINT_LAYER);
        if (mapInstance.getLayer(PREVIEW_LAYER)) mapInstance.removeLayer(PREVIEW_LAYER);
        if (mapInstance.getSource(ENDPOINT_SOURCE)) mapInstance.removeSource(ENDPOINT_SOURCE);
        if (mapInstance.getSource(PREVIEW_SOURCE)) mapInstance.removeSource(PREVIEW_SOURCE);
      } catch {
        // Silently ignore teardown races
      }
    };

    const renderPreview = () => {
      removePreview();
      if (!isEnabled || !floodPreviewGeometry || !mapInstance.getStyle()) return;

      const features: GeoJSON.Feature<RouteGeometry>[] = [
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
            "line-color": "#f97316",
            "line-width": 6,
            "line-dasharray": [2, 2],
            "line-opacity": 0.9,
          },
        });

        const endpointFeatures = endpointConnectorFeatures(floodPreviewGeometry);
        if (endpointFeatures.length > 0) {
          mapInstance.addSource(ENDPOINT_SOURCE, {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: endpointFeatures,
            },
          });
          mapInstance.addLayer({
            id: ENDPOINT_LAYER,
            type: "line",
            source: ENDPOINT_SOURCE,
            layout: { "line-join": "round", "line-cap": "round" },
            paint: {
              "line-color": "#f97316",
              "line-width": 6,
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
