import { useEffect } from "react";
import type { Map } from "maplibre-gl";
import {
  SEVERITY_COLORS,
  SEVERITY_BORDER_COLORS,
  ZOOM_THRESHOLDS,
  PIN_CIRCLE_PAINT,
  PENDING_REPORT_ROAD_AURA_PAINT,
  PENDING_REPORT_POINT_AURA_PAINT,
} from "../mapStyles";
import { computeCenterCoordinate, flyToCoordinates } from "../mapGeoUtils";

export function usePendingReportsLayer(
  map: Map | null,
  isLoaded: boolean,
  pendingReports: any[],
  activeTab: string,
  setSelectedReportId: (id: number | null) => void,
  selectedReportId: number | null,
  isolatedReportId?: number | null
) {
  useEffect(() => {
    if (!map || !isLoaded) return;

    const setupLayers = () => {
      if (!map.getStyle()) return;

      const sourceId = "all-pending-reports-source";
      const existingSource = map.getSource(sourceId) as maplibregl.GeoJSONSource;

      if (activeTab !== "pending" || !pendingReports || pendingReports.length === 0) {
        // Hide pending reports if we are not on the pending moderation tab
        if (existingSource) {
          existingSource.setData({ type: "FeatureCollection", features: [] });
        }
        return;
      }

      const features: any[] = [];

      // If an isolatedReportId is set, only render that specific report on the map!
      const targetReports = isolatedReportId 
        ? pendingReports.filter((r) => r.id === isolatedReportId) 
        : pendingReports;

      targetReports.forEach((report) => {
        if (!report.geometry) return;
        const severity = (report.severity || "medium").toLowerCase();
        const color = SEVERITY_COLORS[severity] || "#eab308";
        const borderColor = SEVERITY_BORDER_COLORS[severity] || "#a16207";
        const isSelected = report.id === selectedReportId;

        const commonProps = {
          id: report.id,
          color,
          border_color: borderColor,
          is_selected: isSelected,
        };

        // 1. Zoomed-in detailed geometry (Pure transparent aura only, no solid core)
        features.push({
          type: "Feature",
          properties: { ...commonProps, is_zoomed_out_point: false },
          geometry: report.geometry,
        });

        // 2. Zoomed-out center coordinate for standard map pin circle
        const centerCoord = computeCenterCoordinate(report.geometry, null);
        if (centerCoord) {
          features.push({
            type: "Feature",
            properties: { ...commonProps, is_zoomed_out_point: true },
            geometry: { type: "Point", coordinates: centerCoord },
          });
        }
      });

      // Sort features so selected reports are drawn last (on top)
      features.sort((a, b) => {
        if (a.properties.is_selected && !b.properties.is_selected) return 1;
        if (!a.properties.is_selected && b.properties.is_selected) return -1;
        return 0;
      });

      const featureCollection: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: features,
      };

      if (existingSource) {
        existingSource.setData(featureCollection);
      } else {
        if (!map.getStyle()) return;
        map.addSource(sourceId, {
          type: "geojson",
          data: featureCollection,
        });
      }

      // Layer 1: Zoomed-out Circle Map Pins (City View: Zoom <= 14)
      if (!map.getLayer("all-pending-reports-circle-layer")) {
        map.addLayer({
          id: "all-pending-reports-circle-layer",
          type: "circle",
          source: sourceId,
          filter: ["==", ["get", "is_zoomed_out_point"], true],
          paint: PIN_CIRCLE_PAINT,
        });
      }

      // Layer 2: Zoomed-in Pure Transparent Road Auras (Street View: Zoom > 14)
      if (!map.getLayer("all-pending-reports-line-layer")) {
        map.addLayer({
          id: "all-pending-reports-line-layer",
          type: "line",
          source: sourceId,
          filter: ["all", ["!=", ["get", "is_zoomed_out_point"], true], ["==", ["geometry-type"], "LineString"]],
          layout: {
            "line-cap": "round",
            "line-join": "round",
          },
          paint: PENDING_REPORT_ROAD_AURA_PAINT,
        });
      }

      // Layer 3: Zoomed-in Pure Transparent Point Auras (Street View: Zoom > 14)
      if (!map.getLayer("all-pending-reports-point-layer")) {
        map.addLayer({
          id: "all-pending-reports-point-layer",
          type: "circle",
          source: sourceId,
          filter: ["all", ["!=", ["get", "is_zoomed_out_point"], true], ["==", ["geometry-type"], "Point"]],
          paint: PENDING_REPORT_POINT_AURA_PAINT,
        });
      }
    };

    setupLayers();

    const handleMapStyleData = () => {
      setupLayers();
    };
    map.on("styledata", handleMapStyleData);

    // Interactivity
    const handleLayerClick = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      const feature = e.features[0];
      const id = feature.properties.id;
      const isSelecting = id !== selectedReportId;
      setSelectedReportId(isSelecting ? id : null);

      // Center, angle, and zoom into the clicked report ONLY on select
      if (isSelecting && e.lngLat) {
        flyToCoordinates(map, [e.lngLat.lng, e.lngLat.lat], { zoom: 16, pitch: 45, duration: 1500 });
      }
    };

    const changeCursorToMap = () => (map.getCanvas().style.cursor = "pointer");
    const resetCursor = () => (map.getCanvas().style.cursor = "");

    const layers = [
      "all-pending-reports-circle-layer",
      "all-pending-reports-line-layer",
      "all-pending-reports-point-layer",
    ];

    layers.forEach((layer) => {
      map.on("click", layer, handleLayerClick);
      map.on("mouseenter", layer, changeCursorToMap);
      map.on("mouseleave", layer, resetCursor);
    });

    return () => {
      map.off("styledata", handleMapStyleData);
      layers.forEach((layer) => {
        map.off("click", layer, handleLayerClick);
        map.off("mouseenter", layer, changeCursorToMap);
        map.off("mouseleave", layer, resetCursor);
      });
    };
  }, [map, isLoaded, pendingReports, activeTab, selectedReportId, isolatedReportId]);
}
