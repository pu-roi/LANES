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
import BaseMap from "@/shared/ui/map/BaseMap";
import { getFloodsOffline } from "@/lib/offline/storage";
import { useCityBoundaries } from "./hooks/useCityBoundaries";
import { useFloodZonesLayer } from "./hooks/useFloodZonesLayer";
import { flyToCoordinates } from "./mapGeoUtils";

let hasZoomedToPasigForAnalytics = false;
let hasZoomedToPasigForMap = false;

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
  const [mapInstance, setMapInstance] = useState<Map | null>(null);
  const mapRef = useRef<Map | null>(null);
  const startMarkerRef = useRef<Marker | null>(null);
  const endMarkerRef = useRef<Marker | null>(null);
  const floodStartMarkerRef = useRef<Marker | null>(null);
  const floodEndMarkerRef = useRef<Marker | null>(null);
  const draftPlaceMarkerRef = useRef<Marker | null>(null);
  
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

  const { data: activeZonesData } = useQuery({
    queryKey: ["activeZones"],
    queryFn: async () => {
      try {
        return await apiClient.get<any[]>("/reports/active-zones");
      } catch (err) {
        console.warn("API unreachable, falling back to offline flood cache.");
        return await getFloodsOffline();
      }
    },
    refetchInterval: 15000,
  });

  const isTouchDevice = useMediaQuery("(max-width: 640px), (pointer: coarse)");

  // Hooks for modular map layers (reactive on mapInstance state!)
  useCityBoundaries(mapInstance, isLoaded);
  useFloodZonesLayer(mapInstance, isLoaded, activeZonesData, isTouchDevice);

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
    savePlaceIcon, draftSavePlaceCoords, setIsSavePlacePanelOpen,
    floodIsBidirectional, floodOppositeGeometry,
    draftReports
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

  // Zoom to Pasig City bounds once when visiting analytics or map
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    
    // Ensure map is resized to the active route's container dimensions
    mapRef.current.resize();

    // If navigated with specific coordinates, skip default city bounds zoom
    const hasTargetCoords = !!(searchParams.get("lat") && searchParams.get("lng"));
    if (hasTargetCoords) {
      hasZoomedToPasigForMap = true;
      return;
    }

    const savedViewport = typeof window !== "undefined" ? sessionStorage.getItem("lanes_map_viewport") : null;
    const isAnalyticsPage = pathname.includes("analytics");
    const isMapPage = pathname === "/map";
    
    let shouldZoom = false;
    
    if (!savedViewport) {
      if (isAnalyticsPage && !hasZoomedToPasigForAnalytics) {
        hasZoomedToPasigForAnalytics = true;
        shouldZoom = true;
      } else if (isMapPage && !hasZoomedToPasigForMap) {
        hasZoomedToPasigForMap = true;
        shouldZoom = true;
      }
    } else {
      // If we have a saved viewport, never auto-zoom on load
      hasZoomedToPasigForAnalytics = true;
      hasZoomedToPasigForMap = true;
    }

    if (shouldZoom) {
      mapRef.current.fitBounds([
        [121.0544, 14.5422], // Southwest (Approx Pasig City SW)
        [121.1077, 14.6186]  // Northeast (Approx Pasig City NE)
      ], { padding: 120, duration: 1000 });
    }
  }, [pathname, isLoaded, searchParams]);

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
        // Ensure map is resized to current layout
        mapRef.current.resize();

        // Delay flyTo slightly so layout reflow completes and MapLibre calculates the true visible viewport center
        const timer = setTimeout(() => {
          if (!mapRef.current) return;
          mapRef.current.resize();

          flyToCoordinates(mapRef.current, [lng, lat], {
            zoom,
            pitch: mapRef.current.getPitch(),
            bearing: mapRef.current.getBearing(),
            duration: 1500
          });

          // Create a pulsing marker element using inline styles (no Tailwind dependency)
          const el = document.createElement('div');
          el.style.cssText = 'position:relative;display:flex;align-items:center;justify-content:center;width:40px;height:40px;pointer-events:none;';

          // Pulsing outer ring
          const ring = document.createElement('div');
          ring.style.cssText = `
            position:absolute;
            width:40px;height:40px;
            background:rgba(239,68,68,0.5);
            border-radius:50%;
            animation:pulse-ring 1.2s ease-out infinite;
          `;

          // Inner solid dot
          const dot = document.createElement('div');
          dot.style.cssText = `
            position:relative;
            width:18px;height:18px;
            background:#ef4444;
            border-radius:50%;
            border:3px solid white;
            box-shadow:0 2px 8px rgba(0,0,0,0.4);
            display:flex;align-items:center;justify-content:center;
            z-index:1;
          `;
          const center = document.createElement('div');
          center.style.cssText = 'width:5px;height:5px;background:white;border-radius:50%;';
          dot.appendChild(center);

          el.appendChild(ring);
          el.appendChild(dot);

          // Inject keyframes once
          if (!document.getElementById('pulse-ring-style')) {
            const style = document.createElement('style');
            style.id = 'pulse-ring-style';
            style.textContent = `
              @keyframes pulse-ring {
                0%   { transform: scale(0.6); opacity: 0.8; }
                80%  { transform: scale(1.8); opacity: 0; }
                100% { transform: scale(1.8); opacity: 0; }
              }
            `;
            document.head.appendChild(style);
          }

          // Add a temporary pulsing red pin to highlight the specific location
          const marker = new maplibregl.Marker({ element: el, anchor: 'center' })
            .setLngLat([lng, lat])
            .addTo(mapRef.current);

          // Remove the pin after 3 seconds
          setTimeout(() => {
            marker.remove();
          }, 3000);
        }, 50);

        // Clean up URL query parameters so on page refresh it doesn't re-trigger
        try {
          const url = new URL(window.location.href);
          url.searchParams.delete("lat");
          url.searchParams.delete("lng");
          url.searchParams.delete("zoom");
          window.history.replaceState({}, "", url.pathname + (url.search ? url.search : ""));
        } catch (e) {}

        return () => clearTimeout(timer);
      }
    }
  }, [searchParams, isLoaded]);

  const setPointFromMapRef = useRef(setPointFromMap);
  setPointFromMapRef.current = setPointFromMap;
  const setSelectedRouteIndexRef = useRef(setSelectedRouteIndex);
  setSelectedRouteIndexRef.current = setSelectedRouteIndex;

  const isPickingRef = useRef(isPickingOnMap);
  isPickingRef.current = isPickingOnMap;
  useEffect(() => {
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

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    draftPlaceMarkerRef.current?.remove();
    draftPlaceMarkerRef.current = null;

    if (draftSavePlaceCoords?.coords) {
      const el = document.createElement("div");
      el.className = "text-2xl select-none pointer-events-none drop-shadow-md flex items-center justify-center";
      el.textContent = savePlaceIcon || "🏠";

      draftPlaceMarkerRef.current = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat(draftSavePlaceCoords.coords)
        .addTo(map);
    }
  }, [draftSavePlaceCoords, savePlaceIcon, isLoaded]);

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
          className="flex flex-col items-center group select-none cursor-pointer"
          onClick={(e) => {
            e.stopPropagation();
            if (mapRef.current) {
              flyToCoordinates(mapRef.current, [place.longitude, place.latitude], {
                zoom: 16,
                pitch: mapRef.current.getPitch(),
                duration: 1500,
              });
            }
          }}
        >
          <div className="text-2xl drop-shadow-md select-none flex items-center justify-center">
            {iconText}
          </div>
          <div className="bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded shadow-sm text-xs font-semibold text-slate-700 mt-0.5 pointer-events-none whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity select-none">
            {place.name}
          </div>
        </div>
      );

      const marker = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat([place.longitude, place.latitude])
        .addTo(map);

      savedPlacesMarkersRef.current.push({ marker, root });
    });
  }, [savedPlaces, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    const cleanupRoutes = () => {
      altMarkerRefs.current.forEach((m) => {
        try { m.remove(); } catch {}
      });
      altMarkerRefs.current = [];

      for (let i = 0; i < 10; i++) {
        const lId = `route-alt-layer-${i}`;
        const sId = `route-alt-source-${i}`;
        if (map.getLayer(lId)) {
          try { map.removeLayer(lId); } catch {}
        }
        if (map.getSource(sId)) {
          try { map.removeSource(sId); } catch {}
        }
      }
      altLayerIds.current = [];
      altSourceIds.current = [];

      if (map.getLayer(ROUTE_LAYER_ID)) {
        try { map.removeLayer(ROUTE_LAYER_ID); } catch {}
      }
      if (map.getSource(ROUTE_SOURCE_ID)) {
        try { map.removeSource(ROUTE_SOURCE_ID); } catch {}
      }
    };

    const renderRoutes = () => {
      if (!map.getStyle()) return;

      cleanupRoutes();

      if (!allRoutes || allRoutes.length === 0) return;

      // ── 1. Render alternative (gray) routes with clickable layers + ETA banners ──
      allRoutes.forEach((route) => {
        if (route.index === selectedRouteIndex) return; // selected route rendered separately below

        const sourceId = `route-alt-source-${route.index}`;
        const layerId = `route-alt-layer-${route.index}`;

        try {
          if (!map.getSource(sourceId)) {
            map.addSource(sourceId, {
              type: "geojson",
              data: { type: "Feature", properties: {}, geometry: route.geometry },
            });
          }
          if (!map.getLayer(layerId)) {
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
          }

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
          if (coords && coords.length > 0) {
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
          }
        } catch (e) {
          console.error(`Failed to add alternative route ${route.index}:`, e);
        }
      });

      // ── 2. Render the selected route with blue/flood gradient ──
      const activeRoute = allRoutes[selectedRouteIndex];
      if (!activeRoute) return;

      const routeGeometryActive = activeRoute.geometry;
      const coords = routeGeometryActive.coordinates;

      let hasFloodOverlap = false;
      let gradientExpression: any = [
        "interpolate",
        ["linear"],
        ["line-progress"],
        0.0, "#2563eb",
        1.0, "#2563eb",
      ];

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

          if (uniqueStops.length >= 2) {
            hasFloodOverlap = true;
            gradientExpression = ["interpolate", ["linear"], ["line-progress"]];
            uniqueStops.forEach(([p, c]) => {
              gradientExpression.push(p);
              gradientExpression.push(c);
            });
          }
        }

        // Auto-fit camera bounds to bring the complete route into view
        try {
          let minLng = coords[0][0];
          let maxLng = coords[0][0];
          let minLat = coords[0][1];
          let maxLat = coords[0][1];
          for (const c of coords) {
            if (c[0] < minLng) minLng = c[0];
            if (c[0] > maxLng) maxLng = c[0];
            if (c[1] < minLat) minLat = c[1];
            if (c[1] > maxLat) maxLat = c[1];
          }
          if (minLng !== maxLng || minLat !== maxLat) {
            const isMobile = window.innerWidth < 768;
            map.fitBounds(
              [[minLng, minLat], [maxLng, maxLat]],
              {
                padding: isMobile
                  ? { top: 120, bottom: 200, left: 30, right: 30 }
                  : { top: 80, bottom: 80, left: 380, right: 80 },
                duration: 800,
                maxZoom: 16.5,
              }
            );
          }
        } catch (e) {
          console.warn("Could not fitBounds to route:", e);
        }
      }

      try {
        if (!map.getSource(ROUTE_SOURCE_ID)) {
          map.addSource(ROUTE_SOURCE_ID, {
            type: "geojson",
            lineMetrics: true,
            data: { type: "Feature", properties: {}, geometry: routeGeometryActive },
          });
        }

        if (!map.getLayer(ROUTE_LAYER_ID)) {
          const paintConfig: any = {
            "line-color": "#2563eb",
            "line-width": 6,
            "line-opacity": 0.9,
          };
          if (hasFloodOverlap) {
            paintConfig["line-gradient"] = gradientExpression;
          }

          map.addLayer({
            id: ROUTE_LAYER_ID,
            type: "line",
            source: ROUTE_SOURCE_ID,
            layout: { "line-join": "round", "line-cap": "round" },
            paint: paintConfig,
          });
        }
      } catch (e) {
        console.error("Failed to render active route layer:", e);
      }
    };

    if (map.getStyle()) {
      renderRoutes();
    }

    const handleStyleData = () => {
      renderRoutes();
    };

    map.on("style.load", handleStyleData);

    return () => {
      map.off("style.load", handleStyleData);
      cleanupRoutes();
    };
  }, [allRoutes, selectedRouteIndex, activeZonesData, isLoaded]);

  // ── Step highlight: driven by route-step-hover / route-step-click / route-step-clear events ──
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;

    const HIGHLIGHT_SOURCE = "step-highlight-source";
    const HIGHLIGHT_LAYER  = "step-highlight-layer";
    const HIGHLIGHT_GLOW   = "step-highlight-glow";

    const clearHighlight = () => {
      if (!map.getStyle()) return;
      if (map.getLayer(HIGHLIGHT_LAYER)) map.removeLayer(HIGHLIGHT_LAYER);
      if (map.getLayer(HIGHLIGHT_GLOW))  map.removeLayer(HIGHLIGHT_GLOW);
      if (map.getSource(HIGHLIGHT_SOURCE)) map.removeSource(HIGHLIGHT_SOURCE);
    };

    const drawHighlight = (segment: [number, number][]) => {
      if (!map.getStyle() || segment.length < 2) return;
      clearHighlight();
      map.addSource(HIGHLIGHT_SOURCE, {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: segment },
        },
      });
      // Outer glow
      map.addLayer({
        id: HIGHLIGHT_GLOW,
        type: "line",
        source: HIGHLIGHT_SOURCE,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#38bdf8", "line-width": 14, "line-opacity": 0.25, "line-blur": 4 },
      });
      // Inner highlight line
      map.addLayer({
        id: HIGHLIGHT_LAYER,
        type: "line",
        source: HIGHLIGHT_SOURCE,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": "#0ea5e9", "line-width": 5, "line-opacity": 0.95 },
      });
    };

    const onHover = (e: Event) => {
      const { segment } = (e as CustomEvent).detail;
      drawHighlight(segment);
    };

    const onClick = (e: Event) => {
      const { segment } = (e as CustomEvent).detail;
      drawHighlight(segment);
      // Fly to segment midpoint
      const mid = segment[Math.floor(segment.length / 2)];
      if (mid) {
        map.flyTo({ center: [mid[0], mid[1]], zoom: Math.max(map.getZoom(), 16), duration: 500 });
      }
    };

    const onClear = () => clearHighlight();

    const onFlyToLocation = (e: Event) => {
      const { latitude, longitude, zoom, duration, pitch } = (e as CustomEvent).detail || {};
      if (!map || latitude == null || longitude == null) return;
      flyToCoordinates(map, [longitude, latitude], {
        zoom: zoom ?? 16,
        pitch: pitch ?? map.getPitch(),
        duration: duration ?? 1500,
      });

      // Temporary pulsing red circle indicator
      const el = document.createElement("div");
      el.className = "relative flex items-center justify-center pointer-events-none";
      el.innerHTML = `
        <div class="absolute w-10 h-10 bg-red-500 rounded-full animate-ping opacity-60"></div>
        <div class="relative flex items-center justify-center w-6 h-6 bg-red-500 rounded-full border-[3px] border-white shadow-lg">
          <div class="w-1.5 h-1.5 bg-white rounded-full"></div>
        </div>
      `;
      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([longitude, latitude])
        .addTo(map);

      setTimeout(() => {
        marker.remove();
      }, 3000);
    };

    window.addEventListener("route-step-hover", onHover);
    window.addEventListener("route-step-click", onClick);
    window.addEventListener("route-step-clear", onClear);
    window.addEventListener("fly-to-location", onFlyToLocation);
    return () => {
      window.removeEventListener("route-step-hover", onHover);
      window.removeEventListener("route-step-click", onClick);
      window.removeEventListener("route-step-clear", onClear);
      window.removeEventListener("fly-to-location", onFlyToLocation);
      clearHighlight();
    };
  }, [isLoaded]);

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
    if (!map.getStyle()) return;

    // Remove existing preview source/layers if they exist
    if (map.getLayer("flood-preview-layer")) map.removeLayer("flood-preview-layer");
    if (map.getLayer("flood-preview-layer-opposite")) map.removeLayer("flood-preview-layer-opposite");
    if (map.getSource("flood-preview-source")) map.removeSource("flood-preview-source");
    if (map.getSource("flood-preview-source-opposite")) map.removeSource("flood-preview-source-opposite");

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

    map.addSource("flood-preview-source", {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features,
      },
    });

    map.addLayer({
      id: "flood-preview-layer",
      type: "line",
      source: "flood-preview-source",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": [
          "case",
          ["==", ["get", "is_opposite"], true],
          "#fb923c", // Distinct orange tint for opposite carriageway
          "#f97316", // Primary road segment
        ],
        "line-width": 6,
        "line-dasharray": [2, 2],
        "line-opacity": 0.85,
      },
    });

    return () => {
      try {
        if (map.getLayer("flood-preview-layer")) map.removeLayer("flood-preview-layer");
        if (map.getLayer("flood-preview-layer-opposite")) map.removeLayer("flood-preview-layer-opposite");
        if (map.getSource("flood-preview-source")) map.removeSource("flood-preview-source");
        if (map.getSource("flood-preview-source-opposite")) map.removeSource("flood-preview-source-opposite");
      } catch {}
    };
  }, [floodPreviewGeometry, floodOppositeGeometry, floodIsBidirectional, isLoaded]);

  // Render drafted reports (Cart)
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;
    if (!map.getStyle()) return;

    if (map.getLayer("draft-reports-layer")) map.removeLayer("draft-reports-layer");
    if (map.getSource("draft-reports-source")) map.removeSource("draft-reports-source");

    if (!draftReports || draftReports.length === 0) return;

    const features: any[] = [];
    draftReports.forEach((draft) => {
      features.push({
        type: "Feature",
        properties: { severity: draft.severity },
        geometry: draft.geometry,
      });
      if (draft.isBidirectional && draft.oppositeGeometry) {
        features.push({
          type: "Feature",
          properties: { severity: draft.severity },
          geometry: draft.oppositeGeometry,
        });
      }
    });

    map.addSource("draft-reports-source", {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features,
      },
    });

    map.addLayer({
      id: "draft-reports-layer",
      type: "line",
      source: "draft-reports-source",
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": "#8b5cf6", // Purple to distinguish drafts
        "line-width": 6,
        "line-dasharray": [2, 2],
        "line-opacity": 0.8,
      },
    });

    return () => {
      try {
        if (map.getLayer("draft-reports-layer")) map.removeLayer("draft-reports-layer");
        if (map.getSource("draft-reports-source")) map.removeSource("draft-reports-source");
      } catch {}
    };
  }, [draftReports, isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    const map = mapRef.current;
    if (!map.getStyle()) return;
    
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
      actionControls={(map) => {
        map.addControl(
          new ActionGroupControl(
            () => setIsSavePlacePanelOpen(true),
            () => setIsAnalyticsOpen(true)
          ),
          "bottom-right"
        );
      }}
      onMapInit={(map) => {
        setMapInstance(map);
        mapRef.current = map;
        map.on("click", (event: MapMouseEvent) => {
          if (!isPickingRef.current) return;
          setPointFromMapRef.current([event.lngLat.lng, event.lngLat.lat]);
        });
        map.on("moveend", () => {
          const center = map.getCenter();
          window.dispatchEvent(new CustomEvent("map-center-changed", { detail: [center.lng, center.lat] }));
        });
      }}
      onMapLoad={(map) => {
        setMapInstance(map);
        setIsLoaded(true);
      }}
      className={`relative h-full ${pathname === "/map" ? "w-full md:ml-[340px] md:w-[calc(100%-340px)]" : "w-full"} ${hasBottomOffset ? "flood-panel-open" : ""} ${pathname.includes('analytics') ? "hide-save-place" : ""}`}
    >

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
          cursor: pointer !important;
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
