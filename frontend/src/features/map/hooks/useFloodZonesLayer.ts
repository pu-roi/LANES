import React, { useEffect, useRef } from "react";
import maplibregl, { Map } from "maplibre-gl";
import { createRoot, type Root } from "react-dom/client";
import { FloodZonePopup } from "../components/FloodZonePopup";
import {
  SEVERITY_COLORS,
  SEVERITY_BORDER_COLORS,
  ZOOM_THRESHOLDS,
  PIN_CIRCLE_PAINT,
  ACTIVE_ZONE_POLYGON_FILL_PAINT,
  ACTIVE_ZONE_ROAD_CORE_PAINT,
} from "../mapStyles";
import { computeCenterCoordinate } from "../mapGeoUtils";

export function useFloodZonesLayer(
  map: Map | null,
  isLoaded: boolean,
  activeZonesData?: any[],
  isTouchDevice: boolean = false,
  activeTab: string = "zones",
  selectedZoneId?: number | null,
  setSelectedZoneId?: (id: number | null) => void,
  selectedContributorId?: number | null,
  setSelectedContributorId?: (id: number | null) => void
) {
  const activePopupRef = useRef<{ popup: maplibregl.Popup; root: Root } | null>(null);

  useEffect(() => {
    console.log("[useFloodZonesLayer] hook execution started", { mapExists: !!map, isLoaded, activeZonesLength: activeZonesData?.length });
    if (!map || !isLoaded) return;

    const setupLayers = () => {
      console.log("[useFloodZonesLayer] setupLayers triggered", { activeZonesDataLength: activeZonesData?.length, activeTab });

      const sourceId = "active-zones-source";
      const existingSource = map.getSource(sourceId) as maplibregl.GeoJSONSource;

      if (!activeZonesData || activeZonesData.length === 0 || activeTab !== "zones") {
        console.log("[useFloodZonesLayer] Cleared active zones because activeZonesData is empty or activeTab is not 'zones'");
        if (existingSource) {
          existingSource.setData({ type: "FeatureCollection", features: [] });
        }
        return;
      }
      
      console.log("[useFloodZonesLayer] Proceeding to add map layers for active zones");

      const features: any[] = [];
      activeZonesData.forEach((zone: any) => {
        const severity = (zone.severity || "medium").toLowerCase();
        const color = SEVERITY_COLORS[severity] || "#eab308";
        const borderColor = SEVERITY_BORDER_COLORS[severity] || "#a16207";
        const isSelected = selectedZoneId === zone.id;

        // Check if a specific contributor in this zone is being inspected
        const contributors: any[] = zone.contributors || [];
        const activeContributor = selectedContributorId 
          ? contributors.find((c: any) => c.report_id === selectedContributorId) 
          : null;

        // If inspecting a specific contributor in this zone, render ONLY that contributor's original individual report geometry!
        if (activeContributor && activeContributor.geometry) {
          const contribSeverity = (activeContributor.severity || severity).toLowerCase();
          const contribColor = SEVERITY_COLORS[contribSeverity] || color;
          const contribBorder = SEVERITY_BORDER_COLORS[contribSeverity] || borderColor;
          const isLine = activeContributor.geometry.type === "LineString";

          const contribProps = {
            id: zone.id,
            contributor_report_id: activeContributor.report_id,
            reporter_name: activeContributor.reporter_name,
            reporter_role: activeContributor.reporter_role,
            is_road_based: isLine,
            severity: contribSeverity.toUpperCase(),
            color: contribColor,
            border_color: contribBorder,
            is_selected: isSelected,
          };

          if (isLine) {
            features.push({
              type: "Feature",
              properties: { ...contribProps, is_zoomed_out_point: false, is_road_line: true },
              geometry: activeContributor.geometry,
            });
          } else if (activeContributor.geometry.type === "Point") {
            features.push({
              type: "Feature",
              properties: { ...contribProps, is_zoomed_out_point: true, is_road_line: false },
              geometry: activeContributor.geometry,
            });
          }
          
          const centerCoord = computeCenterCoordinate(
            activeContributor.geometry.type === "Point" ? activeContributor.geometry : null, 
            activeContributor.geometry.type === "LineString" ? activeContributor.geometry : null
          );
          if (centerCoord) {
            features.push({
              type: "Feature",
              properties: { ...contribProps, is_zoomed_out_point: true, is_road_line: false },
              geometry: { type: "Point", coordinates: centerCoord },
            });
          }
          return; // Skip rendering the generic merged polygon / road line!
        }

        // Standard Avoidance Zone rendering
        const isRoadBased = zone.report_geometry && zone.report_geometry.type === "LineString";
        const commonProps = {
          id: zone.id,
          report_id: zone.report_id,
          severity: severity.toUpperCase(),
          color: color,
          border_color: borderColor,
          is_road_based: isRoadBased,
          is_selected: isSelected,
          created_at: zone.created_at,
          expires_at: zone.expires_at,
          depth: zone.depth,
          report_text: zone.report_text,
          reporter_name: zone.reporter_name,
          reporter_role: zone.reporter_role,
          passable_vehicles: zone.passable_vehicles,
          hidden_hazards: zone.hidden_hazards,
          contributors_json: JSON.stringify(zone.contributors || []),
        };

        // 1. Zoomed-in Road Solid Core feature
        if (isRoadBased && zone.report_geometry) {
          features.push({
            type: "Feature",
            properties: { ...commonProps, is_zoomed_out_point: false, is_road_line: true },
            geometry: zone.report_geometry,
          });
        }

        // 2. Zoomed-in Avoidance Buffer Polygon
        if (zone.geometry) {
          features.push({
            type: "Feature",
            properties: { ...commonProps, is_zoomed_out_point: false, is_road_line: false },
            geometry: zone.geometry,
          });
        }

        // 3. Zoomed-out Center Coordinate Point
        const centerCoord = computeCenterCoordinate(zone.geometry, zone.report_geometry);
        if (centerCoord) {
          features.push({
            type: "Feature",
            properties: { ...commonProps, is_zoomed_out_point: true, is_road_line: false },
            geometry: { type: "Point", coordinates: centerCoord },
          });
        }
      });

      // Sort features so selected zone renders on top
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
        if (!map.getStyle()) return; // Failsafe
        map.addSource(sourceId, {
          type: "geojson",
          data: featureCollection,
        });
      }

      // Layer 1: Avoidance Buffer Polygon Aura (Street Level: Zoom > 14 - pure transparent buffer, no border)
      if (!map.getLayer("active-zones-layer")) {
        map.addLayer({
          id: "active-zones-layer",
          type: "fill",
          source: sourceId,
          paint: ACTIVE_ZONE_POLYGON_FILL_PAINT,
          filter: ["==", ["geometry-type"], "Polygon"],
        });
      }

      // Layer 2: Solid Inner Centerline for Road Segments (Street Level: Zoom > 14)
      if (!map.getLayer("active-zones-road-core-layer")) {
        map.addLayer({
          id: "active-zones-road-core-layer",
          type: "line",
          source: sourceId,
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: ACTIVE_ZONE_ROAD_CORE_PAINT,
          filter: ["all", ["!=", ["get", "is_zoomed_out_point"], true], ["==", ["geometry-type"], "LineString"]],
        });
      }

      // Layer 3: Standardized Map Pin Circles (City Overview: Zoom <= 14)
      if (!map.getLayer("active-zones-circle-layer")) {
        map.addLayer({
          id: "active-zones-circle-layer",
          type: "circle",
          source: sourceId,
          paint: PIN_CIRCLE_PAINT,
          filter: ["==", ["get", "is_zoomed_out_point"], true],
        });
      }
    };

    setupLayers();

    // MapLibre GL JS v5 fires 'style.load' (not just 'styledata') after setTerrain()
    // wipes custom layers. Listening here ensures flood zones are always re-applied.
    const handleMapStyleData = () => {
      setupLayers();
    };
    map.on("style.load", handleMapStyleData);

    // Popups and Interactivity
    const closeTimeoutRef = { current: null as any };
    const openTimeoutRef = { current: null as any };

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
    };

    const scheduleClose = () => {
      clearCloseTimeout();
      closeTimeoutRef.current = setTimeout(() => {
        if (!isTouchDevice && activePopupRef.current) {
          activePopupRef.current.popup.remove();
        }
      }, 200); // 200ms grace period to allow cursor to bridge into the popup
    };

    const handlePopupOpen = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      const properties = e.features[0].properties;
      if (!properties) return;

      clearCloseTimeout();

      if (activePopupRef.current) {
        activePopupRef.current.popup.remove();
      }

      const popupContainer = document.createElement("div");
      popupContainer.className = "flood-zone-popup-root";
      
      // Keep popup open when hovering over the popup itself
      popupContainer.addEventListener("mouseenter", clearCloseTimeout);
      popupContainer.addEventListener("mouseleave", scheduleClose);

      // Determine smart anchor placement based on screen position
      let smartAnchor: maplibregl.PositionAnchor = "bottom";
      let projectedPoint: { x: number; y: number } = { x: 0, y: 0 };
      try {
        projectedPoint = map.project(e.lngLat);
      } catch (err) {
        projectedPoint = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
      }

      const mapCanvas = map.getCanvas();
      const width = mapCanvas.clientWidth || window.innerWidth;
      const height = mapCanvas.clientHeight || window.innerHeight;

      const { x, y } = projectedPoint;

      // Popup is approx 320px tall (or up to 450px when expanded)
      const isNearTop = y < 380;
      const isNearBottom = y > height - 200;
      const isNearLeft = x < 200;
      const isNearRight = x > width - 200;

      if (isNearTop && isNearLeft) smartAnchor = "top-left";
      else if (isNearTop && isNearRight) smartAnchor = "top-right";
      else if (isNearTop) smartAnchor = "top";
      else if (isNearBottom && isNearLeft) smartAnchor = "bottom-left";
      else if (isNearBottom && isNearRight) smartAnchor = "bottom-right";
      else if (isNearBottom) smartAnchor = "bottom";
      else if (isNearLeft) smartAnchor = "left";
      else if (isNearRight) smartAnchor = "right";
      else smartAnchor = "bottom";

      const root = createRoot(popupContainer);

      const popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: true,
        maxWidth: "320px",
        offset: 14,
        anchor: smartAnchor,
        className: "flood-zone-popup",
      })
        .setLngLat(e.lngLat)
        .setDOMContent(popupContainer)
        .addTo(map);

      // Auto-fit function to ensure popup never bleeds outside any side of the viewport
      const fitPopupIntoView = () => {
        setTimeout(() => {
          if (!popup.isOpen()) return;
          const el = popup.getElement();
          if (!el) return;
          const rect = el.getBoundingClientRect();
          const padding = 16;

          let panX = 0;
          let panY = 0;

          if (rect.top < padding) {
            panY = -(padding - rect.top);
          } else if (rect.bottom > window.innerHeight - padding) {
            panY = rect.bottom - (window.innerHeight - padding);
          }

          if (rect.left < padding) {
            panX = -(padding - rect.left);
          } else if (rect.right > window.innerWidth - padding) {
            panX = rect.right - (window.innerWidth - padding);
          }

          if ((panX !== 0 || panY !== 0) && map.getPitch() < 75) {
            map.panBy([panX, panY], { duration: 250 });
          }
        }, 60);
      };

      // Run on initial mount to guarantee visibility
      fitPopupIntoView();

      root.render(React.createElement(FloodZonePopup, { properties, onToggleExpand: fitPopupIntoView }));

      popup.on("close", () => {
        setTimeout(() => root.unmount(), 0);
        if (activePopupRef.current?.popup === popup) {
          activePopupRef.current = null;
        }
      });

      activePopupRef.current = { popup, root };
    };

    const handleMouseEnter = (e: any) => {
      map.getCanvas().style.cursor = "pointer";
      if (!isTouchDevice) {
        clearOpenTimeout();
        openTimeoutRef.current = setTimeout(() => {
          handlePopupOpen(e);
        }, 400); // 400ms delay before showing popup
      }
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
      if (!isTouchDevice) {
        clearOpenTimeout(); // Clear open timeout if user leaves early
        scheduleClose();
      }
    };

    const handleZoneClick = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      const id = e.features[0].properties.id;
      if (setSelectedZoneId && id) {
        setSelectedZoneId(selectedZoneId === Number(id) ? null : Number(id));
      }

      // Center, angle, and zoom into the clicked active zone (matching sidebar flyTo parameters)
      if (e.lngLat) {
        map.flyTo({
          center: [e.lngLat.lng, e.lngLat.lat],
          zoom: 16,
          pitch: 45,
          duration: 1500,
        });
      }

      if (isTouchDevice) {
        handlePopupOpen(e);
      }
    };

    const activeLayers = [
      "active-zones-layer",
      "active-zones-road-core-layer",
      "active-zones-circle-layer",
    ];

    activeLayers.forEach((layer) => {
      map.on("mouseenter", layer, handleMouseEnter);
      map.on("mouseleave", layer, handleMouseLeave);
      map.on("click", layer, handleZoneClick);
    });

    return () => {
      map.off("style.load", handleMapStyleData);
      if (activePopupRef.current) {
        activePopupRef.current.popup.remove();
      }
      activeLayers.forEach((layer) => {
        map.off("mouseenter", layer, handleMouseEnter);
        map.off("mouseleave", layer, handleMouseLeave);
        map.off("click", layer, handleZoneClick);
      });
    };
  }, [map, isLoaded, activeZonesData, isTouchDevice, activeTab, selectedZoneId, selectedContributorId]);
}
