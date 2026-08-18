"use client";

import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import type { Map } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Loader2 } from "lucide-react";
import { registerOfflineProtocol } from "@/lib/offline/map-pmtiles";
import { preloadOfflineEngine } from "@/features/routing/routingApi";

registerOfflineProtocol();

export class TopViewControlV3 {
  private _map: maplibregl.Map | undefined;
  private _container: HTMLDivElement | undefined;
  private _button: HTMLButtonElement | undefined;

  onAdd(map: maplibregl.Map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";

    this._button = document.createElement("button");
    this._button.type = "button";
    this._button.title = "Reset to Top View";
    this._button.className = "maplibregl-ctrl-icon";

    this._button.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin: auto;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>`;

    this._button.onclick = () => {
      if (this._map) {
        this._map.easeTo({
          pitch: 0,
          bearing: this._map.getBearing(),
          duration: 600,
        });
      }
    };

    this._container.appendChild(this._button);
    return this._container;
  }

  onRemove() {
    this._button?.parentNode?.removeChild(this._button);
    this._container?.parentNode?.removeChild(this._container);
    this._map = undefined;
  }
}

export class ZoomLevelControl {
  private _map: maplibregl.Map | undefined;
  private _container: HTMLDivElement | undefined;
  private _textSpan: HTMLSpanElement | undefined;

  onAdd(map: maplibregl.Map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this._container.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 26px;
      font-size: 11px;
      font-weight: 700;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      color: #334155;
      background: #ffffff;
      user-select: none;
      cursor: default;
      box-sizing: border-box;
      border-radius: 8px;
    `;

    this._textSpan = document.createElement("span");
    this._textSpan.style.cssText = `
      letter-spacing: -0.5px;
    `;
    this._updateText();
    this._container.appendChild(this._textSpan);

    this._map.on("zoom", this._onZoom);
    return this._container;
  }

  private _onZoom = () => {
    this._updateText();
  };

  private _updateText() {
    if (this._map && this._textSpan) {
      const z = this._map.getZoom();
      this._textSpan.textContent = `Z: ${z.toFixed(1)}`;
      this._textSpan.title = z > 14 ? "Street Level (Lines/Polygons Active)" : "City View (Circle Pins Active)";
    }
  }

  onRemove() {
    this._map?.off("zoom", this._onZoom);
    this._container?.parentNode?.removeChild(this._container);
    this._map = undefined;
  }
}

const DEFAULT_CENTER: [number, number] = [121.0772, 14.562];
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
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [
    {
      id: "osm-layer",
      type: "raster",
      source: "osm",
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

// Standard nationwide freedom when online; dynamic bounds only active when offline
const PHILIPPINES_WIDE_BOUNDS: [[number, number], [number, number]] = [
  [116.0, 4.5],   // Southwest Philippines
  [127.0, 21.5],  // Northeast Philippines
];

interface BaseMapProps {
  onMapInit?: (map: Map) => void;
  onMapLoad?: (map: Map) => void;
  className?: string;
  children?: React.ReactNode;
  center?: [number, number];
  zoom?: number;
  actionControls?: (map: Map) => void;
}

export default function BaseMap({
  onMapInit,
  onMapLoad,
  className = "w-full h-full relative",
  children,
  center = DEFAULT_CENTER,
  zoom = 13.5,
  actionControls,
}: BaseMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [mapStyle, setMapStyle] = useState<any>(
    "https://api.maptiler.com/maps/streets-v2/style.json?key=BHhRqsneD3M4HnOd57WU"
  );
  const [usingFallback, setUsingFallback] = useState(false);

  useEffect(() => {
    preloadOfflineEngine();
  }, []);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    let fallbackTimeout: NodeJS.Timeout;

    const handleFailure = (reason: string) => {
      if (!usingFallback) {
        console.warn(`Map load failed (${reason}). Switching to OpenStreetMap fallback.`);
        setUsingFallback(true);
        setMapStyle(OSM_FALLBACK_STYLE);
      }
    };

    fallbackTimeout = setTimeout(() => {
      if (!isLoaded) handleFailure("Timeout waiting for style to load");
    }, 8000);

    const isOffline = typeof navigator !== "undefined" && !navigator.onLine;

    // Retrieve last explored boundary from localStorage if offline
    let dynamicBounds: [[number, number], [number, number]] = PHILIPPINES_WIDE_BOUNDS;
    if (isOffline && typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("lanes_explored_bounds");
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length === 2) {
            dynamicBounds = parsed;
          }
        }
      } catch (e) {}
    }

    const mapInstance = new maplibregl.Map({
      container: mapContainerRef.current,
      style: isOffline ? OSM_FALLBACK_STYLE : mapStyle,
      center: center,
      zoom: zoom,
      minZoom: isOffline ? 11.5 : 5.0, // Only clamp zoom-out when offline so you don't zoom into grey void
      maxZoom: 20.0,
      maxBounds: isOffline ? dynamicBounds : PHILIPPINES_WIDE_BOUNDS,
      pitch: 0,
      bearing: 0,
    });

    mapInstance.addControl(new TopViewControlV3(), "bottom-right");
    mapInstance.addControl(new ZoomLevelControl(), "bottom-right");
    mapInstance.addControl(
      new maplibregl.NavigationControl({
        showCompass: true,
        showZoom: true,
        visualizePitch: false,
      }),
      "bottom-right"
    );

    if (actionControls) {
      actionControls(mapInstance);
    }

    if (onMapInit) {
      onMapInit(mapInstance);
    }

    mapInstance.on("error", (e) => {
      const errMsg = (e.message || (e.error && e.error.message) || "").toLowerCase();
      // If offline, individual missing tiles should be silently ignored (not trigger a style reset)
      if (typeof navigator !== "undefined" && !navigator.onLine) {
        return;
      }
      const isStyleError =
        errMsg.includes("style") ||
        errMsg.includes("fetch") ||
        errMsg.includes("failed to fetch") ||
        errMsg.includes("ajax");
      if (isStyleError && !isLoaded) {
        handleFailure(errMsg || "MapLibre AJAX or source loading error");
      }
    });

    mapInstance.on("styleimagemissing", (e) => {
      const id = e.id;
      const canvas = document.createElement("canvas");
      canvas.width = 1;
      canvas.height = 1;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        const imageData = ctx.getImageData(0, 0, 1, 1);
        mapInstance.addImage(id, imageData);
      }
    });

    mapInstance.on("load", () => {
      clearTimeout(fallbackTimeout);
      mapRef.current = mapInstance;
      setIsLoaded(true);

      setTimeout(() => mapInstance.resize(), 100);

      if (onMapLoad) {
        onMapLoad(mapInstance);
      }
    });

    // Continuously update the explored boundary in localStorage while online
    mapInstance.on("moveend", () => {
      if (typeof navigator !== "undefined" && navigator.onLine) {
        try {
          const currentBounds = mapInstance.getBounds();
          const sw = currentBounds.getSouthWest();
          const ne = currentBounds.getNorthEast();

          let minLng = sw.lng;
          let minLat = sw.lat;
          let maxLng = ne.lng;
          let maxLat = ne.lat;

          const prev = localStorage.getItem("lanes_explored_bounds");
          if (prev) {
            const [pSW, pNE] = JSON.parse(prev);
            minLng = Math.min(minLng, pSW[0]);
            minLat = Math.min(minLat, pSW[1]);
            maxLng = Math.max(maxLng, pNE[0]);
            maxLat = Math.max(maxLat, pNE[1]);
          }

          // Expand padding slightly (+0.01 deg) so edge tiles feel natural
          const expanded: [[number, number], [number, number]] = [
            [minLng - 0.01, minLat - 0.01],
            [maxLng + 0.01, maxLat + 0.01]
          ];
          localStorage.setItem("lanes_explored_bounds", JSON.stringify(expanded));
        } catch (e) {}
      }
    });

    return () => {
      clearTimeout(fallbackTimeout);
      mapInstance.remove();
      mapRef.current = null;
      setIsLoaded(false);
    };
  }, [mapStyle]);

  const MAPTILER_STYLE_URL = "https://api.maptiler.com/maps/streets-v2/style.json?key=BHhRqsneD3M4HnOd57WU";

  // Auto-retry MapTiler ONLY when browser is online
  useEffect(() => {
    if (!usingFallback) return;
    const interval = setInterval(() => {
      if (typeof navigator !== "undefined" && !navigator.onLine) {
        return; // Do not reload or spam network while user is offline
      }
      fetch(MAPTILER_STYLE_URL, { method: "HEAD" })
        .then((res) => {
          if (res.ok) {
            console.log("MapTiler connectivity restored. Switching back from OSM fallback.");
            setUsingFallback(false);
            setMapStyle(MAPTILER_STYLE_URL);
          }
        })
        .catch(() => {});
    }, 15000); // Check every 15s

    return () => clearInterval(interval);
  }, [usingFallback]);

  return (
    <div className={`${className} bg-[#f2efe9]`}>
      <div ref={mapContainerRef} className="absolute inset-0 w-full h-full bg-[#f2efe9]" />

      {usingFallback && (
        <div className="absolute top-20 md:top-24 left-4 right-4 md:left-1/2 md:right-auto md:-translate-x-1/2 z-30 bg-amber-500/95 text-white text-xs md:text-sm px-4 py-2.5 rounded-xl shadow-lg flex items-center gap-2 backdrop-blur-sm animate-pulse max-w-md pointer-events-auto border border-amber-400/20 font-medium">
          <span>⚠️ MapTiler tiles offline. Switched to OpenStreetMap fallback. Retrying automatically...</span>
        </div>
      )}

      {!isLoaded && (
        <div className="absolute inset-0 bg-slate-100/50 backdrop-blur-sm flex items-center justify-center z-10">
          <div className="bg-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <span className="font-semibold text-sm text-slate-700">Loading Map...</span>
          </div>
        </div>
      )}

      {children}

      <style jsx global>{`
        .maplibregl-ctrl-bottom-right {
          bottom: 16px !important;
          right: 16px !important;
        }
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
      `}</style>
    </div>
  );
}
