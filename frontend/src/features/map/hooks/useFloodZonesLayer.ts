import { useEffect } from "react";
import maplibregl, { Map } from "maplibre-gl";

const SEVERITY_COLORS: Record<string, string> = {
  low: "#84cc16",     // Lime (Yellow-Green) - Gutter & Half-Knee
  medium: "#eab308",  // Yellow (Amber) - Half-Tire & Knee
  high: "#f97316",    // Orange - Tires & Waist
  extreme: "#ef4444", // Red - Chest & Neck
};

export function useFloodZonesLayer(map: Map | null, isLoaded: boolean, activeZonesData?: any[]) {
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

    // 4. Click Popups for Flood Info
    const handlePopup = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      const properties = e.features[0].properties;
      if (!properties) return;

      let reportedText = properties.created_at;
      try {
        if (reportedText) {
          const d = new Date(reportedText);
          if (!isNaN(d.getTime())) {
            reportedText = d.toLocaleString("en-US", {
              month: "short",
              day: "numeric",
              hour: "numeric",
              minute: "2-digit",
            });
          }
        }
      } catch (err) {}

      new maplibregl.Popup({ closeButton: true, maxWidth: "280px" })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div style="font-family: inherit; padding: 4px; color: #1e293b; min-width: 180px;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
              <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: ${properties.color};"></span>
              <strong style="font-size: 14px; text-transform: capitalize;">${properties.severity} Risk</strong>
            </div>
            <div style="font-size: 12px; margin-bottom: 4px;">
              <span style="color: #64748b; font-weight: 500;">Reported:</span>
              <span style="font-weight: 600; margin-left: 4px;">${reportedText || "Unknown"}</span>
            </div>
            ${
              properties.expires_at
                ? `
            <div style="font-size: 11px; margin-top: 6px; color: #ef4444; font-weight: 500;">
              Active Zone
            </div>
            `
                : ""
            }
          </div>
        `)
        .addTo(map);
    };

    const handleMouseEnter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
    };

    map.on("click", "active-zones-layer", handlePopup);
    map.on("click", "active-zones-road-layer", handlePopup);
    map.on("mouseenter", "active-zones-layer", handleMouseEnter);
    map.on("mouseleave", "active-zones-layer", handleMouseLeave);
    map.on("mouseenter", "active-zones-road-layer", handleMouseEnter);
    map.on("mouseleave", "active-zones-road-layer", handleMouseLeave);

    return () => {
      map.off("click", "active-zones-layer", handlePopup);
      map.off("click", "active-zones-road-layer", handlePopup);
      map.off("mouseenter", "active-zones-layer", handleMouseEnter);
      map.off("mouseleave", "active-zones-layer", handleMouseLeave);
      map.off("mouseenter", "active-zones-road-layer", handleMouseEnter);
      map.off("mouseleave", "active-zones-road-layer", handleMouseLeave);
    };
  }, [map, isLoaded, activeZonesData]);
}
