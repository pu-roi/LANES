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
import { computeCenterCoordinate } from "../mapGeoUtils";

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
      if (!map.isStyleLoaded()) return;

      if (activeTab !== "pending" || !pendingReports || pendingReports.length === 0) {
        // Hide pending reports if we are not on the pending moderation tab
        const existingSource = map.getSource("all-pending-reports-source") as maplibregl.GeoJSONSource;
        if (existingSource) existingSource.setData({ type: "FeatureCollection", features: [] });
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

      // Remove existing sources/layers if they exist
      const layersToRemove = [
        "all-pending-reports-circle-layer",
        "all-pending-reports-line-layer",
        "all-pending-reports-point-layer",
      ];
      layersToRemove.forEach((l) => {
        if (map.getLayer(l)) map.removeLayer(l);
      });
      if (map.getSource("all-pending-reports-source")) {
        map.removeSource("all-pending-reports-source");
      }

      // Add source
      map.addSource("all-pending-reports-source", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: features,
        },
      });

      // Layer 1: Zoomed-out Circle Map Pins (City View: Zoom <= 14)
      map.addLayer({
        id: "all-pending-reports-circle-layer",
        type: "circle",
        source: "all-pending-reports-source",
        maxzoom: ZOOM_THRESHOLDS.PIN_MAX_ZOOM,
        filter: ["==", ["get", "is_zoomed_out_point"], true],
        paint: PIN_CIRCLE_PAINT,
      });

      // Layer 2: Zoomed-in Pure Transparent Road Auras (Street View: Zoom > 14)
      map.addLayer({
        id: "all-pending-reports-line-layer",
        type: "line",
        source: "all-pending-reports-source",
        minzoom: ZOOM_THRESHOLDS.DETAILED_MIN_ZOOM,
        filter: ["all", ["!=", ["get", "is_zoomed_out_point"], true], ["==", ["geometry-type"], "LineString"]],
        layout: {
          "line-cap": "round",
          "line-join": "round",
        },
        paint: PENDING_REPORT_ROAD_AURA_PAINT,
      });

      // Layer 3: Zoomed-in Pure Transparent Point Auras (Street View: Zoom > 14)
      map.addLayer({
        id: "all-pending-reports-point-layer",
        type: "circle",
        source: "all-pending-reports-source",
        minzoom: ZOOM_THRESHOLDS.DETAILED_MIN_ZOOM,
        filter: ["all", ["!=", ["get", "is_zoomed_out_point"], true], ["==", ["geometry-type"], "Point"]],
        paint: PENDING_REPORT_POINT_AURA_PAINT,
      });

      // Interactivity
      const handleLayerClick = (e: any) => {
        if (!e.features || e.features.length === 0) return;
        const feature = e.features[0];
        const id = feature.properties.id;
        setSelectedReportId(id === selectedReportId ? null : id);

        // Center, angle, and zoom into the clicked report (matching sidebar flyTo parameters)
        if (e.lngLat) {
          map.flyTo({
            center: [e.lngLat.lng, e.lngLat.lat],
            zoom: 16,
            pitch: 45,
            duration: 1500,
          });
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
    };

    const trySetup = () => {
      if (map.isStyleLoaded()) {
        setupLayers();
      } else {
        let attempts = 0;
        const interval = setInterval(() => {
          attempts++;
          if (map.isStyleLoaded()) {
            clearInterval(interval);
            setupLayers();
          } else if (attempts > 15) {
            clearInterval(interval);
          }
        }, 100);
      }
    };

    trySetup();
  }, [map, isLoaded, pendingReports, activeTab, selectedReportId]);
}
