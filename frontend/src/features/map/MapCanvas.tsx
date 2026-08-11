"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import type { Map, Marker, MapMouseEvent } from "maplibre-gl";
import { Loader2, MapPin } from "lucide-react";
import { CONSTANTS } from "./mapUtils";
import { useMapContext } from "./MapContext";
import { LoadingOverlay } from "@/shared/ui";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { apiClient } from "@/lib/apiClient";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams, usePathname, useRouter } from "next/navigation";
import { createRoot, type Root } from "react-dom/client";
import BaseMap from "@/shared/ui/BaseMap";
import { useCityBoundaries } from "./hooks/useCityBoundaries";
import { useFloodZonesLayer } from "./hooks/useFloodZonesLayer";

const ROUTE_SOURCE_ID = "route-line";
const ROUTE_LAYER_ID = "route-line-layer";

const OSM_FALLBACK_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: [
        "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png"
      ],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors"
    }
  },
  layers: [
    {
      id: "osm-tiles",
      type: "raster",
      source: "osm",
      minzoom: 0,
      maxzoom: 19
    }
  ]
};

const SEVERITY_COLORS: Record<string, string> = {
  low: "#84cc16",      // Lime 500 (Yellow-Green)
  medium: "#eab308",   // Yellow
  high: "#f97316",     // Orange
  extreme: "#ef4444",  // Red
};

const isPointInPolygon = (point: [number, number], polygon: any): boolean => {
  if (!polygon || polygon.type !== "Polygon" || !polygon.coordinates) return false;
  const x = point[0];
  const y = point[1];
  let inside = false;
  const ring = polygon.coordinates[0];
  if (!ring) return false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0];
    const yi = ring[i][1];
    const xj = ring[j][0];
    const yj = ring[j][1];
    const intersect = ((yi > y) !== (yj > y))
      && (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
};

// ActionGroupControl definition remains for commuter-specific UI

class ActionGroupControl {
  private _map: maplibregl.Map | undefined;
  private _container: HTMLDivElement | undefined;
  private _onSavePlace: () => void;
  private _onAnalytics: () => void;

  constructor(onSavePlace: () => void, onAnalytics: () => void) {
    this._onSavePlace = onSavePlace;
    this._onAnalytics = onAnalytics;
  }

  onAdd(map: maplibregl.Map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl";
    
    // Group container
    this._container.style.cssText = `
      display: flex;
      flex-direction: column;
      background-color: white;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
      overflow: hidden;
    `;
    
    const createButton = (iconSvg: string, color: string, title: string, onClick: () => void, extraClass: string) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.title = title;
      btn.className = extraClass; // Tailwind classes for display logic
      
      btn.style.cssText = `
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        background-color: transparent;
        color: ${color};
        border: none;
        cursor: pointer;
        transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 0;
      `;
      
      btn.onmouseenter = () => {
        btn.style.backgroundColor = "#f8fafc";
      };
      btn.onmouseleave = () => {
        btn.style.backgroundColor = "transparent";
      };
      
      btn.innerHTML = iconSvg;
      btn.onclick = onClick;
      return btn;
    };

    const saveBtn = createButton(
      `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
      "#10b981",
      "Save a Place",
      this._onSavePlace,
      "save-place-btn hidden md:flex border-b border-gray-200"
    );

    const analyticsBtn = createButton(
      `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`,
      "#2563eb",
      "View Flood Analytics",
      this._onAnalytics,
      "flex"
    );

    this._container.appendChild(saveBtn);
    this._container.appendChild(analyticsBtn);
    
    return this._container;
  }

  onRemove() {
    this._container?.parentNode?.removeChild(this._container);
    this._map = undefined;
  }
}

export default function MapCanvas() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const startMarkerRef = useRef<Marker | null>(null);
  const endMarkerRef = useRef<Marker | null>(null);
  const floodStartMarkerRef = useRef<Marker | null>(null);
  const floodEndMarkerRef = useRef<Marker | null>(null);
  
  // Ref for saved places markers and their react roots for cleanup
  const savedPlacesMarkersRef = useRef<{ marker: Marker, root: Root }[]>([]);

  // Refs for alternative route layers and ETA markers — cleaned up on each route update
  const altMarkerRefs = useRef<maplibregl.Marker[]>([]);
  const altLayerIds = useRef<string[]>([]);
  const altSourceIds = useRef<string[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const [mapStyle, setMapStyle] = useState<any>(
    "https://api.maptiler.com/maps/streets-v2/style.json?key=BHhRqsneD3M4HnOd57WU"
  );
  const [usingFallback, setUsingFallback] = useState(false);

  const { data: activeZonesData } = useQuery({
    queryKey: ["activeZones"],
    queryFn: () => apiClient.get<any[]>("/reports/active-zones"),
    refetchInterval: 15000,
  });

  // Hooks for modular map layers
  useCityBoundaries(mapRef.current, isLoaded);
  useFloodZonesLayer(mapRef.current, isLoaded, activeZonesData);

  // Auto-retry MapTiler when using fallback
  useEffect(() => {
    if (!usingFallback) return;

    const retryInterval = setInterval(async () => {
      try {
        const response = await fetch("https://api.maptiler.com/maps/streets-v2/style.json?key=BHhRqsneD3M4HnOd57WU", { method: 'GET' });
        if (response.ok) {
          // MapTiler is back online!
          setUsingFallback(false);
          setMapStyle("https://api.maptiler.com/maps/streets-v2/style.json?key=BHhRqsneD3M4HnOd57WU");
        }
      } catch (e) {
        // Still blocked/offline, do nothing and let interval continue
      }
    }, 15000); // Check every 15 seconds

    return () => clearInterval(retryInterval);
  }, [usingFallback]);

  const isTouchDevice = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const isTouchDeviceRef = useRef(isTouchDevice);
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const {
    start, end, floodStart, floodEnd,
    allRoutes, selectedRouteIndex,
    setSelectedRouteIndex,
    setPointFromMap, activePoint, setActivePoint, isPickingOnMap,
    floodPreviewGeometry, activePanel, setActivePanel, hasBottomOffset,
    isAnalyticsOpen, setIsAnalyticsOpen, isAnalyticsCollapsed, savedPlaces,
    savePlaceIcon, setIsSavePlacePanelOpen
  } = useMapContext();

  const isDesktopAnalytics = pathname === "/admin/analytics";
  const shouldShowHeatmap = (isAnalyticsOpen && !isAnalyticsCollapsed) || isDesktopAnalytics;

  const { data: heatmapData } = useQuery({
    queryKey: ["analytics", "heatmap"],
    queryFn: () => apiClient.get<any>("/analytics/heatmap"),
    enabled: shouldShowHeatmap,
  });

  useEffect(() => {
    isTouchDeviceRef.current = isTouchDevice;
  }, [isTouchDevice]);

  // Listen for lat/lng in URL to fly to location
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const latStr = searchParams.get("lat");
    const lngStr = searchParams.get("lng");
    const zoomStr = searchParams.get("zoom");
    
    if (latStr && lngStr) {
      const lat = parseFloat(latStr);
      const lng = parseFloat(lngStr);
      const zoom = zoomStr ? parseFloat(zoomStr) : 16;
      
      if (!isNaN(lat) && !isNaN(lng)) {
        mapRef.current.flyTo({
          center: [lng, lat],
          zoom,
          duration: 1000
        });

        // Create a custom pulsing marker element
        const el = document.createElement('div');
        el.className = 'relative flex items-center justify-center';
        el.innerHTML = `
          <div class="absolute w-10 h-10 bg-red-500 rounded-full animate-ping opacity-60"></div>
          <div class="relative flex items-center justify-center w-6 h-6 bg-red-500 rounded-full border-[3px] border-white shadow-lg">
            <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
          </div>
        `;

        // Add a temporary pulsing red pin to highlight the specific location
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([lng, lat])
          .addTo(mapRef.current);

        // Remove the pin after 3 seconds
        setTimeout(() => {
          marker.remove();
        }, 3000);
      }
    }
  }, [searchParams, isLoaded]);

  const setPointFromMapRef = useRef(setPointFromMap);
  setPointFromMapRef.current = setPointFromMap;
  const setSelectedRouteIndexRef = useRef(setSelectedRouteIndex);
  setSelectedRouteIndexRef.current = setSelectedRouteIndex;

  const isPickingRef = useRef(isPickingOnMap);
  useEffect(() => {
    isPickingRef.current = isPickingOnMap;
    if (mapRef.current) {
      mapRef.current.getCanvas().style.cursor = isPickingOnMap ? "crosshair" : "";
    }
  }, [isPickingOnMap, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    startMarkerRef.current?.remove();
    startMarkerRef.current = null;

    if (start) {
      startMarkerRef.current = new maplibregl.Marker({ color: "#16a34a" })
        .setLngLat(start.coords)
        .addTo(map);
    }
  }, [start, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    endMarkerRef.current?.remove();
    endMarkerRef.current = null;

    if (end) {
      endMarkerRef.current = new maplibregl.Marker({ color: "#dc2626" })
        .setLngLat(end.coords)
        .addTo(map);
    }
  }, [end, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    floodStartMarkerRef.current?.remove();
    floodStartMarkerRef.current = null;

    if (floodStart) {
      floodStartMarkerRef.current = new maplibregl.Marker({ color: "#f97316" })
        .setLngLat(floodStart.coords)
        .addTo(map);
    }
  }, [floodStart, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    floodEndMarkerRef.current?.remove();
    floodEndMarkerRef.current = null;

    if (floodEnd) {
      floodEndMarkerRef.current = new maplibregl.Marker({ color: "#991b1b" }) // darker red
        .setLngLat(floodEnd.coords)
        .addTo(map);
    }
  }, [floodEnd, isLoaded]);

  // Render Saved Places
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    // Cleanup existing saved places
    savedPlacesMarkersRef.current.forEach(({ marker, root }) => {
      marker.remove();
      setTimeout(() => root.unmount(), 0);
    });
    savedPlacesMarkersRef.current = [];

    savedPlaces.forEach((place) => {
      const el = document.createElement("div");
      el.className = "cursor-pointer";
      
      const root = createRoot(el);
      const iconText = place.icon || "📍";
      
      root.render(
        <div 
          className="flex flex-col items-center group transform transition-transform hover:scale-110 active:scale-95"
          onClick={(e) => {
            e.stopPropagation();
            // What to do when a saved place is clicked? Maybe pre-fill route or open a small popup
            // For now, let's just log or set as start/end if route panel is open
          }}
        >
          <div className="bg-blue-600 w-8 h-8 flex items-center justify-center rounded-full text-white shadow-lg border-2 border-white relative z-10 text-sm">
            {iconText}
          </div>
          <div className="bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded shadow-sm text-xs font-semibold text-slate-700 mt-1 pointer-events-none whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
            {place.name}
          </div>
        </div>
      );

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([place.longitude, place.latitude])
        .addTo(map);

      savedPlacesMarkersRef.current.push({ marker, root });
    });
  }, [savedPlaces, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;
    if (!map.style) return;

    // ── Cleanup: remove all previous route layers, sources, and ETA markers ──
    altMarkerRefs.current.forEach((m) => m.remove());
    altMarkerRefs.current = [];

    altLayerIds.current.forEach((id) => {
      if (map.getLayer(id)) map.removeLayer(id);
    });
    altSourceIds.current.forEach((id) => {
      if (map.getSource(id)) map.removeSource(id);
    });
    altLayerIds.current = [];
    altSourceIds.current = [];

    if (map.getLayer(ROUTE_LAYER_ID)) map.removeLayer(ROUTE_LAYER_ID);
    if (map.getSource(ROUTE_SOURCE_ID)) map.removeSource(ROUTE_SOURCE_ID);

    if (!allRoutes || allRoutes.length === 0) return;

    // ── 1. Render alternative (gray) routes with clickable layers + ETA banners ──
    allRoutes.forEach((route) => {
      if (route.index === selectedRouteIndex) return; // selected route rendered separately below

      const sourceId = `route-alt-source-${route.index}`;
      const layerId = `route-alt-layer-${route.index}`;

      map.addSource(sourceId, {
        type: "geojson",
        data: { type: "Feature", properties: {}, geometry: route.geometry },
      });
      map.addLayer({
        id: layerId,
        type: "line",
        source: sourceId,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: {
          "line-color": "#4b5563", // Darker gray for better visibility
          "line-width": 6,
          "line-opacity": 0.85,
        },
      });

      altSourceIds.current.push(sourceId);
      altLayerIds.current.push(layerId);

      // Click handler: selecting this route makes it the active one
      const clickHandler = () => setSelectedRouteIndexRef.current(route.index);
      map.on("click", layerId, clickHandler);
      map.on("mouseenter", layerId, () => {
        map.getCanvas().style.cursor = "pointer";
        if (map.getLayer(layerId)) map.setPaintProperty(layerId, "line-color", "#1f2937"); // Almost black on hover
      });
      map.on("mouseleave", layerId, () => {
        map.getCanvas().style.cursor = isPickingRef.current ? "crosshair" : "";
        if (map.getLayer(layerId)) map.setPaintProperty(layerId, "line-color", "#4b5563");
      });

      // ── ETA Banner HTML Marker at route midpoint ──
      const coords = route.geometry.coordinates;
      const midCoord = coords[Math.floor(coords.length / 2)];
      const mins = Math.round(route.duration / 60);
      const etaText = mins < 60 ? `${mins} min` : `${Math.floor(mins / 60)}h ${mins % 60}m`;
      const distText = `${(route.distance / 1000).toFixed(1)} km`;

      const el = document.createElement("div");
      el.style.cssText = [
        "background: white",
        "border: 1.5px solid #e5e7eb",
        "border-radius: 8px",
        "padding: 5px 10px 3px",
        "box-shadow: 0 2px 8px rgba(0,0,0,0.13)",
        "cursor: pointer",
        "font-family: system-ui,-apple-system,sans-serif",
        "display: flex",
        "flex-direction: column",
        "align-items: center",
        "min-width: 72px",
        "transition: box-shadow 0.15s, border-color 0.15s",
      ].join(";");

      const topRow = document.createElement("div");
      topRow.style.cssText = "display:flex;align-items:center;gap:4px;";

      if (route.is_truncated) {
        const warn = document.createElement("span");
        warn.textContent = "⚠";
        warn.style.cssText = "font-size:11px;color:#d97706;";
        topRow.appendChild(warn);
      }

      const etaEl = document.createElement("span");
      etaEl.textContent = etaText;
      etaEl.style.cssText = "font-size:13px;font-weight:700;color:#111827;";
      topRow.appendChild(etaEl);

      const distEl = document.createElement("span");
      distEl.textContent = distText;
      distEl.style.cssText = "font-size:10px;color:#6b7280;margin-top:1px;";

      // Small downward-pointing triangle (caret) grounding the banner to the route line
      const caret = document.createElement("div");
      caret.style.cssText = [
        "width:0",
        "height:0",
        "border-left:6px solid transparent",
        "border-right:6px solid transparent",
        "border-top:7px solid #e5e7eb",
        "margin:3px auto 0",
        "position:relative",
      ].join(";");
      const caretInner = document.createElement("div");
      caretInner.style.cssText = [
        "width:0",
        "height:0",
        "border-left:5px solid transparent",
        "border-right:5px solid transparent",
        "border-top:6px solid white",
        "position:absolute",
        "top:-8px",
        "left:-5px",
      ].join(";");
      caret.appendChild(caretInner);

      el.appendChild(topRow);
      el.appendChild(distEl);
      el.appendChild(caret);

      el.addEventListener("click", clickHandler);
      el.addEventListener("mouseenter", () => {
        el.style.boxShadow = "0 4px 14px rgba(0,0,0,0.18)";
        el.style.borderColor = "#9ca3af";
      });
      el.addEventListener("mouseleave", () => {
        el.style.boxShadow = "0 2px 8px rgba(0,0,0,0.13)";
        el.style.borderColor = "#e5e7eb";
      });

      const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
        .setLngLat([midCoord[0], midCoord[1]])
        .addTo(map);

      altMarkerRefs.current.push(marker);
    });

    // ── 2. Render the selected route with the existing blue/flood gradient ──
    const activeRoute = allRoutes[selectedRouteIndex];
    if (!activeRoute) return;

    const routeGeometryActive = activeRoute.geometry;

    // Default: solid blue gradient for clear routes
    let gradientExpression: any = [
      "interpolate",
      ["linear"],
      ["line-progress"],
      0.0, "#2563eb",
      1.0, "#2563eb",
    ];

    const coords = routeGeometryActive.coordinates;
    if (coords && coords.length > 0) {
      const dists = [0];
      let totalDist = 0;
      for (let i = 1; i < coords.length; i++) {
        const c1 = coords[i - 1];
        const c2 = coords[i];
        const dx = c2[0] - c1[0];
        const dy = c2[1] - c1[1];
        totalDist += Math.sqrt(dx * dx + dy * dy) * 111000;
        dists.push(totalDist);
      }

      let firstIntersectIdx = -1;
      let lastIntersectIdx = -1;
      for (let i = 0; i < coords.length; i++) {
        const pt = coords[i] as [number, number];
        const isFlooded = (activeZonesData || []).some((zone) =>
          isPointInPolygon(pt, zone.geometry)
        );
        if (isFlooded) {
          if (firstIntersectIdx === -1) firstIntersectIdx = i;
          lastIntersectIdx = i;
        }
      }

      if (firstIntersectIdx !== -1 && totalDist > 0) {
        const D_start = dists[firstIntersectIdx];
        const D_end = dists[lastIntersectIdx];
        const P_start_flood = D_start / totalDist;
        const P_end_flood = D_end / totalDist;
        const p_blue_approach = Math.max(0.0, D_start - 80) / totalDist;
        const p_yellow_approach = Math.max(0.0, D_start - 40) / totalDist;
        const p_orange_approach = Math.max(0.0, D_start - 15) / totalDist;

        const rawStops = [
          { p: 0.0, c: "#2563eb" },
          { p: p_blue_approach, c: "#2563eb" },
          { p: p_yellow_approach, c: "#eab308" },
          { p: p_orange_approach, c: "#f97316" },
          { p: P_start_flood, c: "#ef4444" },
          { p: P_end_flood, c: "#ef4444" },
        ];

        if (P_end_flood < 1.0) {
          rawStops.push({ p: Math.min(totalDist, D_end + 15) / totalDist, c: "#f97316" });
          rawStops.push({ p: Math.min(totalDist, D_end + 40) / totalDist, c: "#eab308" });
          rawStops.push({ p: Math.min(totalDist, D_end + 80) / totalDist, c: "#2563eb" });
          rawStops.push({ p: 1.0, c: "#2563eb" });
        }

        rawStops.sort((a, b) => a.p - b.p);
        const uniqueStops: [number, string][] = [];
        rawStops.forEach((stop) => {
          if (uniqueStops.length === 0) {
            uniqueStops.push([stop.p, stop.c]);
          } else {
            const last = uniqueStops[uniqueStops.length - 1];
            if (last[0] === stop.p) last[1] = stop.c;
            else uniqueStops.push([stop.p, stop.c]);
          }
        });

        gradientExpression = ["interpolate", ["linear"], ["line-progress"]];
        uniqueStops.forEach(([p, c]) => {
          gradientExpression.push(p);
          gradientExpression.push(c);
        });
      }
    }

    map.addSource(ROUTE_SOURCE_ID, {
      type: "geojson",
      lineMetrics: true,
      data: { type: "Feature", properties: {}, geometry: routeGeometryActive },
    });
    map.addLayer({
      id: ROUTE_LAYER_ID,
      type: "line",
      source: ROUTE_SOURCE_ID,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-gradient": gradientExpression,
        "line-width": 6,
        "line-opacity": 0.9,
      },
    });

  }, [allRoutes, selectedRouteIndex, activeZonesData, isLoaded]);


  // Active flood avoidance zones are handled by useFloodZonesLayer hook above

  useEffect(() => {
    if (!isLoaded || !mapRef.current || !start) return;
    const map = mapRef.current;
    map.flyTo({
      center: start.coords,
      zoom: Math.max(map.getZoom(), 14),
      bearing: map.getBearing(),
      pitch: map.getPitch(),
      duration: 600,
    });
  }, [start?.coords[0], start?.coords[1], isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current || !end) return;
    const map = mapRef.current;
    map.flyTo({
      center: end.coords,
      zoom: Math.max(map.getZoom(), 14),
      bearing: map.getBearing(),
      pitch: map.getPitch(),
      duration: 600,
    });
  }, [end?.coords[0], end?.coords[1], isLoaded]);

  // Zoom in slightly when picking on map mode is activated
  useEffect(() => {
    if (!isLoaded || !mapRef.current || !isPickingOnMap) return;
    const map = mapRef.current;
    map.flyTo({
      zoom: map.getZoom() + 1,
      bearing: map.getBearing(),
      pitch: map.getPitch(),
      duration: 400,
    });

    // Immediately dispatch center so it's available for selection without panning
    const center = map.getCenter();
    window.dispatchEvent(new CustomEvent("map-center-changed", { detail: [center.lng, center.lat] }));
  }, [isPickingOnMap, isLoaded]);

  // Draw the preview of the flood report road segment (only when road-aligned geometry is ready)
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;
    if (!map.style) return;

    // Remove existing preview source/layers if they exist
    if (map.getLayer("flood-preview-layer")) map.removeLayer("flood-preview-layer");
    if (map.getSource("flood-preview-source")) map.removeSource("flood-preview-source");

    if (!floodPreviewGeometry) return;

    map.addSource("flood-preview-source", {
      type: "geojson",
      data: {
        type: "Feature",
        properties: {},
        geometry: floodPreviewGeometry,
      },
    });

    map.addLayer({
      id: "flood-preview-layer",
      type: "line",
      source: "flood-preview-source",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": "#f97316", // Orange preview color matching markers
        "line-width": 6,
        "line-dasharray": [2, 2], // Dashed line for visual distinction
        "line-opacity": 0.85,
      },
    });
  }, [floodPreviewGeometry, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;
    if (!map.style) return;
    
    if (map.getLayer("heatmap-layer")) map.removeLayer("heatmap-layer");
    if (map.getSource("heatmap-source")) map.removeSource("heatmap-source");

    const showAnalytics = (isAnalyticsOpen && !isAnalyticsCollapsed) || pathname === "/admin/analytics";
    if (!showAnalytics || !heatmapData || !heatmapData.features || heatmapData.features.length === 0) return;

    map.addSource("heatmap-source", {
      type: "geojson",
      data: heatmapData
    });

    map.addLayer({
      id: "heatmap-layer",
      type: "heatmap",
      source: "heatmap-source",
      maxzoom: 15,
      paint: {
        "heatmap-weight": ["get", "weight"],
        "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 1, 15, 3],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0, "rgba(0, 0, 255, 0)",
          0.2, "royalblue",
          0.4, "cyan",
          0.6, "lime",
          0.8, "yellow",
          1, "red"
        ],
        "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 2, 15, 20],
        "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 15, 0]
      }
    });
  }, [heatmapData, isLoaded, pathname, isAnalyticsOpen, isAnalyticsCollapsed]);

  return (
    <BaseMap
      onMapInit={(map) => {
        mapRef.current = map;
        map.addControl(
          new ActionGroupControl(
            () => setIsSavePlacePanelOpen(true),
            () => setIsAnalyticsOpen(true)
          ),
          "bottom-right"
        );
        map.on("click", (event: MapMouseEvent) => {
          setPointFromMapRef.current([event.lngLat.lng, event.lngLat.lat]);
        });
        map.on("moveend", () => {
          const center = map.getCenter();
          window.dispatchEvent(new CustomEvent("map-center-changed", { detail: [center.lng, center.lat] }));
        });
      }}
      onMapLoad={() => {
        setIsLoaded(true);
      }}
      className={`relative w-full h-full ${hasBottomOffset ? "flood-panel-open" : ""} ${pathname.includes('analytics') ? "hide-save-place" : ""}`}
    >

      {usingFallback && (
        <div className="absolute top-20 left-4 right-4 md:left-1/2 md:right-auto md:-translate-x-1/2 z-30 bg-amber-500/95 text-white text-xs md:text-sm px-4 py-2.5 rounded-xl shadow-lg flex items-center gap-2 backdrop-blur-sm animate-pulse max-w-md pointer-events-auto border border-amber-400/20 font-medium">
          <span>⚠️ MapTiler tiles blocked or offline. Switched to OpenStreetMap fallback. Retrying automatically...</span>
        </div>
      )}

      {/* Center Pin Overlay (for touch device panning) */}
      {isTouchDevice && isPickingOnMap && activePoint && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-full mt-[1.5px] pointer-events-none z-10 drop-shadow-md">
          {activePoint === "save_place_location" && savePlaceIcon ? (
            <div className="flex items-center justify-center animate-bounce text-4xl drop-shadow-md pb-2">
              {savePlaceIcon}
            </div>
          ) : (
            <svg width="32" height="32" viewBox="0 0 24 24" className="animate-bounce">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" 
                fill={activePoint === "start" ? "#16a34a" : activePoint === "flood_start" ? "#f97316" : activePoint === "flood_end" ? "#991b1b" : "#dc2626"} 
                stroke={activePoint === "start" ? "#16a34a" : activePoint === "flood_start" ? "#f97316" : activePoint === "flood_end" ? "#991b1b" : "#dc2626"} 
                strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="12" cy="10" r="3" fill="white" />
            </svg>
          )}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-1 bg-black/25 rounded-full blur-[1px]"></div>
        </div>
      )}

      {/* Force map controls above the navigation bar */}
      <style>{`
        .mapboxgl-ctrl-bottom-right,
        .maplibregl-ctrl-bottom-right {
          bottom: calc(64px + env(safe-area-inset-bottom) + 16px) !important;
          transition: bottom 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .flood-panel-open .mapboxgl-ctrl-bottom-right,
        .flood-panel-open .maplibregl-ctrl-bottom-right {
          bottom: calc(64px + env(safe-area-inset-bottom) + 80px) !important;
        }
        @media (min-width: 641px) {
          .mapboxgl-ctrl-bottom-right,
          .maplibregl-ctrl-bottom-right {
            bottom: 16px !important;
          }
          .flood-panel-open .mapboxgl-ctrl-bottom-right,
          .flood-panel-open .maplibregl-ctrl-bottom-right {
            bottom: 16px !important;
          }
        }

        /* Redesign MapLibre Native Controls (Zoom, Compass, Geolocate) */
        .maplibregl-ctrl-group {
          background-color: white !important;
          border-radius: 12px !important;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
          overflow: hidden !important;
          display: flex;
          flex-direction: column;
          margin-bottom: 12px !important;
        }
        .maplibregl-ctrl-group:not(:empty) {
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        }
        .maplibregl-ctrl-group > button {
          width: 48px !important;
          height: 48px !important;
          background-color: transparent !important;
          border: none !important;
          border-radius: 0 !important;
          box-shadow: none !important;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          margin: 0 !important;
        }
        .maplibregl-ctrl-group > button + button {
          border-top: 1px solid #e5e7eb !important;
        }
        .maplibregl-ctrl-group > button:hover {
          background-color: #f8fafc !important;
        }
        .maplibregl-ctrl-group > button:active {
          background-color: #f1f5f9 !important;
        }
        .maplibregl-ctrl-icon {
          width: 22px !important;
          height: 22px !important;
          opacity: 0.8;
        }
        .hide-save-place .save-place-btn {
          display: none !important;
        }
      `}</style>
    </BaseMap>
  );
}
