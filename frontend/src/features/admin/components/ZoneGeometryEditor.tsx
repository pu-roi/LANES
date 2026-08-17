"use client";

/**
 * ZoneGeometryEditor
 *
 * An overlay toolbar that lets admins draw custom flood zone boundaries
 * directly on the live map. Supports Polygon (inundation area) and LineString
 * (blocked road segment) drawing modes, powered by MapLibre GL JS click handlers.
 *
 * Usage:
 *   <ZoneGeometryEditor
 *     map={mapInstance}
 *     isActive={isDrawing}
 *     onGeometryComplete={(geojson) => setCustomGeometry(geojson)}
 *     onCancel={() => setIsDrawing(false)}
 *   />
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Map, MapMouseEvent } from "maplibre-gl";
import { Square, Minus, Check, Trash2, CornerDownLeft, Info } from "lucide-react";
import { Button } from "@/shared/ui/Button";

// ─── Types ────────────────────────────────────────────────────────────────────

export type DrawMode = "polygon" | "linestring";

export interface PolygonGeometry {
  type: "Polygon";
  coordinates: [number, number][][];
}

export interface LineStringGeometry {
  type: "LineString";
  coordinates: [number, number][];
}

export type DrawnGeometry = PolygonGeometry | LineStringGeometry;

interface ZoneGeometryEditorProps {
  map: Map | null;
  isActive: boolean;
  initialMode?: DrawMode;
  onGeometryComplete: (geometry: DrawnGeometry) => void;
  onCancel: () => void;
}

// ─── Layer IDs ────────────────────────────────────────────────────────────────
const DRAW_SOURCE = "draw-editor-source";
const DRAW_FILL_LAYER = "draw-editor-fill";
const DRAW_LINE_LAYER = "draw-editor-line";
const DRAW_POINT_LAYER = "draw-editor-points";

// ─── Component ────────────────────────────────────────────────────────────────

export function ZoneGeometryEditor({
  map,
  isActive,
  initialMode = "polygon",
  onGeometryComplete,
  onCancel,
}: ZoneGeometryEditorProps) {
  const [drawMode, setDrawMode] = useState<DrawMode>(initialMode);
  const [points, setPoints] = useState<[number, number][]>([]);
  const [cursorPos, setCursorPos] = useState<[number, number] | null>(null);
  const cursorPosRef = useRef<[number, number] | null>(null);
  const pointsRef = useRef<[number, number][]>([]);

  // Keep refs in sync for use inside event callbacks
  useEffect(() => { pointsRef.current = points; }, [points]);
  useEffect(() => { cursorPosRef.current = cursorPos; }, [cursorPos]);

  // ── Canvas Update ────────────────────────────────────────────────────────────

  const updateDrawCanvas = useCallback(
    (pts: [number, number][], cursor: [number, number] | null) => {
      if (!map) return;
      if (!map.getSource(DRAW_SOURCE)) return;

      const all = cursor ? [...pts, cursor] : pts;
      const features: any[] = [];

      if (drawMode === "polygon" && all.length >= 2) {
        const ring = [...all, all[0]]; // close it
        features.push({
          type: "Feature",
          geometry: { type: "Polygon", coordinates: [ring] },
          properties: { type: "fill" },
        });
      } else if (drawMode === "linestring" && all.length >= 2) {
        features.push({
          type: "Feature",
          geometry: { type: "LineString", coordinates: all },
          properties: { type: "line" },
        });
      }

      // Draw placed points
      pts.forEach((p, i) => {
        features.push({
          type: "Feature",
          geometry: { type: "Point", coordinates: p },
          properties: { index: i, type: "point" },
        });
      });

      (map.getSource(DRAW_SOURCE) as any).setData({
        type: "FeatureCollection",
        features,
      });
    },
    [map, drawMode]
  );

  // ── MapLibre Layer Setup ──────────────────────────────────────────────────────

  useEffect(() => {
    if (!map || !isActive) return;

    const addLayers = () => {
      if (!map.getSource(DRAW_SOURCE)) {
        map.addSource(DRAW_SOURCE, {
          type: "geojson",
          data: { type: "FeatureCollection", features: [] },
        });
      }

      if (!map.getLayer(DRAW_FILL_LAYER)) {
        map.addLayer({
          id: DRAW_FILL_LAYER,
          type: "fill",
          source: DRAW_SOURCE,
          filter: ["==", ["get", "type"], "fill"],
          paint: {
            "fill-color": "#3b82f6",
            "fill-opacity": 0.18,
          },
        });
      }

      if (!map.getLayer(DRAW_LINE_LAYER)) {
        map.addLayer({
          id: DRAW_LINE_LAYER,
          type: "line",
          source: DRAW_SOURCE,
          paint: {
            "line-color": "#3b82f6",
            "line-width": 2.5,
            "line-dasharray": [4, 2],
            "line-opacity": 0.9,
          },
        });
      }

      if (!map.getLayer(DRAW_POINT_LAYER)) {
        map.addLayer({
          id: DRAW_POINT_LAYER,
          type: "circle",
          source: DRAW_SOURCE,
          filter: ["==", ["get", "type"], "point"],
          paint: {
            "circle-radius": 5,
            "circle-color": "#ffffff",
            "circle-stroke-color": "#3b82f6",
            "circle-stroke-width": 2,
          },
        });
      }
    };

    if (map.isStyleLoaded()) {
      addLayers();
    } else {
      map.once("styledata", addLayers);
    }

    // Change cursor
    const canvas = map.getCanvas();
    canvas.style.cursor = "crosshair";

    return () => {
      canvas.style.cursor = "";
      // Clean up layers when drawing stops
      [DRAW_FILL_LAYER, DRAW_LINE_LAYER, DRAW_POINT_LAYER].forEach((id) => {
        if (map.getLayer(id)) map.removeLayer(id);
      });
      if (map.getSource(DRAW_SOURCE)) map.removeSource(DRAW_SOURCE);
    };
  }, [map, isActive]);

  // ── Mouse Event Handlers ──────────────────────────────────────────────────────

  useEffect(() => {
    if (!map || !isActive) return;

    const handleClick = (e: MapMouseEvent) => {
      const coord: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      const newPoints = [...pointsRef.current, coord];
      setPoints(newPoints);
      updateDrawCanvas(newPoints, cursorPosRef.current);
    };

    const handleMouseMove = (e: MapMouseEvent) => {
      const coord: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      setCursorPos(coord);
      updateDrawCanvas(pointsRef.current, coord);
    };

    map.on("click", handleClick);
    map.on("mousemove", handleMouseMove);

    return () => {
      map.off("click", handleClick);
      map.off("mousemove", handleMouseMove);
    };
  }, [map, isActive, updateDrawCanvas]);

  // ── Update canvas whenever mode/points change ──────────────────────────────

  useEffect(() => {
    updateDrawCanvas(points, cursorPos);
  }, [points, cursorPos, updateDrawCanvas]);

  // ── Reset on open ─────────────────────────────────────────────────────────────

  useEffect(() => {
    if (isActive) {
      setPoints([]);
      setCursorPos(null);
      setDrawMode(initialMode);
    }
  }, [isActive, initialMode]);

  // ── Undo last point ───────────────────────────────────────────────────────────

  const handleUndo = () => {
    setPoints((prev) => {
      const next = prev.slice(0, -1);
      updateDrawCanvas(next, cursorPos);
      return next;
    });
  };

  // ── Clear all ─────────────────────────────────────────────────────────────────

  const handleClear = () => {
    setPoints([]);
    updateDrawCanvas([], cursorPos);
  };

  // ── Confirm geometry ─────────────────────────────────────────────────────────

  const handleConfirm = () => {
    if (drawMode === "polygon" && points.length >= 3) {
      const closed: [number, number][] = [...points, points[0]];
      onGeometryComplete({ type: "Polygon", coordinates: [closed] });
    } else if (drawMode === "linestring" && points.length >= 2) {
      onGeometryComplete({ type: "LineString", coordinates: points });
    }
  };

  const minPoints = drawMode === "polygon" ? 3 : 2;
  const canConfirm = points.length >= minPoints;

  if (!isActive) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="geometry-editor-toolbar"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 16 }}
        transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
        className="absolute bottom-20 left-1/2 -translate-x-1/2 z-30 pointer-events-auto"
      >
        {/* Toolbar */}
        <div className="bg-white/95 backdrop-blur-md shadow-2xl border border-slate-200/80 rounded-2xl px-4 py-3 flex flex-col items-center gap-3 min-w-[320px]">
          
          {/* Header */}
          <div className="flex items-center justify-between w-full">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Draw Zone Boundary
            </span>
            <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
              <button
                onClick={() => { setDrawMode("polygon"); handleClear(); }}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                  drawMode === "polygon"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                <Square className="w-3 h-3" />
                Polygon
              </button>
              <button
                onClick={() => { setDrawMode("linestring"); handleClear(); }}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                  drawMode === "linestring"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                <Minus className="w-3 h-3" />
                Road Line
              </button>
            </div>
          </div>

          {/* Instruction */}
          <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 rounded-xl px-3 py-2 w-full">
            <Info className="w-3.5 h-3.5 shrink-0 text-blue-400" />
            {drawMode === "polygon"
              ? `Click on the map to place vertices. Minimum 3 points to confirm. (${points.length} placed)`
              : `Click to place road segment endpoints. Minimum 2 points. (${points.length} placed)`}
          </div>

          {/* Point count indicator */}
          <div className="flex items-center gap-1 w-full flex-wrap">
            {points.map((_, i) => (
              <div
                key={i}
                className="w-5 h-5 rounded-full bg-blue-100 border-2 border-blue-400 flex items-center justify-center text-[9px] font-bold text-blue-700"
              >
                {i + 1}
              </div>
            ))}
            {points.length === 0 && (
              <span className="text-xs text-slate-400 italic">No points placed yet</span>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 w-full pt-1 border-t border-slate-100">
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              className="h-8 text-xs px-3 rounded-xl flex-1"
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleUndo}
              disabled={points.length === 0}
              className="h-8 px-2.5 rounded-xl"
              title="Undo last point"
            >
              <CornerDownLeft className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleClear}
              disabled={points.length === 0}
              className="h-8 px-2.5 rounded-xl text-red-500 hover:bg-red-50 border-red-200"
              title="Clear all points"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleConfirm}
              disabled={!canConfirm}
              className="h-8 text-xs px-4 rounded-xl flex-1 gap-1.5 shadow-sm"
            >
              <Check className="w-3.5 h-3.5" />
              Confirm Shape
            </Button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
