import React, { useEffect, useRef } from "react";
import maplibregl, { Map } from "maplibre-gl";
import { createRoot, type Root } from "react-dom/client";
import { FloodZonePopup } from "../components/FloodZonePopup";

const SEVERITY_COLORS: Record<string, string> = {
  low: "#84cc16",     // Lime (Yellow-Green) - Gutter & Half-Knee
  medium: "#eab308",  // Yellow (Amber) - Half-Tire & Knee
  high: "#f97316",    // Orange - Tires & Waist
  extreme: "#ef4444", // Red - Chest & Neck
};

export function useFloodZonesLayer(map: Map | null, isLoaded: boolean, activeZonesData?: any[], isTouchDevice: boolean = false) {
  const activePopupRef = useRef<{ popup: maplibregl.Popup, root: Root } | null>(null);
  useEffect(() => {
    if (!map || !isLoaded || !activeZonesData) return;
    if (!map.style) return;

    // Remove existing sources/layers if they exist
    if (map.getLayer("active-zones-layer")) map.removeLayer("active-zones-layer");
    if (map.getLayer("active-zones-outline")) map.removeLayer("active-zones-outline");
    if (map.getLayer("active-zones-road-layer")) map.removeLayer("active-zones-road-layer");
    if (map.getSource("active-zones-source")) map.removeSource("active-zones-source");

    const features: any[] = [];
    activeZonesData.forEach((zone: any) => {
      const severity = zone.severity || "medium";
      const color = SEVERITY_COLORS[severity] || "#f59e0b";
      const isRoadBased = zone.report_geometry && zone.report_geometry.type === "LineString";

      const commonProps = {
        id: zone.id,
        report_id: zone.report_id,
        severity: severity.toUpperCase(),
        color: color,
        is_road_based: isRoadBased,
        created_at: zone.created_at,
        expires_at: zone.expires_at,
      };

      if (isRoadBased) {
        // Add LineString feature for highlighted road segment glow
        features.push({
          type: "Feature",
          properties: { ...commonProps, is_road_line: true },
          geometry: zone.report_geometry,
        });
      }

      // Add Polygon feature (avoidance zone buffer)
      if (zone.geometry) {
        features.push({
          type: "Feature",
          properties: { ...commonProps, is_road_line: false },
          geometry: zone.geometry,
        });
      }
    });

    map.addSource("active-zones-source", {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: features,
      },
    });

    // 1. Polygon Fill Layer (Renders ALL flood polygons, including road-based ones)
    map.addLayer({
      id: "active-zones-layer",
      type: "fill",
      source: "active-zones-source",
      paint: {
        "fill-color": ["get", "color"],
        "fill-opacity": 0.35,
      },
      filter: ["==", ["geometry-type"], "Polygon"],
    });

    // 2. Polygon Outline Layer
    map.addLayer({
      id: "active-zones-outline",
      type: "line",
      source: "active-zones-source",
      paint: {
        "line-color": ["get", "color"],
        "line-width": 2,
        "line-opacity": 0.8,
      },
      filter: ["==", ["geometry-type"], "Polygon"],
    });

    // 3. Highlighted Road Line Layer (Soft glow for street segments)
    map.addLayer({
      id: "active-zones-road-layer",
      type: "line",
      source: "active-zones-source",
      layout: {
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": ["get", "color"],
        "line-width": 14,
        "line-opacity": 0.6,
      },
      filter: ["==", ["geometry-type"], "LineString"],
    });

    // 4. Popups for Flood Info
    const handlePopupOpen = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      const properties = e.features[0].properties;
      if (!properties) return;

      // Close existing popup if any
      if (activePopupRef.current) {
        activePopupRef.current.popup.remove();
        // The root unmount is handled by the close event listener below
      }

      const popupContainer = document.createElement("div");
      const root = createRoot(popupContainer);
      
      const popup = new maplibregl.Popup({ 
        closeButton: false, 
        closeOnClick: true,
        maxWidth: "340px",
        className: "flood-zone-popup"
      })
        .setLngLat(e.lngLat)
        .setDOMContent(popupContainer)
        .addTo(map);

      root.render(React.createElement(FloodZonePopup, { properties }));

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
        handlePopupOpen(e);
      }
    };
    
    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
      if (!isTouchDevice && activePopupRef.current) {
        activePopupRef.current.popup.remove();
      }
    };

    const handleMouseClick = (e: any) => {
      if (isTouchDevice) {
        handlePopupOpen(e);
      }
    };

    map.on("mouseenter", "active-zones-layer", handleMouseEnter);
    map.on("mouseleave", "active-zones-layer", handleMouseLeave);
    map.on("click", "active-zones-layer", handleMouseClick);

    map.on("mouseenter", "active-zones-road-layer", handleMouseEnter);
    map.on("mouseleave", "active-zones-road-layer", handleMouseLeave);
    map.on("click", "active-zones-road-layer", handleMouseClick);

    return () => {
      if (activePopupRef.current) {
        activePopupRef.current.popup.remove();
      }
      map.off("mouseenter", "active-zones-layer", handleMouseEnter);
      map.off("mouseleave", "active-zones-layer", handleMouseLeave);
      map.off("click", "active-zones-layer", handleMouseClick);
      
      map.off("mouseenter", "active-zones-road-layer", handleMouseEnter);
      map.off("mouseleave", "active-zones-road-layer", handleMouseLeave);
      map.off("click", "active-zones-road-layer", handleMouseClick);
    };
  }, [map, isLoaded, activeZonesData, isTouchDevice]);
}
