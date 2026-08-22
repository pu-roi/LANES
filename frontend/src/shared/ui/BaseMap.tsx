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
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 48px;
      padding: 4px 2px;
      font-size: 10px;
      font-weight: 700;
      line-height: 1.2;
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
      text-align: center;
    `;
    this._updateText();
    this._container.appendChild(this._textSpan);

    this._map.on("zoom", this._onUpdate);
    this._map.on("pitch", this._onUpdate);
    this._map.on("rotate", this._onUpdate);
    return this._container;
  }

  private _onUpdate = () => {
    this._updateText();
  };

  private _updateText() {
    if (this._map && this._textSpan) {
      const z = this._map.getZoom();
      const p = this._map.getPitch();
      this._textSpan.innerHTML = `<div>Z: ${z.toFixed(1)}</div><div class="mt-0.5">P: ${Math.round(p)}°</div>`;
      this._textSpan.title = `Zoom: ${z.toFixed(2)}, Pitch: ${p.toFixed(1)}° | ${z >= 14 ? "Street Level (Lines/Polygons Active)" : "City View (Circle Pins Active)"}`;
    }
  }

  onRemove() {
    this._map?.off("zoom", this._onUpdate);
    this._map?.off("pitch", this._onUpdate);
    this._map?.off("rotate", this._onUpdate);
    this._container?.parentNode?.removeChild(this._container);
    this._map = undefined;
  }
}

// ── Map Style Definitions ─────────────────────────────────────────────────────
const MAPTILER_KEY = "BHhRqsneD3M4HnOd57WU";

// OpenStreetMap raster style — used as the OSM option in the picker.
// Defined here (above MAP_STYLES) so it can be referenced in the array.
const OSM_PICKER_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: [
        "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm-layer", type: "raster", source: "osm", minzoom: 0, maxzoom: 19 }],
};

export const MAP_STYLES: { id: string; label: string; emoji: string; url: string | object }[] = [
  {
    id: "streets-v2",
    label: "Streets",
    emoji: "\uD83C\uDFD9",
    url: `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`,
  },
  {
    id: "streets-v2-dark",
    label: "Dark",
    emoji: "\uD83C\uDF11",
    url: `https://api.maptiler.com/maps/streets-v2-dark/style.json?key=${MAPTILER_KEY}`,
  },
  {
    // bright-v2 uses high-contrast road colours:
    // motorways = orange, primary = yellow, secondary = white, residential = light-grey.
    // Ideal for differentiating expressways, highways, city roads, and streets at a glance.
    id: "bright-v2",
    label: "Roads",
    emoji: "\uD83D\uDEE3",
    url: `https://api.maptiler.com/maps/bright-v2/style.json?key=${MAPTILER_KEY}`,
  },
  {
    id: "satellite",
    label: "Satellite",
    emoji: "\uD83D\uDEF0",
    url: `https://api.maptiler.com/maps/satellite/style.json?key=${MAPTILER_KEY}`,
  },
  {
    // Raw OpenStreetMap raster tiles — no API key required, no terrain support.
    id: "openstreetmap",
    label: "OpenStreetMap",
    emoji: "\uD83D\uDDFA",
    url: OSM_PICKER_STYLE,
  },
];

// ── MapStylePickerControl ─────────────────────────────────────────────────────
// A 🎨 button that opens a floating panel to switch between map styles.
export class MapStylePickerControl {
  private _map: maplibregl.Map | undefined;
  private _container: HTMLDivElement | undefined;
  private _panel: HTMLDivElement | undefined;
  private _isOpen: boolean = false;
  private _activeStyleId: string = "streets-v2";

  onAdd(map: maplibregl.Map) {
    this._map = map;

    // Outer control wrapper
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this._container.style.cssText = `position: relative; overflow: visible !important;`;

    // Toggle button
    const btn = document.createElement("button");
    btn.type = "button";
    btn.title = "Change Map Style";
    btn.className = "maplibregl-ctrl-icon";
    btn.style.cssText = `
      width: 48px; height: 48px;
      display: flex; align-items: center; justify-content: center;
      background: transparent; border: none; cursor: pointer;
      font-size: 20px; transition: background-color 0.2s;
    `;
    btn.innerHTML = `<span style="font-size:18px;line-height:1;">🎨</span>`;
    btn.onmouseenter = () => { btn.style.backgroundColor = "#f8fafc"; };
    btn.onmouseleave = () => { btn.style.backgroundColor = "transparent"; };
    btn.onclick = (e) => { e.stopPropagation(); this._togglePanel(); };

    // Floating style picker panel
    this._panel = document.createElement("div");
    this._panel.style.cssText = `
      display: none;
      position: absolute;
      bottom: 54px;
      right: 0;
      background: white;
      border-radius: 14px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.10);
      padding: 8px;
      min-width: 140px;
      z-index: 9999;
      border: 1px solid #e5e7eb;
    `;

    MAP_STYLES.forEach((style) => {
      const item = document.createElement("button");
      item.type = "button";
      item.style.cssText = `
        display: flex; align-items: center; gap: 8px;
        width: 100%; padding: 8px 10px;
        background: transparent; border: none; border-radius: 8px;
        cursor: pointer; font-size: 13px; font-weight: 500;
        color: #1e293b; text-align: left;
        transition: background-color 0.15s;
        white-space: nowrap;
      `;
      item.innerHTML = `<span style="font-size:16px;">${style.emoji}</span><span>${style.label}</span>`;

      const updateActive = () => {
        item.style.backgroundColor = this._activeStyleId === style.id ? "#eff6ff" : "transparent";
        (item.querySelector("span:last-child") as HTMLElement).style.color =
          this._activeStyleId === style.id ? "#2563eb" : "#1e293b";
        (item.querySelector("span:last-child") as HTMLElement).style.fontWeight =
          this._activeStyleId === style.id ? "700" : "500";
      };
      updateActive();

      item.onmouseenter = () => {
        if (this._activeStyleId !== style.id) item.style.backgroundColor = "#f8fafc";
      };
      item.onmouseleave = () => { updateActive(); };
      item.onclick = (e) => {
        e.stopPropagation();
        this._activeStyleId = style.id;
        this._map?.setStyle(style.url as any);
        // Refresh all item active states
        this._panel?.querySelectorAll("button").forEach((btn, i) => {
          const s = MAP_STYLES[i];
          const lbl = btn.querySelector("span:last-child") as HTMLElement;
          if (s) {
            btn.style.backgroundColor = this._activeStyleId === s.id ? "#eff6ff" : "transparent";
            if (lbl) {
              lbl.style.color = this._activeStyleId === s.id ? "#2563eb" : "#1e293b";
              lbl.style.fontWeight = this._activeStyleId === s.id ? "700" : "500";
            }
          }
        });
        this._closePanel();
      };

      this._panel!.appendChild(item);
    });

    this._container.appendChild(btn);
    this._container.appendChild(this._panel);

    // Close panel when clicking anywhere on the map
    map.on("click", () => this._closePanel());

    return this._container;
  }

  private _togglePanel() {
    this._isOpen ? this._closePanel() : this._openPanel();
  }

  private _openPanel() {
    if (!this._panel) return;
    this._isOpen = true;
    this._panel.style.display = "block";
    // Animate in
    this._panel.style.opacity = "0";
    this._panel.style.transform = "translateY(8px)";
    this._panel.style.transition = "opacity 0.18s ease, transform 0.18s ease";
    requestAnimationFrame(() => {
      if (this._panel) {
        this._panel.style.opacity = "1";
        this._panel.style.transform = "translateY(0)";
      }
    });
  }

  private _closePanel() {
    if (!this._panel) return;
    this._isOpen = false;
    this._panel.style.display = "none";
  }

  onRemove() {
    this._container?.parentNode?.removeChild(this._container);
    this._map = undefined;
  }
}

// ── Toggle3DControl ──────────────────────────────────────────────────────────
// A custom map control that switches between flat (2D) and terrain (3D) mode.
export class Toggle3DControl {
  private _map: maplibregl.Map | undefined;
  private _container: HTMLDivElement | undefined;
  private _button: HTMLButtonElement | undefined;
  private _is3D: boolean = true; // default: start in 3D mode

  private static readonly DEM_SOURCE_ID = "terrarium-dem";
  private static readonly TARGET_PITCH_3D = 45;
  private static readonly EXAGGERATION = 1.5;

  onAdd(map: maplibregl.Map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";

    this._button = document.createElement("button");
    this._button.type = "button";
    this._button.className = "maplibregl-ctrl-icon";
    this._button.style.cssText = `
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      cursor: pointer;
      font-size: 20px;
      transition: background-color 0.2s;
    `;
    this._button.onmouseenter = () => {
      if (this._button) this._button.style.backgroundColor = "#f8fafc";
    };
    this._button.onmouseleave = () => {
      if (this._button) this._button.style.backgroundColor = "transparent";
    };
    this._updateButton();
    this._button.onclick = () => this._toggle();

    this._container.appendChild(this._button);
    return this._container;
  }

  private _updateButton() {
    if (!this._button) return;
    if (this._is3D) {
      this._button.title = "Switch to 2D (Flat) View";
      this._button.innerHTML = `<span style="font-size:18px;line-height:1;display:flex;align-items:center;justify-content:center;">🗺</span>`;
    } else {
      this._button.title = "Switch to 3D Terrain View";
      this._button.innerHTML = `<span style="font-size:18px;line-height:1;display:flex;align-items:center;justify-content:center;">🏔</span>`;
    }
  }

  // Helper: get all fill-extrusion layer IDs from the current style (3D buildings)
  private _getExtrusionLayerIds(map: maplibregl.Map): string[] {
    try {
      return (map.getStyle()?.layers ?? [])
        .filter((l: any) => l.type === "fill-extrusion")
        .map((l: any) => l.id);
    } catch {
      return [];
    }
  }

  private _toggle() {
    if (!this._map) return;
    this._is3D = !this._is3D;
    const map = this._map;

    if (this._is3D) {
      // Re-enable terrain
      if (!map.getSource(Toggle3DControl.DEM_SOURCE_ID)) {
        map.addSource(Toggle3DControl.DEM_SOURCE_ID, {
          type: "raster-dem",
          tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
          tileSize: 256,
          encoding: "terrarium",
          maxzoom: 15,
          attribution: "Elevation tiles &copy; Mapzen, &copy; USGS",
        });
      }
      map.setTerrain({ source: Toggle3DControl.DEM_SOURCE_ID, exaggeration: Toggle3DControl.EXAGGERATION });
      map.easeTo({ pitch: Toggle3DControl.TARGET_PITCH_3D, duration: 700 });
      // Restore 3D buildings
      this._getExtrusionLayerIds(map).forEach((id) => {
        try { map.setLayoutProperty(id, "visibility", "visible"); } catch {}
      });
    } else {
      // Disable terrain and flatten the map
      map.setTerrain(null);
      map.easeTo({ pitch: 0, duration: 700 });
      // Hide 3D building extrusions for a clean flat look
      this._getExtrusionLayerIds(map).forEach((id) => {
        try { map.setLayoutProperty(id, "visibility", "none"); } catch {}
      });
    }

    this._updateButton();
  }

  onRemove() {
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
            dynamicBounds = parsed as [[number, number], [number, number]];
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
      maxPitch: 70,
      maxBounds: isOffline ? dynamicBounds : PHILIPPINES_WIDE_BOUNDS,
      // Start flat (pitch 0) by default per user request
      pitch: 0,
      bearing: 0,
    });

    mapInstance.addControl(new TopViewControlV3(), "bottom-right");
    mapInstance.addControl(new ZoomLevelControl(), "bottom-right");
    mapInstance.addControl(
      new maplibregl.NavigationControl({
        showCompass: true,
        showZoom: true,
        visualizePitch: true, // Show pitch arc on the compass when map is tilted
      }),
      "bottom-right"
    );

    // Add the 3D / 2D terrain toggle button (only when online; offline has no elevation data)
    if (!isOffline) {
      mapInstance.addControl(new Toggle3DControl(), "bottom-right");
      mapInstance.addControl(new MapStylePickerControl(), "bottom-right");
    }

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

    // ── Terrain helpers ──────────────────────────────────────────────────────
    // MapLibre GL JS v5 internally re-triggers a 'style.load' event when
    // setTerrain() is called — this wipes all custom sources/layers added after
    // the initial 'load'. We solve this by re-applying terrain inside a
    // persistent 'style.load' listener, so it survives every style reload.
    const applyTerrain = (m: maplibregl.Map) => {
      if (isOffline) return; // No elevation data available offline
      try {
        if (!m.getSource("terrarium-dem")) {
          m.addSource("terrarium-dem", {
            type: "raster-dem",
            tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
            tileSize: 256,
            encoding: "terrarium",
            maxzoom: 15,
            attribution: "Elevation tiles &copy; Mapzen, &copy; USGS",
          });
        }
        // setTerrain will itself cause another style.load in v5 — the guard
        // above (getSource check) prevents an infinite add-source loop.
        m.setTerrain({ source: "terrarium-dem", exaggeration: 1.5 });

        if (!m.getLayer("sky")) {
          m.addLayer({
            id: "sky",
            type: "sky",
            paint: {
              "sky-type": "atmosphere",
              "sky-atmosphere-sun": [0.0, 90.0],
              "sky-atmosphere-sun-intensity": 15,
              "sky-atmosphere-color": "rgba(135, 206, 235, 1.0)",
              "sky-horizon-blend": 0.4,
            },
          } as any); // 'sky' layer type not yet in this version's maplibre-gl typedefs
        }
      } catch (err) {
        // Guard: if the map has already been removed, swallow the error silently
        console.warn("[Terrain] applyTerrain error:", err);
      }
    };

    // Re-apply terrain every time the style (re-)loads so it survives hot-swaps
    // between MapTiler ↔ OSM fallback and the internal reload triggered by setTerrain itself.
    mapInstance.on("style.load", () => {
      applyTerrain(mapInstance);
    });

    mapInstance.on("load", () => {
      clearTimeout(fallbackTimeout);
      mapRef.current = mapInstance;
      setIsLoaded(true);

      setTimeout(() => mapInstance.resize(), 100);

      // Initial terrain application — the 'style.load' listener above will
      // handle all subsequent reloads automatically.
      applyTerrain(mapInstance);

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
