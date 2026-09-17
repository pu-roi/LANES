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
      border-radius: 12px;
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
const MAPTILER_KEY = process.env.NEXT_PUBLIC_MAPTILER_KEY?.trim();

function getMapTilerStyleUrl(styleId: string): string | null {
  return MAPTILER_KEY
    ? `https://api.maptiler.com/maps/${styleId}/style.json?key=${encodeURIComponent(MAPTILER_KEY)}`
    : null;
}

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
  ...(MAPTILER_KEY
    ? [
        { id: "streets-v2", label: "Streets", emoji: "\uD83C\uDFD9", url: getMapTilerStyleUrl("streets-v2")! },
        { id: "streets-v2-dark", label: "Dark", emoji: "\uD83C\uDF11", url: getMapTilerStyleUrl("streets-v2-dark")! },
        { id: "bright-v2", label: "Roads", emoji: "\uD83D\uDEE3", url: getMapTilerStyleUrl("bright-v2")! },
        { id: "satellite", label: "Satellite", emoji: "\uD83D\uDEF0", url: getMapTilerStyleUrl("satellite")! },
      ]
    : []),
  // Raw OpenStreetMap raster tiles — no API key required, no terrain support.
  { id: "openstreetmap", label: "OpenStreetMap", emoji: "\uD83D\uDDFA", url: OSM_PICKER_STYLE },
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
    this._container.style.cssText = `position: relative; overflow: visible !important; border-radius: 12px;`;

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
      border-radius: 12px;
    `;
    btn.innerHTML = `<span style="font-size:18px;line-height:1;">🎨</span>`;
    btn.onmouseenter = () => { btn.style.backgroundColor = "#f8fafc"; };
    btn.onmouseleave = () => { btn.style.backgroundColor = "transparent"; };
    btn.onclick = (e) => { e.stopPropagation(); this._togglePanel(); };

    // Floating style picker panel (opens to the left of the control so it does not overlap upper buttons or route panel)
    this._panel = document.createElement("div");
    this._panel.style.cssText = `
      display: none;
      position: absolute;
      bottom: 0;
      right: calc(100% + 8px);
      background: white;
      border-radius: 14px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.10);
      padding: 8px;
      min-width: 140px;
      z-index: 9999;
      border: 1px solid #e5e7eb;
      overflow: hidden;
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
  private _is3D: boolean = false; // default: start in 2D (flat) mode
  private _onStyleLoad: (() => void) | undefined;

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

    this._onStyleLoad = () => {
      this._enforceState();
    };
    map.on("style.load", this._onStyleLoad);

    // Ensure initial 2D state (flat view, no 3D extrusions)
    if (!this._is3D) {
      this._disable3D(false);
    }

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

  // Helper: get 3D extruded building layer IDs from the current style
  private _get3DBuildingLayerIds(map: maplibregl.Map): string[] {
    try {
      return (map.getStyle()?.layers ?? [])
        .filter((l: any) => l.type === "fill-extrusion" || (l.id.toLowerCase().includes("building") && (l.id.toLowerCase().includes("3d") || l.id.toLowerCase().includes("extrusion"))))
        .map((l: any) => l.id);
    } catch {
      return [];
    }
  }

  // Helper: get 2D flat building layer IDs from the current style
  private _get2DBuildingLayerIds(map: maplibregl.Map): string[] {
    try {
      return (map.getStyle()?.layers ?? [])
        .filter((l: any) => l.id.toLowerCase().includes("building") && l.type !== "fill-extrusion")
        .map((l: any) => l.id);
    } catch {
      return [];
    }
  }

  private _enforceState() {
    if (!this._map || !this._map.getStyle()) return;
    try {
      if (this._is3D) {
        // Only add terrain source if it doesn't exist
        if (!this._map.getSource(Toggle3DControl.DEM_SOURCE_ID)) {
          this._map.addSource(Toggle3DControl.DEM_SOURCE_ID, {
            type: "raster-dem",
            tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
            tileSize: 256,
            encoding: "terrarium",
            maxzoom: 15,
            attribution: "Elevation tiles &copy; Mapzen, &copy; USGS",
          });
        }
        // Always ensure terrain is applied when in 3D mode
        if (!this._map.getTerrain()) {
          this._map.setTerrain({ source: Toggle3DControl.DEM_SOURCE_ID, exaggeration: Toggle3DControl.EXAGGERATION });
        }
        // In 3D mode, show 3D building extrusions and restore their heights
        this._get3DBuildingLayerIds(this._map).forEach((id) => {
          try {
            this._map!.setLayoutProperty(id, "visibility", "visible");
            this._map!.setPaintProperty(id, "fill-extrusion-height", { property: "render_height", type: "identity" });
            this._map!.setPaintProperty(id, "fill-extrusion-base", { property: "render_min_height", type: "identity" });
            this._map!.setPaintProperty(id, "fill-extrusion-opacity", 0.4);
            this._map!.setPaintProperty(id, "fill-extrusion-color", "hsl(44,14%,79%)");
          } catch {}
        });

        // Restore 2D building layer maxzooms to 15 (default MapTiler behavior)
        this._get2DBuildingLayerIds(this._map).forEach((id) => {
          try {
            const styleLayer = this._map!.getStyle()?.layers.find(l => l.id === id);
            const minZ = styleLayer?.minzoom ?? 13;
            this._map!.setLayerZoomRange(id, minZ, 15);
          } catch {}
        });
      } else {
        // In 2D mode: disable terrain and hide 3D building extrusions entirely
        if (this._map.getTerrain()) {
          this._map.setTerrain(null);
        }

        this._get3DBuildingLayerIds(this._map).forEach((id) => {
          try {
            this._map!.setLayoutProperty(id, "visibility", "none");
          } catch {}
        });

        // The critical fix: The 2D 'Building' layer natively disappears at maxzoom 15 in MapTiler styles.
        // We override this to maxzoom 24 so the crisp 2D building footprints remain visible at all zoom levels!
        this._get2DBuildingLayerIds(this._map).forEach((id) => {
          try {
            const styleLayer = this._map!.getStyle()?.layers.find(l => l.id === id);
            const minZ = styleLayer?.minzoom ?? 13;
            this._map!.setLayerZoomRange(id, minZ, 24);
            this._map!.setLayoutProperty(id, "visibility", "visible");
            
            if (styleLayer?.type === "fill") {
              this._map!.setPaintProperty(id, "fill-opacity", 0.7);
              this._map!.setPaintProperty(id, "fill-color", "#d1cbbf");
              this._map!.setPaintProperty(id, "fill-outline-color", "#9e9787");
            }
          } catch {}
        });
      }
    } catch (err) {
      console.warn("[Toggle3DControl] _enforceState error:", err);
    }
  }

  private _enable3D(animate: boolean = true) {
    if (!this._map) return;
    this._enforceState();
    if (animate && this._map.isStyleLoaded()) {
      this._map.easeTo({ pitch: Toggle3DControl.TARGET_PITCH_3D, duration: 700 });
    }
    try {
      if (this._map.getStyle() && !this._map.getLayer("sky")) {
        this._map.addLayer({
          id: "sky",
          type: "sky",
          paint: {
            "sky-type": "atmosphere",
            "sky-atmosphere-sun": [0.0, 90.0],
            "sky-atmosphere-sun-intensity": 15,
            "sky-atmosphere-color": "rgba(135, 206, 235, 1.0)",
            "sky-horizon-blend": 0.4,
          },
        } as any);
      }
    } catch {}
  }

  private _disable3D(animate: boolean = true) {
    if (!this._map) return;
    this._enforceState();
    if (animate && this._map.isStyleLoaded()) {
      this._map.easeTo({ pitch: 0, duration: 700 });
    }
    try {
      if (this._map.getStyle() && this._map.getLayer("sky")) {
        this._map.removeLayer("sky");
      }
    } catch {}
  }

  private _toggle() {
    if (!this._map) return;
    this._is3D = !this._is3D;
    if (this._is3D) {
      this._enable3D(true);
    } else {
      this._disable3D(true);
    }
    this._updateButton();
  }

  onRemove() {
    if (this._onStyleLoad && this._map) {
      this._map.off("style.load", this._onStyleLoad);
    }
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

const PRIMARY_MAP_STYLE_URL = getMapTilerStyleUrl("streets-v2");
const FIRST_RENDER_BUDGET_MS = 1500;
// OSM is already usable before a background retry begins, so MapTiler gets a
// longer window to fully rebuild its detailed style without weakening startup.
const PRIMARY_RETRY_RENDER_BUDGET_MS = 6000;
const MAPTILER_RETRY_DELAYS_MS = [30_000, 60_000, 120_000, 300_000];

type ActiveMapStyle = "primary" | "fallback";

function redactMapTilerKey(value: string | undefined): string | undefined {
  return value?.replace(/([?&]key=)[^&]+/i, "$1[redacted]");
}

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
  const initialViewportRef = useRef({ center, zoom });
  const callbacksRef = useRef({ onMapInit, onMapLoad, actionControls });
  const [isLoaded, setIsLoaded] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [isUsingFallback, setIsUsingFallback] = useState(false);

  useEffect(() => {
    callbacksRef.current = { onMapInit, onMapLoad, actionControls };
  }, [actionControls, onMapInit, onMapLoad]);

  useEffect(() => {
    preloadOfflineEngine();
  }, []);

  // Map creation intentionally uses the initial viewport only. Updating these
  // props must not recreate the WebGL map; callback props are read via refs.
  useEffect(() => {
    if (!mapContainerRef.current) return;

    let destroyed = false;
    let activeStyle: ActiveMapStyle = (
      !PRIMARY_MAP_STYLE_URL || (typeof navigator !== "undefined" && !navigator.onLine)
    ) ? "fallback" : "primary";
    let activeAttempt = 1;
    let initialLoadFinished = false;
    let hasNotifiedMapLoad = false;
    let retryIndex = 0;
    let firstRenderTimer: ReturnType<typeof setTimeout> | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    const reportedAttempts = new Set<number>();

    const clearFirstRenderTimer = () => {
      if (firstRenderTimer) {
        clearTimeout(firstRenderTimer);
        firstRenderTimer = null;
      }
    };

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

    let initialCenter = initialViewportRef.current.center;
    let initialZoom = initialViewportRef.current.zoom;
    let initialPitch = 0;
    let initialBearing = 0;

    if (typeof window !== "undefined") {
      try {
        const savedViewport = sessionStorage.getItem("lanes_map_viewport");
        if (savedViewport) {
          const parsed = JSON.parse(savedViewport);
          if (parsed.center) initialCenter = parsed.center;
          if (parsed.zoom !== undefined) initialZoom = parsed.zoom;
          if (parsed.pitch !== undefined) initialPitch = parsed.pitch;
          if (parsed.bearing !== undefined) initialBearing = parsed.bearing;
        }
      } catch (e) {}
    }

    const startedAt = performance.now();
    const mapInstance = new maplibregl.Map({
      container: mapContainerRef.current,
      style: activeStyle === "primary" ? PRIMARY_MAP_STYLE_URL! : OSM_FALLBACK_STYLE,
      center: initialCenter,
      zoom: initialZoom,
      minZoom: isOffline ? 11.5 : 5.0, // Only clamp zoom-out when offline so you don't zoom into grey void
      maxZoom: 20.0,
      maxPitch: 70,
      maxBounds: isOffline ? dynamicBounds : PHILIPPINES_WIDE_BOUNDS,
      pitch: initialPitch,
      bearing: initialBearing,
    });
    mapRef.current = mapInstance;

    const styleMatchesActiveAttempt = () => {
      try {
        const isOsmStyle = Boolean(mapInstance.getSource("osm"));
        return activeStyle === "fallback" ? isOsmStyle : !isOsmStyle;
      } catch {
        return false;
      }
    };

    const reportFailure = (phase: string, error?: unknown) => {
      if (reportedAttempts.has(activeAttempt)) return;
      reportedAttempts.add(activeAttempt);
      const event = error as { message?: string; error?: { message?: string }; url?: string } | undefined;
      const message = event?.message || event?.error?.message || String(error || "No first visual render");
      console.warn("[map-style-fallback]", {
        attempt: activeAttempt,
        phase,
        elapsedMs: Math.round(performance.now() - startedAt),
        url: redactMapTilerKey(event?.url),
        message: redactMapTilerKey(message),
      });
    };

    const completeStyle = (style: ActiveMapStyle) => {
      if (destroyed || style !== activeStyle || !styleMatchesActiveAttempt()) return;
      clearFirstRenderTimer();
      // A fallback can become the map's first completed style when MapTiler
      // misses the startup budget. Mark it complete so future MapTiler
      // `style.load` events are eligible to restore the detailed map.
      initialLoadFinished = true;
      setIsLoaded(true);
      setIsRecovering(false);
      setIsUsingFallback(style === "fallback");

      if (style === "primary") {
        retryIndex = 0;
        if (retryTimer) {
          clearTimeout(retryTimer);
          retryTimer = null;
        }
        console.debug("[map-performance]", {
          style: "maptiler",
          loadMs: Math.round(performance.now() - startedAt),
        });
      }

      if (!hasNotifiedMapLoad) {
        hasNotifiedMapLoad = true;
        callbacksRef.current.onMapLoad?.(mapInstance);
      }
    };

    const schedulePrimaryRetry = (immediate = false) => {
      if (destroyed || retryTimer || !PRIMARY_MAP_STYLE_URL || (typeof navigator !== "undefined" && !navigator.onLine)) return;
      const delay = immediate ? 0 : MAPTILER_RETRY_DELAYS_MS[Math.min(retryIndex, MAPTILER_RETRY_DELAYS_MS.length - 1)];
      retryIndex += 1;
      retryTimer = setTimeout(() => {
        retryTimer = null;
        if (destroyed || activeStyle !== "fallback" || (typeof navigator !== "undefined" && !navigator.onLine)) return;
        activeStyle = "primary";
        activeAttempt += 1;
        setIsLoaded(false);
        setIsRecovering(true);
        setIsUsingFallback(false);
        mapInstance.setStyle(PRIMARY_MAP_STYLE_URL, { diff: false });
        firstRenderTimer = setTimeout(
          () => activateFallback("primary_retry_timeout"),
          PRIMARY_RETRY_RENDER_BUDGET_MS,
        );
      }, delay);
    };

    const activateFallback = (phase: string, error?: unknown) => {
      if (destroyed || activeStyle === "fallback") return;
      reportFailure(phase, error);
      clearFirstRenderTimer();
      activeStyle = "fallback";
      activeAttempt += 1;
      setIsLoaded(false);
      setIsRecovering(true);
      setIsUsingFallback(true);
      mapInstance.setStyle(OSM_FALLBACK_STYLE, { diff: false });
      schedulePrimaryRetry();
    };

    if (activeStyle === "primary") {
      firstRenderTimer = setTimeout(() => activateFallback("first_render_timeout"), FIRST_RENDER_BUDGET_MS);
    } else {
      setIsUsingFallback(true);
    }

    mapInstance.on('moveend', () => {
      try {
        const viewport = {
          center: mapInstance.getCenter().toArray(),
          zoom: mapInstance.getZoom(),
          pitch: mapInstance.getPitch(),
          bearing: mapInstance.getBearing()
        };
        sessionStorage.setItem("lanes_map_viewport", JSON.stringify(viewport));
      } catch (e) {}
    });

    mapInstance.addControl(new TopViewControlV3(), "bottom-right");
    mapInstance.addControl(new ZoomLevelControl(), "bottom-right");
    const navControl = new maplibregl.NavigationControl({
      showCompass: true,
      showZoom: true,
      visualizePitch: true, // Show pitch arc on the compass when map is tilted
    });
    mapInstance.addControl(navControl, "bottom-right");

    // Hijack compass click to ONLY reset bearing, not pitch (we have TopViewControlV3 for pitch)
    setTimeout(() => {
      const compassBtn = mapInstance.getContainer().querySelector('.maplibregl-ctrl-compass');
      if (compassBtn) {
        compassBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          e.preventDefault();
          mapInstance.easeTo({ bearing: 0, pitch: mapInstance.getPitch(), duration: 800 });
        }, true);
      }
    }, 100);

    // Add the 3D / 2D terrain toggle button (only when online; offline has no elevation data)
    if (!isOffline && PRIMARY_MAP_STYLE_URL) {
      mapInstance.addControl(new Toggle3DControl(), "bottom-right");
      mapInstance.addControl(new MapStylePickerControl(), "bottom-right");
    }

    callbacksRef.current.actionControls?.(mapInstance);
    callbacksRef.current.onMapInit?.(mapInstance);

    mapInstance.on("error", (e) => {
      if (activeStyle !== "primary" || (typeof navigator !== "undefined" && !navigator.onLine)) return;
      const errorEvent = e as unknown as { message?: string; error?: { message?: string }; url?: string };
      const message = `${errorEvent.message || ""} ${errorEvent.error?.message || ""}`.toLowerCase();
      const url = errorEvent.url || "";
      if (url.includes("api.maptiler.com") || message.includes("maptiler") || message.includes("failed to fetch") || message.includes("ajax")) {
        activateFallback("maptiler_resource_error", errorEvent);
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
      initialLoadFinished = true;
      completeStyle(activeStyle);
      setTimeout(() => mapInstance.resize(), 100);
    });

    mapInstance.on("style.load", () => {
      // `load` establishes the initial first-render budget. Subsequent setStyle
      // operations retain this WebGL map and let feature hooks restore layers.
      if (!initialLoadFinished && activeStyle === "primary") return;
      requestAnimationFrame(() => completeStyle(activeStyle));
    });

    const handleOnline = () => {
      if (activeStyle === "fallback") {
        retryIndex = 0;
        schedulePrimaryRetry(true);
      }
    };
    window.addEventListener("online", handleOnline);

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

    // Observe container size changes (e.g. sidebar open/close, responsive breakpoint shifts, route transitions)
    const container = mapContainerRef.current;
    let resizeObserver: ResizeObserver | null = null;
    let resizeTimer: ReturnType<typeof setTimeout> | null = null;
    if (container && typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(() => {
        // Debounce resize events so the WebGL canvas buffer is not discarded on every 16ms animation frame
        if (resizeTimer) clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
          try {
            if (mapInstance && typeof mapInstance.resize === "function") {
              mapInstance.resize();
            }
          } catch (e) {}
        }, 400);
      });
      resizeObserver.observe(container);
    }

    return () => {
      destroyed = true;
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeObserver?.disconnect();
      clearFirstRenderTimer();
      if (retryTimer) clearTimeout(retryTimer);
      window.removeEventListener("online", handleOnline);
      mapInstance.remove();
      mapRef.current = null;
      setIsLoaded(false);
    };
  }, []);

  const showLoader = !isLoaded || isRecovering;

  return (
    <div className={`${className} bg-[#f2efe9]`}>
      <div ref={mapContainerRef} className="absolute inset-0 w-full h-full bg-[#f2efe9] transform-gpu" />

      {showLoader && (
        <div className="absolute inset-0 bg-slate-100/50 backdrop-blur-sm flex items-center justify-center z-10">
          <div className="bg-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
            <span className="font-semibold text-sm text-slate-700">
              {isRecovering ? "Reconnecting detailed map..." : "Loading map..."}
            </span>
          </div>
        </div>
      )}

      {isLoaded && isUsingFallback && (
        <div
          role="status"
          className="pointer-events-none fixed top-4 sm:top-[5.25rem] left-1/2 -translate-x-1/2 z-10 w-[calc(100vw-2rem)] max-w-sm sm:w-auto sm:max-w-72 rounded-2xl bg-white/95 px-3 py-2 text-center text-xs font-medium leading-5 text-slate-600 shadow-md backdrop-blur-sm"
        >
          Using a basic map while the detailed map reconnects.
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
          box-shadow: none !important;
          cursor: pointer !important;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          margin: 0 !important;
        }
        .maplibregl-ctrl-group > button:only-child {
          border-radius: 12px !important;
        }
        .maplibregl-ctrl-group > button:first-child:not(:only-child) {
          border-top-left-radius: 12px !important;
          border-top-right-radius: 12px !important;
          border-bottom-left-radius: 0 !important;
          border-bottom-right-radius: 0 !important;
        }
        .maplibregl-ctrl-group > button:last-child:not(:only-child) {
          border-bottom-left-radius: 12px !important;
          border-bottom-right-radius: 12px !important;
          border-top-left-radius: 0 !important;
          border-top-right-radius: 0 !important;
        }
        .maplibregl-ctrl-group > button:not(:first-child):not(:last-child) {
          border-radius: 0 !important;
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
