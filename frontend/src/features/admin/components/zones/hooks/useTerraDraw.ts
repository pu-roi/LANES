"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  TerraDraw,
  TerraDrawPolygonMode,
  TerraDrawRectangleMode,
  TerraDrawCircleMode,
  TerraDrawFreehandMode,
  TerraDrawSelectMode,
} from "terra-draw";
import { TerraDrawMapLibreGLAdapter } from "terra-draw-maplibre-gl-adapter";
import type { GeometryMode, Severity } from "../types";
import { getTerraDrawActiveZoneStyles } from "../types";
import type { ReportGeometry } from "@/features/admin/adminApi";

interface UseTerraDrawOptions {
  mapInstance: any;
  geometryMode: GeometryMode;
  severity: Severity;
  isEnabled?: boolean;
  isInteractive?: boolean;
  isEditingExistingShape?: boolean;
}

const TERRADRAW_LAYER_IDS = [
  "td-point",
  "td-point-marker",
  "td-linestring",
  "td-polygon",
  "td-polygon-outline",
];
const TERRADRAW_SOURCE_IDS = ["td-point", "td-linestring", "td-polygon"];

/**
 * A cancelled `style.load` callback can otherwise outlive this hook and leave
 * TerraDraw's MapLibre sources behind. Clear only this hook's known artifacts
 * before creating its single replacement instance.
 */
function removeStaleTerraDrawArtifacts(mapInstance: any) {
  if (!mapInstance) return;
  try {
    const style = mapInstance.getStyle?.();
    const styleLayers = style?.layers || [];

    // 1. Remove all MapLibre layers that belong to TerraDraw from style
    styleLayers.forEach((layer: any) => {
      if (
        layer.id?.startsWith("td-") ||
        layer.source?.startsWith("td-") ||
        TERRADRAW_LAYER_IDS.includes(layer.id) ||
        TERRADRAW_SOURCE_IDS.includes(layer.source)
      ) {
        try {
          if (mapInstance.getLayer(layer.id)) {
            mapInstance.removeLayer(layer.id);
          }
        } catch {}
      }
    });

    // Explicitly remove known layers in safe detachment order (outline, point-marker before base)
    [
      "td-point-marker",
      "td-polygon-outline",
      "td-point",
      "td-polygon",
      "td-linestring",
    ].forEach((layerId) => {
      try {
        if (mapInstance.getLayer(layerId)) {
          mapInstance.removeLayer(layerId);
        }
      } catch {}
    });

    // 2. Remove all TerraDraw sources now that dependent layers are cleared
    const styleSources = style?.sources || {};
    Object.keys(styleSources).forEach((sourceId) => {
      if (sourceId.startsWith("td-") || TERRADRAW_SOURCE_IDS.includes(sourceId)) {
        try {
          if (mapInstance.getSource(sourceId)) {
            mapInstance.removeSource(sourceId);
          }
        } catch {}
      }
    });

    // Explicitly remove known sources, purging any lingering layer referencing them
    TERRADRAW_SOURCE_IDS.forEach((sourceId) => {
      try {
        if (mapInstance.getSource(sourceId)) {
          mapInstance.getStyle?.()?.layers?.forEach((l: any) => {
            if (l.source === sourceId && mapInstance.getLayer(l.id)) {
              try { mapInstance.removeLayer(l.id); } catch {}
            }
          });
          mapInstance.removeSource(sourceId);
        }
      } catch {}
    });
  } catch (err) {
    console.warn("Could not remove stale TerraDraw artifacts:", err);
  }
}

export function useTerraDraw({
  mapInstance,
  geometryMode,
  severity,
  isEnabled = true,
  isInteractive = isEnabled,
  isEditingExistingShape = false,
}: UseTerraDrawOptions) {
  const drawRef = useRef<TerraDraw | null>(null);
  const [drawInstance, setDrawInstance] = useState<TerraDraw | null>(null);
  const [drawnGeometry, setDrawnGeometry] = useState<ReportGeometry | null>(null);
  const [drawnFeatures, setDrawnFeatures] = useState<any[]>([]);
  const [isDrawingMode, setIsDrawingMode] = useState(false);

  const resetMapCursor = useCallback(() => {
    const canvas = mapInstance?.getCanvas?.();
    const container = mapInstance?.getCanvasContainer?.();
    if (canvas) canvas.style.cursor = "";
    if (container) container.style.cursor = "";
  }, [mapInstance]);

  // Initialize TerraDraw
  useEffect(() => {
    if (!mapInstance || !isEnabled) return;

    let cancelled = false;

    const initDraw = () => {
      if (cancelled || drawRef.current) return;
      try {
        if (!mapInstance.getStyle || !mapInstance.getStyle()) return;

        removeStaleTerraDrawArtifacts(mapInstance);
        const adapter = new TerraDrawMapLibreGLAdapter({ map: mapInstance });
        const initialStyles = getTerraDrawActiveZoneStyles(severity);

        const draw = new TerraDraw({
          adapter,
          modes: [
            new TerraDrawPolygonMode({ pointerDistance: 45, styles: initialStyles as any }),
            new TerraDrawFreehandMode({ pointerDistance: 45, styles: initialStyles as any }),
            new TerraDrawRectangleMode({ pointerDistance: 45, styles: initialStyles as any }),
            new TerraDrawCircleMode({ pointerDistance: 45, styles: initialStyles as any }),
            new TerraDrawSelectMode({}),
          ],
        });

        draw.start();
        drawRef.current = draw;
        setDrawInstance(draw);

        // Apply initial mode immediately upon start
        if (!isInteractive || geometryMode === "line") {
          draw.setMode("static");
          setIsDrawingMode(false);
          resetMapCursor();
        } else if (isEditingExistingShape) {
          draw.setMode("select");
          setIsDrawingMode(false);
        } else {
          draw.setMode(geometryMode);
          setIsDrawingMode(true);
        }

        // Listen for drawing changes
        draw.on("change", () => {
          const snapshot = draw.getSnapshot();
          const polygonFeatures = snapshot.filter(
            (f: any) => f.geometry?.type === "Polygon" || f.geometry?.type === "MultiPolygon"
          );
          setDrawnFeatures(polygonFeatures);
          if (polygonFeatures.length === 0) {
            setDrawnGeometry(null);
          } else if (polygonFeatures.length === 1) {
            setDrawnGeometry(polygonFeatures[0].geometry as any);
          } else {
            const multiPolyCoords = polygonFeatures
              .map((f: any) => {
                const coords = f.geometry?.coordinates;
                if (!Array.isArray(coords) || coords.length === 0) return null;
                const isFlat = Array.isArray(coords[0]) && typeof coords[0][0] === "number";
                return isFlat ? [coords] : coords;
              })
              .filter(Boolean);
            setDrawnGeometry({
              type: "MultiPolygon",
              coordinates: multiPolyCoords,
            } as any);
          }
        });
      } catch (err) {
        console.warn("Failed to initialize TerraDraw:", err);
      }
    };

    const handleStyleLoad = () => {
      if (drawRef.current) {
        try {
          drawRef.current.stop();
        } catch {}
        drawRef.current = null;
        setDrawInstance(null);
      }
      initDraw();
    };

    if (mapInstance.isStyleLoaded && mapInstance.isStyleLoaded()) {
      initDraw();
    } else {
      mapInstance.once?.("style.load", handleStyleLoad);
    }

    mapInstance.on?.("style.load", handleStyleLoad);

    return () => {
      cancelled = true;
      mapInstance.off?.("style.load", handleStyleLoad);
      if (drawRef.current) {
        try {
          if (drawRef.current.enabled && mapInstance?.getStyle && mapInstance.getStyle()) {
            drawRef.current.stop();
          }
        } catch {}
        drawRef.current = null;
        setDrawInstance(null);
      }
      removeStaleTerraDrawArtifacts(mapInstance);
      resetMapCursor();
    };
  }, [mapInstance, isEnabled, resetMapCursor, severity]);

  // Sync mode changes
  useEffect(() => {
    if (!drawRef.current) return;
    try {
      if (!isInteractive || geometryMode === "line") {
        drawRef.current.setMode("static");
        setIsDrawingMode(false);
        resetMapCursor();
      } else if (isEditingExistingShape) {
        drawRef.current.setMode("select");
        setIsDrawingMode(false);
      } else {
        drawRef.current.setMode(geometryMode);
        setIsDrawingMode(true);
      }
    } catch (err) {
      console.warn("Error setting TerraDraw mode:", err);
    }
  }, [geometryMode, drawInstance, isEditingExistingShape, isInteractive, resetMapCursor]);

  // Sync styles on severity change
  useEffect(() => {
    if (!drawRef.current) return;
    const styles = getTerraDrawActiveZoneStyles(severity);
    try {
      const modes = ["polygon", "freehand", "rectangle", "circle"] as const;
      modes.forEach((modeName) => {
        const mode = (drawRef.current as any)?._modes?.[modeName];
        if (mode && typeof mode.updateStyles === "function") {
          mode.updateStyles(styles);
        }
      });
    } catch (err) {
      console.warn("Error updating TerraDraw styles:", err);
    }
  }, [severity]);

  // Clear features helper
  const clearDrawing = useCallback(() => {
    if (drawRef.current) {
      try {
        drawRef.current.clear();
      } catch (err) {
        console.warn("Failed to clear features:", err);
      }
    }
    setDrawnFeatures([]);
    setDrawnGeometry(null);
  }, []);

  const restoreDrawing = useCallback((features: any[]) => {
    if (!drawRef.current) return false;
    try {
      drawRef.current.clear();
      if (features.length > 0) {
        drawRef.current.addFeatures(features);
      }
      const snapshot = drawRef.current.getSnapshot();
      const polygonFeatures = snapshot.filter(
        (f: any) => f.geometry?.type === "Polygon" || f.geometry?.type === "MultiPolygon"
      );
      setDrawnFeatures(polygonFeatures);
      if (polygonFeatures.length === 0) {
        setDrawnGeometry(null);
      } else if (polygonFeatures.length === 1) {
        setDrawnGeometry(polygonFeatures[0].geometry as ReportGeometry);
      } else {
        const multiPolyCoords = polygonFeatures
          .map((f: any) => {
            const coords = f.geometry?.coordinates;
            if (!Array.isArray(coords) || coords.length === 0) return null;
            const isFlat = Array.isArray(coords[0]) && typeof coords[0][0] === "number";
            return isFlat ? [coords] : coords;
          })
          .filter(Boolean);
        setDrawnGeometry({
          type: "MultiPolygon",
          coordinates: multiPolyCoords,
        } as ReportGeometry);
      }
      return true;
    } catch (err) {
      console.error("Failed to restore zone drawing", err);
      return false;
    }
  }, []);

  const cancelDrawingMode = useCallback(() => {
    if (drawRef.current) {
      try {
        drawRef.current.setMode("static");
      } catch {}
    }
    resetMapCursor();
    setIsDrawingMode(false);
  }, [resetMapCursor]);

  return {
    drawInstance,
    drawnGeometry,
    drawnFeatures,
    isDrawingMode,
    clearDrawing,
    restoreDrawing,
    cancelDrawingMode,
    setDrawnGeometry,
  };
}
