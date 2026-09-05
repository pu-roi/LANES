import React, { useEffect, useRef } from "react";
import maplibregl, { Map } from "maplibre-gl";
import { createRoot, type Root } from "react-dom/client";
import { FloodZonePopup } from "../components/FloodZonePopup";
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
  const activePopupRef = useRef<{ popup: maplibregl.Popup; root: Root; reportId?: number } | null>(null);
  const openTimeoutRef = useRef<any>(null);
  const closeTimeoutRef = useRef<any>(null);
  const pendingHoverIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!map || !isLoaded) return;

    const clearCloseTimeout = () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
        closeTimeoutRef.current = null;
      }
    };

    const clearOpenTimeout = () => {
      if (openTimeoutRef.current) {
        clearTimeout(openTimeoutRef.current);
        openTimeoutRef.current = null;
      }
      pendingHoverIdRef.current = null;
    };

    const scheduleClose = () => {
      clearCloseTimeout();
      closeTimeoutRef.current = setTimeout(() => {
        if (activePopupRef.current) {
          activePopupRef.current.popup.remove();
          activePopupRef.current = null;
        }
      }, 150);
    };

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
          severity: severity.toUpperCase(),
          color,
          border_color: borderColor,
          is_selected: isSelected,
          created_at: report.created_at,
          report_text: report.raw_text,
          reporter_name: report.reporter_name || "Verified Citizen",
          reporter_role: report.reporter_role || "Citizen",
          depth: report.depth,
          passable_vehicles: report.survey?.passable_vehicles,
          hidden_hazards: report.survey?.hidden_hazards,
          is_pending: true,
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
          filter: [
            "all",
            ["!=", ["get", "is_zoomed_out_point"], true],
            ["in", ["geometry-type"], ["literal", ["LineString", "MultiLineString"]]],
          ],
          layout: {
            "line-cap": "round",
            "line-join": "round",
          },
          paint: PENDING_REPORT_ROAD_AURA_PAINT,
        });
      }

      // Layer 3: Zoomed-in Pure Transparent Polygon Auras (Street View: Zoom > 14)
      if (!map.getLayer("all-pending-reports-polygon-layer")) {
        map.addLayer({
          id: "all-pending-reports-polygon-layer",
          type: "fill",
          source: sourceId,
          filter: [
            "all",
            ["!=", ["get", "is_zoomed_out_point"], true],
            ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
          ],
          paint: {
            "fill-color": ["get", "color"],
            "fill-opacity": [
              "step", ["zoom"],
              0,
              14,
              ["case", ["==", ["get", "is_selected"], true], 0.55, 0.35],
            ],
          },
        });
      }

      // Layer 4: Zoomed-in Pure Transparent Point Auras (Street View: Zoom > 14)
      if (!map.getLayer("all-pending-reports-point-layer")) {
        map.addLayer({
          id: "all-pending-reports-point-layer",
          type: "circle",
          source: sourceId,
          filter: [
            "all",
            ["!=", ["get", "is_zoomed_out_point"], true],
            ["in", ["geometry-type"], ["literal", ["Point", "MultiPoint"]]],
          ],
          paint: PENDING_REPORT_POINT_AURA_PAINT,
        });
      }
    };

    setupLayers();

    const handleMapStyleData = () => {
      setupLayers();
    };
    map.on("styledata", handleMapStyleData);

    const handlePopupOpen = (properties: any, lngLat: { lng: number; lat: number }) => {
      if (!properties) return;

      clearCloseTimeout();

      // If active popup is already showing this exact report, don't recreate
      if (activePopupRef.current && activePopupRef.current.reportId === Number(properties.id)) {
        return;
      }

      if (activePopupRef.current) {
        activePopupRef.current.popup.remove();
        activePopupRef.current = null;
      }

      const popupContainer = document.createElement("div");
      popupContainer.className = "flood-zone-popup-root";
      
      popupContainer.addEventListener("mouseenter", clearCloseTimeout);
      popupContainer.addEventListener("mouseleave", scheduleClose);

      let smartAnchor: maplibregl.PositionAnchor = "bottom";
      try {
        const pt = map.project(lngLat);
        const mapCanvas = map.getCanvas();
        const width = mapCanvas.clientWidth || window.innerWidth;
        const height = mapCanvas.clientHeight || window.innerHeight;

        const spaceAbove = pt.y;
        const spaceBelow = height - pt.y;
        const spaceLeft = pt.x;
        const spaceRight = width - pt.x;

        // The popup is ~350px tall and 340px wide.
        // Accounting for top app bars (~60px), we need at least 420px above to safely anchor "bottom".
        const canFitAbove = spaceAbove >= 420;
        const canFitBelow = spaceBelow >= 380;
        const isNearLeft = spaceLeft < 190;
        const isNearRight = spaceRight < 190;

        if (canFitAbove) {
          if (isNearLeft) smartAnchor = "bottom-left";
          else if (isNearRight) smartAnchor = "bottom-right";
          else smartAnchor = "bottom";
        } else if (canFitBelow) {
          if (isNearLeft) smartAnchor = "top-left";
          else if (isNearRight) smartAnchor = "top-right";
          else smartAnchor = "top";
        } else {
          // If vertical space is constrained, place to the side with more horizontal room
          if (spaceRight >= spaceLeft) {
            smartAnchor = "left";
          } else {
            smartAnchor = "right";
          }
        }
      } catch (err) {
        smartAnchor = "bottom";
      }

      const root = createRoot(popupContainer);

      const popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        maxWidth: "360px",
        offset: 14,
        anchor: smartAnchor,
        className: "flood-zone-popup",
      })
        .setLngLat(lngLat)
        .setDOMContent(popupContainer)
        .addTo(map);

      // Colorize the popup tip to match the header when anchored at the top
      const tip = popup.getElement()?.querySelector(".maplibregl-popup-tip") as HTMLElement;
      if (tip) {
        if (smartAnchor.startsWith("top")) {
          tip.style.borderBottomColor = properties.color || "#eab308";
        } else if (smartAnchor.startsWith("bottom")) {
          tip.style.borderTopColor = "#f9fafb";
        }
      }

      root.render(React.createElement(FloodZonePopup, { properties }));

      popup.on("close", () => {
        setTimeout(() => root.unmount(), 0);
        if (activePopupRef.current?.popup === popup) {
          activePopupRef.current = null;
        }
      });

      activePopupRef.current = { popup, root, reportId: Number(properties.id) };
    };

    const handleMouseEnterOrMove = (e: any) => {
      map.getCanvas().style.cursor = "pointer";
      if (!e.features || e.features.length === 0) return;
      const feature = e.features[0];
      const properties = feature.properties;
      const id = Number(properties?.id);
      if (!id) return;

      clearCloseTimeout();

      // If popup is already active for this exact report, don't recreate
      if (activePopupRef.current && activePopupRef.current.reportId === id) {
        return;
      }

      // If already counting down for this exact report, let the timer run (do not reset!)
      if (pendingHoverIdRef.current === id) {
        return;
      }

      // Start 400ms hover dwell countdown for this report
      clearOpenTimeout();
      pendingHoverIdRef.current = id;
      const targetLngLat = { lng: e.lngLat.lng, lat: e.lngLat.lat };

      openTimeoutRef.current = setTimeout(() => {
        handlePopupOpen(properties, targetLngLat);
        pendingHoverIdRef.current = null;
      }, 400);
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
      clearOpenTimeout();
      scheduleClose();
    };

    // Interactivity
    const handleLayerClick = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      const feature = e.features[0];
      const id = feature.properties.id;
      const isSelecting = id !== selectedReportId;
      setSelectedReportId(isSelecting ? id : null);

      // Center, angle, and zoom into the clicked report ONLY on select
      if (isSelecting && e.lngLat) {
        flyToCoordinates(map, [e.lngLat.lng, e.lngLat.lat], { zoom: 16, pitch: map.getPitch(), duration: 1500 });
      }
    };

    const layers = [
      "all-pending-reports-circle-layer",
      "all-pending-reports-line-layer",
      "all-pending-reports-polygon-layer",
      "all-pending-reports-point-layer",
    ];

    layers.forEach((layer) => {
      map.on("click", layer, handleLayerClick);
      map.on("mouseenter", layer, handleMouseEnterOrMove);
      map.on("mousemove", layer, handleMouseEnterOrMove);
      map.on("mouseleave", layer, handleMouseLeave);
    });

    return () => {
      map.off("styledata", handleMapStyleData);
      clearOpenTimeout();
      clearCloseTimeout();
      if (activePopupRef.current) {
        activePopupRef.current.popup.remove();
        activePopupRef.current = null;
      }
      layers.forEach((layer) => {
        map.off("click", layer, handleLayerClick);
        map.off("mouseenter", layer, handleMouseEnterOrMove);
        map.off("mousemove", layer, handleMouseEnterOrMove);
        map.off("mouseleave", layer, handleMouseLeave);
      });
    };
  }, [map, isLoaded, pendingReports, activeTab, selectedReportId, isolatedReportId]);
}
